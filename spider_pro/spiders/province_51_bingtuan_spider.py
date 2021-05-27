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

from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element


# TODO 完成

class MySpider(Spider):
    name = "province_51_bingtuan_spider"
    area_id = "51"
    allowed_domains = ['ggzy.xjbt.gov.cn']
    start_url = 'http://ggzy.xjbt.gov.cn'
    domain_url = "http://ggzy.xjbt.gov.cn/TPFront/jyxx/"
    area_province = "兵团公共资源交易网"

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
        info_url = 'http://ggzy.xjbt.gov.cn/TPFront/infodetail/?infoid=6bb01a91-3b84-490d-8daf-0de63e515b26&CategoryNum=004001002'
        yield scrapy.Request(url=info_url, callback=self.parse_itme)
        # yield scrapy.Request(url=self.domain_url, callback=self.parse_categoy_urls)

    def parse_categoy_urls(self, response):
        try:
            li_list = response.xpath('//td[@class="LeftMenu"]/a')
            for li in li_list:
                categoy = li.xpath('./font/text()').get()
                classify_url_list = self.url + li.xpath('./@href').get()
                # print(categoy, classify_url_list)
                yield scrapy.Request(url=classify_url_list, callback=self.parse_categoy_data_urls,
                                     meta={'categoy': categoy})
        except Exception as e:
            self.logger.error(f"获取的url错误 {response.meta=} {e} {response.url=}")

    def parse_categoy_data_urls(self, response):
        try:
            li_list = response.xpath('//td[@background="/TPFront/webimages/sub_01_bg.gif"]/table/tr')
            for li in li_list:
                if li.xpath('./td[@class="MoreinfoColor"]/text()'):
                    type_name = li.xpath('./td[@class="MoreinfoColor"]/text()').get()
                    type_url = response.url + li.xpath('./td[@align="right"]/a/@href').get()        #获取类型url的code 拼接详情页的url
                    if type_name in self.list_notice_category_num:         # 招标公告
                        notice = const.TYPE_ZB_NOTICE
                    elif type_name in self.list_win_notice_category_num:   # 中标公告
                        notice = const.TYPE_WIN_NOTICE
                    elif type_name in self.list_zb_abnormal:               # 招标变更
                        notice = const.TYPE_ZB_ALTERATION
                    elif type_name in self.list_win_advance_notice_num:    # 中标预告
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif type_name in self.list_qualification_num:         # 资格预审结果公告
                        notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                    elif type_name in self.list_others_notice_num:         # 其他公告
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=type_url, callback=self.parse_all_urls, priority=50,
                                             meta={'categoy': response.meta.get('categoy'), 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_all_urls(self, response):
        try:
            urls_list = response.url + '?Paging={}'
            if self.enable_incr:
                nums = 1
                page = 1
                li_list = response.xpath('//div[@align="center"]/table/tr')[:-1:2]
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./td[3]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        nums += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    if li >= nums:
                        page += 1
                    else:
                        page = 1
                    yield scrapy.Request(url=urls_list.format(page), callback=self.parse_all_data, priority=100,
                                         meta={'categoy': response.meta.get('categoy'),
                                               'notice': response.meta['notice']})

            else:
                pages = re.findall('/(\d+)', response.xpath('//div[@class="pagemargin"]/div/table/tr/td[@class="huifont"]/text()').get())[0]    #总页数
                total = int(pages) * 20              #总条数
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for i in range(1, int(pages) + 1):
                    yield scrapy.Request(url=urls_list.format(i), callback=self.parse_all_data, priority=100,
                                         meta={'categoy': response.meta.get('categoy'),
                                               'notice': response.meta['notice']})

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
                if re.search(r'变更|更正|澄清', title_name):                              # 招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'中标候选人公示', title_name):                               # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'资格预审', title_name):                                     # 资格预审结果公告
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'终止|中止|异常|废标|流标', title_name):                 # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'终止|中止|异常|废标|流标', title_name):                  # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    notice_type = response.meta['notice']
                # print(title_url, title_name, notice_type, pub_time)
                yield scrapy.Request(url=title_url, callback=self.parse_itme, priority=150,
                                     meta={'categoy': response.meta.get('categoy'),
                                           'notice_type': notice_type,
                                           'pub_time': pub_time,
                                           'info_source': info_source,
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
            content = response.xpath('//table[@id="tblInfo"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'td', 'id', 'tdTitle')

            # 去除 下方的文件
            _, content = remove_specific_element(content, 'td', 'style', 'border:0;margin:0 auto;')

            _, content = remove_specific_element(content, 'p', 'align', 'center', index=1)

            files_path = {}
            files_cont = etree.HTML(content)
            suffix_list = ['html', 'com', 'com/', 'cn', 'cn/']
            if files_cont.xpath('//table[@id="filedown"]//a/@href'):
                cont_list = files_cont.xpath('//table[@id="filedown"]//a')
                for cont in cont_list:
                    if cont.xpath('./@href'):
                        values = cont.xpath('./@href')[0]
                        if ''.join(values).split('.')[-1] not in suffix_list:
                            if 'http://www' not in values:
                                value = self.start_url + values
                            else:
                                value = values
                            if cont.xpath('.//text()'):
                                key = ''.join(cont.xpath('.//text()')).strip()
                                files_path[key] = value

            notice_item = NoticesItem()
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

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_51_bingtuan_spider".split(" "))


























