#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-17
# @Describe: 宁夏回族自治区公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(Spider):
    name = "province_49_ningxia_spider"
    area_id = "49"
    area_province = "宁夏"
    allowed_domains = ['nxggzyjy.org']
    domain_url = "http://www.nxggzyjy.org"
    count_url = "http://www.nxggzyjy.org/ningxiawebservice/services/BulletinWebServer/getInfoCountNew?"
    info_url = "http://www.nxggzyjy.org/ningxiawebservice/services/BulletinWebServer/getInfoListInAboutNew?"
    data_url = "http://www.nxggzyjy.org/ningxiaweb"
    page_size = "18"
    list_notice_category_num = ["002001001", "002002001", "002003001", "002004001", "002005001"]
    list_alteration_category_num = ["002001002", "002002002"]
    list_win_advance_category_num = ["002001004"]
    list_win_notice_category_num = ["002001003", "002002003", "002003002", "002004003", "002005003"]
    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_advance_category_num + list_win_notice_category_num
    project_category_dict = {
        "002001": "工程建设",
        "002002": "政府采购",
        "002003": "药品采购",
        "002004": "产权交易",
        "002005": "土地及矿业权"}
    # list_all_category_num = ["002001001"]
    # start_urls = [
    #     # 招标公告 5
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002001/002001001/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002002/002002001/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002003/002003001/listPage.html",  # 附件类型的
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002004/002004001/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002005/002005001/listPage.html",
    #     # 招标变更(招标异常) 2
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002001/002001002/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002002/002002002/listPage.html",
    #     # 中标预告 1
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002001/002001004/listPage.html",
    #     # 中标公告 5
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002001/002001003/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002002/002002003/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002003/002003002/listPage.html",  # 附件类型的
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002004/002004003/listPage.html",
    #     "http://www.nxggzyjy.org/ningxiaweb/002/002005/002005003/listPage.html",
    # ]

    # rules = (
    #     # 招标公告
    #     Rule(LinkExtractor(allow=[
    #         r'/ningxiaweb/002/00200([1-2]|5){1}/00200([1-2]|5){1}001/.*/.*\-.*\-.*\-.*\-.*\.html',
    #         r'/ningxiaweb/002/002004/002004001/.*/[0-9a-z]{32}\.html',
    #         r'/ningxiaweb/002/002003/002003001/.*/.*\-.*\-.*\-.*\-.*\.html'  # 附件类型的
    #     ], unique=True),
    #         cb_kwargs={"name": const.TYPE_ZB_NOTICE}, callback="parse_item", follow=False),
    #     Rule(LinkExtractor(allow=[
    #         r'/ningxiaweb/002/00200([1-2]|[4-5]){1}/00200([1-2]|[4-5]){1}001/\d+\.html'
    #         r'/ningxiaweb/002/002003/002003001/\d+\.html'  # 附件类型的
    #     ], unique=True)),
    #     # 招标变更
    #     Rule(LinkExtractor(allow=r'/ningxiaweb/002/00200[1-2]{1}/00200[1-2]{1}002/.*/.*\-.*\-.*\-.*\-.*\.html',
    #                        unique=True),
    #          cb_kwargs={"name": const.TYPE_ZB_ALTERATION}, callback="parse_item", follow=False),
    #     Rule(LinkExtractor(allow=r'/ningxiaweb/002/00200[1-2]{1}/00200[1-2]{1}002/\d+\.html', unique=True)),
    #     # 中标预告
    #     Rule(LinkExtractor(allow=r'/ningxiaweb/002/002001/002001004/.*/.*\-.*\-.*\-.*\-.*\.html', unique=True),
    #          cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_item", follow=False),
    #     Rule(LinkExtractor(allow=r'/ningxiaweb/002/002001/002001004/\d+\.html', unique=True)),
    #     # # 中标公告
    #     Rule(LinkExtractor(allow=[
    #         r'/ningxiaweb/002/00200([1-2]|[4-5]){1}/00200([1-2]|[4-5]){1}003/.*/.*\-.*\-.*\-.*\-.*\.html',
    #         r'/ningxiaweb/002/002003/002003002/.*/.*\-.*\-.*\-.*\-.*\.html'  # 附件类型的
    #     ], unique=True),
    #         cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_item", follow=False),
    #     Rule(LinkExtractor(allow=[
    #         r'/ningxiaweb/002/00200([1-2]|[4-5]){1}/00200([1-2]|[4-5]){1}003/\d+\.html',
    #         r'/ningxiaweb/002/002003/002001002/\d+\.html'  # 附件类型的
    #     ], unique=True)),
    # )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        r_dict = {"response": "application/json", "siteguid": "2e221293-d4a1-40ed-854b-dcfea12e61c5",
                  "cityname": "", "title": "", "hy": "", }
        if day := kwargs.get("day"):
            time_dict = {"sdt": "" if day == "0" else get_back_date(int(day) - 1),
                         "edt": "" if day == "0" else get_back_date(0)}
        elif kwargs.get("sdt") and kwargs.get("edt"):
            time_dict = {"sdt": kwargs.get("sdt"), "edt": kwargs.get("edt"), }
        else:
            # time_dict = {"sdt": get_back_date(0), "edt": get_back_date(0), }
            time_dict = {"sdt": "", "edt": "", }  # TODO 默认为全量
        self.info_dict = {"pageSize": self.page_size} | r_dict | time_dict
        self.count_dict = r_dict | time_dict

    def start_requests(self):
        for item in self.list_all_category_num:
            yield scrapy.Request(
                url=f"{self.count_url}{urllib.parse.urlencode(self.count_dict | {'categorynum': item})}", priority=6,
                callback=self.parse_page_urls, meta={"categorynum": item})

    def parse_page_urls(self, response):
        try:
            total = json.loads(response.text).get("return")
            self.logger.info(
                f"初始总数提取成功 {response.meta['categorynum']} {total=} {response.url=} {response.meta.get('proxy')}")
            pages = math.ceil(int(total) / int(self.page_size)) + 1
            for i in range(1, pages):
                temp_dict = self.info_dict | {'categorynum': response.meta['categorynum'], "pageIndex": str(i)}
                yield scrapy.Request(
                    url=f"{self.info_url}{urllib.parse.urlencode(temp_dict)}", priority=8,
                    callback=self.parse_data_urls, meta={
                        "categorynum": response.meta['categorynum']
                    })
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            category_num = response.meta['categorynum']
            if category_num in self.list_notice_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
            elif category_num in self.list_alteration_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
            elif category_num in self.list_win_advance_category_num:
                cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
            else:
                cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
            r_list = json.loads(json.loads(response.text).get('return')).get('Table')
            for item in r_list:
                pub_time = item.get("infodate")
                temp_url = "/".join([self.data_url, category_num[0:3], category_num[0:6], category_num,
                                     item.get("infodate").replace("-", ""), item.get("infoid") + ".html"])
                yield scrapy.Request(url=temp_url, callback=self.parse_item, priority=10, meta={
                    "cb_kwargs": cb_kwargs, "pub_time": pub_time, "category": item.get("categorynum"),
                    "title_name": item.get("title")}, cb_kwargs=cb_kwargs)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            title = response.meta["title_name"]
            if info_source := re.search(r"\[(自治区|银川市|石嘴山市|吴忠市|固原市|中卫市)\]", title):
                info_source = info_source.group().split("[")[1].split("]")[0]
                if info_source == "自治区":
                    info_source = self.area_province
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            print(info_source)
            title_name = re.sub(r"\[(自治区|银川市|石嘴山市|吴忠市|固原市|中卫市)\]", "", title)
            print(title_name)

            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)
            # if not pub_time:
            #     pub_time = get_accurate_pub_time(response.xpath("/html/body/div[2]/div[1]/div[2]/div[2]/text()[1]/text()[1]").get())
            # if not pub_time:
            #     pub_time = get_accurate_pub_time(response.xpath("/html/body/div[2]/div[1]/div[2]/div[2]/text()[1]").get())
            # if not pub_time:
            #     pub_time = get_accurate_pub_time(response.xpath("/html/body/div[2]/div[1]/div[2]/div[1]/text()[1]").get())
            # if not pub_time:
            #     pub_time = ""

            content = response.xpath('//div[@id="tablecontent1"]').get()
            if not content:
                content = response.xpath('//div[@id="mainContent"]').get()
                if not content:
                    content = response.xpath('//div[@id="tablecontent3"]').get()
                    if not content:
                        content = response.xpath("//div[@id='tab-1']").get()
            name_project_category = self.project_category_dict.get(response.meta["category"][0:6])
            files_path = {}
            if img_list := response.xpath("//div[@id='mainContent']//img"):
                for item in img_list:
                    value = item.xpath('./@href').get()
                    key = item.xpath('./text()').get()
                    files_path[key] = value
            if a_list := response.xpath("//div[@id='mainContent']//a"):
                for item in a_list:
                    value = item.xpath('./@href').get()
                    key = item.xpath('./text()').get()
                    files_path[key] = value

            # full_content = response.xpath("/html/body/div[2]/div[1]/div[2]").get()
            # if full_content:
            #     if files := re.findall(r"/ningxiaweb/uploadfile/.*?\"", full_content):
            #         pub_time_simple = pub_time.split(" ")[0]
            #         for item in files:
            #             item = item.replace("\"", "")
            #             file_item = FileItem()
            #             unquote_name = parse.unquote(item).split("/")[-1]
            #             file_item["file_url"] = parse.urljoin(self.domain_url, item)
            #             file_item["file_name"] = unquote_name.split('.')[0]
            #             file_item["file_type"] = unquote_name.split('.')[1]
            #             file_item["file_path"] = fr"{self.name}/{pub_time_simple}/{item.split('/')[-2]}/{unquote_name}"
            #             files_path.append(file_item["file_path"])
            #             yield file_item

            # item
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = name_project_category
            notice_item["web_name"] = self.area_province
            if not title_name:
                title_name = ""

            if name == const.TYPE_ZB_ALTERATION and re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = name

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_49_ningxia_spider -a std=2020-01-04 -a edt=2020-01-04".split(" "))
    cmdline.execute("scrapy crawl province_49_ningxia_spider -s DOWNLOAD_DELAY=0".split(" "))
