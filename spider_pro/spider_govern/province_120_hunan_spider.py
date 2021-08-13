#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-09
# @Describe: 湖南省政府采购网

import datetime
import scrapy
import re
import json, math
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_files, get_notice_type, \
    remove_specific_element, get_back_date, remove_element_by_xpath


class Province119HubeiSpiderSpider(CrawlSpider):
    name = 'province_120_hunan_spider'
    allowed_domains = ['ccgp-hunan.gov.cn']
    start_urls = 'http://www.ccgp-hunan.gov.cn'
    domain_url = 'http://www.ccgp-hunan.gov.cn/page/notice/more.jsp?prcmMode=06#'
    base_url = 'http://www.ccgp-hunan.gov.cn/mvc/getNoticeList4Web.do'
    query_url = 'http://www.ccgp-hunan.gov.cn/mvc/viewNoticeContent.do?noticeId={}&area_id='
    area_id = "120"
    area_province = '湖南省政府采购网'

    # 招标预告
    list_tender_notice_num = {}
    # 招标公告
    list_notice_category_name = {'采购公告': 'prcmNotices'}
    # 招标变更
    list_zb_abnormal_name = {"更正公告": 'modfiyNotices'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'中标(成交)公告': 'dealNotices'}
    # 招标异常
    list_alteration_category_name = {'终止公告': 'endNotices', '废标公告': 'invalidNotices'}
    # 资格预审
    list_qualifiction_advance_num = {}
    # 其他
    list_qita_num = {'其他公告': 'otherNotices', '合同公告': 'contractNotices'}

    r_dict = {
        'nType': 'prcmNotices',
        'pType': '',
        'prcmPrjName': '',
        'prcmItemCode': '',
        'prcmOrgName': '',
        'startDate': '2021-01-01',
        'endDate': '2021-08-08',
        'prcmPlanNo': '',
        'page': '1',
        'pageSize': '100',
    }

    def __init__(self, *args, **kwargs):
        super(Province119HubeiSpiderSpider, self).__init__()
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
                time_dict = self.r_dict | {'startDate': startDate} | {'endDate': endDate}
            else:
                endDate = datetime.datetime.now().strftime("%Y-%m-%d")
                startDate = get_back_date(365)
                time_dict = self.r_dict | {'startDate': startDate} | {'endDate': endDate}
            li_list = response.xpath('//div[@class="mian_left_nei"]/div')[3:10]
            for li in li_list:
                notice_list = []
                notice_name = li.xpath('./a/text()').get()
                if notice_name in self.list_notice_category_name.keys():                 # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                    notice_list.append(self.list_notice_category_name[notice_name])
                elif notice_name in self.list_zb_abnormal_name.keys():                    # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                    notice_list.append(self.list_zb_abnormal_name[notice_name])
                elif notice_name in self.list_win_advance_notice_name.keys():             # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                    notice_list.append(self.list_win_advance_notice_name[notice_name])
                elif notice_name in self.list_win_notice_category_name.keys():            # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                    notice_list.append(self.list_win_notice_category_name[notice_name])
                elif notice_name in self.list_tender_notice_num.keys():                    # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                    notice_list.append(self.list_tender_notice_num[notice_name])
                elif notice_name in self.list_alteration_category_name.keys():             # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                    notice_list.append(self.list_alteration_category_name[notice_name])
                elif notice_name in self.list_qualifiction_advance_num.keys():              # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    notice_list.append(self.list_qualifiction_advance_num[notice_name])
                elif notice_name in self.list_qita_num.keys():                              # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                    notice_list.append(self.list_qita_num[notice_name])
                else:
                    notice = ''
                if notice:
                    for value in notice_list:
                        r_dict = time_dict | {'nType': value}
                        yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_info,
                                                 dont_filter=True, formdata=r_dict,
                                                 meta={'r_dict': r_dict,
                                                       'notice': notice})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if json.loads(response.text):
                    data_info = json.loads(response.text)['rows']
                    num = 0
                    for info in data_info:
                        pub_time = info['NEWWORK_DATE']
                        info_url = self.query_url.format(info['NOTICE_ID'])
                        title_name = info['NOTICE_TITLE']
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(data_info)):
                            total = int(len(data_info))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            pages = int(response.meta['r_dict']['page']) + 1
                            r_dict = response.meta['r_dict'] | {'page': str(pages)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_dict,
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'r_dict': r_dict})
            else:
                if json.loads(response.text):
                    total = json.loads(response.text)['total']
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta['r_dict']} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total) / 100)
                    for num in range(1, int(pages) + 1):
                        new_dict = response.meta['r_dict'] | {'page': str(num)}
                        yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_check,
                                                 formdata=new_dict, dont_filter=True, priority=(int(pages)-num)*10,
                                                 meta={'notice': response.meta['notice']})
                else:
                    print(response.meta['r_dict'])
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if json.loads(response.text):
                data_info = json.loads(response.text)['rows']
                for info in data_info:
                    pub_time = info['NEWWORK_DATE']
                    info_url = self.query_url.format(info['NOTICE_ID'])
                    title_name = info['NOTICE_TITLE']
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                         meta={'pub_time': pub_time,
                                               'title_name': title_name,
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = response.text
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = response.meta['title_name']
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title
                # 去除时间
                if 'class="danyi_title"' in content:
                    _, content = remove_specific_element(content, 'p', 'class', 'danyi_title')
                elif 'style="text-align:center;"' in content:
                    _, content = remove_specific_element(content, 'h2')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@style="text-align:center;margin-top:15px;" and contains(text(), "公告日期") or contains(text(), "公告时间")]')
                else:
                    _, content = remove_specific_element(content, 'h1')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@style="text-align:center;margin-top:10px;" and contains(text(), "公告日期") or contains(text(), "公告时间")]')

                _, content = remove_element_by_xpath(content, xpath_rule='//td[@align="center" and contains(text(), "公告日期") or contains(text(), "公告时间")]')
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
    # cmdline.execute("scrapy crawl province_120_hunan_spider".split(" "))
    cmdline.execute("scrapy crawl province_120_hunan_spider -a sdt=2021-07-20 -a edt=2021-08-15".split(" "))