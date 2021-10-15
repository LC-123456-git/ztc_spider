# -*- coding: utf-8 -*-
# @file           :province_145_qingdao_spider.py
# @description    :青岛市政府采购网
# @date           :2021/10/14 16:09:42
# @author         :miaokela
# @version        :1.0
import random
import time
import re
import execjs

import scrapy

from spider_pro import utils, constans, items


class Province145QingdaoSpiderSpider(scrapy.Spider):
    name = 'province_145_qingdao_spider'
    allowed_domains = ['www.ccgp-qingdao.gov.cn']
    start_urls = ['http://www.ccgp-qingdao.gov.cn/']

    basic_area = '青岛市政府采购网'
    query_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/dwr/call/plaincall/dwrmng.queryWithoutUi.dwr'
    base_url = 'http://www.ccgp-qingdao.gov.cn'
    first_url = 'http://www.ccgp-qingdao.gov.cn/sdgp2014/site/channelall370200.jsp?colcode=0401&flag=0401'

    area_id = 145
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标公告': [
            {'category_id': '0401', 'patch_id': '13'},  # 采购公告
            {'category_id': '0405', 'patch_id': '15'},  # 单一来源
        ],
        '招标变更': [
            {'category_id': '0403', 'patch_id': '17'},  # 更正公告
        ],
        '招标异常': [
            {'category_id': '0404', 'patch_id': '19'},  # 废标公告
        ],
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
    c0-e5=string:undefined
    c0-param1=Object_Object:{{_COLCODE:reference:c0-e1, _INDEX:reference:c0-e2, _PAGESIZE:reference:c0-e3, _REGION:reference:c0-e4, _KEYWORD:reference:c0-e5}}
    batchId={patch_id}
    instanceId=0
    page=%2Fsdgp2014%2Fsite%2Fchannelall370200.jsp%3Fcolcode%3D0401%26flag%3D0401
    scriptSessionId={script_session_id}""".replace(' ', '')

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
        dwr_session_id = '~PU!Y8CjFdhM3vA1fbPHobMm8EL5vMvOZNn'
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
            js_func.call('tokenify', int(round(time.time() * 10 * 3))),
            js_func.call('tokenify', random.random() * 10 ** 16),
        ])

        return '/'.join([dwr_session_id, page_id])

    def start_requests(self):
        yield scrapy.Request(
            url=self.first_url, callback=self.parse
        )

    def parse(self, resp):
        for notice_type, params in self.url_map.items():
            for param in params:
                patch_id = param['patch_id']
                category_id = param['category_id']

                c_pay_load = self.pay_load.format(**{
                    'category_id': category_id,
                    'index': 1,
                    'patch_id': patch_id,
                    'script_session_id': Province145QingdaoSpiderSpider.create_script_session_id()
                })

                yield scrapy.Request(
                    url=self.query_url, method='POST', body=c_pay_load, headers={
                        # 'Content-Type': ['text/plain'],
                        # 'Accept': ['*/*']
                    },
                    callback=self.parse_list, meta={
                        'notice_type': notice_type,
                    })

    def parse_list(self, resp):
        print(resp)
        # headers = utils.get_headers(resp)
        # proxies = utils.get_proxies(resp)
        #
        # last_page_loca = resp.xpath('//form[@id="formModule"]/p/a[text()="末页"]/@onclick').get()
        # notice_type = resp.meta.get('notice_type', '')
        # com = re.compile(r'(\d+)')
        #
        # last_pages = com.findall(last_page_loca)
        # if last_pages:
        #     max_page = last_pages[0]
        #
        #     try:
        #         max_page = int(max_page)
        #     except Exception as e:
        #         print(e)
        #         max_page = 1
        #     c_form_data = {
        #         'noticetypeId': notice_type_id,
        #         'categoryId': category_id,
        #     }
        #     if all([self.start_time, self.end_time]):
        #         for page in range(1, max_page + 1):
        #             c_form_data['currentPage'] = str(page)
        #             judge_status = utils.judge_in_interval(
        #                 self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST',
        #                 data=c_form_data, proxies=proxies, headers=headers,
        #                 rule='//div[@id="list_right"]//li/span[last()]/text()[not(normalize-space()="")]'
        #             )
        #             if judge_status == 0:
        #                 break
        #             elif judge_status == 2:
        #                 continue
        #             else:
        #                 yield scrapy.FormRequest(
        #                     url=self.query_url, formdata=c_form_data, callback=self.parse_urls, meta={
        #                         'notice_type': notice_type,
        #                     }, dont_filter=True, priority=max_page - page)
        #     else:
        #         for page in range(1, max_page + 1):
        #             c_form_data['currentPage'] = str(page)
        #             yield scrapy.FormRequest(url=self.query_url, formdata=c_form_data, callback=self.parse_urls, meta={
        #                 'notice_type': notice_type,
        #             }, dont_filter=True, priority=max_page - page)

    def parse_urls(self, resp):
        li_els = resp.xpath('//div[@id="list_right"]/ul/li')

        for n, li in enumerate(li_els):
            href = li.xpath('./a/@href').get()
            pub_time = li.xpath('./span/text()').get()

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                yield scrapy.Request(url=''.join([self.base_url, href]), callback=self.parse_detail, meta={
                    'notice_type': resp.meta.get('notice_type'),
                    'pub_time': pub_time,
                }, priority=(len(li_els) - n) * 10000, dont_filter=True)

    def parse_detail(self, resp):
        content = resp.xpath('//div[@id="xiangqingneiron"]').get()
        title_name = resp.xpath('//h2[position()=1]/font/text()').get()
        pub_time = resp.meta.get('pub_time')
        notice_type_ori = resp.meta.get('notice_type')

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 移除不必要信息
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//h2[position()=1]/font'
        )  # 标题
        _, content = utils.remove_element_by_xpath(
            content,
            xpath_rule='//h3[position()=1]/span'
        )  # 日期

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

    cmdline.execute("scrapy crawl province_145_qingdao_spider -a sdt=2021-10-01 -a edt=2021-10-14".split(" "))
    # cmdline.execute("scrapy crawl province_145_qingdao_spider".split(" "))
