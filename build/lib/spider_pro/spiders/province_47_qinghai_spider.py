#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-04-07
# @Describe: 青海省公共资源交易中心
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
    name = 'province_47_qinghai_spider'
    area_id = "47"
    domain_url = "https://www.qhggzyjy.gov.cn"
    query_url = "https://www.qhggzyjy.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
    allowed_domains = ['qhggzyjy.gov.cn']
    # 建设工程未入围公示，最高限价公示分类待定
    # # 招标预告
    # list_advance_notice_num = ["003004001"]
    # 招标公告
    list_notice_category_num = ["001001001", "001002001", "001003001", "001004001", "001004002", "001005001",
                                "001005002"]
    # 招标变更
    list_alteration_category_num = ["001001003", "001002002", "001003003"]
    # 资格预审结果公告
    list_qualification_advance_notice = ["001001002", "001001008", "001003002"]
    # 招标异常
    list_zb_abnormal = ["001001007", "001002005", "001004004", "001005006", "001005005"]
    # 中标预告
    list_win_advance_notice_num = ["001001005"]
    # 中标公告
    list_win_notice_category_num = ["001001006", "001002004", "001004003", "001005003", "001005004"]

    area_province = "青海省公共资源交易服务平台"
    project_category_dict = {
        "001001": "工程建设",
        "001002": "政府采购",
        "001003": "药品采购",
        "001004": "产权交易",
        "001005": "矿权及土地"
    }

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_qualification_advance_notice \
                            + list_zb_abnormal + list_win_advance_notice_num + list_win_notice_category_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.time_dict = {"time": [{"fieldName": "infodatepx", "startTime": "2021-01-07 00:00:00",
                                    "endTime": "2021-01-10 23:59:59"}]}
        self.pn_dict = {"pn": 0}
        self.days = "1"
        self.con_dict = {
            "condition": [{"fieldName": "categorynum", "isLike": "true", "likeType": 2, "equal": "001001001"}]}
        self.r_dict = {"token": "", "rn": 10, "sdt": "", "edt": "", "wd": "", "inc_wd": "", "exc_wd": "",
                       "fields": "title", "cnum": "001;002;003;004;005;006;007;008;009;010", "sort": "{\"showdate\":\"0\"}", "ssort": "title", "cl": 200,
                       "terminal": "", "time": "null", "highlights": "title", "statistics": "null", "unionCondition": "null",
                       "accuracy": "100", "noParticiple": "0", "searchRange": "null", "isBusiness": "1"}

    def start_requests(self):
        for item in self.list_all_category_num:
            equal_dict = {"equal": item}
            info_dict = {"fieldName": "categorynum", "isLike": "true", "likeType": 2} | equal_dict
            con_dict = {"condition": [info_dict]}
            pages_dict = self.r_dict | con_dict | self.time_dict
            self.type_dict = json.dumps(pages_dict | self.pn_dict)
            yield scrapy.Request(
                url=self.query_url, method="POST", body=self.type_dict, callback=self.parse_urls,
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
            pages = math.ceil(int(total) / int(10)) + 1
            for i in range(1, pages):
                if i == 1:
                    pn = 0
                else:
                    pn += 10
                pn_dict = {"pn": pn}
                self.page_dict = json.dumps(self.r_dict | pn_dict | con_dict | self.time_dict)
                yield scrapy.Request(
                    url=self.query_url, method="POST", body=self.page_dict,
                    callback=self.parse_data_urls, meta={"cont_id": response.meta['cont_id']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            category_num = response.meta['cont_id']
            if category_num in self.list_notice_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
            elif category_num in self.list_alteration_category_num:
                cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
            elif category_num in self.list_qualification_advance_notice:
                cb_kwargs = {"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}
            elif category_num in self.list_zb_abnormal:
                cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
            elif category_num in self.list_win_advance_notice_num:
                cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
            elif category_num in self.list_win_notice_category_num:
                cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
            else:
                cb_kwargs = {"name": const.TYPE_OTHERS_NOTICE}
            records = json.loads(response.text).get("result").get("records")
            for urls in records:
                linkurl = urls.get("linkurl", "")
                info_source = urls.get("xiaquname", "")
                pub_time = urls.get("infodate", "")
                title_name = urls.get("title", "")
                name_project_category = self.project_category_dict.get(category_num[0:6], "")
                data_url = self.domain_url + linkurl
                yield scrapy.Request(url=data_url, callback=self.parse_item, priority=10, meta={
                    "cb_kwargs": cb_kwargs,
                    "info_source": info_source,
                    "pub_time": pub_time,
                    "title_name": title_name,
                    "name_project_category": name_project_category,
                }, cb_kwargs=cb_kwargs)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            print(origin)
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            if re.search(r"终止|中止|流标|废标|异常", title_name):
                name = const.TYPE_ZB_ABNORMAL
            if re.search(r"变更|更正", title_name):
                name = const.TYPE_ZB_ALTERATION
            if re.search(r"候选人", title_name):
                name = const.TYPE_WIN_ADVANCE_NOTICE
            pub_time = get_accurate_pub_time(pub_time)

            info_source = response.meta.get("info_source")
            if not info_source:
                info_source = self.area_province
            else:
                info_source = f"{self.area_province}-{info_source}"
            try:
                content = response.xpath("//div[@class='ewb-ca-detail clearfix']").get()
                if not content:
                    content = response.xpath("//div[@class='ewb-ca-detail']").get()
                patterns = re.compile(r'<div class="xiangxidate".*?>(.*?)</div>', re.S)
                content = content.replace(re.findall(patterns, content)[0], '')
                content = re.sub("&nbsp", "", content)
                files_path = {}
                if jpg_path := response.xpath('//div[@class="xiangxiyekuang"]/p//img'):
                    info_jpg_url = jpg_path.xpath('./@src').get()
                    info_jpg_url = self.domain_url + info_jpg_url
                    files_path["info_jpg"] = info_jpg_url
                if file_text := response.xpath("//div[@class='ewb-ca-detail clearfix']/div[@id='att']"):
                    if li_list := file_text.xpath("//li"):
                        for item in li_list:
                            value = item.xpath("./a/@href").get()
                            if not value:
                                patterns = re.compile(r'<div class="ewb-m-p hidden".*?>(.*?)</div>', re.S)
                                content = content.replace(re.findall(patterns, content)[0], '')
                            if "http" in item.xpath("./a/@href").get():
                                value = item.xpath("./a/@href").get()
                            else:
                                value = self.domain_url + item.xpath("./a/@href").get()
                            key = item.xpath('./a/text()').get()
                            files_path[key] = value
                # “附件如下：”的界面
                if file_text := response.xpath("//div[@class='l']"):
                    if file_text.xpath("//div[@class='l']/p[2]"):
                        for item in file_text:
                            if value := item.xpath("./p/a/@href").get():
                                if "http" in value:
                                    value = value
                                else:
                                    value = self.domain_url + value
                                key = file_text.xpath('./p/a/text()').get()
                                files_path[key] = value
                    else:
                        patterns = re.compile(r'<div class="l".*?>(.*?)</div>', re.S)
                        content = content.replace(re.findall(patterns, content)[0], '')
                print(files_path)
                # print(content)
            except Exception as e:
                print(e)

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
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["notice_type"] = name
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = response.meta.get("name_project_category")
            notice_item["web_name"] = self.area_province
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_47_qinghai_spider".split(" "))
    # cmdline.execute("scrapy crawl province_47_qinghai_spider -a sdt=2021-01-26 -a edt=2021-01-26".split(" "))