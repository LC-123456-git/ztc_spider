"""
@file          :run.py
@description   :调试爬虫系统
@date          :2021/05/12 16:04:06
@author        :miaokela
@version       :1.0
"""
from scrapy import cmdline


if __name__ == '__main__':
    # cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider -a sdt=2021-01-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl province_00_quanguo_spider -a sdt=2021-02-13 -a edt=2021-03-13 -s DOWNLOAD_DELAY=0 -s CONCURRENT_REQUESTS_PER_IP=20".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3323_xiaoshan_spider -a sdt=2020-08-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3328_changshan_spider -a sdt=2018-05-01 -a edt=2018-12-30".split(" "))
    # cmdline.execute("scrapy crawl tyc_crawler".split(" "))
    cmdline.execute("scrapy crawl province_52_pinming_spider -a sdt=2021-04-01 -a edt=2021-05-10".split(" "))
    