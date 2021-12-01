#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-24
# @Describe: 内蒙古政府采购网

import datetime
from collections import OrderedDict

import scrapy
import re, requests
import json, math
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const, constans
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
    get_files, get_notice_type, get_back_date, remove_specific_element, remove_element_by_xpath


class Province127NeiMengGuSpiderSpider(CrawlSpider):
    name = 'province_127_neimenggu_spider'
    allowed_domains = ['ccgp-neimenggu.gov.cn']
    start_url = 'http://www.ccgp-neimenggu.gov.cn/'
    domain_url = 'http://www.ccgp-neimenggu.gov.cn/category/cgggg'
    base_url = 'http://www.ccgp-neimenggu.gov.cn/zfcgwslave/web/index.php?r=pro%2Fanndata'
    query_url = 'http://www.ccgp-neimenggu.gov.cn/category/cgggg?tb_id={}&p_id={}&type={}'
    area_id = "127"
    area_province = '内蒙古政府采购网'

    # 招标预告
    list_tender_notice_num = {}
    # 招标公告
    list_notice_category_name = {'招标公告': '1'}
    # 招标变更
    list_zb_abnormal_name = {'招标更正公告': '2', '中标(成交)更正公告': '4', '资格预审更正公告': '7'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'中标(成交)公告': '3'}
    # 招标异常
    list_alteration_category_name = {'废标公告': '5'}
    # 资格预审
    list_qualifiction_advance_num = {'资格预审公告': '6'}
    # 其他
    list_qita_num = {}

    r_dict = {
        'type_name': '7',
        'purmet': '',
        'keyword': '',
        'annstartdate_S': '',
        'annstartdate_E': '',
        'annenddate_S': '',
        'annenddate_E': '',
        'byf_page': '1',
        'fun': 'cggg',
        'page_size': '50'
    }
    keywords_map = OrderedDict({
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    })

    def match_title(self, title_name):
        """
        根据标题匹配关键字 返回招标类别
        Args:
            title_name: 标题

        Returns:
            notice_type: 招标类别
        """
        matched = False
        notice_type = ''
        for keywords, value in self.keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def __init__(self, *args, **kwargs):
        super(Province127NeiMengGuSpiderSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            if self.enable_incr:
                startDate = self.sdt_time
                endDate = self.edt_time
                time_dict = self.r_dict | {'annstartdate_S': startDate} | {'annstartdate_E': endDate}
            else:
                endDate = datetime.datetime.now().strftime("%Y-%m-%d")
                startDate = get_back_date(365)
                time_dict = self.r_dict | {'annstartdate_S': startDate} | {'annstartdate_E': endDate}
            li_list = response.xpath('//div[@class="fast-nav-2"]//ul[@class="spread-item fast-nav-list fast-nav-list-2 mt mb"]/li')
            conut = 0
            for li in li_list:
                conut += 1
                notice_name = li.xpath('./a/text()').get()
                if notice_name in self.list_notice_category_name.keys():             # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                    notice_value = self.list_notice_category_name[notice_name]
                elif notice_name in self.list_zb_abnormal_name.keys():               # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                    notice_value = self.list_zb_abnormal_name[notice_name]
                elif notice_name in self.list_win_advance_notice_name.keys():        # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                    notice_value = self.list_win_advance_notice_name[notice_name]
                elif notice_name in self.list_win_notice_category_name.keys():       # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                    notice_value = self.list_win_notice_category_name[notice_name]
                elif notice_name in self.list_tender_notice_num.keys():              # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                    notice_value = self.list_tender_notice_num[notice_name]
                elif notice_name in self.list_alteration_category_name.keys():       # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                    notice_value = self.list_alteration_category_name[notice_name]
                elif notice_name in self.list_qualifiction_advance_num.keys():       # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    notice_value = self.list_qualifiction_advance_num[notice_name]
                elif notice_name in self.list_qita_num.keys():                       # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                    notice_value = self.list_qita_num[notice_name]
                else:
                    notice = ''
                    notice_value = ''
                if notice:
                    r_dict = time_dict | {'type_name': notice_value}
                    yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_info,
                                             dont_filter=True, formdata=r_dict,
                                             priority=(len(li_list) - conut) * 5,
                                             meta={'r_dict': r_dict,
                                                   'notice': notice,
                                                   })
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if json.loads(response.text):
                    info_data = json.loads(response.text)
                    num = 0
                    count = 0
                    for data in info_data[0]:
                        count += 1
                        info_url = self.query_url.format(data['ay_table_tag'], data['wp_mark_id'], data['type'])
                        pub_time = get_accurate_pub_time(data['SUBDATE'])
                        title_name = data['TITLE']
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 priority=(len(info_data[0]) - count) * 100,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(info_data[0])):
                            total = int(len(info_data[0]))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            pages = int(response.meta['r_dict']['byf_page']) + 1
                            r_dict = response.meta['r_dict'] | {'byf_page': str(pages)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_dict,
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'r_dict': r_dict})
            else:
                if json.loads(response.text):
                    info_data = json.loads(response.text)
                    total = info_data[1]
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta['r_dict']} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total) / 50)
                    for num in range(1, int(pages) + 1):
                        new_dict = response.meta['r_dict'] | {'byf_page': str(num)}
                        yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_check, formdata=new_dict,
                                                 dont_filter=True, priority=(int(pages) - num) * 10,
                                                 meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if json.loads(response.text):
                count = 0
                info_data = json.loads(response.text)
                for data in info_data[0]:
                    count += 1
                    info_url = self.query_url.format(data['ay_table_tag'], data['wp_mark_id'], data['type'])
                    pub_time = get_accurate_pub_time(data['SUBDATE'])
                    title_name = data['TITLE']
                    yield scrapy.Request(url=info_url, callback=self.parse_item,
                                         priority=(len(info_data[0]) - count) * 100,
                                         meta={'pub_time': pub_time,
                                               'title_name': title_name,
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = response.xpath('//div[@class="content-box-1"]').get()
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = response.meta['title_name']
        pub_time = response.meta['pub_time']
        notice_type_ori = response.meta['notice']
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_types = match_notice_type

            notice_type = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_types, constans.TYPE_NOTICE_DICT))[0]
        else:
            notice_type = notice_type_ori
        if '测试' not in title_name:
            if notice_type and content:
                # pattern = re.compile(r'<div style="border: 1px solid .*?>(.*?)<h4>', re.S)
                # content = content.replace(re.findall(pattern, content)[0], '')
                keys_a = []
                files_text = etree.HTML(content)
                files_path = get_files(self.domain_url, origin, files_text, start_urls=self.start_url,
                                       pub_time=pub_time, keys_a=keys_a)

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

    cmdline.execute("scrapy crawl province_127_neimenggu_spider".split(" "))
    # cmdline.execute("scrapy crawl province_127_neimenggu_spider -a sdt=2021-07-20 -a edt=2021-11-20".split(" "))
