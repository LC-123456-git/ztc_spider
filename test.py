# -*- coding:utf-8 -*-
import json
import random

import re

import requests
from lxml import etree

from scrapyd_timing_post import get_accurate_pub_time
from spider_pro.utils import judge_dst_time_in_interval
from datetime import datetime

start_date = datetime.strptime('2021-05-18', '%Y-%m-%d')




headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    # 'Referer': 'http://jczh.jczh100.com/JCZH//ShowInfo/MoreInfoZbxxNew.aspx',
    # 'Cookie': 'ASP.NET_SessionId=3c4eap0sltg001a315jucs2h; __CSRFCOOKIE=93b8ce4d-48d3-47f3-bb84-ea972f4fece7',
    # 'Content-Type': 'text/html; charset=utf-8'
}


url = "http://www.ccgp-beijing.gov.cn/xxgg/sjzfcggg/sjdygg/t20210615_1351145.html"
s = url[:url.rindex('/') + 1]

# headers = {
#   'Cookie': 'ASP.NET_SessionId=3c4eap0sltg001a315jucs2h; __CSRFCOOKIE=93b8ce4d-48d3-47f3-bb84-ea972f4fece7'
# }

res = requests.get(url=url, headers=headers).text




# # F045F8EF177F052A54CB4862F9F4DC6280EBCA3DE7D7EBF439EBF3C635D5F7EF51F43ADFB0E07CE2      M1301000205507222003
# # 92011A412F701F129EF90DAE9DB841D67D76B0ED6635AD97AAC00AEC94DFEFDACC3BF9CBF80C8F34D2D6FE9A28DABBC36C4717C31596875691206451068E99DE    3ba50541a6c4443c9bd9a38eee4c785b
#
# data = {
#     'schemaVersion': 'V60.02',
#     'businessKeyWord': 'winBidBulletin',
#     'tenderProjectCode': 'A9AA61A84CB8BD45401019D24C259B0E2B501F733E620C5BC39DE07D2416D677385DF88772CFA30B',
#     'businessObjectName': '秦皇岛市第一医院综合门诊楼改扩建工程（含新建中心院区儿科专科建设工程项目）扶梯采购(二次)中标结果公告',
#     'businessId': '33D16B293695A70401DA741693C66292DB54AE5010B9B293C340C42939B287B423CD9418B0362859781CEC0DAC2ECF9DDD9B767BE5B7DDF821FA539D3542DFA4'
# }
_value = '按基准价浮动-24.10%'
if re.findall('[0-9 .].*', _value):
	print(re.findall('.*^\-([0-9 .])?%', _value)[0])









# pl_reg = '项\s*目\s*名\s*称[:|：]\s*[,|，](?P<{}>.*[u4e00-u9fa5].*?)[)|）]'.format(keys)
# pl_reg = '\s*<.*>[\u4e00-\u9fa5 0-9 a-z A-Z]*?[: ：\s]+?[\+]*?([\u4e00-\u9fa5 0-9 a-z A-Z （ ） ( ) - 、]+?)\+</.*>'
# pl_reg = fr'{keys}<.*>\s*[\u4e00-\u9fa5 0-9 a-z A-Z （ ） ( ) - 、]+?</.*>'
# pl_com = re.compile(pl_reg)
# ret = [m.groupdict() for m in re.finditer(pl_com, doc)]
# data = {}
# if ret:
#     ret = ret[-1]
#     data['keys'] = ''.join(ret.get('{}'.format(keys), '')).replace(',', '')

# print(data)
#
#         data['liaison'] = re.findall('(.*?)\/\d+', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
#         data['contact_information'] = re.findall('.*\/(\d{11})', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
#         data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
#         data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''
#
#     elif re.findall('(.*)\s*\d{4}-\d{7,8}|\d{11}', ''.join(ret.get('liaison', '')).replace(',', '').strip()):
#         data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
#         data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''
#         data['liaison'] = re.findall('(.*)\s*\d{4}-\d{7,8}|\d{11}', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
#         data['contact_information'] = re.findall('.*\s*(\d{4}-\d{7,8}|\d{11})', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''

    # elif re.findall('(.*?)\d{3,4}-\d{7,8}?|\d{11}', ''.join(ret.get('contact_information', '')).replace(',', '').strip()):
    #     data['liaison'] = re.findall('(.*?)\d+', ''.join(ret.get('contact_information', '')).replace(',', '').strip())[0] or ''
    #     data['contact_information'] = re.findall('.*(\d{11})', ''.join(ret.get('contact_information', '')).replace(',', '').strip())[0] or ''
    #     data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
    #     data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''

