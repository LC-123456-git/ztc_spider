#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2021-01-07
# @Describe: 延迟中间件
from twisted.internet import reactor
from twisted.internet.defer import Deferred


class DelayedRequestMiddleware(object):

    def __init__(self, logger, **kwargs):
        super(DelayedRequestMiddleware, self).__init__()
        self.logger = logger
        self.name_delay_request = kwargs.get("NAME_DELAY_REQUEST")
        self.time_delay_request = kwargs.get("TIME_DELAY_REQUEST")

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        logger = crawler.spider.logger
        return cls(logger, **settings)

    def process_request(self, request, spider):
        if request.meta.get(self.name_delay_request):
            request.meta[self.name_delay_request] = False
            defer = Deferred()
            reactor.callLater(self.time_delay_request, defer.callback, None)
            return defer


if __name__ == "__main__":
    pass
