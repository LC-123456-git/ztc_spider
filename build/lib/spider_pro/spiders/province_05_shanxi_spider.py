#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-05
# @Describe: 山西省公共资源交易网 - 全量/增量脚本
import re
import math
import scrapy
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time


def process_request_category(origin):
    if "jyxxgc" in origin:
        classify_show = "工程建设"
        return classify_show
    elif"jyxxzc" in origin:
        classify_show = "政府采购"
        return classify_show
    elif"jyxxtd" in origin:
        classify_show = "土地使用权"
        return classify_show
    elif"jyxxkc" in origin:
        classify_show = "矿业权"
        return classify_show
    elif"jyxxcq" in origin:
        classify_show = "国有产权"
        return classify_show
    elif"jyxxyx" in origin:
        classify_show = "药械采购"
        return classify_show
    elif"jyxxym" in origin:
        classify_show = "二类疫苗"
        return classify_show


class MySpider(CrawlSpider):
    name = 'province_05_shanxi_spider'
    area_id = "05"
    area_province = "山西"
    domain_url = "http://prec.sxzwfw.gov.cn"
    query_url = "http://prec.sxzwfw.gov.cn/queryContent-jyxx.jspx"
    query_page_url = "http://prec.sxzwfw.gov.cn/queryContent_{}-jyxx.jspx"
    allowed_domains = ['prec.sxzwfw.gov.cn']

    rules = (
        # 招标公告
        Rule(LinkExtractor(allow=[
            r'/jyxxgczb/\d+\.jhtml', r'/jyxxzcgg/\d+\.jhtml', r'/jyxxtdgg/\d+\.jhtml',
            r'/jyxxkcgg/\d+\.jhtml', r'/jyxxcqgg/\d+\.jhtml', r'/jyxxyxgg/\d+\.jhtml',
            r'/jyxxyxmx/\d+\.jhtml'
        ], unique=True), cb_kwargs={"name": const.TYPE_ZB_NOTICE}, callback="parse_item", follow=False),

        # 招标变更
        Rule(LinkExtractor(allow=[r'/jyxxgcgz/\d+\.jhtml', r'/jyxxzcgz/\d+\.jhtml']),
             cb_kwargs={"name": const.TYPE_ZB_ALTERATION},
             callback="parse_item", follow=False),
        # 中标预告
        Rule(LinkExtractor(allow=[r'/jyxxgchxr/\d+\.jhtml']), cb_kwargs={"name": const.TYPE_ZB_ADVANCE_NOTICE},
             callback="parse_item", follow=False),
        # 中标公告
        Rule(LinkExtractor(allow=[
            r'/jyxxgcgs/\d+\.jhtml', r'/jyxxzczb/\d+\.jhtml', r'/jyxxtdgs/\d+\.jhtml',
            r'/jyxxkcgs/\d+\.jhtml', r'/jyxxcqgs/\d+\.jhtml']),
            cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 招标异常
        Rule(LinkExtractor(allow=[r'/jyxxgcyc/\d+\.jhtml']), cb_kwargs={"name": const.TYPE_ZB_ABNORMAL},
             callback="parse_item", follow=False),
        # 其他公告
        Rule(LinkExtractor(allow=[r'/jyxxymqt/\d+\.jhtml']), cb_kwargs={"name": const.TYPE_OTHERS_NOTICE},
             callback="parse_item", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.time_dict = {}
        r_dict = {"title": "", "origin": ""}
        if inDates := kwargs.get("day"):  # 1为当天，3为近3天，以此类推;4000为全部时间，则为全量脚本
            self.time_dict = {
                                 "inDates": "4000" if inDates == "0" else inDates,
                                 "beginTime": "",
                                 "endTime": "",
                             } | r_dict
        elif kwargs.get("sdt") and kwargs.get("edt"):  # 比如 2021-01-02 至 2021-01-05
            self.time_dict = {
                                 "inDates": "",
                                 "beginTime": kwargs.get("sdt"),
                                 "endTime": kwargs.get("edt"),
                             } | r_dict
        else:
            self.time_dict = {
                                 "inDates": "4000",  # TODO 默认为全量
                                 "beginTime": "",
                                 "endTime": "",
                             } | r_dict

    def start_requests(self):
        for item in [
            "12", "18", "22", "63", "25", "37", "39",  # 招标公告
            "13", "19",  # 招标变更
            "14",  # 中标预告
            "15", "20", "23", "64", "26",  # 中标公告
            "16",  # 招标异常
            "44",  # 其他
        ]:
            yield scrapy.FormRequest(
                self.query_url, formdata=self.time_dict | {"channelId": item}, callback=self.parse_urls, meta={
                    "channelId": item
                })

    def parse_urls(self, response):
        try:
            if count_str := re.search(r"count: \d+", response.text):
                limit = 10
                count = int(re.search(r"\d+", count_str.group(0)).group(0))
                if limit_str := re.search(r"limit: \d+", response.text):
                    limit = int(re.search(r"\d+", limit_str.group(0)).group(0))
                self.logger.info(f"初始链接提取成功： id={response.meta['channelId']} {count=} {self.time_dict}")
                pages = math.ceil(count / limit) + 1
                for i in range(1, pages):
                    yield scrapy.FormRequest(self.query_page_url.format(i),
                                             formdata=self.time_dict | {"channelId": response.meta["channelId"]})
            else:
                self.logger.error(f"初始链接数量提取异常：{response.url=} {response.meta=}")
        except Exception as e:
            self.logger.error(f"初始链接提取错误：{response.url=} {response.meta=} {e}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("/html/body/div[2]/div/div/p[1]/text()").get()
            pub_time = response.xpath("/html/body/div[2]/div/div/p[2]/text()").get()
            info_source = self.area_province
            content = response.xpath("//*[@class='div-article2']").get()
            if not content:
                content = response.xpath("//*[@class='gycq-table']").get()
            if not content:
                content = response.xpath("//*[@class='cs_xq_content']").get()

            pub_time = get_accurate_pub_time(pub_time)

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
            classify_show = process_request_category(origin)
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["notice_type"] = name
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classify_show
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_05_shanxi_spider".split(""))
