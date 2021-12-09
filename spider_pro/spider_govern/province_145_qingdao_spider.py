# -*- coding: utf-8 -*-
# @file           :province_145_qingdao_spider.py
# @description    :青岛市政府采购网
# @date           :2021/10/14 16:09:42
# @author         :miaokela
# @version        :1.0
import copy
import json
import random
import time
import re
import execjs
import requests
from datetime import datetime
from collections import OrderedDict
import traceback

import scrapy

from spider_pro import utils, constans, items


class Province145QingdaoSpiderSpider(scrapy.Spider):
    name = 'province_145_qingdao_spider'
    allowed_domains = ['ccgp-qingdao.gov.cn']
    start_urls = ['http://www.ccgp-qingdao.gov.cn/']

    basic_area = '青岛市政府采购网'
    query_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/dwr/call/plaincall/dwrmng.queryWithoutUi.dwr'
    base_url = 'http://www.ccgp-qingdao.gov.cn'
    notice_base_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/site/'
    first_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/site/channelall370200.jsp?colcode=0401&flag=0401'
    detail_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/site/read370200.jsp?id={id}&flag=0401'

    area_id = 145
    keywords_map = OrderedDict({
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    })
    url_map = {
        # '招标公告': [
        #     {'category_id': '0401', 'patch_id': '13'},  # 采购公告
        #     {'category_id': '0405', 'patch_id': '15'},  # 单一来源
        # ],
        # '招标变更': [
        #     {'category_id': '0403', 'patch_id': '17'},  # 更正公告
        # ],
        # '招标异常': [
        #     {'category_id': '0404', 'patch_id': '19'},  # 废标公告
        # ],
        '中标公告': [
            {'category_id': '0402', 'patch_id': '24'},  # 中标公告
        ],
    }
    pay_load = """callCount=1
    nextReverseAjaxIndex=0
    c0-scriptName=dwrmng
    c0-methodName=queryWithoutUi
    c0-id=0
    c0-param0=number:7
    c0-e1=string:{category_id}
    c0-e2=string:{index}
    c0-e3=number:10
    c0-e4=string:
    c0-param1=Object_Object:{{_COLCODE:reference:c0-e1, _INDEX:reference:c0-e2, _PAGESIZE:reference:c0-e3, _REGION:reference:c0-e4}}
    batchId={patch_id}
    instanceId=0
    page=%2Fsdgp2014%2Fsite%2Fchannelall370200.jsp%3Fcolcode%3D0401%26flag%3D0401
    scriptSessionId={script_session_id}""".replace(' ', '')

    custom_settings = {
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
        #     'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
        # },

        # 'CONCURRENT_REQUESTS': 1,
        # 'COOKIES_ENABLED': True,
        # 'ENABLE_PROXY_USE': False,
    }

    # @category_id: 栏目ID
    # @index: 所在页索引
    # @page_size: 当前页总记录数
    # @patch_id: 补丁号
    # @script_session_id: 未知(~PU!Y8CjFdhM3vA1fbPHobMm8EL5vMvOZNn/BMoQZNn-vp4ikf*Pu)

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

    @staticmethod
    def create_script_session_id():
        dwr_session_id = 'unoiaZsZ6YVE8vfv!OInBTsVQyPFAGVzsSn'
        js_script = """
        function tokenify(number) {
            var tokenbuf = [];
            var charmap = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ*$";
            var remainder = number;
            while (remainder > 0) {
                tokenbuf.push(charmap.charAt(remainder & 0x3F));
                remainder = Math.floor(remainder / 64);
            }
            return tokenbuf.join("");
        }
        """
        js_func = execjs.compile(js_script)
        page_id = '-'.join([
            js_func.call('tokenify', int(round(time.time() * 10 ** 3))),
            js_func.call('tokenify', random.random() * 10 ** 16),
        ])

        return '/'.join([dwr_session_id, page_id])

    @staticmethod
    def format_rslt_string(rslt_string):
        return [{
            'id': y.split(',')[0],
            'title': y.split(',')[1],
            'pub_time': y.split(',')[2],
            'code': y.split(',')[3],
        } for y in [x for x in rslt_string.split('?')] if len(y.split(',')) == 4]

    def start_requests(self):
        for notice_type, params in self.url_map.items():
            for param in params:
                patch_id = 1
                category_id = param['category_id']

                pay_load_data = {
                    'category_id': category_id,
                    'index': 1,
                    'patch_id': patch_id,
                    'script_session_id': Province145QingdaoSpiderSpider.create_script_session_id()
                }

                c_pay_load = self.pay_load.format(**pay_load_data)

                yield scrapy.Request(
                    url=self.query_url, method='POST', body=c_pay_load,
                    callback=self.parse_list, meta={
                        'notice_type': notice_type,
                    }, cb_kwargs={
                        'pay_load_data': copy.deepcopy(pay_load_data),
                        'patch_id': patch_id,
                    }, dont_filter=True,
                )

    def parse_list(self, resp, pay_load_data, patch_id):
        com = re.compile(r'rsltStringValue:"(.*?)",rsltType')
        rslt_string_list = []
        try:
            rslt_string = com.findall(resp.text)[0]
            rslt_string = u'{}'.format(rslt_string).encode('utf-8').decode('unicode_escape')
            rslt_string_list = Province145QingdaoSpiderSpider.format_rslt_string(rslt_string)
        except (Exception,) as e:
            traceback.print_exc()
            print(f'翻页结束，当前请求：{self.pay_load.format(**pay_load_data)}，错误信息：{e}')
        else:
            for n, rs in enumerate(rslt_string_list):
                pub_time = rs.get('pub_time', '')
                c_id = rs.get('id', '')
                title = rs.get('title', '')

                c_url = self.detail_url.format(**{
                    'id': c_id,
                })

                tmp_meta = copy.deepcopy(resp.meta)  # 千万不要直接修改resp.meta
                tmp_meta.update(**{
                    'title': title,
                    'pub_time': pub_time,
                })
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(
                        url=c_url, callback=self.catch_detail_url,
                        meta=tmp_meta,
                    )

            if_turn = True
            # 最后一条的发布时间早于开始时间终止翻页
            if all([self.start_time, self.end_time]):
                if rslt_string_list:
                    last_pub_time = datetime.strptime(rslt_string_list[-1]['pub_time'], '%Y-%m-%d')
                    start_time = datetime.strptime(self.start_time, '%Y-%m-%d')
                    if last_pub_time < start_time:
                        if_turn = False
            print(rslt_string_list)
            if if_turn:
                patch_id += 1
                next_index = resp.meta.get('index', 1) + 1
                resp.meta.update(**{
                    'index': next_index,
                })
                pay_load_data.update(**{
                    'index': next_index,
                    'patch_id': patch_id
                })
                pay_load = self.pay_load.format(**pay_load_data)
                yield scrapy.Request(
                    url=self.query_url, method='POST', body=pay_load,
                    callback=self.parse_list, meta=resp.meta,
                    cb_kwargs={'pay_load_data': copy.deepcopy(pay_load_data), 'patch_id': patch_id},
                    dont_filter=True,
                )

    def catch_detail_url(self, resp):
        """
        - 获取【显示公告正文】链接
        :param resp:
        :return:
        """
        inner_els = resp.xpath('//div[@class="biaotq"]/a[text()="【显示公告正文】"]')

        if inner_els:
            suffix_params_com = re.compile(r'var\s*url1\s*=\s*\"(.*?)\";.*?msgWindow')
            suffix_params = suffix_params_com.findall(resp.text.replace('\n', ''))

            if suffix_params:
                suffix_params = suffix_params[0]
                yield scrapy.Request(
                    url=''.join([self.notice_base_url, suffix_params]), callback=self.parse_detail,
                    meta=resp.meta,
                )
            else:
                self.logger.info(f'请求{resp.url}时没有获取到【显示公告正文】链接.')
        else:
            content = resp.xpath('//div[contains(@style, "overflow-x:auto; width:100%;")]').get()
            title_name = resp.meta.get('title')
            pub_time = resp.meta.get('pub_time')
            notice_type_ori = resp.meta.get('notice_type')

            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )

            # 移除相关信息
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//table[.//img[@src="images/huan.jpg"]]'
            )
            _, content = utils.remove_element_by_xpath(
                content,
                xpath_rule='//div[@style="text-align:center;"]'
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

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="cont"]').get()
        title_name = resp.meta.get('title')
        pub_time = resp.meta.get('pub_time')
        notice_type_ori = resp.meta.get('notice_type')

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 移除相关信息
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//div[contains(@style, "windowtext")]'
        )
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//div[contains(@style, "text-align:center")]'
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

    # cmdline.execute("scrapy crawl province_145_qingdao_spider -a sdt=2021-12-07 -a edt=2021-12-9".split(" "))
    cmdline.execute("scrapy crawl province_145_qingdao_spider".split(" "))
