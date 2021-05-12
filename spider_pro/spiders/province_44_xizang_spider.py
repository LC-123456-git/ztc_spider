# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-07
# @Describe: 西藏自治区公共资源交易信息网 - 全量/增量脚本
import re
import math
import json

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
    name = 'province_44_xizang_spider'
    area_id = "44"
    domain_url = "http://www.xzggzy.gov.cn:9090"
    query_url = "http://www.xzggzy.gov.cn:9090/gcjs/index.jhtml"
    allowed_domains = ['xzggzy.gov.cn']
    area_province = "西藏"

    # 招标公告
    list_notice_category_num = ["http://www.xzggzy.gov.cn:9090/zbzsgg/index.jhtml",
                                'http://www.xzggzy.gov.cn:9090/cjgs/index.jhtml',
                                'http://www.xzggzy.gov.cn:9090/kyq/index.jhtml',
                                'http://www.xzggzy.gov.cn:9090/qtfscrxx/index.jhtml',
                                'http://www.xzggzy.gov.cn:9090/gpjg/index.jhtml',
                                'http://www.xzggzy.gov.cn:9090/cggg/index.jhtml',
                                'http://www.xzggzy.gov.cn:9090/yx/index.jhtml']
    # 中标公告
    list_win_notice_category_num = ["http://www.xzggzy.gov.cn:9090/jyjggg/index.jhtml",
                                    'http://www.xzggzy.gov.cn:9090/jyjg/index.jhtml',
                                    'http://www.xzggzy.gov.cn:9090/zbgg/index.jhtml',
                                    'http://www.xzggzy.gov.cn:9090/zpgcrjg/index.jhtml',
                                    'http://www.xzggzy.gov.cn:9090/jggs/index.jhtml']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ['http://www.xzggzy.gov.cn:9090/gzsx/index.jhtml']
    # 中标预告
    list_win_advance_notice_num = []
    # 资格预审结果公告
    list_qualification_num = ['http://www.xzggzy.gov.cn:9090/zgysjg/index.jhtml']
    # 其他公告
    list_others_notice_num = ['http://www.xzggzy.gov.cn:9090/zbwjcq/index_2.jhtml',
                              'http://www.xzggzy.gov.cn:9090/zrbqyxx/index.jhtml',
                              'http://www.xzggzy.gov.cn:9090/zrbgdxx/index.jhtml']
    mimetypes = ['application/msword', 'application/pdf', 'application/vnd.ms-excel',
                 'application/zip', 'text/xml', 'application/octet-stream']


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_url(self, url):
        res = requests.get(url=url).headers.get('content-type')
        return res
    def start_requests(self):
        # ll_url = 'http://www.xzggzy.gov.cn:9090/zbzsgg/1307184.jhtml'
        # ll_url = 'http://www.xzggzy.gov.cn:9090/cjgs/1285440.jhtml'
        # yield scrapy.Request(url=ll_url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_data)

    def parse_data(self, response):
        li_list = response.xpath('//div[@class="jyxxcontent-old"]/ul/li[1]/ul/li')
        for li in li_list:
            urls = li.xpath('./a/@href').get()
            classifyShow = li.xpath('./a/text()').get()
            yield scrapy.Request(url=urls,  callback=self.parse_urls,
                                 meta={'classifyShow': classifyShow})

    def parse_urls(self, response):
        try:
            url_all = response.xpath('//div[@class="jyxxcontent-old"]/ul/li[2]/ul/li')
            for all in url_all:
                type_url = all.xpath('./a/@href').get()
                if type_url in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE                    # 招标公告
                elif type_url in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE                    # 中标公告
                elif type_url in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION                 # 招标变更
                elif type_url in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE  # 资格预审
                elif type_url in self.list_others_notice_num:
                    notice = const.TYPE_OTHERS_NOTICE                 # 其他公告
                else:
                    notice = 'null'
                yield scrapy.Request(url=type_url, callback=self.parse_data_urls,
                                     meta={'notice': notice, 'classifyShow': response.meta['classifyShow']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if response.xpath('//div[@class="pages"]/ul/li[1]/a/text()').get():
                if self.enable_incr:
                    page = 1
                    num = 1
                    li_list = response.xpath('//div[@class="article-content-old"]/ul/li')
                    for li in range(len(li_list)):
                        pub_time = li_list[li].xpath('./div/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        if li >= num:
                            page += 1
                        else:
                            page = 1
                        data_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                        yield scrapy.Request(url=data_url.format(num), callback=self.parse_info,
                                             meta={'notice': response.meta['notice'], 'classifyShow': response.meta['classifyShow']})
                else:
                    pages = re.findall('\/(\d+)', response.xpath('//div[@class="pages"]/ul/li[1]/a/text()').get())[0]
                    total = re.findall('共(\d+)条', response.xpath('//div[@class="pages"]/ul/li[1]/a/text()').get())[0]
                    self.logger.info(f"本次获取总条数为：{total}")
                    data_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                    for num in range(1, int(pages)):
                        yield scrapy.Request(url=data_url.format(num), callback=self.parse_info,
                                                 meta={'notice': response.meta['notice'], 'classifyShow': response.meta['classifyShow']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            data_list = response.xpath('//div[@class="article-content-old"]/ul/li')
            for li in data_list:
                put_time = li.xpath('./div/text()').get()
                title_name = li.xpath('./a/@title').get()
                info_url = li.xpath('./a/@href').get()
                if response.meta['notice'] != "null":
                    if re.search(r'资格预审', title_name):
                        notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif re.search(r'候选人', title_name):
                        notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                    elif re.search(r'终止|中止|异常|废标|流标', title_name):
                        notice_type = const.TYPE_ZB_ABNORMAL
                    elif re.search(r'变更|更正|澄清', title_name):
                        notice_type = const.TYPE_ZB_ALTERATION
                    else:
                        notice_type = response.meta['notice']
                    yield scrapy.Request(url=info_url, callback=self.parse_item,
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
            # content = response.xpath("//div[@class='div-content']").get()
            content = response.xpath("//div[@class='div-article2']").get()
            # 去除title
            pattern = re.compile(r'<div class="div-title".*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            # 去除发布时间
            pattern = re.compile(r'<div class="div-title2".*?>(.*?)</div>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')
            content = re.sub(' 分享到：', '', content)

            files_path = {}

            value_list = ['http://www.creditchina.gov.cn', 'http://www.ccgp.gov.cn', 'https://baike.so.com/create/edit/?eid=4795154&sid=5011264',
                          'http://www.qichacha.com/firm_ad1609d9ecb71e090b1ee06395714cc2.html', 'http://www.creditchina.gov.cn）中列入失信被执行人和/',
                          'http://www.ccgp.gov.cn）等渠道查询2017', 'http://www.rkzw.cn/', 'https://wenshu.court.gov.cn/', 'http://www.jiathis.com/share',
                          'http://www.ccgp/', 'http://wwww.lsggzy.cn/', 'http://www.xzzbtb.gov.cn/', 'http://www.ccgp-xizang.gov.cn', 'http://www.ccgp/']
            keys_list = ['原文链接地址', 'http://ggzy.lasa.gov.cn', '国家企业信用信息公示系统', '财务会计制度', '社会保障资金', '普查报告', 'www.creditchina.gov.cn',
                         '社会保障资金的良好记录（提供承诺函）；', 'www.gsxt.gov.cn', '国家企业信用', 'www.ccgp.gov.cn']
            if response.xpath("//div[@class='div-content']//a"):
                str_content = response.xpath("//div[@class='div-content']//a")
                for con in str_content:
                    if con.xpath('./@href').get() and con.xpath('./@href').get() not in value_list:
                        if 'http' in con.xpath('./@href').get():
                            value = con.xpath('./@href').get()
                            if con.xpath('.//text()').get() not in keys_list:
                                keys = con.xpath('.//text()').get()
                                files_path[keys] = value

                        else:
                            value = self.domain_url + con.xpath('./@href').get()
                            if con.xpath('.//text()').get() not in keys_list:
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
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_44_xizang_spider".split(" "))

