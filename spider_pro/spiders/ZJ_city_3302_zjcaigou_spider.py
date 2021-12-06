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
from lxml import etree

class MySpider(CrawlSpider):
    name = 'ZJ_city_3302_zjcaigou_spider'
    area_id = "3302"
    domain_url = "https://zfcg.czt.zj.gov.cn/"
    query_url = "https://zfcgmanager.czt.zj.gov.cn/cms/api/cors/remote/results?"
    allowed_domains = ['zfcg.czt.zj.gov.cn']
    area_province = "浙江政府采购网"

    # 招标预告
    list_advance_notice = ['10016', '3014']
    # 招标公告
    list_notice_category_num = ['3012,1002,1003', '3001,3020', '3003,3002,3011', '10001,10002,10012,10003,10014,10004,10013', '10006,10007,10008,10009,10010,10011']
    # 招标变更
    list_zb_abnormal_code = ["3017,3018,3005,3006,3015", '']
    # 招标异常
    list_alteration_category_num = ["3007,3015"]
    # 中标公告
    list_win_notice_category_code = ['3004,4005,4006', '中标公告', '', '结果公示', '', '']
    # 资格预审
    list_qualification_num = ['3009,4004,3008,2001', ]
    # 其他
    list_qita_code = ['3013', '3010', "3016,6003", '4002,4001,4003,8006', "1995,1996,1997,8008,8009,8013,8014,9002,9003,808030100"]
    # all_list = list_advance_notice + list_notice_category_num + list_zb_abnormal_code + list_alteration_category_num + \
    #            list_win_notice_category_code + list_qualification_num + list_qita_code
    all_list = ['3001,3020']


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
                    "isGov": "true", "pubDate": self.pubDate, "endDate": self.endDate, "isExact": "1", "url": "notice"}
        self.page_dict = {"pageNo": "1"}

    def start_requests(self):
        # url = 'http://bidding.ningbo.gov.cn/cms/qtzbjg/169060.htm'
        # yield scrapy.Request(url=url, callback=self.parse_item)
        for item in self.all_list:
            self.type_dict = {"sourceAnnouncementType": item}
            yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(self.info_dict|self.page_dict|self.type_dict)}",
                                 priority=2, callback=self.pages_urls, meta={"type_dict": self.type_dict})

    def pages_urls(self, response):
        try:
            total = json.loads(response.text).get("realCount")
            pages = int(total) // 100 + 1
            type_dict = response.meta["type_dict"]
            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            for page in range(1, pages + 1):
            # page = 2
                page_dict = {'pageNo': str(page)}
                url = f"{self.query_url}{urllib.parse.urlencode(self.info_dict| page_dict|type_dict)}"
                yield scrapy.Request(url=url, priority=6, dont_filter=True, callback=self.parse_data_urls,
                                     meta={"type_dict": type_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            info_list = json.loads(response.text).get("articles")
            type_dict = response.meta["type_dict"].get("sourceAnnouncementType")
            if type_dict in self.list_advance_notice:
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif type_dict in self.list_notice_category_num:
                notice_type = const.TYPE_ZB_NOTICE
            elif type_dict in self.list_zb_abnormal_code:
                notice_type = const.TYPE_ZB_ALTERATION
            elif type_dict in self.list_alteration_category_num:
                notice_type = const.TYPE_ZB_ABNORMAL
            elif type_dict in self.list_win_notice_category_code:
                notice_type = const.TYPE_WIN_NOTICE
            elif type_dict in self.list_qualification_num:
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif type_dict in self.list_qita_code:
                notice_type = const.TYPE_OTHERS_NOTICE
            else:
                notice_type =const.TYPE_UNKNOWN_NOTICE

            for item in info_list:
                title_name = item.get("title", "")
                project_number = item.get("projectCode", "")
                info_url = item.get("url", "")
                info_id = item.get("id", "")
                projectName = item.get("projectName", "")
                districtName = item.get("districtName", "")
                yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode({'noticeId':info_id, 'url': 'noticeDetail'})}"
                                     , priority=10, callback=self.parse_item, dont_filter=True,
                                     meta={"notice_type": notice_type, "title_name": title_name,
                                           "project_number": project_number, "projectName": projectName,
                                           "districtName": districtName, "info_url": info_url})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            response_dict = json.loads(response.text)
            origin = response.meta["info_url"]
            pub_time = response_dict.get("noticePubDate", "")
            pub_time = get_accurate_pub_time(pub_time)
            info_source = self.area_province
            title_name = response.meta["title_name"]
            print(origin + title_name + pub_time)
            notice_type = response.meta["notice_type"]
            project_number = response.meta["project_number"]
            projectName = response.meta["projectName"]
            content = response_dict.get("noticeContent", "")
            if project_number == "normal" or projectName == "normal":
                project_number = ""
                projectName = ""
            districtName = response.meta["districtName"]
            if districtName:
                info_source = self.area_province + "_" + districtName

            files_path = {}
            if fjxx_list := re.findall('<a href="(.*?)">(.*?)</a>', content):
                for fjxx in fjxx_list:
                    file_url = fjxx[0]
                    file_name = fjxx[1]
                    files_path[file_name] = file_url

            #     conet_list = response.xpath('//div[@style="width: 100%; overflow: auto"]//img')
            #     for con in conet_list:
            #         if 'http' in con.xpath('./@src').get():
            #             value = con.xpath('./@src').get()
            #         else:
            #             value = self.domain_url + con.xpath('./@src').get()
            #         if con.xpath('./@alt').get():
            #             keys = con.xpath('./@alt').get()
            #         else:
            #             keys = 'img/pdf/doc/xls'
            #         files_path[keys] = value
            # else:
            #     files_path = ''
            # if response.xpath('//div[@style="width:300px;margin:0 auto;"]/a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href'):
            #     conet_list = response.xpath('//div[@style="width:300px;margin:0 auto;"]//a') or response.xpath('//div[@style="width: 100%; overflow: auto"]//a/@href')
            #     for con in conet_list:
            #         if 'http' in con.xpath('./@href').get():
            #             value = con.xpath('./@href').get()
            #         else:
            #             value = self.domain_url + con.xpath('./@href').get()
            #         keys = con.xpath('./b/text()').get() or con.xpath('./span/text()').get()
            #         files_path[keys] = value
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
            notice_item["project_number"] = project_number
            notice_item["project_name"] = projectName
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl ZJ_city_3302_zjcaigou_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3302_zjcaigou_spider -a sdt=2021-06-18 -a edt=2021-06-28".split(" "))

