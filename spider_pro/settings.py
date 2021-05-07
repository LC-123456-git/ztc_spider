#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-23
# @Describe: Scrapy settings for spider project
import os
import datetime
import logging.config

# project bot name
BOT_NAME = 'spider_pro'

# project spider modules
SPIDER_MODULES = ['spider_pro.spiders']
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
    # 'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 100,
}

# item pipelines
ITEM_PIPELINES = {
    'spider_pro.pipelines.pipelines_file.FilePipeline': 200,
    'spider_pro.pipelines.pipelines_clean.CleanPipeline': 250,
    'spider_pro.pipelines.pipelines_mysql.MysqlPipeline': 300,
}

# Telnet disable
TELNETCONSOLE_ENABLED = False

# Enable or disable extensions
# MYEXT_ITEMCOUNT = 100  # 每爬100条打印一次或者记录一次日志
# EXTENSIONS = {
#     'spider_pro.extensions.SpiderOpenCloseLogging.SpiderOpenCloseLogging': 1,
# }

# spider_por path
spider_pro_path = os.path.dirname(os.path.abspath(__file__))

# Scrapy Log setting
logs_spider_path = os.path.join(spider_pro_path, "logs")
os.makedirs(logs_spider_path, 0o777, exist_ok=True)
# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {'simple': {'class': 'logging.Formatter',
#                               'format': '%(asctime)s [%(name)s] %(levelname)s | %(message)s',
#                               'datefmt': '%Y-%m-%d %H:%M:%S'}},
#     'handlers': {'console': {'class': 'logging.StreamHandler',
#                              'level': 'INFO',
#                              'formatter': 'simple',
#                              'stream': 'ext://sys.stdout'},
#                  'pipelines_mysql_handler': {
#                      'class': "logging.handlers.TimedRotatingFileHandler",
#                      'level': "INFO",
#                      'formatter': "simple",
#                      'filename': os.path.join(logs_spider_path, 'pipelines_mysql.log'),
#                      'when': "MIDNIGHT",
#                      'interval': 1,
#                      'backupCount': 3,
#                      'encoding': "utf8",
#                  },
#                  'proxy_handle': {
#                      'class': "logging.handlers.TimedRotatingFileHandler",
#                      'level': "INFO",
#                      'formatter': "simple",
#                      'filename': os.path.join(logs_spider_path, 'middleware_proxy.log'),
#                      'when': "MIDNIGHT",
#                      'interval': 1,
#                      'backupCount': 3,
#                      'encoding': "utf8",
#                  }
#                  },
#     'loggers': {'pipelines_mysql': {'handlers': ['pipelines_mysql_handler'],
#                                     'level': 'INFO',
#                                     'propagate': True},
#                 'middleware_proxy': {'handlers': ['proxy_handle'],
#                                      'level': 'INFO',
#                                      'propagate': False}
#                 },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO'
#     }
# })
today_date = datetime.datetime.now()
LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
LOG_FILE = f"{logs_spider_path}/info_{datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '_')}.log"
LOG_LEVEL = 'INFO'
# LOG_LEVEL = 'DEBUG'
for root, dirs, files in os.walk(logs_spider_path):
    for item in files:
        if "info_" in item and os.path.isfile(os.path.join(root, item)):
            if (datetime.datetime.now() - datetime.datetime.fromisoformat(
                    item.split("info_")[1].split(".")[0].replace("_", "-"))).days >= 3:
                os.remove(os.path.join(root, item))

# Files store
FILES_STORE_PATH = os.path.join(spider_pro_path, "files")
os.makedirs(FILES_STORE_PATH, 0o777, exist_ok=True)
FILES_STORE = FILES_STORE_PATH
IMAGES_STORE = FILES_STORE_PATH

# download timeout
DOWNLOAD_TIMEOUT = 10

# retry setting
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 400, 403, 404]

# concurrent
CONCURRENT_REQUESTS = 32  # 32 理论上可以支持 每小时10w数据 调式环境设置为1
CONCURRENT_REQUESTS_PER_IP = 5     # 1
REACTOR_THREADPOOL_MAXSIZE = 20

# download delay   延时下载
DOWNLOAD_DELAY = 2

# not scrapy setting **********************************************************************
# DEBUG_MODE setting
DEBUG_MODE = True
# "True":切换为测试数据库，否则为正式库
# "True":不启用URL去重，否则不启用

# Mysql setting
BUCKET_SIZE = 10
ENGINE_CONFIG = 'mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/data_collection?charset=utf8mb4'
TEST_ENGINE_CONFIG = 'mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4'

# Redis setting
REDIS_HOST = "114.67.84.76"
MAX_CONNECTIONS = 50
REDIS_PASSWORD = "Ly3sa%@D0$pJt0y6."
NAME_DUPLICATE_URLS = "duplicate_urls"
DEFAULT_ERROR_RATE = 0.0001
DEFAULT_CAPACITY = 100000

# Redis Proxy setting
CURRENT_HTTP_PROXY_MAX = 1  # redis http 最大数量
CURRENT_HTTPS_PROXY_MAX = 1  # redis https 最大数量
TIME_WAIT_PROXY_SLEEP = 10
TIME_MAINTAIN_PROXY_POOL_AGAIN = 10
TIME_EXIT_WHEN_LOCAL_PROXY_SET_EMPTY = 300  # 允许300s内未获得新的ip就退出spider

LOCAL_PROXY_RETRY_TIMES_DICT = {}  # 本地代理池 代理重试次数记录
LOCAL_PROXY_RETRY_MAX_TIMES = 2  # 每个ip只能重试10次，只有10次失败的机会 否则移除代理池

NAME_HTTP_PROXY = "http_proxy"  # redis http代理池
NAME_HTTPS_PROXY = "https_proxy"  # redis https代理池
NAME_HTTP_USED_PROXY = "used:http_proxy"  # 已使用的代理池
NAME_HTTPS_USED_PROXY = "used:https_proxy"  # 已使用的代理池
NAME_RETRY_TIMES = "retry_times"  # 代理重试池

NAME_DELAY_REQUEST = "delay_request"  # 延迟请求
TIME_DELAY_REQUEST = 5  # 延迟请求5s

NAME_HTTP_ABANDON_PROXY = "http_abandon_proxy"  # redis http废弃池
NAME_HTTPS_ABANDON_PROXY = "https_abandon_proxy"  # redis https废弃池

# Upload And Clean setting*****************************************************************
URL_DATA_CENTER = "https://data-center.zhaotx.cn/feign/data/v1/notice/addGatherNotice"
TEST_URL_DATA_CENTER = "http://192.168.1.249:9081/feign/data/v1/notice/addGatherNotice"
ENABLE_AUTO_UPLOAD = False
ENABLE_AUTO_CLEAN = True
ENABLE_CLEAN_ALL_WHEN_START = False  # 异常自动恢复清洗功能
ENABLE_UPLOAD_ALL_WHEN_START = False  # 异常自动恢复上传功能

ENABLE_PROXY_INFINITE = False
NAME_PROXY_INFINITE = "proxy_infinite"

ENABLE_PROXY_USE = True  # 启用代理
ENABLE_URL_DUP_REMOVE_USE = False

DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'