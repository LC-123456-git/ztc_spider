#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-06-30
# @Describe: 拱墅区公共资源交易网
import re
import math
import json
import scrapy
import urllib
import requests
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(Spider):
    name = "ZJ_city_3329_gongshu_spider"
    area_id = "3329"
    area_province = "浙江-杭州市-拱墅区"
    allowed_domains = ['gongshu.gov.cn']
    domain_url = "http://www.gongshu.gov.cn/"
    count_url = "http://www.gongshu.gov.cn/zwgk/public/home/gszw/realmListData.action?"
    base_url = "http://www.gongshu.gov.cn/zwgk/public/home/gszw/realmDetailsData.action"
    info_url = "http://www.gongshu.gov.cn/zwgk/public/home/gszw/realmDetails.action?strMap.uuid={}"

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {'area': '', 'IsToday': '', 'title': '', 'proID': '', 'number': '',
                  '_search': 'false', 'nd': '1617083532556', 'rows': '10', 'sidx': 'PublishStartTime',
                  'sord': 'desc'}

    def start_requests(self):
        temp_dict = {"strMap.columnUuid": "E1450138F63747948B4CF6A72FA06833", "strMap.current": "1"}
        yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_urls, priority=7)

    def parse_urls(self, response):
        try:
            response_text = json.loads(response.text)
            ttlrow = response_text.get("total", "")
            pages = response_text.get("page", "")
            self.logger.info(f"本次获取总条数为：{ttlrow}，共有{pages}页")
            for i in range(1, int(pages) + 1):
                temp_dict = {"strMap.columnUuid": "E1450138F63747948B4CF6A72FA06833", "strMap.current": "{}".format(i)}
                yield scrapy.FormRequest(self.count_url, formdata=temp_dict, dont_filter=True, priority=8,
                                         callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            response_text = json.loads(response.text)
            temp_list = response_text.get("rows", "")
            for item in temp_list:
                title_name = item.get("rsmegTitle", "")
                rsmegUuid = item.get("rsmegUuid", "")
                pub_time = item.get("rsmegCdate", "")
                info_url =self.info_url.format(rsmegUuid)
                yield scrapy.FormRequest(url=self.base_url, formdata={"strMap.uuid": "{}".format(rsmegUuid)},
                                         callback=self.parse_item, dont_filter=True, priority=100,
                                         meta={"title_name": title_name, "pub_time": pub_time, "info_url": info_url})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.meta.get("info_url", "")
            print(origin)
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            pub_time = get_accurate_pub_time(re.sub("T", " ", pub_time))
            info_source = self.area_province
            content = json.loads(response.text).get("rsmegContent", "")
            notice_type_str = json.loads(response.text).get("rsmegBy5", "")
            if re.search(r"采购意向|需求公示", notice_type_str):
                notice_type = {"name": const.TYPE_ZB_ADVANCE_NOTICE}
            elif re.search(r"单一来源|询价|竞争性谈判|竞争性磋商|招标(采购)公告|招标公告", notice_type_str):
                notice_type = {"name": const.TYPE_ZB_NOTICE}
            elif re.search(r"资格预审|资格后审", notice_type_str):
                notice_type = {"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}
            elif re.search(r"终止|中止|流标|废标|异常", notice_type_str):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|补充|取消|延期|答疑", notice_type_str):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"候选人", notice_type_str):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"中标结果公示|成交公告|中标公告|结果公告", notice_type_str):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r"开标结果|合同公告", notice_type_str):
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE
            files_path = {}
            if fjxx_list := re.findall('<a href="(.*?)".*?>(.*?)</a>', content):
                for fjxx in fjxx_list:
                    file_url = fjxx[0]
                    if re.search(">", fjxx[1]):
                        file_name = fjxx[1].split(">")[1]
                    else:
                        file_name = fjxx[1]
                    files_path[file_name] = file_url

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl ZJ_city_3329_gongshu_spider -a sdt=2021-06-04 -a edt=2021-06-28".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3329_gongshu_spider".split(" "))
