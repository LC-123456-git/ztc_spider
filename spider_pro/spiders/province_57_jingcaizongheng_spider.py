# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-07
# @Describe: 精彩纵横 - 全量/增量脚本

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
from sqlalchemy import create_engine


class MySpider(CrawlSpider):
    name = 'province_57_jingcaizongheng_spider'
    area_id = "57"
    domain_url = "http://jczh.jczh100.com"
    query_url = "http://jczh.jczh100.com/JCZH//showinfo/IframeZbxxZn.aspx?type=&Infotype={}&Ggtype={}&StartDate=&EndDate=&title=&categoryNum=014"
    base_url = 'http://jczh.jczh100.com/JCZH//showinfo/IframeQycgZn.aspx?Infotype={}&Ggtype={}&StartDate=&EndDate=&title=&categoryNum=013'
    allowed_domains = ['jczh.jczh100.com']
    area_province = "精彩纵横"
    engine_config = 'mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4'
    engine = create_engine(engine_config, pool_size=105)


    # 招标公告
    list_notice_category_num = ['招标公告']
    # 中标公告
    list_win_notice_category_num = ['结果公告', ' 采购结果公示']
    # 招标异常
    list_alteration_category_num = ['流标公告']
    # 招标变更
    list_zb_abnormal_num = ["变更公告", '采购变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = []

    # all 分类的name
    type_name_list = ['政府采购', '建设工程', '国际招标', '其他招标', '询价采购', '竞谈采购', '招标采购', '竞价采购']
    # all 分类的code
    type_code_list = ['001', '002', '003', '004', '013001001', '013001002', '013001003', '013001004']

    # 招标信息类的分类info_name
    info_name_list = ['招标公告', '变更公告', '流标公告', '结果公告', '中标候选人公示']

    info_code_list = ['001', '002', '003', '004', '005']

    # 企业采购的分类data_name
    data_name_list = ['招标公告', '采购变更公告', '采购结果公告']

    data_code_list = ['013001', '013002', '013003']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for Infotype in self.type_code_list:
            if Infotype in re.findall('\d{3}', Infotype):
                for Ggtype,type_name in zip(self.info_code_list, self.info_name_list):
                    if Infotype == '001':
                        classifyShow = '建设工程'
                    elif Infotype == '002':
                        classifyShow = '政府采购'
                    elif Infotype == '003':
                        classifyShow = '国际招标'
                    else:
                        classifyShow = '其他招标'
                    info_url = self.query_url.format(Infotype, Ggtype)
                    yield scrapy.Request(url=info_url, callback=self.parse_urls,
                                         meta={'classifyShow': classifyShow, 'type_name': type_name})

            else:
                for Ggtype, type_name in zip(self.data_code_list, self.data_name_list):
                    if Infotype == '013001001':
                        classifyShow = '询价采购'
                    elif Infotype == '013001002':
                        classifyShow = '竞谈采购'
                    elif Infotype == '013001003':
                        classifyShow = '招标采购'
                    else:
                        classifyShow = '竞价采购'
                    data_url = self.base_url.format(Infotype, Ggtype)
                    yield scrapy.Request(url=data_url, callback=self.parse_urls,
                                         meta={'classifyShow': classifyShow, 'type_name': type_name})


    def parse_urls(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 0
                with self.engine.connect() as conn:
                    li_list = response.xpath('//form[@id="form1"]/div[@class="ewb-list"]')
                    for li in range(len(li_list)):
                        title_name = li_list[li].xpath('./div[1]/a[1]/@title').get()
                        result = conn.execute(f"select * from notices_57 where title_name='{title_name}' and pub_time >= '{self.sdt_time}' and pub_time < '{self.edt_time}'").fetchall()
                        # result = conn.execute(f"select * from notices_57 where title_name='{title_name}' and pub_time >= '{self.sdt_time}' and pub_time < '{self.edt_time}'").fetchall()
                        if not result:
                            num += 1
                        info_url = response.url + '&Paging={}'
                        if num >= len(li_list):
                            pn += 1
                        else:
                            pn = 1
                        yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info, priority=100,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'type_name': response.meta['type_name']})

            else:
                if response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get():
                    page = re.findall('\/(\d+)', response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get())[0]
                    total = int(page) * 13
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")

                    for num in range(1, int(page)+1):
                        url = response.url + '&Paging={}'.format(num)
                        yield scrapy.Request(url=url, callback=self.parse_info, priority=100,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'type_name': response.meta['type_name']})

        except Exception as e:
            self.logger.error(f"parse_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")


    def parse_info(self, response):
        try:
            li_list = response.xpath('//form[@id="form1"]/div[@class="ewb-list"]')
            for li in li_list:
                info_url = self.domain_url + li.xpath('./div[1]/a[1]/@href').get()
                info_title = li.xpath('./div[1]/a[1]/@title').get()
                # 代理机构   后期可以不用清洗
                bidding_agency = li.xpath('./div[2]/div[@class="l"]/text()').get().replace('代理机构：', '')
                if response.meta['type_name'] in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE                             # 招标公告
                elif response.meta['type_name'] in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE                            # 中标公告
                elif response.meta['type_name'] in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION                         # 招标变更
                elif response.meta['type_name'] in self.list_alteration_category_num:
                    notice = const.TYPE_ZB_ABNORMAL                           # 招标异常
                else:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE                    # 中标预告

                if re.search(r"变更", info_title):
                    notice_type = const.TYPE_ZB_ALTERATION       # 招标变更
                elif re.search(r"废标|流标", info_title):
                    notice_type = const.TYPE_ZB_ABNORMAL         # 招标异常
                elif re.search(r"候选人", info_title):
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE  # 中标预告
                elif re.search(r"中标", info_title):
                    notice_type = const.TYPE_WIN_NOTICE          # 中标公告
                else:
                    notice_type = notice

                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=150,
                                     meta={'classifyShow': response.meta['classifyShow'],
                                     'info_title': info_title, 'notice_type': notice_type})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            if response.xpath('//div[@class="ewb-span15 r"]/div[2]/div[@class="ewb-right-sub"]/span/span/text()').get():
                pub_time = re.findall('\d{4}-\d{1,2}-\d{1,2}', response.xpath('//div[@class="ewb-span15 r"]/div[2]/div[@class="ewb-right-sub"]/span/span/text()').get())[0]
                pub_time = get_accurate_pub_time(pub_time)
                origin = response.url
                info_source = self.area_province
                title_name = response.meta['info_title']
                classifyShow = response.meta['classifyShow']
                notice_type = response.meta['notice_type']
                content = response.xpath('//div[@class="ewb-right-txt"]').get()
                files_path = {}
                if response.xpath('//div[@class="ewb-right-txt"]/span[@class="infodetail"]/a/@href'):
                    con_list = response.xpath('//div[@class="ewb-right-txt"]/span[@class="infodetail"]/a')
                    for con in con_list:
                        if con.xpath('./@href'):
                            value = con.xpath('./@href').get()
                            key = con.xpath('./text()').get()
                            files_path[key] = value

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
                # yield notice_item
                print(notice_item)

if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_57_jingcaizongheng_spider".split(" "))
