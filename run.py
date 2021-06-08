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
    # cmdline.execute("scrapy crawl qcc_crawler".split(" "))
    # cmdline.execute("scrapy crawl province_67_yangguangyizhao_spider -a sdt=2021-01-01 -a edt=2021-05-31".split(" "))
    # cmdline.execute("scrapy crawl province_65_guoepingtai_spider -a sdt=2021-01-01 -a edt=2021-06-03".split(" "))
    # cmdline.execute("scrapy crawl province_65_guoepingtai_spider".split(" "))
    # cmdline.execute("scrapy crawl province_67_yangguangyizhao_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3322_anji_spider -a sdt=2021-05-27 -a edt=2021-05-28".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3302_zjcaigou_spider".split(" "))
    # cmdline.execute("scrapy crawl province_68_qilu_spider".split(" "))
    # cmdline.execute("scrapy crawl province_53_bilian_spider".split(" "))
    # cmdline.execute("scrapy crawl province_78_zhuzhaixiushan_spider -a sdt=2021-01-01 -a edt=2021-06-08".split(" "))
    cmdline.execute("scrapy crawl province_77_zhaobide_spider -a sdt=2021-01-01 -a edt=2021-06-08".split(" "))
    