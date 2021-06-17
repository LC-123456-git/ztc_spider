#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-06-15
# @Describe: 北京市政府采购网 - 全量/增量脚本

import re
import math
import json

import requests
import scrapy
import random
import urllib
import datetime
from lxml import etree
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element
from lxml.html import tostring

class MySpider(CrawlSpider):
    name = 'province_1102_beijingZFW_spider'
    area_id = "1102"
    domain_url = "http://www.ccgp.gov.cn"
    query_url = "http://www.ccgp-beijing.gov.cn/xxgg/index.html?name=jieshou"
    base_url = 'http://www.ccgp-beijing.gov.cn/xxgg/'
    allowed_domains = ['ccgp.gov.cn']
    area_province = '北京市政府采购网'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_num = ['招标公告', '单一公告']
    # 招标变更
    list_zb_abnormal_num = ['更正公告']
    # 中标预告
    list_win_advance_notice_num = ['']
    # 中标公告
    list_win_notice_category_num = ['中标公告']
    # 招标异常
    list_alteration_category_num = ['废标公告']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['合同公告', '其他公告']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    }

    page = 0  # page为0 是因为 第二页的 index 为1
    def get_pages(self, url):
        res = requests.get(url=url, headers=self.headers).text
        html = etree.HTML(res)
        page_list = html.xpath('//div[@class="a_div"]/a//text()')
        bool = True if '下一页' in page_list else False
        return bool


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_time(self, pub_time):
        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
        if x:
            return True

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="xinxi_left"]//ul/li')[4:5]
            for li in li_list:
                if li.xpath('./@id'):
                    li_url = self.base_url + li.xpath('./@id').get()
                    li_name = li.xpath('./text()').get()
                    if li_name in self.list_notice_category_num:            # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    elif li_name in self.list_zb_abnormal_num:              # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif li_name in self.list_alteration_category_num:      # 招标异常
                        notice = const.TYPE_ZB_ABNORMAL
                    elif li_name in self.list_win_notice_category_num:      # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif li_name in self.list_qita_num:                     # 其他
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=li_url, callback=self.parse_data, dont_filter=True,
                                             meta={'notice': notice, 'li_name': li_name})

        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data(self, response):
        try:
            if self.enable_incr:
                if response.xpath('//ul[@class="xinxi_ul"]/li/a/@href'):
                    data_li_list = response.xpath('//ul[@class="xinxi_ul"]/li')
                    nums = 0

                    for li in range(len(data_li_list)):
                        info_url = ''.join(data_li_list[li].xpath('./a/@href').get()).replace('./', response.url[:response.url.rindex('/') + 1])
                        pub_time = data_li_list[li].xpath('./span/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")

                            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150, dont_filter=True,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time})

                        if nums >= len(data_li_list):
                            self.page += 1
                            data_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.html'.format(self.page)
                            yield scrapy.Request(url=data_url,
                                                 callback=self.parse_data, priority=100, dont_filter=True,
                                                 meta={'notice': response.meta['notice']})

            else:
                page = -1
                while True:
                    if self.get_pages(response.url):
                        page += 1
                        info = response.url[:response.url.rindex('/') + 1]
                        info_urls = response.url if page == 0 else info + 'index_{}.html'.format(page)
                        if self.get_pages(info_urls):
                            yield scrapy.Request(url=info_urls, callback=self.parse_data_info, dont_filter=True,
                                                 priority=100, meta={'notice': response.meta['notice']})
                        else:
                            yield scrapy.Request(url=info_urls, callback=self.parse_data_info, dont_filter=True,
                                                 priority=100, meta={'notice': response.meta['notice']})
                            break
                    else:
                        yield scrapy.Request(url=response.url, callback=self.parse_data_info, dont_filter=True,
                                             priority=100, meta={'notice': response.meta['notice']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if response.xpath('//ul[@class="xinxi_ul"]/li/a/@href'):
                data_list = response.xpath('//ul[@class="xinxi_ul"]/li')
                for data in data_list:
                    info_url = ''.join(data.xpath('./a/@href').get()).replace('./', response.url[:response.url.rindex('/') + 1])
                    pub_time = data.xpath('./span/text()').get()

                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150, dont_filter=True,
                                         meta={'notice': response.meta['notice'],
                                               'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            category = '采购'
            origin = response.url
            info_source = self.area_province
            title_name = response.xpath('//div[@style="text-align: center;margin:28px 0 28px 0;"]/span/text()').get()
            pub_time = response.meta['pub_time']

            pub_time = get_accurate_pub_time(pub_time)

            if re.search(r'资格预审', title_name):                         # 资格审查
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif re.search(r'变更|更正|澄清|补充|取消|延期', title_name):   # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'终止|中止|废标|流标', title_name):             # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'候选人', title_name):                          # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'征求意见', title_name):                        # 招标预告
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']
            if notice_type:
                content = response.xpath('//div[@style="width: 1105px;margin:0 auto"]').get()
                # 去除导航栏
                _, content = remove_specific_element(content, 'div', 'class', 'div_hui')
                # 去除 title
                _, content = remove_specific_element(content, 'div', 'style', 'text-align: center;margin:28px 0 28px 0;')
                # 去除 尾部 字样
                _, content = remove_specific_element(content, 'div', 'class', 'anniu')
                files_path = {}
                suffix_list = ['html', 'com', 'com/', 'cn', 'cn/', '##']
                files_text = etree.HTML(content)
                if files_text.xpath('//a/@href'):
                    files_list = files_text.xpath('//a')
                    for cont in files_list:
                        if cont.xpath('./@href'):
                            values = cont.xpath('./@href')[0]
                            if ''.join(values).split('.')[-1] not in suffix_list:
                                if 'http:' not in values:
                                    value = ''.join(values).replace('./', response.url[:response.url.rindex('/') + 1])
                                    contents = ''.join(content).replace(values, value)
                                else:
                                    value = values
                                if cont.xpath('.//text()'):
                                    keys = ''.join(cont.xpath('.//text()')).strip()
                                    if ''.join(values).split('.')[-1] not in keys:
                                        key = keys + '.' + ''.join(values).split('.')[-1]
                                    else:
                                        key = keys
                                    files_path[key] = value
                if files_path:
                    content = contents
                else:
                    content = content


                notice_item = NoticesItem()
                notice_item["origin"] = origin
                notice_item["title_name"] = title_name
                notice_item["pub_time"] = pub_time
                notice_item["info_source"] = info_source
                notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                notice_item["files_path"] = "" if not files_path else files_path
                notice_item["notice_type"] = notice_type
                notice_item["content"] = content
                notice_item["area_id"] = self.area_id
                notice_item["category"] = category

                yield notice_item



if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_1102_beijingZFW_spider".split(" "))
    cmdline.execute("scrapy crawl province_1102_beijingZFW_spider -a sdt=2021-06-13 -a edt=2021-06-16".split(" "))


