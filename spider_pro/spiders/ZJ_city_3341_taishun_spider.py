#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-20
# @Describe: 浙江省温州市泰顺县人民政府 - 全量/增量脚本

import re
import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_files, get_notice_type


class MySpider(CrawlSpider):
    name = 'ZJ_city_3341_taishun_spider'
    area_id = "3341"
    domain_url = "http://www.ts.gov.cn"
    start_url = 'http://117.149.227.75:81'
    query_url = "http://117.149.227.75:81/TPFront/jyxx/"
    base_url = 'http://117.149.227.75:81/TPFront/ShowInfo/MoreInfoListjygg.aspx?categoryNum={}&Paging={}'
    allowed_domains = ['ts.gov.cn']
    area_province = '浙江省温州市泰顺县人民政府'

    # 招标预告
    list_tender_notice_num = ['招标文件预公示', '采购文件征询']
    # 招标公告
    list_notice_category_name = ['招标公告', '单一来源采购公示', '采购公告', '出让公告', '乡镇交易公告', '交易公告']
    # 招标变更
    list_zb_abnormal_name = ["答疑与补充", "更正公告", "乡镇公告变更", "变更公告"]
    # 中标预告
    list_win_advance_notice_name = ['候选公示', '中标公示']
    # 中标公告
    list_win_notice_category_name = ['中标结果', '出让结果', '中标公告', '乡镇中标公告']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['合同订立信息', '采购合同公示', '进口产品公示']

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
            lis_list = response.xpath('//div[@class="left-nav"]/table/tr')[2::2]
            li_list = response.xpath('//div[@class="left-nav"]/table/tr')[1::2]
            for li, lis in zip(li_list, lis_list):
                category = li.xpath('./td/font/text()').get()
                notices_list = lis.xpath('./td/table/tr')
                for notice in notices_list:
                    if notice.xpath('./td/a/@href'):
                        notice_code = notice.xpath('./td/a/@href').get()
                        notice_name = notice.xpath('./td/a/font/text()').get()
                        if notice_name in self.list_notice_category_name:                   # 招标公告
                            notice = const.TYPE_ZB_NOTICE
                        elif notice_name in self.list_zb_abnormal_name:                     # 招标变更
                            notice = const.TYPE_ZB_ALTERATION
                        elif notice_name in self.list_win_advance_notice_name:              # 中标预告
                            notice = const.TYPE_WIN_ADVANCE_NOTICE
                        elif notice_name in self.list_win_notice_category_name:             # 中标公告
                            notice = const.TYPE_WIN_NOTICE
                        elif notice_name in self.list_tender_notice_num:                    # 招标预告
                            notice = const.TYPE_ZB_ADVANCE_NOTICE
                        elif notice_name in self.list_qita_num:                             # 其他
                            notice = const.TYPE_OTHERS_NOTICE
                        else:
                            notice = ''
                        if notice:
                            notice_url = self.base_url.format(notice_code[notice_code.rindex('/') + 1:], 1)
                            yield scrapy.Request(url=notice_url, callback=self.parse_data_info, dont_filter=True,
                                                 meta={'category': category,
                                                       'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")


    def parse_data_info(self, response):
        try:
            info_url = response.url.replace(''.join(response.url).split('/')[-1], 'Paging={}')
            if self.enable_incr:
                li_list = response.xpath('//div[@id="infolist"]/table/tr')[:-1]
                num = 0
                for info_num in range(len(li_list)):
                    _url = self.start_url + li_list[info_num].xpath('./td[2]/a/@href').get()
                    title_name = li_list[info_num].xpath('./td[2]/a/@title').get()
                    pub_time = ''.join(li_list[info_num].xpath('./td[last()]/text()').get()).strip()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=_url, callback=self.parse_item, priority=200, dont_filter=True,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice'],
                                                   'pub_time': pub_time,
                                                   'title_name': title_name})
                    if num >= int(len(li_list)):
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page_num = int(re.findall('.*=(\d+)', response.url[response.url.rindex('&') + 1:])[0])
                        page_num += 1
                        yield scrapy.Request(url=info_url.format(page_num),
                                             callback=self.parse_data_info,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice']})
            else:
                pages = re.findall('^\/(\d+)', response.xpath('//div[@class="pagemargin"]//td[@class="huifont"]/text()').get())[0]
                total = int(pages) * 15
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(1, int(pages) + 1):
                    yield scrapy.Request(url=info_url.format(num), callback=self.parse_data_check,
                                         meta={'category': response.meta['category'],
                                               'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            li_list = response.xpath('//div[@id="infolist"]/table/tr')[:-1]
            for info in li_list:
                info_url = self.domain_url + info.xpath('./td[2]/a/@href').get()
                title_name = info.xpath('./td[2]/a/@title').get()
                pub_time = ''.join(info.xpath('./td[last()]/text()').get()).strip()
                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=200,
                                     meta={'category': response.meta['category'],
                                           'notice': response.meta['notice'],
                                           'pub_time': pub_time,
                                           'title_name': title_name})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            category = response.meta['category']
            info_source = self.area_province
            title_name = response.meta['title_name']
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                if notice_type:
                    content = response.xpath('//td[@id="TDContent"]').get()
                    files_text = etree.HTML(content)
                    keys_a = []
                    files_path = get_files(self.domain_url, origin, files_text, keys_a=keys_a)

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

if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl ZJ_city_3341_taishun_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3341_taishun_spider -a sdt=2021-06-01 -a edt=2021-07-20".split(" "))


