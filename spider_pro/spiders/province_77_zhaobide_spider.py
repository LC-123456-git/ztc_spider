# -*- coding: utf-8 -*-
"""
@file          :province_77_zhaobide_spider.py
@description   :浙江省-杭州市-招必得
@date          :2021/06/07 11:03:56
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
import copy
import json

from spider_pro import items, constans, utils


class Province77ZhaobideSpiderSpider(scrapy.Spider):
    name = 'province_77_zhaobide_spider'
    allowed_domains = ['www.zhaobide.com']
    start_urls = ['http://www.zhaobide.com/']
    area_id = 77
    basic_area = '浙江省-杭州市-招必得'
    notice_keywords_map = {
        '资格审查': '资格预审结果公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    base_url = 'https://www.zhaobide.com'
    query_url = 'https://www.zhaobide.com/Web/GetAfficheList_detail?afficheType={affiche_type}&type={type}'
    detail_url = 'https://www.zhaobide.com/Web/WebAfficheIndex?tenderID={tender_id}&afficheID={affiche_id}&moduleID={module_id}&afficheType={affiche_type}'
    bsniz_keywords_map = {
        '采购|购买': '采购',
    }
    params_map = {
        '招标公告': [
            {'affiche_type': 5, 'type': 0, 'has_module_id': True},  # 招标采购-招标公告
            {'affiche_type': 1, 'type': 1, 'has_module_id': False},  # 产权交易-交易公告
        ],
        '招标变更': [
            {'affiche_type': 6, 'type': 0, 'has_module_id': True},  # 招标采购-更正答疑
            {'affiche_type': 2, 'type': 1, 'has_module_id': False},  # 产权交易-更正答疑
        ],
        '招标异常': [
            {'affiche_type': 11, 'type': 0, 'has_module_id': True},  # 招标采购-废标公告
        ],
        '中标预告': [
            {'affiche_type': 7, 'type': 0, 'has_module_id': True},  # 招标采购-中标候选人公示
        ],
        '中标公告': [
            {'affiche_type': 8, 'type': 0, 'has_module_id': True},  # 招标采购-中标结果公告
            {'affiche_type': 3, 'type': 1, 'has_module_id': False},  # 产权交易-成交结果公告
        ],
    }
    _post_data = {
        'filter': '',
        '_search': 'false',
        'nd': '',
        'rows': '10',
        'page': '1',
        'sidx': 'PublishStartTime',
        'sord': 'desc',
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

    def match_bsniz_category(self, title_name):
        """
        根据标题去匹配，招标公告中带（采购、购买）关键词的，匹配项目类型为采购，其余为工程
        """
        matched = False
        notice_type = ''
        for keywords, value in self.bsniz_keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def judge_in_interval_from_json(self, url, formdata=None, resp=None):
        status = 0
        headers = Province77ZhaobideSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                content = requests.post(url=url, data=formdata, headers=headers).content.decode('utf-8')

                data = json.loads(content)

                error = data.get('error', '')
                if not error:
                    content_list = data.get('rows', [])
                    first_pub_time = '{0:%Y-%m-%d}'.format(datetime.strptime(
                        content_list[0].get('PublishStartTime', ''), '%Y-%m-%d %H:%M:%S'
                    ))
                    final_pub_time = '{0:%Y-%m-%d}'.format(datetime.strptime(
                        content_list[-1].get('PublishStartTime', ''), '%Y-%m-%d %H:%M:%S'
                    ))

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

    @property
    def post_data(self):
        return copy.deepcopy(self._post_data)

    def start_requests(self):
        for pm, params in self.params_map.items():
            for param in params:
                affiche_type = param.get('affiche_type', '')
                type = param.get('type', '')
                has_module_id = param.get('has_module_id', '')

                c_url = self.query_url.format(**{
                    'affiche_type': affiche_type,
                    'type': type,
                })

                yield scrapy.FormRequest(url=c_url, formdata=self.post_data, callback=self.turn_pages, meta={
                    'notice_type': pm,
                    'has_module_id': has_module_id,
                }, cb_kwargs={
                    'url': c_url,
                })

    def turn_pages(self, resp, url):
        """
        TURN PAGES
        """
        data = json.loads(resp.text)
        error = data.get('error', '')
        if not error:
            max_page = data.get('total', 0)
            for page in range(1, max_page + 1):
                post_data = self.post_data
                post_data['nd'] = str(int(time.time() * 1000))
                post_data['page'] = str(page)

                judge_status = self.judge_in_interval_from_json(url, formdata=post_data, resp=resp)
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.FormRequest(
                        url=url, callback=self.parse_list, formdata=post_data, dont_filter=True,
                        priority=(max_page - page) * 1, meta={
                            'notice_type': resp.meta.get('notice_type', ''),
                            'has_module_id': resp.meta.get('has_module_id', False),
                        }
                    )

    def parse_list(self, resp):
        """
        GET DETAIL HREF
        /Web/WebAfficheIndex?
            tenderID=30f06018-3b27-43df-a8a2-6e2175d0d305&
            afficheID=fb3b04fe-aee3-4afa-bdd8-c736e04dfdb7&
            moduleID=8&
            afficheType=8
        """
        has_module_id = resp.meta.get('has_module_id', False)
        data = json.loads(resp.text)
        error = data.get('error', '')
        if not error:
            content_list = data.get('rows', [])
            for n, content in enumerate(content_list):
                affiche_type = content.get('AfficheType', '')
                module_id = affiche_type if has_module_id else ''
                pub_time = content.get('PublishStartTime', '')

                c_pub_time = '{0:%Y-%m-%d}'.format(datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S'))

                c_url = self.detail_url.format(**{
                    'tender_id': content.get('TenderID', ''),
                    'affiche_id': content.get('AfficheID', ''),
                    'module_id': module_id,
                    'affiche_type': content.get('AfficheType', ''),
                })

                if utils.check_range_time(self.start_time, self.end_time, c_pub_time):
                    yield scrapy.Request(url=c_url, callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                        'pub_time': pub_time,
                    }, priority=(len(content_list) - n) * 10000)

    @classmethod
    def handle_iframe_content(cls, content, resp):
        """
        HANDLE CONTENT FROM IFRAME HREF
        """
        msg = ''
        try:
            doc = etree.HTML(content)

            iframe_href_els = doc.xpath('//iframe[@id="frame_content"]')
            if iframe_href_els:
                iframe_href_el = iframe_href_els[0]
                iframe_href = iframe_href_el.attrib['src']

                headers = cls.get_headers(resp)
                response = requests.get(url=iframe_href, headers=headers)

                iframe_href_el.attrib['src'] = response.url

                content = etree.tounicode(doc, method='html')
        except Exception as e:
            msg = 'error: {0}'.format(e)

        return msg, content.replace('<html><body>', '').replace('</body></html>', '')

    def parse_detail(self, resp):
        """
        - business_category: 根据标题去匹配，招标公告中带（采购、购买）关键词的，匹配项目类型为采购，其余为工程
        """
        title_name = resp.xpath('//div[@class="noticeTitle"]/text()').get().replace('\r\n', '').strip()
        notice_type_ori = resp.meta.get('notice_type')
        content = resp.xpath('//div[@class="noticeDetail"]').get().replace('\n', '')

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        bsniz_matched, business_category = self.match_bsniz_category(title_name)
        if not bsniz_matched:
            business_category = '工程'

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # HANDLE CONTENT FROM IFRAME HREF
        _, content = Province77ZhaobideSpiderSpider.handle_iframe_content(content, resp)
        _, content = utils.remove_specific_element(content, 'div', 'class', 'area01')

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url)

        notice_item = items.NoticesItem()

        notice_item.update(**{
            'origin': resp.url,
            'title_name': title_name,
            'pub_time': resp.meta.get('pub_time'),
            'info_source': self.basic_area,
            'is_have_file': constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE,
            'files_path': files_path,
            'notice_type': notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE,
            'content': content,
            'area_id': self.area_id,
            'business_category': business_category,
        })

        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute(
        "scrapy crawl province_77_zhaobide_spider -a sdt=2021-01-01 -a edt=2021-06-07".split(" ")
    )
    # cmdline.execute("scrapy crawl province_77_zhaobide_spider".split(" "))
