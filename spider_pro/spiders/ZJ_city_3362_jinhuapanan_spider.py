# -*- coding: utf-8 -*-
# @file           :ZJ_city_3362_jinhuapanan_spider.py
# @description    :浙江省金华市磐安县人民政府
# @date           :2021/08/03 08:45:58
# @author         :miaokela
# @version        :1.0
import re
import random
import json
import requests
from datetime import datetime
from math import ceil

import scrapy

from spider_pro import utils, constans, items


class ZjCity3362JinhuapananSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3362_jinhuapanan_spider'
    allowed_domains = ['www.panan.gov.cn']
    start_urls = ['http://www.panan.gov.cn/']
    basic_area = '浙江省金华市磐安县人民政府'
    query_url = 'http://www.panan.gov.cn'

    area_id = 3362
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '建设工程', 'url': 'http://www.panan.gov.cn/col/col1229500305/index.html'},  # 招标公告、文件预公示
        ],
        '招标公告': [
            {'category': '政府采购', 'url': 'http://www.panan.gov.cn/col/col1229170812/index.html'},  # 采购公告
            {'category': '建设工程', 'url': 'http://www.panan.gov.cn/col/col1229170806/index.html'},  # 招标公告
            {'category': '土地交易', 'url': 'http://www.panan.gov.cn/col/col1229170816/index.html'},  # 招标公告
            {'category': '产权交易', 'url': 'http://www.panan.gov.cn/col/col1229170819/index.html'},  # 招标公告
            {'category': '乡镇分中心', 'url': 'http://www.panan.gov.cn/col/col1229170822/index.html'},  # 乡镇分中心
            {'category': '园区分中心', 'url': 'http://www.panan.gov.cn/col/col1229321833/index.html'},  # 交易公告
        ],
        '招标变更': [
            {'category': '建设工程', 'url': 'http://www.panan.gov.cn/col/col1229170807/index.html'},  # 更正（补充公告）
        ],
        '招标异常': [
            {'category': '建设工程', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001007/list3gc.html'},  # 废标公告
        ],
        '中标预告': [
            {'category': '建设工程', 'url': 'http://www.panan.gov.cn/col/col1229170808/index.html'},  # 预中标公示
        ],
        '中标公告': [
            {'category': '建设工程', 'url': 'http://www.panan.gov.cn/col/col1229170809/index.html'},  # 中标公示
            {'category': '政府采购', 'url': 'http://www.panan.gov.cn/col/col1229170813/index.html'},  # 中标成交公告
            {'category': '土地交易', 'url': 'http://www.panan.gov.cn/col/col1229170817/index.html'},  # 中标公示
            {'category': '产权交易', 'url': 'http://www.panan.gov.cn/col/col1229170820/index.html'},  # 中标公示
            {'category': '乡镇分中心', 'url': 'http://www.panan.gov.cn/col/col1229170823/index.html'},  # 中标公示
            {'category': '园区分中心', 'url': 'http://www.panan.gov.cn/col/col1229321837/index.html'},  # 中标公示
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
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                c_url = cu['url']
                yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                })

    def parse_list(self, resp):
        txt = resp.text
        if txt:
            content = ''.join([t.strip() for t in txt.split(' ')]).replace('\n', '').replace('\t', '')
            c_com = re.compile(r'<record>.*?<span>(?P<pub_time>[0-9 \-]+)</span><ahref=\"(?P<url>.*?)\"target')

            for pub_time, suffix_url in c_com.findall(content):
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    c_url = ''.join([self.query_url, suffix_url])
                    c_url = 'http://www.panan.gov.cn/art/2021/6/18/art_1229170823_59236367.html'
                    yield scrapy.Request(url=c_url, callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                        'category': resp.meta.get('category', ''),
                        'pub_time': pub_time,
                    })
                    break
                else:
                    break

    def parse_detail(self, resp):
        title_name = ''.join(resp.xpath('//div[@class="gm_tt"]/text()').extract()).strip()
        content = resp.xpath('//div[@class="gm_tt3"]').get()
        if content:
            content = content.replace('<body>', '').replace('</body>', '')

        notice_type_ori = resp.meta.get('notice_type')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url, resp=resp, pub_time=resp.meta.get('pub_time'))

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name.strip() if title_name else ''
        notice_item["pub_time"] = resp.meta.get('pub_time')

        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = resp.meta.get('category')
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl ZJ_city_3362_jinhuapanan_spider -a sdt=2021-01-01 -a edt=2021-06-01".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3362_jinhuapanan_spider".split(" "))
