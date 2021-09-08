#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-09-08 修改
# @Describe: 比德电子采购平台 - 全量/增量脚本

import re
import math
import json
import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
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

    data = {'params': '{"categorynum":"003001","title":"","datetime":"","codearea":"110000","hangye":"","pageIndex":"0","pageSize":"50"}'}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_category(self, category):
        if category in self.list_notice_category_num:  # 招标公告
            notice = const.TYPE_ZB_NOTICE
        elif category in self.list_zb_abnormal_num:  # 招标变更
            notice = const.TYPE_ZB_ALTERATION
        elif category in self.list_win_advance_notice_num:  # 中标预告
            notice = const.TYPE_WIN_ADVANCE_NOTICE
        elif category in self.list_win_notice_category_num:  # 中标公告
            notice = const.TYPE_WIN_NOTICE
        else:
            notice = ''
        return notice

    def start_requests(self):

        for code in range(len(self.category_code_list)):
            category = self.category_name_list[code]
            notice = self.get_category(category)
            for num in range(len(self.city_code_list)):
                city_name = self.city_name_list[num]
                _data = json.loads(self.data['params']) | {'categorynum': self.category_code_list[code]} | {'codearea': self.city_code_list[num]}
                data_dict = self.data | {'params': json.dumps(_data)}
                # format里面的0为第一页
                yield scrapy.FormRequest(url=self.query_url, formdata=data_dict, dont_filter=True,
                                         callback=self.parse_data, priority=100,
                                         meta={'notice': notice,
                                               'city_name': city_name,
                                               'category': category,
                                               'data_dict': data_dict})

    def parse_data(self, response):
        try:
            if json.loads(response.text)['Totle'] != 0:
                data_info = json.loads(response.text)
                if self.enable_incr:
                    page = 0
                    data_list = data_info['infodata']
                    nums = 0
                    for li in range(len(data_list)):
                        title_name = data_list[li]['title2']
                        info_url = self.domain_url + data_list[li]['infourl']
                        pub_time = data_list[li]['infodate']
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 meta={'pub_time': pub_time,
                                                       'title_name': title_name,
                                                       'city_name': response.meta['city_name'],
                                                       'notice': response.meta['notice'],
                                                       'category': response.meta['category']})

                        total = int(len(data_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        if nums >= len(data_list):
                            page += 1
                            data = json.loads(response.meta['data_dict']['params']) | {'pageIndex': str(page)}
                            info_data_dict = response.meta['data_dict'] | {'params': json.dumps(data)}
                            yield scrapy.FormRequest(url=self.query_url, callback=self.parse_data,
                                                     priority=100,
                                                     formdata=info_data_dict, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'city_name': response.meta['city_name'],
                                                           'category': response.meta['category']})
                else:
                    total = data_info['Totle']
                    RowCount = data_info['RowCount']
                    self.logger.info(f"本次获取总条数为：{total}")
                    pages = math.ceil(int(total)/RowCount)
                    count = 0
                    for page in range(1, pages):
                        count += 1
                        data = json.loads(response.meta['data_dict']['params']) | {'pageIndex': str(page)}
                        info_data_dict = response.meta['data_dict'] | {'params': json.dumps(data)}
                        yield scrapy.FormRequest(url=self.query_url, callback=self.parse_data_info,
                                                 priority=((pages+1)-count)*50,
                                                 formdata=info_data_dict, dont_filter=True,
                                                 meta={'notice': response.meta['notice'],
                                                       'city_name': response.meta['city_name'],
                                                       'category': response.meta['category']})
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
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                         meta={'notice': response.meta['notice'],
                                               'pub_time': pub_time,
                                               'title_name': title_name,
                                               'city_name': response.meta['city_name'],
                                               'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_urls {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source =response.meta['city_name'] + self.area_province
            title_name = response.meta['title_name']
            category = response.meta['category']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'资格审查', title_name):  # 资格审查
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif re.search(r'变更|更正|澄清|补充|取消|延期', title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'终止|中止|废标|流标', title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = response.meta['notice']
            content = response.xpath('//div[@class="ewb-list-main"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'div', 'class', 'ewb-trade-title')
            # 去除 info 时间栏目
            _, content = remove_specific_element(content, 'div', 'class', 'ewb-article-sources')

            files_text = etree.HTML(content)
            keys_a = []
            files_path = get_files(self.domain_url, origin, files_text, pub_time=pub_time, keys_a=keys_a)

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
    # cmdline.execute("scrapy crawl province_82_bide_spider".split(" "))
    cmdline.execute("scrapy crawl province_82_bide_spider -a sdt=2021-09-01 -a edt=2021-10-09".split(" "))








