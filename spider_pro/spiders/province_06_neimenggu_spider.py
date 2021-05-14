#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-04
# @Describe: 内蒙古公共资源交易平台 - 全量/增量脚本
#
import re
import math
import json
import scrapy
import random
import urllib
import datetime
from urllib import parse
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_iframe_pdf_div_code

def process_request_category(origin):
    for item in ["jsgcZbgg", "jsgcGzsx", "jsgcZbhxrgs", "jsgcZbjggs", "jyxxgcjshtgs"]:
        if item in origin:
            classify_show = "工程建设"
            return classify_show
    for item in ["zfcg/cggg", "zfcg/gzsx", "zfcg/zbjggs"]:
        if item in origin:
            classify_show = "政府采购"
            return classify_show
    for item in ["tdAndKq/toCrggPage", "tdAndKq/toCjqrPage"]:
        if item in origin:
            classify_show = "土地矿权"
            return classify_show
    for item in ["cqjy/cjqr", "jyxxswzcjyjg", "jyxxgqgpplxx"]:
        if item in origin:
            classify_show = "国有产权"
            return classify_show
    for item in ["qtjy/jygg", "qtjy/jyqr",]:
        if item in origin:
            classify_show = "其他交易"
            return classify_show
    for item in ["classTwo/jygg", "classTwo/jyjg", "jyxxrjxxjyjg"]:
        if item in origin:
            classify_show = "疫苗交易"
            return classify_show


class MySpider(CrawlSpider):
    name = 'province_06_neimenggu_spider'
    area_id = "06"
    domain_url = "http://ggzyjy.nmg.gov.cn"
    query_url = "http://ggzyjy.nmg.gov.cn/jyxx/"
    allowed_domains = ['ggzyjy.nmg.gov.cn']
    # 招标公告
    list_notice_category_num = ["jsgcZbgg", "zfcg/cggg", "tdAndKq/toCrggPage", "cqjy/crgg", "qtjy/jygg",
                                "classTwo/jygg"]
    # 招标变更
    list_alteration_category_num = ["jsgcGzsx", "zfcg/gzsx"]
    # 中标预告
    list_win_advance_category_num = ["jsgcZbhxrgs"]
    # 中标公告
    list_win_notice_category_num = ["jsgcZbjggs", "zfcg/zbjggs", "tdAndKq/toCjqrPage", "cqjy/cjqr", "qtjy/jyqr",
                                    "classTwo/jyjg"]

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_advance_category_num + \
                            list_win_notice_category_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"industriesTypeCode": "", "time": "", "bulletinName": "", "area": ""}
        # scrollValue 滚动条坐标
        self.scrollValue = {"scrollValue": ""}
        self.time_dict = {"startTime": "", "endTime": ""}

    def start_requests(self):
        for item in self.list_all_category_num:
            random_int = random.randint(200, 500)
            list_url = self.query_url + item
            yield scrapy.FormRequest(list_url, priority=6, formdata=self.r_dict | {"scrollValue": "".format(random_int)} |
                                                        self.time_dict | {"currentPage": "1"}, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            pages = re.search(r"共\d+页", response.text)
            self.logger.info(f"本次获取总条数为：{pages}")
            if pages_str := re.search(r"totalPage = \d+", response.text):
                pages = int(re.search(r"\d+", pages_str.group(0)).group(0))
                pages = int(pages) + 1
                for i in range(1, pages):
                    if not i == 1:
                        self.query_url = "http://ggzyjy.shandong.gov.cn/queryContent_{}-jyxxgk.jspx".format(i)
                    else:
                        self.query_url = "http://ggzyjy.shandong.gov.cn/queryContent-jyxxgk.jspx"
                    yield scrapy.FormRequest(self.query_url, priority=8, formdata=self.r_dict, callback=self.parse_data_urls, )
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath("/html/body/div[4]/div[2]/div/ul/li").getall()
            for item in li_list:
                data_url = re.search(r"http://ggzyjy.shandong.gov.cn:80/\w+/\d+\.jhtml", item).group(0)
                data_url = get_real_url(data_url)
                info_source = re.search(r"信息来源：\w+", item).group(0)
                info_source = info_source.split("信息来源：")[1]
                classifyShow = re.search(r"业务类型：\w+", item).group(0)
                classifyShow = classifyShow.split("业务类型：")[1]
                category_num = item.split("信息分类：")[1]
                category_num = category_num.split("</div>")[0]
                if category_num in self.list_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif category_num in self.list_win_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
                elif category_num in self.list_win_advance_category_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
                else:
                    self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

                yield scrapy.Request(url=data_url, callback=self.parse_item,priority=10, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                           "classifyShow": classifyShow})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            info_source = response.meta.get("info_source")
            classifyShow = response.meta.get("classifyShow")
            title_name = response.xpath("//div[@class='div-title']/text()").get()
            title_name = "".join(title_name)
            title_name = title_name.strip()
            pub_time = response.xpath("/html/body/div[4]/div[2]/div[5]/div[1]/span[1]/text()").get()
            if not pub_time:
                pub_time = response.xpath("//*[@id='85']/li/div").get()
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath("/html/body/div[4]/div[2]/div[5]").get()
            if not content:
                content = response.xpath("/html/body/div[4]/div[2]/div[5]/div[2]/table").get()

            files_path = []
            is_clean = True
            # 判断是pdf页面
            try:
                if url_str := re.search(r'''<a id='pdfUrl' href=".*?">''', response.text):
                    url_pdf_str = url_str.group(0).split(r'''<a id='pdfUrl' href="''')[1].split(r'''">''')[0]
                    url_pdf_str_list = [self.domain_url]
                    url_pdf_str_list.extend(url_pdf_str.split('/')[-3:])
                    url_pdf = '/'.join(url_pdf_str_list)
                    url_pdf_date = url_pdf.split('/')[-2]
                    file_item = FileItem()
                    unquote_name = parse.unquote(url_pdf).split("/")[-1]
                    file_item["file_url"] = url_pdf
                    file_item["file_name"] = unquote_name.split('.')[0]
                    file_item["file_type"] = unquote_name.split('.')[1]
                    file_item["file_path"] = fr"{self.name}/{url_pdf_date}/{unquote_name}"
                    files_path.append(file_item["file_path"])
                    is_clean = False
                    # TODO 替换成本站链接
                    content = get_iframe_pdf_div_code(url=url_pdf)
                    yield file_item
            except Exception as e:
                pass
            if re.search(r"候选人", title_name):
                self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
            elif re.search(r"变更|更正", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}

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
            notice_item["category"] = classifyShow

            # TODO 产品要求推送，故注释
            # if not is_clean:
            #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_06_neimenggu_spider".split(" "))
    # cmdline.execute("scrapy crawl province_21_shandong_spider -a sdt=2021-02-01 -a edt=2021-03-18".split(" "))
    # cmdline.execute("scrapy crawl province_21_shandong_spider".split(" "))
