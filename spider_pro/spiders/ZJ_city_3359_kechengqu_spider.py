#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-07-05
# @Describe: 衢州柯城区公共资源交易网
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

from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval,remove_specific_element


class MySpider(Spider):
    name = "ZJ_city_3359_kechengqu_spider"
    area_id = "3359"
    area_province = "浙江-衢州市柯城区公共资源交易服务平台"
    allowed_domains = ['kecheng.gov.cn']
    domain_url = "http://www.kecheng.gov.cn"
    count_url = "http://www.kecheng.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=20"
    type_list = ["6600801", "6600802", "6600803", "6600804"]


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"col": "1", "appid": "1", "webid": "3017", "sourceContentType": "9", "columnid": "1229449685",
         "webname": "柯城区人民政府", "path": "/", "permissiontype": "0"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        cookies_str = 'JSESSIONID=CCB943E7F919FB96A8AC77814A6D44BC; SERVERID=e741bbf83b6f24e79f118d965207c05f|1625456743|1625455585'
                      # 将cookies_str转换为cookies_dict
        self.cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.parse_urls
        # for item in self.type_list:
        item = "6600801"
        temp_dict = self.r_dict | {"unitid": "{}".format(item)}
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
            info_url = re.findall("href='(.*?)'", item.get())[0]
            pub_time = re.findall("&gt;(\d+\-\d+\-\d+)&lt;", item.get())[0]
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                count_num += 1
                yield scrapy.Request(url=info_url, callback=self.parse_item,  dont_filter=True,
                                     priority=10, meta={"category_num": category_num, "pub_time": pub_time})
            if count_num >= len(temp_list):
                startrecord += 60
                endrecord += 60
                if endrecord <= int(ttlrow):
                    temp_dict = self.r_dict | {"unitid": "{}".format(category_num)}
                    yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                             dont_filter=True, callback=self.parse_data_urls, priority=8, cookies=self.cookies_dict,
                                             meta={"afficheType": category_num})

    def parse_urls(self, response):
        try:
            afficheType = response.meta["afficheType"]
            ttlrow = response.xpath("totalrecord/text()").get()
            if int(ttlrow) < 60:
                pages = int(ttlrow)
            else:
                pages = int(ttlrow) // 60
            self.logger.info(f"本次获取总条数为：{ttlrow},共有{pages}页")
            startrecord = 1
            endrecord = 60
            for page in range(1, pages+1):
                if page > 1:
                    startrecord += 60
                    endrecord += 60
                    if endrecord > int(ttlrow):
                        endrecord = int(ttlrow)
                temp_dict = self.r_dict | {"unitid": "{}".format(afficheType)}
                yield scrapy.FormRequest(self.count_url.format(str(startrecord), str(endrecord)), formdata=temp_dict,
                                         dont_filter=True, callback=self.parse_data_urls, priority=8, cookies=self.cookies_dict,
                                         meta={"afficheType": afficheType, "temp_dict": temp_dict})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            temp_list = response.xpath("recordset//record")
            category_num = response.meta["afficheType"]
            for item in temp_list:
                info_url = re.findall('href="(.*?)"', item.get())[0]
                pub_time = re.findall("&gt;(\d+\-\d+\-\d+)&lt;", item.get())[0]
                info_url = self.domain_url + info_url
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
            title_name = response.xpath("//td[@class='title']/text()").get()
            title_name = title_name.strip()
            pub_time = response.meta.get("pub_time", "")
            info_source = self.area_province
            content = response.xpath("//table[@id='c']").get()
            # _, content = remove_specific_element(content, 'td', 'class', 'bt-heise', index=0)
            _, content = remove_specific_element(content, 'td', 'align', 'right', index=0)
            _, content = remove_specific_element(content, 'div', 'class', 'fare', index=0)
            content = re.sub("浏览次数: ", "", re.sub("分享到：", "", content))
            files_path = {}
            if file_list := re.findall("""附件:<a href="(.*)"><strong>""", content):
                file_suffix = file_list[0].split(".")[1]
                file_url = self.domain_url + file_list[0]
                file_name = "附件下载." + file_suffix
                files_path[file_name] = file_url

            if re.search(r"单一来源|询价|竞争性谈判|竞争性磋商|招标公告", title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r"候选人|评标结果", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充|延期|取消", title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"候选人|中标公示", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"结果公告|出让结果", title_name):
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type = const.TYPE_OTHERS_NOTICE

            if category_num in ["6600801"]:
                classifyShow = "政府采购"
            elif category_num in ["6600802", "6600803"]:
                classifyShow = "国有产权交易"
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
    # cmdline.execute("scrapy crawl ZJ_city_3359_kechengqu_spider -a sdt=2020-01-04 -a edt=2020-01-04".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3359_kechengqu_spider".split(" "))