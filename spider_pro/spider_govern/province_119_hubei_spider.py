#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-16
# @Describe: 湖北省政府采购网

import datetime
import scrapy
import re, requests
import json, math
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_files, get_notice_type, \
     remove_specific_element, get_back_date

def get_cookie(url):
    cookie = {}
    res = requests.get(url=url)
    cookies = res.cookies
    cookie_dict = requests.utils.dict_from_cookiejar(cookies)
    coo = 'JSESSIONID' + '=' + cookie_dict['JSESSIONID']
    cookie['Cookie'] = coo
    return cookie

class Province119HubeiSpiderSpider(CrawlSpider):
    name = 'province_119_hubei_spider'
    allowed_domains = ['ccgp-hubei.gov.cn']
    base64_url = 'http://www.ccgp-hubei.gov.cn:8090/gpmispub/download?id='
    domain_url = 'http://www.ccgp-hubei.gov.cn:9040/quSer/initSearch'
    base_url = 'http://www.ccgp-hubei.gov.cn:9040/quSer/search'
    query_url = 'http://www.ccgp-hubei.gov.cn:9040/quSer/searchXmgg.html'
    area_id = "119"
    area_province = '湖北省政府采购网'

    # 招标预告
    list_tender_notice_num = {'需求公示（征询意见）': '5'}
    # 招标公告
    list_notice_category_name = {'招标公告（公开招标、邀请招标）': '1', '单一来源采购公示': '1',
                                 '竞争性谈判（竞争性磋商、询价采购）公告': '1'}
    # 招标变更
    list_zb_abnormal_name = {'更正公告': '2'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'中标（成交结果）公告': '7'}
    # 招标异常
    list_alteration_category_name = {'终止公告': '3'}
    # 资格预审
    list_qualifiction_advance_num = {'资格预审公告': '6'}
    # 其他
    list_qita_num = {}

    r_dict = {
        'queryInfo.type': 'xmgg',
        'queryInfo.key': '',
        'queryInfo.jhhh': '',
        'queryInfo.fbr': '',
        'queryInfo.gglx': '招标公告（公开招标、邀请招标）',
        'queryInfo.cglx': '',
        'queryInfo.cgfs': '',
        'queryInfo.city': '湖北省',
        'queryInfo.qybm': '42????',
        'queryInfo.district': '全省',
        'queryInfo.cgr': '',
        'queryInfo.begin': '2020/06/01',
        'queryInfo.end': '2021/08/16',
        'queryInfo.pageNo': '1',
        'queryInfo.pageSize': '50',
        'queryInfo.pageTotle': '',
    }

    custom_settings = {
        'COOKIES_ENABLED': False
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
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

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
            li_list = response.xpath('//form[@id="noticeForm"]/div[2]//select[@name="queryInfo.gglx"]/option')[1:]
            conut = 0
            for li in li_list:
                conut += 1
                notice_name = li.xpath('./@value').get()
                if notice_name in self.list_notice_category_name.keys():                      # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name.keys():                        # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_advance_notice_name.keys():                 # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif notice_name in self.list_win_notice_category_name.keys():                # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_tender_notice_num.keys():                       # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif notice_name in self.list_alteration_category_name.keys():                # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                elif notice_name in self.list_qualifiction_advance_num.keys():                # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif notice_name in self.list_qita_num.keys():                                # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    r_dict = time_dict | {'queryInfo.gglx': notice_name}
                    yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_info,
                                             dont_filter=True, formdata=r_dict, headers=get_cookie(self.domain_url),
                                             priority=(len(li_list) - conut)*5,
                                             meta={'r_dict': r_dict,
                                                   'notice': notice,
                                                   'cookie': get_cookie(self.domain_url)})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if response.text:
                    li_list = response.xpath('//ul[@class="serach-page-results list-unstyled"]/li')
                    num = 0
                    count = 0
                    for li in li_list:
                        count += 1
                        info_url = li.xpath('.//div[@class="title ellipsis"]/a/@href').get()
                        pub_time = li.xpath('.//div[@class="time"]/text()').get()
                        title_name = li.xpath('.//div[@class="title ellipsis"]/a/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 priority=(len(li_list)-count)*100,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(li_list)):
                            total = int(len(li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            pages = int(response.meta['r_dict']['queryInfo.pageNo']) + 1
                            r_dict = response.meta['r_dict'] | {'queryInfo.pageNo': str(pages)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_dict, headers=response.meta['cookie'],
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'r_dict': r_dict})
            else:
                if response.text:
                    total = ''.join(response.xpath('//div[@class="serach-page-state"]/p[1]/span[last()]/font/text()').get()).replace('“', "").replace('”', "")
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta['r_dict']} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total) / 50)
                    for num in range(1, int(pages) + 1):
                        new_dict = response.meta['r_dict'] | {'queryInfo.pageNo': str(num)}
                        yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_check,
                                                 headers=response.meta['cookie'], formdata=new_dict,
                                                 dont_filter=True, priority=(int(pages)-num)*10,
                                                 meta={'notice': response.meta['notice']})
                else:
                    print(response.meta['r_dict'])
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if response.text:
                count = 0
                li_list = response.xpath('//ul[@class="serach-page-results list-unstyled"]/li')
                for li in li_list:
                    count += 1
                    info_url = li.xpath('.//div[@class="title ellipsis"]/a/@href').get()
                    pub_time = li.xpath('.//div[@class="time"]/text()').get()
                    title_name = li.xpath('.//div[@class="title ellipsis"]/a/text()').get()
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(li_list)-count)*100,
                                         meta={'pub_time': pub_time,
                                               'title_name': title_name,
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = response.xpath('//div[@class="col-lg-12 col-sm-12 col-md-12 col-xs-12 no-padding"]').get()
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = response.meta['title_name']
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title  去除时间
                _, content = remove_specific_element(content, 'div', 'style', 'margin: 0 20px 30px;font-family:微软雅黑;')
                # 去除相关公告
                _, content = remove_specific_element(content, 'div', 'class', 'col-lg-12 col-sm-12 col-md-12 col-xs-12 margin-top-20')
                # 去除相关合同
                _, content = remove_specific_element(content, 'div', 'class', 'col-lg-12 col-sm-12 col-md-12 col-xs-12 margin-top-20 margin-bottom-30')
                keys_a = []
                files_text = etree.HTML(content)
                files_path = get_files(self.domain_url, origin, files_text, start_urls=self.base64_url, keys_a=keys_a)
                if not files_path:
                    # 去除相关下载
                    _, content = remove_specific_element(content, 'div', 'class', 'details-title')

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
    # cmdline.execute("scrapy crawl province_119_hubei_spider".split(" "))
    cmdline.execute("scrapy crawl province_119_hubei_spider -a sdt=2021-07-20 -a edt=2021-08-20".split(" "))