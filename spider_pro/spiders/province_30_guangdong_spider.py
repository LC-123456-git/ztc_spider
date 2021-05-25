#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-26
# @Describe: 广东公共资源交易平台 - 全量/增量脚本
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
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(CrawlSpider):
    name = 'province_30_guangdong_spider'
    area_id = "30"
    domain_url = "http://dsg.gdggzy.org.cn:8080"
    query_url = "http://dsg.gdggzy.org.cn:8080/Bigdata/InformationPublic/viewList.do"
    allowed_domains = ['dsg.gdggzy.org.cn']
    area_province = "广东公共资源交易平台"

    type_list = ['GovernmentProcurement', 'Construction', 'LandMine', 'GovernmentProperty', 'BusAuction', 'OceanIsland',
                 'MedicalDrug', 'FinancialAgent', 'SpecialIndustry', 'IntellectualProperty']


    type_name = ["政府采购", "工程建设", "土地矿业", "国有产权", "公车拍卖", "海域海岛",
                 "药品耗材", "国有资产处置", "特许经营", "城乡用地建设指标", "知识产权"]
    type_noctice_name = ['政府采购', '工程建设']
    list_info_name_num = ['GPAnnouncement', 'GPResultAnnouncement']
    # 招标公告
    list_notice_category_num = "GPAnnouncement"
    # 中标公告
    list_win_notice_category_num = "CBResultAnnouncement"

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"pageSize": '50', "currPage": '1', 'releaseTime': '2021-02-25 00:00:00'}   # 增量需要在这里更改时间即可
        # self.time_dict = {"releaseTime": get_back_date(kwargs.get("sdt")) + " 00:00:00" if not kwargs.get("sdt") else ""}

    def start_requests(self):
        try:
            for list in range(len(self.type_list)):
                type_dict = self.r_dict | {'businessType': self.type_list[list]}
                classifyShow = self.type_name[list]
                if classifyShow in self.type_noctice_name:
                    for info_name in self.list_info_name_num:
                        if info_name in self.list_notice_category_num:
                            notice = const.TYPE_ZB_NOTICE
                        else:
                            notice = const.TYPE_WIN_NOTICE
                        type_dict = self.r_dict | {'businessType': self.type_list[list]} | {'informationPublicType': info_name}
                        yield scrapy.FormRequest(url=self.query_url, formdata=type_dict, callback=self.parse_urls,
                                                 meta={'type_dict': type_dict, 'classifyShow': classifyShow, 'notice': notice})
                else:
                    yield scrapy.FormRequest(url=self.query_url, formdata=type_dict, callback=self.parse_urls,
                                     meta={'type_dict': type_dict, 'classifyShow': classifyShow})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e}")


    def parse_urls(self, response):
        try:
            total = int(re.findall('(\d+)', response.xpath('//div[@class="m-pagination pege"]').get())[0])   #总条数
            if total != 0:
                self.logger.info(f"本次获取总条数为：{total}")
                page = int(math.ceil(total/50))
                for num in range(1, page + 1):
                    data_dict = response.meta['type_dict'] | {'currPage': '{}'.format(num)}
                    yield scrapy.FormRequest(url=self.query_url, formdata=data_dict, callback=self.parse_data_urls,
                                             priority=50, dont_filter=True,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'notice': response.meta['notice']})


        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath('//table[@class="table-list2"]/tbody/tr')
            for li in li_list:
                data_url = self.domain_url + li.xpath('./td[@class="txt-lf"]/a/@href').get()
                put_time = li.xpath('./td[3]/i/text()').get() or ''
                info_source = li.xpath('./td[1]/em/text()').get() or ''
                yield scrapy.Request(url=data_url, callback=self.parse_item, priority=100,
                                     meta={"put_time": put_time, "info_source": info_source,
                                           'classifyShow': response.meta['classifyShow'],
                                           'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = response.meta["info_source"]
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            classifyShow = response.meta.get("classifyShow")
            title_name = response.xpath('//div[@class="formBox formBox-txt"]/table/tbody/tr[1]/td[1]/text()').get() or ''
            if not title_name:
                notice_type = ""
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清", title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"候选人", title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            else:
                notice_type = response.meta['notice']
            pub_time = response.meta['put_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath("//div[@class='BoxB marb20']").get()

            pattern = re.compile(r'<div class="title_origin marb10".*?>(.*?)</div>', re.S)
            contents = content.replace(''.join(re.findall(pattern, content)), '')

            pattern = re.compile(r'<th colspan="4".*?>(.*?)</strong>', re.S)
            contents = contents.replace(''.join(re.findall(pattern, contents)), '')

            pattern = re.sub(r'<th width="20%">\w+</th>', '', contents)
            pattern = re.sub(r'<th width="40%">\w+</th>', '', pattern)
            contents = re.sub(r'<th colspan="4"><strong>附件材料</strong></th>', '', pattern)

            # title_names = ''.join(re.findall('项目名称：(.*?)</.*>', contents)).strip() or re.findall('项目名称：.*>$(.*?)</.*>', contents) or \
            #               re.findall('项目名称：.*>$(.*?)<.*>', contents) or re.findall('项目名称：.*">$(.*?)</.*>', contents)

            files_path = {}
            if response.xpath('//div[@class="BoxB marb20"]//div//a'):
                dict = response.xpath('//div[@class="BoxB marb20"]//div//a')
                for itme in dict:
                    value = itme.xpath('./@href').get()
                    keys = itme.xpath('./text()').get()
                    files_path[keys] = value
            else:
                files_path = ''
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
            notice_item["category"] = classifyShow
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_30_guangdong_spider".split(" "))


