# -*- coding: utf-8 -*-
# @file           :province_117_hebei_spider.py
# @description    :中国河北政府采购网
# @date           :2021/08/09 16:56:29
# @author         :miaokela
# @version        :1.0
import re
import random
import requests
from datetime import datetime
from lxml import etree

import scrapy

from spider_pro import utils, constans, items


class Province117HebeiSpiderSpider(scrapy.Spider):
    name = 'province_117_hebei_spider'
    allowed_domains = ['ccgp-hebei.gov.cn']
    start_urls = ['http://ccgp-hebei.gov.cn/']

    basic_area = '中国河北政府采购网'
    query_url = 'http://search.hebcz.cn:8080/was5/web/search?'

    area_id = 117
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
    }
    url_map = {
        '招标预告': [
            {'params': 'channelid=218195&lanmu=zfcgyx&city=province'},  # 政府采购意向 省级
            {'params': 'channelid=218195&lanmu=zfcgyxAAAA&city=sjz_ys'},  # 政府采购意向 县市
        ],
        '招标公告': [
            {'params': 'channelid=240117&lanmu=zbgg&syprovince=0'},  # 招标采购 省级
            {'params': 'channelid=240117&lanmu=zbgg&syprovince=0'},  # 招标采购 县市
            {'params': 'channelid=228483&lanmu=fgw_zbfggg&syprovince=0'},  # 招标采购 其他
        ],
        '招标变更': [
            {'params': 'channelid=218195&lanmu=zfcgyxbg&city=province'},  # 政府采购意向变更 省级
            {'params': 'channelid=240117&lanmu=gzgg&syprovince=0'},  # 变更 省级
            {'params': 'channelid=218195&lanmu=zfcgyxbgAAAS&city=sjz'},  # 政府采购意向变更 县市
            {'params': 'channelid=240117&lanmu=gzgg&syprovince=0'},  # 变更 县市
            {'params': 'channelid=228483&lanmu=fgw_gzfggg&syprovince=0'},  # 变更 其他
        ],
        '招标异常': [
            {'params': 'channelid=240117&lanmu=fbgg&syprovince=0'},  # 废标终止
        ],
        '中标公告': [
            {'params': 'channelid=240117&lanmu=zhbgg&syprovince=0'},  # 中标结果
            {'params': 'channelid=228483&lanmu=zhbfggg_fgw&syprovince=0'},  # 中标结果
        ],
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

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    def judge_in_interval(self, url, method='GET', resp=None, ancestor_el='table', ancestor_attr='id', ancestor_val='',
                          child_el='tr', time_sep='-', doc_type='html', **kwargs):
        """
        判断最末一条数据是否在区间内
        Args:
            resp: scrapy请求响应
            url: 分页链接
            method: 请求方式
            ancestor_el: 祖先元素
            ancestor_attr: 属性
            ancestor_val: 属性值
            child_el: 子孙元素
            time_sep: 时间中间分隔符 默认：-
            doc_type: 文档类型
            **kwargs:
                @data: POST请求体
                @enhance_els: 扩展xpath匹配子节点细节['table', 'tbody'] 连续节点
        Returns:
            status: 结果状态
                1 首条在区间内 可抓、可以翻页
                0 首条不在区间内 停止翻页
                2 末条大于最大时间 continue
        """
        status = 0
        headers = Province117HebeiSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers, proxies=resp.meta.get('proxy') if resp else None).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'
                    ), headers=headers, proxies=resp.meta.get('proxy') if resp else None).text
                if text:
                    els = []
                    if doc_type == 'html':
                        doc = etree.HTML(text)

                        # enhance_els
                        enhance_els = kwargs.get('enhance_els', [])

                        enhance_condition = ''
                        if enhance_els:
                            for enhance_el in enhance_els:
                                enhance_condition += '/{0}'.format(enhance_el)

                        _path = '//{ancestor_el}[contains(@{ancestor_attr},"{ancestor_val}")]{enhance_condition}/{child_el}[last()]/text()[not(normalize-space()="")]'.format(
                            **{
                                'ancestor_el': ancestor_el,
                                'ancestor_attr': ancestor_attr,
                                'ancestor_val': ancestor_val,
                                'child_el': child_el,
                                'enhance_condition': enhance_condition
                            })
                        els = doc.xpath(_path)
                    if doc_type == 'xml':
                        doc = etree.XML(text)
                        _path = '//{child_el}/text()'.format(**{
                            'child_el': child_el,
                        })
                        els = doc.xpath(_path)
                    if els:
                        first_el = els[0]
                        final_el = els[-1]

                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' % (time_sep, time_sep))

                        first_pub_time = t_com.findall(first_el)
                        final_pub_time = t_com.findall(final_el)

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = datetime.strptime(
                                first_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            final_pub_time = datetime.strptime(
                                final_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            start_time = datetime.strptime(
                                self.start_time, '%Y-%m-%d')
                            end_time = datetime.strptime(
                                self.end_time, '%Y-%m-%d')
                            # 比最大时间大 continue
                            # 比最小时间小 break
                            # 1 首条在区间内 可抓、可以翻页
                            # 0 首条不在区间内 停止翻页
                            # 2 末条大于最大时间 continue
                            if first_pub_time < start_time:
                                status = 0
                            elif final_pub_time > end_time:
                                status = 2
                            else:
                                status = 1
            except Exception as e:
                self.log(e)
        else:
            status = 1  # 没有传递时间
        return status

    def start_requests(self):
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                params = cu['params']
                c_url = ''.join([self.query_url, params])
                yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'url': c_url
                })

    def parse_list(self, resp, url):
        last_page = resp.xpath('//a[@class="last-page"]/@href').get()

        try:
            p_com = re.compile(r'\?page=(\d+)')
            max_pages = p_com.findall(last_page)
            max_age = int(max_pages[0])
        except Exception as e:
            print(e)
            max_age = 1
        # for page in range(1, max_age + 1):
        for page in range(1, 2):
            c_url = ''.join([url, '&page={0}'.format(page)])

            judge_status = self.judge_in_interval(
                c_url, method='GET', ancestor_el='table', ancestor_attr='id',
                ancestor_val='moredingannctable',
                child_el='/td[@class="txt1"]/span[position()=1]', resp=resp,
            )
            if judge_status == 0:
                break
            elif judge_status == 2:
                continue
            else:
                print(c_url)
                yield scrapy.Request(url=c_url, callback=self.parse_urls, meta={
                    'notice_type': resp.meta.get('notice_type', ''),
                }, priority=max_age - page, dont_filter=True)

    def parse_urls(self, resp):
        url_els = resp.xpath('//tr[@id="biaoti"]/td[2]/a/@href').extract()
        pub_time_els = resp.xpath('//td[@class="txt1"]/span[position()=1]/text()').extract()

        for n, href in enumerate(url_els):
            if href:
                pub_time = pub_time_els[n]
                if pub_time:
                    pub_time = pub_time.strip()
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(url=href, callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'pub_time': pub_time,
                    }, priority=(len(url_els) - n) * 1000)

    def parse_detail(self, resp):
        content = resp.xpath('//table[position()=1]').get()
        title_name = resp.xpath('//span[@class="txt2"]/text()').get()

        notice_type_ori = resp.meta.get('notice_type')

        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 移除不必要信息
        _, content = utils.remove_specific_element(content, 'span', 'class', 'txt2')
        _, content = utils.remove_specific_element(content, 'td', 'align', 'center', text="（公告来源：")
        _, content = utils.remove_specific_element(content, 'input', 'class', 'guanbi')
        _, content = utils.remove_specific_element(content, 'td', 'bgcolor', 'EAEAEA')
        _, content = utils.remove_specific_element(content, 'td', 'class', 'txt7')

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
        notice_item["category"] = '采购'
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_117_hebei_spider -a sdt=2021-06-01 -a edt=2021-08-09".split(" "))
    # cmdline.execute("scrapy crawl province_117_hebei_spider".split(" "))
