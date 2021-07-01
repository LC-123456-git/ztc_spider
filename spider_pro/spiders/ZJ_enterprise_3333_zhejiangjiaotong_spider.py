#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-07-01
# @Describe: 浙江省水利厅 - 全量/增量脚本
import re
import math
import json
import scrapy
import random
import datetime
from lxml import etree
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_enterprise_3333_zhejiangjiaotong_spider'
    area_id = "3333"
    domain_url = "http://jtyst.zj.gov.cn"
    query_url = "http://jtyst.zj.gov.cn/col/col1229248415/index.html?uid=6209196&pageNum={}"
    allowed_domains = ['jtyst.zj.gov.cn']
    area_province = "浙江-交通运输厅"

    # data = {'infotypeId': 'A1802', 'jdid': '3028', 'area': '002482285', 'divid': 'div1543161', 'standardXxgk': '1',
    #          'isAllList': '1', 'currpage': '1', 'sortfield': ',compaltedate:0'}

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
        self.payload={'col': '1',
                 'appid': '1',
                 'webid': '3234',
                 'columnid': '1229248415',
                 'sourceContentType': '1',
                 'unitid': '6209196',
                 'webname': '浙江交通',
                 'permissiontype': '0'}
        cookies_str = 'JSESSIONID=134AE590EC89389DFF7F9BA7B4CF767A; _zcy_log_client_uuid=419adb20-bf62-11eb-a2a7-4750d985d4a9; jskey=c7fc9280e90e247afc7f4b0046f6edb9; _gscu_1504213107=251037093lcx7317; _gscbrs_1504213107=1; ZJYHZXSESSIONID=ca40944e-abcd-45e0-923b-7c5ad63237a1; _gscs_1504213107=t25117890t4wyrj20|pv:3; SERVERID=57526053d080975751a9538d16dda0a7|1625118234|1625117888'
                      # 将cookies_str转换为cookies_dict
        self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.pages_urls
        yield scrapy.FormRequest(url="http://jtyst.zj.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=45&perpage=15",
                                 formdata=self.payload, priority=2, cookies=self.cookies_dict, callback=callback_url)

    def extract_data_urls(self, response):
        info_list = re.findall("""<a href="(.*?)".*?title='(.*?)'.*?<span>(.*?)</span>""", response.text)
        for item in info_list:
            title_name = item[1]
            info_url = item[0]
            pub_time = item[2]
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.pubDate, self.endDate)
            if x:
                info_url = re.sub("cnart", "cn/art", info_url)
                yield scrapy.Request(url=f"{info_url}", priority=10, dont_filter=True, callback=self.parse_item,
                                     meta={"title_name": title_name, "pub_time": pub_time})


    def pages_urls(self, response):
        try:
            total = response.xpath("totalrecord/text()").get()
            pages = int(total) % 45
            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            startrecord = 1
            endrecord = 45
            for page in range(1, pages):
                if page > 1:
                    startrecord += 45
                    endrecord += 45
                    if endrecord > int(total):
                        endrecord = int(total)
                yield scrapy.FormRequest(url="http://jtyst.zj.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=15".format(startrecord,endrecord),
                                         formdata=self.payload, priority=6, cookies=self.cookies_dict, dont_filter=True,
                                         callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            info_list = re.findall("""<a href="(.*?)".*?title='(.*?)'.*?<span>(.*?)</span>""", response.text)
            for item in info_list:
                title_name = item[1]
                info_url = item[0]
                pub_time = item[2]
                info_url = re.sub("cnart", "cn/art", info_url)
                yield scrapy.Request(url=f"{info_url}", priority=10, dont_filter=True, callback=self.parse_item,
                                     meta={"title_name": title_name, "pub_time": pub_time})
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)
            info_source = self.area_province
            title_name = response.meta["title_name"]
            print(origin + title_name + pub_time)
            content = response.xpath("//div[@id='zoom']").get()
            files_path = {}
            if fjxx_list := re.findall('<a href="(.*?)">(.*?)</a>', content):
                for fjxx in fjxx_list:
                    file_url = re.sub("amp;", "", self.domain_url + fjxx[0])
                    if re.search(">", fjxx[1]):
                        file_name = fjxx[1].split(">")[1]
                    else:
                        file_name = fjxx[1] + ".doc"
                    files_path[file_name] = file_url

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = const.TYPE_ZB_NOTICE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_enterprise_3333_zhejiangjiaotong_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_enterprise_3333_zhejiangjiaotong_spider -a sdt=2021-07-01 -a edt=2021-07-01".split(" "))