#     else:
#         data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
#         data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''
#         data['contact_information'] = ''.join(ret.get('contact_information')).replace(',', '').strip() or ''
#         data['liaison'] = ''.join(ret.get('liaison', '')).replace(',', '').strip() or ''
# #
#
#


# <p align="right" style='margin: 0cm 0cm 0pt; text-align: right; line-height: 150%; text-indent: 24pt; font-family: "Times New Roman","serif"; font-size: 10.5pt; -ms-text-justify: inter-ideograph;'><span style="line-height: 150%; font-family: 宋体; font-size: 12pt;">嘉兴市嘉南投资发展有限公司<span>                                                                                                                                
#             </span>浙江中惠工程管理有限公司</span></p>
# <p style='margin: 0cm 0cm 0pt; text-align: justify; font-family: "Times New Roman","serif"; font-size: 10.5pt; -ms-text-justify: inter-ideograph;'><span style="font-family: 宋体; font-size: 12pt;">                                                   
# </span><span style="font-family: 宋体; font-size: 12pt;">二〇二一年五月十二日</span></p></div>"""
# sinter = content.replace("</td>", " </td>").strip()
# keys = ["项目名称"]
# keys = ["项目名称", "招标项目", "工程名称", "招标工程项目", "项目编号", "招标项目编号", "招标编号", "招标代理:", "招标代理：", "招标代理机构",
#         "中标价格", "成交价格", "中标单位", "中标日期", "联系电话", "项目经理（负责人）"]

# <tr style="height: 18.15pt;">
#       <td width="54" valign="center" style="width: 40.55pt; padding: 0pt 5.4pt; border-width: 1pt; border-style: solid; border-color: windowtext;">
#       <p class="MsoNormal" align="center" style='margin: 0pt 0pt 0.0001pt; text-align: center; font-family: "Times New Roman"; font-size: 10.5pt; line-height: 22pt;'><span style="font-family: 微软雅黑; font-size: 10.5pt;">标段</span><span style="font-family: 微软雅黑; font-size: 10.5pt;"><p></p></span></p>
#       </td>
#       <td width="273" valign="center" style="width: 205.15pt; padding: 0pt 5.4pt; border-left: none; border-right: 1pt solid windowtext; border-top: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
#       <p class="MsoNormal" align="center" style='margin: 0pt 0pt 0.0001pt; text-align: center; font-family: "Times New Roman"; font-size: 10.5pt; line-height: 22pt;'><span style="font-family: 微软雅黑; font-size: 10.5pt;">项目名称</span><span style="font-family: 微软雅黑; font-size: 10.5pt;"><p></p></span></p>
#       </td>
#       <td width="47" valign="center" style="width: 35.45pt; padding: 0pt 5.4pt; border-left: none; border-right: 1pt solid windowtext; border-top: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
#       <p class="MsoNormal" align="center" style='margin: 0pt 0pt 0.0001pt; text-align: center; font-family: "Times New Roman"; font-size: 10.5pt; line-height: 22pt;'><span style="font-family: 微软雅黑; font-size: 10.5pt;">单位</span><span style="font-family: 微软雅黑; font-size: 10.5pt;"><p></p></span></p>
#       </td>
#       <td width="56" valign="center" style="width: 42.55pt; padding: 0pt 5.4pt; border-left: none; border-right: 1pt solid windowtext; border-top: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
#       <p class="MsoNormal" align="center" style='margin: 0pt 0pt 0.0001pt; text-align: center; font-family: "Times New Roman"; font-size: 10.5pt; line-height: 22pt;'><span style="font-family: 微软雅黑; font-size: 10.5pt;">数量</span><span style="font-family: 微软雅黑; font-size: 10.5pt;"><p></p></span></p>
#       </td>
#       <td width="126" valign="center" style="width: 94.95pt; padding: 0pt 5.4pt; border-left: none; border-right: 1pt solid windowtext; border-top: 1pt solid windowtext; border-bottom: 1pt solid windowtext;">
#       <p class="MsoNormal" align="center" style='margin: 0pt 0pt 0.0001pt; text-align: center; font-family: "Times New Roman"; font-size: 10.5pt; line-height: 22pt;'><span style="font-family: 微软雅黑; font-size: 10.5pt;">预算金额（元）</span><span style="font-family: 微软雅黑; font-size: 10.5pt;"><p></p></span></p>
#       </td>
#     </tr>




