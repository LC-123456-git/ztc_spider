# @file           :province_125_liaoning_spider.py
# @description    :辽宁省政府采购网
# @date           :2021/08/23 09:14:29
# @author         :miaokela
# @version        :1.0
import re
import random
import os
import time
from datetime import datetime
from lxml import etree
import copy
import json
import math
import html
import requests
import pytesseract
from PIL import Image

import scrapy
from scrapy.http import headers

from spider_pro import utils, constans, items


class Province125LiaoningSpiderSpider(scrapy.Spider):
    name = 'province_125_liaoning_spider'
    allowed_domains = ['www.ccgp-liaoning.gov.cn']
    start_urls = ['http://www.ccgp-liaoning.gov.cn/']
    basic_area = '辽宁省政府采购网'
    query_url = 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=getPubInfoList'
    detail_url = 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=getPubInfoViewOpenNew&infoId={infoId}'
    captcha_server = 'http://www.ccgp-liaoning.gov.cn/jcaptcha/{random_n}'
    check_auth_url = 'http://www.ccgp-liaoning.gov.cn/download.do?method=checkAuth&r_t={r_t}'
    base_url = 'http://www.ccgp-liaoning.gov.cn'

    area_id = 125
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'info_type_code': '1007', 'specific_category': ['征求社会公众意见公示']},  # 其他公告【征求社会公众意见公示】
        ],
        '招标公告': [
            {'info_type_code': '1001', 'specific_category': []},  # 采购公告
            {'info_type_code': '1008', 'specific_category': []},  # 单一来源公示  文件通过验证码输入下载
        ],
        '招标变更': [
            {'info_type_code': '1003', 'specific_category': []},  # 更正公告
        ],
        '招标异常': [
            {'info_type_code': '1002', 'specific_category': ['失败公告', '终止公告']},  # 结果公告【失败公告】,结果公告【终止公告】
        ],
        '中标公告': [
            {'info_type_code': '1002', 'specific_category': ['中标公告', '成交公告']},  # 结果公告【中标公告】,结果公告【成交公告】
        ],
    }
    FORM_DATA = {
        'current': '1',
        'rowCount': '10',
        'releaseDateStart': '',
        'releaseDateEnd': '',
        'infoTypeCode': '',
        'privateOrCity': '1',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    def get_form_data(self, **kwargs):
        c_form_data = copy.deepcopy(Province125LiaoningSpiderSpider.FORM_DATA)
        c_form_data.update(**kwargs)
        if all([self.start_time, self.end_time]):
            c_form_data.update(**{
                'releaseDateStart': self.start_time,
                'releaseDateEnd': self.end_time,
            })
        return c_form_data

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
                info_type_code = param['info_type_code']
                specific_category = param['specific_category']

                form_data = self.get_form_data(**{
                    'infoTypeCode': info_type_code,
                })

                yield scrapy.FormRequest(url=self.query_url, formdata=form_data, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                    'specific_category': specific_category,
                    'row_count': form_data.get('rowCount', 0),
                    'info_type_code': info_type_code,
                }, dont_filter=True)

    def parse_list(self, resp):
        info_type_code = resp.meta.get('info_type_code', '')
        notice_type = resp.meta.get('notice_type', '')
        specific_category = resp.meta.get('specific_category', '')
        row_count = resp.meta.get('row_count')
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        content = json.loads(resp.text)
        total = content.get('total', 0)

        max_page = math.ceil(total / int(row_count)) if row_count else 0

        # for page in range(3):
        for page in range(max_page):
            form_data = self.get_form_data(**{
                'infoTypeCode': info_type_code,
                'current': str(page + 1)
            })

            judge_status = utils.judge_in_interval(
                self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST',
                data=form_data, proxies=proxies, headers=headers,
                rule='//rows/releaseDate/text()', doc_type='json'
            )
            if judge_status == 0:
                break
            elif judge_status == 2:
                continue
            else:
                yield scrapy.FormRequest(url=self.query_url, formdata=form_data, callback=self.parse_urls, meta={
                    'notice_type': notice_type,
                    'specific_category': specific_category,
                }, dont_filter=True, priority=max_page - page)

    def parse_urls(self, resp):
        notice_type = resp.meta.get('notice_type', '')
        specific_category = resp.meta.get('specific_category', '')
        content = json.loads(resp.text)
        rows = content.get('rows', [])

        for n, row in enumerate(rows):
            info_id = row.get('id', '')
            title = row.get('title', '')
            info_type_name = row.get('infoTypeName', '')
            c_url = self.detail_url.format(infoId=info_id)

            pub_time = row.get('releaseDate', '')

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                # 判断当前文章类型
                if not specific_category or info_type_name in specific_category:
                    # c_url = 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=getPubInfoViewOpenNew
                    # &infoId=-1cecdbc817b574b1c36-429f'
                    yield scrapy.Request(url=c_url, callback=self.parse_detail, meta={
                        'notice_type': notice_type,
                        'pub_time': pub_time,
                        'title': title,
                    }, priority=(len(rows) - n) * 10000, dont_filter=True)
                    break

    def get_code_from_captcha(self, pic_url, proxies=None, headers=None):
        """
        - 下载图片，识别图片，返回code
        """
        content = utils.get_page(pic_url, proxies=proxies, headers=headers, set_decode=False)

        img_path = os.path.join(self.settings.get('IMAGES_PATH'), 'captcha.jpeg')
        print(img_path)
        with open(img_path, 'wb') as f:
            f.write(content)

        # 读取图片识别
        img = Image.open(img_path)
        txt = pytesseract.image_to_string(img)
        txt = ''.join(txt.split(' '))
        com = re.compile(r'(\d+)')
        codes = com.findall(txt)
        return codes[0] if codes else ''

    def reset_file_href_from_captcha(self, content, proxies=None, headers=None):
        """
        - 获取验证码图片、识别
        - 获取真实文件地址
        - 替换原有文件地址
            {
                "status":"success",
                "msg":"http://218.60.151.61:9004/lnnew/M00/10/07/ooYBAGESKzWAUavfACEMFYfxm1o365.doc?" + \
                        "token\u003dae0e1d7394d6aeac81c5d4cb03c1697a\u0026t\u003d1629731060713\u0026y\u003de"
            }
        """
        doc = etree.HTML(content)
        els = doc.xpath('//a[contains(@onclick, "downloadFile")]')

        c_data = {}

        f_com = re.compile(r'fileName=(.*?)&')
        t_com = re.compile(r'type=(.*?)&')
        for el in els:
            on_click = el.attrib.get('onclick', '')
            file_names = f_com.findall(on_click)
            types = t_com.findall(on_click)
            if all([file_names, types]):
                file_name = file_names[0]
                c_type = types[0]
                # 下载图片，识别图片，返回code
                pic_code = self.get_code_from_captcha(
                    self.captcha_server.format(random_n=round(random.randint(1, 100) * 100000)), proxies=proxies,
                    headers=headers
                )

                c_data.update(**{
                    'fileName': file_name,
                    'authType': c_type,
                    't': str(round(time.time() * 1000)),
                    'j_jcaptcha': str(pic_code)
                })

                check_auth_url = self.check_auth_url.format(r_t='%s%s' % (str(round(time.time() * 1000)), random.random()*1000))
                result = utils.get_page(check_auth_url, method='POST', data=c_data, proxies=proxies,
                                        headers=headers)

                file_info = json.loads(result)
                file_url = file_info.get('msg', '')

                el.attrib.clear()
                el.attrib['href'] = file_url

        content = etree.tounicode(doc, method='html').replace('<html><body>', '').replace('</body></html>', '')
        return content

    def parse_detail(self, resp):
        proxies = utils.get_proxies(resp)
        headers = utils.get_headers(resp)

        pre_content = resp.xpath('//div[@id="template"]/text()').get()
        pre_content = html.unescape(pre_content.replace('\n', ''))

        # 正则提取<body></body>内部信息
        c_com = re.compile(r'<body>(.*?)</body>')
        contents = c_com.findall(pre_content)
        if contents:
            content = contents[0]

            title_name = resp.meta.get('title')
            pub_time = resp.meta.get('pub_time')
            notice_type_ori = resp.meta.get('notice_type')

            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )

            # - 移除不必要信息
            # 公告信息移除
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//table[contains(.//span/text(), "公告标题")]'
            )
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//span[contains(text(), "公告信息")]'
            )

            # Title
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//h1[1]'
            )
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//b[1]'
            )

            # 处理文件地址
            content = self.reset_file_href_from_captcha(content, proxies=proxies, headers=headers)

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

    cmdline.execute("scrapy crawl province_125_liaoning_spider -a sdt=2021-06-01 -a edt=2021-08-20".split(" "))
    # cmdline.execute("scrapy crawl province_125_liaoning_spider".split(" "))
