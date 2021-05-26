#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-25
# @Describe: 陕西公共资源交易平台 - 全量/增量脚本
#
import re
import math
import json
import scrapy
import random
import urllib
import datetime
from lxml import etree


from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element




class MySpider(CrawlSpider):
    name = 'province_45_shanxi_spider'
    area_id = "45"
    domain_url = "http://www.sxggzyjy.cn"
    query_url = "http://www.sxggzyjy.cn/jydt/001001/001001001/subPage_jyxx.html"
    allowed_domains = ['sxggzyjy.cn']
    area_province = '陕西'

    # 招标公告
    list_notice_category_num = ['http://www.sxggzyjy.cn/jydt/001001/001001001/001001001001/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001002/001001002001/subPage_jyxx.html',
                                 'http://www.sxggzyjy.cn/jydt/001001/001001003/001001003001/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001004/001001004001/subPage_jyxx.html',
                                 'http://www.sxggzyjy.cn/jydt/001001/001001006/001001006001/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001008/001001008001/subPage_jyxx.html',
                                 'http://www.sxggzyjy.cn/jydt/001001/001001013/001001013001/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001014/001001014001/subPage_jyxx.html',
                                 'http://www.sxggzyjy.cn/jydt/001001/001001012/001001012001/subPage_jyxx.html']
    # 招标变更
    list_zb_abnormal_num = ['http://www.sxggzyjy.cn/jydt/001001/001001001/001001001002/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001002/001001002003/subPage_jyxx.html',
                             'http://www.sxggzyjy.cn/jydt/001001/001001004/001001004002/subPage_jyxx.html']
    # 中标预告
    list_win_advance_notice_num = ['http://www.sxggzyjy.cn/jydt/001001/001001001/001001001005/subPage_jyxx.html']
    # 中标公告
    list_win_notice_category_num = ['http://www.sxggzyjy.cn/jydt/001001/001001001/001001001003/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001002/001001002002/subPage_jyxx.html',
                                     'http://www.sxggzyjy.cn/jydt/001001/001001003/001001003002/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001004/001001004003/subPage_jyxx.html',
                                     'http://www.sxggzyjy.cn/jydt/001001/001001008/001001008002/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001013/001001013002/subPage_jyxx.html',
                                     'http://www.sxggzyjy.cn/jydt/001001/001001014/001001014002/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001012/001001012002/subPage_jyxx.html']
    # 招标异常
    list_alteration_category_num = ['http://www.sxggzyjy.cn/jydt/001001/001001001/001001001004/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001004/001001004004/subPage_jyxx.html']
    # 其他
    list_qita_num = ['http://www.sxggzyjy.cn/jydt/001001/001001006/001001006002/subPage_jyxx.html', 'http://www.sxggzyjy.cn/jydt/001001/001001006/001001006003/subPage_jyxx.html',
                      'http://www.sxggzyjy.cn/jydt/001001/001001006/001001006004/subPage_jyxx.html']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        # info_url = 'http://www.sxggzyjy.cn/jydt/001001/001001001/001001001001/20210521/ff808081796a5c95017988afe62b1c40.html'
        # yield scrapy.Request(url=info_url, callback=self.parse_item)
        yield scrapy.Request(url=self.query_url, callback=self.parse_urls)

    def parse_urls(self, response):
        try:
            li_list = response.xpath('//ul[@class="wb-tree-sub"]/li')
            for itmes in li_list:
                itmes_list = itmes.xpath('./ul/li')
                category = itmes.xpath('./h3/a/text()').get()
                for itme in itmes_list:
                    info_url = self.domain_url + itme.xpath('./a/@href').get()
                    if info_url in self.list_notice_category_num:
                        notice = const.TYPE_ZB_NOTICE
                    elif info_url in self.list_zb_abnormal_num:
                        notice = const.TYPE_ZB_ALTERATION
                    elif info_url in self.list_win_advance_notice_num:
                        notice = const.TYPE_WIN_ADVANCE_NOTICE
                    elif info_url in self.list_win_notice_category_num:
                        notice = const.TYPE_WIN_NOTICE
                    elif info_url in self.list_alteration_category_num:
                        notice = const.TYPE_ZB_ABNORMAL
                    elif info_url in self.list_qita_num:
                        notice = const.TYPE_OTHERS_NOTICE
                    else:
                        notice = ''
                    if notice:
                        yield scrapy.Request(url=info_url, callback=self.parse_data_urls, priority=50,
                                             meta={'category': category, 'notice': notice})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_urls {e} {response.url=}")


    def parse_data_urls(self, response):
        try:
            if response.xpath('//div[@class="ewb-page"]/ul/li/span[@id="index"]/text()'):
                pages = ''.join(re.findall('/(\d+)', response.xpath('//div[@class="ewb-page"]/ul/li/span[@id="index"]/text()').get()))
                data_info_urls = re.sub('subPage_jyxx', '{}', response.url)
                self.logger.info(f"本次获取总条数为：{int(pages) * 10}")
                if self.enable_incr:
                    page = 1
                    nums = 1
                    data_li_list = response.xpath('//div[@id="categorypagingcontent"]/ul/li')
                    for li in range(len(data_li_list)):
                        put_time = data_li_list[li].xpath('./span/text()').get()
                        put_time = get_accurate_pub_time(put_time)
                        x, y, z = judge_dst_time_in_interval(put_time, self.sdt_time, self.edt_time)
                        if x:
                            nums += 1
                            total = int(len(data_li_list))
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        if li >= nums:
                            page += 1
                        else:
                            page = 1
                        yield scrapy.Request(url=data_info_urls.format(page), callback=self.parse_data_info, priority=100,
                                             meta={"category": response.meta['category'], 'notice': response.meta['notice']})
                else:
                    for num in range(1, int(pages) + 1):
                        yield scrapy.Request(url=data_info_urls.format(num), callback=self.parse_data_info, priority=100,
                                             meta={"category": response.meta['category'],
                                                       'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_urls {response.meta=} {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            li_list = response.xpath('//div[@id="categorypagingcontent"]/ul/li')
            for li in li_list:
                title_name = li.xpath('./a/@title').get()
                put_time = li.xpath('./span/text()').get()
                data_info_url = self.domain_url + li.xpath('./a/@href').get()
                if re.search(r'资格预审', title_name):
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'变更|更正|澄清', title_name):
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'终止|中止|异常|废标|流标', title_name):
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'候选人', title_name):
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                else:
                    notice_type = response.meta['notice']
                yield scrapy.Request(url=data_info_url, callback=self.parse_item, priority=150,
                                     meta={"category": response.meta['category'], "title_name": title_name,
                                           "put_time": put_time, 'notice_type': notice_type})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误parse_data_info {response.meta=} {e} {response.url=}")


    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            source = re.findall('【信息来源：(.*)】', ''.join(response.xpath('//div[@class="info-source"]/text()').extract()))[0]
            if source:
                info_source = self.area_province + source
            else:
                info_source = self.area_province
            category = response.meta.get("category")
            title_name = response.meta['title_name']
            pub_time = response.meta['put_time']
            notice_type = response.meta['notice_type']
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//div[@class="ewb-main"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'h3', 'class', 'article-title')
            # 去除 info信息 来源等信息
            _, content = remove_specific_element(content, 'div', 'class', 'info-source')
            # 去除 视力保护色
            _, content = remove_specific_element(content, 'font', 'style', 'float: right;margin-right: 10%;margin-top: 10px;')
            # 去除 登录系统
            _, content = remove_specific_element(content, 'a', 'class', 'ewb-tab-btn3')
            # 去除 提醒等字段
            _, content = remove_specific_element(content, 'font', 'color', 'red')

            _, content = remove_specific_element(content, 'div', 'id', 'cont001001004')

            files_path = {}
            suffix_list = ['html', 'com', 'com/', 'cn', 'cn/']
            files_text = etree.HTML(content)
            if files_text.xpath('//a/@href'):
                files_list = files_text.xpath('//a')
                for cont in files_list:
                    if cont.xpath('./@href'):
                        values = cont.xpath('./@href')[0]
                        if ''.join(values).split('.')[-1] not in suffix_list:
                            if 'http://www' not in values:
                                value = self.domain_url + values
                            else:
                                value = values
                            if cont.xpath('.//text()'):
                                keys = ''.join(cont.xpath('.//text()')).strip()
                                files_path[keys] = value

            # if response.xpath('//div[@class="ewb-main"]//p/a') or response.xpath('//div[@id="mainContent"]//span/a') or\
            #         response.xpath('//div[@id="epoint-article-content jynr news_content"]/p/a'):
            #     pass
            # #     key_name = ['png', 'jpg', 'jepg', 'doc', 'docx', 'pdf', 'xls']
            # #     key_list = ['www.creditchina.gov.cn', 'hbtpwq@shaanxi.gov.cn', '100290295@qq.com']
            #     if response.xpath('//div[@class="ewb-main"]/div[@id="mainContent"]/p/a') or response.xpath('//div[@id="epoint-article-content jynr news_content"]/p/a'):
            #         conet_list = response.xpath('//div[@class="ewb-main"]/div[@id="mainContent"]/p') or response.xpath('//div[@id="epoint-article-content jynr news_content"]/p')
            #         pass
            # #         num = 1
            # #         for con in conet_list:
            # #             if con.xpath('./a/@href').get() and con.xpath('./a/text()').get():
            # #                 value = con.xpath('./a/@href').get()
            # #                 if 'http' in value:
            # #                      value = value
            # #                 else:
            # #                     value = self.domain_url + value
            # #                 if con.xpath('./a/text()').get():
            # #                     keys = con.xpath('./a/text()').get()
            # #                     if keys not in key_list:
            # #                         if value[value.rindex('.') + 1:] in key_name:
            # #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            # #                             files_path[keys] = value
            # #                 num += 1
            # #             else:
            # #                 pass
            # #
            # #     elif response.xpath('//div[@class="ewb-main"]/p/a'):
            # #         dict = response.xpath('//div[@class="ewb-main"]/p')
            # #         num = 1
            # #         for itme in dict:
            # #             if itme.xpath('./a/@href').get() and itme.xpath('./a/text()').get():
            # #                 value = itme.xpath('./a/@href').get()
            # #                 if 'http' in value:
            # #                      value = value
            # #                 else:
            # #                     value = self.domain_url + value
            # #                 if itme.xpath('./a/text()').get():
            # #                     keys = itme.xpath('./a/text()').get()
            # #                     if keys not in key_list:
            # #                         if keys not in re.findall(r'[0-9a-zA-Z_]{0,19}@[a-zA-Z0-9].*', keys)[0]:
            # #                             files_path[keys] = value
            # #                         elif value[value.rindex('.') + 1:] in key_name:
            # #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            # #                             files_path[keys] = value
            # #                 num += 1
            # #             else:
            # #                 pass
            #
            #     elif response.xpath('//div[@id="mainContent"]/p/span/a'):
            #         pass
            # #         conet_list = response.xpath('//div[@id="mainContent"]/p/span/a')
            # #         num = 1
            # #         for con in conet_list:
            # #             if con.xpath('./@href').get() and con.xpath('./span/span/text()').get():
            # #                 value = self.domain_url + con.xpath('./@href').get()
            # #                 if 'http' in value:
            # #                      value = value
            # #                 else:
            # #                     value = self.domain_url + value
            # #                 if con.xpath('./span/span/text()').get():
            # #                     keys = con.xpath('./span/span/text()').get()
            # #                     if keys not in key_list:
            # #                         if keys not in re.findall(r'[0-9a-zA-Z_]{0,19}@[a-zA-Z0-9].*', keys)[0]:
            # #                             files_path[keys] = value
            # #                         elif value[value.rindex('.') + 1:] in key_name:
            # #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            # #                             files_path[keys] = value
            # #                 num += 1
            # #             elif con.xpath('./@href').get() and con.xpath('./span/text()').get():
            # #                 value = self.domain_url + con.xpath('./@href').get()
            # #                 if 'http' in value:
            # #                      value = value
            # #                 else:
            # #                     value = self.domain_url + value
            # #                 if con.xpath('./span/text()').get():
            # #                     keys = con.xpath('./span/text()').get()
            # #                     if keys not in key_list:
            # #                         if keys not in re.findall(r'[0-9a-zA-Z_]{0,19}@[a-zA-Z0-9].*', keys)[0]:
            # #                             files_path[keys] = value
            # #                         elif value[value.rindex('.') + 1:] in key_name:
            # #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            # #                             files_path[keys] = value
            # #                 num += 1
            # #             elif con.xpath('./@href').get() and con.xpath('./span/font/span/text()').get():
            # #                 value = self.domain_url + con.xpath('./@href').get()
            # #                 if 'http' in value:
            # #                      value = value
            # #                 else:
            # #                     value = self.domain_url + value
            # #                 if con.xpath('./span/font/span/text()').get():
            # #                     keys = con.xpath('./span/font/span/text()').get()
            # #                     if keys not in key_list:
            # #                         if keys not in re.findall(r'[0-9a-zA-Z_]{0,19}@[a-zA-Z0-9].*', keys)[0]:
            # #                             files_path[keys] = value
            # #                         elif value[value.rindex('.') + 1:] in key_name:
            # #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            # #                             files_path[keys] = value
            # #                 num += 1
            # #             else:
            # #                 pass
            # #
            #
            #     elif response.xpath('//div[@id="mainContent"]/div/span/span/a'):
            #         pass
            #         conet_list = response.xpath('//div[@id="mainContent"]/div/span/span/a')
            #         num = 1
            #         for con in conet_list:
            #             if con.xpath('./@href').get() and con.xpath('./span/text()').get():
            #                 value = con.xpath('./@href').get()
            #                 if 'http' in value:
            #                      value = value
            #                 else:
            #                     value = self.domain_url + value
            #                 if con.xpath('./span/text()').get():
            #                     keys = con.xpath('./span/text()').get()
            #                     if keys not in key_list:
            #                         if keys not in re.findall(r'[0-9a-zA-Z_]{0,19}@[a-zA-Z0-9].*', keys)[0]:
            #                             files_path[keys] = value
            #                         elif value[value.rindex('.') + 1:] in key_name:
            #                             keys = value[value.rindex('/') + 1:] + '_' + str(num)
            #                             files_path[keys] = value
            #                 num += 1
            #             else:
            #                 pass
            #
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
            print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_45_shanxi_spider".split(" "))


