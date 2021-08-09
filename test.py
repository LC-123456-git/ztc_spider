# -*- coding:utf-8 -*-

import json, pytesseract
import re
import time
from functools import wraps

import requests, base64, hashlib

import datetime
import xmltodict
from lxml import etree
from pyquery import PyQuery

# start_date = datetime.strptime('2021-05-18', '%Y-%m-%d')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Cookie': 'ASP.NET_SessionId=pzm3imhg2m1yghjooey5q0m5; __RequestVerificationToken=grgPkZaRHX1JnJzHv_GrKkUxX-MCBqKs1-cW-h8Lf9gjHG8BwkQE_rRklJAZxw3lBSt91jSCbdCtOlS42mDnsiKHwu23wTxwMPAgEpUWiJg1'
    }
r_dict = {'col': '1', 'appid': '1', 'webid': '3558', 'path': '/', 'sourceContentType': '1',
          'unitid': '6208573', 'webname': '武义县人民政府', 'permissiontype': '0', 'columnid': '1229150642'}
# r_dict = {'col': '1', 'appid': '1', 'webid': '2761', 'path': '/', 'sourceContentType': '1', 'unitid': '6496286', 'webname': '浙江新昌政府门户网站', 'permissiontype': '0', 'columnid': '1637586'}

url = "http://jyzx.sanmen.gov.cn/Detail/17779"
# res = requests.get(url=url, headers=headers)
# res = requests.post(url=url, headers=headers, data=r_dict)

sit = '吕婷(0571)-64780061 13566668888'
phton = '13499990000'

name = '最高限价20万元，20天内完成供货。'
# nums = ','.join(re.findall('[\d \- （）\( \)]+', sit))
re_string = r'最高限价(.*?[(元)|(万元)])'
com = re.compile(re_string)
result = com.findall(name)


# stre = '1583215'
# dd = stre if u'\u4e00' <= stre <= u'\u9fff' else 'no'
# print(dd)

fff = r'受(.*[(公司)|(单位)|(公安局)])[^, 。，]*?委托'
queue_list = [1, 2]
key_list = ['ff', 'gg']
lll_list = ['yy', 'pp']
for name, key, ll in zip(queue_list, key_list, lll_list):
    print(name, key, ll)

