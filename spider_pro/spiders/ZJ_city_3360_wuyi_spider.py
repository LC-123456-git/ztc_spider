#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-02
# @Describe: 浙江省金华市武义县人民政府 - 全量/增量脚本

import re
import math
import json
import scrapy
import xmltodict
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
                             remove_specific_element, get_files, get_notice_type


class MySpider(CrawlSpider):
    name = 'ZJ_city_3360_wuyi_spider'
    area_id = "3360"
    domain_url = "http://www.zjwy.gov.cn"
    query_url = "http://www.zjwy.gov.cn/col/col1229150614/index.html"
    base_url = 'http://www.zjwy.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['zjwy.gov.cn']
    area_province = '浙江省金华市武义县人民政府'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['招标公告', '询价公告', '竞价公告']
    # 招标变更
    list_zb_abnormal_name = ['变更通知', '补充说明']
    # 中标预告
    list_win_advance_notice_name = ['中标候选人公示', '中标公示']
    # 中标公告
    list_win_notice_category_name = ['中标结果公告', '询价成交公告', '成交公示']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = ['资格预审公告']
    # 其他
    list_qita_num = ['开标结果公示']

    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '3558',
        'path': '/',
        # 'columnid': '1229425304',
        'sourceContentType': '1',
        'unitid': '6208573',
        'webname': '武义县人民政府',
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
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="lm_02 bot"]/h3')
            for li in li_list:
                category = li.xpath('./span/text()').get()
                notice_li_list = li.xpath('./ul/li')
                count = 0
                for notice_li in notice_li_list:
                    if notice_li.xpath('./a'):
                        count += 1
                        notice_url = notice_li.xpath('./a/@href').get()
                        notice_name = notice_li.xpath('./a/text()').get()
                        li_code = re.findall('(\d+)', notice_url)[0]
                        if notice_name in self.list_tender_notice_num:           # 招标预告
                            notice = const.TYPE_ZB_ADVANCE_NOTICE
                        elif notice_name in self.list_notice_category_name:      # 招标公告
                            notice = const.TYPE_ZB_NOTICE
                        elif notice_name in self.list_zb_abnormal_name:          # 招标变更
                            notice = const.TYPE_ZB_ALTERATION
                        elif notice_name in self.list_win_advance_notice_name:   # 中标预告
                            notice = const.TYPE_WIN_ADVANCE_NOTICE
                        elif notice_name in self.list_win_notice_category_name:  # 中标公告
                            notice = const.TYPE_WIN_NOTICE
                        elif notice_name in self.list_qita_num:                  # 其他
                            notice = const.TYPE_OTHERS_NOTICE
                        else:
                            notice = ''
                        if notice:
                            info_dict = self.r_dict | {'columnid': str(li_code)}
                            yield scrapy.FormRequest(url=self.base_url.format(1, 120), callback=self.parse_data_info,
                                                     formdata=info_dict, priority=(len(notice_li_list)-count)*2,
                                                     meta={'category': category,
                                                           'notice': notice,
                                                           'info_dict': info_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            startrecord = 1
            endrecord = 120
            if self.enable_incr:
                if xmltodict.parse(response.text):
                    xmlparse = xmltodict.parse(response.text)
                    jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
                    num = 0
                    for info in jsonstr:
                        pub_time = ''.join(re.findall("<span.*>(.*)</span>", info)).strip()
                        info_url = self.domain_url + re.findall("<a .*? href='(.*?)' .*>", info)[0]
                        title_name = re.findall("<a .* title='(.*?)'>", info)[0]
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                                 meta={'category': response.meta['category'],
                                                       'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(jsonstr)):
                            total = int(len(jsonstr))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            startrecord = int(re.findall('startrecord=(\d+?)&', response.url)[0])
                            endrecord = int(re.findall('endrecord=(\d+?)&', response.url)[0])
                            startrecord += 120
                            endrecord += 120
                            yield scrapy.Request(url=self.base_url.format(startrecord, endrecord),
                                                 callback=self.parse_data_info, dont_filter=True,
                                                 meta={'category': response.meta['category'],
                                                       'notice': response.meta['notice']})
            else:
                if response.xpath('//datastore/totalrecord/text()').get():
                    total = response.xpath('//datastore/totalrecord/text()').get()
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total)/120)
                    count = 0
                    for num in range(1, int(pages) + 1):
                        count += 1
                        if num == 1:
                            startrecord = 1
                            endrecord = 120
                        else:
                            startrecord += 120
                            endrecord += 120
                        yield scrapy.FormRequest(url=self.base_url.format(startrecord, endrecord),
                                                 formdata=response.meta['info_dict'], priority=(int(pages)-count)*5,
                                                 callback=self.parse_data_check, dont_filter=True,
                                                 meta={'notice': response.meta['notice'],
                                                       'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data_info {e} {response.meta['info_dict']}")

    def parse_data_check(self, response):
        try:
            if xmltodict.parse(response.text):
                xmlparse = xmltodict.parse(response.text)
                jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
                count = 0
                for info in jsonstr:
                    count += 1
                    pub_time = ''.join(re.findall("<span.*>(.*)</span>", info)).strip()
                    info_url = self.domain_url + re.findall("<a .*? href='(.*?)' .*?>", info)[0]
                    title_name = re.findall("<a .* title='(.*?)'>", info)[0]
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(jsonstr)-count)*2,
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
                    content = response.xpath('//div[@class="con_wen"]').get()
                    # 尾部多余
                    _, content = remove_specific_element(content, 'meta', 'name', 'ContentEnd')
                    # 去除 底部 script
                    _, content = remove_specific_element(content, 'script', 'language', 'javascript')
                    # # 去除a 下面的img
                    pattern = re.compile(r'<a .*?>(<img .*?>)', re.S)
                    con_num = len(re.findall(pattern, content))
                    for n in range(con_num):
                        content = content.replace(re.findall(pattern, content)[con_num - 1 - n], '')
                        if n == con_num - 1:
                            break
                    files_text = etree.HTML(content)
                    keys_a = []
                    files_path = get_files(self.domain_url, origin, files_text, keys_a=keys_a)

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
    cmdline.execute("scrapy crawl ZJ_city_3360_wuyi_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3360_wuyi_spider -a sdt=2021-07-01 -a edt=2021-08-30".split(" "))


