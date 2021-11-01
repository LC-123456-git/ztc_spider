#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-10-25
# @Describe: 冀招标全流程电子交易平台
import ast
import re

import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_notice_type, remove_specific_element, remove_element_by_xpath, get_time


class Province150JiZhaoBiaoSpider(CrawlSpider):
    name = 'province_150_jizhaobiao_spider'
    allowed_domains = ['jizhaobiao.com']
    start_urls = 'http://www.jizhaobiao.com'
    domain_url = 'http://www.jizhaobiao.com/HB/TradeCenter/colTableInfo.do'
    base_url = 'http://www.jizhaobiao.com:9069/jrupload6/downloadFile.html?file={}&fileType='
    query_url = ''
    area_id = "150"
    area_province = '冀招标全流程电子交易平台'

    # 招标预告
    list_tender_notice_name = []
    # 招标公告
    list_notice_category_name = ['招标公告']
    # 招标变更
    list_zb_abnormal_name = ["变更、澄清答疑公告"]
    # 中标预告
    list_win_advance_notice_name = ['中标候选人公示']
    # 中标公告
    list_win_notice_category_name = ['中标结果公告']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = ['资格预审公告']
    # 其他
    list_qita_num = []

    const_dict = {'资格预审公告': '2 ', '招标公告': '1 ', '中标候选人公示': 'PUBLICITY',
                  '中标结果公告': 'RESULT_NOTICE', '变更、澄清答疑公告': 'WEB_JY_NOTICE'}

    r_dict = {'projectName': '', 'date': '', 'begin_time': '', 'end_time': '',
              'date2': '', 'projectType': '', 'dealType': '', 'noticType': '',
              'area': '', 'dataSource': '', 'huanJie': 'NOTICE', 'pageIndex': '1'}

    custom_settings = {'DOWNLOAD_DELAY': {
                            # 'spider_pro.middlewares.DelayedRequestMiddleware.DelayedRequestMiddleware': 50,
                            'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
                            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
                            # 'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 750,

                            # Splash
                            'scrapy_splash.SplashCookiesMiddleware': 770,
                            'scrapy_splash.SplashMiddleware': 780,
                            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
                    }
                        }

    def get_category(self, notice_name):
        if notice_name in self.list_notice_category_name:         # 招标公告
            notice = const.TYPE_ZB_NOTICE
        elif notice_name in self.list_zb_abnormal_name:           # 招标变更
            notice = const.TYPE_ZB_ALTERATION
        elif notice_name in self.list_win_advance_notice_name:    # 中标预告
            notice = const.TYPE_WIN_ADVANCE_NOTICE
        elif notice_name in self.list_win_notice_category_name:   # 中标公告
            notice = const.TYPE_WIN_NOTICE
        elif notice_name in self.list_tender_notice_name:         # 招标预告
            notice = const.TYPE_ZB_ADVANCE_NOTICE
        elif notice_name in self.list_alteration_category_name:   # 招标异常
            notice = const.TYPE_ZB_ABNORMAL
        elif notice_name in self.list_qualifiction_advance_num:   # 资格预审
            notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice_name in self.list_qita_num:                   # 其他
            notice = const.TYPE_OTHERS_NOTICE
        else:
            notice = ''
        return notice

    def _monkey_patching_HTTPClientParser_statusReceived(self):
        from twisted.web._newclient import HTTPClientParser, ParseError
        old_sr = HTTPClientParser.statusReceived

        def statusReceived(self, status):
            try:
                return old_sr(self, status)
            except ParseError as e:
                if e.args[0] == 'wrong number of parts':
                    return old_sr(self, status + ' OK')
                raise

        statusReceived.__doc__ = old_sr.__doc__
        HTTPClientParser.statusReceived = statusReceived


    def __init__(self, *args, **kwargs):
        super(Province150JiZhaoBiaoSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        # self._monkey_patching_HTTPClientParser_statusReceived()
        yield scrapy.Request(url=self.start_urls, callback=self.parse_data)

    def parse_data(self, response):
        if self.enable_incr:
            begin_time = self.sdt_time
            end_time = self.edt_time
        else:
            begin_time = ''
            end_time = ''
        src_html = re.findall('(<!DOCTYPE html>(?:.|\n)*?</html>)', response.text)[0]
        html = etree.HTML(src_html)
        info_list = html.xpath('//div[@class="transaction"]/ul/li')[1:]
        for info in info_list:
            notice_name = info.xpath('./text()').get()
            noticType = self.const_dict[notice_name]
            notice_type = self.get_category(notice_name)
            new_dict = self.r_dict | {'noticType': noticType} | {'begin_time': begin_time, 'end_time': end_time}
            yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_info,
                                     formdata=new_dict, dont_filter=True,
                                     meta={'new_dict': new_dict,
                                           'notice_type': notice_type})

    def parse_data_info(self, response):
        try:
            pages = int(response.xpath('//input[@id="Page_TotalPage"]/@value').get())
            total = response.xpath('//input[@id="Page_TotalRecords"]/@value').get()
            self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
            count = 0
            for page in range(1, pages + 1):
                count += 1
                new_dicts = response.meta['new_dict'] | {'pageIndex': str(page)}
                yield scrapy.FormRequest(url=self.domain_url, callback=self.parse_data_check, formdata=new_dicts,
                                         priority=((pages + 1) - count) * 50, dont_filter=True,
                                         meta={'new_dicts': new_dicts,
                                               'notice_type': response.meta['notice_type']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')

    def parse_data_check(self, response):
        try:
            info_data = response.xpath('//dl/dt')
            count = 0
            for info in info_data:
                count += 1
                title_name = info.xpath("./a/text()").get().strip()
                pub_time = info.xpath('./span/text()').get()
                info_url = self.start_urls + info.xpath('./a/@href').get()
                yield scrapy.Request(url=info_url, callback=self.parse_item,
                                     priority=(len(info_data) - count) * 100, dont_filter=True,
                                     meta={'notice_type': response.meta['notice_type'],
                                           'title_name': title_name,
                                           'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            category = ''
            origin = response.url
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            files_path = {}
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice_type'])
                if response.xpath('//div[@class="cui-Bidfold"]'):
                    content = response.xpath('//div[@class="cui-Bidfold"]').get()
                    _, content = remove_specific_element(content, 'div', 'class', 'bnt-title')
                    _, content = remove_specific_element(content, 'div', 'class', 'cui-tbzys clearfix')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@class="notice_content"]//a[contains(string(), "打印")]')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@class="notice_content"]/p/span[contains(string(), "本次招标公告同时")]')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="filetable"]/table/tbody/tr[2]/td[3]/p/a[contains(string(), "（下载并安装工具箱7.0.0.0）")]')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="filetable"]/table/tbody/tr[3]/td[last()]/a[contains(string(), "我要参与")]')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="filetable"]/table/tbody/tr[3]/td[last()]/a[contains(string(), "申请保函")]')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="filetable"]/table/tbody/tr[3]/td[2]/div/a[contains(string(), "复制")]')
                    files_text = etree.HTML(content)
                    if files_text.xpath('//div[@id="filetable"]/table/tbody/tr[last()]/td/div/a'):
                        files_list = files_text.xpath('//div[@id="filetable"]/table/tbody/tr[last()]/td/div')[2:]
                        for cont, cont_value in enumerate(files_list):
                            value = cont_value.xpath('./a/text()')[0]
                            str_key = ast.literal_eval(cont_value.xpath('./a/@onclick')[0].replace('getFileDownStatus', '').replace('this,', '').replace('0,', ''))
                            for a_xpath in cont_value.xpath('./a'):
                                cont_value.remove(a_xpath)
                            key = self.base_url.format(str_key[0])
                            try:
                                suffix = value[value.rindex('.') + 1:]
                                values = str(cont) + '_' + value
                            except:
                                values = str(cont) + '_' + value + str_key[4]

                            sub_el = etree.SubElement(cont_value, 'a')
                            sub_el.attrib['href'] = key
                            sub_el.text = values

                            content = etree.tounicode(files_text, method='html')
                            content = content.replace(r'<html>', '').replace(r'<body>', '').replace(r'</body>', '').replace(
                                r'</html>', '')
                            files_path[values] = key
                        if get_time(pub_time):
                            files_path = files_path
                        else:
                            files_path = {'key': '不在文件处理时效内'}
                else:
                    content = response.xpath('//div[@class="table_project_container"]/div/div[@class="notice_content"]').get()
                    _, content = remove_specific_element(content, 'div', 'class', 'bnt-title')
                    _, content = remove_element_by_xpath(content, xpath_rule='//div[@class="notice_content"]//a[contains(string(), "打印")]')

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
            self.logger.error(f'发起数据请求失败parse_item {e}, {response.url}')


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_150_jizhaobiao_spider".split(" "))
    cmdline.execute("scrapy crawl province_150_jizhaobiao_spider -a sdt=2021-10-01 -a edt=2021-10-25".split(" "))
