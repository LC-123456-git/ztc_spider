"""
@file          :ZJ_city_3323_xiaoshan_spider.py
@description   :萧山
@date          :2021/05/11 14:58:47
@author        :miaokela
@version       :1.0
"""
import re
import requests
import copy
import random
from lxml import etree
from datetime import datetime
from math import ceil

import scrapy

from spider_pro import utils, constans, items


class ZjCity3323XiaoshanSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3323_xiaoshan_spider'
    allowed_domains = ['www.xiaoshan.gov.cn']
    start_urls = ['http://www.xiaoshan.gov.cn/']
    query_url = 'http://www.xiaoshan.gov.cn'
    basic_area = '浙江省-杭州市-萧山区'
    area_id = 3323
    keywords_map = {
        '变更|答疑|澄清|补充|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|预成交': '中标预告',
        '中标|成交|出让结果|交易结果': '中标公告',
    }
    url_map = {
        '招标公告': [
            {'category': '区级平台小额建设工程', 'url': 'http://www.xiaoshan.gov.cn/col/col1229181747/index.html'},
        ],
        '招标变更': [
            {'category': '区级平台小额建设工程', 'url': 'http://www.xiaoshan.gov.cn/col/col1229181748/index.html'},
        ],
        '中标预告': [
            {'category': '区级平台小额建设工程', 'url': 'http://www.xiaoshan.gov.cn/col/col1229181749/index.html'},
        ],
        '中标公告': [
            {'category': '区级平台小额建设工程', 'url': 'http://www.xiaoshan.gov.cn/col/col1229181750/index.html'},
        ]
    }
    default_data = {
        # '__VIEWSTATE': '',  # 首页不能传改参数
        '__VIEWSTATEENCRYPTED': '',
        '__EVENTVALIDATION': '',
        'txtProjectNo': '',
        'txtProjectName': '',
        'ddlState': '0',
        'grdBulletin$ctl18$BtnFirst': '首页',
        'grdBulletin$ctl18$NumGoto': '2',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    @property
    def _data(self):
        return copy.deepcopy(self.default_data)

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
                yield scrapy.Request(url=cu['url'], callback=self.parse_iframe_urls, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                })

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    @classmethod
    def get_page(cls, url, method='GET', headers=None, **kwargs):
        """获取网页html文档

        Args:
            headers: 请求头
            url (str): 链接地址
            method (str, optional): 请求方法. Defaults to 'GET'.

        Returns:
            str: 响应结果
        """
        ret = ''
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
        }
        headers = headers if headers else default_headers
        if method == 'GET':
            ret = requests.get(
                url=url, headers=headers).content.decode('utf-8')
        if method == 'POST':
            ret = requests.post(
                url=url, headers=headers, data=kwargs.get('data', {})
            ).content.decode('utf-8')
        return ret

    def parse_iframe_urls(self, resp):
        """
        从iframe中获取列表页获取的路由
        """
        start_url = resp.xpath('//iframe[position()=1]/@src').get()

        init_data = self._data
        try:
            headers = ZjCity3323XiaoshanSpiderSpider.get_headers(resp)
            text = ZjCity3323XiaoshanSpiderSpider.get_page(start_url, method='POST', data=init_data,
                                                           headers=headers)

            doc = etree.HTML(text)

            els = doc.xpath('//div[@class="RowPager"]/text()')
            if els:
                el = els[0]

                # 匹配最大页数
                # 第&nbsp;2&nbsp;/&nbsp;123&nbsp;页&nbsp;&nbsp;共&nbsp;1842&nbsp;条&nbsp;&nbsp;
                com = re.compile('.*?共.*?(\d+)')
                max_pages = com.findall(el)
                if max_pages:
                    max_page = int(max_pages[0])
                    for i in range(1, max_page + 1):
                        # 获取列表页
                        c_text = ZjCity3323XiaoshanSpiderSpider.get_page(
                            start_url, method='POST', data=init_data, headers=headers
                        )

                        c_doc = etree.HTML(c_text)
                        c_els = c_doc.xpath('//td[@class="DispLimitColumn"]/div/a/@href')

                        view_state = c_doc.xpath('//input[@id="__VIEWSTATE"]/@value')
                        view_state_encrypted = c_doc.xpath('//input[@id="__VIEWSTATEENCRYPTED"]/@value')
                        event_validation = c_doc.xpath('//input[@id="__EVENTVALIDATION"]/@value')
                        txt_project_no = c_doc.xpath('//input[@id="txtProjectNo"]/@value')
                        txt_project_name = c_doc.xpath('//input[@id="txtProjectName"]/@value')
                        ddl_state = c_doc.xpath('//input[@id="ddlState"]/@value')
                        drd_bulletin_btn_next = c_doc.xpath('//input[@id="grdBulletin$ctl18$BtnNext"]/@value')
                        drd_bulletin_num_goto = c_doc.xpath('//input[@id="grdBulletin$ctl18$NumGoto"]/@value')

                        init_data['__VIEWSTATE'] = view_state[0] if view_state else ''
                        init_data['__VIEWSTATEENCRYPTED'] = view_state_encrypted[0] if view_state_encrypted else ''
                        init_data['__EVENTVALIDATION'] = event_validation[0] if event_validation else ''
                        init_data['txtProjectNo'] = txt_project_no[0] if txt_project_no else ''
                        init_data['txtProjectName'] = txt_project_name[0] if txt_project_name else ''
                        init_data['ddlState'] = ddl_state[0] if ddl_state else ''
                        init_data['grdBulletin$ctl18$BtnNext'] = drd_bulletin_btn_next[0] if drd_bulletin_btn_next else ''
                        init_data['grdBulletin$ctl18$NumGoto'] = drd_bulletin_num_goto[0] if drd_bulletin_num_goto else ''
                        del init_data['grdBulletin$ctl18$BtnFirst']

                        for c_el in c_els:
                            yield scrapy.Request(url=self.query_url + c_el, callback=self.parse_item, meta={
                                'notice_type': resp.meta.get('notice_type', ''),
                                'category': resp.meta.get('category', ''),
                            })
        except Exception as e:
            self.log('error:{e}'.format(e=e))

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="Content"]').get()
        title_name = resp.xpath('//div[@class="AfficheTitle"]/span[position()=1]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 移除不必要信息: 删除第一个正文title/发布时间、打印关闭
        _, content = utils.remove_specific_element(content, 'div', 'class', 'AfficheTitle')

        content = utils.avoid_escape(content)  # 防止转义
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

    cmdline.execute("scrapy crawl ZJ_city_3323_xiaoshan_spider -a sdt=2021-01-01 -a edt=2021-05-11".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3323_xiaoshan_spider".split(" "))
