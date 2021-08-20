# -*- coding: utf-8 -*-
# @file           :province_124_jilin_spider.py
# @description    :吉林省政府采购网
# @date           :2021/08/16
# @author         :miaokela
# @version        :1.0
import re
import random
import requests
from datetime import datetime
from lxml import etree

import scrapy

from spider_pro import utils, constans, items


class Province124JilinSpiderSpider(scrapy.Spider):
    name = 'province_124_jilin_spider'
    allowed_domains = ['www.ccgp-jilin.gov.cn']
    start_urls = ['http://www.ccgp-jilin.gov.cn/']

    basic_area = '吉林省政府采购网'
    query_url = 'http://www.ccgp-jilin.gov.cn/shopHome/morePolicyNews.action'
    base_url = 'http://www.ccgp-jilin.gov.cn'

    area_id = 124
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标公告': [
            {'notice_type_id': '2', 'category_id': '124'},  # 省级 公开招标
            {'notice_type_id': '7', 'category_id': '124'},  # 省级 邀请招标
            {'notice_type_id': '4', 'category_id': '124'},  # 省级 竞争性谈判
            {'notice_type_id': '5', 'category_id': '124'},  # 省级 竞争性磋商
            {'notice_type_id': '6', 'category_id': '124'},  # 省级 单一来源
            {'notice_type_id': '3', 'category_id': '124'},  # 省级 询价公告

            {'notice_type_id': '2', 'category_id': '125'},  # 市级 公开招标
            {'notice_type_id': '7', 'category_id': '125'},  # 市级 邀请招标
            {'notice_type_id': '4', 'category_id': '125'},  # 市级 竞争性谈判
            {'notice_type_id': '5', 'category_id': '125'},  # 市级 竞争性磋商
            {'notice_type_id': '6', 'category_id': '125'},  # 市级 单一来源
            {'notice_type_id': '3', 'category_id': '125'},  # 市级 询价公告
        ],
        '中标公告': [
            {'notice_type_id': '9', 'category_id': '124'},  # 省级 中标公告
            {'notice_type_id': '10', 'category_id': '124'},  # 省级 成交公告

            {'notice_type_id': '9', 'category_id': '125'},  # 市级 中标公告
            {'notice_type_id': '10', 'category_id': '125'},  # 市级 成交公告
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

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
        for notice_type, params in self.url_map.items():
            for param in params:
                notice_type_id = param['notice_type_id']
                category_id = param['category_id']
                yield scrapy.FormRequest(url=self.query_url, formdata={
                    'currentPage': '1',
                    'noticetypeId': notice_type_id,
                    'categoryId': category_id,
                }, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'notice_type_id': notice_type_id,
                    'category_id': category_id,
                })

    def parse_list(self, resp, notice_type_id, category_id):
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        last_page_loca = resp.xpath('//form[@id="formModule"]/p/a[text()="末页"]/@onclick').get()
        notice_type = resp.meta.get('notice_type', '')
        com = re.compile(r'(\d+)')

        last_pages = com.findall(last_page_loca)
        if last_pages:
            max_page = last_pages[0]

            try:
                max_page = int(max_page)
            except Exception as e:
                print(e)
                max_page = 1
            c_form_data = {
                'noticetypeId': notice_type_id,
                'categoryId': category_id,
            }
            if all([self.start_time, self.end_time]):
                for page in range(1, max_page + 1):
                    c_form_data['currentPage'] = str(page)
                    judge_status = utils.judge_in_interval(
                        self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST',
                        data=c_form_data, proxies=proxies, headers=headers,
                        rule='//div[@id="list_right"]//li/span[last()]/text()[not(normalize-space()="")]'
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        yield scrapy.FormRequest(
                            url=self.query_url, formdata=c_form_data, callback=self.parse_urls, meta={
                                'notice_type': notice_type,
                            }, dont_filter=True, priority=max_page - page)
            else:
                for page in range(1, max_page + 1):
                    c_form_data['currentPage'] = str(page)
                    yield scrapy.FormRequest(url=self.query_url, formdata=c_form_data, callback=self.parse_urls, meta={
                        'notice_type': notice_type,
                    }, dont_filter=True, priority=max_page - page)

    def parse_urls(self, resp):
        li_els = resp.xpath('//div[@id="list_right"]/ul/li')

        for n, li in enumerate(li_els):
            href = li.xpath('./a/@href').get()
            pub_time = li.xpath('./span/text()').get()

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                yield scrapy.Request(url=''.join([self.base_url, href]), callback=self.parse_detail, meta={
                    'notice_type': resp.meta.get('notice_type'),
                    'pub_time': pub_time,
                }, priority=(len(li_els) - n) * 10000, dont_filter=True)

    def parse_detail(self, resp):
        content = resp.xpath('//div[@id="xiangqingneiron"]').get()
        title_name = resp.xpath('//h2[position()=1]/font/text()').get()
        pub_time = resp.meta.get('pub_time')
        notice_type_ori = resp.meta.get('notice_type')

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 移除不必要信息
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//h2[position()=1]/font'
        )  # 标题
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//h3[position()=1]/span'
        )  # 日期

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

    cmdline.execute("scrapy crawl province_124_jilin_spider -a sdt=2021-06-01 -a edt=2021-08-20".split(" "))
    # cmdline.execute("scrapy crawl province_124_jilin_spider".split(" "))
