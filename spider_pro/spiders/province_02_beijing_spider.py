#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2020-12-17
# @Describe: 北京市公共资源交易服务平台
import re
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
            return classify_show
    for item in ["jyxxcggg", "jyxxgzsx", "jyxxzbjggg"]:
        if item in origin:
            classify_show = "政府采购"
            return classify_show
    for item in ["jyxxzpggg"]:
        if item in origin:
            classify_show = "土地使用权"
            return classify_show
    for item in ["jyxxswzcgpplxx", "jyxxswzcjyjg", "jyxxgqgpplxx"]:
        if item in origin:
            classify_show = "国有产权"
            return classify_show
    for item in ["jyxxtpfjyjg"]:
        if item in origin:
            classify_show = "碳排放权"
            return classify_show
    for item in ["jyxxrjxxzbgg", "jyxxrjxxzbhx", "jyxxrjxxjyjg"]:
        if item in origin:
            classify_show = "软件和信息服务"
            return classify_show
    for item in ["gkbxgg", "gkbxzxjg"]:
        if item in origin:
            classify_show = "课题单位公开比选"
            return classify_show
    for item in ["jyxxqtjygg", "jyxxqtjyxx"]:
        if item in origin:
            classify_show = "其他"
            return classify_show


class MySpider(CrawlSpider):
    name = 'province_02_beijing_spider'
    area_id = "02"
    area_province = "北京市公共资源交易服务平台"
    allowed_domains = ['ggzyfw.beijing.gov.cn']
    start_urls = [
                # 招标公告
                "https://ggzyfw.beijing.gov.cn/jyxxggjtbyqs/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxcggg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxzpggg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxswzcgpplxx/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxgqgpplxx/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbgg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbgg/index.html",
                "https://ggzyfw.beijing.gov.cn/gkbxgg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxqtjygg/index.html",
                # 招标预告
                "https://ggzyfw.beijing.gov.cn/jyxxgcjszbjh/index.html",
                # 招标变更
                "https://ggzyfw.beijing.gov.cn/jyxxgzsx/index.html",
                # 中标预告
                "https://ggzyfw.beijing.gov.cn/jyxxzbhxrgs/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbhx/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxzbhx/index.html",
                # 中标公告
                "https://ggzyfw.beijing.gov.cn/jyxxzbgg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxzbjggg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxjyjg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxrjxxjyjg/index.html",
                "https://ggzyfw.beijing.gov.cn/gkbxzxjg/index.html",
                "https://ggzyfw.beijing.gov.cn/jyxxqtjyxx/index.html",
                # 其他公告
                "https://ggzyfw.beijing.gov.cn/jyxxgcjshtgs/index.html"
    ]

    info_zbgg_dict = ["jyxxggjtbyqs", "jyxxcggg", "jyxxzpggg", "jyxxswzcgpplx",
                      "jyxxgqgpplxx", "jyxxrjxxzbgg", "gkbxgg", "jyxxqtjygg"]
    info_zbyg_dict = ["jyxxgcjszbjh"]
    info_zbbg_dict = ["jyxxgzsx"]
    win_bidyg_dict = ["jyxxzbhxrgs", "jyxxrjxxzbhx", "jyxxrjxxzbhx"]
    win_bidgg_dict = ["jyxxzbgg", "jyxxzbjggg", "jyxxrjxxjyjg", "jyxxrjxxjyjg", "gkbxzxjg",
                      "jyxxqtjyxx", "jyxxgcjshtgs"]

    rules = (
        Rule(LinkExtractor(allow=[r'/jyxx\w+\/index.html', r'/gkbxgg/index.html'], tags='li', attrs='data-href'),
             follow=True),
        Rule(LinkExtractor(allow=r'/index_\d+\.html', tags='a', attrs="onclick", process_value=process_value_s),
             follow=True),
        # 招标公告
        Rule(LinkExtractor(
            allow=[r'/jyxxggjtbyqs/\d+\/\d+\.html', r'/jyxxcggg/\d+\/\d+\.html', r'/jyxxzpggg/\d+\/\d+\.html',
                   r'/jyxxswzcgpplx/\d+\/\d+\.html', r'/jyxxgqgpplxx/\d+\/\d+\.html', r'/jyxxrjxxzbgg/\d+\/\d+\.html',
                   r'/gkbxgg/\d+\/\d+\.html', r'/jyxxqtjygg/\d+\/\d+\.html'],
            attrs='href'), cb_kwargs={"name": const.TYPE_ZB_NOTICE},
            callback="parse_items", follow=False),
        # 招标预告
        Rule(LinkExtractor(allow=[r'/jyxxgcjszbjh/\d+\/\d+\.html'], attrs='href'), cb_kwargs={"name": const.TYPE_ZB_ADVANCE_NOTICE},
             callback="parse_items", follow=False),
        # 招标变更
        Rule(LinkExtractor(allow=[r'/jyxxgzsx/\d+\/\d+\.html'], attrs='href'), cb_kwargs={"name": const.TYPE_ZB_ALTERATION},
             callback="parse_items", follow=False),
        # 中标预告
        Rule(LinkExtractor(
            allow=[r'/jyxxzbhxrgs/\d+\/\d+\.html', r'/jyxxrjxxzbhx/\d+\/\d+\.html', r'/jyxxrjxxzbhx/\d+\/\d+\.html'],
            attrs='href'), cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_items", follow=False),
        # 中标公告
        Rule(LinkExtractor(
            allow=[r'/jyxxzbgg/\d+\/\d+\.html', r'/jyxxzbjggg/\d+\/\d+\.html', r'/jyxxrjxxjyjg/\d+\/\d+\.html',
                   r'/jyxxrjxxjyjg/\d+\/\d+\.html', r'/gkbxzxjg/\d+\/\d+\.html', r'/jyxxqtjyxx/\d+\/\d+\.html'],
            attrs='href'), cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_items", follow=False),
        #其他公告
        Rule(LinkExtractor(allow=[r'/jyxxgcjshtgs/\d+\/\d+\.html'], attrs='href'), cb_kwargs={"name": const.TYPE_OTHERS_NOTICE},
             callback="parse_items", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

    def parse_items(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("//div[@class='div-title']/text()").get()
            title_name = title_name.replace("\r", "").replace("\t", "").replace("\n", "")
            title_2 = response.xpath("//div[@class='div-title2']/text()").get()
            pub_time = re.search("\d{4}-\d{1,2}-\d{1,2}", title_2).group(0)
            info_source = "".join(re.findall(r"信息来源：(.+) ", title_2))
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            content = response.xpath("//*[@class='ggxx-info']").getall() \
                      or response.xpath('//*[@class="div-article2"]').getall()
            content_text = content[0].replace("\r", "").replace("\t", "").replace("\n", "")
            classify_show = process_request_category(origin)
            print(title_name)
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = ""
            notice_item["content"] = content_text
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = name
            notice_item["category"] = classify_show
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_02_beijing_spider".split(" "))
