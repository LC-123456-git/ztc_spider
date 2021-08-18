#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-17
# @Describe: 山东省政府采购网

import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
     get_files, get_notice_type, remove_specific_element


class Province122ShandongSpiderSpider(CrawlSpider):
    name = 'province_122_shandong_spider'
    allowed_domains = ['ccgp-shandong.gov.cn']
    start_urls = 'http://www.ccgp-shandong.gov.cn'
    domain_url = 'http://www.ccgp-shandong.gov.cn/sdgp2017/site/listnew.jsp'
    base_url = 'http://www.ccgp-shandong.gov.cn/sdgp2017/site/index.jsp'
    query_url = ''
    area_id = "122"
    area_province = '山东省政府采购网'

    # 招标预告
    list_tender_notice_num = {'意向公开': '2500'}
    # 招标公告
    list_notice_category_name = {'采购公告': '0301', '单一来源': '2102'}
    # 招标变更
    list_zb_abnormal_name = {"更正公告": '0305'}
    # 中标预告
    list_win_advance_notice_name = {}
    # 中标公告
    list_win_notice_category_name = {'结果公告': '0302'}
    # 招标异常
    list_alteration_category_name = {'终止公告': '0306'}
    # 资格预审
    list_qualifiction_advance_num = {}
    # 其他
    list_qita_num = {'合同公示': '2502'}

    r_dict = {
        'subject': '',
        'unitname': '',
        'pdate': '',
        'colcode': '2502',
        'curpage': '1',
        'grade': 'province',
        'region': '',
        'firstpage': '',
    }

    def __init__(self, *args, **kwargs):
        super(Province122ShandongSpiderSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.base_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="conl"]/div[2]/div[2]/div/div/figure')[1:-2]
            for li in li_list:
                notice_name = li.xpath('./h1/text()'). get()
                if notice_name in self.list_notice_category_name.keys():                   # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                    notice_value = self.list_notice_category_name[notice_name]
                elif notice_name in self.list_zb_abnormal_name.keys():                     # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                    notice_value = self.list_zb_abnormal_name[notice_name]
                elif notice_name in self.list_win_advance_notice_name.keys():              # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                    notice_value = self.list_win_advance_notice_name[notice_name]
                elif notice_name in self.list_win_notice_category_name.keys():             # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                    notice_value = self.list_win_notice_category_name[notice_name]
                elif notice_name in self.list_tender_notice_num.keys():                    # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                    notice_value = self.list_tender_notice_num[notice_name]
                elif notice_name in self.list_alteration_category_name.keys():             # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                    notice_value = self.list_alteration_category_name[notice_name]
                elif notice_name in self.list_qualifiction_advance_num.keys():             # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    notice_value = self.list_qualifiction_advance_num[notice_name]
                elif notice_name in self.list_qita_num.keys():                              # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                    notice_value = self.list_qita_num[notice_name]
                else:
                    notice = ''
                    notice_value = ''
                if notice:
                    r_dict = self.r_dict | {'colcode': notice_value}
                    yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_info,
                                             dont_filter=True, formdata=r_dict,
                                             meta={'r_dict': r_dict,
                                                   'notice': notice})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if response.text:
                    li_list = response.xpath('//div[@class="subCont"]/ul/li')
                    num = 0
                    count = 0
                    for li in li_list:
                        count += 1
                        pub_time = li.xpath('.//span[@class="hits"]/text()').get()
                        info_url = self.start_urls + li.xpath('./span[@class="title"]/span[1]/a/@href').get()
                        title_name = li.xpath('./span[@class="title"]/span[1]/a/@title').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(li_list)-count)*5,
                                                 meta={'notice': response.meta['notice'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if num >= int(len(li_list)):
                            total = int(len(li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            pages = int(response.meta['r_dict']['curpage']) + 1
                            r_dict = response.meta['r_dict'] | {'curpage': str(pages)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_dict,
                                                     callback=self.parse_data_info, dont_filter=True,
                                                     meta={'notice': response.meta['notice'],
                                                           'r_dict': r_dict})
            else:
                if response.text:
                    pages = response.xpath('//div[@class="page_list"]/span[@id="totalnum"]/text()').get()
                    total = int(pages) * 20
                    self.logger.info(f"初始总数提取成功 {total=} {response.meta['r_dict']} {response.meta.get('proxy')}")
                    for num in range(1, int(pages) + 1):
                        new_dict = response.meta['r_dict'] | {'curpage': str(num)}
                        yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_check,
                                                 formdata=new_dict, dont_filter=True, priority=(int(pages) - num) * 10,
                                                 meta={'notice': response.meta['notice']})
                else:
                    print(response.meta['r_dict'])
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if response.text:
                li_list = response.xpath('//div[@class="subCont"]/ul/li')
                for li in li_list:
                    pub_time = li.xpath('.//span[@class="hits"]/text()').get()
                    info_url = self.start_urls + li.xpath('./span[@class="title"]/span[1]/a/@href').get()
                    title_name = li.xpath('./span[@class="title"]/span[1]/a/@title').get()
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                         meta={'pub_time': pub_time,
                                               'title_name': title_name,
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = response.xpath('//div[@class="listConts"]').get()
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = ''.join(response.meta['title_name']).replace('【山东省本级】', '')
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title
                _, content = remove_specific_element(content, 'h1', 'class', 'title')
                # 去除时间
                _, content = remove_specific_element(content, 'div', 'class', 'info_box')
                # 详细信息
                _, content = remove_specific_element(content, 'div', 'class', 'conttitle')
                # 内容以外区域
                _, content = remove_specific_element(content, 'div', 'class', 'relative')
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.domain_url, origin, files_text, keys_a=keys_a)
                if not files_path:
                    _, content = remove_specific_element(content, 'div', 'id', 'file_list')
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

    # cmdline.execute("scrapy crawl province_122_shandong_spider".split(" "))
    cmdline.execute("scrapy crawl province_122_shandong_spider -a sdt=2021-06-20 -a edt=2021-08-30".split(" "))
