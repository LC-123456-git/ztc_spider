# -*- coding: utf-8 -*-
# @file           :province_139_fujian_spider.py
# @description    :福建政府采购网
# @date           :2021/10/20 08:40:26
# @author         :miaokela
# @version        :1.0
import re

from spider_pro import constans, utils, items
import scrapy


class Province139FujianSpiderSpider(scrapy.Spider):
    name = 'province_139_fujian_spider'
    allowed_domains = ['ccgp-fujian.gov.cn']
    start_urls = ['http://ccgp-fujian.gov.cn/']

    basic_area = '福建政府采购网'
    area_id = 139
    base_url = 'http://ccgp-fujian.gov.cn'
    query_url = 'http://www.ccgp-fujian.gov.cn/3500/noticelist/d03180adb4de41acbb063875889f9af1/'

    url_map = {
        '招标预告': [
            {'notice_type_code': '8fd455f244cc11eb88b50cda411d946b'},  # 采购意向公开
        ],
        '招标公告': [
            {'notice_type_code': '463fa57862ea4cc79232158f5ed02d03'},  # 采购公告
            {'notice_type_code': '255e087cf55a42139a1f1b176b244ebb'},  # 单一来源公示
        ],
        '招标变更': [
            {'notice_type_code': '7dc00df822464bedbf9e59d02702b714'},  # 更正公告
            {'notice_type_code': 'd812e46569204c7fbd24cbe9866d0651'},  # 结果更正公告
        ],
        '中标公告': [
            {'notice_type_code': 'b716da75fe8d4e4387f5a8c72ac2a937'},  # 结果公告
        ],
        '其他公告': [
            {'notice_type_code': '1d5eac5cd0b14515aacaf2e9aee5f928'},  # 合同公告
            {'notice_type_code': 'ce932df3036340559c19acc4935c04b9'},  # 网上超市合同
        ]
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
                notice_type_code = param.get('notice_type_code', '')

                c_url = ''.join([self.query_url, '?', '&'.join(['page=1', 'notice_type=%s' % notice_type_code])])

                yield scrapy.Request(
                    url=c_url, callback=self.turn_page, meta={
                        'notice_type': notice_type,
                    }, cb_kwargs={
                        'notice_type_code': notice_type_code,
                    }
                )

    def turn_page(self, resp, notice_type_code):
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        max_page_str = resp.xpath('//button[contains(text(), "末页")]/@onclick').get()

        com = re.compile(r'page=(\d+)')
        max_pages = com.findall(max_page_str)
        max_page = int(max_pages[0])

        if all([self.start_time, self.end_time]):
            for page in range(max_page):
                # for page in range(2):
                c_url = ''.join([
                    self.query_url,
                    '?',
                    '&'.join(['page=%d' % (page + 1), 'notice_type=%s' % notice_type_code])
                ])

                judge_status = utils.judge_in_interval(
                    c_url, start_time=self.start_time, end_time=self.end_time, method='GET',
                    proxies=proxies, headers=headers, rule='//tr[@class="gradeX"]/td[last()]/text()',
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, meta=resp.meta, dont_filter=True,
                        priority=(max_page - page) * 10 ** 2
                    )
        else:
            for page in range(max_page):
                c_url = ''.join([
                    self.query_url,
                    '?',
                    '&'.join(['page=%d' % (page + 1), 'notice_type=%s' % notice_type_code])
                ])

                yield scrapy.Request(
                    url=c_url, callback=self.parse_list, meta=resp.meta, dont_filter=True,
                    priority=(max_page - page) * 10 ** 2
                )

    def parse_list(self, resp):
        els = resp.xpath('//tr[@class="gradeX"]')

        for n, el in enumerate(els):
            pub_time = el.xpath('./td[last()]/text()').get()
            title_name = el.xpath('./td[4]/a/text()').get()
            c_href = el.xpath('./td[4]/a/@href').get()
            c_url = ''.join([self.base_url, c_href])

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                resp.meta.update(**{
                    'pub_time': pub_time,
                    'title_name': title_name
                })
                yield scrapy.Request(
                    url=c_url, callback=self.parse_detail, meta=resp.meta,
                    priority=(len(els) - n) * 10 ** 8
                )

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="notice-con"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

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
        notice_item["category"] = '政府采购'
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_139_fujian_spider -a sdt=2021-09-01 -a edt=2021-10-19".split(" "))
    # cmdline.execute("scrapy crawl province_139_fujian_spider".split(" "))
