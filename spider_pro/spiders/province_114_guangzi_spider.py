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
    allowed_domains = ['www.gzebid.cn']

    area_province = "广咨电子招投标交易平台"



    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公告', '成交公告', '公示公告']
    # 招标异常
    list_alteration_category_num = ['流标公告']
    # 招标变更
    list_zb_abnormal_num = ['变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 资格预审结果公告
    list_qualification_num = ['预审公告']
    # 其他公告
    list_others_notice_num = []

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
        yield scrapy.FormRequest(url=self.list_url, formdata=self.r_dict, callback=self.parse_urls)

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
                        yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                         callback=self.parse_info, meta={"classifyShow": name,
                                                                              "categoryId": categoryId})
                    else:
                        data_dict = {"categoryId": categoryId, "pageNumber": "1", "pageSize": "15", "title": "",
                                     "pubshTime": ""}
                        yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                             callback=self.parse_pages, meta={"classifyShow": name,
                                                                                  "categoryId": categoryId})
            else:
                self.logger.error(f"发起数据请求失败 {response.url=}")
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_pages(self, response):
        if json.loads(response.text).get("message") == "成功":
            categoryId = response.meta["categoryId"]
            classifyShow = response.meta["classifyShow"]
            total = json.loads(response.text).get("total")
            pages = total/100 + 1
            self.logger.info(f"本次获取总条数为：{total} ")
            for num in range(1, pages):
                data_dict = {"categoryId": categoryId, "pageNumber": num, "pageSize": "100", "title": "", "pubshTime": ""}
                yield scrapy.Request(url=f"{self.query_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                     callback=self.parse_info, meta={"classifyShow": classifyShow,
                                                                          "categoryId": categoryId})


    def parse_info(self, response):
        try:
            if json.loads(response.text).get("success"):
                data_list = json.loads(json.loads(response.text).get("data")).get("rows")
                categoryId = response.meta["categoryId"]
                classifyShow = response.meta["classifyShow"]
                for item in data_list:
                    info_id = item.get("id")
                    pub_time = item.get("publishTime")
                    title_name = item.get("noticeName")
                    data_dict = {"id": info_id}
                    yield scrapy.Request(url=f"{self.info_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                         callback=self.parse_item, meta={"classifyShow": classifyShow,
                                         "pub_time": pub_time, "title_name": title_name, "categoryId": categoryId})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if json.loads(response.text).get("success"):
            content = json.loads(response.text).get("context")

            origin = response.url
            info_source = response.meta['info_source']
            if info_source:
                info_source = self.area_province + response.meta['info_source']
            else:
                info_source = self.area_province
            notice_type = response.meta['notice_type']
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta['put_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)

            content = response.xpath('//div[@class="article-content"]').get()
            # 去除第一个广告
            pattern = re.compile(r'<a class="broadcast_flb_05".*?>(.*?)</a>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除title
            pattern = re.compile(r'<div class="article-title"*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除 发布时间
            pattern = re.compile(r'<div class="article-author"*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除最后一个广告
            pattern = re.compile(r'<div class="article-bottom"*?>(.*?)</a>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<div class="fileDownload"*?>(.*?)</table>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除隐藏表格
            pattern = re.compile(r'<h3>(.*?)</i>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            pattern = re.compile(r'<div class="modalBody">(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            list_name = ['本公告发布媒体', '发布媒介']
            for name in list_name:
                if name in content:
                    pattern = re.compile(fr'{name}[:|：].*?</p>', re.S)
                    content = content.replace(''.join(re.findall(pattern, content)), '')


            files_path = {}
            if response.xpath('//div[@id="filediv1"]'):
                str_content = response.xpath("//div[@id='filediv1']//a")
                for con in str_content:
                    if 'http' not in con.xpath('./@href').get():
                        if con.xpath('./@href').get():
                            value = self.domain_url + con.xpath('./@href').get()
                            keys = con.xpath('.//text()').get()
                            files_path[keys] = value
                        else:
                            value = con.xpath('./@href').get()
                            keys = con.xpath('.//text()').get()
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
            notice_item["category"] = classifyShow


            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_114_guangzi_spider".split(" "))




