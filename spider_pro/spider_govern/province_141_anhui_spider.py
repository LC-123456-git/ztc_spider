#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-10-18
# @Describe: 安徽省政府采购网
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
    get_files, get_notice_type, remove_specific_element, get_timestamp, remove_element_by_xpath


class Province141AnHuiSpider(CrawlSpider):
    name = 'province_141_anhui_spider'
    allowed_domains = ['ccgp-jiangsu.gov.cn']
    start_urls = 'http://www.ccgp-anhui.gov.cn'
    domain_url = 'http://www.ccgp-anhui.gov.cn/indexController/index.do?'
    base_url = ''
    query_url = 'http://www.ccgp-anhui.gov.cn/cmsNewsController/getCgggNewsList.do?pageNum=1&numPerPage=10&title=&buyer_name=&agent_name=&proj_code=&bid_type={}&type=&dist_code=340001&pubDateStart={}&pubDateEnd={}&pProviceCode=340000&areacode_city=340001&areacode_dist=&channelCode={}&three=on'
    area_id = "141"
    area_province = '安徽省政府采购网'

    # 招标预告
    list_tender_notice_name = ['采购意向']
    # 招标公告
    list_notice_category_name = ['单一来源公示', '采购公告', '商城采购公告']
    # 招标变更
    list_zb_abnormal_name = ["更正公告"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标公告', '成交公告']
    # 招标异常
    list_alteration_category_name = ['终止公告']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['合同公告', '商城成交公告']

    def get_category(self, notice_name):
        if notice_name in self.list_notice_category_name:         # 招标公告
            notice = const.TYPE_ZB_NOTICE
        elif notice_name in self.list_zb_abnormal_name:           # 招标变更
            notice = const.TYPE_ZB_ALTERATION
        elif notice_name in self.list_win_advance_notice_name:    # 中标预告
            notice = const.TYPE_WIN_ADVANCE_NOTICE
        elif notice_name in self.list_win_notice_category_name:   # 中标公告
            notice = const.TYPE_WIN_NOTICE
        elif notice_name in self.list_tender_notice_name:         # 招标预告
            notice = const.TYPE_ZB_ADVANCE_NOTICE
        elif notice_name in self.list_alteration_category_name:   # 招标异常
            notice = const.TYPE_ZB_ABNORMAL
        elif notice_name in self.list_qualifiction_advance_num:   # 资格预审
            notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice_name in self.list_qita_num:                   # 其他
            notice = const.TYPE_OTHERS_NOTICE
        else:
            notice = ''
        return notice

    def __init__(self, *args, **kwargs):
        super(Province141AnHuiSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_data)

    def parse_data(self, response):
        try:
            if self.enable_incr:
                sdt_time = self.sdt_time
                edt_time = self.edt_time
            else:
                sdt_time = ''
                edt_time = ''
            li_list = response.xpath('//div[@id="div_b"]//ul/li')[:10]
            for li in li_list:
                notice_name = li.xpath('./a/text()').get()
                notice = self.get_category(notice_name)
                notice_code = li.xpath('./a/@target').get()
                notice_code_name = li.xpath('./a/@id').get()
                query_url = self.query_url.format(notice_code, sdt_time, edt_time, notice_code_name)
                yield scrapy.Request(url=query_url, callback=self.parse_data_info, dont_filter=True,
                                     meta={'notice': notice})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')

    def parse_data_info(self, response):
        try:
            pages_str = response.xpath('//div[@class="page"]/div[@class="pg"]/ul/li//span/text()').get()
            total = re.findall('.*共(\d+?)条', ''.join(pages_str).replace(' ', ''))[0]
            pages = re.findall('.*共(\d+?)页', ''.join(pages_str).replace(' ', ''))[0]
            self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
            for page in range(1, int(pages) + 1):
                sub_gage = re.findall('.*pageNum=(\d+)', response.url)[0]
                info_url = re.sub('pageNum={}'.format(sub_gage), 'pageNum={}'.format(page), response.url)
                yield scrapy.Request(url=info_url, callback=self.parse_data_check, dont_filter=True,
                                     meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_check(self, response):
        try:
            count = 0
            data_info = response.xpath('//div[@class="zc_content1"]/div[last()]/table/tr')
            for info in data_info:
                count += 1
                pub_time = ''.join(info.xpath('./td[last()]/a/text()').get()).replace('[', '').replace(']', '').strip()
                title_name = info.xpath('./td[1]/a/@title').get()
                info_url = self.start_urls + info.xpath('./td[1]/a/@href').get()
                yield scrapy.FormRequest(url=info_url, callback=self.parse_item, dont_filter=True,
                                         priority=(len(data_info) - count) * 100,
                                         meta={'notice': response.meta['notice'],
                                               'title_name': title_name,
                                               'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            category = '政府采购'
            origin = response.url
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//div[@class="colspanColumn"]').get()
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                _, content = remove_specific_element(content, 'h1')
                _, content = remove_specific_element(content, 'div', 'class', 'source')
                _, content = remove_specific_element(content, 'div', 'class', 'navCurrent')
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                                       keys_a=keys_a, log=self.logger)
                if not files_path:
                    _, content = remove_specific_element(content, 'div', 'class', 'related_new')

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
            self.logger.error(f'发起数据请求失败parse_data_check {e}, {response.meta["info_url"]}')



if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_141_anhui_spider".split(" "))
    cmdline.execute("scrapy crawl province_141_anhui_spider -a sdt=2021-09-01 -a edt=2021-10-20".split(" "))
