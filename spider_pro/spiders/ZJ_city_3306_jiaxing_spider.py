#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-01
# @Describe: 嘉兴公共资源交易网 - 全量/增量脚本
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
    name = 'ZJ_city_3306_jiaxing_spider'
    area_id = "3306"
    domain_url = "http://jxszwsjb.jiaxing.gov.cn"
    query_url = "http://jxszwsjb.jiaxing.gov.cn/jygg/subpage.html"
    allowed_domains = ['jxszwsjb.jiaxing.gov.cn']
    area_province = "浙江-嘉兴公共资源交易网"
    # 招标预告
    list_advance_notice_code = []
    # 招标异常
    list_alteration_category_num = ['003001006']
    # 招标公告
    list_notice_category_code = ['003001001', '003002001', '003003001', '003003002', '003004001',
                                 '003004002', '003004003', '003006001', '003007001', '003007002', '003008001']
    # 招标变更
    list_zb_abnormal_code = ['003002003']
    # 中标预告
    list_win_advance_notice_code = ['003001004']
    # 中标公告
    list_win_notice_category_code = ['003001005', '003002002', '003003003', '003004004', '003006001', '003007001',
                                     '003007002', '003008001']
    # 资格预审
    list_qualification_num = ['003001002']
    # 其他
    list_qita_code = ['003001003', '003001007', '003001008']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="ewb-tree-bd"]/ul/li')
            for li in li_list:
                classifyShow = li.xpath('./h3/span/a/text()').get()
                info_url_list = li.xpath('./ul/li')
                for info in info_url_list:
                    info_url = self.domain_url + info.xpath('./a/@href').get()
                    code = re.findall('\d{8,10}', info_url)[0]
                    if code in self.list_alteration_category_num:
                        notice = const.TYPE_ZB_ABNORMAL
                    elif code in self.list_notice_category_code:
                        notice = const.TYPE_ZB_NOTICE
                    elif code in self.list_zb_abnormal_code:
                        notice = const.TYPE_ZB_ALTERATION
                    elif code in self.list_win_advance_notice_code:
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif code in self.list_win_notice_category_code:
                        notice = const.TYPE_WIN_NOTICE
                    elif code in self.list_qualification_num:
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif code in self.list_qita_code:
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = 'null'
                    if notice != 'null':
                        # print(info_url, classifyShow, notice)
                        yield scrapy.Request(url=info_url, callback=self.parse_data_urls,
                                         meta={'classifyShow': classifyShow, 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            if self.enable_incr:
                li_list = response.xpath('//div[@class="ewb-con-bd"]/ul/li')
                li_num = 0
                pn = 1
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./span/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        li_num += 1
                    if li_num >= len(li_list):
                        pn += 1
                    else:
                        pn = 1
                    data_url = response.url[:response.url.rindex('/') + 1] + '{}.html'.format(pn)
                    yield scrapy.Request(url=data_url, callback=self.parse_info,
                                         meta={'classifyShow': response.meta['classifyShow'], 'notice': response.meta['notice']})
            else:
                if response.xpath('//div[@class="ewb-page"]/script/text()'):
                    total = re.findall('var totalnum=(\d+)', response.xpath('//div[@class="ewb-page"]/script/text()').get())[0]
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    pages = math.ceil(int(total)/18)
                    for num in range(1, int(pages) + 1):
                        data_url = response.url[:response.url.rindex('/') + 1] + '{}.html'.format(num)

                        yield scrapy.Request(url=data_url, callback=self.parse_info,
                                             meta={'classifyShow': response.meta['classifyShow'], 'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"parse_data_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")


    def parse_info(self, response):
        try:
            li_list = response.xpath('//div[@class="ewb-con-bd"]/ul/li')
            for li in li_list:
                all_url = self.domain_url + li.xpath('./div/a/@href').get()
                title_name = li.xpath('./div/a/@title').get()
                pub_time = li.xpath('./span/text()').get()
                if re.search(r'资格预审', title_name):
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'变更|更正|澄清|修正|补充', title_name):
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'招标|谈判|磋商|出让|招租', title_name):
                    notice_type = const.TYPE_ZB_NOTICE
                elif re.search(r'终止|废标|终止|中止', title_name):
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'成交|结果|中标', title_name):
                    notice_type = const.TYPE_WIN_NOTICE
                elif re.search(r'候选人|评标结果', title_name):
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                else:
                    notice_type = response.meta['notice']
                # print(all_url, response.meta['classifyShow'], notice_type)
                yield scrapy.Request(url=all_url, callback=self.parse_item,
                                    meta={"title_name": title_name, 'classifyShow': response.meta['classifyShow'],
                                          'notice_type': notice_type, 'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            classifyShow = response.meta['classifyShow']
            notice_type = response.meta['notice_type']
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            if not pub_time:
                pub_time = "null"
            pub_time = get_accurate_pub_time(pub_time)
            contents = response.xpath("//div[@class='con']").get()

            files_path = {}
            if response.xpath("//div[@class='con']//a"):
                conet_list = response.xpath("//div[@class='con']//a")
                num = 1
                for con in conet_list:
                    if 'http' in con.xpath('./@href').get():
                        value = con.xpath('./@href').get()
                    else:
                        value = self.domain_url + con.xpath('./@href').get()
                    value_list = ['http://www.zjzfcg.gov.cn/', 'http://cgzx.zjxu.edu.cn/', 'http://www.jxzbtb.gov.cn/jxggzyjyzx/',
                                'http://jx.jxzbtb.cn/jxcms/jxztb/content/2018-10/11/#', 'http://land.zjgtjy.cn/GTJY_ZJ/',
                                'http://www.zjzfcg.gov.cn/new/', 'http://www.zrar.com/']
                    if value in value_list:
                        pass
                    else:
                        key_list = ['[收藏]', '[评论]', '[打印]', '[关闭]', 'allan_xiao@163.com']
                        keys = con.xpath('./text()').get()
                        if keys not in key_list:
                            key_name = ['png', 'jpg', 'jepg', 'doc', 'docx', 'pdf', 'xls']
                            if not keys:
                                if re.findall('\w+\.(\w+)', value[value.rindex('/')+1:]) in key_name:
                                    keys = re.findall('\w+\.(\w+)', value[value.rindex('/')+1:])[0] + '_' + str(num)
                                    files_path[keys] = value
                                else:
                                    files_path = ''
                            files_path[keys] = value
                    num += 1

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
    cmdline.execute("scrapy crawl ZJ_city_3306_jiaxing_spider".split(" "))

