#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-31
# @Describe: 齐鲁采购与招标网 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import urllib
import datetime
from lxml import etree
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element


class MySpider(CrawlSpider):
    name = 'province_68_qilu_spider'
    area_id = "68"
    domain_url = "http://www.qlebid.com"
    query_url = "http://www.qlebid.com/cms/channel/1ywgg1qb/index.htm"
    allowed_domains = ['qlebid.com']
    area_province = '齐鲁采购与招标网'

    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告']
    # 招标变更
    list_zb_abnormal_num = ['变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示', '成交候选人公示']
    # 中标公告
    list_win_notice_category_num = []
    # 招标异常
    list_alteration_category_num = ['终止公告']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_urls, dont_filter=True)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="m-hd"]/ul/li')
            for li in li_list:
                if li.xpath('./div/a/@href'):
                    itme_url = self.domain_url + li.xpath('./div/a/@href').get()
                    itme_name = li.xpath('./span/text()').get()
                    if itme_name in self.list_notice_category_num:            # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    elif itme_name in self.list_zb_abnormal_num:              # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif itme_name in self.list_win_advance_notice_num:       # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif itme_name in self.list_alteration_category_num:      # 招标异常
                        notice = const.TYPE_ZB_ABNORMAL
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=itme_url, callback=self.parse_data, priority=50,
                                             meta={'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data(self, response):
        try:
            li_list = response.xpath('//div[@class="infolist-tab"]/ul/li')[1:]
            for li in li_list:
                category_url =self.domain_url + li.xpath('./a/@href').get()
                business_category = ''.join(li.xpath('./a/text()').get()).strip()
                yield scrapy.Request(url=category_url, callback=self.parse_data_urls, priority=100,
                                     meta={'notice': response.meta['notice'],
                                           'business_category': business_category})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if response.xpath('//div[@class="pag-txt"]/em[last()]/text()'):
                pages = response.xpath('//div[@class="pag-txt"]/em[last()]/text()').get()
                self.logger.info(f"本次获取总条数为：{int(pages) * 10}")
                data_info_urls = response.url + '?pageNo={}'

                if self.enable_incr:
                    page = 1
                    nums = 1
                    data_li_list = response.xpath('//ul[@id="list1"]/li')
                    for li in range(len(data_li_list)):
                        put_time = ''.join(data_li_list[li].xpath('./a/em/text()').get()).strip()
                        put_time = get_accurate_pub_time(put_time)
                        x, y, z = judge_dst_time_in_interval(put_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        if nums >= len(data_li_list):
                            page += 1
                        else:
                            page = 1
                        yield scrapy.Request(url=data_info_urls.format(page), callback=self.parse_data_info, priority=100,
                                             meta={"business_category": response.meta['business_category'],
                                                   'notice': response.meta['notice']})
                else:
                    for num in range(1, int(pages) + 1):
                        yield scrapy.Request(url=data_info_urls.format(num), callback=self.parse_data_info, priority=100,
                                             meta={"business_category": response.meta['business_category'],
                                                   'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_urls {response.meta=} {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            li_list = response.xpath('//ul[@id="list1"]/li')
            for li in li_list:
                title_name = li.xpath('./a/@title').get()
                put_time = ''.join(li.xpath('./a/em[last()]/text()').get()).strip()
                data_info_url = self.domain_url + li.xpath('./a/@href').get()
                if re.search(r'资格审查', title_name):
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'变更|更正|澄清|补充|取消|延期', title_name):
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'终止|中止|废标|流标', title_name):
                    notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    notice_type = response.meta['notice']
                yield scrapy.Request(url=data_info_url, callback=self.parse_item, priority=150,
                                     meta={"business_category": response.meta['business_category'],
                                           "title_name": title_name,
                                           "put_time": put_time,
                                           'notice_type': notice_type})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source =self.area_province
            business_category = response.meta.get("business_category")
            title_name = response.meta['title_name']
            pub_time = response.meta['put_time']
            notice_type = response.meta['notice_type']
            pub_time = get_accurate_pub_time(pub_time)

            content = response.xpath('//div[@class="article-content"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'div', 'class', 'article-title')
            # 去除 info信息 来源等信息
            _, content = remove_specific_element(content, 'div', 'class', 'article-author')
            # 去除 最下面的 上一篇 下一篇
            _, content = remove_specific_element(content, 'div', 'class', 'article-bottom')

            pattern = re.compile(r'公告发布媒介(.*?</table>)', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'发布公告的媒介(.*?</table>)', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            # pattern = re.compile(r'发布公告的媒介(.*?。)', re.S)
            # content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'发布招标公告的媒介(.*?。)', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            files_path = {}
            suffix_list = ['html', 'com', 'com/', 'cn', 'cn/', '##']
            files_text = etree.HTML(content)
            if files_text.xpath('//div[@class="main-text"]//tr//a/@href'):
                files_list = files_text.xpath('//div[@class="main-text"]//tr//a')
                for cont in files_list:
                    if cont.xpath('./@href'):
                        values = cont.xpath('./@href')[0]
                        if ''.join(values).split('.')[-1] not in suffix_list:
                            if 'http:' not in values:
                                value = self.domain_url + values
                            else:
                                value = values
                            if cont.xpath('.//text()'):
                                keys = ''.join(cont.xpath('.//text()')).strip()
                                if ''.join(values).split('.')[-1] not in keys:
                                    key = keys + '.' + ''.join(values).split('.')[-1]
                                else:
                                    key = keys
                                files_path[key] = value


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
            notice_item["business_category"] = business_category

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_68_qilu_spider".split(" "))


