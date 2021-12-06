#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-07-13
# @Describe: 金华市永康市公共资源交易网
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
    name = "ZJ_city_3355_yongkang_spider"
    area_id = "3355"
    area_province = "浙江-金华市永康市公共资源交易服务平台"
    allowed_domains = ['yk.gov.cn']
    domain_url = "http://www.yk.gov.cn"
    count_url = "http://www.yk.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=20"
    page_size = "10"
    # 招标预告
    list_advance_notice_num = ["1229505631"]
    # 招标公告
    list_notice_category_num = ["1229497995", "1229497999", "1229498002"]
    # 招标变更
    list_alteration_category_num = ["1229497996", "1229498000"]
    # 中标预告
    list_win_advance_notice_num = ["1229497997"]
    # 中标公告
    list_win_notice_category_num = ["1229497998", "1229498001", "1229498004"]

    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num \
                            + list_win_advance_notice_num + list_win_notice_category_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"col": "1", "appid": "1", "webid": "3586", "sourceContentType": "1",
        "unitid": "6804595", "path": "/", "webname": "永康市人民政府", "permissiontype": "0"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        cookies_str = 'SERVERID=57526053d080975751a9538d16dda0a7|1626174283|1626174269'
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
        endrecord = 45
        count_num = 0
        for item in temp_list:
            title_name = re.findall('title="(.*?)"', item.get())[0]
            info_url = re.findall('href="(.*?)"', item.get())[0]
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
                pub_time = re.findall('\d+\-\d+\-\d+', item.get())[0]
                # info_url = "http://www.yk.gov.cn/art/2021/7/15/art_1229497995_3898961.html"
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
            content = response.xpath("//div[@class='con_article-bd']").get()
            _, contents = remove_specific_element(content, 'div', 'class', 'clearfix', index=0)
            files_path = {}
            try:
                if file_notout_time(pub_time):
                    if file_list := re.findall("""href="(/module/download/downfile.jsp.*?)\"""", content):
                        for i, file_url_str in enumerate(file_list):
                            if re.search("反馈表.doc", content) and i == 0:
                                file_name = "反馈表.doc"
                            else:
                                file_name = "附件{}".format(i) + ".doc"
                            file_url = self.domain_url + re.sub("amp;", "", file_url_str)
                            files_path[file_name] = file_url

                    # if file_info := response.xpath("//div[@class='article-fj']"):
                    #     file_url = file_info.xpath("./a/@href").get()
                    #     file_url = self.domain_url + file_url
                    #     file_name = file_info.xpath("./a/text()").get() + ".doc"
                    #     files_path[file_name] = file_url
                    # if picture_list := re.findall('src="(/picture/.*?)"', content):
                    #     file_suffix = picture_list[0].split(".")[1]
                    #     file_url = self.domain_url + picture_list[0]
                    #     file_name = "picture." + file_suffix
                    #     files_path[file_name] = file_url
                    #
                    if picture_url := response.xpath("//div[@class='con_article-con']/img/@src").get():
                        file_name = "picture.jpg"
                        files_path[file_name] = picture_url
                    #
                    # if file_list := re.findall("""<a href="(/module/download/downfile.jsp.*?)">.*?png">(.*?)</a>""", content):
                    #     for file_url_str in file_list:
                    #         file_name = file_url_str[1]
                    #         file_url = self.domain_url + re.sub("amp;", "", file_url_str[0])
                    #         files_path[file_name] = file_url
                    if file_list := re.findall("""href="(http://www.jhykztb.cn/fileserver//down.*?)".*?tag">(.*?)</a>""", content):
                        for file_url_str in file_list:
                            file_name = file_url_str[1]
                            file_url = re.sub("amp;", "", file_url_str[0])
                            files_path[file_name] = file_url
                    if file_list := re.findall("""href="(http://www.jhykztb.cn/fileserver//down.*?)">(.*?)</a>""", content):
                        for file_url_str in file_list:
                            file_name = file_url_str[1]
                            file_url = re.sub("amp;", "", file_url_str[0])
                            files_path[file_name] = file_url

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
            elif re.search(r"候选人|评标结果", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充|延期|取消", title_name):
                notice_type = const.TYPE_ZB_ALTERATION

            if category_num in ["1229498002", "1229498004"]:
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
            notice_item["content"] = contents
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
    # cmdline.execute("scrapy crawl ZJ_city_3355_yongkang_spider -a sdt=2021-08-04 -a edt=2021-08-30".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3355_yongkang_spider".split(" "))