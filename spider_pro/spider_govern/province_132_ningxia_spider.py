#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-08-31
# @Describe: 宁夏回族自治区政府采购网
import json, copy
import scrapy, re, math, requests
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, \
     get_files, get_notice_type, remove_specific_element, get_timestamp


class Province132NingXinSpider(CrawlSpider):
    name = 'province_132_ningxia_spider'
    allowed_domains = ['ccgp-ningxia.gov.cn']
    start_urls = 'http://www.ccgp-ningxia.gov.cn'
    domain_url = 'http://www.ccgp-ningxia.gov.cn/public/NXGPPNEW/dynamic/contents/CGGG/index.jsp?cid=312&sid=1'
    base_url = 'http://www.ccgp-ningxia.gov.cn//site/InteractionQuestion_findVNoticeNew.do'
    query_url = 'http://www.ccgp-ningxia.gov.cn/public/NXGPPNEW/dynamic/'
    area_id = "132"
    area_province = '宁夏回族自治区政府采购网'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'spider_pro.middlewares.VerificationMiddleware.VerificationMiddleware': 120,
        }
    }

    # 招标预告
    list_tender_notice_name = ['采购意向']
    # 招标公告
    list_notice_category_name = ['竞价公告', '公开招标', '邀请招标', '询价', '竞争性谈判', '竞争性磋商', '单一来源']
    # 招标变更
    list_zb_abnormal_name = ["更正公告"]
    # 中标预告
    list_win_advance_notice_name = []
    # 中标公告
    list_win_notice_category_name = ['中标公告']
    # 招标异常
    list_alteration_category_name = ['失败公告']
    # 资格预审
    list_qualifiction_advance_num = ['资格预审']
    # 其他
    list_qita_num = ['合同公告']

    r_dict = {'type': 'bid',
              'page': '0',
              'tab': 'QBJ',
              'authCode': '',
              'noticeTab': 'CGYX',
              'keyword_all': '',
              'departmentName_all': '',
              'date1_all': '',
              'date2_all': '',
              'regionId_all': '640000',
              'keyword_each': '',
              'departmentName_each': '',
              'agentName_each': '',
              'projectNumber_each': '',
              'planNumber_each': '',
              'date1_each': '',
              'date2_each': '',
              'regionId_each': '640000',
              'title_cgyx': '',
              'departmentName_cgyx': '',
              'date1_cgyx': '',
              'date2_cgyx': '',
              'regionId_notice_0': '640000',
              'projectName_cgyxxm': '',
              'departmentName_cgyxxm': '',
              'yjcgsj_cgyxxm': '',
              'date1_cgyxxm': '',
              'date2_cgyxxm': '',
              'purchaseItem_cgyxxm': '',
              'agreCode_htgs': '',
              'departmentName_htgs': '',
              'supplierName_htgs': '',
              'date1_htgs': '',
              'date2_htgs': '',
              'agreCode_ysjggg': '',
              'reportCode_ysjggg': '',
              'departmentName_ysjggg': '',
              'supplierName_ysjggg': '',
              'date1_ysjggg': '',
              'date2_ysjggg': ''}

    def get_category(self, notice_name):
        if notice_name in self.list_notice_category_name:  # 招标公告
            notice = const.TYPE_ZB_NOTICE
        elif notice_name in self.list_zb_abnormal_name:  # 招标变更
            notice = const.TYPE_ZB_ALTERATION
        elif notice_name in self.list_win_advance_notice_name:  # 中标预告
            notice = const.TYPE_WIN_ADVANCE_NOTICE
        elif notice_name in self.list_win_notice_category_name:  # 中标公告
            notice = const.TYPE_WIN_NOTICE
        elif notice_name in self.list_tender_notice_name:  # 招标预告
            notice = const.TYPE_ZB_ADVANCE_NOTICE
        elif notice_name in self.list_alteration_category_name:  # 招标异常
            notice = const.TYPE_ZB_ABNORMAL
        elif notice_name in self.list_qualifiction_advance_num:  # 资格预审
            notice = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice_name in self.list_qita_num:  # 其他
            notice = const.TYPE_OTHERS_NOTICE
        else:
            notice = ''
        return notice

    def __init__(self, *args, **kwargs):
        super(Province132NingXinSpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        yield scrapy.Request(url=self.domain_url, callback=self.parse_urls,
                             meta={'r_dict': self.r_dict})

    def parse_urls(self, resp):
        try:
            li_list = resp.xpath('//div[@class="cg-menu"]/ul/li')[1:-1]
            count = 0
            for li in li_list:
                count += 1
                code = li.xpath('./@name').get()
                category_name = li.xpath('./a/text()').get()
                notice = self.get_category(category_name)
                new_dict = self.r_dict | {'type': code}
                yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_info,
                                         priority=(len(li_list)-count)*10,
                                         formdata=new_dict,
                                         meta={'notice': notice, 'new_dict': copy.deepcopy(new_dict),
                                               'category_name': category_name})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_urls {e}')

    def parse_data_info(self, response):
        try:
            if response.text:
                data_info = json.loads(response.text)
                if self.enable_incr:
                    count = 0
                    num = 0
                    for info_key, info_url_value in data_info.items():
                        for key in json.loads(info_key):
                            count += 1
                            try:
                                pub_time = key['publish_time']
                            except:
                                pub_time = key['publishTime']
                            info_url = self.query_url + key['url']
                            title_name = key['title']
                            pub_time = get_accurate_pub_time(pub_time)
                            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                            if x:
                                num += 1
                                yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                                     priority=(len(data_info) - count) * 100,
                                                     meta={'notice': response.meta['notice'],
                                                           'title_name': title_name,
                                                           'category_name': response.meta['category_name'],
                                                           'pub_time': pub_time})
                            if num >= int(len(json.loads(info_key))):
                                total = int(len(json.loads(info_key)))
                                if total == None:
                                    return
                                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                                page = int(response.meta['new_dict']['page']) + 1
                                new_dict = response.meta['new_dict'] | {"page": str(page)}
                                yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_info,
                                                         formdata=new_dict, dont_filter=True,
                                                         meta={'notice': response.meta['notice'],
                                                               'new_dict': copy.deepcopy(new_dict),
                                                               'category_name': response.meta['category_name']})
                else:
                    for dict_key, dict_value in data_info.items():
                        files_text = etree.HTML(dict_value)
                        total = re.findall('.*?共(\d+)条数据', files_text.xpath('//table/tr/td[1]/div/text()')[0])[0]
                        pages = int(re.findall('.*?共(\d+)页', files_text.xpath('//table/tr/td[2]/div/text()')[0])[0])
                        self.logger.info(f"初始总数提取成功 {total=} {response.meta.get('proxy')}")
                        count = 0
                        for page in range(pages):
                            count += 1
                            new_dicts = response.meta['new_dict'] | {'page': str(page)}
                            yield scrapy.FormRequest(url=self.base_url, callback=self.parse_data_check, dont_filter=True,
                                                     formdata=new_dicts, priority=((pages + 1) - count) * 100,
                                                     meta={'notice': response.meta['notice'],
                                                           'new_dict': copy.deepcopy(new_dicts)})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_info {response.url} {e}')

    def parse_data_check(self, response):
        try:
            if response.text:
                count = 0
                data_info = json.loads(response.text)
                for info_key, info_url_value in data_info.items():
                    for key in json.loads(info_key):
                        count += 1
                        pub_time = key.get('createTime', '') or key.get('publishTime', '') or key.get('publish_time', '')
                        info_url = self.query_url + key['url']
                        title_name = key['title']
                        yield scrapy.Request(url=info_url, callback=self.parse_item, dont_filter=True,
                                             priority=(len(data_info) - count) * 100,
                                             meta={'notice': response.meta['notice'],
                                                   'title_name': title_name,
                                                   'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f'发起数据请求失败parse_data_check {response.url} {e}')

    def parse_item(self, response):
        content = response.xpath('//div[@class="newAgreShow"]').get() or\
                  response.xpath('//div[@id="createForm"]').get() or \
                  response.xpath('//div[@class="vT_z w100"]').get()
        category = '政府采购'
        origin = response.url
        info_source = self.area_province
        title_name = ''.join(response.meta['title_name'])
        pub_time = response.meta['pub_time']
        pub_time = get_accurate_pub_time(pub_time)
        if '测试' not in title_name:
            notice_type = get_notice_type(title_name, response.meta['notice'])
            if notice_type and content:
                # 去除title
                _, content = remove_specific_element(content, 'h1')
                _, content = remove_specific_element(content, 'h3')
                _, content = remove_specific_element(content, 'h2')
                _, content = remove_specific_element(content, 'p', 'class', 'tc')
                _, content = remove_specific_element(content, 'span', 'class', 'blank20')
                _, content = remove_specific_element(content, 'div', 'class', 'vF_detail_content')

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


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_132_ningxia_spider".split(" "))
    cmdline.execute("scrapy crawl province_132_ningxia_spider -a sdt=2021-08-20 -a edt=2021-09-06".split(" "))
