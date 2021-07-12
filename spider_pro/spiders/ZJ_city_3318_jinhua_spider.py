# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-26
# @Describe: 金华市公共资源交易中心 - 全量/增量脚本
import ast
import re
import math
import json

import requests
import scrapy
import random
import datetime
from urllib import parse

from lxml import etree
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval, get_url


class MySpider(CrawlSpider):
    name = 'ZJ_city_3318_jinhua_spider'
    area_id = "3318"
    domain_url = "http://ggzyjy.jinhua.gov.cn"
    query_url = "http://ggzyjy.jinhua.gov.cn"
    allowed_domains = ['ggzyjy.jinhua.gov.cn']
    area_province = "浙江-金华市公共资源交易中心"


    # 招标公告
    list_notice_category_num = ['招标公告', '采购公告', '采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公示', '采购结果公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ['补充文件']
    # 中标预告
    list_win_advance_notice_num = ['中标公示', '评标公示', '评标结果公示']
    # 资格预审结果公告
    list_qualification_num = ['预审结果']
    # 其他公告
    list_others_notice_num = []

    url_list = [
                'http://ggzyjy.jinhua.gov.cn/cms/gcjy/index.htm',
                'http://ggzyjy.jinhua.gov.cn/cms/zfcg/index.htm',
                'http://ggzyjy.jinhua.gov.cn/cms/cqjy/index.htm'
                ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
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
        for url in self.url_list:
            if 'gcjy' in url:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/gcjy/index.htm'
                classifyShow = '建设工程'
            elif 'zfcg' in url:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/zfcg/index.htm'
                classifyShow = '政府采购'
            else:
                type_url = 'http://ggzyjy.jinhua.gov.cn/cms/cqjy/index.htm'
                classifyShow = '产权交易'
            yield scrapy.Request(url=type_url, callback=self.parse_urls, meta={'classifyShow': classifyShow})

    def parse_urls(self, response):
        try:
            list_li = response.xpath('//div[@class="ListBorder floatL"]//a')
            type_list_name = ['省重点工程', '市本级工程', '金华山工程', '金义都工程', '小额工程', '公开招标']
            for li in list_li:
                if li.xpath('./text()').get() not in type_list_name:
                    type_url = self.domain_url + li.xpath('./@href').get()
                    type_name = li.xpath('./text()').get()
                    if type_name in self.list_qualification_num:                 # 资格预审
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif type_name in self.list_win_advance_notice_num:          # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif type_name in self.list_zb_abnormal_num:                 # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif type_name in self.list_win_notice_category_num:         # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif type_name in self.list_notice_category_num:             # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=type_url, callback=self.parse_info,
                                             meta={'classifyShow': response.meta['classifyShow'], 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_info(self, response):
        try:
            if self.enable_incr:
                num = 0
                data_list = response.xpath('//div[@class="Right-Border floatL"]/dl/dt')
                for li in range(len(data_list)):
                    info_url = self.domain_url + data_list[li].xpath('./a/@href').get()
                    pub_time = ''.join(data_list[li].xpath('./span/text()').get()).replace('[', '').replace(']', '')
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                             meta={'notice': response.meta['notice'],
                                                   'pub_time': pub_time,
                                                   'classifyShow': response.meta['classifyShow']})
                    if num >= 20:
                        total = int(len(data_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数2u0l;"
                                         f"提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page = re.findall('(.*?)\.\w+', response.url[response.url.rindex('/') + 1:])[0]
                        if page == 'index':
                            page = 2
                        else:
                            page = int(re.findall('\w+\_(\d+)', page)[0]) + 1
                        info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'.format(page)
                        yield scrapy.Request(url=info_url, callback=self.parse_info,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'notice': response.meta['notice']})
            else:
                page_str = response.xpath('//div[@class="Page-bg floatL"]/div/text()').get()
                pages = ''.join(re.findall('.*\d\/(\d+)', page_str))
                total = ''.join(re.findall('共(\d+)条', page_str))
                self.logger.info(f"本次获取总条数为：{total}")
                info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.jhtml'
                for num in range(1, int(pages)+1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_data_info, priority=100,
                                         meta={'classifyShow': response.meta['classifyShow'],
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            data_list = response.xpath('//div[@class="Right-Border floatL"]/dl/dt')
            for li in data_list:
                pub_time = ''.join(li.xpath('./span/text()').get()).replace('[', '').replace(']', '')
                info_url = self.domain_url + li.xpath('./a/@href').get()
                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                     meta={'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'classifyShow': response.meta['classifyShow']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            classifyShow = response.meta.get("classifyShow")
            title_name = response.xpath('//div[@class="content-Border floatL"]/font/text()').extract_first()
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'候选人', title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'废标|流标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|答疑|澄清|补充|延期', title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'预审结果', title_name):  # 资格预审
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']
            content = response.xpath('//div[@class="Main-p floatL"]').get()
            files_path = {}
            key_name = 'pdf/img/doc'
            keys_list = ['前往报名', 'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
                         'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF', 'png',
                         'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG', 'ZJYQCF', 'YQZBX']
            files_text = etree.HTML(content)
            # 处理 文件 files_path
            table_list = files_text.xpath('//div[@class="Main-p floatL"]/table')
            cid = re.findall('(\d+)', origin[origin.rindex('/') + 1:])[0]
            for table_num in table_list:
                table_text = table_num.xpath('./tr//text()')
                if '相关下载文件' in table_text:
                    file_list = table_num.xpath('./tr')[1:]
                    value_list = get_url(self.domain_url, cid, len(file_list))
                    for file_num in range(len(file_list)):
                        # 通过第三方请求 获得files_path的路径
                        value = "{}/attachment.jspx?cid={}&i={}".format(self.query_url, cid, file_num) + value_list[file_num]
                        keys = ''.join(file_list[file_num].xpath('./td[1]/a/@title')[0]).strip()
                        files_path[keys] = value
                        content = ''.join(content).replace('<a id="attach{}" title="文件下载">'.format(file_num),
                                                           '<a id="attach{}" title="文件下载" href="{}">'.format(file_num, value))
                else:
                    pattern = re.compile('({}.*?</table>)'.format(''.join(table_text[:2]).strip()), re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')
            # 处理正文img
            if files_text.xpath('//img/@src'):
                files_list = files_text.xpath('//img')
                for con in files_list:
                    values = con.xpath('./@src')[0]
                    if 'http:' not in values:
                        value = self.query_url + values
                    else:
                        value = values
                    if value[value.rindex('.') + 1:] in keys_list:
                        key = key_name + value[value.rindex('.'):]
                    else:
                        key = key_name + '.jpg'
                    files_path[key] = value

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
    cmdline.execute("scrapy crawl ZJ_city_3318_jinhua_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3318_jinhua_spider -a sdt=2021-04-01 -a edt=2021-07-12".split(" "))




