#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2020-12-17
# @Describe: 北京市公共资源交易服务平台
import re
import urllib
from urllib import parse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider_pro.items import *
from spider_pro import constans as const


def process_value_s(value):
    try:

        value = value.split("location.href=")[0] + re.search("index_\d+\.html", value).group(0)
        # add_list(value)
        return value
    except:
        return value


def process_request_category(origin):
    for item in ["jyxxgcjszbjh", "jyxxggjtbyqs", "jyxxzbhxrgs", "jyxxzbgg", "jyxxgcjshtgs"]:
        if item in origin:
            classify_show = "工程建设"
            channelId = "121"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxcggg", "jyxxgzsx", "jyxxzbjggg"]:
        if item in origin:
            classify_show = "政府采购"
            channelId = "126"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxzpggg"]:
        if item in origin:
            classify_show = "土地使用权"
            channelId = "132"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxswzcgpplxx", "jyxxswzcjyjg", "jyxxgqgpplxx", "jyxxswzcgpplx"]:
        if item in origin:
            classify_show = "国有产权"
            channelId = "136"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxtpfjyjg"]:
        if item in origin:
            classify_show = "碳排放权"
            channelId = "189"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxrjxxzbgg", "jyxxrjxxzbhx", "jyxxrjxxjyjg"]:
        if item in origin:
            classify_show = "软件和信息服务"
            channelId = "192"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["gkbxgg", "gkbxzxjg"]:
        if item in origin:
            classify_show = "课题单位公开比选"
            channelId = "312"
            return {"classify_show": classify_show, "channelId": channelId}
    for item in ["jyxxqtjygg", "jyxxqtjyxx"]:
        if item in origin:
            classify_show = "其他"
            channelId = "197"
            return {"classify_show": classify_show, "channelId": channelId}


