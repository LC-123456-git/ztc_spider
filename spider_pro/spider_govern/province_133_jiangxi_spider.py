# -*- coding: utf-8 -*-
# @file           :province_133_jiangxi_spider.py
# @description    :江西省政府采购网
# @date           :2021/10/12 10:43:15
# @author         :miaokela
# @version        :1.0
import ast
import copy
import datetime
import json
import re
import math
from collections import OrderedDict

import scrapy

from spider_pro import utils, constans, items


class Province133JiangxiSpiderSpider(scrapy.Spider):
    name = 'province_133_jiangxi_spider'
    allowed_domains = ['ccgp-jiangxi.gov.cn']
    start_urls = ['http://ccgp-jiangxi.gov.cn/']

    basic_area = '江西省政府采购网'
    query_url = 'http://www.ccgp-jiangxi.gov.cn/jxzfcg/services/JyxxWebservice/getList?response=application/json' \
                '&pageIndex={page_index}&pageSize={page_size}&area=&prepostDate={start_time}&nxtpostDate={end_time}&xxTitle=&categorynum={category_num}'
    page_num_url = 'http://www.ccgp-jiangxi.gov.cn/jxzfcg/services/JyxxWebservice/getListByCount?response=application/json' \
                   '&area=&prepostDate={start_time}&nxtpostDate={end_time}&xxTitle=&categorynum={category_num}'
    detail_url = 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/{prefix}/{category_num}/{date}/{info_id}.html'
    base_url = 'http://www.ccgp-jiangxi.gov.cn'

    area_id = 133
    keywords_map = OrderedDict({
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    })
    notice_map = {
        '招标预告': ['采购意向'],
        '招标公告': ['采购公告', '单一来源公示'],
        '招标变更': ['变更公告', '答疑澄清'],
        '中标公告': ['结果公示'],
        '其他公告': ['合同公告'],
    }
    notice_code_map = {
        '采购意向': '002006007',
        '采购公告': '002006001',
        '单一来源公示': '002006005',
        '变更公告': '002006002',
        '答疑澄清': '002006003',
        '结果公示': '002006004',
        '合同公告': '002006006',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = kwargs.get('sdt', '2021-01-01')
        self.end_time = kwargs.get('edt', '{0:%Y-%m-%d}'.format(datetime.datetime.now()))
        self._query_data = {
            "page_index": "1",
            "page_size": "22",
            "start_time": self.start_time,
            "end_time": self.end_time,
            "category_num": "",
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
    def query_data(self):
        return copy.deepcopy(self._query_data)

    @classmethod
    def get_notice(cls, sub_notice):
        notice_type = ''
        for k, v in cls.notice_map.items():
            if sub_notice in v:
                notice_type = k
                break
        return notice_type

    def start_requests(self):
        for sub_notice, category_num in self.notice_code_map.items():
            query_data = self.query_data
            query_data['category_num'] = category_num
            # 获取总页数
            page_num_url = self.page_num_url.format(**{k: v for k, v in query_data.items() if k in [
                'start_time', 'end_time', 'category_num'
            ]})
            yield scrapy.Request(
                url=page_num_url, callback=self.parse_list,
                dont_filter=True, meta={
                    'notice_type': Province133JiangxiSpiderSpider.get_notice(sub_notice),
                    'category_num': category_num,
                }, cb_kwargs={
                    'query_data': copy.deepcopy(query_data),
                }
            )

    def parse_list(self, resp, query_data):
        """
        翻页
        """
        try:
            content = json.loads(resp.text)
        except Exception as e:
            self.logger.info('parse_list解析响应数据失败:{}'.format(e))
        else:
            total_record = content.get('return', 0)
            max_page = math.ceil(total_record / 22)
            for page in range(max_page):
                query_data['page_index'] = page + 1

                c_query_url = self.query_url.format(**query_data)
                yield scrapy.Request(
                    url=c_query_url, callback=self.parse_url,
                    dont_filter=True, meta=resp.meta,
                    priority=(max_page - page) * 10
                )

    def parse_url(self, resp):
        """
        解析详情页链接
        http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006007/20211012/9345b46c-822c-4c0e-9c05-f594336c1297.html
        """
        try:
            content = json.loads(resp.text)
            result = ast.literal_eval(content.get('return'))
        except Exception as e:
            self.logger.info('parse_url解析响应数据失败:{}'.format(e))
        else:
            table = result.get('Table', [])

            for n, t in enumerate(table):
                category_num = t.get('categorynum', '')
                info_id = t.get('infoid', '')
                post_date = t.get('postdate', '')
                title = t.get('title', '')
                title = re.sub(r'\d{11}', '', title)
                title = re.sub(r'\[[A-Za-z0-9\-\u4e00-\u9fa5]+]', '', title)
                title = re.sub(r"<font.*?/font>", '', title)

                prefix = category_num[0:6]
                date = ''.join(post_date.split('-'))
                detail_url = self.detail_url.format(**{
                    'prefix': prefix,
                    'category_num': category_num,
                    'date': date,
                    'info_id': info_id
                })

                resp.meta.update(**{
                    'title': title,
                    'pub_time': post_date,
                })
                yield scrapy.Request(
                    url=detail_url, callback=self.parse_detail,
                    meta=resp.meta, priority=10 ** 4 * (len(table) - n)
                )

    def parse_detail(self, resp):
        title_name = resp.meta.get('title', '')
        pub_time = resp.meta.get('pub_time', '')
        notice_type_ori = resp.meta.get('notice_type', '')

        content = resp.xpath('//div[@class="con"]').get()

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

    # cmdline.execute("scrapy crawl province_133_jiangxi_spider -a sdt=2021-09-01 -a edt=2021-10-10".split(" "))
    cmdline.execute("scrapy crawl province_133_jiangxi_spider".split(" "))
