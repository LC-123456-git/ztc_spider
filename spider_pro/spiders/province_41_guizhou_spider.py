#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-02-01
# @Describe: 贵州省公共资源交易中心
import re
import math
import json
import scrapy
import datetime
import urllib
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http.request.json_request import JsonRequest
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = 'province_41_guizhou_spider'
    area_id = "41"
    domain_url = "http://ggzy.guizhou.gov.cn"
    query_url = "http://ggzy.guizhou.gov.cn/import/trade/getPageList"
    get_list_url = "http://ggzy.guizhou.gov.cn/igs/front/search/list.html?"
    info_url = "http://ggzy.guizhou.gov.cn/jyxx/view.html?meteIds="
    allowed_domains = ['ggzy.guizhou.gov.cn']

    # 招标公告
    list_notice_category_num = ["招标公告", "资审公告", "采购公告", "交易公告", "通知公告"]
    # 资格预审结果公告
    list_qualification_advance_notice = ["资审结果公示", "资审结果公告"]
    # 招标变更
    list_alteration_category_num = ["更正公告", "变更公告", "澄清与答疑", "变更转让公告"]
    # 招标异常
    list_zb_abnormal = ["流标公示", "废标公告", "异常公告", "废标公示"]
    # 中标预告
    list_win_advance_category_num = ["中标候选人公示"]
    # 中标公告
    list_win_notice_category_num = ["中标（成交）公告", "中标（成交）结果公告",  "交易结果公示", "中标结果公告", "中标公示"]
    # 其他公告
    list_other_notice = ["最高限价公示", "交易证明书"]

    # 产权交易
    cqjy_list = ["5237521"]
    # 政府采购
    zfcg_list = ["5377338", "5377101", "5377103"]
    # 建设工程
    jsgc_list = ["5377337", "5377100", "5376927"]
    # 医药采购
    yycg_list = ["5237522"]

    area_province = "贵州省公共资源交易服务平台"

    headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                # "Content-Length": "57",
                "Content-Type": "application/json;charset=UTF-8",
                "Cookie": "UM_distinctid=17743175c2e5d6-0a483a4fea218b-e343166-13c680-17743175c2faed; _trs_uv=kkf7e6rs_4151_bqsd; token=a5eee624-d9c5-4956-9112-178ce5bf639a; uuid=a5eee624-d9c5-4956-9112-178ce5bf639a; _trs_ua_s_1=kkmd628k_4151_9upg; G3_SESSION_V=MmNiMDAxNzUtMmQzOS00N2JkLThjNjgtZjhmYmZlMGZmNTMy; CNZZDATA1278901740=1866882402-1611735481-%7C1612171856",
                "Host": "ggzy.guizhou.gov.cn",
                "Origin": "http://ggzy.guizhou.gov.cn",
                "Referer": "http://ggzy.guizhou.gov.cn/jyxx/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
                }

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

        # self.pn_dict = {"pageNum": 1}
        # self.r_dict = {"pageSize": 10, "siteId": 500483, "isPage": True}
        # self.today = datetime.datetime.today().date()
        # if kwargs.get("sdt") and kwargs.get("edt"):
        #     self.time_dict = {"timeStart": kwargs.get('sdt') + ' 00:00:00', 'timeEnd': kwargs.get('edt') + ' 23:59:59'}
        # if kwargs.get("day"):
        #     self.time_dict = {'timeStart': get_back_date(kwargs.get('day')) + ' 00:00:00',
        #                       'timeEnd': str(self.today) + ' 23:59:59'}
        # self.time_dict = {}
        # self.pn_dict = {"pageNumber": 1}
        self.r_dict = {"pageSize": 10, "siteId": 500483, "isPage": True}
        self.today = datetime.datetime.today().date()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.time_dict = {"filter[docRelTime-gte]": kwargs.get('sdt') + ' 00:00:00', 'filter[docRelTime-lte]': kwargs.get('edt') + ' 23:59:59'}
        if kwargs.get("day"):
            self.time_dict = {'filter[docRelTime-gte]': get_back_date(kwargs.get('day')) + ' 00:00:00',
                              'filter[docRelTime-lte]': str(self.today) + ' 23:59:59'}
        self.pn_dict = {"pageSize": 10, "siteId": 500483, "index": "trades", "type": "infomation_v6",
                        "filter[channelId]": "5376927,5377100,5377337,5377101,5377103,5377338,5237520,5237521,5617491,5617492,5617493,5237523",
                        "orderProperty": "docRelTime", "orderDirection": "desc", "isPage": "true", "filter[docTitle-like]": ""}
        self.page_dict = {"pageNumber": 1}
        # self.linshi_dict = {"pageNumber": 1, "pageSize": 100, "siteId": 500483, "index": "trades", "type": "infomation_v6",
        #                    "filter[channelId]": "5377101,5377103,5377338",
        #                    "orderProperty": "docRelTime", "orderDirection": "desc", "isPage": "true", "filter[docTitle-like]": "",
        #                    "filter[docRelTime-gte]": "2021-05-20 00:00:00", "filter[docRelTime-lte]": "2021-05-20 23:59:59"}
    def start_requests(self):
        # pages_dict = self.r_dict | self.time_dict | self.pn_dict
        # self.type_dict = json.dumps(pages_dict)
        # print(self.type_dict)
        # yield scrapy.Request(url=self.query_url, method="POST", body=self.type_dict, headers=self.headers, callback=self.parse_urls)
        yield scrapy.Request(url=f"{self.get_list_url}{urllib.parse.urlencode(self.time_dict|self.pn_dict|self.page_dict)}", callback=self.parse_urls)
        # yield scrapy.Request(url=f"{self.get_list_url}{urllib.parse.urlencode(self.linshi_dict)}", callback=self.parse_item)

    def parse_urls(self, response):
        try:
            total = json.loads(response.text).get("page").get("total")
            self.logger.info(f"初始总数提取成功  {total=} {response.url=}")
            pages = json.loads(response.text).get("page").get("totalPages")
            for i in range(1, int(pages) + 1):
                yield scrapy.Request(url=f"{self.get_list_url}{urllib.parse.urlencode(self.time_dict|self.pn_dict|{'pageNumber': i})}",
                                     callback=self.parse_item)
            # if json.loads(response.text).get("message") == "查询成功":
            #     total = json.loads(response.text).get("data").get("total")
            #     if total == None:
            #         return
            #     self.logger.info(
            #         f"初始总数提取成功  {total=} {response.url=} ")
            #     pages = math.ceil(int(total) / int(10))
            #     for i in range(1, pages):
            #         pn_dict = {"pageNum": i}
            #         self.page_dict = json.dumps(self.r_dict | pn_dict | self.time_dict)
            #         yield scrapy.Request(
            #             url=self.query_url, method="POST", body=self.page_dict, headers=self.headers,
            #             callback=self.parse_data_urls)
            # else:
            #     self.logger.error(f"初始总页数提取错误 {json.loads(response.text).get('message')}{response.url=}")
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    # def parse_data_urls(self, response):
    #     try:
    #         pass
    #         # records = json.loads(response.text).get("data").get("list")
    #         # for urls in records:
    #         #     title_name = urls.get("docTitle", "")
    #         #     pub_time = urls.get("docRelTime", "")
    #         #     info_source = urls.get("docSourceName", "")
    #         #     category_num = urls.get("intypeName", "")
    #         #     channelId = urls.get("channelId", "")
    #         #     if channelId in self.cqjy_list:
    #         #         name_project_category = "产权交易"
    #         #     elif channelId in self.zfcg_list:
    #         #         if category_num == "1" or category_num == "交易公告":
    #         #             category_num = "采购公告"
    #         #         elif category_num == "2" or category_num == "中标结果公告":
    #         #             category_num = "中标（成交）公告"
    #         #         elif category_num == "3" or category_num == "流标公示":
    #         #             category_num = "废标公告"
    #         #         elif category_num == "4":
    #         #             category_num = "资审结果公示"
    #         #         elif category_num == "5" or category_num == "项目澄清":
    #         #             category_num = "变更公告"
    #         #         elif category_num == "6":
    #         #             category_num = "交易证明书"
    #         #         elif category_num == "9":
    #         #             category_num = "其他"
    #         #         name_project_category = "政府采购"
    #         #     elif channelId in self.jsgc_list:
    #         #         if category_num == "1":
    #         #             category_num = "招标公告"
    #         #         elif category_num == "2":
    #         #             category_num = "交易结果公示"
    #         #         elif category_num == "3":
    #         #             category_num = "流标公示"
    #         #         elif category_num == "4" :
    #         #             category_num = "资审结果公示"
    #         #         elif category_num == "5":
    #         #             category_num = "项目澄清"
    #         #         elif category_num == "6":
    #         #             category_num = "交易证明书"
    #         #         elif category_num == "9":
    #         #             category_num = "最高限价公示"
    #         #         name_project_category = "建设工程"
    #         #     elif channelId in self.yycg_list:
    #         #         name_project_category = "医药采购"
    #         #     else:
    #         #         category_num = "通知公告"
    #         #         name_project_category = urls.get("bulletinType", "")
    #         #     # 招标公告
    #         #
    #         #     data_url = urls.get("docpubUrl", "")
    #         #     yield scrapy.Request(url=data_url, callback=self.parse_item,
    #         #                          cb_kwargs=cb_kwargs, meta={"cb_kwargs": cb_kwargs, "info_source": info_source,
    #         #                                                     "name_project_category": name_project_category,
    #         #                                                     "pub_time": pub_time, "title_name": title_name})
    #     except Exception as e:
    #         self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        content_list = json.loads(response.text).get("page").get("content")
        for num, item in enumerate(content_list):
            origin = self.info_url + str(item.get("MetaDataId", ""))
            name_project_category = item.get("bulletinType", "")
            pub_time = item.get("crTime", "")
            title_name = item.get("docTitle", "")
            print(title_name)
            info_source = item.get("docSourceName", "")
            info_source = self.area_province + info_source
            notice_type = item.get("inTypeName", "")
            content = item.get("docContent", "")
            if notice_type in self.list_notice_category_num:
                notice_type = const.TYPE_ZB_NOTICE
                # 资格预审结果公告
            elif notice_type in self.list_qualification_advance_notice:
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                # 招标变更
            elif notice_type in self.list_alteration_category_num:
                notice_type = const.TYPE_ZB_ALTERATION
                #  招标异常
            elif notice_type in self.list_zb_abnormal:
                notice_type = const.TYPE_ZB_ABNORMAL
                #  其他公告
            elif notice_type in self.list_other_notice:
                notice_type = const.TYPE_OTHERS_NOTICE
                # 中标预告
            elif re.search("候选人", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                # 中标预告
            elif notice_type in self.list_win_advance_category_num:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                # 中标公告
            elif notice_type in self.list_win_notice_category_num or re.search("中标结果", title_name):
                notice_type = const.TYPE_WIN_NOTICE
                # 未知公告
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE


            files_path = {}
            # if response.status == 200:
        #     origin = response.url
        #     title_name = response.meta.get("title_name")
        #     if not title_name:
        #         title_name = response.xpath("//*[@id='tab-800']/div/div[2]/div/div/h2/text()").get()
        #     if not title_name:
        #         title_name = response.xpath("//*[@id='title']/text()").get()
        #     if not title_name:
        #         title_name = ""
        #     pub_time = response.meta.get("pub_time")
        #     pub_time = get_accurate_pub_time(pub_time)
        #     info_source = response.meta.get("info_source")
        #     if not info_source:
        #         info_source = self.area_province
        #     info_source = f"{self.area_province}-{info_source}"
        #     content = response.xpath("//div[@class='view_con']").get()
        #     if not content:
        #         content = response.xpath("//*[@id='newsText']/div[1]").get()
        #     if not content:
        #         content = response.xpath("//*[@id='newsText']").get()
        #     files_path = {}
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
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = name_project_category
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_41_guizhou_spider -a sdt=2021-06-11 -a edt=2021-06-11".split(" "))
    # cmdline.execute("scrapy crawl province_41_guizhou_spider".split(" "))
    # cmdline.execute("scrapy crawl province_41_guizhou_spider -a day=0".split(" "))
