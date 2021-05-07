# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-19
# @Describe: 绍兴市柯桥区公共资源中心 - 全量/增量脚本
import re
import math
import json

import requests
import scrapy
import random
import datetime
from urllib import parse
from lxml import etree

import xmltodict
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3315_keqiao_spider'
    area_id = "3315"
    domain_url = "http://www.kq.gov.cn"
    query_url = "http://www.kq.gov.cn/col/col1658072/index.html"
    base_url = 'http://www.kq.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=45&perpage=15'
    allowed_domains = ['kq.gov.cn']
    area_province = "浙江-绍兴市柯桥区公共资源交易服务平台"

    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告', '电子反拍公告', '拍卖服务公告', '交易公告', '网络拍卖拍卖公告']
    # 中标公告
    list_win_notice_category_num = ['中标结果', '电子反拍结果', '网络拍卖拍卖结果', '成交公告', '成交结果', '结果公告']
    # 招标异常
    list_alteration_category_num = ['流标公告']
    # 招标变更
    list_zb_abnormal_num = ['更正公告', '答疑公告']
    # 中标预告
    list_win_advance_notice_num = ['中标公示']
    # 资格预审结果公告
    list_qualification_num = ['']
    # 其他公告
    list_others_notice_num = ['征询意见', '采购合同公告', '网上超市结果', '意见征询', '合同公告']

    r_dict = {
                 'col': '1',
                 'appid': '1',
                 'sourceContentType': '1',
                 'webid': '2944',
                 'unitid': '5040126',
                 'webname': '绍兴市柯桥区人民政府',
                 'permissiontype': '0'
              }


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        # all_url = 'http://www.kq.gov.cn/art/2021/4/9/art_1658099_59063311.html'
        # yield scrapy.Request(url=all_url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            url_all = response.xpath('//div[@class="fun"]/a')[2:]
            for all in url_all:
                type_url = self.domain_url + all.xpath('./@href').get()
                classifyShow = all.xpath('./text()').get()
                yield scrapy.Request(url=type_url, callback=self.parse_data_urls,
                                     meta={'classifyShow': classifyShow})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            list_li = response.xpath('//div[@class="item"]/div')
            for li in list_li:
                type_url = self.domain_url + li.xpath('./a/@href').get()
                type_name = li.xpath('./span/text()').get()
                code = re.findall('(\d+)', type_url)[0]

                if type_name in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE                     # 招标公告
                elif type_name in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE                    # 中标公告
                elif type_name in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION                 # 招标变更
                elif type_name in self.list_alteration_category_num:
                    notice = const.TYPE_ZB_ABNORMAL                   # 招标异常
                elif type_name in self.list_win_advance_notice_num:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE            # 中标预告
                elif type_name in self.list_others_notice_num:
                    notice = const.TYPE_OTHERS_NOTICE                 # 其它公告
                else:
                    notice = 'null'
                if notice != 'null':
                    info_dict = self.r_dict | {'columnid': str(code)}
                    yield scrapy.FormRequest(url=self.base_url, formdata=info_dict, callback=self.parse_data_info,
                                         meta={'classifyShow': response.meta['classifyShow'], 'notice': notice,
                                               'info_dict': info_dict, 'code': code})
        except Exception as e:
            self.logger.error(f"发起数据请求失败  {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if response.status == 200:
                base_url = 'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
                if self.enable_incr:
                    if xmltodict.parse(response.text):
                        xmlparse = xmltodict.parse(response.text)
                        jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record'] or \
                                  json.loads(json.dumps(xmlparse))['datastore']['nextgroup']
                        num = 0
                        startrecord = 1
                        endrecord = 120
                        for info in jsonstr:
                            pub_time = ''.join(re.findall('<span>(.*)</span>', info)[0]).replace('[', '').replace(']', '')
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                num += 1
                                total = int(len(jsonstr))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            if num >= len(jsonstr):
                                startrecord += 120
                                endrecord += 120
                            else:
                                startrecord = 1
                                endrecord = 120
                            yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord), formdata=response.meta['info_dict'], dont_filter=True,
                                                     callback=self.parse_info,
                                                     meta={'notice': response.meta['notice'], 'classifyShow': response.meta['classifyShow']})
                else:
                    if response.xpath('//datastore/totalrecord/text()').get():
                        total = response.xpath('//datastore/totalrecord/text()').get()
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} ")
                        pages = math.ceil(int(total) / 120)
                        startrecord = 0
                        endrecord = 120
                        for num in range(1, int(pages) + 1):
                            if num == 1:
                                startrecord = 1
                                endrecord = 120
                            else:
                                startrecord += 120
                                endrecord += 120
                            yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord), formdata=response.meta['info_dict'],
                                             dont_filter=True, callback=self.parse_info, priority=10,
                                             meta={'notice': response.meta['notice'], 'classifyShow': response.meta['classifyShow']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误  {response.meta=} {e} {response.url=}")


    def parse_info(self, response):
        try:
            if response.status == 200:
                if xmltodict.parse(response.text):
                    xmlparse = xmltodict.parse(response.text)
                    jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record'] or \
                              json.loads(json.dumps(xmlparse))['datastore']['nextgroup']
                    for li in jsonstr:
                        put_time = re.findall('<span>(.*)</span>', li)[0]
                        title_name = re.findall('<a .*?>(.*)</a>', li)[0]
                        info_url = self.domain_url + "/" + re.findall("<a href='(.*)' title=.*?>", li)[0]
                        if re.search(r'候选人', title_name):                    # 中标预告
                            notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                        elif re.search(r'废标|流标', title_name):                # 招标异常
                            notice_type = const.TYPE_ZB_ABNORMAL
                        elif re.search(r'变更|答疑|澄清|补充|延期', title_name):   # 招标变更
                            notice_type = const.TYPE_ZB_ALTERATION
                        elif re.search(r'中标', title_name):                     # 中标公告
                            notice_type = const.TYPE_WIN_NOTICE
                        else:
                            notice_type = response.meta['notice']
                        yield scrapy.Request(url=info_url, callback=self.parse_item, priority=15,
                                             meta={'notice_type': notice_type, 'put_time': put_time, 'title_name': title_name,
                                                   'classifyShow': response.meta['classifyShow']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            notice_type = response.meta['notice_type']
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta['put_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//div[@class="content"]').get()
            files_path = {}

            if response.xpath("//div[@class='content']//a/@href"):
                str_content = response.xpath("//div[@class='content']//a")
                for con in str_content:
                    # 判断href 是否带 http头
                    if con.xpath('./@href').get():
                        if 'http' not in con.xpath('./@href').get():
                        # 判断href 是不是email
                            if con.xpath('./@href').get() not in re.findall('.*[a-zA-Z0-9]{0,19}@[a-zA-Z0-9].*', con.xpath('./@href').get()):
                                value = self.domain_url + con.xpath('./@href').get()
                                keys = con.xpath('.//text()').get()
                                files_path[keys] = value


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
            print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3315_keqiao_spider".split(" "))




