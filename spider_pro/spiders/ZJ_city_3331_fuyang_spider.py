#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-01
# @Describe: 富阳区公共资源交易中心 - 全量/增量脚本

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
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element
from lxml.html import tostring

class MySpider(CrawlSpider):
    name = 'ZJ_city_3331_fuyang_spider'
    area_id = "3331"
    domain_url = "http://www.fuyang.gov.cn"
    query_url = "http://www.fuyang.gov.cn/col/col1229429568/index.html"
    base_url = 'http://www.fuyang.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['fuyang.gov.cn']
    area_province = '浙江省杭州市富阳区公共资源交易中心'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_code = ['6717126', '6717103', '6717280', '6717163']
    list_notice_category_name = ['招标公告', '交易公告']
    # 招标变更
    list_zb_abnormal_code = ['6717274', '6717150', '6717173', '6717283']
    list_zb_abnormal_name = ['答疑文件', '更正公告', '更正通知']
    # 中标预告
    list_win_advance_notice_code = ['6717153', '6717170']
    list_win_advance_notice_name = ['中标公告']
    # 中标公告
    list_win_notice_category_code = ['6717277', '6717291']
    list_win_notice_category_name = ['成交结果公示']
    # 招标异常
    list_alteration_category_code = ['6903292']
    list_alteration_category_name = ['终止公告']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    }
    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '2754',
        'path': '/',
        'columnid': '1229429570',
        'sourceContentType': '1',
        'unitid': '6717153',
        'webname': '杭州市富阳区人民政府',
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
        # url = 'http://www.fuyang.gov.cn/art/2019/1/10/art_1229429570_59081844.html'
        # yield scrapy.Request(url=url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="trem-list list1"]/ul/li')
            for li in li_list:
                li_url = li.xpath('./a/@href').get()
                category = li.xpath('./a/text()').get()
                yield scrapy.Request(url=li_url, callback=self.parse_data_url, dont_filter=True,
                                     meta={'category': category}, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_url(self, response):
        try:
            li_list = response.xpath('//div[@class="trem-list list2"]/ul/li')
            for li in li_list:
                li_url = li.xpath('./a/@href').get()
                notice_name = li.xpath('./a/text()').get()

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
                    yield scrapy.Request(url=li_url, callback=self.parse_data, dont_filter=True,
                                         meta={'category': response.meta['category'],
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data(self, response):
        try:
            unitid = response.xpath('//div[@class="table-box"]/ul/div/@id').get()
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
                    info_url = self.domain_url + re.findall('<a href="(.*?)" .*?>', info)[0]
                    pub_time = re.findall('<div class="sj1">(.*)</div>', info)[0]
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
                info_url = self.domain_url + re.findall('<a href="(.*?)" .*?>', info)[0]
                pub_time = re.findall('<div class="sj1">(.*)</div>', info)[0]
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
            title_name = ''.join(response.xpath('//div[@class="MainList"]/div[@class="AfficheTitle"]/text()').get()).strip()
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                if re.search(r'变更|更正|澄清|补充|取消|延期', title_name):        # 招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'终止|中止|废标|流标', title_name):                # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'候选人', title_name):                            # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'采购意向|需求公示', title_name):                   # 招标预告
                    notice_type = const.TYPE_ZB_ADVANCE_NOTICE
                elif re.search(r'单一来源|询价|竞争性谈判|竞争性磋商', title_name):   # 招标公告
                    notice_type = const.TYPE_ZB_NOTICE
                else:
                    notice_type = response.meta['notice']
                if notice_type:
                    # 去除 content里面多余的html body标签
                    content = ''.join(response.text).replace('</html>', '').replace('</body>', '')
                    pattern = re.compile('<div class="content" .*?>(.*)<script type="text/javascript" .*?>', re.S)
                    content = re.findall(pattern, content)[0]
                    # 去除导航栏
                    _, content = remove_specific_element(content, 'div', 'class', 'MainTitle')
                    # 去除 title
                    _, content = remove_specific_element(content, 'div', 'class', 'AfficheTitle')
                    # 去除 尾部 字样
                    _, content = remove_specific_element(content, 'div', 'class', 'PDFViewArea')


                    files_path = {}
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
                                        value = ''.join(values).replace('./', response.url[:response.url.rindex('/') + 1])
                                    else:
                                        value = values
                                    if cont.xpath('./text()'):
                                        key = ''.join(cont.xpath('./text()')[0]).strip()
                                        if key not in keys_list:
                                        # if ''.join(values).split('.')[-1] in keys:
                                        #     key = keys + '.' + ''.join(values).split('.')[-1]
                                        # else:
                                        #     key = keys
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
                    # print(notice_item)



if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3331_fuyang_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3331_fuyang_spider -a sdt=2021-05-01 -a edt=2021-07-01".split(" "))


