# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-10
# @Describe: 浙江临海市公告资源交易中心 - 全量/增量脚本

import re, ast, requests
import math
import json
import scrapy
import random
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval
from sqlalchemy import create_engine
from lxml import etree

class MySpider(CrawlSpider):
    name = 'ZJ_city_3321_linhai_spider'
    area_id = "3321"
    domain_url = "http://www.linhai.gov.cn"
    query_url = "http://www.linhai.gov.cn/ggzyjy/"
    base_url = 'http://ggzyjy.linhai.gov.cn/dahai/viewmore1.aspx?PrjTypeId={}'
    base_domain_url = 'http://ggzyjy.linhai.gov.cn/dahai/'
    base_query_url = 'http://ggzyjy.linhai.gov.cn'
    allowed_domains = ['www.linhai.gov.cn']
    area_province = "浙江临海市公告资源交易中心"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }



    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告', '信息披露']
    # 招标预告
    list_notice_tender_num = ['招标文件公示']
    # 中标公告
    list_win_notice_category_num = ['中标结果', '成交公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ['澄清或修改', '补充通知']
    # 中标预告
    list_win_advance_notice_num = ['中标公示', '预成交公示']
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = ['合同公告', '履约公告', '意见征询']


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="cont"]/ul/li')
            for li in li_list:
                classifyShow = li.xpath('./a/text()').get()
                if classifyShow in '工程建设':
                    num = '01'
                    info_url = self.base_url.format(num)
                elif classifyShow in '政府采购':
                    num = '02'
                    info_url = self.base_url.format(num)
                elif classifyShow in '土地交易':
                    num = '03'
                    info_url = self.base_url.format(num)
                elif classifyShow in '产权交易（拓展资源）':
                    num = '04'
                    info_url = self.base_url.format(num)
                elif classifyShow in '自行招标':
                    num = '05'
                    info_url = self.base_url.format(num)
                else:
                    num = ''
                    info_url = self.base_url.format(num)

                yield scrapy.Request(url=info_url, callback=self.parse_data_urls, dont_filter=True,
                                     meta={'classifyShow': classifyShow})
        except Exception as e:
            self.logger.error(f"parse_urls: 发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            div_list = response.xpath('//td[@width="220"]//a')
            for div in div_list:
                type_url = self.base_domain_url + div.xpath('./@href').get()
                type_name = ''.join(div.xpath('./text()').get()).strip()
                if type_name in self.list_notice_tender_num:           # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif type_name in self.list_win_advance_notice_num:    # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_name in self.list_zb_abnormal_num:           # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif type_name in self.list_win_notice_category_num:   # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif type_name in self.list_notice_category_num:       # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif type_name in self.list_others_notice_num:         # 其他公告
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    yield scrapy.Request(url=type_url, callback=self.parse_data_info, priority=10, dont_filter=True,
                                         meta={'classifyShow': response.meta['classifyShow'],
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f"parse_data_urls: 发起数据请求失败 {e} {response.url=}")


    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 1
                li_list = response.xpath('//td[@align="center"]/table')
                for li in range(len(li_list)):
                    pub_time = ''.join(li_list[li].xpath('./tr[1]/td[last()]/text()').get()).strip()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    info_url = response.url + '&pageindex={}'
                    if num >= len(li_list):
                        pn += 1
                    else:
                        pn = 1
                    yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info, priority=100, dont_filter=True,
                                         meta={'notice': response.meta['notice'],
                                               'classifyShow': response.meta['classifyShow']})
            else:
                total = re.findall('共(\d+)条记录', response.xpath('//span[@id="Label1"]/div/text()').get())[0]
                pages = re.findall('共(\d+)页', response.xpath('//span[@id="Label1"]/div/text()').get())[0]
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(1, int(pages)+1):
                    info_url = response.url + '&pageindex={}'.format(num)
                    yield scrapy.Request(url=info_url, callback=self.parse_info, priority=100, dont_filter=True,
                                         meta={'classifyShow': response.meta['classifyShow'],
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"parse_data_info:初始总页数提取错误 {response.meta=} {e} {response.url=}")



    def parse_info(self, response):
        try:
            li_list = response.xpath('//td[@align="center"]/table/tr[1]')
            for li in li_list:
                info_url = self.base_query_url + li.xpath('./td[2]/a/@href').get()
                info_title = ''.join(li.xpath('./td[2]/a/text()').get()).strip()
                pub_time = ''.join(li.xpath('./td[last()]/text()').get()).strip()
                if re.search(r"变更|答疑|澄清|补充|延期", info_title):
                    notice_type = const.TYPE_ZB_ALTERATION       # 招标变更
                elif re.search(r"废标|流标", info_title):
                    notice_type = const.TYPE_ZB_ABNORMAL         # 招标异常
                elif re.search(r"候选人|预成交", info_title):
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE  # 中标预告
                elif re.search(r"中标|成交|出让结果|交易结果", info_title):
                    notice_type = const.TYPE_WIN_NOTICE          # 中标公告
                else:
                    notice_type = response.meta['notice']
                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150, dont_filter=True,
                                     meta={'classifyShow': response.meta['classifyShow'],
                                     'info_title': info_title, 'notice_type': notice_type,
                                     'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")



    def parse_item(self, response):
        try:
            if response.status == 200:
                pub_time = response.meta['pub_time']
                pub_time = get_accurate_pub_time(pub_time)
                origin = response.url
                info_source = self.area_province
                title_name = response.meta['info_title']
                classifyShow = response.meta['classifyShow']
                notice_type = response.meta['notice_type']


                content = response.xpath('//td[@id="RightPane"]').get()
                # 去除 带头的导航栏
                pattern = re.compile(r'<div style="padding-left:20px;".*?>(.*?)</div>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 横线
                pattern = re.compile(r'<div (class="gradientLine line1".*?)></div>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 title
                pattern = re.compile(r'<div class="title1".*?>(.*?)</div>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 前面的表格
                pattern = re.compile(r'<tr id="FlowChartContent">(.*?)<!-- 表格内容结束 -->', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 标题表格
                pattern = re.compile(r'<table id="Table3".*?>(.*?)</table>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 二维码
                pattern = re.compile(r'<img (id="_ctl3_Image1".*?)>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                # 去除 网上异议投诉
                content = content.replace('网上异议投诉', '')

                files_path = {}
                file_content = etree.HTML(content)
                if file_content.xpath('//tr[@class="GridView6RowStyle"]/td/a/@href'):
                    con_list = file_content.xpath('//tr[@class="GridView6RowStyle"]')
                    for con in con_list:
                        if con.xpath('./td[last()]/a/@href'):
                            if 'http' not in con.xpath('./td[last()]/a/@href')[0]:
                                value = 'http://ggzyjy.linhai.gov.cn/dhqlc/Framework/Main/' + con.xpath('./td[last()]/a/@href')[0]
                            else:
                                value = con.xpath('./td[last()]/a/@href')[0]
                            key = con.xpath('./td[1]/text()')[0]
                            files_path[key] = value
                if content:
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

                    yield notice_item

        except Exception as e:
            print(e, response.url)


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3321_linhai_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3321_linhai_spider -a sdt=2021-03-19 -a edt=2021-05-10".split(" "))


