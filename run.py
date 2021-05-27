"""
@file          :run.py
@description   :调试爬虫系统
@date          :2021/05/12 16:04:06
@author        :miaokela
@version       :1.0
"""
from scrapy import cmdline
import sys
import os
# 获取当前脚本路径
dirpath = os.path.dirname(os.path.abspath(__file__))
# 添加环境变量
sys.path.append(dirpath)

if __name__ == '__main__':
    # cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider -a sdt=2021-01-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl province_00_quanguo_spider -a sdt=2021-02-13 -a edt=2021-03-13 -s DOWNLOAD_DELAY=0 -s CONCURRENT_REQUESTS_PER_IP=20".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3323_xiaoshan_spider -a sdt=2020-08-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3328_changshan_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3327_pingyang_spider".split(" "))
    