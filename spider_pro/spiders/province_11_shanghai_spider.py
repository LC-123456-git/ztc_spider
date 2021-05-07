#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-04
# @Describe: 上海市公共资源交易中心

import re
import math
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider_pro.items import *
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time


def process_value_s(value):
    try:
        value = value.split("com:80")[1]
        value = value.split("')")[0]
        return value
    except:
        return value


def process_request_category(request, response):
    r_url = request.url
    for item in ["jyxxgczs", "jyxxgcgg", "jyxxgchx", "jyxxgcgs"]:
        if item in r_url:
            request.meta["classify_show"] = "工程建设"
            return request
    for item in ["jyxxzcxm", "jyxxzcgg", "jyxxzcgs", "jyxxzcht"]:
        if item in r_url:
            request.meta["classify_show"] = "政府采购"
            return request
    for item in ["jyxxtdgg", "jyxxtdgs"]:
        if item in r_url:
            request.meta["classify_show"] = "土地出让"
            return request
    for item in ["jyxxcqgg", "jyxxcqgs"]:
        if item in r_url:
            request.meta["classify_show"] = "国有产权"
            return request
    # TODO 机电设备
    for item in ["jyxxtpfgg", "jyxxtpfgs"]:
        if item in r_url:
            request.meta["classify_show"] = "碳排放权"
            return request
    for item in ["jyxxypgg"]:
        if item in r_url:
            request.meta["classify_show"] = "药品采购"
            return request
    # TODO 技术交易
    for item in ["jyxxncgg", "jyxxncgs"]:
        if item in r_url:
            request.meta["classify_show"] = "农村产权"
            return request
    for item in ["jyxxpmgg"]:  # TODO 司法拍卖-结果公告
        if item in r_url:
            request.meta["classify_show"] = "司法拍卖"
            return request
    for item in ["jyxxxnyba"]:  # TODO 新能源汽车补助-除备案外
        if item in r_url:
            request.meta["classify_show"] = "新能源汽车补助"
            return request
    for item in ["jyxxzfbz"]:  # TODO 住房保障-除共有产权保障住房外
        if item in r_url:
            request.meta["classify_show"] = "住房保障"
            return request
    # TODO 物资采购


