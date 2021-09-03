#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-30
# @Describe: 青海省政府采购网
import json

import scrapy, re, math
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
     get_files, get_notice_type, remove_specific_element, get_timestamp


class Province131QingHaiSpider(CrawlSpider):
    name = 'province_131_qinghai_spider'
    allowed_domains = ['ccgp-qinghai.gov.cn']
    start_urls = 'http://www.ccgp-qinghai.gov.cn'
    domain_url = 'http://www.ccgp-qinghai.gov.cn/front/search/category'
    base_url = 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement8/index.html?districtCode=639900&utm=sites_group_front.2ef5001f.0.0.46326230093011ecafed575f5eddb4f6'
    query_url = ''
    area_id = "131"
    area_province = '青海省政府采购网'

    # 招标预告
    list_tender_notice_name = ['采购意向公开', '单一来源采购项目征求意见公示']
    # 招标公告
    list_notice_category_name = ['公开招标公告', '邀请招标公告', '竞争性谈判公告', '竞争性磋商公告', '询价采购公告']
    # 招标变更
    list_zb_abnormal_name = ["更正公告"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标(成交)结果公告']
    # 招标异常
    list_alteration_category_name = ['废标公告']
    # 资格预审
    list_qualifiction_advance_num = ['公开招标资格预审公告']
    # 其他
    list_qita_num = ['采购合同公告', '协议供货结果公告']

    list_code = ['ZcyAnnouncement11', 'ZcyAnnouncement1', 'ZcyAnnouncement2', 'ZcyAnnouncement3009',
                 'ZcyAnnouncement3002', 'ZcyAnnouncement3011', 'ZcyAnnouncement3003', 'ZcyAnnouncement3',
                 'ZcyAnnouncement4', 'ZcyAnnouncement9999', 'ZcyAnnouncement8888', 'ZcyAnnouncement5',
                 'ZcyAnnouncement8']

    r_dict = {"pageNo": '1', "pageSize": '50', "categoryCode": "ZcyAnnouncement3009", "districtCode": ["639900"],
              "utm": "sites_group_front.2ef5001f.0.0.fac44980093411ec93b69734457b2ab6"}

    def get_category(self, notice_name):
        if notice_name in self.list_notice_category_name:         # 招标公告
            notice = const.TYPE_ZB_NOTICE
        elif notice_name in self.list_zb_abnormal_name:           # 招标变更
            notice = const.TYPE_ZB_ALTERATION
        elif notice_name in self.list_win_advance_notice_name:    # 中标预告
            notice = const.TYPE_WIN_ADVANCE_NOTICE
        elif notice_name in self.list_win_notice_category_name:   # 中标公告
            notice = const.TYPE_WIN_NOTICE
        elif notice_name in self.list_tender_notice_name:         # 招标预告
            notice = const.TYPE_ZB_ADVANCE_NOTICE
        elif notice_name in self.list_alteration_category_name:   # 招标异常
            notice = const.TYPE_ZB_ABNORMAL
        elif notice_name in self.list_qualifiction_advance_num:   # 资格预审
            notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice_name in self.list_qita_num:                   # 其他
            notice = const.TYPE_OTHERS_NOTICE
        else:
            notice = ''
        return notice

    def __init__(self, *args, **kwargs):
        super(Province131QingHaiSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for code in self.list_code:
            new_dict = self.r_dict | {'categoryCode': code}
            yield scrapy.Request(url=self.domain_url, method='POST', callback=self.parse_data_info,
                                 body=json.dumps(new_dict), headers={'Content-Type': 'application/json;charset=UTF-8'},
                                 meta={'new_dict': new_dict})

    def parse_data_info(self, response):
        try:
            if response.text:
                data_info = json.loads(response.text)
                if self.enable_incr:
                    count = 0
                    num = 0
                    data_info = json.loads(response.text)['hits']['hits']
                    for info in data_info:
                        count += 1
                        notice = self.get_category(info['_source']['pathName'])
                        title_name = info['_source']['title']
                        info_url = self.start_urls + info['_source']['url']
                        pub_time = get_timestamp(info['_source']['publishDate'])
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 priority=(len(data_info)-count) * 100,
                                                 meta={'notice': notice,
                                                       'title_name': title_name,
                                                       'pub_time': pub_time})
                        if num >= int(len(data_info)):
                            total = int(len(data_info))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            page = int(response.meta['new_dict']['pageNo']) + 1
                            new_dict = response.meta['new_dict'] | {"pageNo": str(page)}
                            yield scrapy.Request(url=self.domain_url, method='POST', callback=self.parse_data_info,
                                                 body=json.dumps(new_dict),
                                                 headers={'Content-Type': 'application/json;charset=UTF-8',
                                                          'new_dict': new_dict})

                else:
                    total = data_info['hits']['total']
                    pages = math.ceil(total / 50)
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                    count = 0
                    for page in range(1, pages+1):
                        count += 1
                        new_dict = response.meta['new_dict'] | {'pageNo': str(page)}
                        yield scrapy.Request(url=self.domain_url, method='POST', callback=self.parse_data_check,
                                             body=json.dumps(new_dict), priority=((pages+1) - count) * 100,
                                             headers={'Content-Type': 'application/json;charset=UTF-8',
                                                      'new_dict': new_dict})

        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')


    def parse_data_check(self, response):
        try:
            if response.text:
                count = 0
                data_info = json.loads(response.text)['hits']['hits']
                for info in data_info:
                    count += 1
                    notice = self.get_category(info['_source']['pathName'])
                    pub_time = get_timestamp(info['_source']['publishDate'])
                    title_name = info['_source']['title']
                    info_url = self.start_urls + info['_source']['url']
                    yield scrapy.Request(url=info_url, callback=self.parse_item,
                                         priority=(len(data_info) - count) * 100,
                                         meta={'notice': notice,
                                               'title_name': title_name,
                                               'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = json.loads(response.xpath('//input[@name="articleDetail"]/@value').get())['content']
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = ''.join(response.meta['title_name'])
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title
                _, content = remove_specific_element(content, 'input', 'id', 'btnPrint')

                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.domain_url, origin, files_text, pub_time=pub_time, keys_a=keys_a)

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

    # cmdline.execute("scrapy crawl province_131_qinghai_spider".split(" "))
    cmdline.execute("scrapy crawl province_131_qinghai_spider -a sdt=2021-07-20 -a edt=2021-08-30".split(" "))
