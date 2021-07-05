#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-06
# @Describe: 浙江省温州市鹿城区人民政府 - 全量/增量脚本

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

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
                            remove_specific_element, get_files, get_notice_type


class MySpider(CrawlSpider):
    name = 'ZJ_city_3335_wzlucheng_spider'
    area_id = "3335"
    domain_url = "http://spgg.lucheng.gov.cn"
    query_url = "http://spgg.lucheng.gov.cn/lccms/"
    base_url = 'http://www.jiande.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['spgg.lucheng.gov.cn']
    area_province = '浙江省温州市鹿城区人民政府'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['招标公告', '招标文件公示', '采购公告', '出让公告', '国企采购']
    # 招标变更
    list_zb_abnormal_name = ["答疑补充", "补充公告"]
    # 中标预告
    list_win_advance_notice_name = ['候选公示']
    # 中标公告
    list_win_notice_category_name = ['中标公告', '出让结果', '中标结果']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []

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
            li_list = response.xpath('//div[@class="Main-Left FloatL Hidden"]/div')[:-1]
            for li in li_list:
                li_url = self.domain_url + li.xpath('./div/div/a/@href').get()
                category = li.xpath('./div/h4/text()').get()
                yield scrapy.Request(url=li_url, callback=self.parse_data_url,
                                     meta={'category': category}, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_url(self, response):
        try:
            li_list = response.xpath('//div[@class="Main-Left FloatL Hidden"]/div')[1:]
            for li in li_list:
                li_url = self.domain_url + li.xpath('./div/div/a/@href').get()
                notice_name = ''.join(li.xpath('./div/h4/text()').get()).strip()
                if notice_name in self.list_notice_category_name:       # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:         # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_notice_category_name:  # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_win_advance_notice_name:   # 中标预告
                    notice = const.TYPE_ZB_ABNORMAL
                else:
                    notice = ''
                if notice:
                    print(li_url)
                    yield scrapy.Request(url=li_url, callback=self.parse_data_info,
                                         meta={'category': response.meta['category'],
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")



    def parse_data_info(self, response):
        try:
            info_url = response.url.replace(''.join(response.url).split('/')[-1], 'index_{}.htm')
            if self.enable_incr:
                li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
                num = 0
                page = 1
                for info_num in range(len(li_list)):
                    _url = self.domain_url + li_list[info_num].xpath('./a/@href').get()
                    pub_time = li_list[info_num].xpath('./span/text()').get()
                    title_name = li_list[info_num].xpath('./a/@title').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        yield scrapy.Request(url=_url, callback=self.parse_item,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice'],
                                                   'pub_time': pub_time,
                                                   'title_name': title_name})
                    if num >= int(len(li_list)):
                        page_num = int(re.findall('(\d+)', response.url[response.url.rindex('/') + 1:])[0])
                        page_num += 1
                        yield scrapy.Request(url=info_url.format(page_num),
                                             callback=self.parse_data_info, dont_filter=True,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice']})

            else:
                total = re.findall('共(\d+)条', response.xpath('//div[@class="Zy-Page FloatL"]/div/text()').get())[0]
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                pages = re.findall('记录.*\/(\d+)页', response.xpath('//div[@class="Zy-Page FloatL"]/div/text()').get())[0]
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_data_check,
                                         meta={'category': response.meta['category'],
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
            for info in li_list:
                info_url = self.domain_url + info.xpath('./a/@href').get()
                pub_time = info.xpath('./span/text()').get()
                title_name = info.xpath('./a/@title').get()
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     meta={'category': response.meta['category'],
                                           'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'title_name': title_name})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            category = response.meta['category']
            info_source = self.area_province
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                if notice_type:
                    content = response.xpath('//div[@class="Content-Main FloatL"]').get()
                    # 去除 title
                    _, content = remove_specific_element(content, 'span', 'class', 'Bold')
                    # 去除 多余的
                    _, content = remove_specific_element(content, 'div', 'class', 'pagebar')
                    _, content = remove_specific_element(content, 'span', 'class', 'bookmark-item uuid-1573127274472 code-AM014acquirePurFileDetailUrl single-line-text-input-box-cls')
                    # # 去除 多于链接
                    _, content = remove_specific_element(content, 'blockquote', 'style', 'display: none;')
                    # 去除 info source
                    pattern = re.compile('(<em>.*?</em>)', re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')
                    # 去除 表格
                    pattern = re.compile('(<table>.*</table>)', re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')

                    files_text = etree.HTML(content)

                    keys_list = ['前往报名', 'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
                                 'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF', 'png',
                                 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG']
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
    # cmdline.execute("scrapy crawl ZJ_city_3335_wzlucheng_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3335_wzlucheng_spider -a sdt=2021-04-01 -a edt=2021-07-06".split(" "))


