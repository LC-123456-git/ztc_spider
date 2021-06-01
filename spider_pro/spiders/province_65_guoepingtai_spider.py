# -*- coding: utf-8 -*-
"""
@file          :province_65_guoepingtai_spider.py
@description   :国e平台
@date          :2021/06/01 08:46:51
@author        :miaokela
@version       :1.0
"""
import scrapy
import re
import requests
from lxml import etree
from datetime import datetime
import random
import time
import json

from spider_pro import items, constans, utils


class Province65GuoepingtaiSpiderSpider(scrapy.Spider):
    name = 'province_65_guoepingtai_spider'
    allowed_domains = ['www.ebidding.com']
    start_urls = ['http://www.ebidding.com/']
    query_url = 'https://www.ebidding.com/portal/announcement/ebd?type={sub_notice_code}&df=&department=' + \
                '&industry=&bidType={business_category_code}&guanjianzi=&openMode=&showDateSort=1&platformType=&_={now_time}&on=false&page={page}'
    detail_url = 'https://www.ebidding.com/portal/announcement/ebd/{sub_notice_code}/{et_id}/{html_content_id}/?_={now_time}'
    origin = 'https://www.ebidding.com/portal/html/index.html#page=main:notice_details?&tenderType={tender_type}&etId={et_id}&type={sub_notice_code}&htmlContentId={html_content_id}&platform={platform}&_={now_time}'
    area_id = 65
    basic_area = '广东省-国e平台'
    keywords_map = {
        '资格审查': '资格预审结果公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
    }
    notices_type_map = {
        '招标公告': '10',
        '资格预审': '70',
        '预审结果': '60',
        '更正公告': '20',
        '终止公告': '40',
        '中标候选人公示': '50',
        '中标结果公告': '80',
        '中标结果公示': '30',
    }
    notices_type_map = {
        '招标公告': {
            'notice_type': '招标公告',
            'sub_notice_code': '10',
        },
        '资格预审': {
            'notice_type': '资格预审公告',
            'sub_notice_code': '70',
        },
        '预审结果': {
            'notice_type': '资格预审公告',
            'sub_notice_code': '60',
        },
        '更正公告': {
            'notice_type': '招标变更',
            'sub_notice_code': '20',
        },
        '终止公告': {
            'notice_type': '招标异常',
            'sub_notice_code': '40',
        },
        '中标候选人公示': {
            'notice_type': '中标预告',
            'sub_notice_code': '50',
        },
        '中标结果公告': {
            'notice_type': '中标公告',
            'sub_notice_code': '80',
        },
        '中标结果公示': {
            'notice_type': '中标公告',
            'sub_notice_code': '30',
        },
    }

    business_category_map = {
        '货物': '10',
        '工程': '20',
        '服务': '30',
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
        for keywords, value in self.keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def judge_in_interval_from_json(self, url, resp=None):
        status = 0
        headers = Province65GuoepingtaiSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                content = requests.get(url=url, headers=headers).content.decode('utf-8')

                data = json.loads(content)

                code = data.get('code', '')
                if code == 0:
                    result = data.get('result', {})
                    content_list = result.get('content', [])
                    first_pub_time = content_list[0].get('showDate', '')
                    final_pub_time = content_list[-1].get('showDate', '')

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
        for nt, ntv in self.notices_type_map.items():
            for bc, bcv in self.business_category_map.items():
                notice_type = ntv.get('notice_type', '')
                sub_notice_code = ntv.get('sub_notice_code', '')

                c_url = self.query_url.format(**{
                    'sub_notice_code': sub_notice_code,
                    'business_category_code': bcv,
                    'now_time': int(time.time()),
                    'page': 1,
                })
                yield scrapy.Request(url=c_url, callback=self.get_max_page, meta={
                    'sub_notice_type': nt,
                    'notice_type': notice_type,
                    'business_category': bc,
                    'sub_notice_code': sub_notice_code,
                    'business_category_code': bcv,
                })

    def get_max_page(self, resp):
        data = json.loads(resp.text)
        code = data.get('code', '')
        if code == 0:
            result = data.get('result', {})
            max_page = result.get('totalPages', 0)
            for page in range(1, max_page + 1):
                c_url = self.query_url.format(**{
                    'sub_notice_code': resp.meta.get('sub_notice_code', ''),
                    'business_category_code': resp.meta.get('business_category_code', ''),
                    'now_time': int(time.time()),
                    'page': page,
                })
                judge_status = self.judge_in_interval_from_json(c_url, resp)
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, dont_filter=True, 
                        priority=(max_page-page) * 10, meta={
                            'notice_type': resp.meta.get('notice_type', ''),
                            'sub_notice_code': resp.meta.get('sub_notice_code', ''),
                            'business_category': resp.meta.get('business_category', ''),
                        }
                    )

    def parse_list(self, resp):
        """
        https://www.ebidding.com/portal/announcement/ebd/公告类型/etId/htmlContentId/?_=1622506725180

        origin = 'https://www.ebidding.com/portal/html/index.html#page=main:notice_details?&tenderType={tender_type}&etId={et_id}&type{sub_notice_code}&htmlContentId={html_content_id}&platform={platform}&_={now_time}'
        """
        data = json.loads(resp.text)
        code = data.get('code', '')
        sub_notice_code = resp.meta.get('sub_notice_code', '')
        if code == 0:
            result = data.get('result', {})
            content_list = result.get('content', [])
            for n, content in enumerate(content_list):
                et_id = content.get('etId', '')
                html_content_id = content.get('htmlContentId', '')
                now_time = int(time.time())
                # YEILD ORIGIN BY tenderType|platformType|etId|htmlContentId|now_time
                tender_type = content.get('tenderType', '')
                platform_type = content.get('platformType', '')

                origin = self.origin.format(**{
                    'tender_type': tender_type,
                    'et_id': et_id,
                    'sub_notice_code': sub_notice_code,
                    'html_content_id': html_content_id,
                    'platform': platform_type,
                    'now_time': now_time,
                })

                c_url = self.detail_url.format(**{
                    'sub_notice_code': sub_notice_code,
                    'et_id': et_id,
                    'html_content_id': html_content_id,
                    'now_time': now_time,
                })

                yield scrapy.Request(url=c_url, callback=self.parse_detail, meta={
                    'notice_type': resp.meta.get('notice_type', ''), 
                    'business_category': resp.meta.get('business_category', ''),
                    'origin': origin,
                }, dont_filter=True, priority=(len(content_list) - n) * 1000)

    def parse_detail(self, resp):
        data = json.loads(resp.text)
        code = data.get('code', '')
        if code == 0:
            result = data.get('result', {})

            title_name = result.get('title', '')
            content = result.get('htmlContent', '').replace('\n', '').replace('\r\n', '').replace('\t', '')
            pub_time = result.get('showDate', '')

            notice_type_ori = resp.meta.get('notice_type')

            # 关键字重新匹配 notice_type
            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )

            # 匹配文件
            _, files_path = utils.catch_files(content, self.query_url)

            notice_item = items.NoticesItem()

            notice_item.update(**{
                'origin': resp.meta.get('origin'),
                'title_name': title_name,
                'pub_time': pub_time,
                'info_source': self.basic_area,
                'is_have_file': constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE,
                'files_path': files_path,
                'notice_type': notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE,
                'content': content,
                'area_id': self.area_id,
                'business_category': resp.meta.get('business_category'),
            })

            print(pub_time, resp.url)
            return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute(
        "scrapy crawl province_65_guoepingtai_spider -a sdt=2021-01-01 -a edt=2021-05-17".split(" ")
    )
    # cmdline.execute("scrapy crawl province_65_guoepingtai_spider".split(" "))








