#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-10
# @Describe: 山西省政府采购网

import datetime
import re

import scrapy
import math
import json
from lxml import etree
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_files, get_notice_type, \
                             get_back_date, get_timestamp, remove_specific_element


class Province121ShanxiSpiderSpider(scrapy.Spider):
    name = 'province_121_shanxi_spider'
    allowed_domains = ['ccgp-shanxi.gov.cn']
    start_urls = 'http://www.ccgp-shanxi.gov.cn'
    domain_url = 'http://www.ccgp-shanxi.gov.cn/front/search/category'
    base_url = ''
    query_url = 'http://www.ccgp-shanxi.gov.cn/home.html'
    area_id = "121"
    area_province = '山西省政府采购网'
    # 招标预告
    list_tender_notice_num = {'意见征询': 'ZcyAnnouncement5', '采购意向公开': 'ZcyAnnouncement6'}
    # 招标公告
    list_notice_category_name = {'采购公告': 'ZcyAnnouncement1'}
    # 招标变更
    list_zb_abnormal_name = {"变更公告": 'ZcyAnnouncement3'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'结果公告': 'ZcyAnnouncement2'}
    # 招标异常
    list_alteration_category_name = {}
    # 资格预审
    list_qualifiction_advance_num = {}
    # 其他
    list_qita_num = {'合同公示': 'ZcyAnnouncement4'}

    r_dict = {"districtCode": ["149900"], "categoryCode": "ZcyAnnouncement3", "pageSize": "100", "pageNo": "1"}

    def __init__(self, *args, **kwargs):
        super(Province121ShanxiSpiderSpider, self).__init__()
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
                publishDateBegin = self.sdt_time
                publishDateEnd = self.edt_time
                time_dict = self.r_dict | {"publishDateBegin": publishDateBegin} | {"publishDateEnd": publishDateEnd}
            else:
                publishDateEnd = datetime.datetime.now().strftime("%Y-%m-%d")
                publishDateBegin = get_back_date(365)
                time_dict = self.r_dict | {"publishDateBegin": publishDateBegin} | {"publishDateEnd": publishDateEnd}
            count = 0
            li_list = response.xpath('//div[@class="main_content"]/div[4]//ul[@class="tabs"]/li')
            for li in li_list:
                count += 1
                notice_name = ''.join(li.xpath('./text()').get()).strip()
                if notice_name in self.list_notice_category_name.keys():  # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                    notice_value = self.list_notice_category_name[notice_name]
                elif notice_name in self.list_zb_abnormal_name.keys():  # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                    notice_value = self.list_zb_abnormal_name[notice_name]
                elif notice_name in self.list_win_advance_notice_name.keys():  # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                    notice_value = self.list_win_advance_notice_name[notice_name]
                elif notice_name in self.list_win_notice_category_name.keys():  # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                    notice_value = self.list_win_notice_category_name[notice_name]
                elif notice_name in self.list_tender_notice_num.keys():  # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                    notice_value = self.list_tender_notice_num[notice_name]
                elif notice_name in self.list_alteration_category_name.keys():  # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                    notice_value = self.list_alteration_category_name[notice_name]
                elif notice_name in self.list_qualifiction_advance_num.keys():  # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    notice_value = self.list_qualifiction_advance_num[notice_name]
                elif notice_name in self.list_qita_num.keys():  # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                    notice_value = self.list_qita_num[notice_name]
                else:
                    notice = ''
                    notice_value = ''
                if notice:
                    r_dict = time_dict | {"categoryCode": notice_value}
                    yield scrapy.Request(url=self.domain_url, callback=self.parse_data_info, method='POST',
                                         dont_filter=True, body=json.dumps(r_dict), priority=(len(li_list)-count)*5,
                                         headers={'Content-Type': 'application/json'},
                                         meta={'r_dict': r_dict,
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f'请求的数据失败parse_urls {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if json.loads(response.text):
                    data_info = json.loads(response.text)['hits']['hits']
                    num = 0
                    count = 0
                    for info in data_info:
                        count += 1
                        pub_time = get_timestamp(info['_source']['publishDate'])
                        info_url = self.start_urls + info['_source']['url']
                        title_name = info['_source']['title']
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 priority=(len(data_info)-count)*2,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(data_info)):
                            total = int(len(data_info))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            pages = int(response.meta['r_dict']['pageNo']) + 1
                            r_dict = response.meta['r_dict'] | {'pageNo': str(pages)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_dict,
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'r_dict': r_dict})
            else:
                if json.loads(response.text):
                    total = json.loads(response.text)['hits']['total']
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta['r_dict']} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total) / 100)
                    for num in range(1, int(pages) + 1):
                        new_dict = response.meta['r_dict'] | {'page': str(num)}
                        yield scrapy.Request(url=self.domain_url, callback=self.parse_data_check,
                                             body=json.dumps(new_dict), dont_filter=True,
                                             priority=(int(pages) - num) * 10, method='post',
                                             headers={'Content-Type': 'application/json'},
                                             meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if json.loads(response.text):
                data_info = json.loads(response.text)['hits']['hits']
                count = 0
                for info in data_info:
                    count += 1
                    pub_time = get_timestamp(info['_source']['publishDate'])
                    info_url = self.start_urls + info['_source']['url']
                    title_name = info['_source']['title']
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(data_info)-count)*2,
                                         meta={'pub_time': pub_time,
                                               'title_name': title_name,
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = json.loads(response.xpath('//input[@name="articleDetail"]/@value').get())['content']
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = response.meta['title_name']
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除附件信息
                _, content = remove_specific_element(content, 'p', 'class', 'fjxx')
                # 去除附件
                _, content = remove_specific_element(content, 'ul', 'class', 'fjxx', index=None)
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.domain_url, origin, files_text, keys_a=keys_a)

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

    # cmdline.execute("scrapy crawl province_121_shanxi_spider".split(" "))
    cmdline.execute("scrapy crawl province_121_shanxi_spider -a sdt=2021-07-20 -a edt=2021-08-11".split(" "))
