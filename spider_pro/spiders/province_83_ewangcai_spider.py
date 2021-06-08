# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-06-01
# @Describe: e招冀成 - 全量/增量脚本
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
    name = 'province_83_wangcai_spider'
    area_id = "83"
    domain_url = "https://sx.5ibid.net"
    list_url = "https://sx.5ibid.net/Liems/{}/{}.html?"
    # query_url = "https://www.gzebid.cn/web-list/articles?"
    # info_url = "https://www.gzebid.cn/web-detail/noticeDetail?"
    # orgin_url = "https://www.gzebid.cn/web-detail/frontDetail?articleId="
    allowed_domains = ['sx.5ibid.net']

    area_province = "山西-旺采网"



    # 招标公告
    # list_notice_category_num = ['sxggList', ]
    # 中标公告
    list_win_notice_category_num = ['sxzbjgList']
    # 中标预告
    list_win_advance_notice_num = ['sxzbhxList']
    # 招标变更
    list_zb_abnormal_num = ['sxbgggList']
    all_list = list_win_notice_category_num + list_win_advance_notice_num + \
           list_zb_abnormal_num
    # all_list = list_notice_category_num + list_win_notice_category_num + list_win_advance_notice_num + \
    #            list_zb_abnormal_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"parentId": "7247b4549b0344acbc40b8f82abf6a7a"}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            'cookie': 'jsessionid_dzsw=q77lD-l-qR6PZeyvq5yqV2OXyGLpcWQ782HMVAYubWYoYT_KpFYf!-1912950762; ck=d9b08bef01d47609182f128ac9effc7fce91d73fa37b7caef862bc4f468116f57b4375c088582974398ba24c5f92493a; JSESSIONID=ea7cacb1-d39b-4757-95e4-b698208ea06a'}

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
            callback_url = self.parse_pages
        for item in self.all_list:
            for pattern in [0, 1]:
                info_dict = {"yfFlg": pattern}
                yield scrapy.Request(url=f"{self.list_url.format(item,1)}{urllib.parse.urlencode(info_dict)}", priority=2,
                                     headers=self.headers,
                                     dont_filter=True, meta={"item": item, "pattern": pattern}, callback=callback_url)

    def parse_pages(self, response):
        try:
            pages = response.xpath("//div[@class='PagerWrap']/ul/li[7]/div/text()").get()
            item = response.meta["item"]
            pattern = response.meta["pattern"]
            for page in range(1, int(pages) + 1):
                info_dict = {"yfFlg": pattern}
                yield scrapy.Request(url=f"{self.list_url.format(item, page)}{urllib.parse.urlencode(info_dict)}", priority=6,
                                     headers=self.headers, dont_filter=True, callback=self.get_info_url, meta={"item": item})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def extract_data_urls(self, response):
        info_list = response.xpath("//td[@id='tdcontent']/table/tr")
        pages = re.findall("totalPageNums = (\w+)", response.text)[0]
        item = response.meta["item"]
        count_num = 0
        currentPage = 1
        for info_item in info_list:
            pub_time = info_item.xpath("./td/ul/li/span[2]/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                info_url = info_item.xpath("./td/ul/li/a/@href").get()
                title_name = info_item.xpath("./td/ul/li/a/text()").get()
                classifyShow = info_item.xpath("./td/ul/li/span[1]/text()").get()
                pub_time = info_item.xpath("./td/ul/li/span[2]/text()").get()
                info_url = self.domain_url + info_url
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True, priority=10,
                                     meta={"item": item, "title_name": title_name, "pub_time": pub_time,
                                           "classifyShow": classifyShow})
                if count_num >= len(info_list):
                    next_page = currentPage + 1
                    if next_page <= pages:
                        info_dict = {"title": "", "lx": "0", "CategoryNum": item, "Paging": next_page}
                        yield scrapy.Request(url=f"{self.list_url}{urllib.parse.urlencode(info_dict)}", priority=6,
                                             dont_filter=True, callback=self.extract_data_urls, meta={"item": item})

    def get_info_url(self, response):
        info_list = response.xpath("//div[@class='Bodyer']/div")
        item = response.meta["item"]
        for info_item in info_list:
            info_url_str = info_item.xpath("./@onclick").get()
            info_url = re.split("'", info_url_str)[1].split("?yfFlg=0")[0]
            info_source_str = info_item.xpath("//div[@class='Row-2']/span[3]/text()").get()
            info_source = info_source_str.split("项目地区：")[1]
            title_name = "".join(info_item.xpath("./div[@class='Row-1']/text()").extract()).strip()
            # classifyShow = info_item.xpath("./td/ul/li/span[1]/text()").get()
            pub_time = "".join(info_item.xpath("//div[@class='Row-3']/text()").get()).strip()
            pub_time = get_accurate_pub_time(pub_time)
            info_url = self.domain_url + info_url
            yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True, priority=10, headers=self.headers,
                                 meta={"item": item, "title_name": title_name, "pub_time": pub_time,
                                       "info_source": info_source})

    def parse_item(self, response):
        origin = response.url
        print(response.text)
        title_name = response.meta["title_name"]
        print(title_name)
        pub_time = response.meta["pub_time"]
        pub_time = get_accurate_pub_time(pub_time)
        classifyShow = response.meta["classifyShow"]
        notice_type = response.meta["item"]
        content = response.xpath("//div[@class='contents']").get()
        info_source = self.area_province
        if notice_type in ['016001']:
            notice_type = const.TYPE_ZB_NOTICE
        elif notice_type in ['016004']:
            notice_type = const.TYPE_WIN_NOTICE
        elif notice_type in ['016006']:
            notice_type = const.TYPE_ZB_ABNORMAL
        elif notice_type in ['016002', '016003']:
            notice_type = const.TYPE_ZB_ALTERATION
        else:
            notice_type = const.TYPE_UNKNOWN_NOTICE
        files_path = {}

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
    # cmdline.execute("scrapy crawl province_76_ezhaojicheng_spider -a sdt=2021-05-31 -a edt=2021-06-01".split(" "))
    cmdline.execute("scrapy crawl province_83_wangcai_spider".split(" "))



