#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-10-19
# @Describe: 兵团政府采购网
import copy
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
     get_files, get_notice_type, remove_specific_element, get_timestamp


class Province146BingTuanSpider(CrawlSpider):
    name = 'province_146_bingtuan_spider'
    allowed_domains = ['ccgp-bingtuan.gov.cn']
    start_urls = 'http://ccgp-bingtuan.gov.cn'
    domain_url = ''
    base_url = 'http://ccgp-bingtuan.gov.cn/front/search/category'
    query_url = ''
    area_id = "146"
    area_province = '兵团政府采购网'

    # 招标预告
    list_tender_notice_name = {'采购意向': 'ZcyAnnouncement11', '采购文件需求公示': 'ZcyAnnouncement3014'}
    # 招标公告
    list_notice_category_name = {'单一来源公示': 'ZcyAnnouncement3012', '采购项目公告': 'ZcyAnnouncement2'}
    # 招标变更
    list_zb_abnormal_name = {"澄清变更公告": 'ZcyAnnouncement3'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'采购结果公告': 'ZcyAnnouncement4'}
    # 招标异常
    list_alteration_category_name = {'废标公告': 'ZcyAnnouncement10'}
    # 资格预审
    list_qualifiction_advance_num = {}
    # 其他
    list_qita_num = {'采购合同公告': 'ZcyAnnouncement5', '电子卖场公告': 'ZcyAnnouncement8'}
    
    all_list_dict = {**list_tender_notice_name, **list_notice_category_name, **list_zb_abnormal_name,
                     **list_win_notice_category_name, **list_alteration_category_name, **list_qita_num}

    r_dict = {"districtCode": ["660000"], "categoryCode": "ZcyAnnouncement3012", "pageSize": '15', "pageNo": '1'}

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
        super(Province146BingTuanSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for key, value in zip(self.all_list_dict.keys(), self.all_list_dict.values()):
            notice = self.get_category(key)
            new_dict = self.r_dict | {'categoryCode': value}
            yield scrapy.Request(url=self.base_url, callback=self.parse_data, dont_filter=True,
                                 headers={'Content-Type': 'application/json'},
                                 body=json.dumps(new_dict), method='POST',
                                 meta={'notice': notice,  '_dict': new_dict})

    def parse_data(self, response):
        try:
            if json.loads(response.text):
                info_data = json.loads(response.text)['hits']
                if self.enable_incr:
                    count = 0
                    num = 0
                    for info in info_data['hits']:
                        count += 1
                        info_url = self.start_urls + info['_source']['url']
                        title_name = info['_source']['title']
                        pub_time = get_timestamp(info['_source']['publishDate'])
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                                 priority=(len(info_data['hits']) - count) * 100,
                                                 meta={'notice': response.meta['notice'],
                                                       'title_name': title_name,
                                                       'pub_time': pub_time})
                        if num >= int(len(info_data['hits'])):
                            total = int(len(info_data['hits']))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            page = int(response.meta['_dict']['pageNo']) + 1
                            new_dict = response.meta['_dict'] | {"pageNo": str(page)}
                            yield scrapy.Request(url=self.base_url, callback=self.parse_data, method='post',
                                                 headers={'Content-Type': 'application/json'},
                                                 body=json.dumps(new_dict), dont_filter=True,
                                                 meta={'notice': response.meta['notice'],
                                                       'new_dict': new_dict})
                else:
                    total = info_data['total']
                    pages = math.ceil(total / 50)
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                    count = 0
                    for page in range(pages):
                        count += 1
                        new_dicts = response.meta['_dict'] | {'pageNo': str(page)}
                        yield scrapy.Request(url=self.base_url, callback=self.parse_data_check, method='post',
                                             dont_filter=True,  headers={'Content-Type': 'application/json'},
                                             body=json.dumps(new_dicts), priority=((pages + 1) - count) * 50,
                                             meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')

    def parse_data_check(self, response):
        try:
            if json.loads(response.text):
                info_data = json.loads(response.text)['hits']
                count = 0
                for info in info_data['hits']:
                    count += 1
                    title_name = info['_source']['title']
                    pub_time = get_timestamp(info['_source']['publishDate'])
                    info_url = self.start_urls + info['_source']['url']
                    yield scrapy.Request(url=info_url, callback=self.parse_item,
                                         priority=(len(info_data['hits']) - count) * 100,
                                         meta={'notice': response.meta['notice'],
                                               'title_name': title_name,
                                               'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            category = '政府采购'
            origin = response.url
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            content = json.loads(response.xpath('//div[@class="xinjiangbingtuan-detail js-comp"]/input/@value').get())['content']
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                                       keys_a=keys_a, log=self.logger)

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
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_item {e}, {response.meta["info_url"]}')



if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_146_bingtuan_spider".split(" "))
    # cmdline.execute("scrapy crawl province_146_bingtuan_spider -a sdt=2021-09-01 -a edt=2021-10-20".split(" "))
