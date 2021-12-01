# -*- coding: utf-8 -*-
"""
@file           :province_3101_shanghaigov_spider.py
@description    :上海市-上海政府采购网
@date           :2021/06/15 10:53:59
@author         :miaokela
@version        :1.0
"""
import scrapy
import re
import time
import requests
import random
import json
import math
from datetime import datetime
from collections import OrderedDict

from spider_pro import items, constans, utils


class Province3101ShanghaigovSpiderSpider(scrapy.Spider):
    name = 'province_3101_shanghaigov_spider'
    allowed_domains = ['ccgp-shanghai.gov.cn']
    start_urls = ['http://ccgp-shanghai.gov.cn/']
    area_id = 3101
    basic_area = '上海市政府采购网'
    # basic_area = '上海市{district_name}-上海政府采购网'
    base_url = 'http://www.ccgp-shanghai.gov.cn'
    query_url = 'http://www.ccgp-shanghai.gov.cn/front/search/category'
    notice_keywords_map = OrderedDict({
        '采购意向': '招标预告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    })
    formdata_map = {
        "招标预告": [
            {"categoryCode": "ZcyAnnouncement10016", "pageSize": "15", "pageNo": "1"},
        ],
        "招标公告": [
            {"categoryCode": "ZcyAnnouncement1", "pageSize": "15", "pageNo": "1"},
            {"categoryCode": "ZcyAnnouncement2", "pageSize": "15", "pageNo": "1"},
        ],
        "招标变更": [
            {"categoryCode": "ZcyAnnouncement3", "pageSize": "15", "pageNo": "1"},
        ],
        "招标异常": [
            {"categoryCode": "ZcyAnnouncement6", "pageSize": "15", "pageNo": "1"},
        ],
        "中标公告": [
            {"categoryCode": "ZcyAnnouncement4", "pageSize": "15", "pageNo": "1"},
        ],
        "其他公告": [
            {"categoryCode": "ZcyAnnouncement5", "pageSize": "15", "pageNo": "1"},
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

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
        for keywords, value in self.notice_keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def judge_in_interval_from_json(self, url, formdata=None, resp=None):
        status = 0
        headers = Province3101ShanghaigovSpiderSpider.get_headers(resp)
        headers.update(**{
            'Content-Type': 'application/json',
        })
        if all([self.start_time, self.end_time]):
            try:
                content = requests.post(url=url, data=formdata, headers=headers).content.decode('utf-8')

                data = json.loads(content)

                hits = data.get('hits', {})

                content_list = hits.get('hits', [])

                first_pub_time = time.strftime("%Y-%m-%d", time.localtime(
                    content_list[0].get('_source', '').get('publishDate', '') / 1000
                )
                                               )
                final_pub_time = time.strftime("%Y-%m-%d", time.localtime(
                    content_list[-1].get('_source', '').get('publishDate', '') / 1000
                )
                                               )

                if all([first_pub_time, final_pub_time]):
                    first_pub_time = datetime.strptime(first_pub_time, '%Y-%m-%d')
                    final_pub_time = datetime.strptime(final_pub_time, '%Y-%m-%d')
                    start_time = datetime.strptime(self.start_time, '%Y-%m-%d')
                    end_time = datetime.strptime(self.end_time, '%Y-%m-%d')
                    # 比最大时间大 continue
                    # 比最小时间小 break
                    # 1 首条在区间内 可抓、可以翻页
                    # 0 首条不在区间内 停止翻页
                    # 2 末条大于最大时间 continue
                    if first_pub_time < start_time:
                        status = 0
                    elif final_pub_time > end_time:
                        status = 2
                    else:
                        status = 1

            except Exception as e:
                self.log(e)
        else:
            status = 1  # 没有传递时间
        return status

    def start_requests(self):
        for notice_type, formdata_list in self.formdata_map.items():
            for formdata in formdata_list:
                yield scrapy.Request(url=self.query_url, method='POST', body=json.dumps(formdata), meta={
                    'notice_type': notice_type,
                    'formdata': formdata,
                }, headers={
                    'Content-Type': 'application/json',
                }, callback=self.get_max_page, dont_filter=True)

    def get_max_page(self, resp):
        """
        {
            "took": 13,
            "timed_out": false,
            "_shards": {
                "total": 2,
                "successful": 2,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": 7443,
                "max_score": null,
                "hits": [
                    {
                        "_index": "prod-articles-77",
                        "_type": "prod-article-77",
                        "_id": "1256574",
                        "_score": null,
                        "_source": {
                            "pathName": "采购意向公开",
                            "districtName": "嘉定区",
                            "articleId": 1256574,
                            "publishDate": 1623723582709,
                            "invalid": 0,
                            "siteId": 77,
                            "title": "嘉定新城（马陆镇）城市建设管理办公室2021年6月至7月政府采购意向",
                            "url": "/ZcyAnnouncement10016/Dro9u0cHhVKkutzEzyzpVw==.html"
                        },
                        "sort": [
                            1623723582709,
                            "1256574"
                        ]
                    }
                    ...
                ]
            }
        }
        """
        formdata = resp.meta.get('formdata', {})
        ret = json.loads(resp.text)

        hits = ret.get('hits', {})
        total_record = hits.get('total', 0)

        try:
            max_pages = math.ceil(int(total_record) // 15)
        except Exception as e:
            self.logger.info('error:{0}'.format(e))
        else:
            for page in range(1, max_pages + 1):
                formdata['pageNo'] = str(page)
                # 请求当前页 判断时间区间
                judge_status = self.judge_in_interval_from_json(resp.url, formdata=json.dumps(formdata), resp=resp)

                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(url=self.query_url, method='POST', body=json.dumps(formdata), meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                    }, headers={
                        'Content-Type': 'application/json',
                    }, callback=self.parse_list, dont_filter=True, priority=10 * (max_pages - page))

    def parse_list(self, resp):
        data = json.loads(resp.text)

        hits = data.get('hits', {})

        content_list = hits.get('hits', [])

        for n, row in enumerate(content_list):
            source = row.get('_source', {})
            title_name = source.get('title', '')
            c_url = source.get('url', '')
            district_name = source.get('districtName', '')
            pub_time = time.strftime("%Y-%m-%d", time.localtime(
                source.get('publishDate', '') / 1000
            )
                                     )

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                c_url = ''.join([self.base_url, c_url])
                yield scrapy.Request(url=c_url, meta={
                    'notice_type': resp.meta.get('notice_type', ''),
                    'title_name': title_name,
                    'pub_time': pub_time,
                    'district_name': district_name,
                }, callback=self.parse_detail, priority=100000 * (len(content_list) - n))

    def parse_detail(self, resp):
        content_el = resp.xpath('//input[@name="articleDetail"]/@value').get()
        content_el = utils.avoid_escape(content_el)
        district_name = resp.meta.get('district_name', '')

        try:
            content_el = json.loads(content_el)
            content = content_el.get('content', '')
        except Exception as e:
            self.logger.info({'error:{0}'.format(e)})
        else:
            title_name = resp.meta.get('title_name')
            notice_type_ori = resp.meta.get('notice_type')

            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )
            # REMOVE DATE
            _, content = utils.remove_specific_element(content, 'p', 'class', 'detail-info')
            # 投标文件
            _, files_path = utils.catch_files(content, self.base_url, resp=resp)

            notice_item = items.NoticesItem()
            notice_item["origin"] = resp.url
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = resp.meta.get('pub_time')
            notice_item["info_source"] = self.basic_area.format(
                district_name='-%s' % district_name if district_name else '')
            notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = files_path
            notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = '采购'
            print(resp.meta.get('pub_time'), resp.url)
            return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute(
        "scrapy crawl province_3101_shanghaigov_spider -a sdt=2021-06-11 -a edt=2021-06-15".split(" ")
    )
    # cmdline.execute("scrapy crawl province_3101_shanghaigov_spider".split(" "))
