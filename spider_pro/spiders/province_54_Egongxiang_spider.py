# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-04-25
# @Describe: E共享交易平台 - 全量/增量脚本
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
    name = 'province_54_Egongxiang_spider'
    area_id = "54"
    domain_url = "http://ebid.okap.com"
    query_url = "http://ebid.okap.com/#/front/trading?tabSelectedIndex=1"
    base_url = 'http://ebid.okap.com/api/ebidproject/listProject'
    allowed_domains = ['ebid.okap.com']
    area_province = ""
    web_name = 'E共享交易平台'

    # 招标公告
    list_notice_category_num = ['招标公告']
    # 中标公告
    list_win_notice_category_num = ['中标结果公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ["答疑纪要"]
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = []

    type_name = ['房建市政', '公路水运', '采购', '竞价', '其他']

    r_dict = {"projectClass": "", "projectName": "", "sort": "", "pageSize": "40", "pageNum": "1"}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for name in self.type_name:
            classifyShow = name
            if name == "房建市政":
                info_dict = self.r_dict | {'projectClass': 'fj,sz'} | {"sort": '1'}
            elif name == '公路水运':
                info_dict = self.r_dict | {'projectClass': 'gsgl,ptgl,sy'} | {"sort": '2'}
            elif name == '采购':
                info_dict = self.r_dict | {'projectClass': 'cg'} | {"sort": '3'}
            elif name == '竞价':
                info_dict = self.r_dict | {'projectClass': 'jg'} | {"sort": '4'}
            else:
                info_dict = self.r_dict | {'projectClass': 'qt'} | {"sort": '5'}

            yield scrapy.FormRequest(url=self.base_url, formdata=info_dict, callback=self.parse_urls,
                                     meta={'classifyShow': classifyShow, "info_dict": info_dict})


    def parse_urls(self, response):
        try:
            if response.status == 200:
                if self.enable_incr:
                    page = 1
                    num = 0
                    data_list = json.loads(response.text)['result']['list']
                    sort = response.meta['info_dict']['sort']
                    for li in range(len(data_list)):
                        pub_time = data_list[li]['V_TIME']
                        pub_time = get_accurate_pub_time(pub_time)
                        title_name = data_list[li]['V_PROJECT_NAME']
                        code_id = data_list[li]['V_PROJECTID']
                        code_dict = {'projectId': code_id}
                        code_type = data_list[li]['V_PROJECT_CLASSIFICATION']
                        info_url = 'http://ebid.okap.com/api/ebidproject/infoProject'
                        origin = 'http://ebid.okap.com/#/front/tradingContent?id={}&tabSelectedIndex={}&classification={}' \
                            .format(code_id, sort, code_type)
                        x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                        if x:
                            num += 1
                            total = int(len(data_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.FormRequest(url=info_url, callback=self.parse_item,
                                                     formdata=code_dict, priority=15,
                                                     meta={'classifyShow': response.meta['classifyShow'],
                                                           'title_name': title_name,
                                                           'origin': origin})

                        if num >= len(data_list):
                            page += 1
                            r_info_dict = response.meta['info_dict'] | {'pageNum': str(page)}
                            yield scrapy.FormRequest(url=self.base_url, formdata=r_info_dict,
                                                     callback=self.parse_data_urls,
                                                     meta={'classifyShow': response.meta['classifyShow'],
                                                           'r_info_dict': r_info_dict})
                else:
                    total = json.loads(response.text)['result']['total']
                    pages = math.ceil(int(total) / 40)
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    for page in range(1, int(pages) + 1):
                        r_info_dict = response.meta['info_dict'] | {'pageNum': str(page)}
                        yield scrapy.FormRequest(url=self.base_url, formdata=r_info_dict, callback=self.parse_data_urls,
                                                 meta={'classifyShow': response.meta['classifyShow'],
                                                       'r_info_dict': r_info_dict})

        except Exception as e:
            self.logger.error(f"parse_urls:初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            data_list = json.loads(response.text)['result']['list']
            sort = response.meta['r_info_dict']['sort']
            for info in data_list:
                title_name = info['V_PROJECT_NAME']
                code_id = info['V_PROJECTID']
                code_dict = {'projectId': code_id}
                code_type = info['V_PROJECT_CLASSIFICATION']
                info_url = 'http://ebid.okap.com/api/ebidproject/infoProject'
                origin = 'http://ebid.okap.com/#/front/tradingContent?id={}&tabSelectedIndex={}&classification={}'\
                    .format(code_id, sort, code_type)
                yield scrapy.FormRequest(url=info_url, callback=self.parse_item, formdata=code_dict, priority=15,
                                         meta={'classifyShow': response.meta['classifyShow'], 'title_name': title_name,
                                               'origin': origin})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        numstr = '零一二三四五六七八九'
        if response.status == 200:
            data_info = json.loads(response.text)['result']['infoTime']
            content = """<iframe href="{}" width="100%" heigth="800" border="0" frameboder="0" style="border: none;"></iframe>
                      """
            file_url = ''
            type_name = ''
            n = 1
            files_path = {}
            for data in data_info:
                if file_url != data['V_FILE_URL']:
                    file_url = data['V_FILE_URL']
                    if type_name == data['TYPE']:
                        type_name = data['TYPE']
                        n += 1
                    else:
                        type_name = data['TYPE']
                        n = 1
                    content = content.format(file_url)
                    keys = str(n) + ".pdf"
                    files_path[keys] = file_url

                    info_source = self.web_name
                    origin = response.meta['origin']
                    classifyShow = response.meta['classifyShow']
                    if n != 1:
                        title_name = response.meta['title_name'] + "-" + type_name + "({})".format(
                            numstr[eval('{}'.format(n))])
                    else:
                        title_name = response.meta['title_name'] + "-" + type_name
                    pub_time = data['V_TIME']
                    pub_time = get_accurate_pub_time(pub_time)

                    if type_name in self.list_notice_category_num:
                        notice_type = const.TYPE_ZB_NOTICE  # 招标公告
                    elif type_name in self.list_win_notice_category_num:
                        notice_type = const.TYPE_WIN_NOTICE  # 中标公告
                    elif type_name in self.list_alteration_category_num:
                        notice_type = const.TYPE_ZB_ALTERATION  # 招标变更
                    else:
                        notice_type = const.TYPE_WIN_ADVANCE_NOTICE  # 中标预告

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

                    yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_54_Egongxiang_spider".split(" "))
