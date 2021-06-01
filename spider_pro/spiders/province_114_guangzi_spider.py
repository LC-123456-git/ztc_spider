# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-05-13
# @Describe: 广咨 - 全量/增量脚本
import re
import math
import json
import lxml.html as LH
import requests
import scrapy
import random
import datetime
import urllib
from urllib import parse
from lxml import etree
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'province_114_guangzi_spider'
    area_id = "114"
    domain_url = "https://www.gzebid.cn/"
    list_url = "https://www.gzebid.cn/web-list/categorys"
    query_url = "https://www.gzebid.cn/web-list/articles?"
    info_url = "https://www.gzebid.cn/web-detail/noticeDetail?"
    orgin_url = "https://www.gzebid.cn/web-detail/frontDetail?articleId="
    allowed_domains = ['www.gzebid.cn']

    area_province = "广咨电子招投标交易平台"



    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公告']
    # 招标异常
    list_alteration_category_num = ['废标/终止公示']
    # 招标变更
    list_zb_abnormal_num = ['变更澄清', "项目答疑"]
    # 中标预告
    list_win_advance_notice_num = ['中标公示']
    # 资格预审结果公告
    list_qualification_num = ['预审公告']
    # 其他公告
    list_others_notice_num = ["其他公告", "其他公示", "评标结果公示"]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"parentId": "7247b4549b0344acbc40b8f82abf6a7a"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        # all_url = 'http://hb.zcjb.com.cn/cms/channel/jsgczb/2100821.htm'
        # yield scrapy.Request(url=all_url, callback=self.parse_item)
        yield scrapy.FormRequest(url=self.list_url, priority=2, formdata=self.r_dict, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            if json.loads(response.text).get("success"):
                data_list = json.loads(json.loads(response.text).get("data")).get("rows")
                for item in data_list:
                    categoryId = item.get("id")
                    name = item.get("name")
                    if self.enable_incr:
                        data_dict = {"categoryId": categoryId, "pageNumber": "1", "pageSize": 100, "title": "",
                                     "pubshTime": self.sdt_time}
                        yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=5,
                                         callback=self.parse_info, meta={"notice_type": name,
                                                                              "categoryId": categoryId})
                    else:
                        data_dict = {"categoryId": categoryId, "pageNumber": "1", "pageSize": "15", "title": "",
                                     "pubshTime": ""}
                        yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=6,
                                             callback=self.parse_pages, meta={"notice_type": name,
                                                                                  "categoryId": categoryId})
            else:
                self.logger.error(f"发起数据请求失败 {response.url=}")
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_pages(self, response):
        if json.loads(response.text).get("message") == "成功":
            categoryId = response.meta["categoryId"]
            notice_type = response.meta["notice_type"]
            total = json.loads(json.loads(response.text).get("data")).get("total")
            pages = total // 100 + 1
            self.logger.info(f"本次获取总条数为：{total} ")
            for num in range(1, pages):
                data_dict = {"categoryId": categoryId, "pageNumber": num, "pageSize": "100", "title": "", "pubshTime": ""}
                yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=8,
                                     callback=self.parse_info, meta={"notice_type": notice_type,
                                                                          "categoryId": categoryId})


    def parse_info(self, response):
        try:
            if json.loads(response.text).get("success"):
                data_list = json.loads(json.loads(response.text).get("data")).get("rows")
                categoryId = response.meta["categoryId"]
                notice_type = response.meta["notice_type"]
                for item in data_list:
                    info_id = item.get("id")
                    pub_time = item.get("publishTime")
                    title_name = item.get("noticeName")
                    data_dict = {"id": info_id}
                    yield scrapy.Request(url=f"{self.info_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                         callback=self.parse_item, meta={"notice_type": notice_type,
                                         "pub_time": pub_time, "title_name": title_name, "categoryId": categoryId,
                                                                         "info_id": info_id})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if json.loads(response.text).get("success"):
            content = json.loads(json.loads(response.text).get("data")).get("context")
            info_id = response.meta['info_id']
            origin = self.orgin_url + info_id
            info_source = self.area_province
            notice_type = response.meta['notice_type']

            # classifyShow = response.meta.get("classifyShow", "")
            title_name = response.meta.get("title_name", "")
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)

            files_path = {}
            a_list = re.findall('<a href="https://jy.gzebid.cn:443/bid/attachment/download\?id=[0-9a-zA-Z]{0,32}">.*?</a>', content)
            for item in a_list:
                doc = etree.HTML(item)
                key = doc.xpath("//a/text()")[0]
                value = doc.xpath("//a/@href")[0]
                # value = re.findall("https://jy.gzebid.cn:443/bid/attachment/download\?id=[0-9a-zA-Z]{0,32}", item)
                files_path[key] = value
            # if response.xpath('//div[@id="filediv1"]'):
            #     str_content = response.xpath("//div[@id='filediv1']//a")
            #     for con in str_content:
            #         if 'http' not in con.xpath('./@href').get():
            #             if con.xpath('./@href').get():
            #                 value = self.domain_url + con.xpath('./@href').get()
            #                 keys = con.xpath('.//text()').get()
            #                 files_path[keys] = value
            #             else:
            #                 value = con.xpath('./@href').get()
            #                 keys = con.xpath('.//text()').get()
            #                 files_path[keys] = value

            if notice_type in ['招标公告', '采购公告']:
                notice_type = const.TYPE_ZB_NOTICE
            elif notice_type in ['中标公告']:
                notice_type = const.TYPE_WIN_NOTICE
            elif notice_type in ['废标/终止公示']:
                notice_type = const.TYPE_ZB_ABNORMAL
            elif notice_type in ['变更澄清', "项目答疑"]:
                notice_type = const.TYPE_ZB_ALTERATION
            elif notice_type in ['中标公示']:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif notice_type in ["其他公告", "其他公示", "评标结果公示"]:
                notice_type = const.TYPE_OTHERS_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE

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
            # notice_item["category"] = classifyShow


            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_114_guangzi_spider -a sdt=2021-05-24".split(" "))




