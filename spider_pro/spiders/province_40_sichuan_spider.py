#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-26
# @Describe: 四川省公共资源交易中心
import re
import math
import json
import scrapy
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http.request.json_request import JsonRequest
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = 'province_40_sichuan_spider'
    area_id = "40"
    domain_url = "http://ggzyjy.sc.gov.cn"
    query_url = "http://ggzyjy.sc.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData"
    allowed_domains = ['ggzyjy.sc.gov.cn']

    # 招标公告
    list_notice_category_num = ["002008001", "002001001", "002002001", "002003001", "002004001", "002005001",
                                "002005006", "002006001", "002007001"]
    # 招标变更
    list_alteration_category_num = ["002008002", "002001002", "002001003", "002002002", "002003005", "002004002"]
    # 招标异常
    list_zb_abnormal = ["002008004", "002001004", "002002005", "002003003", "002004004", "002005005", "002007003"]
    # 中标预告
    list_win_advance_notice_num = ["002001006"]
    # 中标公告
    list_win_notice_category_num = ["002008003", "002001008", "002002003", "002003002", "002004003", "002005002",
                                    "002006002", "002007002"]
    # 其他公告
    list_other_notice = ["002008005", "002001005", "002001007", "002002004", "002005003"]

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_zb_abnormal + \
                            list_win_advance_notice_num + list_win_notice_category_num + list_other_notice
    area_province = "四川省公共资源交易服务平台"
    project_category_dict = {
        "002008": "代理机构比选",
        "002001": "建设工程",
        "002002": "政府采购",
        "002003": "国有产权",
        "002004": "土地使用权",
        "002005": "矿业权",
        "002006": "药品药械",
        "002007": "其他类别"
    }
    headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
               "Accept-Encoding": "gzip, deflate",
               "Accept-Language": "zh-CN,zh;q=0.9",
               "Connection": "keep-alive",
               "Content-Length": "533",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               "Cookie": "JSESSIONID=3DBB429B306E24923A1787455D1E9028; UM_distinctid=1773d7db94fbcf-0f96fd492827a8-"
                         "e343166-13c680-1773d7db950afb; CNZZDATA1276636503=1144682475-1611640875-%7C1611646277",
               "Host": "ggzyjy.sc.gov.cn",
               "Origin": "http://ggzyjy.sc.gov.cn",
               "Referer": "http://ggzyjy.sc.gov.cn/jyxx/transactionInfo.html",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/75.0.3770.100 Safari/537.36",
               "X-Requested-With": "XMLHttpRequest"}
    data_headers = {
        'Cookie': 'clientlanguage=zh_CN; _gscu_740847421=10932974a1q3qv14; _gscbrs_740847421=1; JSESSIONID=A3ECF891BC4E07E161302D9775400FF9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

        self.pn_dict = {"pn": 0}
        self.r_dict = {"token": "", "rn": 12, "sdt": "", "edt": "", "wd": "", "inc_wd": "", "exc_wd": "",
                       "fields": "title", "cnum": "", "sort": "{'webdate':'0'}", "ssort": "title", "cl": 500,
                       "terminal": "", "condition": [{"fieldName": "categorynum", "equal": "002",
                       "notEqual": None, "equalList": None, "notEqualList": None, "isLike": True,
                       "likeType": 2}], "highlights": "", "statistics": None, "unionCondition": None,
                       "accuracy": "", "noParticiple": "0", "searchRange": None, "isBusiness": "1"}

        self.today = datetime.datetime.today().date()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.time_dict = {"time": [{'fieldName': 'webdate', 'startTime': kwargs.get('sdt') + ' 00:00:00',
                                        'endTime': kwargs.get('edt') + ' 23:59:59'}]}
        if kwargs.get("day"):
            self.time_dict = {"time": [{'fieldName': 'webdate',
            'startTime': get_back_date(kwargs.get('day')) + ' 00:00:00',
            'endTime': str(self.today) + ' 23:59:59'}]}
        self.time_dict = {"time": [{"fieldName": "webdate", "startTime": "2010-1-1 00:00:00",
                                    "endTime": str(self.today)+" 23:59:59"}]}

    def start_requests(self):
        pages_dict = self.r_dict | self.time_dict
        self.type_dict = json.dumps(pages_dict | self.pn_dict)
        yield scrapy.Request(url=self.query_url, method="POST", body=self.type_dict, callback=self.parse_urls)
        # yield scrapy.Request(url=self.query_url, method="POST", body=self.type_dict, callback=self.parse_data_urls)

    def parse_urls(self, response):
        try:
            total = json.loads(response.text).get("result").get("totalcount")
            if total == None:
                return
            self.logger.info(
                f"初始总数提取成功  {total=} {response.url=} ")
            pages = math.ceil(int(total) / int(12)) + 1
            for i in range(1, pages):
                if i == 1:
                    pn = 0
                else:
                    pn += 12
                pn_dict = {"pn": pn}
                self.page_dict = json.dumps(self.r_dict | pn_dict | self.time_dict)
                yield scrapy.Request(
                    url=self.query_url, method="POST", body=self.page_dict,
                    callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            records = json.loads(response.text).get("result").get("records")
            for urls in records:
                category_num = urls.get("categorynum", "")
                if category_num in self.list_notice_category_num:
                    cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif category_num in self.list_alteration_category_num:
                    cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
                elif category_num in self.list_zb_abnormal:
                    cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
                elif category_num in self.list_other_notice:
                    cb_kwargs = {"name": const.TYPE_OTHERS_NOTICE}
                else:
                    cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
                area_in = "".join(urls.get("zhuanzai", ""))
                linkurl = urls.get("linkurl", "")
                pub_time = urls.get("webdate", "")
                title_name = urls.get("title", "")
                name_project_category = self.project_category_dict.get(category_num[0:6], "")
                data_url = self.domain_url + linkurl
                # data_url = "http://ggzyjy.sc.gov.cn/jyxx/002008/002008001/20210330/2b4a62a4-bfec-4ad3-8ba1-d43bc2542337.html"
                yield scrapy.Request(url=data_url, callback=self.parse_item, headers=self.data_headers,
                                     cb_kwargs=cb_kwargs, meta={"cb_kwargs": cb_kwargs, "area_in": area_in,
                                                                "name_project_category": name_project_category,
                                                                "pub_time": pub_time, "title_name": title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            test_text = response.text
            title_name = response.meta.get("title_name")
            print(title_name)
            if not title_name:
                title_name = response.xpath("//*[@id='tab-800']/div/div[2]/div/div/h2/text()").get()
            if not title_name:
                title_name = response.xpath("//*[@id='title']/text()").get()
            if not title_name:
                title_name = ""
            else:
                if re.search(r"终止|中止|流标|废标|异常", title_name):
                    name = const.TYPE_ZB_ABNORMAL
                if re.search(r"变更|更正|澄清", title_name):
                    name = const.TYPE_ZB_ALTERATION
                if re.search(r"候选人", title_name):
                    name = const.TYPE_WIN_ADVANCE_NOTICE
            pub_time = response.meta.get("pub_time")
            pub_time = get_accurate_pub_time(pub_time)
            info_source = response.meta.get("area_in")
            if not info_source:
                info_source = self.area_province
            info_source = f"{self.area_province}-{info_source}"
            content = response.xpath('//div[@class="clearfix"]').get()

            pattern = re.compile(r'<p class="detailed-desc".*?>(.*?)</p>', re.S)
            contents = content.replace(''.join(re.findall(pattern, content)), '')
            print(content)
            # if not content:
            #     content = response.xpath("//*[@id='newsText']/div[1]").get()
            # if not content:
            #     content = response.xpath("//*[@id='newsText']").get()

            # print(origin)
            # print(title_name)
            # print(pub_time)
            # print(info_source)
            # print(content)
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
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = response.meta.get("name_project_category")
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_40_sichuan_spider".split(" "))
    # cmdline.execute("scrapy crawl province_40_sichuan_spider -a day=0".split(" "))
    cmdline.execute("scrapy crawl province_40_sichuan_spider -a sdt=2021-05-01 -a edt=2021-05-14".split(" "))
