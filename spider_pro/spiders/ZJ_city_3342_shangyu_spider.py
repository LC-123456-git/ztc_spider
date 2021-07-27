#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-22
# @Describe: 浙江省绍兴市上虞区人民政府 - 全量/增量脚本

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
    name = 'ZJ_city_3342_shangyu_spider'
    area_id = "3342"
    domain_url = "http://xxgk.shangyu.gov.cn"
    query_url = "http://xxgk.shangyu.gov.cn/col/col1228984905/index.html"
    base_url = 'http://xxgk.shangyu.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['xxgk.shangyu.gov.cn']
    area_province = '浙江省绍兴市上虞区人民政府'

    # 招标预告
    list_tender_notice_num = ['采购意向', '采购要素公示']
    # 招标公告
    list_notice_category_name = ['招标公告', '文件公示', '采购公告', '交易公告']
    # 招标变更
    list_zb_abnormal_name = ["答疑补充"]
    # 中标预告
    list_win_advance_notice_name = ['中标公示']
    # 中标公告
    list_win_notice_category_name = ['结果公告']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['合同公告']

    category_construction_code = ['/col/col1228987920/index.html', '/col/col1228987928/index.html',
                                  '/col/col1228987941/index.html', '/col/col1228987950/index.html']
    category_purchase_code = ['/col/col1228987952/index.html', '/col/col1228987953/index.html',
                              '/col/col1228987960/index.html']
    category_property_code = ['/col/col1228987961/index.html', '/col/col1228987962/index.html',
                              '/col/col1228987963/index.html']
    category_stateowned_code = ['/col/col1229104035/index.html']

    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '2328',
        'path': '/',
        # 'columnid': '1518855',
        'sourceContentType': '1',
        'unitid': '5476089',
        'webname': '上虞区人民政府门户网站 政府信息公开',
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
            li_list = response.xpath('//div[@class="clearfix"]/div')
            for li in li_list:
                category = li.xpath('.//div[@class="ewb-com-box"]//span/text()').get()
                list_url = li.xpath('.//div[@class="tabview"]/div//ul[@class="clearfix"]/li')
                for _list in list_url:
                    li_url = _list.xpath('./a/@href').get()
                    if li_url in self.category_construction_code:
                        category = '建设工程'
                    elif li_url in self.category_purchase_code:
                        category = '采购项目'
                    elif li_url in self.category_property_code:
                        category = '产权交易'
                    elif li_url in self.category_stateowned_code:
                        category = '国企采购'
                    else:
                        category = category
                    if li_url:
                        li_code = re.findall('(\d+)', li_url)[0]
                        notice_name = _list.xpath('./a/text()').get()
                        if notice_name in self.list_tender_notice_num:           # 招标预告
                            notice = const.TYPE_ZB_ADVANCE_NOTICE
                        elif notice_name in self.list_notice_category_name:      # 招标公告
                            notice = const.TYPE_ZB_NOTICE
                        elif notice_name in self.list_zb_abnormal_name:          # 招标变更
                            notice = const.TYPE_WIN_NOTICE
                        elif notice_name in self.list_win_advance_notice_name:   # 中标预告
                            notice = const.TYPE_ZB_ABNORMAL
                        elif notice_name in self.list_win_notice_category_name:  # 中标公告
                            notice = const.TYPE_WIN_ADVANCE_NOTICE
                        elif notice_name in self.list_qita_num:                  # 其他
                            notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                        else:
                            notice = ''
                        if notice:
                            info_dict = self.r_dict | {'columnid': str(li_code)}
                            yield scrapy.FormRequest(url=self.base_url.format(1, 120), formdata=info_dict,
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'category': category,
                                                           'notice': notice,
                                                           'info_dict': info_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            startrecord = 1
            endrecord = 120
            if self.enable_incr:
                xmlparse = xmltodict.parse(response.text)
                jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
                num = 0
                for info_num in range(len(jsonstr)):
                    pub_time = re.findall('<span .*>(.*)</span>', jsonstr[info_num])[0]
                    info_url = self.domain_url + re.findall('<a href="(.*?)" .*>', jsonstr[info_num])[0]
                    title_name = re.findall('<a .* title="(.*?)">', jsonstr[info_num])[0]
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
                total = response.xpath('//datastore/totalrecord/text()').get()
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                pages = math.ceil(int(total)/120)
                for num in range(1, int(pages) + 1):
                    if num == 1:
                        startrecord = 1
                        endrecord = 120
                    else:
                        startrecord += 120
                        endrecord += 120
                    yield scrapy.FormRequest(url=self.base_url.format(startrecord, endrecord),
                                             formdata=response.meta['info_dict'],
                                             callback=self.parse_data_check, dont_filter=True,
                                             meta={'notice': response.meta['notice'],
                                                   'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            xmlparse = xmltodict.parse(response.text)
            jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
            for info in jsonstr:
                pub_time = re.findall('<span .*>(.*?)</span>', info)[0]
                info_url = self.domain_url + re.findall('<a href="(.*?)" .*>', info)[0]
                title_name = re.findall('<a .* title="(.*?)">', info)[0]
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
                    content = response.xpath('//div[@class="main-bd clearfix"]').get()
                    # 去除 导航栏
                    _, content = remove_specific_element(content, 'div', 'class', 'bt-note-30')

                    _, content = remove_specific_element(content, 'style', 'type', 'text/css')
                    # 去除 info source
                    _, content = remove_specific_element(content, 'div', 'class', 'art_title')

                    # 去除 多于链接
                    _, content = remove_specific_element(content, 'div', 'class', 'bt-clear')
                    _, content = remove_specific_element(content, 'div', 'class', 'bt_xx')

                    files_text = etree.HTML(content)
                    keys_a = []
                    files_path = get_files(self.domain_url, origin, files_text, pub_time, keys_a=keys_a)

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
    # cmdline.execute("scrapy crawl ZJ_city_3342_shangyu_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3342_shangyu_spider -a sdt=2021-06-20 -a edt=2021-07-23".split(" "))


