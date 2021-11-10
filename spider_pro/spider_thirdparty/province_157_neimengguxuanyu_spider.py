# -*- coding: utf-8 -*-
# @file           :province_157_neimengguxuanyu_spider.py
# @description    :内蒙古宣宇工程电子交易平台
# @date           :2021/10/28 15:58:54
# @author         :miaokela
# @version        :1.0
import json
import math
import re
import copy

import scrapy

from spider_pro import constans, utils, items


class Province157NeimengguxuanyuSpiderSpider(scrapy.Spider):
    name = 'province_157_neimengguxuanyu_spider'
    allowed_domains = ['www.nmgxuanyu.com']
    start_urls = ['http://www.nmgxuanyu.com/']

    basic_area = '内蒙古宣宇工程电子交易平台'
    area_id = 157
    base_url = 'http://www.nmgxuanyu.com'
    query_url = 'http://www.nmgxuanyu.com/EpointWebBuilder/rest/frontAppCustomAction/getPageInfoListNew'

    """
    {
        "controls": [],
        "custom": {
            "count": 139,
            "infodata": [
                {
                    "categorynum": "001001001",
                    "infotype": "News",
                    "strcomment": null,
                    "infoid": "f54b0234-836b-44e8-8e5e-5cdc8ca6094b",
                    "recommend": null,
                    "title": "2021年鄂伦春旗制种大县奖励资金项目",
                    "zblx": "公开招标",
                    "cfgg": "",
                    "titletype": "Text",
                    "quyu": "内蒙古自治区·呼伦贝尔市·鄂伦春自治旗",
                    "infourl": "/xmxx/001001/001001001/20210917/f54b0234-836b-44e8-8e5e-5cdc8ca6094b.html",
                    "customtitle": "2021年鄂伦春旗制种大县奖励资金项目",
                    "shixiao": null,
                    "bgcs": "",
                    "urlname": "linkurl",
                    "infodate": "2021-09-17"
                }
            ]
        },
        "status": {
            "code": 1,
            "top": false,
            "text": "操作成功",
            "url": ""
        }
    }
    """
    url_map = {
        '招标公告': [
            {'code': '001001001'},  # 招标公告
        ],
        '招标变更': [
            {'code': '001001002'},  # 变更公告
            {'code': '001001004'},  # 答疑澄清
        ],
        '招标异常': [
            {'code': '001001005'},  # 招标异常
        ],
        '中标预告': [
            {'code': '001001006'},  # 中标候选人公示
        ],
        '中标公告': [
            {'code': '001001007'},  # 中标公示
        ],
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self.page_size = 8
        self._form_data = {
            'params': '{{"siteGuid":"7eb5f7f1-9041-43ad-8e13-8fcb82ea831a","categoryNum":"{category_num}","kw":"","con":"",' + \
                      '"pageIndex":{page_index},"pageSize":%d,"startDate":"%s","endDate":"%s"}}' % (
                          self.page_size, self.start_time, self.end_time)
        }

    @property
    def form_data(self):
        return copy.deepcopy(self._form_data)

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
                code = param.get('code', '')
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': 0
                }))

                yield scrapy.FormRequest(
                    url=self.query_url, callback=self.turn_page, formdata=form_data,
                    meta={
                        'notice_type': notice_type,
                    }, cb_kwargs={
                        'code': code,
                    }
                )

    def turn_page(self, resp, code):
        content = json.loads(resp.text)

        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        total = content.get('custom', {}).get('count', 0)

        max_page = math.ceil(total / self.page_size)

        if all([self.start_time, self.end_time]):
            for i in range(max_page):
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': i
                }))

                judge_status = utils.judge_in_interval(
                    self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST', data=form_data,
                    proxies=proxies, headers=headers,
                    rule='//infodata/infodate/text()', doc_type='json'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.FormRequest(
                        url=self.query_url, callback=self.parse_list, meta=resp.meta, formdata=form_data,
                        priority=(max_page - i) * 10,
                        dont_filter=True
                    )
        else:
            for i in range(max_page):
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': i
                }))
                yield scrapy.FormRequest(
                    url=self.query_url, callback=self.parse_list, meta=resp.meta, formdata=form_data,
                    priority=(max_page - i) * 10,
                    dont_filter=True
                )

    def parse_list(self, resp):
        content = json.loads(resp.text)
        result = content.get('custom', {}).get('infodata', [])

        for n, r in enumerate(result):
            pub_time = r.get('infodate', '')
            title_name = r.get('title', '')
            info_url = r.get('infourl', '')
            c_url = ''.join([self.base_url, info_url])

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
        content = resp.xpath('//div[@id="maindiv"]').get()
        title_name = resp.meta.get('title_name')
        title_name = re.sub(r'<font>.*?</font>', '', title_name)
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        # 移除相关信息
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//div[@id="title"]'
        )

        # 关键字重新匹配 notice_type
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

        notice_item["title_name"] = title_name
        notice_item["pub_time"] = pub_time
        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = ''
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_157_neimengguxuanyu_spider -a sdt=2021-01-01 -a edt=2021-10-28".split(" "))
    cmdline.execute("scrapy crawl province_157_neimengguxuanyu_spider".split(" "))

