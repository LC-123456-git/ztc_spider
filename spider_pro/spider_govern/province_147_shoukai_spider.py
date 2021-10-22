#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-10-20
# @Describe: 首开工程 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import datetime
import requests
from lxml import etree
from ast import literal_eval
import urllib
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval, file_notout_time
from urllib.parse import quote

class MySpider(CrawlSpider):
    name = 'province_147_shoukai_spider'
    area_id = "147"
    domain_url = "http://ebidding.shoukaigufen.com.cn/"
    query_url = "http://ebidding.shoukaigufen.com.cn/skcms/category/bulletinList.html?"
    result_url = "http://ebidding.shoukaigufen.com.cn/skcms/category/resultBulletinList.html?"
    allowed_domains = ['ebidding.shoukaigufen.com.cn']
    area_province = "首开工程电子招标采购交易平台"
    # url_info_dict = {"searchDate": "2021-07-20", "dates": "90", "word": "", "categoryId": "91", "tabName": "废标公示"}
    notice_category_dict = {"dates": "300", "categoryId": "88", "tabName": "招标公告", "page": "1"}
    zb_alteration_dict = {"dates": "300", "categoryId": "88", "tabName": "变更公告", "page": "1"}
    win_advance_notice_dict = {"dates": "300", "categoryId": "88", "tabName": "中标公示", "page": "1"}
    zb_abnormal_dict = {"dates": "300", "categoryId": "88", "tabName": "废标公示", "page": "1"}
    url_list = [notice_category_dict, zb_alteration_dict, win_advance_notice_dict, zb_abnormal_dict]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.parse_urls
        yield scrapy.Request(
            url=f"{self.query_url}{urllib.parse.urlencode(self.notice_category_dict )}",
            priority=5, callback=callback_url, meta={"tab_name": self.notice_category_dict.get("tabName")})
        for url_item in self.url_list:
            yield scrapy.Request(
                url=f"{self.result_url}{urllib.parse.urlencode(url_item )}",
                priority=5, callback=callback_url, meta={"tabname": url_item.get("tabName")})


    def extract_data_urls(self, response):
        temp_list = response.xpath("recordset//record")
        category_num = response.meta["afficheType"]
        ttlrow = response.xpath("totalrecord/text()").get()
        startrecord = 1
        endrecord = 45
        count_num = 0
        for item in temp_list:
            info_url = re.findall('href="(.*?)"', item.get())[0]
            info_url = self.domain_url + "/" + info_url
            pub_time = re.findall('\d+\-\d+\-\d+', item.get())[0]
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                yield scrapy.Request(url=info_url, callback=self.parse_item,  dont_filter=True,
                                     priority=10, meta={"category_num": category_num, "pub_time": pub_time})
            if count_num >= len(temp_list):
                startrecord += 45
                endrecord += 45
                if endrecord <= int(ttlrow):
                    temp_dict = self.r_dict | {"columnid": "{}".format(category_num)}
                    yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                             dont_filter=True, callback=self.extract_data_urls, priority=8, cookies=self.cookies_dict,
                                             meta={"afficheType": category_num})

    def parse_urls(self, response):
        try:
            res_url = response.url
            a = quote(res_url,encoding="utf-8")
            print(a)
            tabname = response.meta["tabname"]
            pages = response.xpath("//div[@class='pages']/label/text()").get()
            self.logger.info(f"本次获取共有{pages}页")
            for page in range(1, int(pages)+1):
                page_url = re.sub("page=1", "page={}".format(page), res_url)
                yield scrapy.Request(url=page_url, priority=5, callback=self.parse_data_urls, meta={"tabname": tabname})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            temp_list = response.xpath("//ul[@class='newslist']/li/a")
            for item in temp_list:
                title_name = item.xpath("./h1/text()").get()
                year = item.xpath("./div[@class='newsDate']/div/text()").get()
                data_time_list = item.xpath("./div[@class='newsDate']/text()").getall()
                data_time = data_time_list[1].strip()
                info_url = item.xpath("./@href").get()
                pub_time = get_accurate_pub_time(year + "/" + data_time)
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                     priority=10, meta={"pub_time": pub_time, "title_name": title_name, "tabname": response.meta["tabname"]})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            print(origin)
            title_name = response.meta["title_name"]
            pub_time = response.meta["pub_time"]
            tabname = response.meta["tabname"]
            content_1 = response.xpath("//div[@id='main']/div[1]").get()
            content_2 = response.xpath("//div[@id='main']/div[2]").get()
            contents = content_1 + content_2
            files_path = {}
            try:
                if file_notout_time(pub_time):
                    # 招标文件正文
                    if picture_url := response.xpath("//div[@id='showPdf']/iframe/@src").get():
                        contents = contents + "<a href='{}'>公告内容</a>".format(picture_url)
                        file_name = "file_pdf.pdf"

                        files_path[file_name] = picture_url
            except Exception as e:
                print(e)
            if tabname == "招标公告":
                notice_type = const.TYPE_ZB_NOTICE
            elif tabname == "变更公告":
                notice_type = const.TYPE_ZB_ALTERATION
            elif tabname == "中标公示":
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif tabname == "废标公示":
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = const.TYPE_OTHERS_NOTICE

            if re.search(r"单一来源|询价|竞争性谈判|竞争性磋商", title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r"采购意向|需求公示", title_name):
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif re.search(r"候选人|评标结果", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充|延期|取消", title_name):
                notice_type = const.TYPE_ZB_ALTERATION



            classifyShow = "工程建设"

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = self.area_province
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            # print(type(files_path))
            # print(notice_item)
            # # TODO 产品要求推送，故注释
            # # if not is_clean:
            # #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_147_shoukai_spider".split(" "))
    # cmdline.execute("scrapy crawl province_147_shoukai_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))