class MySpider(CrawlSpider):
    name = "province_11_shanghai_spider"
    area_id = "11"
    area_province = "上海市公共资源交易服务平台"
    allowed_domains = ['shggzy.com']
    domain_url = "https://www.shggzy.com"
    query_url = "https://www.shggzy.com/queryContent-jyxx.jspx"
    query_page_url = "https://www.shggzy.com/queryContent_{}-jyxx.jspx"

    rules = (
        # 招标公告
        Rule(LinkExtractor(allow=[
            r'/jyxxgcgg/\d+\.jhtml', r'/jyxxzcgg/\d+\.jhtml', r'/jyxxtdgg/\d+\.jhtml', r'/jyxxcqgg/\d+\.jhtml',
            r'/jyxxtpfgg/\d+\.jhtml', r'/jyxxypgg/\d+\.jhtml', r'/jyxxncgg/\d+\.html', r'/jyxxpmgg/\d+\.jhtml',
            # r'/jyxxjdgg/\d+\.jhtml',  # TODO 待验证
            # r'/jyxxjsgg/\d+\.jhtml'  # TODO 待验证
        ], tags=('li'), attrs=('onclick'), process_value=process_value_s), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_ZB_NOTICE}, callback="parse_item", follow=False),
        # 资格预审公告
        Rule(LinkExtractor(allow=[
            r'/jyxxgczs/\d+\.jhtml',
            # r'/jyxxjdzs/\d+\.jhtml'  # TODO 待验证
        ],
            tags=('li'), attrs=('onclick'), process_value=process_value_s), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 招标变更根据标题带有关键词“更正”归类
        Rule(LinkExtractor(allow=[r'/jyxxzcgz/\d+\.jhtml'], tags=('li'), attrs=('onclick'),
                           process_value=process_value_s), process_request=process_request_category,
             cb_kwargs={"name": const.TYPE_ZB_ALTERATION}, callback="parse_item", follow=False),
        # 招标异常
        Rule(LinkExtractor(allow=[r'/jyxxzcgz/\d+\.jhtml'], tags=('li'), attrs=('onclick'),
                           process_value=process_value_s), process_request=process_request_category,
             cb_kwargs={"name": const.TYPE_ZB_ABNORMAL}, callback="parse_item", follow=False),
        # 中标预告
        Rule(LinkExtractor(allow=[
            r'/jyxxgchx/\d+\.jhtml',
            # r'/jyxxjdhx/\d+\.jhtml'  # TODO 待验证
        ],
            tags=('li'), attrs=('onclick'), process_value=process_value_s),
            process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 中标公告
        Rule(LinkExtractor(
            allow=[r'/jyxxgcgs/\d+\.jhtml', r'/jyxxzcgs/\d+\.jhtml', r'/jyxxtdgs/\d+\.jhtml', r'/jyxxcqgs/\d+\.jhtml',
                   # r'/jyxxjdgs/\d+\.jhtml',  # TODO 待验证
                   r'/jyxxtpfgs/\d+\.jhtml',
                   # r'/jyxxjsgs/\d+\.jhtml',  # TODO 待验证
                   r'/jyxxncgs/\d+\.jhtml',
                   r'/jyxxpmgs/\d+\.jhtml'], tags=('li'), attrs=('onclick'), process_value=process_value_s),
            process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_item", follow=False),
        # 其他公告
        Rule(LinkExtractor(allow=[
            r'/jyxxxnyba/\d+\.jhtml', r'/jyxxzfbz/\d+\.jhtml'],
            tags=('li'), attrs=('onclick'), process_value=process_value_s), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_item", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.time_dict = {}
        r_dict = {"title": "", "origin": "", "ext": ""}
        self.time_dict = {"inDates": "4000"} | r_dict
        if inDates := kwargs.get("day"):  # 1为当天，3为近3天，以此类推;4000为全部时间，则为全量脚本
            self.time_dict = {
                                 "inDates": inDates,
                             } | r_dict

    def start_requests(self):
        # TODO 更正公告没有val
        for item in [
            "29", "37", "42", "45", "48", "55", "58", "61", "64", "67",  # 招标公告
            "30", "49",  # 资格预审公告
            "32", "51",  # 中标预告
            "33", "38", "43", "46", "52", "56", "62", "65", "68",  # 中标公告
            "39", "246", "247"  # 其他
        ]:
            yield scrapy.FormRequest(
                self.query_url, formdata=self.time_dict | {"channelId": item}, callback=self.parse_urls, meta={
                    "channelId": item
                })

    def parse_urls(self, response):
        # 取总信息数量
        if count_str := re.search(r"count: \d+", response.text):
            limit = 10
            count = int(re.search(r"\d+", count_str.group(0)).group(0))
            # 取每页的信息数量
            if limit_str := re.search(r"limit: \d+", response.text):
                limit = int(re.search(r"\d+", limit_str.group(0)).group(0))
            self.logger.info(f"初始链接提取成功： id={response.meta['channelId']} {count=}")
            pages = math.ceil(count / limit) + 1
            for i in range(1, pages):
                yield scrapy.FormRequest(
                    self.query_page_url.format(i), formdata=self.time_dict | {"channelId": response.meta["channelId"]})
        else:
            self.logger.error(f"初始链接数量提取异常：{response.url=} {response.meta=}")

    def parse_item(self, response, name):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("//*[@id='content']/div[2]/h2/text()").get() or ""
            info_source = ""
            info_data = response.xpath("//*[@id='content']/div[2]/p/text()").get()
            try:
                info_source = info_data.split("信息来源：")[1].split("浏览次数")[0].strip()
            except:
                pass
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            pub_time = get_accurate_pub_time(info_data)
            content = response.xpath('//*[@class="content"]').get()
            classify_show = response.meta.get("classify_show", "")
            files_path = []
            # if content:
            #     pub_time_simple = pub_time.split(" ")[0]
            #     if files := re.findall(r"https://sh-gov-open-doc.oss-cn-shanghai.aliyuncs.com/.*?\"", content):
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
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classify_show

            if name == const.TYPE_ZB_ALTERATION and re.search(r"更正", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ALTERATION
            elif name == const.TYPE_ZB_ABNORMAL and re.search(r"终止", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = name
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_11_shanghai_spider".split(" "))
