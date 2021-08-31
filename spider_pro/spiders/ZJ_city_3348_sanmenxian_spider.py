#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-08-03
# @Describe: 台州市三门县公共资源交易
import re
import math
import json
import scrapy
import urllib
from urllib import parse

from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const

from spider_pro.utils import get_accurate_pub_time, file_notout_time, judge_dst_time_in_interval,remove_specific_element


class MySpider(Spider):
    name = "ZJ_city_3348_sanmenxian_spider"
    area_id = "3348"
    area_province = "浙江-台州市三门县公共资源交易服务平台"
    allowed_domains = ['jyzx.sanmen.gov.cn']
    domain_url = "http://jyzx.sanmen.gov.cn"
    list_url = "http://jyzx.sanmen.gov.cn/Content/jyxx/{}"
    page_size = "10"
    # 招标预告
    list_advance_notice_num = ["zbwjyfs", 'yjzx']
    # 招标公告
    list_notice_category_num = ["zbgg", "cggg", "tzgg", "crgg", 'jygg']
    # 招标变更
    list_alteration_category_num = ["bccq", "gzgg"]
    # 中标预告
    list_win_advance_notice_num = ["kbjggg", "zbgs", 'hxrgs']
    # 中标公告
    list_win_notice_category_num = ["zbjg", "cjjg", "cjjg", "jyjg"]
    # 其他公告
    list_others_notice_num = ['xmjbxx', 'htgg', 'lyqk', 'lygg']

    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num \
                            + list_win_advance_notice_num + list_win_notice_category_num +list_others_notice_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        cookies_str = 'JSESSIONID=90E57B532D2336F051A3734F6A9136F0; SERVERID=bc6beea6e995cecb42c7a1341ba3517f|1626679104|1626675536'
                      # 将cookies_str转换为cookies_dict
        self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}
        self.class_list = ['gcjs', 'zfcg', 'cqjy', 'tdcr', 'tzljy', '/xzpt']

    def start_requests(self):
        for item in self.class_list:
            url = self.list_url.format(item)
            yield scrapy.Request(url=url, priority=2, callback=self.parse_urls, meta={"classifyShow": item})

    def parse_urls(self, response):
        try:
            classifyShow = response.meta["classifyShow"]
            class_url_list = response.xpath("//dl[@class='content-left']//dd/a/@href").getall()
            for item in class_url_list:
                class_url = self.domain_url + item
                yield scrapy.Request(url=class_url, priority=4, callback=self.parse_son_urls, meta={"classifyShow": classifyShow})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_son_urls(self, response):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.get_pages_urls
        classifyShow = response.meta["classifyShow"]
        class_url_list = response.xpath("//dl[@class='content-left']//dd/a/@href").getall()
        for i, item in enumerate(class_url_list, start=1):
            class_url = self.domain_url + item
            yield scrapy.Request(url=class_url, priority=4, callback=callback_url,
                                 meta={"classifyShow": classifyShow, "info_num": i}, dont_filter=True)

    def extract_data_urls(self, response):
        url = response.url
        notice_type = url.split("/")[-1]
        classifyShow = response.meta["classifyShow"]
        ttlrow = response.xpath("//ul[@class='pagination']/@data-pagecount").get()
        count_num = 0
        endrecord = 1
        temp_list = response.xpath("//div[@class='list-news']/ul/li")
        for item in temp_list:
            info_url = item.xpath("./a/@href").get()
            title_name = item.xpath("./a/@title").get()
            pub_time = item.xpath("./a/span[@class='time']/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                info_url = self.domain_url + info_url
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=10, meta={"title_name": title_name, "pub_time": pub_time,
                                                        "classifyShow": classifyShow, "notice_type": notice_type,
                                                        "info_num": response.meta["info_num"]})
            if count_num >= len(temp_list):
                endrecord += 1
                if endrecord <= int(ttlrow):
                    page_url = url + "?pageIndex={}".format(endrecord)
                    yield scrapy.Request(url=page_url, priority=6, callback=self.get_page_urls, dont_filter=True,
                                 meta={"classifyShow": classifyShow, "notice_type": notice_type, "info_num": response.meta["info_num"]})

    def get_pages_urls(self, response):
        url = response.url
        notice_type = url.split("/")[-1]
        classifyShow = response.meta["classifyShow"]
        pages = response.xpath("//ul[@class='pagination']/@data-pagecount").get()
        for page in range(1, int(pages) + 1):
            page_url = url + "?pageIndex={}"
            yield scrapy.Request(url=page_url, priority=6, callback=self.get_page_urls, dont_filter=True,
                                 meta={"classifyShow": classifyShow, "notice_type": notice_type, "info_num": response.meta["info_num"]})

    def get_page_urls(self, response):
        try:
            classifyShow = response.meta["classifyShow"]
            notice_type = response.meta["notice_type"]
            data_list = response.xpath("//div[@class='list-news']/ul/li")
            for item in data_list:
                info_url = item.xpath("./a/@href").get()
                title_name = item.xpath("./a/@title").get()
                pub_time = item.xpath("./a/span[@class='time']/text()").get()
                pub_time = get_accurate_pub_time(pub_time)
                info_url = self.domain_url + info_url
                # info_url = "http://jyzx.sanmen.gov.cn/Detail/17744"
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=10, meta={"title_name": title_name, "pub_time": pub_time,
                                                        "classifyShow": classifyShow, "notice_type": notice_type,
                                                        "info_num": response.meta["info_num"]})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            print(origin)
            info_num = response.meta["info_num"]
            notice_type = response.meta.get("notice_type", "")
            classifyshow = response.meta.get("classifyShow", "")
            title_name = response.meta.get("title_name", "")
            pub_time = response.meta.get("pub_time", "")
            info_source = self.area_province
            content = response.xpath("//ul[@class='list-show']/li[{}]".format(info_num)).get()
            content = re.sub("display: none", "display: block", content)
            files_path = {}
            if file_notout_time(pub_time):
                if file_list := response.xpath("//ul[@class='list-show']/li[{}]//a".format(info_num)):
                    for item in file_list:
                        if file_url := item.xpath("./@href").get():
                            if re.findall("""/Uploads/file.*?\.pdf""", file_url):
                                file_url = self.domain_url + file_url
                                file_name = item.xpath("./text()").get()
                                files_path[file_name] = file_url
                            if re.findall("""download""", file_url):
                                file_name = item.xpath("./text()").get()
                                files_path[file_name] = file_url
                            if re.findall("""DownloadFile""", file_url):
                                file_name = item.xpath("./text()").get() + "." + file_url.split(".")[-1]
                                files_path[file_name] = file_url
                            # if file_url := re.findall("""https://cqjy.smztb.com:443/www/downloadTAttachment?id=.*?""", file_url):
                            #     file_name = item.xpath("./text()").get()
                            #     files_path[file_name] = file_url
                            # if file_url := re.findall("""https://tz.smztb.com/attachment/download?id=.*?""", file_url):
                            #     file_name = item.xpath("./text()").get()
                            #     files_path[file_name] = file_url

            print(files_path)
            if notice_type in self.list_advance_notice_num:
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif notice_type in self.list_notice_category_num:
                notice_type = const.TYPE_ZB_NOTICE
            elif notice_type in self.list_alteration_category_num:
                notice_type = const.TYPE_ZB_ALTERATION
            elif notice_type in self.list_win_notice_category_num:
                notice_type = const.TYPE_WIN_NOTICE
            elif notice_type in self.list_win_advance_notice_num:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif notice_type in self.list_others_notice_num:
                notice_type = const.TYPE_OTHERS_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE

            if re.search(r"单一来源|询价|竞争性谈判|竞争性磋商", title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r"采购意向|需求公示", title_name):
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif re.search(r"候选人|评标结果", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充|延期|取消", title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"测试项目", title_name):
                notice_type = const.TYPE_UNKNOWN_NOTICE

            if classifyshow == "gcjs":
                classifyShow = "工程建设"
            elif classifyshow == "zfcg":
                classifyShow = "政府采购"
            elif classifyshow == "cqjy":
                classifyShow = "产权交易"
            elif classifyshow == "tdcr":
                classifyShow = "土地出让"
            elif classifyshow == "tzljy":
                classifyShow = "拓展类交易"
            else:
                classifyShow = "小额交易"

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            # print(type(files_path))
            # print(notice_item)
            # # TODO 产品要求推送，故注释
            # # if not is_clean:
            # #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3348_sanmenxian_spider -a sdt=2021-08-04 -a edt=2021-08-30".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3348_sanmenxian_spider".split(" "))