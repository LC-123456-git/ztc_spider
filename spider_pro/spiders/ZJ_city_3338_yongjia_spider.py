#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-14
# @Describe: 浙江省温州市永嘉县人民政府 - 全量/增量脚本

import re
import math
import json
import requests
import scrapy, ast
import random
import urllib
import datetime
from lxml import etree
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
                            remove_specific_element, get_files, get_notice_type


class MySpider(CrawlSpider):
    name = 'ZJ_city_3338_yongjia_spider'
    area_id = "3338"
    domain_url = "http://ggzy.yj.gov.cn:7088"
    query_url = "http://ggzy.yj.gov.cn:7088/yjcms"
    allowed_domains = ['ggzy.yj.gov.cn']
    area_province = '浙江省温州市永嘉县人民政府'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['招标公告', '招标文件公示', '采购公告', '出让公告']
    # 招标变更
    list_zb_abnormal_name = ["答疑补充", "补充公告"]
    # 中标预告
    list_win_advance_notice_name = ['候选公示']
    # 中标公告
    list_win_notice_category_name = ['中标结果', '出让结果', '中标公告']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = ['预审结果']
    # 其他
    list_qita_num = ['保证金退付', '开标记录']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_url(self, strst_url, cid, num):
        cid_url = "{}/attachment_url.jspx?cid={}&n={}".format(strst_url, cid, num)
        response = requests.get(url=cid_url, headers=self.headers).content.decode('utf-8')
        return response

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="Tab-Main FloatL Hidden"]/div[@class="Head1"]')
            for li in li_list:
                category = li.xpath('./h4/text()').get()
                li_url = self.domain_url + li.xpath('./div/a/@href').get()
                yield scrapy.Request(url=li_url, callback=self.parse_data_urls,
                                     meta={'category': category})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="Tab-Main FloatL Hidden"]/div[@class="Head1"]')
            for li in li_list:
                notice_name = ''.join(li.xpath('./h4/text()').get()).strip()
                li_url = self.domain_url + li.xpath('./div/a/@href').get()
                if notice_name in self.list_notice_category_name:           # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:             # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_advance_notice_name:      # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif notice_name in self.list_win_notice_category_name:     # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_qualifiction_advance_num:     # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif notice_name in self.list_qita_num:                     # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    li_url = li_url.replace(''.join(li_url).split('/')[-1], 'index_1.htm')
                    yield scrapy.Request(url=li_url, callback=self.parse_data_info,
                                         meta={'category': response.meta['category'],
                                               'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            info_url = response.url.replace(''.join(response.url).split('/')[-1], 'index_{}.htm')
            if self.enable_incr:
                li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
                num = 0
                for info_num in range(len(li_list)):
                    _url = self.domain_url + li_list[info_num].xpath('./a/@href').get()
                    title_name = li_list[info_num].xpath('./a/@title').get()
                    pub_time = ''.join(li_list[info_num].xpath('./span/text()').get()).strip()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        yield scrapy.Request(url=_url, callback=self.parse_item,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice'],
                                                   'pub_time': pub_time,
                                                   'title_name': title_name})
                    if num >= int(len(li_list)):
                        page_num = int(re.findall('\w\_(\d+)\.\w', response.url[response.url.rindex('/') + 1:])[0])
                        page_num += 1
                        yield scrapy.Request(url=info_url.format(page_num),
                                             callback=self.parse_data_info, dont_filter=True,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice']})

            else:
                pages = re.findall('\/(\d+)页', response.xpath('//div[@class="Zy-Page FloatL"]/div/text()').get())[0]
                total = re.findall('共(\d+)条', response.xpath('//div[@class="Zy-Page FloatL"]/div/text()').get())[0]
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_data_check,
                                         meta={'category': response.meta['category'],
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
            for info in li_list:
                info_url = self.domain_url + info.xpath('./a/@href').get()
                title_name = info.xpath('./a/@title').get()
                pub_time = ''.join(info.xpath('./span/text()').get()).strip()
                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                     meta={'category': response.meta['category'],
                                           'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'title_name': title_name})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            category = response.meta['category']
            info_source = self.area_province
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                if notice_type:
                    content = response.xpath('//div[@class="Content-Main FloatL"]').get()
                    # 去除 title
                    _, content = remove_specific_element(content, 'span', 'class', 'Bold')
                    # 去除 info source
                    pattern = re.compile('(<em>.*?</em>)', re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')
                    # 去除 多于链接
                    _, content = remove_specific_element(content, 'blockquote', 'style', 'display: none;')
                    _, content = remove_specific_element(content, 'blockquote', 'style', 'display: none; font-size: 13px;')

                    files_path = {}
                    key_name = 'pdf/img/doc'
                    keys_list = ['前往报名', 'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
                                 'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF', 'png',
                                 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG', 'ZJYQCF', 'YQZBX']
                    files_text = etree.HTML(content)
                    # 处理 文件 files_path
                    table_all_list = files_text.xpath('//div[@class="Content-Main FloatL"]//table')
                    table_list = files_text.xpath('//div[@class="Content-Main FloatL"]/table')
                    cid = re.findall('(\d+)', origin[origin.rindex('/') + 1:])[0]
                    for table_num in range(len(table_list)):
                        table_text = table_list[table_num].xpath('./tr//text()')
                        if '相关下载文件' in table_text:
                            file_list = table_list[table_num].xpath('./tr')[1:]
                            values = ast.literal_eval(self.get_url(self.query_url, cid, int(len(file_list))))
                            for file_num in range(len(file_list)):
                                # 通过第三方请求 获得files_path的路径
                                value = "{}/attachment.jspx?cid={}&i={}".format(self.query_url, cid, file_num) + values[file_num]
                                keys = ''.join(file_list[file_num].xpath('./td[1]/a/@title')[0]).strip()
                                files_path[keys] = value
                                content = ''.join(content).replace('<a title="{}">{}</a>'.format(keys, keys), '<p title="{}">{}</p>'.format(keys, keys))
                                content = ''.join(content).replace('<a id="attach{}" title="文件下载">'.format(file_num),  '<a id="attach{}" title="文件下载" href="{}">'.format(file_num, value))
                        else:
                            nums = len(table_all_list) - len(table_list)
                            if table_num == 0:
                                num = nums + 1
                            elif (int(len(table_list)) - 1) - table_num == 0:
                                num = table_num
                            else:
                                num = (int(len(table_list)) - 1) - table_num
                            _, content = remove_specific_element(content, 'table', index=num)

                    # 处理正文img
                    if files_text.xpath('//img/@src'):
                        files_list = files_text.xpath('//img')
                        for con in files_list:
                            values = con.xpath('./@src')[0]
                            if 'http:' not in values:
                                value = self.domain_url + values
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
                    notice_item["category"] = category

                    yield notice_item

if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3338_yongjia_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3338_yongjia_spider -a sdt=2021-04-01 -a edt=2021-07-16".split(" "))


