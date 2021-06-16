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


def process_request_category(item):
    if item in ["jyxxgczs", "jyxxgcgg", "jyxxgchx", "jyxxgcgs"]:
            classify_show = "工程建设"
    elif item in ["jyxxzcxm", "jyxxzcgg", "jyxxzcgs", "jyxxzcht"]:
        classify_show = "政府采购"        
    elif item in ["jyxxtdgg", "jyxxtdgs"]:
        classify_show = "土地出让"           
    elif item in ["jyxxcqgg", "jyxxcqgs"]:
        classify_show = "国有产权"         
    # TODO 机电设备
    elif item in ["jyxxtpfgg", "jyxxtpfgs"]:
        classify_show = "碳排放权"          
    elif item in ["jyxxypgg"]:
        classify_show = "药品采购"            
    # TODO 技术交易
    elif item in ["jyxxncgg", "jyxxncgs"]:
        classify_show = "农村产权"            
    elif item in ["jyxxpmgg"]:  # TODO 司法拍卖-结果公告
        classify_show = "司法拍卖"            
    elif item in ["jyxxxnyba"]:  # TODO 新能源汽车补助-除备案外
        classify_show = "新能源汽车补助"           
    elif item in ["jyxxzfbz"]:  # TODO 住房保障-除共有产权保障住房外
        classify_show = "住房保障"
    else:
        classify_show = "其他"
    return classify_show
            
    # TODO 物资采购


def get_notice_type(item):
    # 招标公告
    if item in ['jyxxgcgg', 'jyxxzcgg', 'jyxxtdgg', 'jyxxcqgg','jyxxtpfgg', 'jyxxypgg', 'jyxxncgg/\d+\.html',
                'jyxxpmgg']:
        notice_type = const.TYPE_ZB_NOTICE
    # 资格预审公告
    elif item in ['jyxxgczs']:
        notice_type =  const.TYPE_QUALIFICATION_ADVANCE_NOTICE
    # 招标变更根据标题带有关键词“更正”归类
    elif item in ['jyxxzcgz']:
        notice_type =  const.TYPE_ZB_ALTERATION
    # 招标异常
    elif item in ['jyxxzcgz']:
        notice_type =  const.TYPE_ZB_ABNORMAL
    # 中标预告
    elif item in ['jyxxgchx',]:
        notice_type =  const.TYPE_WIN_ADVANCE_NOTICE
    # 中标公告
    elif item in['jyxxgcgs', 'jyxxzcgs', 'jyxxtdgs', 'jyxxcqgs','jyxxtpfgs','jyxxncgs','jyxxpmgs']:
        notice_type = const.TYPE_WIN_NOTICE
    # 其他公告
    elif item in ['jyxxxnyba', 'jyxxzfbz']:
        notice_type = const.TYPE_WIN_NOTICE
    else:
        notice_type = const.TYPE_UNKNOWN_NOTICE
    return notice_type


class MySpider(CrawlSpider):
    name = "province_11_shanghai_spider"
    area_id = "11"
    area_province = "上海市公共资源交易服务平台"
    allowed_domains = ['shggzy.com']
    domain_url = "https://www.shggzy.com"
    query_url = "https://www.shggzy.com/queryContent-jyxx.jspx"
    query_page_url = "https://www.shggzy.com/queryContent_{}-jyxx.jspx"

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
                self.query_url, priority=6, formdata=self.time_dict | {"channelId": item}, callback=self.parse_urls, meta={
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
                    self.query_page_url.format(i), priority=8, callback=self.parse_data_urls,
                    formdata=self.time_dict | {"channelId": response.meta["channelId"]})
        else:
            self.logger.error(f"初始链接数量提取异常：{response.url=} {response.meta=}")

    def parse_data_urls(self, response):
        li_list = response.xpath("//div[@class='gui-title-bottom']/ul/li")
        for item in li_list:
            info_url_str = item.xpath("./@onclick").get()
            info_url = re.search(r"http://www.shggzy.com:80/\w+/\d+.jhtml", info_url_str).group(0)
            pub_time = item.xpath("./span[4]/text()").get()
            title_name = item.xpath("./span[2]/text()").get().replace("\n", "").replace("\t", "").replace("\r", "").split()
            title_name = "".join(title_name)
            project_number = item.xpath("./span[2]/text()").get().replace("\n", "").replace("\t", "").replace("\r", "").split()
            project_number = "".join(project_number)
            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=10, meta={"pub_time": pub_time,
                                                                                            "title_name": title_name,
                                                                                            "project_number": project_number})

    def parse_item(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            title_name = response.meta.get("title_name", "")
            pub_time = response.meta.get("pub_time", "")
            project_number = response.meta.get("project_number", "")
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
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//*[@class="content"]').get()
            item_str = origin.split("https://www.shggzy.com/")[1].split("/")[0]
            classify_show = process_request_category(item_str)
            notice_type = get_notice_type(item_str)
            files_path = {}

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
            notice_item["project_number"] = project_number

            if notice_type == const.TYPE_ZB_ALTERATION and re.search(r"更正", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ALTERATION
            elif notice_type == const.TYPE_ZB_ABNORMAL and re.search(r"终止", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = notice_type
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_11_shanghai_spider".split(" "))
    cmdline.execute("scrapy crawl province_11_shanghai_spider -a day=1".split(" "))
