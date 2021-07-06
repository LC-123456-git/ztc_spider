#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-02
# @Describe: 淳安县公共资源交易平台 - 全量/增量脚本

import re
import math
import json

import requests
import scrapy
import random
import urllib
import datetime

import xmltodict
from lxml import etree
from spider_pro.utils import get_files, get_notice_type
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element


class MySpider(CrawlSpider):
    name = 'ZJ_city_3332_chunan_spider'
    area_id = "3332"
    domain_url = "http://www.qdh.gov.cn"
    query_url = "http://www.qdh.gov.cn/ggzyjyw/index.html"
    base_url = 'http://www.qdh.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['qdh.gov.cn']
    area_province = '浙江省淳安县公共资源交易平台'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['招标公告', '采购公告']
    # 招标变更
    list_zb_abnormal_name = []
    # 中标预告
    list_win_advance_notice_name = ['中标公示', '中标前公示']
    # 中标公告
    list_win_notice_category_name = ['成交结果公告', '中标结果']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []
    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '2241',
        'path': '/',
        'columnid': '1229429570',
        'sourceContentType': '1',
        'unitid': '6717153',
        'webname': '淳安县政府门户网站',
        'permissiontype': '0'
    }

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
            li_list = response.xpath('//div[@class="ewb-do-hd l"]/ul/li')
            for li in li_list:
                li_url = self.domain_url + li.xpath('./a/@href').get()
                category = li.xpath('./a/text()').get()
                yield scrapy.Request(url=li_url, callback=self.parse_data_url,
                                     meta={'category': category}, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_url(self, response):
        try:
            li_list = response.xpath('//ul[@class="ewb-pan-items"]/li')
            for li in li_list:
                li_url = self.domain_url + li.xpath('./a/@href').get()
                notice_name = li.xpath('./a/@title').get()

                if notice_name in self.list_notice_category_name:       # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:         # 变更公告
                    notice = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_advance_notice_name:  # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif notice_name in self.list_win_notice_category_name:  # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_alteration_category_name:  # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                else:
                    notice = ''
                if notice:
                    yield scrapy.Request(url=li_url, callback=self.parse_data,
                                         meta={'category': response.meta['category'],
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data(self, response):
        try:
            unitid = response.xpath('//div[@class="ewb-colu-bd"]/div/@id').get()
            columnid = re.findall('(\d+)', response.url)[0]
            data_dict = self.r_dict | {'columnid': columnid} | {'unitid': unitid}
            yield scrapy.FormRequest(url=self.base_url.format(1, 121), callback=self.parse_data_info,
                                     formdata=data_dict, dont_filter=True,
                                     meta={'category': response.meta['category'],
                                           'notice': response.meta['notice'],
                                           'data_dict': data_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                xmlparse = xmltodict.parse(response.text)
                jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
                num = 0
                startrecord = 1
                endrecord = 120
                if jsonstr:
                    for info in jsonstr:
                        info_url = self.domain_url + ''.join(re.findall('<a .*? href=(.*?) .*?>', info)).replace("\'", '')
                        pub_time = re.findall('<span .*?>(.*)</span>', info)[0]
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(jsonstr))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 meta={'category': response.meta['category'],
                                                       'notice': response.meta['notice'],
                                                       'pub_time': pub_time})
                        if num >= int(len(jsonstr)):
                            startrecord += 120
                            endrecord += 120
                            yield scrapy.FormRequest(url=self.base_url.format(startrecord, endrecord),
                                                     callback=self.parse_data_info,
                                                     formdata=response.meta['data_dict'], dont_filter=True,
                                                     meta={'category': response.meta['category'],
                                                           'notice': response.meta['notice']})

            else:
                total = response.xpath('//datastore/totalrecord/text()').get()
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                pages = math.ceil(int(total) / 120)
                startrecord = 0
                endrecord = 120
                for num in range(1, int(pages) + 1):
                    if num == 1:
                        startrecord = 1
                        endrecord = 120
                    else:
                        startrecord += 120
                        endrecord += 120
                    yield scrapy.FormRequest(url=self.base_url.format(startrecord, endrecord),
                                             callback=self.parse_data_check,
                                             formdata=response.meta['data_dict'], dont_filter=True,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            xmlparse = xmltodict.parse(response.text)
            jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
            if jsonstr:
                for info in jsonstr:
                    info_url = self.domain_url + ''.join(re.findall('<a .*? href=(.*?) .*?>', info)).replace("\'", '')
                    pub_time = re.findall('<span .*?>(.*)</span>', info)[0]
                    yield scrapy.Request(url=info_url, callback=self.parse_item,
                                         meta={'category': response.meta['category'],
                                               'notice': response.meta['notice'],
                                               'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            category = response.meta['category']
            info_source = self.area_province
            title_name = ''.join(response.xpath('//div[@class="ewb-article"]/h3/text()').get()).strip()
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                if notice_type:
                    content = response.xpath('//div[@class="ewb-article"]').get()
                    # 去除导航栏
                    _, content = remove_specific_element(content, 'div', 'class', 'ewb-loca')
                    # 去除 info_sources
                    _, content = remove_specific_element(content, 'div', 'class', 'ewb-article-sources')
                    # 去除 title
                    pattern = re.compile('(<h3>.*?</h3>)', re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')

                    # _, files_path = catch_files(content, self.domain_url)
                    files_text = etree.HTML(content)
                    keys_list = ['前往报名', 'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
                                 'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF', 'png',
                                 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG', 'ZJYQCF', 'YQZBX']
                    files_path = get_files(self.domain_url, origin, files_text, keys_list=keys_list)


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
    cmdline.execute("scrapy crawl ZJ_city_3332_chunan_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3332_chunan_spider -a sdt=2021-05-01 -a edt=2021-07-01".split(" "))


