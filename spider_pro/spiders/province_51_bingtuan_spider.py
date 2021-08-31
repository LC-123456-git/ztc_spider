#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-22
# @Describe: 兵团公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse

from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element, get_files


class MySpider(Spider):
    name = "province_51_bingtuan_spider"
    area_id = "51"
    allowed_domains = ['ggzy.xjbt.gov.cn']
    start_url = 'http://ggzy.xjbt.gov.cn'
    domain_url = "http://ggzy.xjbt.gov.cn/TPFront/jyxx/"
    area_province = "新疆兵团公共资源交易网"

    #招标公告
    list_notice_category_num = ['招标公告', '单一来源公示', '采购公告', '交易公告']
    # 招标异常
    list_alteration_category_num = []
    # 中标公告
    list_win_notice_category_num = ['中标结果公告', '结果公示', '成交公示']
    #招标变更
    list_zb_abnormal = ['答疑澄清', '变更公告']
    #中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    #资格预审结果公告
    list_qualification_num = ['资格预审公示']
    # 其他公告
    list_others_notice_num = ['合同公示']


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_categoy_urls)

    def parse_categoy_urls(self, response):
        try:
            li_list = response.xpath('//td[@class="LeftMenu"]/a')
            for li in li_list:
                categoy = li.xpath('./font/text()').get()
                classify_url_list = self.start_url + li.xpath('./@href').get()
                yield scrapy.Request(url=classify_url_list, callback=self.parse_urls,
                                     meta={'categoy': categoy})
        except Exception as e:
            self.logger.error(f"获取的parse_categoy_urls错误 {response.meta=} {e} {response.url=}")

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//td[@background="/TPFront/webimages/sub_01_bg.gif"]/table/tr')
            for li in li_list:
                if li.xpath('./td[@class="MoreinfoColor"]/text()'):
                    type_name = li.xpath('./td[@class="MoreinfoColor"]/text()').get()
                    type_url = response.url + li.xpath('./td[@align="right"]/a/@href').get()        #获取类型url的code 拼接详情页的url
                    if type_name in self.list_notice_category_num:         # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    elif type_name in self.list_win_notice_category_num:   # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif type_name in self.list_zb_abnormal:               # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif type_name in self.list_win_advance_notice_num:    # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif type_name in self.list_qualification_num:         # 资格预审结果公告
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif type_name in self.list_others_notice_num:         # 其他公告
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=type_url, callback=self.parse_data_info, priority=50,
                                             meta={'categoy': response.meta.get('categoy'), 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_categoy_data_urls {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            urls_list = response.url + '?Paging={}'
            if self.enable_incr:
                nums = 1
                page = 1
                count = 0
                li_list = response.xpath('//div[@align="center"]/table/tr')[:-1:2]
                for li in range(len(li_list)):
                    title_name = li_list[li].xpath('./td[2]/a/@title').get()
                    info_url = self.start_url + li_list[li].xpath('./td[2]/a/@href').get()
                    pub_time = li_list[li].xpath('./td[3]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        nums += 1
                        count += 1
                        yield scrapy.Request(url=info_url, callback=self.parse_itme, priority=(len(li_list)-count) * 10,
                                             meta={'title_name': title_name,
                                                   'pub_time': pub_time,
                                                   'categoy': response.meta['categoy'],
                                                   'notice': response.meta['notice']})

                    if li >= nums:
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page += 1
                        yield scrapy.Request(url=urls_list.format(page), callback=self.parse_data_info, priority=100,
                                             meta={'categoy': response.meta.get('categoy'),
                                                   'notice': response.meta['notice']})

            else:
                pages = re.findall('/(\d+)', response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get())[0]    #总页数
                total = int(pages) * 20              #总条数
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for i in range(1, int(pages) + 1):
                    yield scrapy.Request(url=urls_list.format(i), callback=self.parse_data, priority=100,
                                         meta={'categoy': response.meta.get('categoy'),
                                               'notice': response.meta['notice']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_all_urls {e} {response.url=}")

    def parse_data(self, response):
        try:
            name_list = response.xpath('//div[@align="center"]/table/tr')[:-1:2]
            for name in name_list:
                title_url = self.start_url + name.xpath('./td[2]/a/@href').get()
                title_name = name.xpath('./td[2]/a/@title').get()
                pub_time = ''.join(name.xpath('./td[3]/text()').get()).replace('[', '').replace(']', '')
                yield scrapy.Request(url=title_url, callback=self.parse_itme, priority=150,
                                     meta={'categoy': response.meta.get('categoy'),
                                           'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'title_name': title_name})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_itme(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        try:
            if response.status == 200:
                origin = response.url
                title_name = response.meta['title_name']
                if re.search(r'变更|更正|澄清', title_name):  # 招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'中标候选人公示|中标公示', title_name):  # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'资格预审', title_name):  # 资格预审结果公告
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'终止|中止|异常|废标|流标', title_name):  # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'终止|中止|异常|废标|流标', title_name):  # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    notice_type = response.meta['notice']
                pub_time = response.meta["pub_time"]
                pub_time = get_accurate_pub_time(pub_time)
                category = response.meta['categoy']
                content = response.xpath('//table[@id="tblInfo"]').get()
                # 去除 title
                _, content = remove_specific_element(content, 'td', 'id', 'tdTitle')
                # 去除 下方的文件
                _, content = remove_specific_element(content, 'td', 'style', 'border:0;margin:0 auto;')
                _, content = remove_specific_element(content, 'tr', 'id', 'trAttach')


                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.domain_url, origin, files_text, pub_time=pub_time, keys_a=keys_a)

                notice_item = NoticesItem()
                notice_item["origin"] = origin
                notice_item["title_name"] = title_name
                notice_item["pub_time"] = pub_time
                notice_item["info_source"] = self.area_province
                notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                notice_item["files_path"] = '' if not files_path else files_path
                notice_item["content"] = content
                notice_item["area_id"] = self.area_id
                notice_item["notice_type"] = notice_type
                notice_item["category"] = category

                yield notice_item
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_itme {e} {response.url=}")


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_51_bingtuan_spider".split(" "))
    # cmdline.execute("scrapy crawl province_51_bingtuan_spider -a sdt=2021-07-20 -a edt=2021-08-20".split(" "))


























