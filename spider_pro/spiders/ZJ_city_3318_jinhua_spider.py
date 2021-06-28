# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-26
# @Describe: 金华市公共资源交易中心 - 全量/增量脚本
import re
import math
import json

import requests
import scrapy
import random
import datetime
from urllib import parse

from lxml import etree
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval, get_url


class MySpider(CrawlSpider):
    name = 'ZJ_city_3318_jinhua_spider'
    area_id = "3318"
    domain_url = "http://ggzyjy.jinhua.gov.cn"
    query_url = "http://ggzyjy.jinhua.gov.cn"
    allowed_domains = ['ggzyjy.jinhua.gov.cn']
    area_province = "浙江-金华市公共资源交易中心"


    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告', '采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公示', '采购结果公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ['补充文件']
    # 中标预告
    list_win_advance_notice_num = ['中标公示', '评标公示', '评标结果公示']
    # 资格预审结果公告
    list_qualification_num = ['预审结果']
    # 其他公告
    list_others_notice_num = []

    url_list = [
                'http://ggzyjy.jinhua.gov.cn/cms/gcjy/index.htm',
                'http://ggzyjy.jinhua.gov.cn/cms/zfcg/index.htm',
                'http://ggzyjy.jinhua.gov.cn/cms/cqjy/index.htm'
                ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    }

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for url in self.url_list:
            if 'gcjy' in url:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/gcjy/index.htm'
                classifyShow = '建设工程'
            elif 'zfcg' in url:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/zfcg/index.htm'
                classifyShow = '政府采购'
            else:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/cqjy/index.htm'
                classifyShow = '产权交易'

            yield scrapy.Request(url=type_url, callback=self.parse_urls,
                                 meta={'classifyShow': classifyShow})

    def parse_urls(self, response):
        try:
            list_li = response.xpath('//div[@class="ListBorder floatL"]//a')
            type_list_name = ['省重点工程', '市本级工程', '金华山工程', '金义都工程', '小额工程', '公开招标']
            for li in list_li:
                if li.xpath('./text()').get() not in type_list_name:
                    type_url = self.domain_url + li.xpath('./@href').get()
                    type_name = li.xpath('./text()').get()
                    if type_name in self.list_qualification_num:                 # 资格预审
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif type_name in self.list_win_advance_notice_num:          # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif type_name in self.list_zb_abnormal_num:                 # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif type_name in self.list_win_notice_category_num:         # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif type_name in self.list_notice_category_num:             # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    else:
                        notice = 'null'
                    if notice != 'null':
                        yield scrapy.Request(url=type_url, callback=self.parse_info,
                                         meta={'classifyShow': response.meta['classifyShow'], 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_info(self, response):
        try:
            if self.enable_incr:
                page = 1
                num = 0
                data_list = response.xpath('//div[@class="Right-Border floatL"]/dl/dt')
                for li in range(len(data_list)):
                    if '...' not in ''.join(data_list[li].xpath('./a/text()').get()).strip():
                        title_name = ''.join(data_list[li].xpath('./a/text()').get()).strip().replace('（限额以下）', '')\
                            .replace('(限额以下)', '').replace('[市本级]', '').replace('[金华市（本级）] ', '').replace('[金华市]', '')
                        info_url = self.domain_url + data_list[li].xpath('./a/@href').get()
                        pub_time = ''.join(data_list[li].xpath('./span/text()').get()).replace('[', '').replace(']', '')
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(data_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_data_item, priority=150,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'classifyShow': response.meta['classifyShow'],
                                                       'title_name': title_name})

                        if num >= len(data_list):
                            page += 1
                            info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                            yield scrapy.Request(url=info_url.format(page), callback=self.parse_data_info,
                                                 meta={'classifyShow': response.meta['classifyShow'],
                                                       'notice': response.meta['notice']})
            else:
                page_str = response.xpath('//div[@class="Page-bg floatL"]/div/text()').get()
                pages = ''.join(re.findall('.*\d\/(\d+)', page_str))
                total = ''.join(re.findall('共(\d+)条', page_str))
                self.logger.info(f"本次获取总条数为：{total}")
                info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                for num in range(1, int(pages)+1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_data_info, priority=100,
                                                 meta={'classifyShow': response.meta['classifyShow'],
                                                       'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            data_list = response.xpath('//div[@class="Right-Border floatL"]/dl/dt')
            for li in data_list:
                if '...' not in ''.join(li.xpath('./a/text()').get()).strip():
                    title_name = ''.join(li.xpath('./a/text()').get()).strip().replace('（限额以下）', '').replace('(限额以下)', '')\
                                   .replace('[市本级]', '').replace('[金华市（本级）] ', '').replace('[金华市]', '')
                    put_time = ''.join(li.xpath('./span/text()').get()).replace('[', '').replace(']', '')
                    info_url = self.domain_url + li.xpath('./a/@href').get()
                    yield scrapy.Request(url=info_url, callback=self.parse_data_item, priority=150,
                                         meta={'notice': response.meta['notice'],
                                               'put_time': put_time,
                                               'classifyShow': response.meta['classifyShow'],
                                               'title_name': title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_item(self, response):
        try:
            if response.xpath('//table/tr[last()]/td/div/b/a/@href').get():
                info_url = response.xpath('//table/tr[last()]/td/div/b/a/@href').get()
                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=20, dont_filter=True,
                                     meta={'put_time': response.meta['put_time'],
                                           'classifyShow': response.meta['classifyShow'],
                                           'title_name': response.meta['title_name'],
                                           'notice': response.meta['notice']})
            else:
                yield scrapy.Request(url=response.url, callback=self.parse_item, priority=20, dont_filter=True,
                                     meta={'put_time': response.meta['put_time'],
                                           'classifyShow': response.meta['classifyShow'],
                                           'title_name': response.meta['title_name'],
                                           'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta['put_time']
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'候选人', title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'废标|流标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|答疑|澄清|补充|延期', title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'预审结果', title_name):  # 资格预审
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']
            content = response.xpath('//div[@class="Main-p floatL"]').get()
            # 去除最后一个表格
            pattern = re.compile(r'<td>(上一条：.*)</a>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            files_path = {}
            cid = re.findall('\d+', response.url)[0]
            values = get_url(self.domain_url, cid)
            html = etree.HTML(content)
            if html.xpath('//table/tr[2]//a/@title'):
                str_content = html.xpath('//table/tr[2]/td[1]/a')
                for con in range(len(str_content)):
                    key = str_content[con].xpath('./@title')[0]
                    value = self.domain_url + values
                    files_path[key] = value
            elif html.xpath('//div[@class="Main-p floatL"]/img/@src'):
                value = html.xpath('//div[@class="Main-p floatL"]/img/@src')[0]
                key = 'tupian.jpg'
                files_path[key] = value
            else:
                files_path = ''


            notice_item = NoticesItem()

            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3318_jinhua_spider".split(" "))




