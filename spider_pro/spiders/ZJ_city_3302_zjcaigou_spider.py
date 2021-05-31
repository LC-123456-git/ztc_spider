#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-05-31
# @Describe: 浙江政府采购网 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import datetime
import urllib
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3302_zjcaigou_spider'
    area_id = "3302"
    domain_url = "https://zfcg.czt.zj.gov.cn/"
    query_url = "https://zfcgmanager.czt.zj.gov.cn/cms/api/cors/remote/results?"
    allowed_domains = ['zfcg.czt.zj.gov.cn']
    area_province = "浙江政府采购网"

    # 招标预告
    list_advance_notice_ = ['招标文件预公示', '采购预告']
    # 招标公告
    list_notice_category_num = ['招标公告（资格预审公告）', '招标预告', '交易公告', '出让公告', '股权项目', '资产项目',
                                '罚没物品', '融资需求', '金融资产', '采购分类']
    # 招标变更
    list_zb_abnormal_code = []
    # 中标预告
    list_win_advance_notice_code = ['预中标公示']
    # 中标公告
    list_win_notice_category_code = ['中标公告', '中标结果', '出让结果公示', '结果公示', '结果公告', '排污权交易']
    # 资格预审
    list_qualification_num = ['资格预审']
    # 其他
    list_qita_code = ['投诉受理及处理结果公告']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.pubDate = kwargs.get("sdt")
            self.endDate = kwargs.get("edt")
        else:
            self.enable_incr = False
            self.pubDate = self.today
            self.endDate = self.today

        self.info_dict = {"pageSize": "100",
                    "sourceAnnouncementType": "10016,3012,1002,1003,3014,3013,3009,4004,3008,2001,3001,3020,3003,3002,3011,3017,3018,3005,3006,3004,4005,4006,3007,3015,3010,3016,6003,4002,4001,4003,8006,1995,1996,1997,8008,8009,8013,8014,9002,9003,808030100,7003,7004,7005,7006,7007,7008,7009",
                    "isGov": "true", "pubDate": self.pubDate, "endDate": self.endDate, "isExact": "1", "url": "notice"}
        self.page_dict = {"pageNo": "1"}


    def start_requests(self):
        # url = 'http://bidding.ningbo.gov.cn/cms/qtzbjg/169060.htm'
        # yield scrapy.Request(url=url, callback=self.parse_item)
        yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(self.info_dict|self.page_dict)}", priority=2,
                             callback=self.pages_urls)

    def pages_urls(self, response):
        try:
            total = json.loads(response.text).get("realCount")
            pages = int(total) // 100 + 1
            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            # for page in range(1, pages + 1):
            page = 2
            page_dict = {'pageNo': str(page)}
            url=f"{self.query_url}{urllib.parse.urlencode(self.info_dict| page_dict)}"
            yield scrapy.Request(url=url,
                                 priority=6, callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            info_list = json.loads(response.text).get("articles")
            for item in info_list:
                title_name = item.get("title", "")
                project_number = item.get("projectCode", "")
                info_url = item.get("url", "")
                typeName = item.get("typeName", "")
                projectName = item.get("projectName", "")
                districtName = item.get("districtName", "")
                yield scrapy.Request(url=info_url, priority=10, callback=self.parse_item)


            # li_list = response.xpath('//div[@class="c1-body"]/li')
            # for li in li_list:
            #     title_name = li.xpath('./a/@title').get()
            #     all_info_url = self.domain_url + li.xpath('./a/@href').get()
            #     pub_time = li.xpath('./span[@class="date"]/text()').get()
            #     if re.search(r'变更| 更正| 澄清', title_name):
            #         notice_type = const.TYPE_ZB_ALTERATION
            #     elif re.search(r'候选人', title_name):
            #         notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            #     elif re.search(r'中标结果| 中选公示', title_name):
            #         notice_type = const.TYPE_WIN_NOTICE
            #     elif re.search(r'终止| 中止 | 终结', title_name):
            #         notice_type = const.TYPE_ZB_ABNORMAL
            #     elif re.search(r'预公示| 预告', title_name):
            #         notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            #     else:
            #         notice_type = response.meta['notice']
            #     yield scrapy.Request(url=all_info_url, callback=self.parse_item,
            #                          meta={'notice_type': notice_type, 'pub_time': pub_time,
            #                                'title_name': title_name, 'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            category = response.meta['category']
            notice_type = response.meta['notice_type']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            contents = response.xpath("//div[@style='width: 100%; overflow: auto']").get()
    #
    #         # title_names = ''.join(re.findall('项目名称：(.*?)</.*>', contents)).strip() or re.findall('项目名称：.*>$(.*?)</.*>', contents) or \
    #         #               re.findall('项目名称：.*>$(.*?)<.*>', contents) or re.findall('项目名称：.*">$(.*?)</.*>', contents)

            files_path = {}
            if response.xpath('//div[@style="width: 100%; overflow: auto"]//img/@src'):
                conet_list = response.xpath('//div[@style="width: 100%; overflow: auto"]//img')
                for con in conet_list:
                    if 'http' in con.xpath('./@src').get():
                        value = con.xpath('./@src').get()
                    else:
                        value = self.domain_url + con.xpath('./@src').get()
                    if con.xpath('./@alt').get():
                        keys = con.xpath('./@alt').get()
                    else:
                        keys = 'img/pdf/doc/xls'
                    files_path[keys] = value
            else:
                files_path = ''
            if response.xpath('//div[@style="width:300px;margin:0 auto;"]/a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href'):
                conet_list = response.xpath('//div[@style="width:300px;margin:0 auto;"]//a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href')
                for con in conet_list:
                    if 'http' in con.xpath('./@href').get():
                        value = con.xpath('./@href').get()
                    else:
                        value = self.domain_url + con.xpath('./@href').get()
                    keys = con.xpath('./b/text()').get() or con.xpath('./span/text()').get()
                    files_path[keys] = value
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3302_zjcaigou_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3305_ningbo_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))

