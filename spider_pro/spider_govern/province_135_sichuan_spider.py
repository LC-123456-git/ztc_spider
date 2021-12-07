#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-10-12
# @Describe: 四川省政府采购网
import json, copy
import scrapy, re, math, requests
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
     get_files, get_notice_type, remove_specific_element, get_timestamp


class Province135SiChuanSpider(CrawlSpider):
    name = 'province_135_sichuan_spider'
    allowed_domains = ['ccgp-sichuan.gov.cn']
    start_urls = 'http://www.ccgp-sichuan.gov.cn'
    domain_url = 'http://202.61.88.152:9002'
    base_url = ''
    query_url = 'http://www.ccgp-sichuan.gov.cn/CmsNewsController.do?method=search&years=2018&chnlNames={}&chnlCodes={}&title=&tenderno=&agentname=&buyername=&startTime={}&endTime={}&distin_like=510000&province=510000&city=&town=&provinceText=\u56db\u5ddd\u7701&cityText=\u8BF7\u9009\u62E9&townText=\u8BF7\u9009\u62E9&pageSize=10&curPage={}&searchResultForm=search_result_anhui.ftl'
    area_id = "135"
    area_province = '四川省政府采购网'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'spider_pro.middlewares.VerificationMiddleware.VerificationMiddleware': 120,
        },
        'ENABLE_PROXY_USE': False,
        'ENABLE_URL_DUP_REMOVE_USE': False,
    }

    # 招标预告
    list_tender_notice_name = {}
    # 招标公告
    list_notice_category_name = {'公开招标采购公告': '8a817ecb39b9902a0139b9a2dfaf0b4b',
                                 '邀请招标采购公告': '8a817ecb39b9902a0139b9a22bc00b47',
                                 '询价采购公告': '8a817ecb39b9902a0139b9a5d8ea0b53',
                                 '竞争性谈判采购公告': '8a817ecb39b9902a0139b9a541e90b4f',
                                 '竞争性磋商采购公告': '402886875355b06e01539d135c5a3b0e',
                                 '单一来源采购公告': '8a817ecb39b9902a0139b9a72aed0b57',
                                 '竞价采购公告': '99997ecb39b9902a0139b9a72aed0b57'}
    # 招标变更
    list_zb_abnormal_name = {"更正公告": "8a817ecb39add7c40139ae0c09001012"}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'中标公告': '8a817ecb39add7c40139ae0b9b43100e',
                                     '成交公告': '8a817ecb39add7c40139ae0b9b43166',
                                     '竞价成交公告': '88887ecb39b9902a0139b9a72aed0b57'}
    # 招标异常
    list_alteration_category_name = {}
    # 资格预审
    list_qualifiction_advance_num = {}
    # 其他
    list_qita_num = {}

    list_dict = {**list_notice_category_name, **list_zb_abnormal_name, **list_win_notice_category_name}

    def __init__(self, *args, **kwargs):
        super(Province135SiChuanSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        curPage = 1
        if self.enable_incr:
            sdt_time = self.sdt_time
            edt_time = self.edt_time
        else:
            sdt_time = ''
            edt_time = ''
        for key, value in zip(self.list_dict.keys(), self.list_dict.values()):
            start_url = self.query_url.format(key, value, sdt_time, edt_time, curPage)
            if key in self.list_notice_category_name.keys():  # 招标公告
                notice = const.TYPE_ZB_NOTICE
            elif key in self.list_zb_abnormal_name:           # 招标变更
                notice = const.TYPE_ZB_ALTERATION
            elif key in self.list_win_notice_category_name:   # 中标公告
                notice = const.TYPE_WIN_NOTICE
            else:
                notice = ''
            if notice:
                yield scrapy.Request(url=start_url, callback=self.parse_urls,
                                     meta={'notice': notice})

    def parse_urls(self, resp):
        try:
            pages = int(re.findall('页次.*\/(\d+)', resp.xpath('//div[1][@class="span"]/text()').get())[0])
            total = pages * 10
            self.logger.info(f"初始总数提取成功 {total=} {resp.url=} {resp.meta.get('proxy')}")
            for page in range(1, pages+1):
                sub_cupgage = re.findall('.*curPage=(\d+)?&', resp.url)[0]
                info_url = re.sub('curPage={}'.format(sub_cupgage), 'curPage={}'.format(page), resp.url)
                yield scrapy.Request(url=info_url, callback=self.parse_data_check,
                                     meta={'notice': resp.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_urls {e}')

    def parse_data_check(self, resp):
        try:
            data_info = resp.xpath('//div[@class="info"]/ul/li')
            for data in data_info:
                data_url = data.xpath('./a/@href').get()
                if 'http' in data_url:
                    data_url = data_url
                else:
                    data_url = self.start_urls + data_url
                title_name = data.xpath('./a/div[@class="title"]/text()').get()
                pub_time = ''.join(data.xpath('./div[@class="time curr"]/text()').getall()).strip() + \
                           '-' + data.xpath('./div[@class="time curr"]/span/text()').get()
                yield scrapy.Request(url=data_url, callback=self.parse_item, dont_filter=True,
                                     meta={'notice': resp.meta['notice'],
                                           'title_name': title_name,
                                           'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {resp.url} {e}')

    def parse_item(self, resp):
        category = '政府采购'
        origin = resp.url
        info_source = self.area_province
        title_name = ''.join(resp.meta['title_name'])
        pub_time = resp.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        content = resp.xpath('//div[@id="myPrintArea"]').get()
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, resp.meta['notice'])
            if notice_type and content:
                files_path = {}
                # files_text = etree.HTML(content)
                # keys_a = []
                # files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                #                        keys_a=keys_a, log=self.logger)
                #  todo   注  该网站附件名和链接均不带后缀，由于文件服务下载资源时 需要后缀 故 产品要求本站 不采集附件

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

    cmdline.execute("scrapy crawl province_135_sichuan_spider".split(" "))
    # cmdline.execute("scrapy crawl province_135_sichuan_spider -a sdt=2021-10-01 -a edt=2021-10-15".split(" "))
