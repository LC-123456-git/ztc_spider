#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-11-01
# @Describe: 河北张家口交易平台
import copy
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
    get_files, get_notice_type, remove_specific_element, get_timestamp, remove_element_by_xpath
# TODO 产品未说 文件处不处理   文件名和文件链接均未带后缀

class Province158HeBeiZhangJiaKouSpider(CrawlSpider):
    name = 'province_158_hebeizhangjiakou_spider'
    allowed_domains = ['hbzjk.86ztb.com']
    start_urls = 'http://hbzjk.86ztb.com'
    domain_url = 'http://hbzjk.86ztb.com/finddata.htm'
    base_url = ''
    query_url = ''
    area_id = "158"
    area_province = '河北张家口交易平台'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=&property=&tendertype2=',
                                 'http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=fwwbzb&property=C&tendertype2=',
                                 'http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=hwcgzb&property=B&tendertype2=',
                                 'http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=gcxmzb&property=A&tendertype2=',
                                 ]
    # 招标变更
    list_zb_abnormal_name = ['http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=8&property=&tendertype2=']
    # 中标预告
    list_win_advance_notice_name = ['http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=32&property=&tendertype2=']
    # 中标公告
    list_win_notice_category_name = ['http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=3&property=&tendertype2=']
    # 招标异常
    list_alteration_category_name = ['http://hbzjk.86ztb.com/data.htm?systemtype=100&postmode=2&pf=hbzjk&tempId=31&property=&tendertype2=']
    # 资格预审
    list_qualifiction_advance_num = ['http://hbzjk.86ztb.com/data.htm?systemtype=2&postmode=2&pf=hbzjk&tempId=null']
    # 其他
    list_qita_num = []

    all_list = list_notice_category_name + list_zb_abnormal_name + list_win_advance_notice_name + \
               list_win_notice_category_name + list_alteration_category_name + list_qualifiction_advance_num

    r_dict = {'org.apache.struts.taglib.html.TOKEN': '', 'htm': 'dataList', 'postmode': '2', 'id': '0', 'ids': '',
              'ordername': 't.id', 'order': 'desc', 'isorder': 'no', 'tempordername': '', 'systemtype': '100',
              'findTemp': '', 'tempId': '', 'pf': 'hbzjk', 'indexid': '', 'indexid2': '0', 'tendertype2': '',
              'property': '', 'province': '', 'city': '', 'xian': '', 'opentype': '', 'fromday': '', 'endday': '',
              'findText': '名称', 'state': '1', 'pageSize': '0', 'currentPage': '1'}

    def __init__(self, *args, **kwargs):
        super(Province158HeBeiZhangJiaKouSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for data_url in self.all_list:
            if data_url in self.list_notice_category_name:
                notice_type = const.TYPE_ZB_NOTICE
            elif data_url in self.list_zb_abnormal_name:
                notice_type = const.TYPE_ZB_ALTERATION
            elif data_url in self.list_win_advance_notice_name:
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif data_url in self.list_win_notice_category_name:
                notice_type = const.TYPE_WIN_NOTICE
            elif data_url in self.list_alteration_category_name:
                notice_type = const.TYPE_ZB_ABNORMAL
            elif data_url in self.list_qualifiction_advance_num:
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = ''
            yield scrapy.Request(url=data_url, callback=self.parse_data,
                                 meta={'notice_type': notice_type})

    def parse_data(self, response):
        data_code = response.xpath('//form/div/input/@value').get()
        tempId = re.findall('tempId=(.*?)&', response.url)
        tempId = tempId[0] if tempId else ''
        property = re.findall('property=(.*?)&', response.url)
        property = property[0] if property else ''
        new_dict = self.r_dict | {'org.apache.struts.taglib.html.TOKEN': data_code} | \
                                 {'tempId': tempId} | {'property': property}

        yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_info,
                                 dont_filter=True, formdata=new_dict,
                                 meta={'notice_type': response.meta['notice_type'],
                                       'new_dict': copy.deepcopy(new_dict)})


    def parse_data_info(self, response):
        try:
            data_code = response.xpath('//form/div/input/@value').get()
            if self.enable_incr:
                count = 0
                num = 0
                info_data = response.xpath('//table[@class="table w100"]/tr[@class="middle"]')
                for info in info_data:
                    count += 1
                    title_name = info.xpath('./td[@class="autoline"]/a/@title').get()
                    pub_time = info.xpath('./td[last()]/text()').get()
                    info_url = info.xpath('./td/a/@onclick').get().replace("window.open(\'", '').replace("\');", '')
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                             priority=(len(info_data) - count) * 100,
                                             meta={'notice_type': response.meta['notice_type'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time})
                    if num >= int(len(info_data)):
                        total = int(len(info_data))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page = int(response.meta['new_dict']['currentPage']) + 1
                        new_dict = response.meta['new_dict'] | {'org.apache.struts.taglib.html.TOKEN': data_code} | \
                                                               {'currentPage': page} | {'fromday': self.sdt_time} | \
                                                               {'endday': self.edt_time}
                        yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_info, dont_filter=True,
                                                 meta={'notice_type': response.meta['notice_type'],
                                                       'new_dict': copy.deepcopy(new_dict)})
            else:
                total = re.findall('总计\s*(\d+?)\s*条', response.xpath('//div[@id="nulPages"]/text()').get())[0]
                pages = int(re.findall('共\s*(\d+?)\s*页', response.xpath('//div[@id="nulPages"]/text()').get())[0])
                self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                count = 0
                for page in range(1, pages + 1):
                    count += 1
                    new_dict = response.meta['new_dict'] | {'org.apache.struts.taglib.html.TOKEN': data_code} | \
                                                           {'currentPage': str(page)}
                    yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_check, formdata=new_dict,
                                             priority=((pages + 1) - count) * 50, dont_filter=True,
                                             meta={'notice_type': response.meta['notice_type']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')


    def parse_data_check(self, response):
        try:
            info_data = response.xpath('//table[@class="table w100"]/tr[@class="middle"]')
            count = 0
            for info in info_data:
                count += 1
                title_name = info.xpath('./td[@class="autoline"]/a/@title').get()
                pub_time = info.xpath('./td[last()]/text()').get()
                info_url = info.xpath('./td/a/@onclick').get().replace("window.open(\'", '').replace("\');", '')
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=(len(info_data) - count) * 100,
                                     meta={'notice_type': response.meta['notice_type'],
                                           'title_name': title_name,
                                           'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            category = ''
            origin = response.url
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            content = response.xpath('//table[@id="p3"]').get()
            _, content = remove_element_by_xpath(content, '//table/tbody/tr[1]/td/div[contains(string(),"创建时间")]')
            _, content = remove_element_by_xpath(content, '//table/tbody/tr[1]/td/div[@id="noprint"][contains(string(),"打印")]')
            _, content = remove_element_by_xpath(content, '//table/tbody/tr[1]/td/ul/li[contains(string(),"服务范围")]')

            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice_type'])
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                                       keys_a=keys_a, log=self.logger)

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
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_item {e}')


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_158_hebeizhangjiakou_spider".split(" "))
    cmdline.execute("scrapy crawl province_158_hebeizhangjiakou_spider -a sdt=2021-10-01 -a edt=2021-11-30".split(" "))
