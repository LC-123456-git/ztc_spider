#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-06-07
# @Describe: 信e采招标采购电子交易平台 - 全量/增量脚本

import re
import math
import json
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
    name = 'province_79_xinEcai_spider'
    area_id = "79"
    domain_url = "https://www.ahbidding.com"
    query_url = "https://www.ahbidding.com/BidNotice/zbcgxx/zgcggg"
    base_url = 'https://www.ahbidding.com/BidNotice/zbcgxx/zbygg?Length=7'
    allowed_domains = ['www.ahbidding.com']
    area_province = '安徽-信e采招标采购电子交易平台'

    # 招标预告
    list_tender_notice_num = ['招标预公告']
    # 招标公告
    list_notice_category_num = ['招标采购公告']
    # 招标变更
    list_zb_abnormal_num = ['变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 中标公告
    list_win_notice_category_num = ['中标结果公告']
    # 招标异常
    list_alteration_category_num = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['采购合同']

    datas_info = {'keyword': '', 'xmlxHide': '1', 'categoryFirst': '', 'categorySecond': '',
                  'categorythird': '', 'time': '-1', 'laydatas': '', 'dqHide': '1',
                  'ddrarea': '110000', 'area': '', 'project': '-1', 'X-Requested-With': 'XMLHttpRequest'}

    proType = ['443c3b10-79f2-4751-b949-bb53b2429db1',
               'f564a40a-2739-4658-8e24-2b6db20cc53c',
               '70d2bd54-0193-4074-b1de-ac5eea2e9164']

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
            li_list = response.xpath('//div[@class="content-left"]/dl/dd')
            for li in li_list:
                if li.xpath('./a/@href'):
                    itme_url = self.domain_url + li.xpath('./a/@href').get() + '?Length=7'
                    itme_name = li.xpath('./a/text()').get()
                    if itme_name in self.list_notice_category_num:            # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    elif itme_name in self.list_zb_abnormal_num:              # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif itme_name in self.list_tender_notice_num:            # 招标预告
                        notice = const.TYPE_ZB_ADVANCE_NOTICE
                    elif itme_name in self.list_win_advance_notice_num:       # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif itme_name in self.list_win_notice_category_num:      # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif itme_name in self.list_qita_num:                     # 其他
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = ''
                    if notice:
                        for _type in self.proType:
                            data_info = self.datas_info | {'proType': _type}
                            if _type in self.proType[0]:
                                business_category = '货物'
                            elif _type in self.proType[1]:
                                business_category = '服务'
                            else:
                                business_category = '工程'
                            yield scrapy.FormRequest(url=itme_url, callback=self.parse_data, formdata=data_info,
                                                     priority=50, meta={'notice': notice, 'data_info': data_info,
                                                                        'business_category': business_category})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data(self, response):
        try:
            if self.enable_incr:
                page = 1
                _data_dicts = response.meta['data_info'] | {'laydatas': '{} - {}'.format(self.sdt_time, self.edt_time)}
                if response.xpath('//ul[@class="bidding-list"]/li/a/@href'):
                    data_li_list = response.xpath('//ul[@class="bidding-list"]/li')
                    nums = 0
                    for li in range(len(data_li_list)):
                        title_name = data_li_list[li].xpath('./a/span[1]/text()').get()
                        info_url = self.domain_url + data_li_list[li].xpath('./a/@href').get()
                        pub_time = ''.join(data_li_list[li].xpath('./a/span[last()]/text()').get()).replace('发布时间：', '').strip()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                                 meta={'notice': response.meta['notice'],
                                                       'business_category': response.meta['business_category'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})

                        if nums >= len(data_li_list):
                            page += 1
                            _data_dict = _data_dicts | {'pageIndex': str(page)}
                            yield scrapy.FormRequest(url=response.url, formdata=_data_dict,
                                                     callback=self.parse_data_info,
                                                     dont_filter=True, priority=100,
                                                     meta={'notice': response.meta['notice'],
                                                           'business_category':  response.meta['business_category']})

            else:
                pages = response.xpath('//ul[@class="pagination"]/@data-pagecount').get()
                self.logger.info(f"本次获取总条数为：{int(pages) * 15}")
                if pages != '0':
                    for page in range(1, int(pages)):
                        data_dict = response.meta['data_info'] | {'pageIndex': str(page)}
                        yield scrapy.FormRequest(url=response.url, formdata=data_dict, callback=self.parse_data_info,
                                                 dont_filter=True, priority=100,
                                                 meta={'notice': response.meta['notice'],
                                                       'business_category':  response.meta['business_category']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if response.xpath('//ul[@class="bidding-list"]/li/a/@href'):
                data_list = response.xpath('//ul[@class="bidding-list"]/li')
                for data in data_list:
                    title_name = data.xpath('./a/span[1]/text()').get()
                    info_url = self.domain_url + data.xpath('./a/@href').get()
                    pub_time = ''.join(data.xpath('./a/span[last()]/text()').get()).replace('发布时间：', '').strip()
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                         meta={'notice': response.meta['notice'],
                                               'business_category':  response.meta['business_category'],
                                               'pub_time': pub_time,
                                               'title_name': title_name})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_urls {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source =self.area_province
            business_category = response.meta.get("business_category")
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']

            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'测试项目|征求意见公示', title_name):
                notice_type = ''
            elif re.search(r'资格审查', title_name):  # 资格审查
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif re.search(r'变更|更正|澄清|补充|取消|延期', title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'终止|中止|废标|流标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'候选人', title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']
            if notice_type:
                content_list = response.xpath('//div[@class="details-text"]/div')
                for cont in content_list:
                    if cont.xpath('./p[@class="h1"]/text()').get() == title_name:
                        content = cont.get()

                        # 去除 title
                        _, content = remove_specific_element(content, 'p', 'class', 'h1')

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
                                            value = self.domain_url + values
                                        else:
                                            value = values
                                        if cont.xpath('.//text()'):
                                            keys = ''.join(cont.xpath('.//text()')).strip()
                                            if ''.join(values).split('.')[-1] not in keys:
                                                key = keys + '.' + ''.join(values).split('.')[-1]
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
                        notice_item["business_category"] = business_category

                        yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_79_xinEcai_spider".split(" "))
    cmdline.execute("scrapy crawl province_79_xinEcai_spider -a sdt=2021-04-01 -a edt=2021-06-10".split(" "))


