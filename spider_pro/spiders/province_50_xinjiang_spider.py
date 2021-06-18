# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-08
# @Describe: 新疆公共资源交易信息网 - 全量/增量脚本
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
    name = 'province_50_xinjiang_spider'
    area_id = "50"
    start_url = 'http://zwfw.xinjiang.gov.cn'
    domain_url = "http://zwfw.xinjiang.gov.cn/xinjiangggzy"
    query_url = "http://zwfw.xinjiang.gov.cn/xinjiangggzy/jyxx/001004/001004005/tradingNotice.html"
    base_url = 'http://zwfw.xinjiang.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData'
    allowed_domains = ['zwfw.xinjiang.gov.cn']
    area_province = "新疆维吾尔族自治区公共资源交易服务平台"

    # 招标预告
    list_advance_notice_num = ['001005003']
    # 招标公告
    list_notice_category_num = ['001001001', '001002001', '001003001', '001004003', '001005001', '001006001',
                                '001007001', '001008001', '001009001', '001010001']
    # 中标公告
    list_win_notice_category_num = ['001001005', '001002004', '001003004', '001004005', '001005002', '001006002', '001007002',
                                    '001008002', '001009002', '001010002']
    # 招标异常
    list_alteration_category_num = ['001001006', '001002005', '001003005', '001004007', '001005004']
    # 招标变更
    list_zb_abnormal_num = ['001001002', '001002002', '001003002', '001004004', '001006003', '001007003']
    # 中标预告
    list_win_advance_notice_num = ['001001004', '001003003', '001002003']
    # 资格预审结果公告
    list_qualification_num = ['']
    # 其他公告
    list_others_notice_num = ['']

    d_dict = {"token": "", "pn": '0', "rn": '50', "sdt": "", "edt": "", "wd": "", "inc_wd": "", "exc_wd": "",
          "fields": "title,projectnum", "cnum": "005", "sort": "{\"infodate\":\"0\"}", "ssort": "title", "cl": '200',
          "terminal": "", "condition": [{"fieldName": "categorynum", "isLike": 'true', "likeType": '2', "equal": "001005001"}],
          "time": [{"fieldName": "webdate", "startTime": "", "endTime": ""}], "highlights": "title",
          "statistics": 'null',
          "unionCondition": 'null', "accuracy": "100", "noParticiple": "0", "searchRange": 'null',
          "isBusiness": '1'}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_url)

    def parse_url(self, response):
        try:
            li_list = response.xpath('//ul[@class="wb-tree-sub"]/li')
            for li in li_list:
                code = re.findall('\d{8,9}', li.xpath('./a/@href').get())[0]
                if code in self.list_advance_notice_num:
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif code in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE
                elif code in self.list_win_notice_category_num:
                    notice = const.TYPE_WIN_NOTICE
                elif code in self.list_alteration_category_num:
                    notice = const.TYPE_ZB_ABNORMAL
                elif code in self.list_zb_abnormal_num:
                    notice = const.TYPE_ZB_ALTERATION
                elif code in self.list_win_advance_notice_num:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                else:
                    notice = 'null'
                if notice != 'null':
                    if '001001' in code:
                        classifyShow = '工程建设'
                    elif '001002' in code:
                        classifyShow = '交通工程'
                    elif '001003' in code:
                        classifyShow = '水利工程'
                    elif '001004' in code:
                        classifyShow = '政府采购'
                    elif '001005' in code:
                        classifyShow = '产权交易'
                    elif '001006' in code:
                        classifyShow = '矿权交易'
                    elif '001007' in code:
                        classifyShow = '土地交易'
                    elif '001008' in code:
                        classifyShow = '药品耗材'
                    elif '001009' in code:
                        classifyShow = '铁路工程'
                    elif '001009' in code:
                        classifyShow = '民航工程'
                    else:
                        classifyShow = 'null'
                    if classifyShow != 'null':
                        s_dict = self.d_dict['condition'][0] | {'equal': code}
                        data_dict = self.d_dict | {'condition': [s_dict]}
                        yield scrapy.Request(url=self.base_url, method='POST', body=json.dumps(data_dict),
                                             callback=self.parse_data_urls,
                                             meta={'classifyShow': classifyShow,
                                                   'notice': notice, 'data_dict': data_dict})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if json.loads(response.text)['result']['totalcount']:
                if self.enable_incr:
                    pn = 0
                    data_info_list = json.loads(response.text)['result']['records']
                    nums = 0
                    for info in range(len(data_info_list)):
                        pub_time = data_info_list[info]['infodate']
                        pub_time = get_accurate_pub_time(pub_time)
                        title_name = data_info_list[info]['title']
                        info_url = self.domain_url + data_info_list[info]['linkurl']
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_info_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")

                            yield scrapy.Request(url=info_url, callback=self.parse_item,
                                                 meta={'classifyShow': response.meta['classifyShow'],
                                                       'notice': response.meta['notice'],
                                                       'title_name': title_name,
                                                       'pub_time': pub_time})

                    if nums >= len(data_info_list):
                        pn += 50
                        info_dicts = response.meta['data_dict'] | {'pn': str(pn)}

                        yield scrapy.Request(url=self.base_url, method='POST', body=json.dumps(info_dicts),
                                             callback=self.parse_info, priority=200,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'notice': response.meta['notice']})
                else:
                    total = json.loads(response.text)['result']['totalcount']
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    page = int(math.ceil(int(total)/50))
                    pn = 0
                    for num in range(1, page+1):
                        if num == 1:
                            pn = 0
                        else:
                            pn += 50
                        info_dicts = response.meta['data_dict'] | {'pn': str(pn)}
                        yield scrapy.Request(url=self.base_url, method='POST', body=json.dumps(info_dicts),
                                             callback=self.parse_info,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 : {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            if json.loads(response.text)['result']['records']:
                data_info_list = json.loads(response.text)['result']['records']
                for info in data_info_list:
                    title_name = info['title']
                    pub_time = info['infodate']
                    info_url = self.domain_url + info['linkurl']
                    yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                          meta={'classifyShow': response.meta['classifyShow'],
                                               'notice': response.meta['notice'],
                                               'pub_time': pub_time,
                                               'title_name': title_name})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            if response.xpath('//div[@class="ewb-info-intro"]/span[2]/text()'):
                info_source = self.area_province + re.findall('信息来源：(.*)', response.xpath('//div[@class="ewb-info-intro"]/span[2]/text()').get())[0]
            else:
                info_source = self.area_province
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath("//div[@class='ewb-info-bd']").get()
            content = content.replace('&amp;nbsp', '')

            files_path = {}
            if response.xpath("//div[@class='ewb-info-bd']/p/span/a[@target='_blank']"):
                dict = response.xpath("//div[@class='ewb-info-bd']/p/span/a[@target='_blank']")
                for itme in dict:
                    if 'http' in itme.xpath('./@href').get():
                        value = itme.xpath('./@href').get()
                    else:
                        value = self.base_url + itme.xpath('./@href').get()
                    keys = itme.xpath('./text()').get()
                    files_path[keys] = value
            if response.xpath('//div[@class="ewb-info"]/div'):
                content_text = response.xpath('//div[@class="ewb-info"]/div')
                for con in content_text.xpath('./text()').extract():
                    if con in '附件： ':
                        if 'http' in content_text.xpath("./a/@href"):
                            value = content_text.xpath("./a/@href").get()
                        else:
                            value = self.base_url + content_text.xpath("./a/@href").get()
                        keys = content_text.xpath("./a/text()").get()
                        files_path[keys] = value
            if re.search(r'资格预审', title_name):
                notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
            elif re.search(r'候选人', title_name):
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r'终止|中止|异常|废标|流标', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r'变更|更正|澄清', title_name):
                notice_type = const.TYPE_ZB_ALTERATION
            else:
                notice_type = response.meta['notice']

            if notice_type != 'null':

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
    cmdline.execute("scrapy crawl province_50_xinjiang_spider".split(" "))
    # cmdline.execute("scrapy crawl province_50_xinjiang_spider -a sdt=2021-05-18 -a edt=2021-06-10".split(" "))


