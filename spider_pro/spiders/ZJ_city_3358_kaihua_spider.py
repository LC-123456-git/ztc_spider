#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-07-05
# @Describe: 衢州开化县公共资源交易网
import re
import math
import json
import scrapy
import urllib
import requests
from urllib import parse

from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const

from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval,remove_specific_element


class MySpider(Spider):
    name = "ZJ_city_3358_kaihua_spider"
    area_id = "3358"
    area_province = "浙江-衢州市开化县公共资源交易服务平台"
    allowed_domains = ['kaihua.gov.cn']
    domain_url = "http://www.kaihua.gov.cn"
    count_url = "http://www.kaihua.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=10"
    # 招标公告
    list_notice_category_num = ["1229091438", "1229091458", "1229091464"]
    # 中标预告
    list_win_advance_notice_num = ["1229091439", "1229091459", "1229091459"]
    # 中标公告
    list_win_notice_category_num = ["1229091440", "1229091460", "1229091465"]
    # 其他公告
    list_other_notice = ["1229091453"]

    list_all_category_num = list_notice_category_num + list_win_advance_notice_num + \
                            list_win_notice_category_num + list_other_notice

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"col": "1", "appid": "1", "webid": "2681", "sourceContentType": "1",
        "unitid": "6250988", "webname": "开化县人民政府", "path": "/", "permissiontype": "0"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        cookies_str = 'JSESSIONID=E1FAF55052EA5FC5C4DD56ED2FB0A767; SERVERID=57526053d080975751a9538d16dda0a7|1625468091|1625466041'
                      # 将cookies_str转换为cookies_dict
        self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.parse_urls
        for item in self.list_all_category_num:
            # item = "1229091464"
            temp_dict = self.r_dict | {"columnid": "{}".format(item)}
            yield scrapy.FormRequest(self.count_url.format("1", "30"), formdata=temp_dict, priority=2, cookies=self.cookies_dict,
                                     callback=callback_url, meta={"afficheType": str(item)})

    def extract_data_urls(self, response):
        temp_list = response.xpath("recordset//record")
        category_num = response.meta["afficheType"]
        ttlrow = response.xpath("totalrecord/text()").get()
        startrecord = 1
        endrecord = 30
        count_num = 0
        for item in temp_list:
            title_name = re.findall("title='(.*?)'", item.get())[0]
            info_url = re.findall("href='(.*?)'", item.get())[0]
            pub_time = re.findall("&gt;(\d+\-\d+\-\d+)&lt;", item.get())[0]
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                yield scrapy.Request(url=info_url, callback=self.parse_item,  dont_filter=True,
                                     priority=10, meta={"category_num": category_num, "pub_time": pub_time,
                                                        "title_name": title_name})
            if count_num >= len(temp_list):
                startrecord += 30
                endrecord += 30
                if endrecord <= int(ttlrow):
                    temp_dict = self.r_dict | {"columnid": "{}".format(category_num)}
                    yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                             dont_filter=True, callback=self.parse_data_urls, priority=8, cookies=self.cookies_dict,
                                             meta={"afficheType": category_num})

    def parse_urls(self, response):
        try:
            startrecord = 1
            endrecord = 30
            afficheType = response.meta["afficheType"]
            ttlrow = response.xpath("totalrecord/text()").get()
            if int(ttlrow) < 30:
                pages = 1
                endrecord = int(ttlrow)
            else:
                pages = int(ttlrow) // 30
            self.logger.info(f"本次获取总条数为：{ttlrow},共有{pages}页")
            for page in range(1, pages+1):
                if page > 1:
                    startrecord += 30
                    endrecord += 30
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
                info_url = re.findall('href="(.*?)"', item.get())[0]
                pub_time = re.findall("&gt;(\d+\-\d+\-\d+)&lt;", item.get())[0]
                # info_url = "http://www.kaihua.gov.cn/art/2021/7/8/art_1229091438_4683817.html"
                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                     priority=10, meta={
                                           "category_num": category_num, "pub_time": pub_time,
                                           })
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            print(origin)
            category_num = response.meta.get("category_num", "")
            title_name = response.xpath("//title/text()").get()
            pub_time = response.meta.get("pub_time", "")
            info_source = self.area_province
            content = response.xpath("//table[@id='c']").get()
            # _, content = remove_specific_element(content, 'td', 'class', 'bt-heise', index=0)
            _, content = remove_specific_element(content, 'tr', 'align', 'center', index=0)
            _, content = remove_specific_element(content, 'td', 'align', 'right', index=0)
            files_path = {}
            files_list = []
            if file_list := re.findall("""<a href="(/module/download/downfile.jsp.*?)">.*?>(.*?)</a>""", content):
                for item in file_list:
                    file_url = self.domain_url + re.sub("amp;", "", item[0])
                    file_name = item[1]
                    files_path[file_name] = file_url
            if file_url_test := re.findall("附件请至（.*?）下载", content):
                get_file_url = file_url_test[0].split("附件请至（")[1].split("）下载")[0]
                cid = get_file_url.split(".htm")[0].split("/")[-1]
                strst_url = get_file_url.split("cms")[0]
                response = requests.get(url=get_file_url)
                response = response.content.decode('utf-8')
                a_xml = etree.HTML(response)
                file_name_list = a_xml.xpath("//table/tr/td[1]/a/text()")
                num = len(file_name_list)
                cid_url = "{}cms/attachment_url.jspx?cid={}&n={}".format(strst_url, cid, num)
                file_infourl = "{}cms/attachment.jspx?cid={}&i={}{}"
                res_list = requests.get(url=cid_url).content.decode('utf-8')
                i = 0
                for file_name, file_url in zip(file_name_list, eval(res_list)):
                    file_url = file_infourl.format(strst_url, cid, i, file_url)
                    print(file_url)
                    files_path[file_name] = file_url
                    file_path_str = "<a href='{}'>{}</a>".format(file_url, file_name)
                    files_list.append(file_path_str)
                    i += 1
                file_paths = "<br/>".join(files_list)
                content = re.sub("附件请至（.*?）下载", file_paths, content)
            if category_num in self.list_notice_category_num:
                notice_type = const.TYPE_ZB_NOTICE
            elif category_num in self.list_win_notice_category_num:
                notice_type = const.TYPE_WIN_NOTICE
            elif category_num in self.list_win_advance_notice_num:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif category_num in self.list_other_notice:
                notice_type = const.TYPE_OTHERS_NOTICE
            else:
                notice_type = const.TYPE_UNKNOWN_NOTICE

            if re.search(r"终止|中止|流标|废标|异常|暂停", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"招标|谈判|磋商|出让|招租", title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r"候选人|评标结果", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"变更|更正|澄清|修正|补充", title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"关于.*?的通知|关于.*?的公告", title_name):
                notice_type = const.TYPE_UNKNOWN_NOTICE

            if category_num in ["1229091438", "1229091439", "1229091440"]:
                classifyShow = "工程建设"
            else:
                classifyShow = "其他交易"

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
    # cmdline.execute("scrapy crawl ZJ_city_3358_kaihua_spider -a sdt=2020-01-04 -a edt=2020-01-04".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3358_kaihua_spider".split(" "))