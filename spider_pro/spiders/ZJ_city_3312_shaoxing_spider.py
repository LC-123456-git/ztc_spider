# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-09
# @Describe: 绍兴市公共资源交易网 - 全量/增量脚本
import re
import math
import json
import scrapy
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
    name = 'ZJ_city_3312_shaoxing_spider'
    area_id = "3312"
    domain_url = "http://ggb.sx.gov.cn"
    query_url = "http://ggb.sx.gov.cn/index.html"
    base_url = 'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=45&perpage=15'
    allowed_domains = ['ggb.sx.gov.cn']
    area_province = "浙江-绍兴市公共资源交易服务平台"

    # 招标预告
    list_advance_notice_num = ['1518859']
    # 招标公告
    list_notice_category_num = ['1518854', '1518860', '1518864', '1518870', '1518872', '1518878']
    # 中标公告
    list_win_notice_category_num = ['1518857', '1518861', '1518866', '1518871', '1518873', '1518879']
    # 招标异常
    list_alteration_category_num = ['1518862']
    # 招标变更
    list_zb_abnormal_num = []
    # 中标预告
    list_win_advance_notice_num = ['1518856']
    # 资格预审结果公告
    list_qualification_num = ['1518855']
    # 其他公告
    list_others_notice_num = ['1228970908', '1518865']
    r_dict = {
        'col': '1',
        'appid': '1',
        'webid': '3003',
        'path': '/',
        # 'columnid': '1518855',
        'sourceContentType': '1',
        'unitid': '4685909',
        'webname': '绍兴公共资源交易网',
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
        # all_info_url = 'http://ggb.sx.gov.cn/art/2011/9/7/art_1518856_20424370.html'
        # yield scrapy.Request(url=all_info_url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_url)

    def parse_url(self, response):
        try:
            li_list = response.xpath('//ul[@class="ty-ul fr"]/li')
            for li in li_list:
                type_url = self.domain_url + li.xpath('./a/@href').get()
                code = re.findall('(\d+)', type_url)[0]
                if code in self.list_advance_notice_num:
                    noticn = const.TYPE_ZB_ADVANCE_NOTICE
                elif code in self.list_notice_category_num:
                    noticn = const.TYPE_ZB_NOTICE
                elif code in self.list_win_notice_category_num:
                    noticn = const.TYPE_WIN_NOTICE
                elif code in self.list_alteration_category_num:
                    noticn = const.TYPE_ZB_ABNORMAL
                elif code in self.list_win_advance_notice_num:
                    noticn = const.TYPE_WIN_ADVANCE_NOTICE
                elif code in self.list_qualification_num:
                    noticn = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif code in self.list_others_notice_num:
                    noticn = const.TYPE_OTHERS_NOTICE
                else:
                    noticn = 'null'
                if noticn != 'null':
                    info_dict = self.r_dict | {'columnid': str(code)}
                    yield scrapy.FormRequest(url=self.base_url, formdata=info_dict, callback=self.parse_data_urls,
                                         meta={'noticn': noticn, 'info_dict': info_dict})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            base_url = 'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=40'
            if self.enable_incr:
                xmlparse = xmltodict.parse(response.text)
                jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
                num = 0
                startrecord = 1
                endrecord = 120
                for info in jsonstr:
                    pub_time = ''.join(re.findall('<span>(.*)</span>', info)[0]).replace('[', '').replace(']', '')
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(jsonstr))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    if num >= len(jsonstr):
                        startrecord += 120
                        endrecord += 120
                    else:
                        startrecord = 1
                        endrecord = 120
                    yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord),
                                             formdata=response.meta['info_dict'],
                                             callback=self.parse_info, meta={'noticn': response.meta['noticn']})
            else:
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
                    yield scrapy.FormRequest(url=base_url.format(startrecord, endrecord), formdata=response.meta['info_dict'],
                                         callback=self.parse_info, meta={'noticn': response.meta['noticn']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 parse_data_urls : {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            xmlparse = xmltodict.parse(response.text)
            jsonstr = json.loads(json.dumps(xmlparse))['datastore']['recordset']['record']
            for info in jsonstr:
                pub_time = ''.join(re.findall('<span>(.*)</span>', info)[0]).replace('[', '').replace(']', '')
                info_url = self.domain_url + re.findall('<a href="(.*)" .*>', info)[0]

                yield scrapy.Request(url=info_url, callback=self.parse_item, meta={'pub_time': pub_time, 'noticn': response.meta['noticn']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 parse_info {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            classifyShow = response.xpath('//div[@class="dqwz"]/table/tr/td[2]/table/tr/td[1]/a/text()').get()
            title_name = response.xpath('//div[@class="zw"]/table/tr[1]/td/text()').get()
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            if re.search(r'候选人|评标结果', title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'终止|中止|异常|废标|流标', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|更正|澄清|修正|补充', title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r'成交|成果|中标', title_name):
                notice_type = const.TYPE_WIN_NOTICE
            elif re.search(r'招标|谈判|磋商', title_name):
                notice_type = const.TYPE_ZB_NOTICE
            elif re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['noticn']
            content = response.xpath('//td[@class="bt_content"]').get()
            content = re.sub('  历史公告查看:', '', content)



            files_path = {}
            if response.xpath("//td[@class='bt_content']/div/ul/li/p/a"):
                dict = response.xpath("//td[@class='bt_content']/div/ul/li")
                for itme in dict:
                    if itme.xpath('./p/a/@href'):
                        if 'http' in itme.xpath('./p/a/@href').get():
                            value = itme.xpath('./p/a/@href').get()
                        else:
                            value = self.base_url + itme.xpath('./p/a/@href').get()
                        keys = itme.xpath('./p/a/text()').get()
                        files_path[keys] = value
            if response.xpath('//td[@valign="top"]/table[@id="dlstAttachFile"]//a') or response.xpath('//table[@id="zfcg_caigouyaosugongshi_detail_dlstattachfile"]//a') or\
                    response.xpath('//div[@id="zoom"]//a'):
                dict = response.xpath('//td[@valign="top"]/table[@id="dlstAttachFile"]//a') or response.xpath('//table[@id="zfcg_caigouyaosugongshi_detail_dlstattachfile"]//a') or response.xpath('//div[@id="zoom"]//a')
                num = 1
                for itme in dict:
                    if itme.xpath("./@href"):
                        if 'http' in itme.xpath("./@href").get():
                            value = itme.xpath("./@href").get()
                        else:
                            value = self.base_url + itme.xpath("./@href").get()
                        key_name = ['png', 'jpg', 'jepg', 'doc', 'docx', 'pdf', 'xls']
                        key_list = ['www.sxztb.gov.cn', 'yyz18577@163.com', 'www.zjzfcg.gov.cn', 'http://www.sxztb.gov.cn']
                        if itme.xpath("./font/text()").get() or itme.xpath("./span/text()").get() or itme.xpath('./text()').get():
                            keys = itme.xpath("./font/text()").get() or itme.xpath("./span/text()").get() or itme.xpath('./text()').get()
                            if keys not in key_list:
                                files_path[keys] = value
                        elif value[value.rindex('.') + 1:] in key_name:
                            keys = value[value.rindex('/') + 1:] + '_' + str(num)
                            files_path[keys] = value
                        else:
                            pass
                        num += 1

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
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3312_shaoxing_spider".split(" "))


