# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-19
# @Describe: 河北招财进宝 - 全量/增量脚本
import re
import math
import json
import lxml.html as LH
import requests
import scrapy
import random
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'province_71_zhaocaijingbao_spider'
    area_id = "71"
    domain_url = "http://hb.zcjb.com.cn"
    query_url = "http://hb.zcjb.com.cn/cms/index.htm"
    allowed_domains = ['hb.zcjb.com.cn']

    area_province = "河北-招财进宝"



    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公告', '成交公告', '公示公告']
    # 招标异常
    list_alteration_category_num = ['流标公告']
    # 招标变更
    list_zb_abnormal_num = ['变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 资格预审结果公告
    list_qualification_num = ['预审公告']
    # 其他公告
    list_others_notice_num = []

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_requets(self, url):
        html = requests.get(url=url).content.decode('utf-8')
        return html

    def start_requests(self):
        # all_url = 'http://hb.zcjb.com.cn/cms/channel/jsgczb/2100821.htm'
        # yield scrapy.Request(url=all_url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            url_all = response.xpath('//div[@class="left"]/div[@class="slideTxt slideBlock"]/div[1]/ul/li')[3:]
            for all in url_all:
                type_url = self.domain_url + all.xpath('./div/a/@href').get()
                type_name = all.xpath('./span/text()').get()
                if type_name in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE                     # 招标公告
                elif type_name in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE                    # 中标公告
                elif type_name in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION                 # 招标变更
                elif type_name in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE  # 资格预审
                elif type_name in self.list_alteration_category_num:
                    notice = const.TYPE_ZB_ABNORMAL                   # 招标异常
                elif type_name in self.list_win_advance_notice_num:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE            # 中标预告
                else:
                    notice = ''
                if notice:
                    if 'jsgc' in type_url:
                        classifyShow = '建设工程'
                    elif 'zfcg' in type_url:
                        classifyShow = '采购公告'
                    elif 'qycg' in type_url:
                        classifyShow = '企业采购'
                    else:
                        classifyShow = '土地使用权'

                    yield scrapy.Request(url=type_url, callback=self.parse_data_urls,
                                         meta={'classifyShow': classifyShow, 'notice': notice})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if response.xpath('//div[@class="pages"]/span[last()]/text()').get():
                if self.enable_incr:
                    page = 1
                    num = 0
                    data_list = response.xpath('//div[@class="infolist"]/div/ul/li')
                    for li in range(len(data_list)):
                        info_url = self.domain_url + ''.join(data_list[li].xpath('./a/@href').get()).replace('\n', '').replace('\t', '').replace('\r', '').strip()
                        info_source = data_list[li].xpath('./a//span[@class=" "]/text()').get() or ''
                        title_name = data_list[li].xpath('./a/@title').get()
                        pub_time = data_list[li].xpath('./a/em/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(data_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time, 'title_name': title_name,
                                                       'classifyShow': response.meta['classifyShow'],
                                                       'info_source': info_source}, priority=100)
                        if num >= len(data_list):
                            page += 1
                            r_dict = {'pageNo': str(num), 'city': '', 'bidType': '', 'timeType': ''}
                            yield scrapy.FormRequest(url=response.url, formdata=r_dict,
                                                     callback=self.parse_info, priority=50,
                                                     meta={'classifyShow': response.meta['classifyShow'],
                                                           'notice': response.meta['notice']})
                else:
                    pages = response.xpath('//div[@class="pages"]/span[last()]/text()').get()
                    total = int(pages) * 10
                    self.logger.info(f"本次获取总条数为：{total}")
                    for num in range(1, int(pages)+1):
                        r_dict = {'pageNo': str(num), 'city': '', 'bidType': '', 'timeType': ''}

                        yield scrapy.FormRequest(url=response.url, formdata=r_dict, callback=self.parse_info,
                                                     meta={'classifyShow': response.meta['classifyShow'],
                                                           'notice': response.meta['notice']}, priority=10)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            data_list = response.xpath('//div[@class="infolist"]/div/ul/li')
            for li in data_list:
                pub_time = li.xpath('./a/em/text()').get()
                title_name = li.xpath('./a/@title').get()
                info_url = self.domain_url + ''.join(li.xpath('./a/@href').get()).replace('\n', '').replace('\t', '').replace('\r', '').strip()
                info_source = li.xpath('./a//span[@class=" "]/text()').get() or ''

                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     meta={'notice': response.meta['notice'],
                                           'pub_time': pub_time, 'title_name': title_name,
                                           'classifyShow': response.meta['classifyShow'],
                                           'info_source': info_source}, priority=15)
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = response.meta['info_source']
            if info_source:
                info_source = self.area_province + response.meta['info_source']
            else:
                info_source = self.area_province

            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'资格预审', title_name):                       # 资格预审
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif re.search(r'候选人', title_name):                       # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'废标|流标', title_name):                    # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|答疑|澄清|补充|延期', title_name):      # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'中标', title_name):                         # 中标公告
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type = response.meta['notice']
            content = response.xpath('//div[@class="article-content"]').get()
            # 去除第一个广告
            pattern = re.compile(r'<a class="broadcast_flb_05".*?>(.*?)</a>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除title
            pattern = re.compile(r'<div class="article-title"*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除 发布时间
            pattern = re.compile(r'<div class="article-author"*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除最后一个广告
            pattern = re.compile(r'<div class="article-bottom"*?>(.*?)</a>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<div class="fileDownload"*?>(.*?)</table>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除隐藏表格
            pattern = re.compile(r'<h3>(.*?)</i>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            pattern = re.compile(r'<div class="modalBody">(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            list_name = ['本公告发布媒体', '发布媒介']
            for name in list_name:
                if name in content:
                    pattern = re.compile(fr'{name}[:|：].*?</p>', re.S)
                    content = content.replace(''.join(re.findall(pattern, content)), '')


            files_path = {}
            if response.xpath('//div[@id="filediv1"]'):
                str_content = response.xpath("//div[@id='filediv1']//a")
                for con in str_content:
                    if 'http' not in con.xpath('./@href'):
                        if con.xpath('./@href').get():
                            value = self.domain_url + con.xpath('./@href').get()
                            keys = con.xpath('.//text()').get()
                            files_path[keys] = value
                        else:
                            value = con.xpath('./@href').get()
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


            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_71_zhaocaijingbao_spider".split(" "))




