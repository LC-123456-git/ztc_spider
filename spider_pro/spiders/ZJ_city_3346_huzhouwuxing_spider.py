# @file           :ZJ_city_3346_huzhouwuxing_spider.py
# @description    :
# @date           :2021/07/27 08:53:08
# @author         :miaokela
# @version        :1.0
import re
import json
from ast import literal_eval
import requests
from lxml import etree
import random
from datetime import datetime

import scrapy

from spider_pro import utils, constans, items


class ZjCity3346HuzhouwuxingSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3346_huzhouwuxing_spider'
    allowed_domains = ['www.wuxing.gov.cn']
    start_urls = ['http://www.wuxing.gov.cn/']
    query_url = 'http://www.wuxing.gov.cn'

    basic_area = '浙江省湖州吴兴市人民政府'
    area_id = 3346
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '政府采购', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/zfcg/yjzx/index.html'},  # 意见征询
        ],
        '招标公告': [
            {'category': '房建市政', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/fjsz/zbgg/index.html'},  # 招标公告
            {'category': '交通工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/jtgc/zbgg/index.html'},  # 招标公告
            {'category': '水利工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/slgc/zbgg/index.html'},  # 招标公告
            {'category': '政府采购', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/zfcg/zbgg/index.html'},  # 招标公告
            {'category': '其他交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/qtjy/zbgg/index.html'},  # 招标公告
            {'category': '房产交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/gyzcjy/fcjy/jygg/index.html'},
            # 交易公告
            {'category': '其他交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/gyzcjy/qtjy/jygg/index.html'},
            # 交易公告
            {'category': '土地承包经营权流转',
             'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/nczhcq/tdcbjyqlz/jygg/index.html'},  # 交易公告
            {'category': '农村房屋使用权',
             'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/nczhcq/ncfwsyq/jygg/index.html'},  # 交易公告
        ],
        '招标变更': [
            {'category': '房建市政', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/fjsz/bggg/index.html'},  # 变更公告
            {'category': '交通工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/jtgc/bggg/index.html'},  # 变更公告
            {'category': '水利工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/slgc/bggg/index.html'},  # 变更公告
            {'category': '政府采购', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/zfcg/gzgg/index.html'},  # 更正公告
            {'category': '其他交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/qtjy/bggg/index.html'},  # 变更公告
        ],
        '中标预告': [
            {'category': '房建市政', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/fjsz/pbjggs/index.html'},
            # 评标结果公示
            {'category': '交通工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/jtgc/pbjggs/index.html'},
            # 评标结果公示
            {'category': '水利工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/slgc/pbjggs/index.html'},
            # 评标结果公示
            {'category': '其他交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/qtjy/psjggs/index.html'},
            # 评标结果公示
        ],
        '中标公告': [
            {'category': '房建市政', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/fjsz/zbjggg/index.html'},
            # 中标结果公告
            {'category': '交通工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/jtgc/zbjggg/index.html'},
            # 中标结果公告
            {'category': '水利工程', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/slgc/zbjggg/index.html'},
            # 中标结果公告
            {'category': '其他交易', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/qtjy/zbjggs/index.html'},
            # 中标结果公告
            {'category': '土地承包经营权流转',
             'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/nczhcq/tdcbjyqlz/jygs/index.html'},  # 交易公示
            {'category': '农村房屋使用权',
             'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/nczhcq/ncfwsyq/jygs/index.html'},  # 交易公示
            {'category': '政府采购', 'url': 'http://www.wuxing.gov.cn/hzgov/front/s127/jyxx/zfcg/jggg/index.html'},  # 结果公告

        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

        if self.start_time:
            self.start_time = datetime.strptime(self.start_time, '%Y-%m-%d')
        if self.end_time:
            self.end_time = datetime.strptime(self.end_time, '%Y-%m-%d')

    def match_title(self, title_name):
        """
        根据标题匹配关键字 返回招标类别
        Args:
            title_name: 标题

        Returns:
            notice_type: 招标类别
        """
        matched = False
        notice_type = ''
        for keywords, value in self.keywords_map.items():
            if re.search(keywords, title_name):
                notice_type = value
                matched = True
                break
        return matched, notice_type

    def start_requests(self):
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                c_url = cu['url']
                yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                })

    def get_links(self, link_data_list):
        """
        - 获取时间区间内所有详情页链接
        """
        link_infos = []
        if all([self.start_time, self.end_time]):
            is_break = False
            for ldl in link_data_list:
                info_list = ldl.get('infolist')
                for il in info_list:
                    day_time_raw = il.get('daytime')
                    day_time = datetime.strptime(day_time_raw, '%Y-%m-%d')
                    # - 根据时间区间过滤
                    if day_time < self.start_time:  # 发布时间比搜索起始时间早
                        is_break = True
                        break
                    if day_time > self.end_time:  # 发布时间比搜索终止时间晚
                        continue

                    url = il.get('url', '')
                    if url:
                        link_infos.append({
                            'link': url,
                            'pub_time': day_time_raw,
                        })
                if is_break:
                    break
        else:
            for ldl in link_data_list:
                info_list = ldl.get('infolist')
                for il in info_list:
                    day_time_raw = il.get('daytime')
                    url = il.get('url', '')
                    if url:
                        link_infos.append({
                            'link': url,
                            'pub_time': day_time_raw,
                        })
        return link_infos

    def parse_list(self, resp):
        # - 处理页面中Script数据,通过时间来获取数据
        #   + 匹配 //script[not(@*)] 没有任何元素的script节点 ———— 存放了当前列表页所有链接
        link_script = resp.xpath('//script[not(@*)]/text()').get().replace('\t', '')

        c_com = re.compile(r'dataList\s*=\s*(.*?);var pagesData')

        link_data = c_com.findall(link_script)

        if link_data:
            link_data_list = json.loads(link_data[0])

            # 获取某个时间段的详情页链接
            link_infos = self.get_links(link_data_list)

            for link_info in link_infos:
                yield scrapy.Request(url=link_info['link'], callback=self.parse_detail, meta={
                    'notice_type': resp.meta.get('notice_type', ''),
                    'category': resp.meta.get('category', ''),
                    'pub_time': link_info['pub_time'],
                })

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="zw"]').get()
        title_name = resp.xpath('//div[@class="title"]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        _, content = utils.remove_specific_element(content, 'form', 'name', 'form1')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name.strip() if title_name else ''
        notice_item["pub_time"] = resp.meta.get('pub_time')

        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = resp.meta.get('category')
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl ZJ_city_3346_huzhouwuxing_spider -a sdt=2021-06-01 -a edt=2021-07-27".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3346_huzhouwuxing_spider".split(" "))
