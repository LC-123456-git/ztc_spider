#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-26
# @Describe: 河南公共资源交易网
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
    name = "province_23_henan_spider"
    area_id = "23"
    allowed_domains = ['hnsggzyfwpt.hndrc.gov.cn']
    domain_url = "http://hnsggzyfwpt.hndrc.gov.cn"
    count_url = "http://hnsggzyfwpt.hndrc.gov.cn/services/hl/getCount?"
    info_url = "http://hnsggzyfwpt.hndrc.gov.cn/services/hl/getSelect?"
    data_url = "http://hnsggzyfwpt.hndrc.gov.cn"
    page_size = "22"
    page_headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Connection": "keep-alive",
                    "Cookie": "JSESSIONID=AB080CCD14FD555300B5FAA0BBD0EDF0;"
                              " _CSRFCOOKIE=21F5D94FAF1B91E5E983659F1352461A13625542",
                    "Host": "hnsggzyfwpt.hndrc.gov.cn",
                    "Referer": "http://hnsggzyfwpt.hndrc.gov.cn/002/tradePublic.html",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/75.0.3770.100 Safari/537.36",
                    "X-Requested-With": "XMLHttpRequest"}
    data_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "JSESSIONID=AB080CCD14FD555300B5FAA0BBD0EDF0; _CSRFCOOKIE=21F5D94FAF1B91E5E983659F1352461A13625542",
        "Host": "hnsggzyfwpt.hndrc.gov.cn",
        "If-Modified-Since": "Thu, 11 Jul 2019 08:26:22 GMT",
        "If-None-Match": 'W/"5d26f2ae-2b4b"',
        "Referer": "http://hnsggzyfwpt.hndrc.gov.cn/002/tradePublic.html",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/75.0.3770.100 Safari/537.36"}

    # 招标公告
    list_notice_category_num = ["002001001", "002002001", "002003001", "002004001", "002006001"]
    # 招标变更
    list_alteration_category_num = ["002001002", "002002002", "002003002", "002004002"]
    # 中标预告
    list_win_advance_category_num = ["002001003"]
    # 中标公告
    list_win_notice_category_num = ["002001004", "002002003", "002003003", "002004003", "002006002"]
    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_advance_category_num + list_win_notice_category_num

    area_province = "河南省公共资源交易服务平台"
    project_category_dict = {
        "002001": "工程建设",
        "002002": "政府采购",
        "002003": "土地矿产",
        "002004": "产权交易",
        "002006": "其他交易"}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        r_dict = {"response": "application/json", "day": "", "sheng": "x1", "qu": "", "xian": "", "title": "",
                  "siteguid": "9f5b36de-4e8f-4fd6-b3a1-a8e08b38ea38"}
        if day := kwargs.get("day"):
            time_dict = {"timestart": "" if day == "0" else get_back_date(int(day) - 1),
                         "timeend": "" if day == "0" else get_back_date(0)}
        elif kwargs.get("sdt") and kwargs.get("edt"):
            time_dict = {"timestart": kwargs.get("sdt"), "timeend": kwargs.get("edt"), }
        else:
            time_dict = {"timestart": "", "timeend": "", }  # TODO 默认为全量
        self.info_dict = {"pageSize": self.page_size} | r_dict | time_dict
        self.count_dict = r_dict | time_dict

    def start_requests(self):
        for item in self.list_all_category_num:
            yield scrapy.Request(
                url=f"{self.count_url}{urllib.parse.urlencode(self.count_dict | {'categorynum': item})}",
                callback=self.parse_page_urls, meta={"categorynum": item}, headers=self.page_headers)

    def parse_page_urls(self, response):
        try:
            total = json.loads(response.text).get("return")
            self.logger.info(
                f"初始总数提取成功 {response.meta['categorynum']} {total=} {response.url=} {response.meta.get('proxy')}")
            pages = math.ceil(int(total) / int(self.page_size)) + 1
            for i in range(1, pages):
                temp_dict = self.info_dict | {'categorynum': response.meta['categorynum'], "pageIndex": str(i)}
                yield scrapy.Request(
                    url=f"{self.info_url}{urllib.parse.urlencode(temp_dict)}",
                    callback=self.parse_data_urls, meta={"categorynum": response.meta['categorynum']},
                    headers=self.page_headers)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if json.loads(response.text).get('return') == "":
                self.logger.info(f"发起数据请求，未获取到详情页url {response.url=}")
            else:
                category_num = response.meta['categorynum']
                name_project_category = self.project_category_dict.get(category_num[0:6], "")
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
                    city = item.get("infoc", "")
                    title_name = item.get("title", "")
                    pub_time = item.get("infodate", "")
                    temp_url = "".join([self.data_url, item.get("href")])
                    yield scrapy.Request(url=temp_url, callback=self.parse_item, headers=self.data_headers,
                                         meta={"cb_kwargs": cb_kwargs, "city": city,
                                               "title_name": title_name, "pub_time": pub_time,
                                               "name_project_category": name_project_category},
                                         cb_kwargs=cb_kwargs)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e}{response.url=}")

    def parse_item(self, response, name):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            title_name = response.meta["title_name"]
            print(title_name)
            info_source = response.meta["city"]
            if not info_source:
                info_source = self.area_province
            info_source = f"{self.area_province}-{info_source}"
            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)
            if not pub_time:
                pub_time = ""
            content = response.xpath('/html/body/div[2]/div[2]/div[1]/div[2]').get()
            # if not content:
            #     content = response.xpath('//*[@id="mainContent"]').get()

            files_path = []
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
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = response.meta.get("name_project_category")

            if not title_name:
                title_name = ""
            if re.search(r"更正", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ALTERATION
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = name

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_23_henan_spider -a sdt=2021-05-01 -a edt=2021-05-14".split(" "))
    # cmdline.execute("scrapy crawl province_23_henan_spider ".split(" "))
    # cmdline.execute("scrapy crawl province_23_henan_spider -s DOWNLOAD_DELAY=0".split(" "))
    # cmdline.execute("scrapy crawl province_23_henan_spider -a day=0".split(" "))
