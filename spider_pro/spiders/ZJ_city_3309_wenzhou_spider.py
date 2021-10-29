#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-02
# @Describe: 温州市公共资源交易网 - 全量/增量脚本

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
    name = 'ZJ_city_3309_wenzhou_spider'
    area_id = "3309"
    domain_url = "https://ggzyjy.wenzhou.gov.cn"
    query_url = "https://ggzyjy.wenzhou.gov.cn/wzcms/jyxx/index_1.htm"
    base_url = 'https://ggzyjy.wenzhou.gov.cn/wzcms/jyxx/index_{}.htm'
    allowed_domains = ['ggzyjy.wenzhou.gov.cn']
    area_province = "浙江-温州市公共资源交易网"

    # 招标预告
    list_advance_notice_num = []
    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告', '出让公告']
    # 招标异常
    list_alteration_category_num = ['']
    # 招标变更
    list_zb_abnormal_num = ['补充公告', '答疑补充']
    # 中标预告
    list_win_advance_notice_num = ['候选人公示']
    # 中标公告
    list_win_notice_category_num = ['中标公告', '中标结果', '出让结果']
    # 资格预审
    list_qualification_num = []
    # 其他
    list_qita_code = ['保证金退付', '合同订立信息']

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
            if self.enable_incr:
                num = 0
                li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
                for li in range(len(li_list)):
                    title_name = li_list[li].xpath('./a/@title').get()
                    all_info_url = self.domain_url + li_list[li].xpath('./a/@href').get()
                    category_name = li_list[li].xpath('./a/em/text()').get().strip()
                    pub_time = li_list[li].xpath('./span/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")

                        yield scrapy.Request(url=all_info_url, callback=self.parse_item, priority=150,
                                             meta={'pub_time': pub_time,
                                                   'title_name': title_name,
                                                   'category_name': category_name})
                    if num >= len(li_list):
                        page = int(re.findall('(\d+)', response.url[response.url.rindex('/') + 1:])[0]) + 1
                        yield scrapy.Request(url=self.base_url.format(page), callback=self.parse_urls, priority=100)
            else:
                page_list = response.xpath('//div[@class="Zy-Page FloatL"]/div/text()').get()
                total = re.findall('共(\d+).*', page_list)[0]         #总条数
                pages = re.findall('.*\/(\d+)', page_list)[0]         #总页数
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.htm'
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_info, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_info(self, response):
        try:
            li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
            for li in li_list:
                title_name = li.xpath('./a/@title').get()
                all_info_url = self.domain_url + li.xpath('./a/@href').get()
                category_name = li.xpath('./a/em/text()').get().strip()
                pub_time = li.xpath('./span/text()').get()

                yield scrapy.Request(url=all_info_url, callback=self.parse_item, priority=150,
                                     meta={'pub_time': pub_time,
                                           'title_name': title_name,
                                           'category_name': category_name})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = ''.join(re.findall('来源：(.*)', response.xpath('//div[@class="Content-Main FloatL"]//em/text()').get())).strip()
            if info_source:
                info_source = self.area_province + info_source
            else:
                info_source = self.area_province
            category = ''.join(response.xpath('//div[@class="List-head"]/h4/a[3]/text()').getall()).strip()
            category_name = response.meta['category_name']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)

            if category_name in self.list_notice_category_num:
                notice = const.TYPE_ZB_NOTICE
            elif category_name in self.list_win_advance_notice_num:
                notice = const.TYPE_WIN_ADVANCE_NOTICE
            elif category_name in self.list_win_notice_category_num:
                notice = const.TYPE_WIN_NOTICE
            elif category_name in self.list_qita_code:
                notice = const.TYPE_OTHERS_NOTICE
            elif category_name in self.list_zb_abnormal_num:
                notice = const.TYPE_ZB_ALTERATION
            else:
                notice = 'null'

            if re.search(r'变更|更正|澄清|修正|补充', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'候选人|评标结果', title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'中标|结果|成交', title_name):  # 中标公告
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'终止|中止|流标|废标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'招标|谈判|磋商|出让|招租', title_name):  # 招标公告
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = notice
            if notice_type != 'null':
                contents = response.xpath('//div[@class="Main-p"]').get()

                files_path = {}
                if response.xpath('//div[@class="Main-p"]/ul/li/p/a'):
                    conet_list = response.xpath('//div[@class="Main-p"]/ul/li/p/a')
                    for con in conet_list:
                        if con.xpath('./@href'):
                            if 'http' in con.xpath('./@href').get():
                                value = con.xpath('./@href').get()
                            else:
                                value = self.domain_url + con.xpath('./@href').get()

                            if con.xpath('./text()').get():
                                keys = con.xpath('./text()').get()
                            else:
                                keys = 'img/pdf/doc/xls'

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
                yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl ZJ_city_3309_wenzhou_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3309_wenzhou_spider -a sdt=2021-09-01 -a edt=2021-11-15".split(" "))


