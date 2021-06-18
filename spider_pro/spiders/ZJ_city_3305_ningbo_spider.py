#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-02
# @Describe: 宁波市公共资源交易网 - 全量/增量脚本

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
    name = 'ZJ_city_3305_ningbo_spider'
    area_id = "3305"
    domain_url = "http://bidding.ningbo.gov.cn"
    query_url = "http://bidding.ningbo.gov.cn/cms/jyxx/index.htm"
    allowed_domains = ['bidding.ningbo.gov.cn']
    area_province = "浙江-宁波市公共资源交易网"

    # 招标预告
    list_advance_notice_ = ['招标文件预公示', '采购预告']
    # 招标公告
    list_notice_category_num = ['招标公告（资格预审公告）', '招标预告', '交易公告', '出让公告', '股权项目', '资产项目',
                                '罚没物品', '融资需求', '金融资产', '采购分类']
    # 招标变更
    list_zb_abnormal_code = []
    # 中标预告
    list_win_advance_notice_code = ['预中标公示']
    # 中标公告
    list_win_notice_category_code = ['中标公告', '中标结果', '出让结果公示', '结果公示', '结果公告', '排污权交易']
    # 资格预审
    list_qualification_num = ['资格预审']
    # 其他
    list_qita_code = ['投诉受理及处理结果公告']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="nav1"]/ul/li')
            for li in li_list:
                data_url = self.domain_url + li.xpath('./a/@href').get()
                type_name = li.xpath('./a/text()').get()

                if type_name in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE
                elif type_name in self.list_win_advance_notice_code:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_name in self.list_win_notice_category_code:
                    notice = const.TYPE_WIN_NOTICE
                elif type_name in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif type_name in self.list_qita_code:
                    notice = const.TYPE_OTHERS_NOTICE
                elif type_name in self.list_advance_notice_:
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                else:
                    notice = ''
                if notice:
                    yield scrapy.Request(url=data_url, callback=self.parse_data_urls,
                                         meta={'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 0
                li_list = response.xpath('//div[@class="c1-body"]/li')
                category = response.xpath('//div[@class="navCurrent"]/span/a[3]/text()').get()
                for li in range(len(li_list)):
                    title_name = li_list[li].xpath('./a/@title').get()
                    all_info_url = self.domain_url + li_list[li].xpath('./a/@href').get()
                    pub_time = li_list[li].xpath('./span[@class="date"]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        yield scrapy.Request(url=all_info_url, callback=self.parse_item,
                                             meta={'notice': response.meta['notice'], 'pub_time': pub_time,
                                                   'title_name': title_name, 'category': response.meta['category']})


                    info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                    if num >= len(li_list):
                        pn += 1
                        yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info,
                                             meta={'notice': response.meta['notice'], 'category': category})
            else:
                category = response.xpath('//div[@class="navCurrent"]/span/a[3]/text()').get()
                pages = re.findall('/(\d+)', response.xpath('//div[@class="pg-3"]/div/text()').get())[0]
                total = re.findall('共(\d+)条', response.xpath('//div[@class="pg-3"]/div/text()').get())[0]
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_info,
                                         meta={'notice': response.meta['notice'], 'category': category})
        except Exception as e:
            self.logger.error(f"parse_data_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            li_list = response.xpath('//div[@class="c1-body"]/li')
            for li in li_list:
                title_name = li.xpath('./a/@title').get()
                all_info_url = self.domain_url + li.xpath('./a/@href').get()
                pub_time = li.xpath('./span[@class="date"]/text()').get()

                yield scrapy.Request(url=all_info_url, callback=self.parse_item,
                                     meta={'notice': response.meta['notice'], 'pub_time': pub_time,
                                           'title_name': title_name, 'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")



    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            category = response.meta['category']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            contents = response.xpath("//div[@style='width: 100%; overflow: auto']").get()
            if re.search(r'变更| 更正| 澄清', title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'候选人', title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'中标结果| 中选公示', title_name):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'终止| 中止 | 终结', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'预公示| 预告', title_name):
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']

            files_path = {}
            if response.xpath('//div[@style="width: 100%; overflow: auto"]//img/@src'):
                conet_list = response.xpath('//div[@style="width: 100%; overflow: auto"]//img')
                for con in conet_list:
                    if 'http' in con.xpath('./@src').get():
                        value = con.xpath('./@src').get()
                    else:
                        value = self.domain_url + con.xpath('./@src').get()
                    if con.xpath('./@alt').get():
                        keys = con.xpath('./@alt').get()
                    else:
                        keys = 'img/pdf/doc/xls'
                    files_path[keys] = value
            else:
                files_path = ''
            if response.xpath('//div[@style="width:300px;margin:0 auto;"]/a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href'):
                conet_list = response.xpath('//div[@style="width:300px;margin:0 auto;"]//a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href')
                for con in conet_list:
                    if 'http' in con.xpath('./@href').get():
                        value = con.xpath('./@href').get()
                    else:
                        value = self.domain_url + con.xpath('./@href').get()
                    keys = con.xpath('./b/text()').get() or con.xpath('./span/text()').get()
                    files_path[keys] = value
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
            notice_item["category"] = category
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3305_ningbo_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3305_ningbo_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))

