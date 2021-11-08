#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-07-13
# @Describe: 金华市兰溪市公共资源交易
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

from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval, file_notout_time


class MySpider(Spider):
    name = "ZJ_city_3353_lanxi_spider"
    area_id = "3353"
    area_province = "浙江-金华市兰溪市公共资源交易服务平台"
    allowed_domains = ['lanxi.gov.cn']
    domain_url = "www.lanxi.gov.cn"
    domain_name_url = "http://www.lanxi.gov.cn"
    count_url = "http://www.lanxi.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=20"
    page_size = "10"
    # 招标预告
    list_advance_notice_num = ["1229499357"]
    # 招标公告
    list_notice_category_num = ["1229196154", "1229196164", '1229196168', '1229196171', '1229196174', '1229196177',
                                '1229196180', '1229196183', '1229196186', '1229196189', '1229196192', '1229196195',
                                '1229196198', '1229196201', '1229196204', '1229196207', '1229196210', '1229196213']
    # 招标变更
    list_alteration_category_num = ["1229196155"]
    # 中标预告
    list_win_advance_notice_num = ["1229196156"]
    # 中标公告
    list_win_notice_category_num = ["1229196157", "1229196165", '1229196169', '1229196172', '1229196175', '1229196178',
                                    '1229196181', '1229196184', '1229196187', '1229196190', '1229196193', '1229196196',
                                    '1229196199', '1229196202', '1229196205', '1229196208', '1229196211', '1229196214']

    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num \
                            + list_win_advance_notice_num + list_win_notice_category_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"col": "1", "appid": "1", "webid": "3614", "sourceContentType": "1",
        "unitid": "6168450", "webname": "兰溪市人民政府", "permissiontype": "0"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        cookies_str = 'JSESSIONID=06529B7391A1DA551BF3052E0269D35C; UM_distinctid=1795e885e5e6d8-02f8ad48b783d8-c791039-1fa400-1795e885e5f6e7; zh_choose_undefined=s; LANXISESSIONID=e86fd7b7-fc0f-4d74-a241-63c546689626; CNZZDATA1279518033=1080451365-1620784032-https%253A%252F%252Fwww.baidu.com%252F%7C1626400717; SERVERID=a6d2b4ba439275d89aa9b072a5b72803|1626422222|1626414425'
                      # 将cookies_str转换为cookies_dict
        self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.parse_urls
        for item in self.list_all_category_num:
            temp_dict = self.r_dict | {"columnid": "{}".format(item)}
            yield scrapy.FormRequest(self.count_url.format("1", "60"), formdata=temp_dict, priority=2, cookies=self.cookies_dict,
                                 callback=callback_url, meta={"afficheType": str(item)})

    def extract_data_urls(self, response):
        temp_list = response.xpath("recordset//record")
        category_num = response.meta["afficheType"]
        ttlrow = response.xpath("totalrecord/text()").get()
        startrecord = 1
        endrecord = 60
        count_num = 0
        for item in temp_list:
            title_name = re.findall('title="(.*?)"', item.get())[0]
            info_url = re.findall('href="(.*?)"', item.get())[0]
            info_url = self.domain_name_url + "/" + info_url
            pub_time = re.findall('\d+\-\d+\-\d+', item.get())[0]
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                yield scrapy.Request(url=info_url, callback=self.parse_item,  dont_filter=True,
                                     priority=10, meta={"category_num": category_num, "pub_time": pub_time,
                                                        "title_name": title_name})
            if count_num >= len(temp_list):
                startrecord += 60
                endrecord += 60
                if endrecord <= int(ttlrow):
                    temp_dict = self.r_dict | {"columnid": "{}".format(category_num)}
                    yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                             dont_filter=True, callback=self.parse_data_urls, priority=8, cookies=self.cookies_dict,
                                             meta={"afficheType": category_num})

    def parse_urls(self, response):
        try:
            startrecord = 1
            endrecord = 60
            afficheType = response.meta["afficheType"]
            ttlrow = response.xpath("totalrecord/text()").get()
            if int(ttlrow) < 60:
                endrecord = int(ttlrow)
                pages = 1
            else:
                pages = int(ttlrow) // 60
            self.logger.info(f"本次获取总条数为：{ttlrow},共有{pages}页")
            for page in range(1, pages+1):
                if page > 1:
                    startrecord += 60
                    endrecord += 60
                    if endrecord > int(ttlrow):
                        endrecord = int(ttlrow)
                temp_dict = self.r_dict | {"columnid": "{}".format(afficheType)}
                yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                         dont_filter=True, callback=self.parse_data_urls, priority=8, cookies=self.cookies_dict,
                                         meta={"afficheType": afficheType})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            temp_list = response.xpath("recordset//record")
            category_num = response.meta["afficheType"]
            for item in temp_list:
                title_name = re.findall('title="(.*?)"', item.get())[0]
                info_url = re.findall('href="(.*?)"', item.get())[0]
                info_url = self.domain_name_url + "/" + info_url
                pub_time = re.findall('\d+\-\d+\-\d+', item.get())[0]
                # info_url = "http://www.lanxi.gov.cn/art/2021/7/16/art_1229499357_59238808.html"
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                     priority=10, meta={"category_num": category_num, "pub_time": pub_time,
                                           "title_name": title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            category_num = response.meta.get("category_num", "")
            title_name = response.meta.get("title_name", "")
            pub_time = response.meta.get("pub_time", "")
            info_source = self.area_province
            content = response.xpath("//div[@class='Main-p floatL']").get()
            files_path = {}
            try:
                if file_notout_time(pub_time):
                    if file_list := response.xpath("//div[@class='Main-p floatL']//a"):
                        for item in file_list:
                            if file_url := item.xpath("./@href").get():
                                if re.findall("""/module/download/downfile.jsp.*""", file_url):
                                    file_name = item.xpath("./text()").get()
                                    file_url = self.domain_name_url + file_url
                                    files_path[file_name] = file_url
                                elif re.findall('http://ztbapp.lx.gov.cn/fileserver//down.*', file_url):
                                    file_name = item.xpath("./text()").get()
                                    file_url = file_url
                                    files_path[file_name] = file_url
                    # 招标文件正文
                    if picture_url := response.xpath("//div[@class='Main-p floatL']//img[@class='Wzimg']/@src").get():
                        file_name = "picture.jpg"
                        files_path[file_name] = picture_url
                    if QR_code_list := re.findall('src="(/picture.*?)"', content):
                        for item in QR_code_list:
                            QRcode_url = self.domain_name_url + item
                            file_name = "QR_code"
                            files_path[file_name] = QRcode_url
            except Exception as e:
                print(e)
            if category_num in self.list_advance_notice_num:
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif category_num in self.list_notice_category_num:
                notice_type = const.TYPE_ZB_NOTICE
            elif category_num in self.list_alteration_category_num:
                notice_type = const.TYPE_ZB_ALTERATION
            elif category_num in self.list_win_notice_category_num:
                notice_type = const.TYPE_WIN_NOTICE
            elif category_num in self.list_win_advance_notice_num:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE

            if re.search(r"单一来源|询价|竞争性谈判|竞争性磋商", title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r"采购意向|需求公示", title_name):
                notice_type = const.TYPE_ZB_ADVANCE_NOTICE
            elif re.search(r"候选人", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充|延期|取消", title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"开标结果公示", title_name):
                notice_type = const.TYPE_OTHERS_NOTICE

            if category_num in ["1229196164", "1229196165"]:
                classifyShow = "产权交易"
            else:
                classifyShow = "工程建设"

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
    # cmdline.execute("scrapy crawl ZJ_city_3353_lanxi_spider -a sdt=2021-08-03 -a edt=2021-08-30".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3353_lanxi_spider".split(" "))