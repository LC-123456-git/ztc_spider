#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-31
# @Describe: 浙江省水利厅 - 全量/增量脚本
import re
import math
import json
import scrapy
import random
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_enterprise_3304_shuiliting_spider'
    area_id = "3304"
    domain_url = "http://slt.zj.gov.cn"
    query_url = "http://slt.zj.gov.cn/module/xxgk/search.jsp?"
    allowed_domains = ['slt.zj.gov.cn']
    area_province = "浙江-水利厅"
    infotypeId = ['A1802', 'A1801']

    data = {'infotypeId': 'A1802', 'jdid': '3028', 'area': '002482285', 'divid': 'div1543161', 'standardXxgk': '1',
             'isAllList': '1', 'currpage': '1', 'sortfield': ',compaltedate:0'}


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.FormRequest(url=self.query_url, formdata=self.data,
                                 callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            for typeId in self.infotypeId:
                if typeId == 'A1801':
                    notice = const.TYPE_ZB_NOTICE
                elif typeId == 'A1802':
                    notice = const.TYPE_WIN_NOTICE
                if self.enable_incr:
                    pn = 1
                    li_list = response.xpath('//div[@class="zfxxgk_zdgkc"]/ul/li')
                    for li in range(len(li_list)):
                        pub_time = li_list[li].xpath('./b/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            if li >= len(li_list):
                                pn += 1
                            else:
                                pn = 1
                            info_dict = self.data | {"currpage": str(pn)}
                            info_dicts = info_dict | {'infotypeId': typeId}
                            yield scrapy.FormRequest(url=self.query_url, formdata=info_dicts, callback=self.parse_data_urls,
                                                     meta={'notice': notice})
                else:
                    total = int(re.findall('\d+', response.xpath('//td[@align="left"]/table/tr/td[1]/a/text()').get())[0])
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    pages = math.ceil(total/20)
                    for pn in range(1, pages + 1):
                        info_dict = self.data | {'currpage': str(pn)}
                        info_dicts = info_dict | {'infotypeId': typeId}
                        yield scrapy.FormRequest(url=self.query_url, formdata=info_dicts, callback=self.parse_data_urls,
                                                 meta={'notice': notice})
        except Exception as e:
            self.logger.error(f"parse_data_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
           li_list = response.xpath('//div[@class="zfxxgk_zdgkc"]/ul/li')
           for li in li_list:
               all_url = li.xpath('./a/@href').get()
               title_name = li.xpath('./a/@title').get()
               pub_time = li.xpath('./b/text()').get()
               if re.search(r'资格预审', title_name):
                   notice_type = const.TYPE_ZB_NOTICE
               elif re.search(r'变更|更正|澄清', title_name):
                   notice_type = const.TYPE_ZB_ALTERATION
               elif re.search(r'候选人', title_name):
                   notice_type = const.TYPE_WIN_ADVANCE_NOTICE
               elif re.search(r'终止|中止|终结', title_name):
                   notice_type = const.TYPE_ZB_ABNORMAL
               else:
                   notice_type = response.meta['notice']
               yield scrapy.Request(url=all_url, callback=self.parse_item,
                                    meta={'notice_type': notice_type, "title_name": title_name,
                                          "pub_time": pub_time})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = ''.join(response.xpath('//div[@class="wz_con_time"]/text()').extract()).replace('信息来源：', '').strip()
            if info_source:
                info_source = self.area_province + info_source
            else:
                info_source = self.area_province
            classifyShow = ''
            notice_type = response.meta['notice_type']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            contents = response.xpath("//div[@class='wz_con_content']").get()


            files_path = {}
            if response.xpath("//div[@class='wz_con_content']/p//a"):
                conet_list = response.xpath("//div[@class='wz_con_content']/p//a")
                num = 1
                for con in conet_list:
                    if 'http' in con.xpath('./@href'):
                        value = con.xpath('./@href').get()
                    else:
                        value = self.domain_url + con.xpath('./@href').get()

                    if value in 'http://zfcg.czt.zj.gov.cn/':
                        pass
                    else:
                        keys = con.xpath('./text()').get() or con.xpath('./span/text()').get()
                        if not keys:
                            keys = re.findall('\w+\.(\w+)', value[value.rindex('/')+1:])[0] + '_' + str(num)
                        files_path[keys] = value
                    num += 1

            else:
                files_path = ''
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_enterprise_3304_shuiliting_spider".split(" "))

