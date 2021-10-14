#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-30
# @Describe: 江苏省政府采购网
import json

import scrapy, re, math, time
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
     get_files, get_notice_type, remove_specific_element, get_timestamp


class Province136JiangSuSpider(CrawlSpider):
    name = 'province_136_jiangsu_spider'
    allowed_domains = ['ccgp-jiangsu.gov.cn']
    start_urls = 'http://www.ccgp-jiangsu.gov.cn'
    domain_url = 'http://www.ccgp-jiangsu.gov.cn/jiangsu/cggg_search.html?_t=1626312309291'
    base_url = 'http://www.ccgp-jiangsu.gov.cn/pss/jsp/relevantCgggGetById.jsp'
    query_url = 'http://www.ccgp-jiangsu.gov.cn/pss/jsp/search_cggg.jsp?cgr=&xmbh=&pqy=&sd={}&ed={}&dljg=&cglx={}&bt=&nr=&cgfs=&page=1'
    _info_url = 'http://www.ccgp-jiangsu.gov.cn/jiangsu/js_cggg/details.html?gglb={}&ggid={}'
    area_id = "136"
    area_province = '江苏省政府采购网'

    # 招标预告
    list_tender_notice_name = ['采购意向']
    # 招标公告
    list_notice_category_name = ['单一来源公示', '采购公告']
    # 招标变更
    list_zb_abnormal_name = ["更正公告"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标公告', '成交公告']
    # 招标异常
    list_alteration_category_name = ['终止公告']
    # 资格预审
    list_qualifiction_advance_num = ['资格预审']
    # 其他
    list_qita_num = ['合同公告', '其它公告']

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

    def __init__(self, *args, **kwargs):
        super(Province136JiangSuSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_data)

    def parse_data(self, response):
        try:
            if self.enable_incr:
                sdt_time = round(time.mktime(time.strptime(self.sdt_time, '%Y-%m-%d'))*1000)
                edt_time = round(time.mktime(time.strptime(self.edt_time, '%Y-%m-%d'))*1000)
            else:
                sdt_time = '0'
                edt_time = '0'
            li_list = response.xpath('//div[@class="notice_container"]//ul[@id="cgtype"]/li')[1:]
            for li in li_list:
                notice_name = li.xpath('./a/text()').get()
                notice = self.get_category(notice_name)
                data_url = self.query_url.format(sdt_time, edt_time, li.xpath('./a/@data').get())
                yield scrapy.Request(url=data_url, callback=self.parse_data_info,
                                     meta={'notice': notice})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data {e}')

    def parse_data_info(self, response):
        try:
            if json.loads(response.text):
                info_data = json.loads(response.text)['result']
                total = info_data['count']
                self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                pages = info_data['totalPage']
                for page in range(1, int(pages) + 1):
                    sub_gage = re.findall('.*page=(\d+)', response.url)[0]
                    info_url = re.sub('page={}'.format(sub_gage), 'page={}'.format(page), response.url)
                    yield scrapy.Request(url=info_url, callback=self.parse_data_check,
                                         meta={'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {e}')

    def parse_data_check(self, response):
        try:
            if response.text:
                count = 0
                data_info = json.loads(response.text)['result']
                for info in data_info['list']:
                    count += 1
                    pub_time = info['publishDate']
                    title_name = info['title']
                    data_dict = {'ggid': info['id']}
                    info_url = self._info_url.format(info['ggCode'], info['id'])
                    yield scrapy.FormRequest(url=self.base_url, callback=self.parse_item,
                                             formdata=data_dict, dont_filter=True,
                                             priority=(len(data_info) - count) * 100,
                                             meta={'notice': response.meta['notice'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time,
                                                   'info_url': info_url})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {e}')

    def parse_item(self, response):
        try:
            category = '政府采购'
            origin = response.meta['info_url']
            info_source = self.area_province
            title_name = ''.join(response.meta['title_name'])
            pub_time = response.meta['pub_time']
            pub_time = get_accurate_pub_time(pub_time)
            content = json.loads(response.text)['data']['content']
            files_path = {}
            if '测试' not in title_name:
                notice_type = get_notice_type(title_name, response.meta['notice'])
                if notice_type and content:
                    try:
                        files_list = json.loads(response.text)['data']['files']
                        count = '0'
                        for files in files_list:
                            try:
                                ff = files['name'][files['name'].rindex('.'):]
                                files_path[count + '_' + files['name']] = files['url']
                            except:
                                suffix = files['url'][files['url'].rindex('.'):]
                                files_path[count + '_' + files['name'] + suffix] = files['url']
                    except:
                        files_path = ''

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
            self.logger.error(f'发起数据请求失败parse_data_check {e}, {response.meta["info_url"]}')



if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_136_jiangsu_spider".split(" "))
    cmdline.execute("scrapy crawl province_136_jiangsu_spider -a sdt=2021-10-01 -a edt=2021-10-14".split(" "))
