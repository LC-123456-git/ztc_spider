#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-30
# @Describe: 浙江能源集团电子招投标平台 - 全量/增量脚本
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
    name = 'ZJ_enterprise_3303_zhenengjituan_spider'
    area_id = "3303"
    domain_url = "https://www.zeec.cn"
    query_url = ""
    allowed_domains = ['zeec.cn']
    area_province = "浙江能源集团电子招投标平台"

    # 招标预告
    list_advance_notice_code = []
    # 招标公告
    list_notice_category_code = ['https://www.zeec.cn/zbgg/index.jhtml']
    # 招标变更
    list_zb_abnormal_code = ['https://www.zeec.cn/bggg/index.jhtml']
    # 中标预告
    list_win_advance_notice_code = ['https://www.zeec.cn/pbgs/index.jhtml']
    # 中标公告
    list_win_notice_category_code = ['https://www.zeec.cn/jggg/index.jhtml']
    # 资格预审
    list_qualification_num = ['https://www.zeec.cn/zgys/index.jhtml']
    # 其他
    list_qita_code = ['https://www.zeec.cn/kbgg/index.jhtml']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="slideTxt mnotice2"]/div/ul/li')
            for li in li_list:
                type_url = li.xpath('./div/a/@href').get()
                if type_url in self.list_notice_category_code:
                    notice = const.TYPE_ZB_NOTICE
                elif type_url in self.list_zb_abnormal_code:
                    notice = const.TYPE_ZB_ALTERATION
                elif type_url in self.list_win_advance_notice_code:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_url in self.list_win_notice_category_code:
                    notice = const.TYPE_WIN_NOTICE
                elif type_url in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif type_url in self.list_qita_code:
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    yield scrapy.Request(url=type_url, callback=self.parse_data_urls,
                                         meta={'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 0
                li_list = response.xpath('//div[@class="lb-link"]/ul/li')
                for li in range(len(li_list)):
                    title_name = li_list[li].xpath('./a/@title').get()
                    all_info_url = li_list[li].xpath('./a/@href').get()
                    pub_time = li_list[li].xpath('./a/span[@class="bidDate"]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        yield scrapy.Request(url=all_info_url, callback=self.parse_item,
                                             meta={'notice': response.meta['notice'],
                                                   'pub_time': pub_time,
                                                   'title_name': title_name})
                    if num >= len(li_list):
                        pn += 1
                        info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                        yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info,
                                             meta={'notice': response.meta['notice']})
            else:
                pages = response.xpath('//div[@class="pag-txt"]/em[2]/text()').get()
                total = int(pages) * 16
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_info,
                                         meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"parse_data_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            li_list = response.xpath('//div[@class="lb-link"]/ul/li')
            for li in li_list:
                title_name = li.xpath('./a/@title').get()
                all_info_url = li.xpath('./a/@href').get()
                pub_time = li.xpath('./a/span[@class="bidDate"]/text()').get()

                yield scrapy.Request(url=all_info_url, callback=self.parse_item,
                                     meta={'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'title_name': title_name})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")



    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            classifyShow = ''
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            contents = response.xpath("//div[@class='ninfo-con']").get()
            if re.search(r'资格预审', title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'变更|更正|澄清', title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'候选人', title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'中标', title_name):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'终止|中止|终结', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = response.meta['notice']
            files_path = {}
            if response.xpath('//div[@class="ninfo-con"]/ul/li/a'):
                conet_list = response.xpath('//div[@class="ninfo-con"]/ul/li/a')
                for con in conet_list:
                    value = self.domain_url + con.xpath('./@href').get()
                    keys = con.xpath('./text()').get()
                    files_path[keys] = value
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

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl ZJ_enterprise_3303_zhenengjituan_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_enterprise_3303_zhenengjituan_spider -a sdt=2021-02-01 -a edt=2021-06-11".split(" "))

