# -*- coding: utf-8 -*-
# @file           :province_124_jilin_spider.py
# @description    :黑龙江省政府采购网
# @date           :2021/08/16
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


class Province123HeilongjiangSpiderSpider(scrapy.Spider):
    name = 'province_123_heilongjiang_spider'
    allowed_domains = ['ccgp-heilongj.gov.cn', 'hljcg.hlj.gov.cn']
    start_urls = ['http://www.ccgp-heilongj.gov.cn/']

    basic_area = '黑龙江省政府采购网'
    query_url = 'http://www.ccgp-heilongj.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do?'
    base_url = 'http://www.ccgp-heilongj.gov.cn'
    detail_url = 'http://hljcg.hlj.gov.cn/proxy/platform/platform/notice/queryMallNoticeById?platformId=20&id={id}'

    area_id = 123
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
            # '招标预告': [
            #     # 采购需求公告(例外)
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=001072&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': True,
            #     },
            #     # 采购需求和意向公开
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=59&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            # ],
            '招标公告': [
                # 采购公告 项目采购公告
                {
                    'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
                              '&currPage={curr_page}&pageSize=%d&noticeType=00101&operationStartTime=%s'
                              '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                    'is_json_detail': False,
                },
                # # 采购公告 定点采购公告
                # {
                #     'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
                #               '&currPage={curr_page}&pageSize=%d&noticeType=00107D,201111&operationStartTime=%s'
                #               '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                #     'is_json_detail': False,
                # },
                # # 单一来源公示
                # {
                #     'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
                #               '&currPage={curr_page}&pageSize=%d&noticeType=001051&operationStartTime=%s'
                #               '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
                #     'is_json_detail': False,
                # },
            ],
            # '招标变更': [
            #     # 更正公告 项目采购公告
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=00103&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            #     # 中标（成交）更正公告 项目采购公告
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=001032&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            # ],
            # '招标异常': [
            #     # 废标（终止）公告
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=001004,001006&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            # ],
            # '中标公告': [
            #     # 中标（成交）公告
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=00102&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            #     # 结果公告
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=001076&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': False,
            #     },
            #     # 采购成交公告(例外)
            #     {
            #         'params': 'siteId=94c965cc-c55d-4f92-8469-d5875c68bd04&channel=c5bff13f-21ca-4dac-b158-cb40accd3035'
            #                   '&currPage={curr_page}&pageSize=%d&noticeType=001073&operationStartTime=%s'
            #                   '&operationEndTime=%s&selectTimeName=noticeTime' % (self.page_size, start_time, end_time),
            #         'is_json_detail': True,
            #     },
            # ],
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
                is_json_detail = param_dic['is_json_detail']
                yield scrapy.Request(url=''.join([
                    self.query_url, params.format(curr_page=1)
                ]), callback=self.parse_list, meta={
                    'notice_type': notice_type,
                    'is_json_detail': is_json_detail,
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
            is_json_detail = resp.meta.get('is_json_detail', False)

            if is_json_detail:
                for n, url_info in enumerate(url_info_list):
                    page_url = url_info.get('pageurl', '')
                    field_values = url_info.get('fieldValues', {})
                    title_name = field_values.get('f_noticeName', '')
                    pub_time = field_values.get('f_noticeTime', '')

                    p_com = re.compile(r'(\d+)\.html')
                    notice_ids = p_com.findall(page_url)
                    if notice_ids:
                        notice_id = notice_ids[0]
                        c_url = self.detail_url.format(id=notice_id)
                        resp.meta.update(**{
                            'title_name': title_name,
                            'pub_time': pub_time,
                        })
                        yield scrapy.Request(
                            url=c_url, callback=self.parse_detail, meta=resp.meta, dont_filter=True,
                            priority=(len(url_info_list) - n) * 10000
                        )
            else:
                for n, url_info in enumerate(url_info_list):
                    page_url = url_info.get('pageurl', '')
                    field_values = url_info.get('fieldValues', {})
                    title_name = field_values.get('f_noticeName', '')
                    pub_time = field_values.get('f_noticeTime', '')

                    c_url = ''.join([self.base_url, page_url])

                    resp.meta.update(**{
                        'title_name': title_name,
                        'pub_time': pub_time,
                    })
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_detail, meta=resp.meta, dont_filter=True,
                        priority=(len(url_info_list) - n) * 10000
                    )

    def parse_detail(self, resp):
        title_name = resp.meta.get('title_name', '')
        pub_time = resp.meta.get('pub_time', '')
        notice_type_ori = resp.meta.get('notice_type', '')
        is_json_detail = resp.meta.get('is_json_detail', False)

        if is_json_detail:
            try:
                content = json.loads(resp.text).get('data', {}).get('contentStr', '')
                _, content = utils.remove_element_by_xpath(
                    content,
                    xpath_rule='//div[contains(@class, "bid-purchase")]/div[last()]'
                )
            except Exception as e:
                self.logger.info(e)
                content = ''
        else:
            content = resp.xpath('//div[@class="noticeArea" or @id="noticeArea"]').get()
            
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//div[@id="noticeArea"]/div[position()=1]'
        )
        
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

    cmdline.execute("scrapy crawl province_123_heilongjiang_spider -a sdt=2021-06-01 -a edt=2021-08-16".split(" "))
    # cmdline.execute("scrapy crawl province_123_heilongjiang_spider".split(" "))
