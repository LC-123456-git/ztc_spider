# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-04-21
# @Describe: 诸暨市公共资源交易网 - 全量/增量脚本
import re
import math
import json
import scrapy
from lxml import etree
import random
import datetime
from urllib import parse

import xmltodict
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3316_zhuji_spider'
    area_id = "3316"
    domain_url = "http://www.zhuji.gov.cn"
    query_url = "http://www.zhuji.gov.cn/col/col{}/index.html"
    base_url = 'http://www.zhuji.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    allowed_domains = ['zhuji.gov.cn']
    area_province = "浙江-绍兴市-诸暨市公共资源交易服务平台"

    # 招标预告
    list_advance_notice_num = ['1388406', "1679843"]
    # 招标公告
    list_notice_category_num = ['1388402', '1388407', '1388411', '1679845', '1388415', '1388419']
    # 中标公告
    list_win_notice_category_num = ['1388404', '1388409', '1388413', '1679847', '1388417', '1388421']
    # 中标预告
    list_win_advance_notice_num = ['1388403', '1388412', '1679846', '1388416']
    # 其他公告
    list_others_notice_num = ['1693203', '1388422']
    all_list = list_advance_notice_num+list_notice_category_num+list_win_notice_category_num+list_win_advance_notice_num+\
               list_others_notice_num
    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '2745',
        'path': '/',
        # 'columnid': '1518855',
        'sourceContentType': '1',
        'unitid': '6167830',
        'webname': '诸暨市政府门户网站',
        'permissiontype': '0'
    }

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for code in self.all_list:
            info_dict = self.r_dict | {'columnid': str(code)}
            yield scrapy.FormRequest(url=self.base_url, formdata=info_dict, priority=5, callback=self.parse_url,
                                     meta={"info_dict": info_dict, "code": code})

    def parse_url(self, response):
        try:
            url = response.url
            code = response.meta["code"]
            info_dict = self.r_dict | {'columnid': code}
            total = response.xpath('//datastore/totalrecord/text()').get()
            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            pages = math.ceil(int(total)/120)
            startrecord = 0
            endrecord = 120
            for num in range(1, int(pages)+1):
                if num == 1:
                    startrecord = 1
                    endrecord = 120
                else:
                    startrecord += 120
                    endrecord += 120
                yield scrapy.FormRequest(url=self.base_url.format(startrecord, endrecord), priority=8, formdata=info_dict,
                                         callback=self.parse_data_urls, meta={"info_dict": info_dict,
                                                                         "code": code})
            # li_gcjs_list = response.xpath("//ul[@id='two_fr_tit']/li")
            #
            # li_list = response.xpath('//ul[@class="ty-ul fr"]/li')
            # for li in li_list:
            #     type_url = self.domain_url + li.xpath('./a/@href').get()
            #     code = re.findall('(\d+)', type_url)[0]
            #     if code in self.list_advance_notice_num:
            #         noticn = const.TYPE_ZB_ADVANCE_NOTICE
            #     elif code in self.list_notice_category_num:
            #         noticn = const.TYPE_ZB_NOTICE
            #     elif code in self.list_win_notice_category_num:
            #         noticn = const.TYPE_WIN_NOTICE
            #
            #     elif code in self.list_win_advance_notice_num:
            #         noticn = const.TYPE_WIN_ADVANCE_NOTICE
            #     elif code in self.list_others_notice_num:
            #         noticn = const.TYPE_OTHERS_NOTICE
            #     else:
            #         noticn = 'null'
            #     if noticn != 'null':
            #         info_dict = self.r_dict | {'columnid': str(code)}
            #         yield scrapy.FormRequest(url=self.base_url, formdata=info_dict, callback=self.parse_data_urls,
            #                              meta={'noticn': noticn, 'info_dict': info_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 parse_url{e} {response.url=}")

    def parse_data_urls(self, response):
        xmlparse = xmltodict.parse(response.text)
        jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
        noticn = response.meta['code']
        if noticn in self.list_advance_notice_num:
            notice_type = const.TYPE_ZB_ADVANCE_NOTICE
        elif noticn in self.list_notice_category_num:
            notice_type = const.TYPE_ZB_NOTICE
        elif noticn in self.list_win_notice_category_num:
            notice_type = const.TYPE_WIN_NOTICE
        elif noticn in self.list_win_advance_notice_num:
            notice_type = const.TYPE_WIN_ADVANCE_NOTICE
        elif noticn in self.list_others_notice_num:
            notice_type = const.TYPE_OTHERS_NOTICE
        else:
            notice_type = const.TYPE_UNKNOWN_NOTICE
        for info in jsonstr:
            doc = etree.HTML(info)
            pub_time = doc.xpath("//td[@class='bt_time']")[0].text
            info_url = doc.xpath("//a/@href")[0]
            title_name = doc.xpath("//a/@title")[0]
            info_url = self.domain_url + info_url
            yield scrapy.Request(url=info_url, callback=self.parse_item, priority=10,
                                 meta={'pub_time': pub_time, 'noticn': noticn, "title_name": title_name, "notice_type":
                                     notice_type})
    # def parse_data_urls(self, response):
    #     try:
    #         print("~~~~~~~~~~~~~~~~~~~~~~~~")
    #         print(xmltodict.parse(response.text))
    #         base_url = 'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
    #         if self.enable_incr:
    #             pass
    #             # xmlparse = xmltodict.parse(response.text)
    #             # jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
    #             # num = 0
    #             # startrecord = 1
    #             # endrecord = 120
    #             # for info in jsonstr:
    #             #     pub_time = ''.join(re.findall('<span>(.*)</span>', info)[0]).replace('[', '').replace(']', '')
    #             #     pub_time = get_accurate_pub_time(pub_time)
    #             #     x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
    #             #     if x:
    #             #         num += 1
    #             #         total = int(len(jsonstr))
    #             #         if total == None:
    #             #             return
    #             #         self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
    #             #     if num >= len(jsonstr):
    #             #         startrecord += 120
    #             #         endrecord += 120
    #             #     else:
    #             #         startrecord = 1
    #             #         endrecord = 120
    #             #     yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord),
    #             #                              formdata=response.meta['info_dict'],
    #             #                              callback=self.parse_info, meta={'noticn': response.meta['noticn']})
    #         else:
    #             total = response.xpath('//datastore/totalrecord/text()').get()
    #             self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
    #             pages = math.ceil(int(total)/120)
    #             startrecord = 0
    #             endrecord = 120
    #             for num in range(1, int(pages)+1):
    #                 if num == 1:
    #                     startrecord = 1
    #                     endrecord = 120
    #                 else:
    #                     startrecord += 120
    #                     endrecord += 120
    #                 yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord), formdata=response.meta['info_dict'],
    #                                      callback=self.parse_info, meta={"info_dict": response.meta["info_dict"],
    #                                                                      "noticn": response.meta["noticn"]})
    #     except Exception as e:
    #         self.logger.error(f"初始总页数提取错误 : {response.meta=} {e} {response.url=}")
    #
    # def parse_info(self, response):
    #     try:
    #         xmlparse = xmltodict.parse(response.text)
    #         jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
    #         for info in jsonstr:
    #             pub_time = ''.join(re.findall('<span>(.*)</span>', info)[0]).replace('[', '').replace(']', '')
    #             info_url = self.domain_url + re.findall('<a href="(.*)" .*>', info)[0]
    #
    #             yield scrapy.Request(url=info_url, callback=self.parse_item, meta={'pub_time': pub_time,
    #                                                                                'noticn': response.meta['noticn']})
    #
    #     except Exception as e:
    #         self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            title_name = response.meta["title_name"]
            pub_time = response.meta['pub_time']
            noticn = response.meta["noticn"]
            if noticn in ["1388402", "1388403", "1388404"]:
                classifyShow = "建设工程"
            elif noticn in ["1388406", "1388407", "1388409", "1693203"]:
                classifyShow = "政府采购"
            elif noticn in ["1388411", "1388412", "1388413"]:
                classifyShow = "要素资源"
            elif noticn in ["1679843", "1679845", "1679846", "1679847"]:
                classifyShow = "公告代发"
            elif noticn in ["1388415", "1388417", "1388418"]:
                classifyShow = "镇街部门交易信息"
            else:
                classifyShow = "农村产权"
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'候选人|评标结果', title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'终止|中止|异常|废标|流标', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|更正|澄清|修正|补充|延期|答疑', title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'成交|成果|中标', title_name):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'招标|谈判|磋商', title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'预审结果', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice_type']
            content = response.xpath('//div[@class="main-fl bt-left"]').get()
            doc = etree.HTML(content)
            els = doc.xpath('//div[@class="main-fl-riqi-1 bt-left"]') + doc.xpath("//div[@class='main-fl-gn bt-padding-right-20 bt-padding-left-20']")
            # els_1 = doc.xpath("//div[@class='main-fl-gn bt-padding-right-20 bt-padding-left-20']")
            # els_2 = doc.xpath('//div[class="printer bt-right"]')
            for el in els:
                el.getparent().remove(el)
                content = etree.tounicode(doc)
            # content = re.sub(fr'|打印|关闭|', '', content)



            files_path = {}
            if dict := response.xpath("//ul[@class='fjxx']/li"):
                for itme in dict:
                    if 'https' in itme.xpath('./p/a/@href').get():
                        value = itme.xpath('./p/a/@href').get()
                    else:
                        value = self.base_url + itme.xpath('./p/a/@href').get()
                    keys = itme.xpath('./p/a/text()').get()
                    files_path[keys] = value
            # if dict := response.xpath('//*[@id="dlstAttachFile"]/tbody/tr/td/a') or response.xpath('//table[@id="zfcg_caigouyaosugongshi_detail_dlstattachfile"]//a') or\
            #         response.xpath('//div[@id="zoom"]//a'):
            #     dict = response.xpath('//td[@valign="top"]/table[@id="dlstAttachFile"]//a') or response.xpath('//table[@id="zfcg_caigouyaosugongshi_detail_dlstattachfile"]//a') or response.xpath('//div[@id="zoom"]//a')
            #     num = 1
            #     for itme in dict:
            #         if 'http' in itme.xpath("./@href").get():
            #             value = itme.xpath("./@href").get()
            #         else:
            #             value = self.base_url + itme.xpath("./@href").get()
            #         key_name = ['png', 'jpg', 'jpeg', 'doc', 'docx', 'pdf', 'xls']
            #         key_list = ['www.sxztb.gov.cn', 'yyz18577@163.com', 'www.zjzfcg.gov.cn', 'http://www.sxztb.gov.cn']
            #         if itme.xpath("./font/text()").get() or itme.xpath("./span/text()").get() or itme.xpath('./text()').get():
            #             keys = itme.xpath("./font/text()").get() or itme.xpath("./span/text()").get() or itme.xpath('./text()').get()
            #             if keys not in key_list:
            #                 files_path[keys] = value
            #         elif value[value.rindex('.') + 1:] in key_name:
            #             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            #             files_path[keys] = value
            #         else:
            #             pass
            #         num += 1

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3316_zhuji_spider".split(" "))


