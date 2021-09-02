# -*- coding: utf-8 -*-
# @file           :province_130_gansu_spider.py
# @description    :甘肃省政府采购网
# @date           :2021/08/30 15:47:26
# @author         :miaokela
# @version        :1.0
import copy
import re
import requests

import scrapy

from spider_pro import utils, constans, items


class Province130GansuSpiderSpider(scrapy.Spider):
    name = 'province_130_gansu_spider'
    allowed_domains = ['www.ccgp-gansu.gov.cn']
    start_urls = ['http://www.ccgp-gansu.gov.cn/web/doSearchmxarticlelssj.action']

    basic_area = '甘肃省政府采购网'
    query_url = 'http://www.ccgp-gansu.gov.cn/web/doSearchmxarticlelssj.action?limit=20&start={start_n}'
    base_url = 'http://www.ccgp-gansu.gov.cn'

    area_id = 130
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    notice_map = {
        # '招标公告': ['公开招标', '邀请招标', '询价招标', '竞争性谈判', '竞争性磋商', '单一来源公示'],
        # '资格预审结果公告': ['资格预审公告'],
        '招标变更': ['更正公告'],
        # '招标变更': ['更正公告', '废标/终止公告'],
        # '中标公告': ['中标公告', '成交公告'],
        '其他公告': ['其他公告'],
    }
    form_data = {
        "articleSearchInfoVo.releasestarttime": "",
        "articleSearchInfoVo.releaseendtime": "",
        "articleSearchInfoVo.tflag": "1",
        "articleSearchInfoVo.classname": "",
        "articleSearchInfoVo.dtype": "0",
        "articleSearchInfoVo.days": "",
        "limit": "20",
        "current": "1"
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

    @property
    def _form_data(self):
        return copy.deepcopy({
            "articleSearchInfoVo.releasestarttime": self.start_time if self.start_time else "",
            "articleSearchInfoVo.releaseendtime": self.end_time if self.end_time else "",
            "articleSearchInfoVo.tflag": "1",
            "articleSearchInfoVo.classname": "",
            "articleSearchInfoVo.dtype": "0",
            "articleSearchInfoVo.days": "",
            "limit": "20",
            "current": "1"
        })

    @classmethod
    def get_notice(cls, sub_notice):
        notice_type = ''
        for k, v in cls.notice_map.items():
            if sub_notice in v:
                notice_type = k
                break
        return notice_type

    def parse(self, resp):
        # 公告类型
        notice_els = resp.xpath('//div[@class="mBd"]//td[contains(@onclick, "classTypeCheck")]')

        form_data = self._form_data
        n_com = re.compile(r'(\d+)')
        for n, notice_el in enumerate(notice_els):
            sub_notice = notice_el.xpath('./text()').get()
            notice_type = Province130GansuSpiderSpider.get_notice(sub_notice)

            if notice_type:
                notice_type_txt = notice_el.xpath('./@onclick').get()
                notice_type_ids = n_com.findall(notice_type_txt)

                if notice_type_ids:
                    notice_type_id = notice_type_ids[0]
                    form_data['articleSearchInfoVo.classname'] = notice_type_id

                    yield scrapy.FormRequest(
                        url=self.query_url.format(start_n=1), callback=self.parse_list,
                        formdata=form_data, meta={
                            'notice_type': notice_type,
                        },
                        priority=(len(notice_els) - n),
                        cb_kwargs={
                            'form_data': copy.deepcopy(form_data),
                        },
                        dont_filter=True,
                    )

    def parse_list(self, resp, form_data):
        """
        - 获取响应的cookie
        - 最大页数
        """
        max_page = resp.xpath('//input[@id="total"]/@value').get()

        try:
            max_page = int(max_page)
        except Exception as e:
            self.logger.info('parse_list:{0}'.format(e))
        else:
            for page in range(1, max_page + 1):
                start_n = 20 * (page - 1) + 1
                form_data['current'] = str(start_n)
                yield scrapy.FormRequest(
                    url=self.query_url.format(start_n=start_n), callback=self.parse_url,
                    formdata=form_data, meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                    },
                    priority=(max_page - page) * 100,
                    dont_filter=True,
                )

    def parse_url(self, resp):
        """
        - 获取详情页
        """
        els = resp.xpath('//ul[@class="Expand_SearchSLisi"]/li')
        p_com = re.compile(r'发布时间[：:](\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*\|')
        for n, el in enumerate(els):
            c_url = el.xpath('./a/@href').get()
            title_name = el.xpath('./a/text()').get()
            pub_time_txt = el.xpath('./p[1]/span/text()').get()

            # 匹配出发布时间
            pub_times = p_com.findall(pub_time_txt)
            if pub_times:
                pub_time = pub_times[0]
                yield scrapy.Request(
                    url=''.join([self.base_url, c_url]), callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'title_name': title_name,
                        'pub_time': pub_time,
                    },
                    priority=10000 * (len(els) - n)
                )

    def parse_detail(self, resp):
        title_name = resp.meta.get('title_name', '')
        pub_time = resp.meta.get('pub_time', '')
        notice_type_ori = resp.meta.get('notice_type', '')

        content_txt = resp.xpath('//div[@class="conTxt"]').get()
        content_file = resp.xpath('//div[@class="page"]').get()
        content = ''.join([content_txt, content_file])

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//div[@class="page"]/table//tr[contains(./td/font/text(), "附件下载")]'
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, pub_time=pub_time, resp=resp)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name.strip() if title_name else ''
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

    cmdline.execute("scrapy crawl province_130_gansu_spider -a sdt=2021-08-17 -a edt=2021-08-19".split(" "))
    # cmdline.execute("scrapy crawl province_130_gansu_spider".split(" "))
