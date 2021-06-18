#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-29
# @Describe: 浙江公共资源交易服务平台 - 全量/增量脚本
#
import re
import math
import json
import scrapy
import random
import urllib
import datetime
from urllib import parse
from lxml import etree

from spider_pro.utils import get_real_url, remove_specific_element
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_iframe_pdf_div_code




class MySpider(CrawlSpider):
    name = 'province_14_zhejiang_spider'
    area_id = "14"
    data_url = 'http://zjpubservice.zjzwfw.gov.cn'
    domain_url = "http://www.zjpubservice.com"
    base_url = 'http://zjpubservice.zjzwfw.gov.cn/jyxxgk/list.html'
    query_url = "http://zjpubservice.zjzwfw.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
    allowed_domains = ['zjpubservice.com']
    area_province = '浙江'
    #增量在 data里面 变化时间
    dict_data = {"token": "", "pn": 0, "rn": 50, "sdt": "", "edt": "", "wd": 'null', "inc_wd": "", "exc_wd": "",
            "fields": "title", "cnum": "001", "sort": "{\"webdate\":\"0\"}", "ssort": "title", "cl": 200, "terminal": "",
            "condition": [{"fieldName": "categorynum", "isLike": 'true', "likeType": 2},
                          {"fieldName": "infoc", "isLike": 'true', "likeType": 2, "equal": "33"}],
            "time": [{"fieldName": "webdate", "startTime": "2021-05-19 00:00:00", "endTime": "2021-05-20 23:59:59"}], "highlights": "",
            "statistics": 'null', "unionCondition": 'null', "accuracy": "", "noParticiple": "0", "searchRange": 'null', "isBusiness": "1"}

    # 招标预告
    list_advance_notice_code = []
    # 招标公告
    list_notice_category_code = ['002002001', '002001001', '002003001', '002004001', '002007001']
    # 招标变更
    list_zb_abnormal_code = ['002002003']
    # 中标预告
    list_win_advance_notice_code = ['002001004']
    # 中标公告
    list_win_notice_category_code = ['002002002', '002001005', '002003002', '002004002', '002007002']
    # 资格预审
    list_qualification_num = ['002001002']
    # 其他
    list_qita_code = ['002001003', '002002004']

    # 工程建设
    project_type_num = '002001'
    # 政府采购
    purchase_type_num = '002002'
    # 土地及矿产权
    land_type_num = '002003'
    # 国有产权
    owned_type_num = '002004'
    # 其他交易
    medical_type_num = '002007'

    list_all_category_code = list_advance_notice_code + list_notice_category_code + list_zb_abnormal_code + \
                             list_win_advance_notice_code + list_win_notice_category_code + list_qualification_num + list_qita_code

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        yield scrapy.Request(url=self.base_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            code_list = response.xpath('//div[@style="display:none"]/li/a')[:15]  #获取type 类型的code 拼接url
            for codes, category_code in zip(code_list, self.list_all_category_code):
                code = codes.xpath('./@catenum').get()
                if self.project_type_num in code:
                    category = '工程建设'
                elif self.purchase_type_num in code:
                    category = '政府采购'
                elif self.land_type_num in code:
                    category = '土地及矿产权'
                elif self.owned_type_num in code:
                    category = '国有产权'
                elif self.medical_type_num in code:
                    category = '其他交易'
                else:
                    category = ''
                if category_code in self.list_notice_category_code:
                    notice = const.TYPE_ZB_NOTICE
                elif category_code in self.list_zb_abnormal_code:
                    notice = const.TYPE_ZB_ALTERATION
                elif category_code in self.list_win_advance_notice_code:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif category_code in self.list_win_notice_category_code:
                    notice = const.TYPE_WIN_NOTICE
                elif category_code in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif category_code in self.list_qita_code:
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    equal_dict = self.dict_data['condition'][0] | {"equal": category_code}
                    pages_dict = {'condition': [equal_dict]}
                    type_dict = self.dict_data | pages_dict
                    yield scrapy.Request(url=self.query_url, method='POST', body=json.dumps(type_dict), dont_filter=True,
                                         callback=self.parse_data_urls,
                                         meta={'category': category, 'notice': notice,
                                               'type_dict': type_dict})
        except Exception as e:
            self.logger.error(f"parse_urls:发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if json.loads(response.text):
                if self.enable_incr:
                    page = 1
                    _dict = response.meta['type_dict']['time'][0] | {'startTime': self.sdt_time} | {'endTime': self.edt_time}
                    type_dict = response.meta['type_dict'] | {'time': [_dict]}
                    if json.loads(response.text)['result']['records']:
                        num_count = json.loads(response.text)['result']['records']
                        nums = 0
                        for num in range(len(num_count)):
                            pub_time = num_count[num]['infodate'] or ''
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                nums += 1
                                total = int(len(num_count))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            if nums >= len(num_count):
                                page += 1
                            else:
                                page = 1
                            _type_dict = type_dict | {'pn': (page - 1) * 50}

                            yield scrapy.Request(url=self.query_url, method='POST', body=json.dumps(type_dict),
                                                 dont_filter=True, callback=self.parse_info_url,
                                                 meta={'category': response.meta['category'],
                                                       'notice': response.meta['notice']}, priority=1000)

                else:
                    restul = json.loads(response.text)
                    total = restul['result']['totalcount']
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    pages = int(math.ceil(total/50))
                    for num in range(pages):
                        type_dict = self.dict_data | {'pn': num * 50}
                        yield scrapy.Request(url=self.query_url, method='POST', body=json.dumps(type_dict), dont_filter=True, callback=self.parse_info_url,
                                             meta={'category': response.meta['category'], 'notice': response.meta['notice']}, priority=1000)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info_url(self, response):
        try:
            if json.loads(response.text):
                num_count = json.loads(response.text)['result']['records']
                for num in num_count:
                    title_name = num['title'] or ''
                    put_time = num['infodate'] or ''
                    info_url = self.domain_url + num['linkurl']
                    info_source = num['infod'] or ''
                    if re.search(r'更正公告|变更公告', title_name):  # 招标变更
                        notice_type = const.TYPE_ZB_ALTERATION
                    elif re.search(r'中止|终止|异常|废标|流标', title_name):  # 招标异常
                        notice_type = const.TYPE_ZB_ABNORMAL
                    else:
                        notice_type = response.meta['notice']

                    yield scrapy.Request(url=info_url, callback=self.parse_item,
                                         meta={'category': response.meta['category'], 'notice_type': notice_type,
                                               'title_name': title_name, 'put_time': put_time, 'info_source': info_source}, priority=10000)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            if response.meta['info_source']:
                info_source = self.area_province + response.meta['info_source']
            else:
                info_source = self.area_province
            category = response.meta.get("category")
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'更正公告|变更公告', title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'中止|终止|异常|废标|流标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = response.meta['notice']
            files_path = {}

            content = response.xpath('//div[@class="ewb-container clearfix"]').get()
            # 去除导航栏
            _, content = remove_specific_element(content, 'p', 'class', 'info-sources')
            # 去除 title
            pattern = re.compile(r'<h1>(.*?)</h1>', re.S)
            content = content.replace(re.findall(pattern, content)[0], '')

            # 去除横线
            pattern = re.compile(r'(<hr .*?>)', re.S)
            content = content.replace(re.findall(pattern, content)[0], '')
            #去除尾部
            _, content = remove_specific_element(content, 'div', 'id', 'pdff')
            suffix_list = ['html', 'com', 'com/', 'cn', 'cn/', '##']
            files_text = etree.HTML(content)
            if files_text.xpath('//a/@href'):
                files_list = files_text.xpath('//a')
                for cont in files_list:
                    if cont.xpath('./@href'):
                        values = cont.xpath('./@href')[0]
                        if ''.join(values).split('.')[-1] not in suffix_list:
                            if 'http:' not in values:
                                value = self.data_url + values
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
            notice_item["files_path"] = "NULL" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_14_zhejiang_spider".split(" "))
    cmdline.execute("scrapy crawl province_14_zhejiang_spider -a sdt=2021-05-20 -a edt=2021-06-18".split(" "))

