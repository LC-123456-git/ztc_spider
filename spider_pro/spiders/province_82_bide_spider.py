#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-06-08
# @Describe: 比德电子采购平台 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import urllib
import datetime
from lxml import etree
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element, get_files


class MySpider(CrawlSpider):
    name = 'province_82_bide_spider'
    area_id = "82"
    domain_url = "http://www.bdebid.com"
    query_url = "https://www.bdebid.com/EpointWebBuilder5_1/rest/commonSearch/getInfoList"
    base_url = ''
    allowed_domains = ['bdebid.com']
    area_province = '比德电子采购平台'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_num = ['采购公告']
    # 招标变更
    list_zb_abnormal_num = ['变更公告']
    # 中标预告
    list_win_advance_notice_num = ['候选人公示']
    # 中标公告
    list_win_notice_category_num = ['采购结果公示']
    # 招标异常
    list_alteration_category_num = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []

    category_code_list = ['003001', '003002', '003003', '003004']

    category_name_list = ['采购公告', '变更公告', '候选人公示', '采购结果公示']

    city_code_list = ['110000', '120000', '130000', '140000', '150000', '210000', '220000', '230000', '310000',
                 '320000', '330000', '340000', '350000', '360000', '370000', '410000', '420000', '430000',
                 '440000', '450000', '460000', '500000', '510000', '520000', '530000', '540000', '610000',
                 '620000', '630000', '640000', '650000']

    city_name_list = ['北京', '天津', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林', '黑龙江', '上海市',
                 '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省',
                 '广东省', '广西', '海南省', '重庆市', '四川省', '贵州省', '云南省', '西藏', '陕西省',
                 '甘肃省', '青海省', '宁夏', '新疆']

    data = {'params': '{"categorynum":"003001","title":"","datetime":"","codearea":"110000","hangye":"","pageIndex":0,"pageSize":17}'}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for code in range(len(self.category_code_list)):
            category = self.category_name_list[code]
            for num in range(len(self.city_code_list)):
                city_name = self.city_name_list[num]
                _data = json.loads(self.data['params']) | {'categorynum': self.category_code_list[code]} | {'codearea': self.city_code_list[num]}
                data_dict = self.data | {'params': json.dumps(_data)}
                # format里面的0为第一页
                yield scrapy.FormRequest(url=self.query_url, formdata=data_dict, dont_filter=True,
                                         callback=self.parse_data, priority=100,
                                         meta={'category': category, 'city_name': city_name, 'data_dict': data_dict})

    def parse_data(self, response):
        try:
            if json.loads(response.text)['Totle'] != 0:
                data_info = json.loads(response.text)
                category_name = response.meta['category']
                if category_name in self.list_notice_category_num:            # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif category_name in self.list_zb_abnormal_num:              # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif category_name in self.list_win_advance_notice_num:       # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif category_name in self.list_win_notice_category_num:      # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                else:
                    notice = ''
                if notice:
                    if self.enable_incr:
                        page = 0
                        data_list = data_info['infodata']
                        nums = 0
                        for li in range(len(data_list)):
                            pub_time = data_list[li]['infodate']
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                nums += 1
                                total = int(len(data_list))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            if nums >= len(data_list):
                                page += 1
                                data = json.loads(response.meta['data_dict']['params']) | {'pageIndex': page}
                                info_data_dict = response.meta['data_dict'] | {'params': json.dumps(data)}
                            else:
                                page = 0
                                info_data_dict = response.meta['data_dict']
                            yield scrapy.FormRequest(url=self.query_url, callback=self.parse_data_info, priority=100,
                                                     formdata=info_data_dict, dont_filter=True,
                                                     meta={'notice': notice,
                                                           'city_name': response.meta['city_name']})
                    else:
                        total = data_info['Totle']
                        RowCount = data_info['RowCount']
                        self.logger.info(f"本次获取总条数为：{total}")
                        pages = math.ceil(int(total)/RowCount)
                        for page in range(1, pages):
                            data = json.loads(response.meta['data_dict']['params']) | {'pageIndex': page}
                            info_data_dict = response.meta['data_dict'] | {'params': json.dumps(data)}
                            yield scrapy.FormRequest(url=self.query_url, callback=self.parse_data_info, priority=100,
                                                     formdata=info_data_dict, dont_filter=True,
                                                     meta={'notice': notice,
                                                           'city_name': response.meta['city_name']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if json.loads(response.text)['infodata']:
                data_list = json.loads(response.text)['infodata']
                for data in data_list:
                    title_name = data['title2']
                    info_url = self.domain_url + data['infourl']
                    pub_time = data['infodate']

                    if re.search(r'资格审查', title_name):                         # 资格审查
                        notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif re.search(r'变更|更正|澄清|补充|取消|延期', title_name):   # 招标变更
                        notice_type = const.TYPE_ZB_ALTERATION
                    elif re.search(r'终止|中止|废标|流标', title_name):             # 招标异常
                        notice_type = const.TYPE_ZB_ABNORMAL
                    else:
                        notice_type = response.meta['notice']
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                         meta={'notice_type': notice_type,
                                               'pub_time': pub_time,
                                               'title_name': title_name,
                                               'city_name': response.meta['city_name']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_urls {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source =response.meta['city_name'] + self.area_province
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            notice_type = response.meta['notice_type']
            pub_time = get_accurate_pub_time(pub_time)

            content = response.xpath('//div[@class="ewb-list-main"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'div', 'class', 'ewb-trade-title')
            # 去除 info 时间栏目
            _, content = remove_specific_element(content, 'div', 'class', 'ewb-article-sources')

            files_path = get_files(self.domain_url, content)

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

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_82_bide_spider".split(" "))
    # cmdline.execute("scrapy crawl province_82_bide_spider -a sdt=2021-05-18 -a edt=2021-06-09".split(" "))








