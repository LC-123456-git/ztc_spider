# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-06-08
# @Describe: 旺采 - 全量/增量脚本
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
    name = 'province_85_wangcai_spider'
    area_id = "85"
    domain_url = "http://m.zgazxxw.com"
    list_url = "https://sx.5ibid.net/Liems/{}/{}.html?"
    # query_url = "https://www.gzebid.cn/web-list/articles?"
    # info_url = "https://www.gzebid.cn/web-detail/noticeDetail?"
    # orgin_url = "https://www.gzebid.cn/web-detail/frontDetail?articleId="
    allowed_domains = ['m.zgazxxw.com']

    area_province = "安装信息网"



    # 招标公告
    list_notice_category_num = ['/zbpd/zbgg/']
    # 中标公告
    list_win_notice_category_num = ['/zbpd/zhongbgg/']
    # 招标变更
    list_zb_abnormal_num = ['/zbpd/bggg/']
    # 招标预告
    list_advance_notice_code = ['/zbpd/zbyg/"']
    # 其他
    list_qita_code = ["/zbpd/mfgg/"]


    all_list = list_notice_category_num + list_win_notice_category_num + list_advance_notice_code + \
               list_zb_abnormal_num + list_qita_code

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        # cookies_str = 'jsessionid_dzsw=q77lD-l-qR6PZeyvq5yqV2OXyGLpcWQ782HMVAYubWYoYT_KpFYf!-1912950762; ck=d9b08bef01d47609182f128ac9effc7fce91d73fa37b7caef862bc4f468116f57b4375c088582974398ba24c5f92493a; JSESSIONID=ea7cacb1-d39b-4757-95e4-b698208ea06a' # 抓包获取
        # # 将cookies_str转换为cookies_dict
        # self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}

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
            list_url = self.domain_url + item
            yield scrapy.Request(url=list_url, priority=2, dont_filter=True,meta={"item": item}, callback=callback_url)

    def parse_pages(self, response):
        try:
            list_url = response.url
            item = response.meta["item"]
            Total = response.xpath("//div[@class='pagination']/a/b/text()").get()
            pages = int(Total) // 25 + 1
            for page in range(1, int(pages) + 1):
                if page == 1:
                    yield scrapy.Request(url=list_url, priority=6, dont_filter=True, callback=self.get_info_url, meta={"item": item})
                else:
                    page_list_url = list_url + "index_{}.html".format(page)
                    yield scrapy.Request(url=page_list_url, priority=6,
                                      dont_filter=True, callback=self.get_info_url, meta={"item": item})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def extract_data_urls(self, response):
        info_list = response.xpath("//div[@class='w_list']/div[@class='list_con zx_marb']")
        item = response.meta["item"]
        Total = response.xpath("//div[@class='pagination']/a/b/text()").get()
        pages = int(Total) // 25 + 1
        count_num = 0
        currentPage = 1
        for info_item in info_list:
            pub_time = info_item.xpath("./p[@class='info']/span[2]/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                info_url_str = info_item.xpath("./p[@class='lt_title zx']/a/@href").get()
                info_url = self.domain_url + info_url_str
                info_source = info_item.xpath("./p[@class='info']/span[1]/a/text()").get()
                title_name = info_item.xpath("./p[@class='lt_title zx']/a/text()").get()
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True, priority=100,
                                     meta={"item": item, "title_name": title_name, "pub_time": pub_time,
                                           "info_source": info_source})
                if count_num >= len(info_list):
                    next_page = currentPage + 1
                    if next_page <= int(pages):
                        list_url = response.url
                        page_list_url = list_url + "index_{}.html".format(next_page)
                        yield scrapy.Request(url=page_list_url, priority=6,
                                         dont_filter=True, callback=self.get_info_url, meta={"item": item})

    def get_info_url(self, response):
        try:
            info_list = response.xpath("//div[@class='w_list']/div[@class='list_con zx_marb']")
            item = response.meta["item"]
            for info_item in info_list:
                info_url_str = info_item.xpath("./p[@class='lt_title zx']/a/@href").get()
                info_url = self.domain_url + info_url_str
                info_source = info_item.xpath("./p[@class='info']/span[1]/a/text()").get()
                title_name = info_item.xpath("./p[@class='lt_title zx']/a/text()").get()
                pub_time = info_item.xpath("./p[@class='info']/span[2]/text()").get()
                pub_time = get_accurate_pub_time(pub_time)
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True, priority=100,
                                     meta={"item": item, "title_name": title_name, "pub_time": pub_time,
                                           "info_source": info_source})
        except Exception as e:
            print(e)

    def parse_item(self, response):
        origin = response.url
        title_name = response.meta["title_name"]
        print(title_name)
        pub_time = response.meta["pub_time"]
        notice_type = response.meta["item"]
        content = response.xpath("//div[@class='zhengwen']").get()
        if re.search("null", content):
            content = re.sub("null", "", content)
        info_source = response.meta["info_source"]
        info_source = self.area_province + "-" + info_source
        if notice_type in ['/zbpd/zbgg/']:
            notice_type = const.TYPE_ZB_NOTICE
        elif notice_type in ['/zbpd/zhongbgg/']:
            notice_type = const.TYPE_WIN_NOTICE
        elif notice_type in ['/zbpd/zbyg/"']:
            notice_type = const.TYPE_ZB_ADVANCE_NOTICE
        elif notice_type in ['/zbpd/bggg/']:
            notice_type = const.TYPE_ZB_ALTERATION
        elif notice_type in ["/zbpd/mfgg/"]:
            notice_type = const.TYPE_OTHERS_NOTICE
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
        # notice_item["category"] = classifyShow
        yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_85_wangcai_spider -a sdt=2021-06-01 -a edt=2021-06-09".split(" "))
    # cmdline.execute("scrapy crawl province_85_wangcai_spider".split(" "))



