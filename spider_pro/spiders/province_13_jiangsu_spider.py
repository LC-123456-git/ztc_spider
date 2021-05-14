#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-10
# @Describe: 江苏省公共资源交易中心
import re
import math
import json
import scrapy
import datetime
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = 'province_13_jiangsu_spider'
    area_id = "13"
    domain_url = "http://jsggzy.jszwfw.gov.cn"
    query_url = "http://jsggzy.jszwfw.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
    allowed_domains = ['jsggzy.jszwfw.gov.cn']
    # 建设工程未入围公示，最高限价公示分类待定
    # 招标预告
    list_advance_notice_num = ["003004001"]
    # 招标公告
    list_notice_category_num = ["003001001", "003002001", "003003001", "003004002", "003013001", "003006001",
                                "003010001", "003011001", "003014001", "003009001"]
    # 招标变更
    list_alteration_category_num = ["003004003"]
    # 中标预告
    list_win_advance_notice_num = ["003001007", "003002003", "003003003"]
    # 中标公告
    list_win_notice_category_num = ["003001008", "003002004", "003003004", "003004006", "003013002", "003006004",
                                    "003010002", "003011002", "003014002", "003009002"]

    area_province = "江苏省公共资源交易服务平台"
    project_category_dict = {
        "003001": "建设工程",
        "003002": "交通工程",
        "003003": "水利工程",
        "003004": "政府采购",
        "003013": "土地矿业交易",
        "003006": "国有产权",
        "003010": "药品耗材采购",
        "003011": "机电设备",
        "003014": "农村产权",
        "003009": "其他交易"
    }

    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num \
                            + list_win_advance_notice_num + list_win_notice_category_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": "2021-01-07 00:00:00",
                                    "endTime": "2021-01-10 23:59:59"}]}
        self.pn_dict = {"pn": 0}
        self.days = "1"
        self.con_dict = {
            "condition": [{"fieldName": "categorynum", "isLike": "true", "likeType": 2, "equal": "003001"}]}
        self.r_dict = {"token": "", "rn": 20, "sdt": "", "edt": "", "wd": "null", "inc_wd": "", "exc_wd": "",
                       "fields": "title", "cnum": "001", "sort": "{\"infodatepx\":\"0\"}", "ssort": "title", "cl": 200,
                       "terminal": "", "highlights": "title", "statistics": "null", "unionCondition": "null",
                       "accuracy": "", "noParticiple": "1", "searchRange": "null", "isBusiness": "1"}
        self.today = datetime.datetime.today().date()
        self.begin = datetime.date(2018, 10, 7)
        if day := kwargs.get("day"):
            if day == "0":
                self.days = "0"
                # for i in range((today - begin).days + 1):
                #     day = begin + datetime.timedelta(days=i)
                #     self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": str(day)+" 00:00:00",
                #                                 "endTime": str(day)+" 23:59:59"}]}
            else:
                self.time_dict = {"time": [{"fieldName": "infodatepx",
                                            "startTime": str(get_back_date(int(day) - 1)) + " 00:00:00",
                                            "endTime": str(get_back_date(0)) + " 23:59:59"}]}
        elif kwargs.get("sdt") and kwargs.get("edt"):
            self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": kwargs.get("sdt") + " 00:00:00",
                                        "endTime": kwargs.get("edt") + " 23:59:59"}]}
        else:
            self.days = "0"
        #     for i in range((today - begin).days + 1):
        #         day = begin + datetime.timedelta(days=i)
        #         self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": str(day)+" 00:00:00",
        #                                     "endTime": str(day)+" 23:59:59"}]}

    def start_requests(self):
        if self.days == "0":
            for i in range((self.today - self.begin).days + 1):
                day = self.begin + datetime.timedelta(days=i)
                self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": str(day) + " 00:00:00",
                                            "endTime": str(day) + " 23:59:59"}]}
                for item in self.list_all_category_num:
                    equal_dict = {"equal": item}
                    info_dict = {"fieldName": "categorynum", "isLike": "true", "likeType": 2} | equal_dict
                    con_dict = {"condition": [info_dict]}
                    pages_dict = self.r_dict | con_dict | self.time_dict
                    self.type_dict = json.dumps(pages_dict | self.pn_dict)
                    yield scrapy.Request(
                        url=self.query_url, method="POST",priority=5, body=self.type_dict, callback=self.parse_urls,
                        meta={"cont_id": item, "con_dict": con_dict}
                    )
        else:
            for item in self.list_all_category_num:
                equal_dict = {"equal": item}
                info_dict = {"fieldName": "categorynum", "isLike": "true", "likeType": 2} | equal_dict
                con_dict = {"condition": [info_dict]}
                pages_dict = self.r_dict | con_dict | self.time_dict
                self.type_dict = json.dumps(pages_dict | self.pn_dict)
                yield scrapy.Request(
                    url=self.query_url, method="POST", body=self.type_dict,priority=6, callback=self.parse_urls,
                    meta={"cont_id": item, "con_dict": con_dict}
                )

    def parse_urls(self, response):
        try:
            con_dict = response.meta.get("con_dict")
            total = json.loads(response.text).get("result").get("totalcount")
            if total == None:
                return
            self.logger.info(
                f"初始总数提取成功 {response.meta['cont_id']} {total=} {response.url=} ")
            pages = math.ceil(int(total) / int(20)) + 1
            for i in range(1, pages):
                if i == 1:
                    pn = 0
                else:
                    pn += 20
                pn_dict = {"pn": pn}
                self.page_dict = json.dumps(self.r_dict | pn_dict | con_dict | self.time_dict)
                yield scrapy.Request(
                    url=self.query_url, method="POST", body=self.page_dict,
                    callback=self.parse_data_urls, priority=8, meta={"cont_id": response.meta['cont_id']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            category_num = response.meta['cont_id']
            if category_num in self.list_notice_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
            elif category_num in self.list_alteration_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
            elif category_num in self.list_advance_notice_num:
                cb_kwargs = {"name": const.TYPE_ZB_ADVANCE_NOTICE}
            else:
                cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
            records = json.loads(response.text).get("result").get("records")
            for urls in records:
                linkurl = urls["linkurl"]
                area_in = urls.get("zhuanzai", "")
                name_project_category = self.project_category_dict.get(category_num[0:6], "")
                data_url = self.domain_url + linkurl
                yield scrapy.Request(url=data_url, callback=self.parse_item,priority=10, meta={
                    "cb_kwargs": cb_kwargs,
                    "area_in": area_in,
                    "name_project_category": name_project_category,
                }, cb_kwargs=cb_kwargs)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("/html/body/div[2]/div/div[3]/h2/text()").get() or ""
            print(title_name)
            if re.search(r"终止|中止|流标|废标|异常", title_name):
                name = const.TYPE_ZB_ABNORMAL
            if re.search(r"变更|更正", title_name):
                name = const.TYPE_ZB_ALTERATION
            if re.search(r"候选人", title_name):
                name = const.TYPE_WIN_ADVANCE_NOTICE
            pub_time = response.xpath("/html/body/div[2]/div/div[3]/div[1]/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            info_source = response.xpath("/html/body/div[2]/div/div[3]/div[1]/text()[2]").get()
            info_source = info_source.split("来源：")[1]
            area_in = response.meta.get("area_in")
            if not area_in:
                area_in = self.area_province
            else:
                area_in = f"{self.area_province}-{area_in}"
            if not info_source:
                info_source = area_in
            else:
                info_source = f"{area_in}-{info_source}"

            content = response.xpath("/html/body/div[2]/div/div[3]/div[2]").get()
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
            notice_item["category"] = response.meta.get("name_project_category")
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_13_jiangsu_spider -a sdt=2021-05-01 -a edt=2021-05-14".split(" "))
    # cmdline.execute("scrapy crawl province_13_jiangsu_spider -a sdt=2021-01-26 -a edt=2021-01-26".split(" "))
