# -*- coding: utf-8 -*-
# @file           :province_142_xizang_province_spider.py
# @description    :西藏政府采购网
# @date           :2021/10/19 11:33:01
# @author         :miaokela
# @version        :1.0
import json
import math
import re

from spider_pro import constans, utils, items
import scrapy


class Province142XizangProvinceSpiderSpider(scrapy.Spider):
    name = 'province_142_xizang_province_spider'
    allowed_domains = ['ccgp-xizang.gov.cn']
    start_urls = ['http://ccgp-xizang.gov.cn/']

    basic_area = '西藏政府采购网'
    area_id = 142
    base_url = 'http://ccgp-xizang.gov.cn'

    PAGE_SIZE = 60
    query_url = 'http://www.ccgp-xizang.gov.cn/freecms/rest/v1/notice/selectInfoMoreChannel.do?' \
                '&siteId=18de62f0-2fb0-4187-a6c1-cd8fcbfb4585&channel=b541ffff-03ee-4160-be64-b11ccf79660d' \
                '&currPage={cur_page}&pageSize=%d&noticeType={notice_type_code}&cityOrArea=&noticeName=&operationStartTime=' \
                '&operationEndTime=&selectTimeName=noticeTime' % PAGE_SIZE

    url_map = {
        '招标预告': [
            {'notice_type_code': '59'},  # 采购意向公开
        ],
        '招标公告': [
            {'notice_type_code': '00101'},  # 采购公告
            {'notice_type_code': '001051'},  # 单一来源公示
        ],
        '招标变更': [
            {'notice_type_code': '001003,001031,001032'},  # 更正公告
        ],
        '招标异常': [
            {'notice_type_code': '001004,001006'},  # 废标（终止）公告
        ],
        '中标公告': [
            {'notice_type_code': '00102'},  # 中标（成交）公告
        ],
        '其他公告': [
            {'notice_type_code': '001052,001053,001055,001056,001057,001058,001059'},  # 其他公告
            {'notice_type_code': '001054'},  # 合同公告
        ]
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    custom_settings = {
        'CONCURRENT_REQUESTS': 1
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                notice_type_code = param.get('notice_type_code', '')
                c_url = self.query_url.format(
                    notice_type_code=notice_type_code,
                    cur_page=1
                )

                yield scrapy.Request(
                    url=c_url, callback=self.turn_page, meta={
                        'notice_type': notice_type,
                    }, cb_kwargs={
                        'notice_type_code': notice_type_code,
                    }, headers={
                        'Content-Type': 'application/json;charset=utf-8'
                    }
                )

    def turn_page(self, resp, notice_type_code):
        content = json.loads(resp.text)

        headers = utils.get_headers(resp)
        headers.update(**{
            'Content-Type': 'application/json'
        })
        proxies = utils.get_proxies(resp)

        total = content.get('total', 0)

        max_page = math.ceil(total / self.PAGE_SIZE)

        if all([self.start_time, self.end_time]):
            for i in range(max_page):
                c_url = self.query_url.format(
                    notice_type_code=notice_type_code,
                    cur_page=i + 1
                )
                judge_status = utils.judge_in_interval(
                    c_url, start_time=self.start_time, end_time=self.end_time, method='GET',
                    proxies=proxies, headers=headers,
                    rule='//fieldValues/f_noticeTime/text()', doc_type='json'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, meta=resp.meta,
                        headers={
                            'Content-Type': 'application/json;charset=utf-8'
                        }, priority=(max_page - i) * 10,
                        dont_filter=True
                    )
        else:
            for i in range(max_page):
                c_url = self.query_url.format(
                    notice_type_code=notice_type_code,
                    cur_page=i + 1
                )
                yield scrapy.Request(
                    url=c_url, callback=self.parse_list, meta=resp.meta,
                    headers={
                        'Content-Type': 'application/json;charset=utf-8'
                    }, priority=(max_page - i) * 10,
                    dont_filter=True
                )

    def parse_list(self, resp):
        content = json.loads(resp.text)
        result = content.get('data', [])

        for n, r in enumerate(result):
            field_values = r.get('fieldValues', {})
            if field_values:
                pub_time = field_values.get('f_noticeTime', '')
                title_name = r.get('title', '')
                html_path = r.get('htmlpath', '')
                c_url = ''.join([self.base_url, html_path])

                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    resp.meta.update(**{
                        'pub_time': pub_time,
                        'title_name': title_name
                    })
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_detail, meta=resp.meta,
                        priority=(len(result) - n) * 10 ** 6
                    )

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="wangedit"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, pub_time=pub_time, resp=resp)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name
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

    cmdline.execute("scrapy crawl province_142_xizang_province_spider -a sdt=2021-09-01 -a edt=2021-10-19".split(" "))
    # cmdline.execute("scrapy crawl province_142_xizang_spider".split(" "))
