#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-06-15
# @Describe: 北京海淀区公共资源交易网
import re
import math
import json
import scrapy
import urllib
import requests
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(Spider):
    name = "BJ_city_1101_haiding_spider"
    area_id = "1101"
    area_province = "北京-海淀区公共资源交易信息网"
    allowed_domains = ['hzctc.cn']
    count_url = "http://www.bjhd.gov.cn/ggzyjy/queryContent_{}-jyfw.jspx?title=&channelId={}"
    # project_category_list = ["116"]
    project_category_list = ["116", "123"]  # 116 政府采购   123 房建市政

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.num = 0
        self.currentPage = 1
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
        for item in self.project_category_list:
            yield scrapy.Request(self.count_url.format("1", item),  callback=callback_url, priority=7,
                                     meta={"afficheType": str(item)})
        # yield scrapy.Request(url="http://www.bjhd.gov.cn:80/ggzyjy/zfcgCjgs/18504059.jhtml", callback=self.parse_item)

    def extract_data_urls(self, response):
        pages_str = response.xpath("//ul[@class='pages-list']/li/a/text()").get()
        pages = int(re.findall("/(\w+)页", pages_str)[0])
        temp_list = response.xpath("//ul[@class='article clearfix']/li")
        afficheType = response.meta["afficheType"]
        count_num = 0
        for item in temp_list:
            pub_time = item.xpath("./div[2]/p[2]/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                title_name = item.xpath("./div/a/@title").get()
                pub_time = item.xpath("./div[2]/p[2]/text()").get()
                info_url = item.xpath("./div/a/@href").get()
                category_num = item.xpath("./@class").get()
                yield scrapy.Request(url=info_url, priority=10, callback=self.parse_item, dont_filter=True,
                                     meta={"pub_time": pub_time, "title_name": title_name, "category_num": category_num,
                                           "afficheType": afficheType})
            if count_num >= len(temp_list):
                self.currentPage = self.currentPage + 1
                if self.currentPage <= int(pages):
                    yield scrapy.Request(self.count_url.format(self.currentPage, afficheType),  callback=self.extract_data_urls, priority=100,
                                         dont_filter=True, meta={"afficheType": str(afficheType)})

    def parse_urls(self, response):
        try:
            item = response.meta["afficheType"]
            pages_str = response.xpath("//ul[@class='pages-list']/li/a/text()").get()
            pages = int(re.findall("/(\w+)页", pages_str)[0])
            ttlrow = int(re.findall("共(\w+)条记录", pages_str)[0])
            self.logger.info(f"本次获取总条数为：{ttlrow},共有{pages}页")
            for i in range(1, pages):
                yield scrapy.Request(self.count_url.format(i, item), dont_filter=True, callback=self.parse_data_urls, priority=7,
                                     meta={"afficheType": str(item)})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            temp_list = response.xpath("//ul[@class='article clearfix']/li")
            afficheType = response.meta["afficheType"]
            for item in temp_list:
                title_name = item.xpath("./div/a/@title").get()
                pub_time = item.xpath("./div[2]/p[2]/text()").get()
                info_url = item.xpath("./div/a/@href").get()
                category_num = item.xpath("./@class").get()
                yield scrapy.Request(url=info_url, priority=10, callback=self.parse_item, dont_filter=True,
                                     meta={"pub_time": pub_time, "title_name": title_name, "category_num": category_num,
                                           "afficheType": afficheType})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            title_name = response.meta.get("title_name")
            print(origin + "  " + title_name)
            pub_time = response.meta.get("pub_time")
            info_source = self.area_province
            content = response.xpath("//div[@class='content2']/div[3]").get()
            category_num = response.meta.get("category_num")
            afficheType = response.meta.get("afficheType")
            files_path = {}
            file_list = re.findall("""<a href="(.*?)" target="_blank" class="t1">(.*?)</a>""", content)
            for item in file_list:
                files_path[item[1]] = item[0]

            if category_num == "zt1":
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif category_num == "zt2":
                notice_type = const.TYPE_ZB_NOTICE
            elif category_num == "zt4":
                notice_type = const.TYPE_ZB_ALTERATION
            elif category_num in ["zt6", "zt10"]:
                notice_type = const.TYPE_WIN_NOTICE
            elif category_num == "zt5":
                notice_type = const.TYPE_OTHERS_NOTICE
            elif category_num == "zt3":
                notice_type = const.TYPE_ZB_ABNORMAL
            elif category_num == "zt9":
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE
            if re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            if afficheType == "116":
                category = "政府采购"
            else:
                category = "房建市政"

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl BJ_city_1101_haiding_spider -a sdt=2021-06-11 -a edt=2021-06-16".split(" "))
    cmdline.execute("scrapy crawl BJ_city_1101_haiding_spider".split(" "))
