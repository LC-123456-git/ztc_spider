# -*- coding: utf-8 -*-
# @file           :province_129_shanxi_spider.py
# @description    :陕西省政府采购网
# @date           :2021/08/30 09:44:06
# @author         :miaokela
# @version        :1.0
import copy
import re

import scrapy

from spider_pro import utils, constans, items


class Province129ShanxiSpiderSpider(scrapy.Spider):
    name = 'province_129_shanxi_spider'
    allowed_domains = ['www.ccgp-shaanxi.gov.cn']
    start_urls = ['http://www.ccgp-shaanxi.gov.cn/notice/list.do?noticetype=3&index=3&province=province']  # 更多
    basic_area = '陕西省政府采购网'
    query_url = 'http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype={noticetype_id}'
    base_url = 'http://www.ccgp-shaanxi.gov.cn'

    area_id = 129
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    notice_map = {
        '招标预告': ['采购前公示', '意向公开'],
        '招标公告': ['采购公告'],
        '招标变更': ['更正公告'],
        '招标异常': ['终止公告'],
    }
    form_data = {
        "parameters['purcatalogguid']": "",
        "parameters['title']": "",
        "parameters['startdate']": "",
        "parameters['enddate']": "",
        "parameters['regionguid']": "",
        "parameters['projectcode']": "",
        "province": "",
        "parameters['purmethod']": ""
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
            "parameters['purcatalogguid']": "",
            "parameters['title']": "",
            "parameters['startdate']": self.start_time if self.start_time else "",
            "parameters['enddate']": self.end_time if self.end_time else "",
            "parameters['regionguid']": "",
            "parameters['projectcode']": "",
            "province": "",
            "parameters['purmethod']": ""
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
        # 区域
        region_els = resp.xpath('//ul[@id="toRegion"]/li/@onclick').extract()

        # 公告类型
        notice_els = resp.xpath('//ul[@class="type-list"]/li')

        r_com = re.compile(r'regionCity\(\'(\d+)\',')
        n_com = re.compile(r'totype\(\'(\d+)\'\)')
        for r, region_el in enumerate(region_els):
            region_ids = r_com.findall(region_el)
            if region_ids:
                region_id = region_ids[0]
                form_data = self._form_data
                form_data["parameters['regionguid']"] = region_id
                for n, notice_el in enumerate(notice_els):
                    sub_notice = notice_el.xpath('./a/text()').get()
                    notice_type = Province129ShanxiSpiderSpider.get_notice(sub_notice)

                    if notice_type:
                        notice_type_txt = notice_el.xpath('./@onclick').get()
                        notice_type_ids = n_com.findall(notice_type_txt)

                        if notice_type_ids:
                            notice_type_id = notice_type_ids[0]

                            yield scrapy.FormRequest(
                                url=self.query_url.format(noticetype_id=notice_type_id), callback=self.parse_list,
                                formdata=form_data, meta={
                                    'notice_type': notice_type,
                                },
                                priority=(len(notice_els) - n) * (len(region_els) - r),
                                cb_kwargs={
                                    'formdata': copy.deepcopy(form_data),
                                    'notice_type_id': notice_type_id,
                                },
                                dont_filter=True
                            )

    def parse_list(self, resp, formdata, notice_type_id):
        """
        - 最大页数，翻页
        """
        max_page_txt = resp.xpath('//span[contains(@class, "glyphicon-fast-forward")]/parent::a/@href').get()
        p_com = re.compile(r'(\d+)')
        max_pages = p_com.findall(max_page_txt)
        try:
            max_page = int(max_pages[0])
        except Exception as e:
            self.logger.info('parse_list error:{}'.format(e))
        else:
            for page in range(1, max_page + 1):
                formdata['page.pageNum'] = str(page)

                yield scrapy.FormRequest(
                    url=self.query_url.format(noticetype_id=notice_type_id), callback=self.parse_url,
                    formdata=formdata, meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                    },
                    priority=(max_page - page) * 100,
                    dont_filter=True,
                )

    def parse_url(self, resp):
        """
        - 获取详情页
        """
        els = resp.xpath('//div[@class="list-box"]//tbody/tr')
        for n, el in enumerate(els):
            c_url = el.xpath('./td[3]/a/@href').get()
            title_name = el.xpath('./td[3]/@title').get()
            pub_time = el.xpath('./td[4]/text()').get()
            yield scrapy.Request(
                url=c_url, callback=self.parse_detail, meta={
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

        content = resp.xpath('//div[@class="content-inner"]').get()

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

    cmdline.execute("scrapy crawl province_129_shanxi_spider -a sdt=2021-06-01 -a edt=2021-08-30".split(" "))
    # cmdline.execute("scrapy crawl province_129_shanxi_spider".split(" "))
