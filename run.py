'''
author: miaokela
Date: 2021-05-08 11:17:47
LastEditTime: 2021-05-08 11:17:48
Description: 
'''

from scrapy import cmdline

if __name__ == '__main__':
    cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider -a sdt=2021-01-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider".split(" "))
