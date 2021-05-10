'''
author: miaokela
Date: 2021-05-08 11:17:47
LastEditTime: 2021-05-08 11:17:48
Description: 调试爬虫系统
'''
from scrapy import cmdline
import sys
import os
# 获取当前脚本路径
dirpath = os.path.dirname(os.path.abspath(__file__))
# 添加环境变量
sys.path.append(dirpath)

if __name__ == '__main__':
    # cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider -a sdt=2021-01-01 -a edt=2021-04-30".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3320_cangnan_spider".split(" "))
    cmdline.execute("scrapy crawl province_50_xinjiang_spider".split(" "))

    
