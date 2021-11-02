#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-11-01
# @Describe: 惠招标
import copy
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
    get_files, get_notice_type, remove_specific_element, get_timestamp, remove_element_by_xpath


class Province159HuiZhaoBiaoSpider(CrawlSpider):
    name = 'province_159_huizhaobiao_spider'
    allowed_domains = ['hbidding.com']
    start_urls = 'http://www.hbidding.com'
    domain_url = 'http://www.hbidding.com/web/index/information/getjyinfopg.json?pageindex={}&pagesize=50&type={}&citycode=&hycode=&leixing={}&zbdl=&searchtype=ggname&searchcontent=&starttime=&endtime='
    base_url = 'http://www.hbidding.com/hbiddingWeb/pages/jyinfo/detail.html?active=0&&infoid={}&&categoryid={}'
    query_url = 'http://www.hbidding.com/web/index/information/getjyinfodetail.json?&infoid={}&categoryid={}'
    area_id = "159"
    area_province = '惠招标'

    # 招标预告
    list_tender_notice_num = []
    # 招标公告
    list_notice_category_name = ['zbgg']
    # 招标变更
    list_zb_abnormal_name = ['bggg', 'bydy']
    # 中标预告
    list_win_advance_notice_name = ['hxrgs']
    # 中标公告
    list_win_notice_category_name = ['zhongbiaogg']
    # 招标异常
    list_alteration_category_name = ['ycgg']
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = []

    label_type = ['建设工程', '政府采购']

    all_list = list_notice_category_name + list_zb_abnormal_name + list_win_advance_notice_name + \
               list_win_notice_category_name + list_alteration_category_name + list_qualifiction_advance_num

    def __init__(self, *args, **kwargs):
        super(Province159HuiZhaoBiaoSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for label in self.label_type:
            for notice_name in self.all_list:
                if notice_name in self.list_notice_category_name:
                    notice_type = const.TYPE_ZB_NOTICE
                elif notice_name in self.list_zb_abnormal_name:
                    notice_type = const.TYPE_ZB_ALTERATION
                elif notice_name in self.list_win_advance_notice_name:
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif notice_name in self.list_win_notice_category_name:
                    notice_type = const.TYPE_WIN_NOTICE
                elif notice_name in self.list_alteration_category_name:
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif notice_name in self.list_qualifiction_advance_num:
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                else:
                    notice_type = ''
                category = label
                page = 1
                yield scrapy.Request(url=self.domain_url.format(page, notice_name, label), callback=self.parse_data_info,
                                     meta={'notice_type': notice_type,
                                           'category': category})

    def parse_data_info(self, response):
        try:
            data_info = json.loads(response.text)
            if self.enable_incr:
                count = 0
                num = 0
                info_data = data_info['rows']
                for info in info_data:
                    count += 1
                    if '河北' in info['cityname']:
                        info_source = info['cityname']
                    else:
                        info_source = '河北-' + info['cityname']
                    title_name = info['ggname']
                    pub_time = info['ggfbtime']
                    info_url = self.query_url.format(info['ggcode'], info['ggtype'])
                    data_info_url = self.base_url.format(info['ggcode'], info['ggtype'])
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                             priority=(len(info_data) - count) * 100,
                                             meta={'notice_type': response.meta['notice_type'],
                                                   'category': response.meta['category'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time,
                                                   'data_info_url': data_info_url,
                                                   'info_source': info_source})
                    if num >= len(info_data):
                        total = len(info_data)
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page = int(re.findall('pageindex=(\d+?)&', response.url[response.url.rindex('?')+1:])[0]) + 1
                        data_url = re.sub('pageindex=\d+', 'pageindex={}'.format(page), response.url)
                        yield scrapy.Request(url=data_url, callback=self.parse_data_info, dont_filter=True,
                                             meta={'notice_type': response.meta['notice_type'],
                                                   'category': response.meta['category']})
            else:
                total = data_info['total']
                pages = int(math.ceil(total/50))
                self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                count = 0
                for page in range(1, pages + 1):
                    count += 1
                    data_url = re.sub('pageindex=\d+', 'pageindex={}'.format(page), response.url)
                    yield scrapy.Request(url=data_url, callback=self.parse_data_check,
                                         priority=((pages + 1) - count) * 50, dont_filter=True,
                                         meta={'notice_type': response.meta['notice_type'],
                                               'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')


    def parse_data_check(self, response):
        try:
            data_info = json.loads(response.text)['rows']
            count = 0
            for info in data_info:
                count += 1
                if '河北' in info['cityname']:
                    info_source = info['cityname']
                else:
                    info_source = '河北-' + info['cityname']
                title_name = info['ggname']
                pub_time = info['ggfbtime']
                info_url = self.query_url.format(info['ggcode'], info['ggtype'])
                data_info_url = self.base_url.format(info['ggcode'], info['ggtype'])
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=(len(data_info) - count) * 100,
                                     meta={'notice_type': response.meta['notice_type'],
                                           'title_name': title_name,
                                           'pub_time': pub_time,
                                           'info_source': info_source,
                                           'data_info_url': data_info_url,
                                           'category': response.meta['category']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            if json.loads(response.text)['tdata']['Data_content']:
                category = response.meta['category']
                origin = response.meta['data_info_url']
                info_source = response.meta['info_source']
                title_name = response.meta['title_name']
                pub_time = response.meta['pub_time']
                content = (json.loads(response.text)['tdata']['Data_content']).replace('\\', '').replace('%5C%22', '')

                if '测试' not in title_name:
                    notice_type = get_notice_type(title_name, response.meta['notice_type'])

                    files_text = etree.HTML(content)
                    keys_a = []
                    files_path = get_files(self.start_urls, origin, files_text, pub_time=pub_time,
                                           keys_a=keys_a, log=self.logger)

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
                    notice_item["category"] = category

                    yield notice_item
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_item {e}')


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_159_huizhaobiao_spider".split(" "))
    cmdline.execute("scrapy crawl province_159_huizhaobiao_spider -a sdt=2021-10-01 -a edt=2021-11-30".split(" "))
