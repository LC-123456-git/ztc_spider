#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-28
# @Describe: 日志记录扩展件

import logging
from collections import defaultdict
from scrapy import signals
from scrapy.exceptions import NotConfigured
from datetime import datetime


class SpiderOpenCloseLogging(object):
    """监控Spider允许"""

    def __init__(self, item_count):
        self.item_count = item_count

    @classmethod
    def from_crawler(cls, crawler):
        # get the number of items from settings
        item_count = crawler.settings.getint('MYEXT_ITEMCOUNT', 100)

        # instantiate the extension object
        ext = cls(item_count)

        # connect the extension object to signals
        # crawler.signals.connect(ext.engine_started, signal=signals.engine_started)
        # crawler.signals.connect(ext.engine_stopped, signal=signals.engine_stopped)
        # crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        # crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
        # crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        # crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        # crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        # crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)
        # crawler.signals.connect(ext.request_reached_downloader, signal=signals.request_reached_downloader)
        # crawler.signals.connect(ext.response_received, signal=signals.response_received)
        # crawler.signals.connect(ext.request_left_downloader, signal=signals.request_left_downloader)
        # crawler.signals.connect(ext.response_received, signal=signals.response_received)
        # crawler.signals.connect(ext.response_downloaded, signal=signals.response_downloaded)
        # crawler.signals.connect(ext.bytes_received, signal=signals.bytes_received)
        # crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        # crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        # crawler.signals.connect(ext.item_error, signal=signals.item_error)

        # return the extension object
        return ext

    # def engine_started(self, spider):
    #     spider.logger.info("engine_started")
