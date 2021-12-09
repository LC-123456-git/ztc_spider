# -*- coding: utf-8 -*-
# @file           :province_145_qingdao_spider.py
# @description    :青岛市政府采购网
# @date           :2021/10/14 16:09:42
# @author         :miaokela
# @version        :1.0
import asyncio
import aiohttp
import random
import time
import re
import traceback

import execjs
from collections import OrderedDict

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
        #     {'category_id': '0401'},  # 采购公告
        #     {'category_id': '0405'},  # 单一来源
        # ],
        # '招标变更': [
        #     {'category_id': '0403'},  # 更正公告
        # ],
        # '招标异常': [
        #     {'category_id': '0404'},  # 废标公告
        # ],
        '中标公告': [
            {'category_id': '0402'},  # 中标公告
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
    c0-e5=string:undefined
    c0-param1=Object_Object:{{_COLCODE:reference:c0-e1, _INDEX:reference:c0-e2, _PAGESIZE:reference:c0-e3, _REGION:reference:c0-e4, _KEYWORD:reference:c0-e5}}
    batchId=1
    instanceId=0
    page=%2Fsdgp2014%2Fsite%2Fchannelall370200.jsp%3Fcolcode%3D0401%26flag%3D0401
    scriptSessionId={script_session_id}""".replace(' ', '')

    # semaphore = asyncio.Semaphore(5)
    session = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self.results = []

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

    async def request_task(self, pi, headers=None, proxy=None):
        """
        异步请求任务
        :param pi:
        :param headers:
        :param proxy:
        :return:
        """
        # async with self.semaphore:
        try:
            async with self.session.post(
                    url=self.query_url, data=pi['post_data'], headers=headers, proxy=proxy
            ) as response:
                content = await response.text()
                com = re.compile(r'rsltStringValue:"(.*?)",rsltType')

                try:
                    rslt_string = com.findall(content)[0]
                    rslt_string = u'{}'.format(rslt_string).encode('utf-8').decode('unicode_escape')
                    rslt_string_list = Province145QingdaoSpiderSpider.format_rslt_string(rslt_string)
                except (Exception,) as e:
                    traceback.print_exc()
                else:
                    for n, rs in enumerate(rslt_string_list):
                        pub_time = rs.get('pub_time', '')
                        c_id = rs.get('id', '')
                        title = rs.get('title', '')

                        c_url = self.detail_url.format(**{
                            'id': c_id,
                        })

                        self.results.append({
                            'detail_url': c_url,
                            'title': title,
                            'pub_time': pub_time,
                            'notice_type': pi['notice_type'],
                        })
        except (Exception,) as e:
            traceback.print_exc()
            self.logger.info(f'翻页请求失败:{e}.')

    async def fetch(self, post_info, headers=None, proxy=None):
        """
        异步请求: post_info:{'data': ''}
        :param proxy:
        :param headers:
        :param post_info:
        :return:
        """
        self.session = aiohttp.ClientSession()
        async_tasks = [asyncio.ensure_future(self.request_task(pi, headers, proxy)) for pi in post_info]
        await asyncio.gather(*async_tasks)

    def parse(self, resp):
        headers = utils.get_headers(resp)
        headers = {k.decode(): v.decode() for k, v in headers.items()}
        proxies = utils.get_proxies(resp)
        proxy = ''
        for p, v in proxies.items():
            if v:
                proxy = v
                break

        script_session_id = Province145QingdaoSpiderSpider.create_script_session_id()

        data_list = []

        offset = 80
        if all([self.start_time, self.end_time]):
            offset = 10

        for notice_type, params in self.url_map.items():
            for param in params:
                category_id = param['category_id']

                index = 0
                for i in range(offset):
                    index += 1
                    pay_load_data = {
                        'category_id': category_id,
                        'index': index,
                        'script_session_id': script_session_id,
                    }

                    c_pay_load = self.pay_load.format(**pay_load_data)

                    data_list.append({
                        'post_data': c_pay_load,
                        'notice_type': notice_type,
                    })

        asyncio.run(self.fetch(data_list, headers=headers, proxy=proxy))

        for t in self.results:
            pub_time = t['pub_time']
            detail_url = t['detail_url']
            resp.meta.update(**{
                'title': t['title'],
                'pub_time': pub_time,
            })
            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                yield scrapy.Request(
                    url=detail_url, callback=self.catch_detail_url,
                    meta=resp.meta,
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
                    meta=resp.meta, priority=10 ** 10
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

    cmdline.execute("scrapy crawl province_145_qingdao_spider -a sdt=2021-09-01 -a edt=2021-12-09".split(" "))
    # cmdline.execute("scrapy crawl province_145_qingdao_spider".split(" "))
