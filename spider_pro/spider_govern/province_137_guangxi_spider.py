# -*- coding: utf-8 -*-
# @file           :province_137_guangxi_spider.py
# @description    :广西政府采购网
# @date           :2021/10/14 13:27:02
# @author         :miaokela
# @version        :1.0
import copy
from datetime import datetime
import json
import re
import math
from collections import OrderedDict

import scrapy

from spider_pro import utils, constans, items


class Province137GuangxiSpiderSpider(scrapy.Spider):
    name = 'province_137_guangxi_spider'
    allowed_domains = ['ccgp-guangxi.gov.cn']
    start_urls = ['http://www.ccgp-guangxi.gov.cn/']

    basic_area = '广西政府采购网'
    query_url = 'http://www.ccgp-guangxi.gov.cn/front/search/category'
    base_url = 'http://www.ccgp-guangxi.gov.cn'

    add_click_url = 'http://www.ccgp-guangxi.gov.cn/visitor/add-clicks'

    area_id = 137
    keywords_map = OrderedDict({
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    })
    notice_map = {
        '招标预告': [
            {
                'sub_notice': '招标文件预公示', 'category_code': 'ZcyAnnouncement5',
            },
        ],
        '招标公告': [
            {
                'sub_notice': '公开招标公告', 'category_code': 'ZcyAnnouncement3001',
            },
            {
                'sub_notice': '竞争性谈判公告', 'category_code': 'ZcyAnnouncement3002',
            },
            {
                'sub_notice': '询价公告', 'category_code': 'ZcyAnnouncement3003',
            },
            {
                'sub_notice': '竞争性磋商公告', 'category_code': 'ZcyAnnouncement3011',
            },
            {
                'sub_notice': '其他采购项目公告', 'category_code': 'ZcyAnnouncement2002',
            },
            {
                'sub_notice': '邀请招标公告', 'category_code': 'ZcyAnnouncement3020',
            },
            {
                'sub_notice': '单一来源公示', 'category_code': 'ZcyAnnouncement6',
            },
            {
                'sub_notice': '建设工程招标公告', 'category_code': 'ZcyAnnouncement8031',
            },
        ],
        '资格预审公告': [
            {
                'sub_notice': '公开招标资格预审公告', 'category_code': 'ZcyAnnouncement2001',
            },
            {
                'sub_notice': '邀请招标资格预审公告', 'category_code': 'ZcyAnnouncement3008',
            },
        ],
        '招标变更': [
            {
                'sub_notice': '更正公告', 'category_code': 'ZcyAnnouncement4',
            },
            {
                'sub_notice': '建设工程更正公告', 'category_code': 'ZcyAnnouncement8033',
            },
        ],
        '招标异常': [
            {
                'sub_notice': '废标公告', 'category_code': 'ZcyAnnouncement3007',
            },
            {
                'sub_notice': '终止公告', 'category_code': 'ZcyAnnouncement3015',
            },
        ],
        '中标公告': [
            {
                'sub_notice': '中标（成交）结果公告', 'category_code': 'ZcyAnnouncement3004',
            },
            {
                'sub_notice': '中标公告', 'category_code': 'ZcyAnnouncement4005',
            },
            {
                'sub_notice': '成交公告', 'category_code': 'ZcyAnnouncement4006',
            },
            {
                'sub_notice': '其他采购结果公告', 'category_code': 'ZcyAnnouncement4007',
            },
            {
                'sub_notice': '建设工程中标（成交）结果公告', 'category_code': 'ZcyAnnouncement8032',
            },
        ],
        '其他公告': [
            {
                'sub_notice': '合同公告', 'category_code': 'ZcyAnnouncement3',
            },
            {
                'sub_notice': '其他公告', 'category_code': 'ZcyAnnouncement9',
            },
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self.page_size = 15
        self._data = {
            "pageNo": 1,
            "pageSize": self.page_size,
            "categoryCode": "",
        }
        # acw_tc=76b20ff116343686876956180e43310a33cb1824fdc2ecfda288de93f3d3f2
        # acw_tc=76b20feb16343668739862834e311ca78a9db9e031f8a31843d88874b19a65
        self.cookies = {  # 携带Cookie即可
            'acw_tc': '76b20ffb16343650431205183e44ecce910ace15e292bb54562c54792ec089'
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

    @property
    def data(self):
        return copy.deepcopy(self._data)

    def start_requests(self):
        # utils.add_click(self.add_click_url, resp)
        for notice_type, sub_notice_info in self.notice_map.items():
            for sni in sub_notice_info:
                category_code = sni.get('category_code', '')

                c_data = self.data
                c_data['categoryCode'] = category_code
                yield scrapy.Request(
                    url=self.query_url, method='POST', callback=self.parse_list,
                    body=json.dumps(c_data), meta={
                        'notice_type': notice_type,
                    }, headers={
                        'Content-Type': 'application/json',
                    }, dont_filter=True, cb_kwargs={
                        'data': c_data,
                    },
                    # cookies=self.cookies,
                )

    def parse_list(self, resp, data):
        """
        翻页
        """
        # utils.add_click(self.add_click_url, resp)
        headers = utils.get_headers(resp)
        headers.update(**{
            # 'Cookie': ';'.join(['{0}={1}'.format(k, v) for k, v in self.cookies.items()]),
            'Content-type': 'Application/json'
        })
        proxies = utils.get_proxies(resp)

        content = json.loads(resp.text)

        hits = content.get('hits', {})
        total = hits.get('total', 0)
        max_page = math.ceil(total / self.page_size)

        if all([self.start_time, self.end_time]):
            for page in range(max_page):
                data['pageNo'] = page + 1

                judge_status = utils.judge_in_interval(
                    self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST',
                    data=json.dumps(data), proxies=proxies, headers=headers,
                    rule='//hits/hits/_source/publishDate/text()', doc_type='json', date_type='timestamp'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=self.query_url, method='POST', callback=self.parse_url,
                        body=json.dumps(data), meta=resp.meta, headers={
                            'Content-Type': 'application/json',
                        }, dont_filter=True,
                        # cookies=self.cookies,
                    )
        else:
            for page in range(max_page):
                data['pageNo'] = page + 1
                yield scrapy.Request(
                    url=self.query_url, method='POST', callback=self.parse_url,
                    body=json.dumps(data), meta=resp.meta, headers=headers, dont_filter=True,
                    cookies=self.cookies,
                )

    def parse_url(self, resp):
        """
        获取详情页链接
        """
        # utils.add_click(self.add_click_url, resp)
        content = json.loads(resp.text)

        hits = content.get('hits', {}).get('hits', [])

        for hit in hits:
            _source = hit.get('_source', {})
            c_url = _source.get('url', '')
            pub_time = _source.get('publishDate', '')
            article_id = _source.get('articleId', '')

            if pub_time:
                pub_time = '{0:%Y-%m-%d}'.format(datetime.fromtimestamp(int(pub_time) / 1000))
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    resp.meta.update(**{
                        'pub_time': pub_time,
                    })

                    yield scrapy.Request(
                        url=''.join([self.base_url, c_url]), callback=self.parse_detail,
                        meta=resp.meta, cb_kwargs={
                            'article_id': article_id,
                        },
                        # cookies=self.cookies,
                    )

    def parse_detail(self, resp, article_id):
        # utils.add_click(self.add_click_url, resp, **{'articleId': article_id})
        ret = resp.xpath('//input[@name="articleDetail"]/@value').get()
        ret = json.loads(ret)

        content = ret.get('content', '')
        title_name = ret.get('title', '')
        pub_time = resp.meta.get('pub_time', '')
        notice_type_ori = resp.meta.get('notice_type', '')

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

    cmdline.execute("scrapy crawl province_137_guangxi_spider -a sdt=2021-09-01 -a edt=2021-10-16".split(" "))
    # cmdline.execute("scrapy crawl province_137_guangxi_spider".split(" "))
