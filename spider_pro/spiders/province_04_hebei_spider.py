#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-02-01
# @Describe: 河北省公共资源交易中心
import re
import math
import json
import scrapy
import datetime
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date,judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'province_04_hebei_spider'
    area_id = "04"
    sss = 0
    domain_url = "http://ggzy.hebei.gov.cn/hbggfwpt"
    query_url = "http://ggzy.hebei.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
    allowed_domains = ['ggzy.hebei.gov.cn']
    # 招标公告
    list_notice_category_num = ["采购/资审公告", "招标/资审公告", "转让预披露/披露公告", "出让/转让公告", "招标公告", "交易公告"]
    # 招标变更
    list_alteration_category_num = ["变更结果公告", "更正公告", "澄清/变更公告", "变更公告"]
    # 招标异常
    list_zb_abnormal = ["取消中标单位中标资格公告"]
    # 中标预告
    list_win_advance_notice_num = ["中标候选人公示"]
    # 中标公告
    list_win_notice_category_num = ["中标、成交结果公告", "中标结果公告", "成交公告", "成交公示"]

    area_province = "河北省公共资源交易平台"

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        self.pn_dict = {"pn": 0}
        self.r_dict = {"token": "", "rn": 12, "sdt": "", "edt": "", "wd": "", "inc_wd": "", "exc_wd": "",
                       "fields": "title", "cnum": "001", "sort": "{'webdate':'0'}", "ssort": "title", "cl": 200,
                       "terminal": "", "condition": [{"fieldName": "categorynum", "equal": "003001",
                       "notEqual": None, "equalList": None, "notEqualList": None, "isLike": True,
                       "likeType": 2}], "time": None, "highlights": "title", "statistics": None, "unionCondition": None,
                       "accuracy": "", "noParticiple": "0", "searchRange": None, "isBusiness": "1"}

    def start_requests(self):
        self.type_dict = json.dumps(self.r_dict | self.pn_dict)
        yield scrapy.Request(url=self.query_url, method="POST", body=self.type_dict, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            total = json.loads(response.text).get("result").get("totalcount")
            if total == None:
                return
            self.logger.info(
                f"初始总数提取成功 {total=} {response.url=} ")
            pages = math.ceil(int(total) / int(10)) + 1
            for i in range(1, pages):
                if i == 1:
                    pn = 0
                else:
                    pn += 10
                pn_dict = {"pn": pn}
                self.page_dict = json.dumps(self.r_dict | pn_dict)
                yield scrapy.Request(
                    url=self.query_url, method="POST", body=self.page_dict,
                    callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            records = json.loads(response.text).get("result").get("records")
            for urls in records:
                category_num = urls.get("categoryname", "")
                linkurl = urls.get("linkurl", "")
                info_source = urls.get("infod", "")
                title_name = urls.get("title", "")
                pub_time = urls.get("webdate", "")
                name_project_category = urls.get("catename", "")
                if category_num in self.list_notice_category_num:
                    cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif re.search(r"资格预审|资格公告", title_name):
                    cb_kwargs = {"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}
                elif category_num in self.list_alteration_category_num or re.search(r"变更公告", title_name):
                    cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
                elif category_num in self.list_win_advance_notice_num:
                    cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
                elif re.search(r"终止|中止|流标|废标|异常", title_name) or category_num in self.list_zb_abnormal:
                    cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
                else:
                    cb_kwargs = {"name": const.TYPE_WIN_NOTICE}

                if self.enable_incr:
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        data_url = self.domain_url + linkurl
                        self.sss += 1
                        print(self.sss)
                        yield scrapy.Request(url=data_url, callback=self.parse_item, meta={
                            "title_name": title_name,
                            "pub_time": pub_time,
                            "cb_kwargs": cb_kwargs,
                            "info_source": info_source,
                            "name_project_category": name_project_category}, cb_kwargs=cb_kwargs)
                    else:
                        continue
                else:
                    data_url = self.domain_url + linkurl
                    yield scrapy.Request(url=data_url, callback=self.parse_item, meta={
                        "title_name": title_name,
                        "pub_time": pub_time,
                        "cb_kwargs": cb_kwargs,
                        "info_source": info_source,
                        "name_project_category": name_project_category,
                    }, cb_kwargs=cb_kwargs)

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            pub_time = get_accurate_pub_time(pub_time)
            info_source = response.meta.get("info_source")
            print(title_name)
            if not info_source:
                info_source = self.area_province
            else:
                info_source = f"{self.area_province}-{info_source}"
            content = response.xpath("//div[@class='ewb-copy']").get()
            if not content:
                content = response.xpath("/html/body/div[1]/div[3]/div[2]/div[3]/div[2]/div/div[2]/div").get()
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

    # cmdline.execute("scrapy crawl province_04_hebei_spider".split(" "))
    cmdline.execute("scrapy crawl province_04_hebei_spider -a sdt=2021-04-02 -a edt=2021-04-02".split(" "))