# </font>A3304010550000200<font face="宋体">
# for key in keys:
#     all_results = re.findall(fr"{key}</.*?>(.*?)</.*>", content)
#     if all_results:
#         for item in all_results:
#             value = item.split(">")[-1].split(">")[0]
#             if value.strip():
#                 print(value.strip())



    # if re.search(fr"{key}", content):
    #     # 匹配带冒号开始的文本内容
    #     all_results = re.findall(fr"{key}[:|：].*</.*>", content)
    #     if all_results:
    #         for item in all_results:
    #             value = item.split("：")[-1].split("<")[-1]
    #             if value.strip():
    #                 print(value.strip())
    #             # tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
    #             tag = 'span'
    #             if value_str := re.search(fr"{key}[:|：]</{tag}>(.*)?<{tag}.*?>(.*)?</{tag}>", content):
    #                 value = value_str.group().split(">")[-2].split("</")[0]
    #                 if value.strip():
    #                     print(value.strip())





    # all_results = re.findall(fr"{key}\s+?<", sinter)
    # if all_results:
    #     for item in all_results:
    #         value_list = item.split(" ")
    #         for v_item in value_list:
    #             if v_item.strip():
    #                 print(v_item.strip())
    #
    # all_results = re.findall(fr"{key}\s*(.*?)[)|）]", sinter)
    # if all_results:
    #     for item in all_results:
    #         value = re.findall("</.*>(.*)<.*>", item)
    #         print(value)
    # all_results = re.findall(fr"{key}\s+?(.*?)[(|（]", sinter)
    # if all_results:
    #     for item in all_results:
    #         value = re.findall('<.*>(.*?)</.*>', item)[0]
    #         if value.strip():
    #             print(value)
    #
    # all_results = re.findall(fr"{key}[:|：].*?</.*?>", sinter)
    # if all_results:
    #     for item in all_results:
    #         if item.split(":")[-1].split("：")[-1]:
    #             value = re.findall('<.*>(.*)</.*>', item.split(":")[-1].split("：")[-1])[0]
    #         else:
    #             value = item.split(":")[-1].split("：")[-1].split("<")[0]
    #         if value.strip():
    #             print(value.strip())
    #
    #         # tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
    #         # if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
    #         #     value = value_str.group().split(">")[-2].split("</")[0]
    #         #     if value.strip():
    #         #         print(value.strip())
    #
    # # # 匹配带空格开始的文本内容
    # # all_results = re.findall(fr"{key}(\s+?<)", content)
    # # if all_results:
    # #     for item in all_results:
    # #         value_list = item.split(" ")
    # #         for v_item in value_list:
    # #             if v_item.strip():
    # #                 print(v_item.strip())
    #
    #
    # all_results = re.findall(fr"{key}</.*?>", sinter)
    # if all_results:
    #     for item in all_results:
    #         tag = item.split("</")[-1].split(">")[0]
    #         if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", sinter):
    #             value = value_str.group().split(">")[-2].split("</")[0]
    #             if value.strip():
    #                 print(value.strip())
    # all_results = re.findall(fr"{key}.*?</.*>\s*<.*>.*?</.*>", sinter)
    # if all_results:
    #     for itme in all_results:
    #         if re.findall(fr'{key}[:|：](.*?)<', itme):
    #             value = re.findall(fr'{key}[:|：](.*?)<', itme)[0]
    #             if value.strip():
    #                 print(value)
    #         else:
    #             value = ''.join(re.findall('<.*>(.*?)</.*>', itme)[-1]).strip()
    #             if value.strip():
    #                 print(value)

