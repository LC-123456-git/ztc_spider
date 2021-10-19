#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-18
# @Describe: 重庆市公共资源交易服务平台
import re
import math
import json
import scrapy
from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element, get_files, \
     remove_element_by_xpath

class MySpider(Spider):
    name = "province_39_chongqing_spider"
    area_id = "39"
    allowed_domains = ['cqggzy.com']
    domain_url = "https://www.cqggzy.com"
    count_url = "https://www.cqggzy.com/xxhz/"
    data_url = 'https://www.cqggzy.com/interface/rest/inteligentSearch/getFullTextData'
    base_url = 'https://ggzydl.cqggzy.com/CQTPBidder/jsgcztbmis2/pages/zbfilelingqu_hy/cQZBFileDownAttachAction.action?cmd=download&AttachGuid={}&FileCode={}&ClientGuid={}'
    area_province = "重庆市公共资源交易服务平台"

    # 招标预告
    list_advance_category_num = ['014001019', '014005008']
    # 招标公告
    list_notice_category_num = ['014003001', '014001001', '014010001', '014005001', '014011001',
                                '014008001', '014004001']

    # 招标异常
    list_alteration_category_num = ['014001021', '014008015']
    # 中标公告
    list_win_notice_category_num = ['014008003', '014001004', '014009004', '014003004', '014006004', '014005004',
                                    '014002004', '014004004', '014002001']
    # 招标变更
    list_zb_abnormal = ['014008002', '014001002', '014003002', '014005002', '014002002']
    # 中标预告
    list_win_advance_notice_num = ['014008013', '014001003']
    # 其他公告
    list_others_notice_num = ['014004011', '014011002']

    list_count_num = list_advance_category_num + list_notice_category_num + list_alteration_category_num + \
                     list_win_notice_category_num + list_zb_abnormal + list_win_advance_notice_num + list_others_notice_num

    r_dict = {'token': '', 'pn': 0, 'rn': 50, 'sdt': '', 'edt': '', 'wd': ' ', 'inc_wd': '', 'exc_wd': '',
              'fields': 'title;projectno;', 'cnum': '001',
              'sort': '{"istop":"0","ordernum":"0","webdate":"0","rowid":"0"}', 'ssort': 'title', 'cl': 200, 'terminal':
                  '', 'condition': [{'fieldName': 'categorynum', 'equal': '014002001', 'notEqual': None, 'equalList': None,
                                     'notEqualList': ['014001018', '004002005', '014001015', '014005014', '014008011'],
                                     'isLike': True, 'likeType': 2}],
              'time': [{'fieldName': 'webdate', 'startTime': '2021-07-13 00:00:00', 'endTime': '2021-10-11 23:59:59'}],
              'highlights': 'title', 'statistics': None, 'unionCondition': [], 'accuracy': '', 'noParticiple': '0',
              'searchRange': None, 'isBusiness': '1'}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for count_url in self.list_count_num:
            new_dict = self.r_dict | {'condition': [self.r_dict['condition'][0] | {'equal': count_url}]}
            yield scrapy.Request(url=self.data_url, dont_filter=True,
                                 callback=self.parse_categoy_data_urls, method='post',
                                 body=json.dumps(new_dict), meta={'new_dict': new_dict})

    def parse_categoy_data_urls(self, response):
        try:
            if json.loads(response.text)['result']['totalcount'] != 0:
                if self.enable_incr:
                    nums_count = 0
                    data_info_count = response.json()['result']['records']
                    for data_info in data_info_count:
                        put_time = data_info['pubinwebdate']
                        put_time = get_accurate_pub_time(put_time)
                        pub_time = ''.join(re.findall('(\d{4}\-\d{1,2}\-\d{1,2}).*', put_time)[0]).replace('-', '')
                        title_name = data_info['title']
                        info_id = data_info['infoid']
                        info_url_code = data_info['categorynum']
                        category = data_info['categorytype']
                        info_count = re.findall('\d{9}', json.loads(response.text)['result']['records'][0]['categorynum'])[0]
                        if len(info_url_code) > 10:
                            code_1 = info_url_code[:6]
                            code_2 = info_url_code[:9]
                            info_url = self.count_url + code_1 + '/' + code_2 + '/' + \
                                       info_url_code + '/' + pub_time + '/' + info_id + '.html'
                        else:
                            code_1 = info_url_code[:6]
                            info_url = self.count_url + code_1 + '/' + \
                                       info_url_code + '/' + pub_time + '/' + info_id + '.html'
                        x, y, z = judge_dst_time_in_interval(put_time, self.sdt_time, self.edt_time)
                        if x:
                            nums_count += 1
                            total = response.json()['result']['totalcount']  # 总条数
                            if total == None:
                                return
                            # self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                            yield scrapy.Request(url=info_url, callback=self.parse_itme,
                                                 meta={'put_time': put_time,
                                                       'title_name': title_name,
                                                       'category': category,
                                                       'info_count': info_count})
                        if nums_count >= len(data_info_count):
                            pn = response.meta['pn'] + 50
                            new_dicts = response.meta['new_dict'] | {'pn': pn} | {'time': [response.meta['new_dict']
                                        ['time'][0] | {'startTime': self.sdt_time} | {'endTime': self.edt_time}]}
                            yield scrapy.Request(url=self.data_url, dont_filter=True,
                                                 callback=self.parse_categoy_data_urls, method='post',
                                                 body=json.dumps(new_dicts), meta={'new_dict': new_dicts})

                else:
                    total = json.loads(response.text)['result']['totalcount']
                    pages = math.ceil(int(total) / 50)
                    self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    pn = 0
                    for num in range(pages):
                        if num == 0:
                            pn = pn
                        else:
                            pn += 50
                        new_dicts = response.meta['new_dict'] | {'pn': pn}
                        yield scrapy.Request(url=self.data_url, dont_filter=True,
                                             callback=self.parse_data_info, method='post',
                                             body=json.dumps(new_dicts), meta={'new_dict': new_dicts})
        except Exception as e:
            self.logger.error(f"parse_categoy_data_urls:发起数据请求失败 {e} {response.meta['new_dict']}")

    def parse_data_info(self, response):
        try:
            if response.json()['result']['records']:
                data_info_count = response.json()['result']['records']
                for data_info in data_info_count:
                    put_time = data_info['pubinwebdate']
                    put_time = get_accurate_pub_time(put_time)
                    pub_time = ''.join(re.findall('(\d{4}\-\d{1,2}\-\d{1,2}).*', put_time)[0]).replace('-', '')
                    title_name = data_info['title']
                    info_id = data_info['infoid']
                    info_url_code = data_info['categorynum']
                    category = data_info['categorytype']
                    info_count = re.findall('\d{9}', json.loads(response.text)['result']['records'][0]['categorynum'])[0]
                    if len(info_url_code) > 10:
                        code_1 = info_url_code[:6]
                        code_2 = info_url_code[:9]
                        info_url = self.count_url + code_1 + '/' + code_2 + '/' + \
                                   info_url_code + '/' + pub_time + '/' + info_id + '.html'
                    else:
                        code_1 = info_url_code[:6]
                        info_url = self.count_url + code_1 + '/' + \
                                   info_url_code + '/' + pub_time + '/' + info_id + '.html'
                    yield scrapy.Request(url=info_url, callback=self.parse_itme,
                                         meta={'put_time': put_time,
                                               'title_name': title_name,
                                               'category': category,
                                               'info_count': info_count})
        except Exception as e:
            self.logger.error(f"parse_data_info:发起数据请求失败 {e} {response.url=}")

    def parse_itme(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            origin = response.url
            info_source = self.area_province
            pub_time = response.meta["put_time"]

            title_name = response.meta['title_name']
            category = response.meta['category']
            info_count = response.meta['info_count']
            if info_count in self.list_advance_category_num:  # 招标预告
                notice = const.TYPE_ZB_ADVANCE_NOTICE
            elif info_count in self.list_notice_category_num:  # 招标公告
                notice = const.TYPE_ZB_NOTICE
            elif info_count in self.list_alteration_category_num:  # 招标异常
                notice = const.TYPE_ZB_ABNORMAL
            elif info_count in self.list_win_notice_category_num:  # 中标公告
                notice = const.TYPE_WIN_NOTICE
            elif info_count in self.list_zb_abnormal:  # 招标变更
                notice = const.TYPE_ZB_ALTERATION
            elif info_count in self.list_win_advance_notice_num:  # 中标预告
                notice = const.TYPE_WIN_ADVANCE_NOTICE
            elif info_count in self.list_others_notice_num:  # 其他公告
                notice = const.TYPE_OTHERS_NOTICE
            else:
                notice = ''
            if notice:
                content = response.xpath('//div[@class="detail-block"]').get()
                # 去除 title
                _, content = remove_specific_element(content, 'div', 'class', 'title')
                _, content = remove_specific_element(content, 'div', 'class', 'tabview-title')
                _, content = remove_specific_element(content, 'div', 'class', 'result-title')
                # 去除 info信息 来源等信息
                _, content = remove_specific_element(content, 'div', 'class', 'info-source')

                _, content = remove_specific_element(content, 'div', 'id', 'xiangqing')
                _, content = remove_specific_element(content, 'div', 'class', 'ewb-acce')
                _, content = remove_specific_element(content, 'iframe', 'id', 'wytw')
                _, content = remove_specific_element(content, 'div', 'id', 'normal')
                _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="mainContent"]/div/a[contains(string(), "请到原网址下载附件")]')

                _, content = remove_element_by_xpath(content, xpath_rule='//div[@id="mainContent"]/div/h4[contains(string(), "附件")]')

                _, content = remove_specific_element(content, 'div', 'list-name', '附件列表')

                patterns = re.compile(r'<a target="_blank" .*?>(.*?)</div>', re.S)
                content = content.replace(''.join(re.findall(patterns, content)), '')

                keys_a = []
                files_text = etree.HTML(content)
                files_path = get_files(self.domain_url, origin, files_text, pub_time=pub_time,
                                       start_urls=self.domain_url, keys_a=keys_a, base_url=self.base_url)
                num = 1
                if files_path:
                    for itme_key in files_path.values():
                        if files_text.xpath('//a/@onclick'):
                            content = ''.join(content).replace('<a class="ewb-blue-a" onclick="{}">'.format(files_text.xpath('//a[{}]/@onclick'.format(num))[0]),
                                                           '<a class="ewb-blue-a" href="{}">'.format(itme_key))
                        else:
                            content = content
                        num += 1

                notice_item = NoticesItem()
                notice_item["origin"] = origin
                notice_item["title_name"] = title_name
                notice_item["pub_time"] = pub_time
                notice_item["info_source"] = info_source
                notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                notice_item["files_path"] = "" if not files_path else files_path
                notice_item["content"] = content
                notice_item["area_id"] = self.area_id
                notice_item["notice_type"] = notice
                notice_item["category"] = category

                yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_39_chongqing_spider".split(" "))
    cmdline.execute("scrapy crawl province_39_chongqing_spider -a sdt=2021-05-01 -a edt=2021-10-22".split(" "))
