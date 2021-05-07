#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-28
# @Describe: Url去重中间件
import redis
from redisbloom.client import Client
from scrapy.exceptions import IgnoreRequest
from spider_pro import constans as const


class UrlDuplicateRemovalMiddleware(object):

    def __init__(self, area_id, logger, **kwargs):
        super(UrlDuplicateRemovalMiddleware, self).__init__()
        self.logger = logger
        self.redis_pool = redis.ConnectionPool(
            host=kwargs.get("REDIS_HOST"), port=8090, decode_responses=True, max_connections=int(kwargs.get("MAX_CONNECTIONS")),
            password=kwargs.get("REDIS_PASSWORD"), retry_on_timeout=True)
        self.redis_bloom_client = Client(connection_pool=self.redis_pool, port=8090)
        self.key = f"{kwargs.get('NAME_DUPLICATE_URLS')}:{area_id}"
        self.enable = True if kwargs.get("ENABLE_URL_DUP_REMOVE_USE") in const.TRUE_LIST else False
        if not self.redis_bloom_client.exists(self.key) and self.enable:
            self.redis_bloom_client.bfCreate(self.key, kwargs.get("DEFAULT_ERROR_RATE"), kwargs.get("DEFAULT_CAPACITY"))

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        area_id = crawler.spider.area_id
        logger = crawler.spider.logger
        return cls(area_id, logger, **settings)

    def process_request(self, request, spider):
        if self.enable and request.meta.get("cb_kwargs", None):
            if self.redis_bloom_client.bfExists(self.key, request.url):
                raise IgnoreRequest

    def process_response(self, request, response, spider):
        if self.enable and request.meta.get("cb_kwargs", None) and response.status == 200:
            if self.redis_bloom_client.bfExists(self.key, request.url):
                raise IgnoreRequest
            else:
                self.redis_bloom_client.bfAdd(self.key, request.url)
        return response


if __name__ == "__main__":
    REDIS_HOST = "114.67.84.76"
    MAX_CONNECTIONS = 50
    REDIS_PASSWORD = "Ly3sa%@D0$pJt0y6."
    redis_pool = redis.ConnectionPool(
        host=REDIS_HOST, password=REDIS_PASSWORD, decode_responses=True, max_connections=MAX_CONNECTIONS,
        retry_on_timeout=True)
    rb = Client(connection_pool=redis_pool, port=8090)
    print(f'{rb.bfInfo("duplicate_urls:49").insertedNum=}')
    print(f'{rb.bfInfo("duplicate_urls:49").size=}')
    print(f'{rb.bfExists("duplicate_urls:49", "http://www.nxggzyjy.org/ningxiaweb/002/002004/002004003/2.html")}')
    pass
