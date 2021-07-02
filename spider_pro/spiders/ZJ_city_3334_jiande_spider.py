#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-05
# @Describe: 杭州市公共资源交易中心建德分中心 - 全量/增量脚本

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
from spider_pro.utils import get_real_url, catch_files
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element


class MySpider(CrawlSpider):
    name = 'ZJ_city_3334_jiande_spider'
    area_id = "3334"
    domain_url = "http://www.jiande.gov.cn"
    query_url = "http://www.jiande.gov.cn/col/col1229346101/index.html"
    base_url = 'http://www.jiande.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['jiande.gov.cn']
    area_province = '浙江省杭州市建德市公共资源交易中心'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['招标公告', '产权公告']
    # 招标变更
    list_zb_abnormal_name = ["通知答疑"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标公示', '成交公示']
    # 招标异常
    list_alteration_category_name = ['废标公告']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []
    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '2210',
        'path': '/',
        'columnid': '1229429570',
        'sourceContentType': '1',
        'unitid': '6717153',
        'webname': '建德市政府',
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
            li_list = response.xpath('//td[@bgcolor="2496D4"]/a')[2:]
            for li in li_list:
                li_url = self.domain_url + li.xpath('./@href').get()
                category = li.xpath('./text()').get()
                yield scrapy.Request(url=li_url, callback=self.parse_data_url, dont_filter=True,
                                     meta={'category': category}, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_url(self, response):
        try:
            li_list = response.xpath('//td[@class="mtjj_mb3"]/div/ul/li')
            for li in li_list:
                li_url = self.domain_url + li.xpath('./a/@href').get()
                notice_name = li.xpath('./a/text()').get()

                if notice_name in self.list_notice_category_name:       # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:         # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
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
            unitid = response.xpath('//table[@width="759"]/tr[2]/td/div/@id').get()
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
                for info in jsonstr:
                    info_url = ''.join(re.findall('<a href=(.*?) .*?>', info)).replace('"', '')
                    pub_time = '20' + re.findall('<td .* class="xxlb_xhx">(.*?)</td>', info)[0]
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
            for info in jsonstr:
                info_url = ''.join(re.findall('<a href=(.*?) .*?>', info)).replace('"', '')
                pub_time = '20' + re.findall('<td .* class="xxlb_xhx">(.*?)</td>', info)[0]
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
            title_name = ''.join(response.xpath('//div[@id="ivs_title"]/text()').get()).strip()
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                if re.search(r'变更|更正|澄清|补充|取消|延期', title_name):        # 招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'终止|中止|废标|流标', title_name):                # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'候选人', title_name):                             # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'采购意向|需求公示', title_name):                   # 招标预告
                    notice_type = const.TYPE_ZB_ADVANCE_NOTICE
                elif re.search(r'单一来源|询价|竞争性谈判|竞争性磋商', title_name):   # 招标公告
                    notice_type = const.TYPE_ZB_NOTICE
                else:
                    notice_type = response.meta['notice']
                if notice_type:
                    content = response.xpath('//div[@class="col-md-20 top20 border-infodetail"]').get()
                    # 去除 title
                    _, content = remove_specific_element(content, 'div', 'class', 'infotitle top10')
                    # 去除 info_sources
                    _, content = remove_specific_element(content, 'div', 'class', 'infosecond')
                    # 去除 横线
                    _, content = remove_specific_element(content, 'div', 'class', 'infoline')


                    files_path = {}
                    # _, files_path = catch_files(content, self.domain_url)

                    suffix_list = ['html', 'com', 'com/', 'cn', 'cn/', '##', 'cn:8080/']
                    keys_list = ['前往报名']
                    files_text = etree.HTML(content)
                    if files_text.xpath('//a/@href'):
                        files_list = files_text.xpath('//a')
                        for cont in files_list:
                            if cont.xpath('./@href'):
                                values = cont.xpath('./@href')[0]
                                if ''.join(values).split('.')[-1] not in suffix_list:
                                    if 'http:' not in values:
                                        value = self.domain_url + ''.join(values).replace('./', response.url[:response.url.rindex('/') + 1])
                                    else:
                                        value = values
                                    if cont.xpath('./text()'):
                                        keys = ''.join(cont.xpath('./text()')[0]).strip()
                                        if keys not in keys_list:
                                            if ''.join(values).split('.')[-1] not in keys:
                                                key = keys + '.' + ''.join(values).split('.')[-1].split('&')[0]
                                            else:
                                                key = keys
                                            files_path[key] = value


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
    # cmdline.execute("scrapy crawl ZJ_city_3334_jiande_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3334_jiande_spider -a sdt=2021-05-01 -a edt=2021-07-02".split(" "))


