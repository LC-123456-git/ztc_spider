#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-06
# @Describe: 湖州市公共资源交易网 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import datetime
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3307_huzhou_spider'
    area_id = "3307"
    domain_url = "http://ggzy.huzhou.gov.cn"
    query_url = "http://ggzy.huzhou.gov.cn/HZfront"
    allowed_domains = ['ggzy.huzhou.gov.cn']
    area_province = "浙江-湖州市公共资源交易网"

    # 招标预告
    list_advance_notice_num = ['国有产权预转让']
    # 招标公告
    list_notice_category_num = ['招标公告', '交通招标公告', '水利招标公告', '集中采购招标公告', '分散采购招标公告', '采购公告',
                                '国有产权转让公告', '国有资产转让公告', '国土出让挂牌公告', '矿业权出让拍卖公告', '农村综合产权交易公告',
                                '国土出让成交公告', '建设工程招标文件公示', '水利工程招标文件公示', '交通工程招标文件公示']
    # 招标异常
    list_alteration_category_num = ['']
    # 招标变更
    list_zb_abnormal_num = ['变更公告', '交通变更公告', '水利变更公告']
    # 中标预告
    list_win_advance_notice_num = ['评标结果公示', '交通评标结果公示', '水利评标结果公示', '交易公示']
    # 中标公告
    list_win_notice_category_num = ['中标结果公告', '交通中标结果公告', '水利中标结果公告', '集中采购中标公示', '分散采购中标公示', '采购公示',
                                     '交易结果公告', '农村综合产权交易公示', '交易公告', '国有产权转让公示', '国有资产转让公示', '矿业权出让成交公告']
    # 资格预审
    list_qualification_num = ['资格预审']
    # 其他
    list_qita_code = ['开标结果公示', '集中采购征求意见', '分散采购征求意见']

    # 工程建设
    category_project_code = ['/jcjs/021001', '/jcjs/021002', '/jcjs/021003']
    # 土地矿产
    category_land_code = ['/tdkc/022001', '/tdkc/022002']
    # 产权交易
    category_property_code = ['/cqjy/023001', '/cqjy/023002']
    # 政府采购
    category_government_code = ['/zfcg/024001', '/zfcg/024002']
    # 医疗采购
    category_medical_code = ['/ylcg/025001']
    # 农村综合产权交易
    category_village_code = ['/nczhcq/037001', '/nczhcq/037002']
    # 其他交易
    category_rest_code = ['/qtjy/037001', '/qtjy/037002']

    category_all_code = category_project_code + category_land_code + category_property_code + \
                        category_government_code + category_medical_code + category_village_code + category_rest_code



    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for itme in self.category_all_code:
            itme_url = self.query_url + itme
            if itme in self.category_project_code:
                category_name = '工程建设'
            elif itme in self.category_land_code:
                category_name = '土地矿产'
            elif itme in self.category_land_code:
                category_name = '产权交易'
            elif itme in self.category_government_code:
                category_name = '政府采购'
            elif itme in self.category_medical_code:
                category_name = '医疗采购'
            elif itme in self.category_village_code:
                category_name = '农村综合产权交易'
            elif itme in self.category_rest_code:
                category_name = '其他交易'
            else:
                category_name = ''

            yield scrapy.Request(url=itme_url, callback=self.parse_urls,
                             meta={'category_name': category_name})

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="right-slider-content"]/table/tr/td/table/tr[1]/td/table/tr')
            for li in li_list:
                data_url = response.url + li.xpath('./td[last()]/a/@href').get()
                type_name = li.xpath('./td[2]/text()').get()
                if type_name in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE
                elif type_name in self.list_win_advance_notice_num:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_name in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE
                elif type_name in self.list_qualification_num:
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif type_name in self.list_qita_code:
                    notice = const.TYPE_OTHERS_NOTICE
                elif type_name in self.list_advance_notice_num:
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif type_name in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION
                else:
                    notice = 'null'

                yield scrapy.Request(url=data_url, callback=self.parse_data_urls,
                                     meta={'category_name': response.meta['category_name'], 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 0
                li_list = response.xpath('//div[@class="right-slider-content"]/table/tr[@height="24"]')[1:]
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./td[last()]/font/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                    info_url = response.url[:response.url.rindex('/') + 1] + '?Paging={}'
                    if num >= len(li_list):
                        pn += 1
                    else:
                        pn = 1
                    yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info,
                                         meta={'category_name': response.meta['category_name'], 'notice': response.meta['notice']})
            else:
                if response.xpath('//div[@class="pagemargin"]//td[@class="huifont"]/text()').get() is not None:
                    pages = re.findall('/(\d+)', response.xpath('//div[@class="pagemargin"]//td[@class="huifont"]/text()').get())[0]
                    total = int(pages) * 17
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    info_url = response.url[:response.url.rindex('/') + 1] + '?Paging={}'
                    for num in range(1, int(pages) + 1):
                        yield scrapy.Request(url=info_url.format(num), callback=self.parse_info,
                                         meta={'category_name': response.meta['category_name'], 'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"parse_data_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            if response.xpath('//div[@class="right-slider-content"]/table/tr[@height="24"]'):
                li_list = response.xpath('//div[@class="right-slider-content"]/table/tr[@height="24"]')[1:]
                for li in li_list:
                    title_name = li.xpath('./td[2]/a/@title').get()
                    all_info_url = self.domain_url + li.xpath('./td[2]/a/@href').get()
                    # info_source = ''.join(li.xpath('./td[2]/a/text()').get()).replace('[', '').replace(']', '') or ''
                    pub_time = li.xpath('./td[last()]/font/text()').get()
                    if response.meta['notice'] != 'null':
                        if re.search(r'变更|更正|澄清', title_name):           # 招标变更
                            notice_type = const.TYPE_ZB_ALTERATION
                        elif re.search(r'候选人|评标结果', title_name):         # 中标预告
                            notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                        elif re.search(r'中标|结果|成交', title_name):          # 中标公告
                            notice_type = const.TYPE_WIN_NOTICE
                        elif re.search(r'终止|中止|流标|废标', title_name):      # 招标异常
                            notice_type = const.TYPE_ZB_ABNORMAL
                        elif re.search(r'预招标|预披露', title_name):            # 招标预告
                            notice_type = const.TYPE_ZB_ADVANCE_NOTICE
                        else:
                            notice_type = response.meta['notice']
                        #
                        yield scrapy.Request(url=all_info_url, callback=self.parse_item, priority=15,
                                         meta={'notice_type': notice_type, 'pub_time': pub_time,
                                               'title_name': title_name, 'category_name': response.meta['category_name'],
                                               })
        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            # if response.meta['info_source']:
            #     info_source = self.area_province + response.meta['info_source']
            # else:
            info_source = self.area_province
            category = response.meta['category_name']
            notice_type = response.meta['notice_type']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//td[@height="859"]').get()

            pattern = re.compile(r'<iframe width="980".*?>(.*?)</iframe>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<td id="tdTitle".*?>(.*?)</td>', re.S)
            content = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<iframe .*?></iframe>', re.S)
            contents = content.replace(''.join(re.findall(pattern, content)), '')


            files_path = {}
            if response.xpath('//td[@height="859"]//td[@id="TDContent"]/div/img'):
                conet_list = response.xpath('//td[@height="859"]//td[@id="TDContent"]/div/img')
                for con in conet_list:
                    if con.xpath('./@src'):
                        if 'http' in con.xpath('./@src').get():
                            value = con.xpath('./@src').get()
                            if 'http://ggzy.huzhou.gov.cn:8090' in value:
                                continue
                        else:
                            value = self.domain_url + con.xpath('./@src').get()


                        if con.xpath('./@alt').get():
                            keys = con.xpath('./@alt').get()
                        else:
                            keys = 'img/pdf/doc/xls'

                        files_path[keys] = value

            if response.xpath('//td[@height="859"]//table[@id="filedown"]/tr/td/a'):
                conet_list = response.xpath('//td[@height="859"]//table[@id="filedown"]/tr')
                num = 1
                for con in conet_list:
                    if con.xpath('./td/a/@href'):
                        if 'http' in con.xpath('./td/a/@href').get():
                            value = con.xpath('./td/a/@href').get()
                        else:
                            value = self.domain_url + con.xpath('./td/a/@href').get()
                        if con.xpath('./td/a/font/text()').get():
                            keys = con.xpath('./td/a/font/text()').get()
                        else:
                            keys = re.findall('\w+\.(\w+)', value[value.rindex('/') + 1:])[0] + '_' + str(num)
                        num += 1
                        files_path[keys] = value

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl ZJ_city_3307_huzhou_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3307_huzhou_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))


