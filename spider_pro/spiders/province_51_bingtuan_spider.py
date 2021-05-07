#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-22
# @Describe: 兵团公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time
# TODO 完成

class MySpider(Spider):
    name = "province_51_bingtuan_spider"
    area_id = "51"
    allowed_domains = ['ggzy.xjbt.gov.cn']
    url = 'http://ggzy.xjbt.gov.cn'
    domain_url = "http://ggzy.xjbt.gov.cn/TPFront/jyxx/"
    area_province = "兵团"

    #招标公告
    list_notice_category_num = ['招标公告', '单一来源公示', '采购公告', '交易公告']
    # 招标异常
    list_alteration_category_num = []
    # 中标公告
    list_win_notice_category_num = ['中标结果公告', '结果公示', '成交公示']
    #招标变更
    list_zb_abnormal = ['答疑澄清', '变更公告']
    #中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    #资格预审结果公告
    list_qualification_num = ['资格预审公示']
    # 其他公告
    list_others_notice_num = ['合同公示']


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_categoy_urls)

    def parse_categoy_urls(self, response):
        try:
            li_list = response.xpath('//td[@class="LeftMenu"]/a')
            print(li_list)
            # for li in li_list:
            #     categoy = li.xpath('./font/text()').get()
            #     classify_url_list = self.url + li.xpath('./@href').get()
            #     print(classify_url_list)
                # yield scrapy.Request(url=classify_url_list, callback=self.parse_categoy_data_urls,
                #                      meta={'categoy': categoy})
        except Exception as e:
            self.logger.error(f"获取的url错误 {response.meta=} {e} {response.url=}")

    def parse_categoy_data_urls(self, response):
        try:
            li_list = response.xpath('//*/tr')
            for li in li_list:
                if li.xpath('./td[@class="MoreinfoColor"]/text()'):
                    type_name = li.xpath('./td[@class="MoreinfoColor"]/text()').get()
                    type_url = response.url + li.xpath('./td[@align="right"]/a/@href').get()        #获取类型url的code 拼接详情页的url
                    print(type_url)
                    yield scrapy.Request(url=type_url, callback=self.parse_all_urls,
                                 meta={'categoy': response.meta.get('categoy'), 'type_name': type_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_all_urls(self, response):
        try:
            pages = re.findall('/(\d+)', response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get())[0]    #总页数
            total = int(pages) * 20              #总条数
            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            urls_list = response.url + '?Paging={}'
            for i in range(1, int(pages) + 1):
                urls_lists = urls_list.format(i)
                print(urls_lists)
                yield scrapy.Request(url=urls_lists, callback=self.parse_all_data,
                                     meta={'categoy': response.meta.get('categoy'), 'type_name': response.meta['type_name']})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_all_data(self, response):
        try:
            name_list = response.xpath('//div[@align="center"]/table/tr')[:-1:2]
            for name in name_list:
                title_url = self.url + name.xpath('./td[2]/a/@href').get()
                title_name = name.xpath('./td[2]/a/@title').get()
                pub_time = ''.join(name.xpath('./td[3]/text()').get()).replace('[', '').replace(']', '')
                info_source = ''.join(name.xpath('./td[2]/a/font/text()').get()).replace('[', '').replace(']', '')
                type_name = response.meta['type_name']
                if type_name in self.list_notice_category_num:                   #招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif type_name in self.list_win_notice_category_num:             #中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif type_name in self.list_zb_abnormal:                         #招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif type_name in self.list_win_advance_notice_num:              #中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif type_name in self.list_qualification_num:                   #资格预审结果公告
                    notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif type_name in self.list_others_notice_num:                    #其他公告
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''

                if re.search(r'变更| 更正 | 澄清', title_name):                            #招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'中标候选人公示', title_name):                               #中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'资格预审', title_name):                                     #资格预审结果公告
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'终止| 中止 | 异常| 废标 |流标', title_name):                  # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'终止| 中止 | 异常| 废标 |流标', title_name):                   # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    notice_type = notice
                # print(title_url, title_name, notice_type, pub_time)
                yield scrapy.Request(url=title_url, callback=self.parse_itme,
                                     meta={'categoy': response.meta.get('categoy'), 'type_name': response.meta['type_name'],
                                           'notice_type': notice_type, 'pub_time': pub_time, 'info_source': info_source,
                                           'title_name': title_name})

        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_itme(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            if response.meta['info_source']:
                info_source = f"{self.area_province}-{response.meta['info_source']}"
            else:
                info_source = self.area_province
            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)

            title_name = response.meta['title_name']
            category = response.meta['categoy']
            notice_type = response.meta['notice_type']
            files_path = {}
            if response.xpath('//table[@id="tblInfo"]/tr[@id="trAttach"]/td/table[@id="filedown"]/tr/td/b/table[@id="filedown"]/tr'):
                content = response.xpath('//table[@id="tblInfo"]').get()
                pattern = re.compile(r'<td id="tdTitle".*?>(.*?)</td>', re.S)
                contents = content.replace(re.findall(pattern, content)[0], '')
                conet_list = response.xpath('//table[@id="tblInfo"]/tr[@id="trAttach"]/td/table[@id="filedown"]/tr/td/b/table[@id="filedown"]/tr')
                for con in conet_list:
                    values = con.xpath('./td/a/@href').get()
                    keys = con.xpath('./td/a/font/text()').get()
                    files_path[keys] = values

                notice_item = NoticesItem()
                notice_item["origin"] = origin
                notice_item["title_name"] = title_name
                notice_item["pub_time"] = pub_time
                notice_item["info_source"] = info_source
                notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                notice_item["files_path"] = 'null' if not files_path else files_path
                notice_item["content"] = contents
                notice_item["area_id"] = self.area_id
                notice_item["notice_type"] = notice_type
                notice_item["category"] = category
                print(notice_item)
                yield notice_item
            else:
                notice_item = NoticesItem()
                content = response.xpath('//table[@id="tblInfo"]').get()
                pattern = re.compile(r'<td id="tdTitle".*?>(.*?)</td>', re.S)
                contents = content.replace(re.findall(pattern, content)[0], '')
                notice_item["origin"] = origin
                notice_item["title_name"] = title_name
                notice_item["pub_time"] = pub_time
                notice_item["info_source"] = info_source
                notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                notice_item["files_path"] = 'NULL' if not files_path else files_path
                notice_item["content"] = contents
                notice_item["area_id"] = self.area_id
                notice_item["notice_type"] = notice_type
                notice_item["category"] = category
                print(notice_item)
                # yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_51_bingtuan_spider".split(" "))


























