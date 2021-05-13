#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-07
# @Describe: 全国公共资源交易平台 - 全量/增量脚本
import re
import math
import json
import scrapy
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = 'province_00_quanguo_spider'
    area_id = "00"
    domain_url = "http://www.ggzy.gov.cn"
    query_url = "http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp"
    allowed_domains = ['ggzy.gov.cn']
    area_province = "全国公共资源交易平台"
    page_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "deal.ggzy.gov.cn",
        "Origin": "http://deal.ggzy.gov.cn",
        "Referer": "http://deal.ggzy.gov.cn/ds/deal/dealList.jsp?HEADER_DEAL_TYPE=01",
        "X-Requested-With": "XMLHttpRequest",
        # "Cookie": "JSESSIONID=9b810b92cf8e99c1f6866d165ad9; insert_cookie=67313298",
    }
    data_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Connection": "keep-alive",
        "Host": "deal.ggzy.gov.cn",
        # "If-Modified-Since": "Sun, 17 Jan 2021 23:00:06 GMT",
        "Upgrade-Insecure-Requests": "1",
        # "Cookie": "JSESSIONID=9b810b92cf8e99c1f6866d165ad9; insert_cookie=67313298",
    }

    # 招标公告
    list_notice_category_num = ["招标/资审公告", "采购/资审公告", "出让公示", "出让公告", "挂牌披露", "信息披露", "出售公告",
                                "交易公告"]
    # 招标变更
    list_alteration_category_num = ["招标/资审文件澄清", "更正事项", "变更公告"]
    # 中标公告
    list_win_notice_category_num = ["交易结果公示", "中标公告", "成交宗地", "出让结果", "交易结果", "成交公告", "成交公示", "结果公示"]
    # 其他公告
    list_others_notice_num = ["开标记录", "采购合同", "公开信息", "登记公告信息", "交易目录"]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.page_dict = {"PAGENUMBER": "1"}
        self.time_dict = {}
        # self.r_dict = {"SOURCE_TYPE": "1", "DEAL_PROVINCE": "500000", "DEAL_CITY": "0", "DEAL_PLATFORM": "0",
        #                "DEAL_STAGE": "9000", "DEAL_CLASSIFY": "00", "BID_PLATFORM": "0", "DEAL_TRADE": "0",
        #                "isShowAll": "1", "FINDTXT": ""}
        self.r_dict = {"SOURCE_TYPE": "1", "DEAL_PROVINCE": "0", "DEAL_CITY": "0", "DEAL_PLATFORM": "0",
                       "DEAL_STAGE": "0000", "DEAL_CLASSIFY": "00", "BID_PLATFORM": "0", "DEAL_TRADE": "0",
                       "isShowAll": "1", "FINDTXT": ""}

        self.time_dict = {"TIMEBEGIN_SHOW": kwargs.get("sdt", ""), "TIMEEND_SHOW": kwargs.get("edt", ""),
                          "TIMEBEGIN": kwargs.get("sdt", ""), "TIMEEND": kwargs.get("edt", ""), "DEAL_TIME": "06"}

    def start_requests(self):
        self.type_dict = self.page_dict | self.r_dict | self.time_dict
        # self.type_dict = {k: v if v else '' for k, v in self.type_dict.items()}
        yield scrapy.FormRequest(
            self.query_url, formdata=self.type_dict, callback=self.parse_urls, priority=6, headers=self.page_headers)

    def parse_urls(self, response):
        try:
            success = json.loads(response.text).get("success")
            if success:
                ttlrow = json.loads(response.text).get("ttlrow")
                self.logger.info(f"本次获取总条数为：{ttlrow}")
                pages = json.loads(response.text).get("ttlpage", "")
                pages = int(pages) + 1
                for i in range(1, pages):
                    yield scrapy.FormRequest(
                        self.query_url, formdata=self.r_dict | self.time_dict | {"PAGENUMBER": str(i)}, priority=8,
                        callback=self.parse_data_urls, headers=self.page_headers)
            else:
                error = json.loads(response.text).get("error")
                self.logger.error(f"初始总页数提取错误 {response.meta=} {error} {response.url=}")
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            r_url = json.loads(response.text).get('data', [])
            for item in r_url:
                classify_show = item.get("classifyShow", "")
                category_num = item.get("stageShow", "")
                if item.get("districtShow") and item.get("platformName"):
                    info_source = f'{item.get("districtShow")}-{item.get("platformName")}'
                elif item.get("districtShow") or item.get("platformName"):
                    info_source = item.get("districtShow") or item.get("platformName")
                else:
                    info_source = ""
                data_url = item.get("url", "")
                if category_num in self.list_notice_category_num:
                    cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif category_num in self.list_alteration_category_num:
                    cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
                elif category_num in self.list_others_notice_num:
                    cb_kwargs = {"name": const.TYPE_OTHERS_NOTICE}
                else:
                    cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
                data_headers = self.data_headers | {"Referer": data_url}
                data_url = data_url.replace("/a/", "/b/")
                yield scrapy.Request(url=data_url, callback=self.parse_item, priority=10, cb_kwargs=cb_kwargs,
                                     meta={"cb_kwargs": cb_kwargs, "info_source": info_source,
                                           "classify_show": classify_show}, headers=data_headers)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            origin = origin.replace("/b/", "/a/")
            info_source = response.meta.get("info_source", "")
            classify_show = response.meta.get("classify_show", "")
            title_name = response.xpath("/html/body/div/h4/text()").get() or ""

            print(title_name)
            if re.search(r"终止|中止|流标|废标|异常", title_name):
                name = const.TYPE_ZB_ABNORMAL
            if re.search(r"变更|更正|澄清", title_name):
                name = const.TYPE_ZB_ALTERATION
            if re.search(r"候选人", title_name):
                name = const.TYPE_WIN_ADVANCE_NOTICE
            pub_time = response.xpath("/html/body/div/p/span[1]/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            if not pub_time:
                pub_time = "null"
            if re.search("重庆", info_source) and classify_show == "其他":
                content = response.xpath("//*[@id='mycontent']").get()

                style_content = response.xpath("//div[@class='detail_content']/text()").get()
                son_content = response.xpath("//div[@class='detail_content']/descendant::p").get()
                if not son_content:
                    return
                if style_content:
                    content = re.sub(style_content, "", content)

            else:
                content = response.xpath("//*[@id='mycontent']").get()
            files_path = []
            # if content:
            #     pub_time_simple = pub_time.split(" ")[0]
            #     if files := re.findall(r"http://www.sxyxcg.com/UploadFile/.*?\"", content):
            #         for item in files:
            #             item = item.replace("\"", "")
            #             file_item = FileItem()
            #             unquote_name = parse.unquote(item).split("/")[-1]
            #             file_item["file_url"] = parse.urljoin(self.domain_url, item)
            #             file_item["file_name"] = unquote_name.split('.')[0]
            #             file_item["file_type"] = unquote_name.split('.')[1]
            #             file_item["file_path"] = fr"{self.name}/{pub_time_simple}/{unquote_name}"
            #             files_path.append(file_item["file_path"])
            #             yield file_item

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name.strip()
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["notice_type"] = name
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classify_show
            # notice_item["notice_type"] = notice_type
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_00_quanguo_spider -a day=3".split(" "))
    # cmdline.execute("scrapy crawl province_00_quanguo_spider -a sdt=2021-01-01 -a edt=2021-01-26 -s DOWNLOAD_DELAY=0 -s CONCURRENT_REQUESTS_PER_IP=20".split(" "))
    cmdline.execute("scrapy crawl province_00_quanguo_spider -a sdt=2021-02-13 -a edt=2021-03-13 -s DOWNLOAD_DELAY=0 -s CONCURRENT_REQUESTS_PER_IP=20".split(" "))
