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
from spider_pro.utils import get_accurate_pub_time, get_back_date, remove_specific_element, judge_dst_time_in_interval


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
                 "药品耗材", "国有资产处置", "特许经营", "知识产权"]
    type_noctice_name = ['GP', 'CB', 'LM', 'SP', 'VA', 'OI', 'MP', 'FA', 'SI', 'IP']
    list_info_name_num = ['Announcement', 'ResultAnnouncement']

    data = {'pageSize': '50', 'currPage': '1', 'releaseTime': '2021-06-10 00:00:00',
            'businessType': 'GovernmentProcurement', 'informationPublicType': 'GPResultAnnouncement'}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"pageSize": '50', "currPage": '1', 'releaseTime': '2021-02-25 00:00:00'}   # 增量需要在这里更改时间即可
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        try:
            for list in range(len(self.type_list)):
                type_dicts = self.r_dict | {'businessType': self.type_list[list]}
                classifyShow = self.type_name[list]
                for info_name in self.list_info_name_num:
                    info_type_name = self.type_noctice_name[list] + info_name
                    if 'ResultAnnouncement' not in info_type_name:
                        notice = const.TYPE_ZB_NOTICE                                      # 招标公告
                    else:
                        notice = const.TYPE_WIN_NOTICE                                     # 中标公告
                    type_dict = type_dicts | {'informationPublicType': info_type_name}
                    yield scrapy.FormRequest(url=self.query_url, formdata=type_dict, callback=self.parse_urls, dont_filter=True,
                                             meta={'type_dict': type_dict, 'classifyShow': classifyShow, 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e}")


    def parse_urls(self, response):
        try:
            if re.findall('(\d+)', response.xpath('//div[@class="m-pagination pege"]').get())[0]:
                if self.enable_incr:
                    pn = 1
                    nums = 0
                    li_list = response.xpath('//table[@class="table-list2"]/tbody/tr')
                    for li in range(len(li_list)):
                        data_url = self.domain_url + li_list[li].xpath('./td[@class="txt-lf"]/a/@href').get()
                        info_source = li_list[li].xpath('./td[1]/em/text()').get() or ''
                        pub_time = li_list[li].xpath('./td[3]/i/text()').get() or ''
                        pub_time = get_accurate_pub_time(pub_time)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=data_url, callback=self.parse_item, priority=100,
                                                 meta={"pub_time": pub_time, "info_source": info_source,
                                                       'classifyShow': response.meta['classifyShow'],
                                                       'notice': response.meta['notice']})


                        if nums >= len(li_list):
                            pn += 50
                            data_dict = response.meta['type_dict'] | {'currPage': '{}'.format(pn)} | {'releaseTime': self.edt_time}
                            yield scrapy.FormRequest(url=self.query_url, formdata=data_dict,
                                                     callback=self.parse_data_urls,
                                                     priority=50, dont_filter=True,
                                                     meta={'classifyShow': response.meta['classifyShow'],
                                                           'notice': response.meta['notice']})
                else:
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
                pub_time = li.xpath('./td[3]/i/text()').get() or ''
                info_source = li.xpath('./td[1]/em/text()').get() or ''
                yield scrapy.Request(url=data_url, callback=self.parse_item, priority=100,
                                     meta={"pub_time": pub_time, "info_source": info_source,
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
            title_name = response.xpath('//div[@class="title"]/p/text()').get() or ''
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
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath("//div[@class='BoxB marb20']").get()
            # 去除 title
            _, content = remove_specific_element(content, 'div', 'class', 'title_origin marb10')

            _, content = remove_specific_element(content, 'th', 'colspan', '4')

            pattern = re.sub(r'<th width="20%">\w+</th>', '', content)
            pattern = re.sub(r'<th width="40%">\w+</th>', '', pattern)
            contents = re.sub(r'<th colspan="4"><strong>附件材料</strong></th>', '', pattern)



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

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_30_guangdong_spider -a sdt=2021-05-06 -a edt=2021-06-10".split(" "))


