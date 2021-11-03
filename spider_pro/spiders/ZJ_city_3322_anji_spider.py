"""
@file          :ZJ_city_3322_anji_spider.py
@description   :安吉
@date          :2021/05/11 14:58:10
@author        :miaokela
@version       :1.0
"""
import re
import requests
from lxml import etree
from datetime import datetime
from math import ceil

import scrapy

from spider_pro import utils, constans, items


class ZjCity3322AnjiSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3322_anji_spider'
    allowed_domains = ['ggzy.anji.gov.cn']
    start_urls = ['http://ggzy.anji.gov.cn/']
    query_url = 'http://ggzy.anji.gov.cn'
    basic_area = '浙江省-湖州市-安吉县-安吉公共资源交易中心'
    area_id = 3322
    keywords_map = {
        '变更|答疑|澄清|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|预成交|中标公示|结果公示': '中标预告',
        '中标结果|成交|出让结果|交易结果': '中标公告',
    }
    url_map = {
        '招标预告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001007/'},
        ],
        '招标公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001001/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011001/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005001/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007001/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008001/'},
            {'category': '其他项目', 'url': 'http://ggzy.anji.gov.cn/jyxx/003012/003012001/'},
        ],
        '招标变更': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001002/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005003/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007002/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008003/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005002/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011002/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008002/'},
        ],
        '招标异常': [],
        '中标预告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001005/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007004/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011003/'},
        ],
        '中标公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001006/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005004/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007005/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008004/'},
            {'category': '其他项目', 'url': 'http://ggzy.anji.gov.cn/jyxx/003012/003012002/'},
        ],
        '其他公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001008/'},
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001004/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007003/'},
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

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
                c_url = ''.join([cu['url'], 'moreinfo.html'])
                yield scrapy.Request(url=c_url, callback=self.parse_urls, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                }, cb_kwargs={
                    'url': cu['url'],
                })

    def parse_urls(self, resp, url):
        """
        js通过正则匹配最大页数
        """
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)
        max_page_com = re.compile(r'<script>.*?\$\("#page"\).pagination.*?pageSize:\s*(.*?),.*?total:\s*(.*?),')

        match_pages = max_page_com.findall(resp.text.replace('\t', '').replace('\n', '').replace('\r\n', ''))
        if match_pages:
            match_page = match_pages[0]

            page_size, total = match_page
            page_size = int(page_size)
            total = int(total)

            max_page = ceil(total / page_size)  # 最大页数

            c_url = ''.join([url, 'moreinfo.html'])
            if all([self.start_time, self.end_time]):
                for i in range(1, max_page + 1):
                    # 最末一条符合时间区间则翻页
                    # 解析详情页时再次根据区间判断去采集
                    judge_status = utils.judge_in_interval(
                        c_url, start_time=self.start_time, end_time=self.end_time, method='GET',
                        proxies=proxies, headers=headers, rule='//ul[contains(@class, "notice-items")]/li//span/text()',
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        if i > 1:
                            c_url = ''.join([url, '{0}.html'.format(i)])
                        else:
                            c_url = ''.join([url, 'moreinfo.html'])
                        yield scrapy.Request(
                            url=c_url, callback=self.parse_data_urls, meta={
                                'notice_type': resp.meta.get('notice_type', ''),
                                'category': resp.meta.get('category', '')
                            }, priority=(max_page - i) * 10, dont_filter=True
                        )
            else:
                for i in range(1, max_page + 1):
                    if i > 1:
                        c_url = ''.join([url, '{0}.html'.format(i)])
                    else:
                        c_url = ''.join([url, 'moreinfo.html'])
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_data_urls, meta={
                            'notice_type': resp.meta.get('notice_type', ''),
                            'category': resp.meta.get('category', '')
                        }, priority=(max_page - i) * 10, dont_filter=True
                    )
        else:
            c_url = ''.join([url, 'moreinfo.html'])
            yield scrapy.Request(url=c_url, callback=self.parse_data_urls, meta={
                'notice_type': resp.meta.get('notice_type', ''),
                'category': resp.meta.get('category', '')
            })

    def parse_data_urls(self, resp):
        """
        获取detail_url, pub_time
        """
        els = resp.xpath('//ul[@class="ewb-notice-items"]/li')
        for n, el in enumerate(els):
            href = el.xpath(".//a/@href").get()
            if href:
                pub_time = el.xpath(".//span[last()]/text()").get()
                pub_time = pub_time.replace('.', '-') if pub_time else ''
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(url=self.query_url + href, callback=self.parse_item, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'category': resp.meta.get('category'),
                        'pub_time': pub_time,
                    }, priority=(len(els) - n) * 10 ** 6)

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="ewb-container"]').get()
        title_name = resp.xpath('//div[@class="detail-tt"]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        if '测试' not in title_name:
            # 移除不必要信息: 删除第一个正文title/发布时间、打印关闭
            _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-tt')
            _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-info')
            _, content = utils.remove_specific_element(content, 'div', 'class', 'ewb-route')
            _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-tt')

            # 删除表单
            _, content = utils.remove_specific_element(content, 'div', 'class', 'clearfix hidden', index=0)
            _, content = utils.remove_specific_element(content, 'input', 'id', 'souceinfoid')

            content = utils.avoid_escape(content)  # 防止转义
            # 关键字重新匹配 notice_type
            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )
            pub_time = resp.meta.get('pub_time')

            # 匹配文件
            _, files_path = utils.catch_files(content, self.query_url, pub_time=pub_time, resp=resp)

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

    # cmdline.execute("scrapy crawl ZJ_city_3322_anji_spider -a sdt=2021-05-27 -a edt=2021-11-02".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3322_anji_spider".split(" "))
