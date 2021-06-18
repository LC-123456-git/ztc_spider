#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-25
# @Describe: 湖南公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time


class MySpider(Spider):
    name = "province_28_hunan_spider"
    area_id = "28"
    allowed_domains = ['ggzy.hunan.gov.cn']
    url = 'https://ggzy.hunan.gov.cn'
    domain_url = "https://ggzy.hunan.gov.cn/jydt/002002/about.html"
    area_province = "湖南"

    #招标公告
    list_notice_category_num = ['002002006001', '002002007001', '002002005001', '002002004001', '002002003001', '002002002001', '002002001001']
    # 招标异常
    list_alteration_category_num = []
    # 中标公告
    list_win_notice_category_num = ['002002001003', '002002002002', '002002003002', '002002005002', '002002006002', '002002007004']
    #招标变更
    list_zb_abnormal_num = ['002002001005', '002002001006', '002002002003', '002002003003', '002002005003', '002002006003', '002002007002']
    #中标预告
    list_win_advance_notice_num = ['002002001002', '002002007003']
    #资格预审结果公告
    list_qualification_num = ['002002001004']
    # 其他公告
    list_others_notice_num = []


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
            li_list = response.xpath('//ul[@class="wb-tree"]/li[2]/ul/li')[:-1]
            for li in li_list:
                categoy = ''.join(li.xpath('./a/text()').get()).strip()
                classify_url_list = self.url + li.xpath('./a/@href').get()
                yield scrapy.Request(url=classify_url_list, callback=self.parse_categoy_data_urls,
                                     meta={'categoy': categoy})
        except Exception as e:
            self.logger.error(f"获取的url错误 {response.meta=} {e} {response.url=}")

    def parse_categoy_data_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="tabview-hd"]/ul/li')
            for li in li_list:
                type_code = re.search('\d+', li.xpath('./@data-target').get())[0]        #获取类型url的code
                type_url = re.findall('(.*\d{9})', response.url)[0] + '/' + type_code + '/moreinfo.html'
                if type_code in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE
                elif type_code in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE
                elif type_code in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION
                elif type_code in self.list_win_advance_notice_num:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_code in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                else:
                    notice = const.TYPE_OTHERS_NOTICE
                if notice:
                    yield scrapy.Request(url=type_url, callback=self.parse_all_urls,
                                 meta={'categoy': response.meta.get('categoy'),
                                       'notice': notice, 'type_code': type_code})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_all_urls(self, response):
        try:
            if response.xpath('//ul[@class="wb-data-item"]/li'):
                if self.enable_incr:
                    page = 1
                    data_li_list = response.xpath('//ul[@class="wb-data-item"]/li')
                    nums = 0
                    for li in range(len(data_li_list)):
                        pub_time = data_li_list[li].xpath('./span/text()').get()
                        pub_time = get_accurate_pub_time(pub_time)
                        info_url = self.url + data_li_list[li].xpath('./div/a/@href').get()
                        title_name = data_li_list[li].xpath('./div/a/@title').get()
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_itme,
                                                 meta={'categoy': response.meta.get('categoy'),
                                                       'notice': response.meta['notice'],
                                                       'type_code': response.meta['type_code'],
                                                       'pub_time': pub_time,
                                                       'title_name': title_name})
                        if nums >= len(data_li_list):
                            page += 1
                            data_all_url = re.findall('(.*\d{12})', response.url)[0] + '/{}.html'.format(page)
                            yield scrapy.Request(url=data_all_url, callback=self.parse_all_data,
                                                 meta={'categoy': response.meta.get('categoy'),
                                                       'notice': response.meta['notice'],
                                                       'type_code': response.meta['type_code']})
                else:
                    if response.xpath('//ul[@class="ewb-page-items clearfix"]/li/span/text()').get():
                        pages = re.findall('/(\d+)', response.xpath('//ul[@class="ewb-page-items clearfix"]/li/span/text()').get())[0]  #总页数
                        total = int(pages) * 14                                                           # 总条数
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    else:
                        pages = 1
                    for num in range(1, int(pages) + 1):
                        if num == 1:
                            data_all_url = response.url
                        else:
                            data_all_url = re.findall('(.*\d{12})', response.url)[0] + '/{}.html'.format(num)

                        yield scrapy.Request(url=data_all_url, callback=self.parse_all_data,
                                             meta={'categoy': response.meta.get('categoy'), 'notice': response.meta['notice'],
                                                   'type_code': response.meta['type_code']})


        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_all_data(self, response):
        try:
            info_list = response.xpath('//ul[@class="wb-data-item"]/li')
            for li in info_list:
                info_url = self.url + li.xpath('./div/a/@href').get()
                title_name = li.xpath('./div/a/@title').get()
                pub_time = li.xpath('./span/text()').get()
                yield scrapy.Request(url=info_url, callback=self.parse_itme, priority=200,
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
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)

            title_name = response.meta['title_name']
            category = response.meta['categoy']
            if re.search(r'交易公告', title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'成交公告', title_name):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'终止|中止|异常|废标|流标', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = response.meta['notice']
            files_path = {}
            content = response.xpath('//div[@class="news-article"]').get()
            pattern = re.compile(r'<p class="news-article-info".*?>(.*?)</p>', re.S)
            contents = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<div id="BM".*?>.*?</table>', re.S)
            contents = contents.replace(''.join(re.findall(pattern, contents)), '')

            pattern = re.compile(r'<h6 class="news-article-tt".*?>(.*?)</h6>', re.S)
            contents = contents.replace(''.join(re.findall(pattern, contents)), '')

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = '' if not files_path else files_path
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = notice_type
            notice_item["category"] = category
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_28_hunan_spider".split(" "))


























