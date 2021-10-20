#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-04-14
# @Describe: 台州市公共资源交易网 - 全量/增量脚本

import re
import math
import json
import scrapy
import random
import datetime
import requests
from lxml import etree
from ast import literal_eval
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'ZJ_city_3310_taizhou_spider'
    area_id = "3310"
    domain_url = "https://tzztb.zjtz.gov.cn"
    query_url = "https://tzztb.zjtz.gov.cn/tzcms/{}/index.htm"
    allowed_domains = ['tzztb.zjtz.gov.cn']
    area_province = "浙江-台州市公共资源交易服务平台"

    county_list = ["lh", "wl", "yh", "tt", "xj", "sm"]
    # 招标公告
    list_notice_category_num = ['jsgczhaobwjygs', "gcjyzhaobgg", 'gcjybzjtf', "zfcgcggg", "fscggg", "cqjycrgg",
                                "tzzycrgg", "tdjydcrgg", "xegccrgs", 'lhxjsgc', 'lhxzfcg', 'lhxcqjy', 'lhhqtjy',
                                'lhxtdjy', 'wlxjsgc', 'wlxzfcg', 'wlxcqjy',
                                'wlhqtjy', 'wlxtdjy', 'yhxjsgc', 'yhxzfcg', 'yhxcqjy', 'yhhqtjy', 'yhxtdjy', 'ttxjsgc',
                                'ttxzfcg', 'ttxcqjy', 'tthqtjy', 'ttxtdjy', 'xjxjsgc', 'xjxzfcg', 'xjxcqjy', 'xjhqtjy',
                                'xjxtdjy', 'smxjsgc', 'smxzfcg', 'smxcqjy', 'smhqtjy', 'smxtdjy']
    # 资格预审
    list_qualification_num = ['jsgcysgg', 'zgysgglhsjsgc', 'zgysggwlsjsgc', 'zgysggyhsjsgc', 'zgysggttsjsgc',
                              'zgysggxjsjsgc', 'zgysggsmsjsgc']
    # 资格预审结果公告
    list_qualification_advance_notice = ['gcjyysgs', 'zgysgslhsjsgc', 'zgysgswlsjsgc', 'zgysgsyhsjsgc', 'zgysgsttsjsgc',
                                         'zgysgsxjsjsgc', 'zgysgssmsjsgc']
    # 招标变更
    list_zb_abnormal_num = ['gcjybcwj', "zfcgdybc", "cqjycqxggg", "tzzycqhxggg", 'cqhxggglhsjsgc', 'cqhxgggwlsjsgc',
                            'cqhxgggyhsjsgc', 'cqhxgggttsjsgc', 'cqhxgggxjsjsgc', 'cqhxgggsmsjsgc']
    # 招标异常
    list_alteration_category_num = ['ycgg']
    # 中标预告
    list_win_advance_notice_num = ['gcjyzbgg', "cqjyzbhxrgs", 'pbgslhxjsgc', 'pbgslhxcqjy', 'pbgswlxjsgc',
                                   'pbgswlxcqjy', 'pbgsyhxjsgc', 'pbgsyhxcqjy', 'pbgsttxjsgc', 'pbgsttxcqjy',
                                   'pbgsxjxjsgc', 'pbgsxjxcqjy', 'pbgssmxjsgc', 'pbgssmxcqjy']
    # 中标公告
    list_win_notice_category_num = ['gcjyzbjg', "zfcgzbhxgs", "fszbgg", "gycjgs", "tzzygs", "tdcrgs", "xegccjgs",
                                    'zbgglhxjsgc', 'zbgglhxzfcg', 'zbgglhxcqjy', 'zbgglhxqtjy', 'zbgglhxtdjy',
                                    'zbggwlxjsgc', 'zbggwlxzfcg', 'zbggwlxcqjy', 'zbggwlxqtjy', 'zbggwlxtdjy',
                                    'zbggyhxjsgc', 'zbggyhxzfcg', 'zbggyhxcqjy', 'zbggyhxqtjy', 'zbggyhxtdjy',
                                    'zbggttxjsgc', 'zbggttxzfcg', 'zbggttxcqjy', 'zbggttxqtjy', 'zbggttxtdjy',
                                    'zbggxjxjsgc', 'zbggxjxzfcg', 'zbggxjxcqjy', 'zbggxjxqtjy', 'zbggxjxtdjy',
                                    'zbggsmxjsgc', 'zbggsmxzfcg', 'zbggsmxcqjy', 'zbggsmxqtjy', 'zbggsmxtdjy']
    # 其他
    list_qita_code = ["qtgg", "zfcgzqyj", "tdbzjtz", "gcjybzjtf", 'bzjthgslhsjsgc', 'bzjthgswlsjsgc', 'bzjthgsyhsjsgc',
                      'bzjthgsttsjsgc', 'bzjthgsxjsjsgc', 'bzjthgssmsjsgc']
    list_all_city = list_notice_category_num + list_qualification_num + list_qualification_advance_notice + \
                    list_zb_abnormal_num + list_alteration_category_num + list_win_advance_notice_num + \
                    list_win_notice_category_num + list_qita_code

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for city_item in self.list_all_city:
            city_url = self.query_url.format(city_item)
            yield scrapy.Request(url=city_url, priority=5, callback=self.parse_urls, meta={"city_item": city_item})

    def parse_urls(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 1
                li_list = response.xpath('//div[@class="List-Li FloatL"]/ul/li')
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./span/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                    info_url = response.url[:response.url.rindex('/') + 1] + 'index_{}.htm'
                    if num >= len(li_list):
                        pn += 1
                    else:
                        pn = 1
                    yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info)
            else:
                page_list = response.xpath('/html/body/div[2]/div[1]/ul/li/div/div/text()').get()
                total = re.findall('共(\d+).*', page_list)[0]  # 总条数
                pages = re.findall('.*\/(\d+)', page_list)[0]  # 总页数
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                if total == "1":
                    return
                else:
                    for num in range(1, int(pages) + 1):
                        url = "http://tzztb.zjtz.gov.cn/tzcms/{}/index_{}.htm".format(response.meta["city_item"], num)
                        yield scrapy.Request(url=url, priority=8, callback=self.parse_info,
                                             meta={"city_item": response.meta["city_item"]})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_info(self, response):
        try:
            tr_list = response.xpath('/html/body/div[2]/div[1]/ul/li/table/tr')
            for n, tr in enumerate(tr_list):
                if n == 0:
                    continue
                else:
                    info_source = tr.xpath("./td/text()").get()
                    title_name = tr.xpath("./td[2]/a/span/text()").get()
                    url = tr.xpath("./td[2]/a/@href").get()
                    pub_time = tr.xpath("./td[4]/text()").get()
                    # notice = tr.xpath("./td[3]/label/text()").get()
                    info_url = self.domain_url + url

                    # all_info_url = self.domain_url + li.xpath('./a/@href').get()
                    # category_name = li.xpath('./a/em/text()').get()
                    # pub_time = li.xpath('./span/text()').get()
                    category_name = response.meta["city_item"]
                    if category_name in self.list_notice_category_num:
                        notice = const.TYPE_ZB_NOTICE
                    elif category_name in self.list_qualification_num:
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif category_name in self.list_qualification_advance_notice:
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif category_name in self.list_win_advance_notice_num:
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif category_name in self.list_win_notice_category_num:
                        notice = const.TYPE_WIN_NOTICE
                    elif category_name in self.list_qita_code:
                        notice = const.TYPE_OTHERS_NOTICE
                    elif category_name in self.list_zb_abnormal_num:
                        notice = const.TYPE_ZB_ALTERATION
                    elif category_name in self.list_alteration_category_num:
                        notice = const.TYPE_ZB_ABNORMAL
                    else:
                        notice = 'null'
                    # info_url = "https://tzztb.zjtz.gov.cn/tzcms/gcjyzhaobgg/330694.htm"
                    yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True, priority=10,
                                         meta={'pub_time': pub_time, 'title_name': title_name,
                                               'info_source': info_source, 'notice_type': notice})

        except Exception as e:
            self.logger.error(f"parse_info:发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            print(origin)
            contents = response.xpath('//div[@class="content-text"]').get()
            category = response.xpath("//div[@class='outer-content']/p/a[3]/text()").get()
            files_path = {}
            files_list = []
            try:
                getfile_info_list = re.findall('Cms.attachment\("(.*?)","(.*?)","(.*?)","(.*?)"\)', response.text)
                for item in getfile_info_list:
                    base = item[0]
                    self.cid = item[1]
                    self.file_num = item[2]
                    if int(self.file_num) > 0:
                        file_info_url = "{}{}/attachment_url.jspx?cid={}&n={}".format(self.domain_url, base, self.cid, self.file_num)
                        response_dict = requests.get(file_info_url)
                        self.file_list = response_dict.content.decode('utf-8')
                        literal_eval(self.file_list)
                        file_neme_list = response.xpath("//table/tr/td/a/@title").getall()
                        file_neme_list.remove("文件下载")
                        for i, get_info in enumerate(literal_eval(self.file_list)):
                            temp_url = "{}/tzcms/attachment.jspx?cid={}&i={}{}".format(self.domain_url, self.cid, i, get_info)
                            file_path_str = "<a href='{}'>{}</a>".format(temp_url, file_neme_list[i])
                            files_list.append(file_path_str)
                            files_path[file_neme_list[i]] = temp_url
                        file_paths = "<br/>".join(files_list)
                        contents = re.sub("</div> </div>", "</div>{}</div>".format(file_paths), contents)

                if Notice_file := response.xpath('//div[@class="content-text"]/p/img/@src'):
                    keys = "notice_file"
                    files_path[keys] = Notice_file
                # if tr_list := response.xpath("//div[@class='content-box']/table[1]/tr"):
                #     for n, tr in enumerate(tr_list):
                #         if n == 0:
                #             continue
                #         else:
                #             keys = tr.xpath("./td[1]/a/text()").get()
                #             value = tr.xpath("./td[2]/a/@href").get()
                #             if "http" in value:
                #                 files_path[keys] = value
                #             else:
                #                 value = self.domain_url + value
                #                 files_path[keys] = value
            except Exception as e:
                print(e)
                self.logger.error(f"parse_item:获取文件失败 {e} {response.url=}")
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = response.meta["title_name"]
            notice_item["pub_time"] = response.meta["pub_time"]
            notice_item["info_source"] = response.meta["info_source"]
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = response.meta["notice_type"]
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl ZJ_city_3310_taizhou_spider".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3310_taizhou_spider -a sdt=2015-02-01 -a edt=2021-03-10".split(" "))
