#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-23
# @Describe: 海南省政府采购网

import scrapy, re, math
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
     get_files, get_notice_type, remove_specific_element


class Province126HainanSpiderSpider(CrawlSpider):
    name = 'province_126_hainan_spider'
    allowed_domains = ['ccgp-hainan.gov.cn']
    start_urls = 'https://www.ccgp-hainan.gov.cn'
    domain_url = 'https://www.ccgp-hainan.gov.cn/cgw/cgw_list.jsp?zone='
    base_url = 'https://www.ccgp-hainan.gov.cn/cgw/cgw_list.jsp?currentPage={}&begindate=&enddate=&title=&bid_type={}&proj_number=&zone=&ctype='
    query_url = 'https://www.ccgp-hainan.gov.cn/cgw/cgw_list_cgyx.jsp?mofdivcode=&pageNo={}&searchword='
    area_id = "126"
    area_province = '海南省政府采购网'

    # 招标预告
    list_tender_notice_num = ['采购意向', '采购需求']
    # 招标公告
    list_notice_category_name = ['公开招标公告', '询价公告', '竞争性谈判公告', '竞争性磋商公告', '单一来源公示', '邀请招标公告']
    # 招标变更
    list_zb_abnormal_name = ["更正公告"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标公告', '成交公告']
    # 招标异常
    list_alteration_category_name = ['终止公告']
    # 资格预审
    list_qualifiction_advance_num = ['资格预审公告']
    # 其他
    list_qita_num = ['合同公告', '其它公告']

    def __init__(self, *args, **kwargs):
        super(Province126HainanSpiderSpider, self).__init__()
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
            li_list = response.xpath('//div[@class="cg20-gll1"]/ul/li')[1:-1]
            for li in li_list:
                notice_name = li.xpath('./a/text()').get()
                notice_url = self.start_urls + li.xpath('./a/@href').get()
                if notice_name in self.list_notice_category_name:                   # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:                     # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_advance_notice_name:              # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif notice_name in self.list_win_notice_category_name:             # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_tender_notice_num:                    # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif notice_name in self.list_alteration_category_name:             # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                elif notice_name in self.list_qualifiction_advance_num:             # 资格预审
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif notice_name in self.list_qita_num:                              # 其他
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if notice:
                    yield scrapy.Request(url=notice_url, callback=self.parse_data_info,
                                         meta={'notice': notice, 'notice_name': notice_name})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_urls {e}')

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                if response.text:
                    if response.meta['notice_name'] == '采购意向':
                        li_list = response.xpath('//div[@class="cg20-glR"]/table/tr')[1:]
                        count = 0
                        num = 0
                        page = 1
                        for li in li_list:
                            count += 1
                            pub_time = li.xpath('./td[last()]/text()').get()
                            info_url = 'https://www.ccgp-hainan.gov.cn/cgw/' + li.xpath('./td[1]/a/@href').get()
                            title_name = li.xpath('./td[1]/a/text()').get()
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                num += 1
                                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                     priority=(len(li_list) - count)*5,
                                                     meta={'notice': response.meta['notice'],
                                                           'pub_time': pub_time,
                                                           'title_name': title_name,
                                                           'notice_name': response.meta['notice_name']})
                            if num >= int(len(li_list)):
                                total = int(len(li_list))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                                page += 1
                                yield scrapy.Request(url=self.query_url.format(page),
                                                     callback=self.parse_data_info,
                                                     meta={'notice': response.meta['notice'],
                                                           'notice_name': response.meta['notice_name']})
                    else:
                        li_list = response.xpath('//div[@class="index07_07_02"]/ul/li')
                        num = 0
                        count = 0
                        page = 1
                        for li in li_list:
                            count += 1
                            pub_time = li.xpath('./span[1]/em/text()').get()
                            info_url = self.start_urls + li.xpath('./span[1]/a/@href').get()
                            title_name = li.xpath('./span[1]/a/text()').get()
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                num += 1
                                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                     priority=(len(li_list)-count)*5,
                                                     meta={'notice': response.meta['notice'],
                                                           'pub_time': pub_time,
                                                           'title_name': title_name,
                                                           'notice_name': response.meta['notice_name']})
                            if num >= int(len(li_list)):
                                total = int(len(li_list))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                                page += 1
                                yield scrapy.Request(url=self.base_url,
                                                     callback=self.parse_data_info,
                                                     meta={'notice': response.meta['notice'],
                                                           'notice_name': response.meta['notice_name']})
            else:
                if response.text:
                    if response.meta['notice_name'] == '采购意向':
                        total_con = ''.join(response.xpath('//div[@class="nei02_04_02"]/text()').getall()).strip()
                        total = int(re.findall('(\d+?)条', total_con)[0])
                        pages = math.ceil(total/20)
                        self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                        for num in range(1, int(pages) + 1):
                            yield scrapy.Request(url=self.query_url.format(num),
                                                 callback=self.parse_data_check,
                                                 priority=(int(pages) - num) * 10,
                                                 meta={'notice': response.meta['notice'],
                                                       'notice_name': response.meta['notice_name']})
                    else:
                        pages_con = ''.join(response.xpath('//div[@class="nei02_04_02"]//ul/li/text()').getall()).strip()
                        pages = int(re.findall('(\d+?)页', pages_con)[0])
                        total = pages * 20
                        self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                        bid_type = re.findall('.*?bid_type=(\d+?)&', response.url)[0]
                        for num in range(1, int(pages) + 1):
                            yield scrapy.Request(url=self.base_url.format(num, bid_type),
                                                 callback=self.parse_data_check,
                                                 priority=(int(pages) - num) * 10,
                                                 meta={'notice': response.meta['notice'],
                                                       'notice_name': response.meta['notice_name']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e} {response.url}')

    def parse_data_check(self, response):
        try:
            if response.text:
                if response.meta['notice_name'] == '采购意向':
                    li_list = response.xpath('//div[@class="cg20-glR"]/table/tr')[1:]
                    count = 0
                    for li in li_list:
                        count += 1
                        pub_time = li.xpath('./td[last()]/text()').get()
                        info_url = 'https://www.ccgp-hainan.gov.cn/cgw/' + li.xpath('./td[1]/a/@href').get()
                        title_name = li.xpath('./td[1]/a/text()').get()
                        yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(li_list)-count)*10,
                                             meta={'pub_time': pub_time,
                                                   'title_name': title_name,
                                                   'notice': response.meta['notice'],
                                                   'notice_name': response.meta['notice_name']})
                else:
                    li_list = response.xpath('//div[@class="index07_07_02"]/ul/li')
                    count = 0
                    for li in li_list:
                        count += 1
                        pub_time = li.xpath('./span[1]/em/text()').get()
                        info_url = self.start_urls + li.xpath('./span[1]/a/@href').get()
                        title_name = li.xpath('./span[1]/a/text()').get()
                        yield scrapy.Request(url=info_url, callback=self.parse_item, priority=(len(li_list)-count)*10,
                                             meta={'pub_time': pub_time,
                                                   'title_name': title_name,
                                                   'notice': response.meta['notice'],
                                                   'notice_name': response.meta['notice_name']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        content = response.xpath('//div[@class="cg20-gl"]').get()
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = ''.join(response.meta['title_name'])
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title
                _, content = remove_specific_element(content, 'div', 'class', 'zx-xxxqy')
                # 尾部 多余字样
                _, content = remove_specific_element(content, 'div', 'class', 'content04')
                _, content = remove_specific_element(content, 'div', 'class', 'content_1')
                _, content = remove_specific_element(content, 'table', 'bgcolor', '#ba2424')

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

    # cmdline.execute("scrapy crawl province_126_hainan_spider".split(" "))
    cmdline.execute("scrapy crawl province_126_hainan_spider -a sdt=2021-07-20 -a edt=2021-08-30".split(" "))
