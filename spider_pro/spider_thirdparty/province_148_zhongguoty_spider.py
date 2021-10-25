# -*- coding: utf-8 -*-
# @file           :province_148_zhongguoty_spider.py
# @description    :中国通用招标网
# @date           :2021/10/25 13:36:40
# @author         :miaokela
# @version        :1.0
import re

from spider_pro import constans, utils, items
import scrapy


class Province148ZhongguotySpiderSpider(scrapy.Spider):
    name = 'province_148_zhongguoty_spider'
    allowed_domains = ['china-tender.com.cn']
    start_urls = ['https://www.china-tender.com.cn/']

    basic_area = '中国通用招标网'
    area_id = 148
    base_url = 'https://www.china-tender.com.cn'
    query_url = 'https://www.china-tender.com.cn/{type_code}/index{page}.jhtml'

    url_map = {
        '招标公告': [
            {'type_code': 'zbhw', 'type_name': '货物'},  # 货物
            {'type_code': 'zbgc', 'type_name': '工程'},  # 工程
            {'type_code': 'zbfw', 'type_name': '服务'},  # 服务
        ],
        '资格预审结果公告': [
            {'type_code': 'zshw', 'type_name': '货物'},  # 货物
            {'type_code': 'zsgc', 'type_name': '工程'},  # 工程
            {'type_code': 'zsfw', 'type_name': '服务'},  # 服务
        ],
        '招标变更': [
            {'type_code': 'bghw', 'type_name': '货物'},  # 货物
            {'type_code': 'bggc', 'type_name': '工程'},  # 工程
            {'type_code': 'bgfw', 'type_name': '服务'},  # 服务
        ],
        '中标公告': [
            {'type_code': 'jghw', 'type_name': '货物'},  # 货物
            {'type_code': 'jggc', 'type_name': '工程'},  # 工程
            {'type_code': 'jgfw', 'type_name': '服务'},  # 服务
        ],
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    custom_settings = {
        'ENABLE_PROXY_USE': False,
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
                    'page': ''
                })
                yield scrapy.Request(
                    url=c_url, callback=self.turn_page, meta={
                        'notice_type': notice_type,
                        'type_name': param.get('type_name', '')
                    }, cb_kwargs={
                        'type_code': type_code
                    }
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
                    'page': '_%d' % (page + 1) if page > 0 else ''
                })

                judge_status = utils.judge_in_interval(
                    c_url, start_time=self.start_time, end_time=self.end_time, method='GET',
                    proxies=proxies, headers=headers, rule='//span[@class="Gray Right"]/text()', verify=False,
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, meta=resp.meta,
                        priority=(max_page - page) * 10
                    )
        else:
            for page in range(max_page):
                c_url = self.query_url.format(**{
                    'type_code': type_code,
                    'page': '_%d' % (page + 1) if page > 1 else ''
                })

                yield scrapy.Request(
                    url=c_url, callback=self.parse_list, meta=resp.meta,
                    priority=(max_page - page) * 10
                )

    def parse_list(self, resp):
        t_com = re.compile(r'(\d+[.\-/]\d+[.\-/]\d+)')

        els = resp.xpath('//div[@class="ConBox1"]//li')

        for n, el in enumerate(els):
            try:
                pub_time = el.xpath('./p/span[last()]/text()').get()
                pub_time = t_com.findall(pub_time)[0]
            except Exception as e:
                self.logger.info('error:{}'.format(e))
            else:
                title_name = el.xpath('./a/text()').get()
                area = el.xpath('./p/span[2]/a/text()').get()
                c_href = el.xpath('./a/@href').get()
                c_url = ''.join([self.base_url, c_href])

                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    resp.meta.update(**{
                        'pub_time': pub_time,
                        'title_name': title_name,
                        'area': area,
                    })
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_detail, meta=resp.meta,
                        priority=(len(els) - n) * 10 ** 10
                    )

    def parse_detail(self, resp):
        content = resp.xpath('//div[contains(@class, "Contnet")]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')
        area = resp.meta.get('area')

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
        notice_item["info_source"] = '-'.join([area, self.basic_area]) if area else self.basic_area
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

    cmdline.execute("scrapy crawl province_148_zhongguoty_spider -a sdt=2021-09-01 -a edt=2021-10-22".split(" "))
    # cmdline.execute("scrapy crawl province_148_zhongguoty_spider".split(" "))

