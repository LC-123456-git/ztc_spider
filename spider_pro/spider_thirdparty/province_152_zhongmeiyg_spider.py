# -*- coding: utf-8 -*-
# @file           :province_152_zhongmeiyg_spider.py
# @description    :中煤易购
# @date           :2021/10/25 11:42:06
# @author         :miaokela
# @version        :1.0
import re

from spider_pro import constans, utils, items
import scrapy


class Province152ZhongmeiygSpiderSpider(scrapy.Spider):
    name = 'province_152_zhongmeiyg_spider'
    allowed_domains = ['zmzb.com']
    start_urls = ['http://www.zmzb.com/']

    basic_area = '中煤易购'
    area_id = 152
    base_url = 'http://www.zmzb.com'
    query_url = 'http://www.zmzb.com/cms/channel/{type_code}/index.htm?pageNo={page}'

    url_map = {
        '招标公告': [
            {'type_code': 'ywgg1hw', 'type_name': '货物'},  # 招标公告 货物
            {'type_code': 'ywgg1gc', 'type_name': '工程'},  # 招标公告 工程
            {'type_code': 'ywgg1fw', 'type_name': '服务'},  # 招标公告 服务

            {'type_code': 'ywgg2hw', 'type_name': '货物'},  # 非招标公告 货物
            {'type_code': 'ywgg2gc', 'type_name': '工程'},  # 非招标公告 工程
            {'type_code': 'ywgg2fw', 'type_name': '服务'},  # 非招标公告 服务
        ],
        '招标变更': [
            {'type_code': 'ywgg3hw', 'type_name': '货物'},  # 货物
            {'type_code': 'ywgg3gc', 'type_name': '工程'},  # 工程
            {'type_code': 'ywgg3fw', 'type_name': '服务'},  # 服务
        ],
        '中标预告': [
            {'type_code': 'ywgg4hw', 'type_name': '货物'},  # 货物
            {'type_code': 'ywgg4gc', 'type_name': '工程'},  # 工程
            {'type_code': 'ywgg4fw', 'type_name': '服务'},  # 服务
        ],
        '中标公告': [
            {'type_code': 'ywgg5hw', 'type_name': '货物'},  # 货物
            {'type_code': 'ywgg5gc', 'type_name': '工程'},  # 工程
            {'type_code': 'ywgg5fw', 'type_name': '服务'},  # 服务
        ],
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        for notice_type, params in self.url_map.items():
            for param in params:
                type_code = param.get('type_code', '')

                c_url = self.query_url.format(**{
                    'type_code': type_code,
                    'page': 1
                })
                yield scrapy.Request(
                    url=c_url, callback=self.turn_page, meta={
                        'notice_type': notice_type,
                        'type_name': param.get('type_name', '')
                    }, cb_kwargs={
                        'type_code': type_code
                    }, dont_filter=True
                )

    def turn_page(self, resp, type_code):
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        max_page_str = resp.xpath('//div[contains(@class, "fenye")]/div/a[last()]/@href').get()

        com = re.compile(r'(\d+)')
        try:
            max_pages = com.findall(max_page_str)
            max_page = int(max_pages[0])
        except Exception as e:
            self.logger.info('没有下一页:{}'.format(e))
            max_page = 1
        if all([self.start_time, self.end_time]):
            for page in range(max_page):
                c_url = self.query_url.format(**{
                    'type_code': type_code,
                    'page': (page + 1) if page > 0 else 1
                })

                judge_status = utils.judge_in_interval(
                    c_url, start_time=self.start_time, end_time=self.end_time, method='GET',
                    proxies=proxies, headers=headers, rule='//ul[@id="list1"]/li[@name="li_name"]/a/em/text()',
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, meta=resp.meta,
                        priority=(max_page - page) * 10, dont_filter=True
                    )
        else:
            for page in range(max_page):
                c_url = self.query_url.format(**{
                    'type_code': type_code,
                    'page': '_%d' % (page + 1) if page > 1 else 1
                })

                yield scrapy.Request(
                    url=c_url, callback=self.parse_list, meta=resp.meta,
                    priority=(max_page - page) * 10, dont_filter=True
                )

    def parse_list(self, resp):
        els = resp.xpath('//ul[@id="list1"]/li[@name="li_name"]')

        for n, el in enumerate(els):
            pub_time = el.xpath('./a/em/text()').get().strip()
            title_name = el.xpath('./a/span[1]/text()[last()]').get().strip()
            c_href = el.xpath('./a/@href').get()
            c_url = ''.join([self.base_url, c_href])

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                resp.meta.update(**{
                    'pub_time': pub_time,
                    'title_name': title_name,
                })
                yield scrapy.Request(
                    url=c_url, callback=self.parse_detail, meta=resp.meta,
                    priority=(len(els) - n) * 10 ** 10
                )

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="main-text"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, pub_time=pub_time, resp=resp)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name
        notice_item["pub_time"] = pub_time
        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["business_category"] = resp.meta.get('type_name', '')
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_152_zhongmeiyg_spider -a sdt=2021-09-01 -a edt=2021-10-22".split(" "))
    cmdline.execute("scrapy crawl province_152_zhongmeiyg_spider".split(" "))
