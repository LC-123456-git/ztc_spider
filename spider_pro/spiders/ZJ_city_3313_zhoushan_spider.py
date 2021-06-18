#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-12
# @Describe: 舟山市公共资源交易网 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3313_zhoushan_spider'
    area_id = "3313"
    domain_url = "http://zsztb.zhoushan.gov.cn"
    query_url = "http://zsztb.zhoushan.gov.cn/zsztbweb/"
    allowed_domains = ['zsztb.zhoushan.gov.cn']
    area_province = "浙江-舟山市公共资源交易网"

    # 招标预告
    list_advance_notice_num = ['政府采购意向公开']
    # 招标公告
    list_notice_category_num = ['招标公告', '政府采购公告', '产权交易公告', '公房出租交易公告', '交易公告']
    # 招标异常
    list_alteration_category_num = ['异常处理结果公告', '终止公示']
    # 招标变更
    list_zb_abnormal_num = ['变更公告', '中标候选人变更公示', '政府采购更正公告', '政府采购结果更正公告 ']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示', '交易结果']
    # 中标公告
    list_win_notice_category_num = ['中标结果公告', '政府采购结果公告', '产权交易结果', '公房出租交易结果', '成交公示']
    # 资格预审
    list_qualification_num = ['资格预审未入围公示']
    # 其他
    list_qita_code = ['开标结果公示', '政府采购征询意见', '政府采购合同公告']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            type_list = response.xpath('//td[@width="660"]/table/tr/td')
            for type_t in type_list:
                type_url = self.domain_url + type_t.xpath('./a/@href').get()
                category_name = type_t.xpath('./a/text()').get().strip()       #获取到分类的name
                yield scrapy.Request(url=type_url, callback=self.parse_data_urls, meta={'category_name': category_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败: parse_urls: {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            data_url_list = response.xpath('//div[@class="span12 ml10"]/div/div[1]/h5')
            for data_u in data_url_list:
                if data_u.xpath('./a/@href').get():
                    data_url = self.query_url + re.findall('/(\w+\/\d+)',data_u.xpath('./a/@href').get())[0]     #获取到分类下面的详情url
                    data_name = data_u.xpath('./a/text()').get()      #获取到分类下面的详情name
                    if data_name in self.list_advance_notice_num:  # 招标预告
                        noticn = const.TYPE_ZB_ADVANCE_NOTICE
                    elif data_name in self.list_notice_category_num:  # 招标公告
                        noticn = const.TYPE_ZB_NOTICE
                    elif data_name in self.list_alteration_category_num:  # 招标异常
                        noticn = const.TYPE_ZB_ABNORMAL
                    elif data_name in self.list_zb_abnormal_num:  # 招标变更
                        noticn = const.TYPE_ZB_ALTERATION
                    elif data_name in self.list_win_advance_notice_num:  # 中标预告
                        noticn = const.TYPE_WIN_ADVANCE_NOTICE
                    elif data_name in self.list_win_notice_category_num:  # 中标公告
                        noticn = const.TYPE_WIN_NOTICE
                    elif data_name in self.list_qualification_num:  # 资格预审
                        noticn = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif data_name in self.list_qita_code:  # 其他公告
                        noticn = const.TYPE_OTHERS_NOTICE
                    else:
                        noticn = 'null'
                    yield scrapy.Request(url=data_url, callback=self.parse_data_info,
                                     meta={'noticn': noticn, 'category_name': response.meta['category_name']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败:parse_data_urls: {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get():
                if self.enable_incr:
                    pn = 1
                    num = 0
                    li_list = response.xpath('//table[@class="article-body"]/tr/td/table/tr[@height="30"]')
                    for li in range(len(li_list)):
                        title_name = li_list[li].xpath('./td[2]/a/@title').get()
                        all_info_url = self.domain_url + li_list[li].xpath('./td[2]/a/@href').get()
                        pub_time = ''.join(li_list[li].xpath('./td[3]/text()').get()).replace('[', '').replace(']', '')
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=all_info_url, callback=self.parse_item,
                                                 dont_filter=True, priority=100,
                                                 meta={'notice': response.meta['noticn'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name,
                                                       'category_name': response.meta['category_name']})

                        if num >= len(li_list):
                            pn += 1
                            info_url = response.url + '?Paging={}'
                            yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info,
                                                 meta={'noticn': response.meta['noticn'],
                                                       'category_name': response.meta['category_name']})
                else:
                    pages = re.findall('\/(\d+)', response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get())[0]
                    total = int(pages) * 20
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    info_url = response.url + '?Paging={}'
                    for num in range(1, int(pages) + 1):
                        yield scrapy.Request(url=info_url.format(num), callback=self.parse_info,
                                             meta={'noticn': response.meta['noticn'],
                                                   'category_name': response.meta['category_name']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            li_list = response.xpath('//div[@class="article"]/table/tr/td/table/tr[@height="30"]')
            for li in li_list:
                title_name = li.xpath('./td[2]/a/@title').get()
                all_info_url = self.domain_url + li.xpath('./td[2]/a/@href').get()
                pub_time = ''.join(li.xpath('./td[3]/text()').get()).replace('[', '').replace(']', '')
                yield scrapy.Request(url=all_info_url, callback=self.parse_item, dont_filter=True, priority=100,
                                     meta={'notice': response.meta['noticn'],
                                           'pub_time': pub_time,
                                           'title_name': title_name,
                                           'category_name': response.meta['category_name']})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = ''.join(re.findall('来源：(.*)】', str(response.xpath('//td[@id="tdTitle"]/text()').extract()))).strip()
            if info_source and info_source != '0':
                if '舟山市' in info_source:
                    info_source = self.area_province + ''.join(info_source).replace('舟山市', '')
                else:
                    info_source = self.area_province + info_source
            else:
                info_source = self.area_province

            category = response.meta['category_name']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)

            if re.search(r'变更|更正|澄清|修正|补充', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'候选人|评标结果', title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'中标|结果|成交', title_name):  # 中标公告
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'终止|中止|流标|废标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'招标|谈判|磋商', title_name):  # 招标公告
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['noticn']

            cont = response.xpath('//table[@width="1002"]').extract()[0]
            contents = cont.replace(r"/zsztbweb/UploadFile/", "http://zsztb.zhoushan.gov.cn/zsztbweb/UploadFile/")

            pattern = re.compile(r'<td id="tdTitle".*?>(.*?)</tr>', re.S)
            content = contents.replace(''.join(re.findall(pattern, contents)), '')
            if content:
                files_path = {}
                if response.xpath('//tr[@id="trAttach"]//table[@id="filedown"]/tr/td/a'):
                    conet_list = response.xpath('//tr[@id="trAttach"]//table[@id="filedown"]/tr/td/a')
                    for con in conet_list:
                        if con.xpath('./@href'):
                            if 'http' in con.xpath('./@href').get():
                                value = con.xpath('./@href').get()
                            else:
                                value = self.domain_url + con.xpath('./@href').get()

                            if con.xpath('./font/text()').get():
                                keys = con.xpath('./font/text()').get()
                            else:
                                keys = 'img/pdf/doc/xls'

                            files_path[keys] = value

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
                notice_item["category"] = category
                yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3313_zhoushan_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3313_zhoushan_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))


