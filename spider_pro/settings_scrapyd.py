#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-23
# @Describe: Scrapy settings for scrapyd
import os
import datetime
import logging.config

# project bot name
BOT_NAME = 'spider_pro'

# project spider modules
SPIDER_MODULES = ['spider_pro.spiders', 'spider_pro.extra_spiders', 'spider_pro.spider_govern',
                  'spider_pro.spider_thirdparty']
NEWSPIDER_MODULE = 'spider_pro.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# DEFAULT_REQUEST_HEADERS
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# download middleware
DOWNLOADER_MIDDLEWARES = {
    # 'spider_pro.middlewares.DelayedRequestMiddleware.DelayedRequestMiddleware': 50,
    'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
    'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
    'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 750,

    # Splash
    'scrapy_splash.SplashCookiesMiddleware': 770,
    'scrapy_splash.SplashMiddleware': 780,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# spider_middleware
SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

# item pipelines
ITEM_PIPELINES = {
    'spider_pro.pipelines.pipelines_file.FilePipeline': 200,
    'spider_pro.pipelines.pipelines_clean.CleanPipeline': 250,
    'spider_pro.pipelines.pipelines_mysql.MysqlPipeline': 300,
}

# Telnet disable
TELNETCONSOLE_ENABLED = True

# Enable or disable extensions
# MYEXT_ITEMCOUNT = 100  # 每爬100条打印一次或者记录一次日志
# EXTENSIONS = {
#     'spider_pro.extensions.SpiderOpenCloseLogging.SpiderOpenCloseLogging': 1,
# }

# spider_por path
spider_pro_path = "/data"

# Scrapy Log setting
LOG_ENABLED = True
LOG_LEVEL = 'INFO'

# Files store
FILES_STORE_PATH = os.path.join(spider_pro_path, "files")
os.makedirs(FILES_STORE_PATH, 0o777, exist_ok=True)
FILES_STORE = FILES_STORE_PATH
IMAGES_STORE = FILES_STORE_PATH

# 静态文件目录statics
IMAGES_PATH = os.path.join(os.path.join(FILES_STORE_PATH, "statics"), "images")
os.makedirs(IMAGES_PATH, 0o777, exist_ok=True)

# download timeout
DOWNLOAD_TIMEOUT = 30

# retry setting
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 400, 403, 404]

# concurrent
CONCURRENT_REQUESTS = 32  # 32 理论上可以支持 每小时10w数据 调式环境设置为1
CONCURRENT_REQUESTS_PER_IP = 1  # 对单个IP进行并发请求的最大值。如果非0,则忽略 CONCURRENT_REQUESTS_PER_DOMAIN 设定,使用该设定。 也就是说,并发限制将针对IP,而不是网站。该设定也影响 DOWNLOAD_DELAY: 如果 CONCURRENT_REQUESTS_PER_IP 非0,下载延迟应用在IP而不是网站上。
REACTOR_THREADPOOL_MAXSIZE = 20

# download delay
DOWNLOAD_DELAY = 1

# not scrapy setting **********************************************************************
# DEBUG_MODE setting
DEBUG_MODE = False
# True:切换为测试数据库，否则为正式库
# True:不启用URL去重，否则不启用

MYSQL_USER_NAME = 'root'
MYSQL_IP = '114.67.84.76'
MYSQL_PASSWORD = 'Ly3sa%@D0$pJt0y6'
MYSQL_PORT = 8050
MYSQL_DB_NAME = 'data_collection'
MYSQL_TEST_DB_NAME = 'test2_data_collection'

# Mysql setting
BUCKET_SIZE = 50
ENGINE_CONFIG = 'mysql+pymysql://{username}:{password}@{ip}:{port}/{db_name}?charset=utf8mb4'.format(**{
    'username': MYSQL_USER_NAME,
    'password': MYSQL_PASSWORD,
    'ip': MYSQL_IP,
    'port': MYSQL_PORT,
    'db_name': MYSQL_DB_NAME,
})
TEST_ENGINE_CONFIG = 'mysql+pymysql://{username}:{password}@{ip}:{port}/{test_db_name}?charset=utf8mb4'.format(**{
    'username': MYSQL_USER_NAME,
    'password': MYSQL_PASSWORD,
    'ip': MYSQL_IP,
    'port': MYSQL_PORT,
    'test_db_name': MYSQL_TEST_DB_NAME,
})

# Redis setting
REDIS_HOST = "114.67.84.76"
MAX_CONNECTIONS = 50
REDIS_PASSWORD = "Ly3sa%@D0$pJt0y6."
NAME_DUPLICATE_URLS = "duplicate_urls"
DEFAULT_ERROR_RATE = 0.0001
DEFAULT_CAPACITY = 300000

# Redis Proxy setting
CURRENT_HTTP_PROXY_MAX = 1  # redis http 最大数量
CURRENT_HTTPS_PROXY_MAX = 1  # redis https 最大数量
TIME_WAIT_PROXY_SLEEP = 10
TIME_MAINTAIN_PROXY_POOL_AGAIN = 10
TIME_EXIT_WHEN_LOCAL_PROXY_SET_EMPTY = 300  # 允许300s内未获得新的ip就退出spider

LOCAL_PROXY_RETRY_TIMES_DICT = {}  # 本地代理池 代理重试次数记录
LOCAL_PROXY_RETRY_MAX_TIMES = 10  # 每个ip只能重试10次，只有10次失败的机会 否则移除代理池

NAME_HTTP_PROXY = "http_proxy"  # redis http代理池
NAME_HTTPS_PROXY = "https_proxy"  # redis https代理池
NAME_HTTP_USED_PROXY = "used:http_proxy"  # 已使用的代理池
NAME_HTTPS_USED_PROXY = "used:https_proxy"  # 已使用的代理池
NAME_RETRY_TIMES = "retry_times"  # 代理重试池

NAME_DELAY_REQUEST = "delay_request"  # 延迟请求
TIME_DELAY_REQUEST = 5  # 延迟请求5s

NAME_HTTP_ABANDON_PROXY = "http_abandon_proxy"  # redis http废弃池
NAME_HTTPS_ABANDON_PROXY = "https_abandon_proxy"  # redis http废弃池

# Upload setting***********************************************************************************
URL_DATA_CENTER = "https://data-center.zhaotx.cn/feign/data/v1/notice/addGatherNotice"
TEST_URL_DATA_CENTER = "http://192.168.1.249:9081/feign/data/v1/notice/addGatherNotice"
ENABLE_AUTO_UPLOAD = False
ENABLE_AUTO_CLEAN = True
ENABLE_CLEAN_ALL_WHEN_START = False
ENABLE_UPLOAD_ALL_WHEN_START = False

ENABLE_PROXY_INFINITE = False
NAME_PROXY_INFINITE = "proxy_infinite"

ENABLE_PROXY_USE = True
ENABLE_URL_DUP_REMOVE_USE = True

# Splash
SPLASH_URL = 'http://114.67.84.76:4300'
