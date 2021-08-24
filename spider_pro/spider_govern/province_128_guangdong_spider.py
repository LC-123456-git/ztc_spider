# -*- coding: utf-8 -*-
# @file           :province_128_guangdong_spider.py
# @description    :黑龙江省政府采购网
# @date           :2021/08/24
# @author         :miaokela
# @version        :1.0
import json
import math
import re
import random
import requests
from datetime import datetime
from lxml import etree

import scrapy

from spider_pro import utils, constans, items


class Province128GuangdongSpiderSpider(scrapy.Spider):
    name = 'province_128_guangdong_spider'
    allowed_domains = ['gdgpo.czt.gd.gov.cn']
    start_urls = ['http://gdgpo.czt.gd.gov.cn/']

    basic_area = '广东省政府采购网'
    query_url = 'https://gdgpo.czt.gd.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do?'
    base_url = 'http://gdgpo.czt.gd.gov.cn'

    area_id = 128
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

        start_time = '%20'.join([self.start_time, '00:00:00']) if self.start_time else ''
        end_time = '%20'.join([self.end_time, '11:59:59']) if self.end_time else ''

        self.page_size = 10
        self.url_map = {
            '招标预告': [
                # 采购意向公开
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=59&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 采购计划
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001101&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 采购需求
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001059&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '招标公告': [
                # 采购公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=00101&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 单一来源公示
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001051&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 采购公告 电子卖场公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=3b49b9ba-48b6-4220-9e8b-eb89f41e9d66'
                              '&currPage={curr_page}&pageSize=%d&noticeType=201022,201023,201111,00107D&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 采购公告 批量采购
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=751c7726-20a2-47f2-b190-206ae6e9cd89'
                              '&currPage={curr_page}&pageSize=%d&noticeType=00107H&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '资格预审结果公告': [
                # 资格预审结果公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001052,001053&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '招标变更': [
                # 更正公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=00103&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 电子卖场公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=3b49b9ba-48b6-4220-9e8b-eb89f41e9d66'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001071&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '招标异常': [
                # 终止公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001004,001006&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 终止公告 电子卖场公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=3b49b9ba-48b6-4220-9e8b-eb89f41e9d66'
                              '&currPage={curr_page}&pageSize=%d&noticeType=204022,204023,204111,204112&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '中标公告': [
                # 中标（成交）结果公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=00102&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
            '其他公告': [
                # 合同公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=fca71be5-fc0c-45db-96af-f513e9abda9d'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001054&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
                # 合同公告 电子卖场公告
                {
                    'params': 'siteId=cd64e06a-21a7-4620-aebc-0576bab7e07a&channel=3b49b9ba-48b6-4220-9e8b-eb89f41e9d66'
                              '&currPage={curr_page}&pageSize=%d&noticeType=001054&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                },
            ],
        }

    def match_title(self, title_name):
        """
        根据标题匹配关键字 返回招标类别
        Args:
            title_name: 标题

        Returns:
            notice_type: 招标类别
        """
        matched = False
        notice_type = ''
        for keywords, value in self.keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def start_requests(self):
        for notice_type, param_dics in self.url_map.items():
            for param_dic in param_dics:
                params = param_dic['params']
                yield scrapy.Request(url=''.join([
                    self.query_url, params.format(curr_page=1)
                ]), callback=self.parse_list, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'params': params,
                }, headers={
                    'Content-Type': 'application/json',
                }, dont_filter=True)

    def parse_list(self, resp, params):
        txt = resp.text
        try:
            data = json.loads(txt)
        except Exception as e:
            self.logger.info(e)
        else:
            total_records = data.get('total', 0)
            max_page = math.ceil(total_records / self.page_size)

            for page in range(1, max_page + 1):
                # for page in range(1, 2):
                c_url = ''.join([self.query_url, params.format(curr_page=page)])

                yield scrapy.Request(url=c_url, callback=self.parse_urls, meta=resp.meta, headers={
                    'Content-Type': 'application/json',
                }, priority=max_page - page, dont_filter=True)

    def parse_urls(self, resp):
        txt = resp.text
        try:
            data = json.loads(txt)
        except Exception as e:
            self.logger.info(e)
        else:
            url_info_list = data.get('data', [])

            for n, url_info in enumerate(url_info_list):
                page_url = url_info.get('pageurl', '')
                title_name = url_info.get('title', '')
                pub_time = url_info.get('addtimeStr', '')

                c_url = ''.join([self.base_url, page_url])

                resp.meta.update(**{
                    'title_name': title_name,
                    'pub_time': pub_time,
                })
                yield scrapy.Request(
                    url=c_url, callback=self.parse_detail, meta=resp.meta,
                    priority=(len(url_info_list) - n) * 10000
                )

    def parse_detail(self, resp):
        title_name = resp.meta.get('title_name', '')
        pub_time = resp.meta.get('pub_time', '')
        notice_type_ori = resp.meta.get('notice_type', '')

        content = resp.xpath('//div[contains(@class, "info-article")]').get()

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, pub_time=pub_time, resp=resp)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name.strip() if title_name else ''
        notice_item["pub_time"] = pub_time

        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = '政府采购'
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_128_guangdong_spider -a sdt=2021-06-01 -a edt=2021-08-16".split(" "))
    # cmdline.execute("scrapy crawl province_128_guangdong_spider".split(" "))
