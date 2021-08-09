#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-04
# @Describe: 吉林公共资源交易网

import scrapy


class Province119HubeiSpiderSpider(scrapy.Spider):
    name = 'province_119_hubei_spider'
    allowed_domains = ['ccgp-hubei.gov.cn']
    start_urls = ['http://ccgp-hubei.gov.cn/']

    def parse(self, response):
        pass
