#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2021-01-11
# @Describe: 速度测试脚本

import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider, CrawlSpider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = "a_speed_test_spider"
    area_id = "999"
    allowed_domains = ['www.baidu.com']
    domain_url = "https://www.baidu.com/"
    timeout = 10

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

    def start_requests(self):
        for i in range(1, 100000):
            yield scrapy.Request(url=self.domain_url, callback=self.parse_item, meta={"id": f"{i}"}, dont_filter=True)

    def parse_item(self, response):
        """
        :param response: response
        :return: 回调函数
        """
        notice_item = NoticesItem()
        notice_item["origin"] = "orgin"
        notice_item["title_name"] = "title_name"
        notice_item["pub_time"] = "1970-01-01"
        notice_item["info_source"] = "info_source"
        notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = ""
        notice_item["content"] = "content"
        notice_item["area_id"] = self.area_id
        notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL

        yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl a_speed_test_spider".split(" "))
