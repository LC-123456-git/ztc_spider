#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-10-25
# @Describe: 中招联合招标采购网
import copy
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
    get_files, get_notice_type, remove_specific_element, get_timestamp, remove_element_by_xpath


class Province149ZhongZhaoLianSpider(CrawlSpider):
    name = 'province_149_zhongzhaolian_spider'
    allowed_domains = ['365trade.com']
    start_urls = 'http://www.365trade.com.cn'
    domain_url = ''
    base_url = ''
    query_url = ''
    area_id = "149"
    area_province = '中招联合招标采购网'

    def __init__(self, *args, **kwargs):
        super(Province149ZhongZhaoLianSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    custom_settings = {'DOWNLOADER_MIDDLEWARES': {
                            'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
                            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
                            'scrapy_splash.SplashCookiesMiddleware': 770,
                            'scrapy_splash.SplashMiddleware': 780,
                            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
                        }
                       }

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls, callback=self.parse_data)

    def parse_data(self, response):
        info_list = response.xpath('//div[@class="TabbedPanels"]/ul')
        for info in info_list:
            info_url = self.start_urls + info.xpath('./li[last()]/a/@href').get()
            if 'zbgg' in info_url:
                notice_type = const.TYPE_ZB_NOTICE
            elif 'bggg' in info_url:
                notice_type = const.TYPE_ZB_ALTERATION
            elif 'jggs' in info_url:
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type = ''
            if notice_type:
                info_url = info_url.replace(''.join(info_url).split('/')[-1], 'index_1.htm')
                yield scrapy.Request(url=info_url, callback=self.parse_data_info, dont_filter=True,
                                     meta={'notice_type': notice_type})

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                count = 0
                num = 0
                info_data = response.xpath('//div[@class="search_warp"]/ul/li')
                for info in info_data:
                    count += 1
                    title_name = info.xpath("./a/p/span/@title").get()
                    pub_time = (info.xpath('./a/i/text()').get()).replace('发布日期：', '')
                    info_url = self.start_urls + info.xpath('./a[@class="searchBtn fr"]/@href').get()
                    business_category = info.xpath('./a/p/em/text()').get()
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                             priority=(len(info_data) - count) * 100,
                                             meta={'notice_type': response.meta['notice_type'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time,
                                                   'business_category': business_category})
                    if num >= int(len(info_data)):
                        total = int(len(info_data))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        data_page = int(re.findall('(\d+)', ''.join(response.url).split('/')[-1])[0]) + 1
                        data_url = response.url.replace(''.join(response.url).split('/')[-1], 'index_{}.htm').format(data_page)
                        yield scrapy.Request(url=data_url, callback=self.parse_data_info, dont_filter=True,
                                             meta={'notice_type': response.meta['notice_type']})
            else:
                total_data = response.xpath('//div[@class="pagination_div"]/div/text()').get()
                total = re.findall('共(\d+)条', total_data)[0]
                pages = int(re.findall('\d+\/(\d+)页', total_data)[0])
                self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                count = 0
                for page in range(1, pages + 1):
                    count += 1
                    data_url = response.url.replace(''.join(response.url).split('/')[-1], 'index_{}.htm').format(page)
                    yield scrapy.Request(url=data_url, callback=self.parse_data_check,
                                         priority=((pages + 1) - count) * 50, dont_filter=True,
                                         meta={'notice_type': response.meta['notice_type']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')


    def parse_data_check(self, response):
        try:
            info_data = response.xpath('//div[@class="search_warp"]/ul/li')
            count = 0
            for info in info_data:
                count += 1
                title_name = info.xpath("./a/p/span/@title").get()
                pub_time = info.xpath('./a/i/text()').get().replace('发布日期：', '')
                info_url = self.start_urls + info.xpath('./a[@class="searchBtn fr"]/@href').get()
                business_category = info.xpath('./a/p/em/text()').get()
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=(len(info_data) - count) * 100,
                                     meta={'notice_type': response.meta['notice_type'],
                                           'title_name': title_name,
                                           'pub_time': pub_time,
                                           'business_category': business_category})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}, {response.url}')

    def parse_item(self, response):
        try:
            category = ''
            business_category = response.meta['business_category']
            origin = response.url
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            content = response.xpath('//div[@id="content"]').get()
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "本次招标公告")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "本次公告")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "本采购项目")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "本次采购公告")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "中国招标投标")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "河南省电子")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "中原招采网")]')
            _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="noticeNote"]/p[contains(string(), "本次变更公告")]')

            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice_type'])
                files_text = etree.HTML(content)
                keys_a = []
                files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                                       keys_a=keys_a, log=self.logger)

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
                notice_item['business_category'] = business_category

                yield notice_item
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_item {e}, {response.meta["info_url"]}')


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_149_zhongzhaolian_spider".split(" "))
    # cmdline.execute("scrapy crawl province_149_zhongzhaolian_spider -a sdt=2021-10-01 -a edt=2021-10-30".split(" "))