class MySpider(CrawlSpider):
    name = 'province_02_beijing_spider'
    area_id = "02"
    area_province = "北京市公共资源交易服务平台"
    num_str = 0
    list_1 = ["请求前"]
    list_2 = ["请求后"]
    domain_url = "https://ggzyfw.beijing.gov.cn"
    info_url = "https://ggzyfw.beijing.gov.cn/cmsbj/queryContent.jspx?"
    page_url = "https://ggzyfw.beijing.gov.cn/cmsbj/queryContent_{}.jspx?"
    allowed_domains = ['ggzyfw.beijing.gov.cn']
    # start_urls = [
    #             # 招标公告
    #             "https://ggzyfw.beijing.gov.cn/jyxxggjtbyqs/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxcggg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxzpggg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxswzcgpplxx/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxgqgpplxx/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbgg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbgg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/gkbxgg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxqtjygg/index.html",
    #             # 招标预告
    #             "https://ggzyfw.beijing.gov.cn/jyxxgcjszbjh/index.html",
    #             # 招标变更
    #             "https://ggzyfw.beijing.gov.cn/jyxxgzsx/index.html",
    #             # 中标预告
    #             "https://ggzyfw.beijing.gov.cn/jyxxzbhxrgs/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbhx/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbhx/index.html",
    #             # 中标公告
    #             "https://ggzyfw.beijing.gov.cn/jyxxzbgg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxzbjggg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxjyjg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxrjxxjyjg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/gkbxzxjg/index.html",
    #             "https://ggzyfw.beijing.gov.cn/jyxxqtjyxx/index.html",
    #             # 其他公告
    #             "https://ggzyfw.beijing.gov.cn/jyxxgcjshtgs/index.html"
    # ]

    info_zbgg_list = ["jyxxggjtbyqs", "jyxxcggg", "jyxxzpggg", "jyxxswzcgpplx",
                      "jyxxgqgpplxx", "jyxxrjxxzbgg", "gkbxgg", "jyxxqtjygg"]
    info_zbyg_list = ["jyxxgcjszbjh"]
    info_zbbg_list = ["jyxxgzsx"]
    win_bidyg_list = ["jyxxzbhxrgs", "jyxxrjxxzbhx", "jyxxrjxxzbhx"]
    win_bidgg_list = ["jyxxzbgg", "jyxxzbjggg", "jyxxrjxxjyjg", "jyxxrjxxjyjg", "gkbxzxjg",
                      "jyxxqtjyxx", "jyxxgcjshtgs"]

    all_list = info_zbgg_list + info_zbyg_list + info_zbbg_list + win_bidyg_list + win_bidgg_list

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if inDates := kwargs.get("day"):

            self.time_dict = {"inDates": inDates}
        else:
            self.time_dict = {"inDates": inDates}

    def start_requests(self):
        for item in self.all_list:
            channelId = process_request_category(item).get("channelId")
            info_dict = {"c1": "", "c2": "", "c3": item, "c4": "", "e": "", "ext8": "", "channelId": channelId,
                         "q": ""} | self.time_dict
            yield scrapy.Request(url=f"{self.info_url}{urllib.parse.urlencode(info_dict)}", priority=2,
                                 callback=self.parse_urls, meta={"info_dict": info_dict})

    def parse_urls(self, response):
        info_dict = response.meta["info_dict"]
        pages_str = response.xpath("//ul[@class='pages-list']/li/a/text()").get()
        ttlrow = re.findall(r"\d+", re.search(r"共\d+条", pages_str).group(0))[0]
        pages = re.findall(r"\d+", re.search(r"/\d+页", pages_str).group(0))[0]
        if ttlrow == "0":
            self.logger.info(f"本次获取总条数为：{ttlrow}")
            return
        else:
            self.logger.info(f"本次获取总条数为：{ttlrow}")
            pages = int(pages) + 1
            for num in range(1, pages):
                # if num == 1:
                #     yield scrapy.Request(url=f"{self.info_url}{urllib.parse.urlencode(info_dict)}", priority=4,
                #                          callback=self.parse_data_urls, meta={"info_dict": info_dict})
                # else:
                pages_url = self.page_url.format(num)
                yield scrapy.Request(url=f"{pages_url}{urllib.parse.urlencode(info_dict)}", priority=4,
                                     callback=self.parse_data_urls, meta={"info_dict": info_dict})

    def parse_data_urls(self, response):
        # print(response.url)
        li_list = response.xpath("//div[@class='content-list']/ul/li")
        for li in li_list:
            info_url = li.xpath("./a/@href").get()
            title_name = li.xpath("./a/@title").get()
            pub_time = li.xpath("./div[@class='list-times1']/p/text()").get()
            info_url = self.domain_url + info_url
            self.list_1.append(info_url)
            yield scrapy.Request(url=info_url, priority=10,
                                 callback=self.parse_items, meta={"title_name": title_name, "pub_time": pub_time,
                                                                      "info_dict": response.meta["info_dict"]})

    def parse_items(self, response):
        if response.status == 200:
            origin = response.url
            self.list_2.append(origin)
            title_name = response.meta["title_name"]
            print(title_name)
            title_2 = response.xpath("//div[@class='div-title2']/text()").get()
            pub_time = response.meta["pub_time"]
            info_source = "".join(re.findall(r"信息来源：(.+) ", title_2))
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            content = response.xpath("//*[@class='ggxx-info']").getall() \
                      or response.xpath('//*[@class="div-article2"]').getall()
            content_text = content[0].replace("\r", "").replace("\t", "").replace("\n", "")
            classify_show = process_request_category(origin).get("classify_show")
            if response.meta["info_dict"].get("c3") in self.info_zbgg_list:
                notice_type = const.TYPE_ZB_NOTICE
            elif response.meta["info_dict"].get("c3") in self.info_zbyg_list:
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif response.meta["info_dict"].get("c3") in self.info_zbbg_list:
                notice_type = const.TYPE_ZB_ALTERATION
            elif response.meta["info_dict"].get("c3") in self.win_bidyg_list:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif response.meta["info_dict"].get("c3") in self.win_bidgg_list:
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type =const.TYPE_UNKNOWN_NOTICE

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = ""
            notice_item["content"] = content_text
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = notice_type
            notice_item["category"] = classify_show
            yield notice_item
        else:
            print(response.url)


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_02_beijing_spider -a day=1".split(" "))
