# -*- coding: utf-8 -*-
import scrapy


class CreditInfoCrawlerSpider(scrapy.Spider):
    name = 'credit_info_crawler'
    allowed_domains = ['www.gsxt.gov.cn']
    start_urls = ['http://www.gsxt.gov.cn/']

    def parse(self, response):
        pass
