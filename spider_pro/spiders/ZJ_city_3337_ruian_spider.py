#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-07-12
# @Describe: 浙江温州市瑞安市人民政府 - 全量/增量脚本

import re, scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time,\
                            remove_specific_element, get_files, get_notice_type


class MySpider(CrawlSpider):
    name = 'ZJ_city_3337_ruian_spider'
    area_id = "3337"
    domain_url = "http://ggzy.ruian.gov.cn"
    query_url = "http://ggzy.ruian.gov.cn/TPFrontNew/jyxx"
    base_url = 'http://ggzy.yueqing.gov.cn/yqwebnew/ShowInfo/ShowSearchInfo.aspx?'
    allowed_domains = ['ggzy.ruian.gov.cn']
    area_province = '浙江瑞安市人民政府'

    # 招标预告
    list_tender_notice_num = ['征求意见', '需求公示']
    # 招标公告
    list_notice_category_name = ['招标公告', '招标文件公示', '采购公告', '出让公告', '交易公告']
    # 招标变更
    list_zb_abnormal_name = ["澄清公告", "变更公告", "更正补充"]
    # 中标预告
    list_win_advance_notice_name = ['中标公示']
    # 中标公告
    list_win_notice_category_name = ['中标结果', '出让结果']
    # 招标异常
    list_alteration_category_name = []
    # 资格预审
    list_qualifiction_advance_num = []
    # 其他
    list_qita_num = ['开标结果公示', '合同订立信息']

    form_data = {'__VIEWSTATE': '__VIEWSTATE', '__VIEWSTATEGENERATOR': 'BFB6D9E6',
                 '__EVENTTARGET': 'MoreInfoList1$Pager', '__EVENTARGUMENT': 1,
                 '__VIEWSTATEENCRYPTED': ''}

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
            li_list = response.xpath('//td[@height="410"]/table/tr/td')[1::2]
            for li in li_list:
                code = li.xpath('./@id').get()
                ul_list = li.xpath('./table/tr/td[2]')
                if code == 'TD002001':
                    category = '建设工程'
                elif code == 'TD002002':
                    category = '政府采购'
                elif code == 'TD002003':
                    category = '产权交易'
                elif code == 'TD002004':
                    category = '土地交易'
                elif code == 'TD002007':
                    category = '社会交易项目'
                elif code == 'TD002008':
                    category = '国企采购交易'
                else:
                    category = ''
                if category:
                    for ui in ul_list:
                        li_url = self.domain_url + ui.xpath('./a/@href').get()
                        notice_name = ''.join(ui.xpath('./a/font/text()').get()).strip()
                        if notice_name in self.list_notice_category_name:           # 招标公告
                            notice = const.TYPE_ZB_NOTICE
                        elif notice_name in self.list_tender_notice_num:            # 招标预告
                            notice = const.TYPE_ZB_ADVANCE_NOTICE
                        elif notice_name in self.list_zb_abnormal_name:             # 招标变更
                            notice = const.TYPE_ZB_ALTERATION
                        elif notice_name in self.list_win_notice_category_name:     # 中标公告
                            notice = const.TYPE_WIN_NOTICE
                        elif notice_name in self.list_win_advance_notice_name:       # 中标预告
                            notice = const.TYPE_ZB_ABNORMAL
                        elif notice_name in self.list_qita_num:                      # 其他公告
                            notice = const.TYPE_OTHERS_NOTICE
                        else:
                            notice = ''
                        if notice:
                            info_url = li_url + "/MoreInfo.aspx?CategoryNum=" + li_url[li_url.rindex('/')+1:]
                            yield scrapy.Request(url=info_url, callback=self.parse_data_info,
                                                 meta={'category': category,
                                                       'notice': notice,
                                                       'data': self.form_data}, priority=100)
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            __VIEWSTATE = response.xpath('//form[@id="ctl00"]/div[1]/input[1]/@value').get()
            __VIEWSTATEGENERATOR = response.xpath('//form[@id="ctl00"]/div[2]/input[1]/@value').get()
            if self.enable_incr:
                li_list = response.xpath('//td[@id="MoreInfoList1_tdcontent"]/table/tr')
                num = 0
                for info_num in range(len(li_list)):
                    _url = self.domain_url + li_list[info_num].xpath('./td[2]/a/@href').get()
                    title_name = li_list[info_num].xpath('./td[2]/a/text()').get()
                    pub_time = ''.join(li_list[info_num].xpath('./td[last()]/text()').get()).strip()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        yield scrapy.Request(url=_url, callback=self.parse_item,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time})
                    if num >= int(len(li_list)):
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        page = int(response.meta['data']['__EVENTARGUMENT'])
                        page += 1
                        data = self.form_data | {'__VIEWSTATE': __VIEWSTATE} | {'__EVENTARGUMENT': str(page)} | {'__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR}
                        yield scrapy.FormRequest(url=response.url, callback=self.parse_data_info, formdata=data,
                                                 meta={'category': response.meta['category'],
                                                       'notice': response.meta['notice'],
                                                       "data": data})

            else:
                total = response.xpath('//div[@id="MoreInfoList1_Pager"]/table/tr/td[1]/font[1]/b/text()').get()
                pages = response.xpath('//div[@id="MoreInfoList1_Pager"]/table/tr/td[1]/font[2]/b/text()').get()
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(1, int(pages) + 1):
                    data = self.form_data | {'__VIEWSTATE': __VIEWSTATE} | {'__EVENTARGUMENT': str(num)} | {'__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR}
                    yield scrapy.FormRequest(url=response.url, callback=self.parse_data_check, formdata=data,
                                             meta={'category': response.meta['category'],
                                                   'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败parse_data {e} {response.url=}")

    def parse_data_check(self, response):
        try:
            li_list = response.xpath('//td[@id="MoreInfoList1_tdcontent"]/table/tr')
            for info in li_list:
                _url = self.domain_url + info.xpath('./td[2]/a/@href').get()
                title_name = info.xpath('./td[2]/a/text()').get()
                pub_time = ''.join(info.xpath('./td[last()]/text()').get()).strip()
                yield scrapy.Request(url=_url, callback=self.parse_item, priority=200,
                                     meta={'category': response.meta['category'],
                                           'notice': response.meta['notice'],
                                           'title_name': title_name,
                                           'pub_time': pub_time})
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
                    content = response.xpath('//table[@id="tblInfo"]').get()
                    # 去除 title
                    _, content = remove_specific_element(content, 'td', 'id', 'tdTitle')
                    # 去除 多余的表格
                    _, content = remove_specific_element(content, 'tr', 'align', 'center')
                    # 去除 多于链接
                    _, content = remove_specific_element(content, 'blockquote', 'style', 'display: none;')
                    _, content = remove_specific_element(content, 'blockquote', 'style', 'display: none; font-size: 13px;')
                    files_text = etree.HTML(content)
                    keys_a = ['javascript:void(0)', 'close()']
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
    # cmdline.execute("scrapy crawl ZJ_city_3337_ruian_spider".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3337_ruian_spider -a sdt=2021-05-01 -a edt=2021-07-12".split(" "))


