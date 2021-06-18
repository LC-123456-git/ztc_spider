# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-17
# @Describe: 浙江省-湖州市-南浔区公共资源交易平台 - 全量/增量脚本
import re
import math
import json
import requests
import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3324_nanxun_spider'
    area_id = "3324"
    domain_url = "http://ggzy.nanxun.gov.cn/"
    query_url = "http://ggzy.nanxun.gov.cn/hzgov/openapi/info/ajaxpagelist.do?pagesize=15&"
    base_url = ''
    details_url = ''
    data_url = ''
    allowed_domains = ['ggzy.nanxun.gov.cn']
    area_province = "浙江省-湖州市-南浔区公共资源交易平台"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }

    # 招标公告
    list_notice_category_num = ['招标公告', '发包公告', '交易公告']
    # 中标公告
    list_win_notice_category_num = ['中标公告', '中标公示', '成交公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = ['招标答疑']
    # 中标预告
    list_win_advance_notice_num = []
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = []

    # category_url 链接
    category_url_list = [
                         'http://ggzy.nanxun.gov.cn/gcxmjy/fbgg/jsl/index.html', 'http://ggzy.nanxun.gov.cn/gcxmjy/fbgg/jtl/index.html',
                         'http://ggzy.nanxun.gov.cn/gcxmjy/fbgg/ssl/index.html', 'http://ggzy.nanxun.gov.cn/gcxmjy/zbgg/jsl/index.html',
                         'http://ggzy.nanxun.gov.cn/gcxmjy/zbgg/jtl/index.html', 'http://ggzy.nanxun.gov.cn/gcxmjy/zbgg/ssl/index.html',
                         'http://ggzy.nanxun.gov.cn/ysscjy/zbgg/index.html', 'http://ggzy.nanxun.gov.cn/ysscjy/zbgs/index.html',
                         'http://ggzy.nanxun.gov.cn/cqjy/gycqjy/gg/index.html', 'http://ggzy.nanxun.gov.cn/cqjy/gycqjy/gc/index.html ',
                         'http://ggzy.nanxun.gov.cn/cqjy/nczhcqjy/gg/index.html', 'http://ggzy.nanxun.gov.cn/cqjy/nczhcqjy/gc/index.html',
                         'http://ggzy.nanxun.gov.cn/zbdy/index.html'
                         ]

    category_name_list = ['发包公告', '发包公告', '发包公告', '中标公告', '中标公告', '中标公告', '招标公告', '中标公示',
                          '交易公告', '交易公示', '交易公告', '交易公示', '招标答疑']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_page(self, url):
        response = requests.get(url=url, headers=self.headers).content.decode('utf-8')
        html = etree.HTML(response)
        page_text = ''.join(html.xpath('//td[@align="center"]/script[2]/text()')).strip()
        return page_text


    def start_requests(self):
        for url, name in zip(self.category_url_list, self.category_name_list):
            if 'gcxmjy' in url:
                classifyShow = '工程项目交易'
            elif 'ysscjy' in url:
                classifyShow = '要素市场交易'
            elif 'gycqjy' in url:
                classifyShow = '国有产权交易'
            elif 'nczhcqjy' in url:
                classifyShow = '农村综合产权交易'
            else:
                classifyShow = '工程'
            if name in self.list_notice_category_num:        # 招标公告
                notice = const.TYPE_ZB_NOTICE
            elif name in self.list_win_notice_category_num:  # 中标公告
                notice = const.TYPE_ZB_NOTICE
            elif name in self.list_zb_abnormal_num:          # 招标变更
                notice = const.TYPE_ZB_NOTICE
            else:
                notice = ''
            if notice:
                yield scrapy.Request(url=url, callback=self.parse_urls, priority=50,
                                     meta={'classifyShow': classifyShow,
                                           'notice': notice})

    def parse_urls(self, response):
        try:
            code = ''.join(re.findall('(.*?);.*', self.get_page(response.url))).replace('var', '').strip().lower()
            if self.enable_incr:
                page = 1
                num = 0
                td_list = response.xpath('//div[@id="ajaxpage-list"]/table/tr/td[3]')
                for td in range(len(td_list)):
                    td_url = td_list[td]['url']
                    t_name = td_list[td]['title']
                    pub_time = td_list[td].xpath('./span/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(td_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        yield scrapy.Request(url=td_url, callback=self.parse_item, priority=150,
                                             meta={'t_name': t_name, 'notice': response.meta['notice'],
                                                   'classifyShow': response.meta['classifyShow'],
                                                   'pub_time': pub_time})
                    if num >= len(td_list):
                        page += 1
                        info_url = self.query_url + code + '&pageno={}'
                        yield scrapy.Request(url=info_url.format(page), callback=self.parse_info, priority=100,
                                             meta={'classifyShow': response.meta['classifyShow'],
                                                   'notice': response.meta['notice']})

            page = json.loads(re.findall('pagesData=(.*?);.*', self.get_page(response.url))[0])['pageTotal']
            total = int(page) * 15
            self.logger.info(f"post 初始总数提取成功 {total=} {response.url=}")

            for num in range(1, int(page)+1):
                info_url = self.query_url + code + '&pageno={}'.format(num)
                yield scrapy.Request(url=info_url, callback=self.parse_info,
                                     meta={'classifyShow': response.meta['classifyShow'],
                                           'notice': response.meta['notice']})

        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_info(self, response):
        try:
            td_list = json.loads(response.text)['infolist']
            for td in td_list:
                _url = td['url']
                t_name = td['title']
                pub_time = td['daytime']
                yield scrapy.Request(url=_url, callback=self.parse_item, priority=150,
                                     meta={'t_name': t_name, 'notice': response.meta['notice'],
                                           'classifyShow': response.meta['classifyShow'],
                                           'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"parse_data_info 发起数据请求失败  {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            info_source = self.area_province
            classifyShow = response.meta['classifyShow'] or ''
            title_name = response.meta.get("t_name") or ''
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            origin = response.url
            if re.search(r"流标|废标|终止|中止", title_name):  # 招标异常
                notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|答疑|澄清|补充|延期", title_name):  # 招标变更
                notice_type = const.TYPE_ZB_ALTERATION
            elif re.search(r"候选人|预成交|侯选人", title_name):  # 中标预告
                notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"中标|成交|成交公示", title_name):  # 中标公告
                notice_type = const.TYPE_WIN_NOTICE
            else:
                notice_type = response.meta['notice']
            files_path = {}
            # 判断content 里面是否有正文
            if response.xpath('//div[@id="zoom"]'):
                content = response.xpath('//div[@id="zoom"]').get()
                respon = etree.HTML(content)
                if respon.xpath("//p//a/@href"):
                    str_content = respon.xpath("//p//a")
                    for con in str_content:
                        # 判断href 是否带 http头
                        if con.xpath('./@href'):
                            if 'http' not in con.xpath('./@href')[0]:
                            # 判断href 是不是email
                                if con.xpath('./@href')[0] not in re.findall('.*[a-zA-Z0-9]{0,19}@[a-zA-Z0-9].*', con.xpath('./@href')[0]):
                                    value = 'http' + con.xpath('./@href')[0]
                                    if con.xpath('.//text()'):
                                        keys = ''.join(con.xpath('.//text()')[0]).strip()
                                        files_path[keys] = value
                            else:
                                if con.xpath('./@href')[0] not in re.findall('.*[a-zA-Z0-9]{0,19}@[a-zA-Z0-9].*', con.xpath('./@href')[0]):
                                    value = con.xpath('./@href')[0]
                                    if con.xpath('.//text()'):
                                        keys = ''.join(con.xpath('.//text()')[0]).strip()
                                        files_path[keys] = value

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
    cmdline.execute("scrapy crawl ZJ_city_3324_nanxun_spider".split(" "))




