# -*- coding: utf-8 -*-
"""
@file           :province_80_yankuangzhaocai_spider.py
@description    :山东省-兖矿集团电子招投标采购平台
@date           :2021/06/17 13:20:56
@author         :miaokela
@version        :1.0
"""
import scrapy
import re
import requests
import random
from datetime import datetime
from lxml import etree

from spider_pro import utils, items, constans


class Province80YankuangzhaocaiSpiderSpider(scrapy.Spider):
    name = 'province_80_yankuangzhaocai_spider'
    allowed_domains = ['www.ykjtzb.com']
    start_urls = ['http://www.ykjtzb.com/']
    query_url = 'http://www.ykjtzb.com'
    basic_area = '山东省-兖矿集团电子招投标采购平台'
    area_id = 80
    keywords_map = {
        '资格审查': '资格预审结果公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标公告': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg1qb/index.htm',  # 招标采购-招标公告
                'http://www.ykjtzb.com/cms/channel/zbywgg5qb/index.htm',  # 招标采购-二次公告
                'http://www.ykjtzb.com/cms/channel/fzbywgg5qb/index.htm',  # 非招标采购-二次公告
                'http://www.ykjtzb.com/cms/channel/fzbywgg1qb/index.htm',  # 非招标采购-采购公告
            ],
        },
        '资格预审结果公告': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg7qb/index.htm',   # 招标采购-资格预审公告
            ],
        },
        '招标变更': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg6qb/index.htm',  # 招标采购-变更公告
                'http://www.ykjtzb.com/cms/channel/fzbywgg4qb/index.htm',  # 非招标采购-变更公告
            ],
        },
        '中标预告': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg2qb/index.htm',  # 招标采购-中标候选人公示
            ],
        },
        '中标公告': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg3qb/index.htm',  # 招标采购-中标结果公示
                'http://www.ykjtzb.com/cms/channel/fzbywgg2qb/index.htm',  # 非招标采购-采购公示
            ],
        },
        '其他公告': {
            'url': [
                'http://www.ykjtzb.com/cms/channel/zbywgg4qb/index.htm',  #  招标采购-其他公告
                'http://www.ykjtzb.com/cms/channel/fzbywgg3qb/index.htm',  # 非招标采购-其他公告
            ],
        },
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
        headers = Province80YankuangzhaocaiSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'), headers=headers).text
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

                        _path = '//{ancestor_el}[@{ancestor_attr}="{ancestor_val}"]{enhance_condition}//{child_el}[last()]/text()[not(normalize-space()="")]'.format(
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

                        el = els[-1]
                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' %
                                           (time_sep, time_sep))

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
        for notice_type, url_dic in self.url_map.items():
            urls = url_dic.get('url', [])

            for c_url in urls:
                yield scrapy.Request(url=c_url, callback=self.get_max_page, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'url': c_url,
                })

    def get_max_page(self, resp, url):
        last_page_str = resp.xpath('//div[@class="pag-link"]/a[last()]/@onclick').get()

        if last_page_str:
            page_com = re.compile('(\d+)')
            max_pages = page_com.findall(last_page_str)

            if max_pages:
                try:
                    max_page = int(max_pages[0])
                except ValueError as e:
                    self.logger.info('error:{0}'.format(e))
                else:
                    for i in range(1, max_page + 1):
                        c_url = '{0}?pageNo={1}'.format(url, i)
                        judge_status = self.judge_in_interval(
                            c_url, method='GET', ancestor_el='ul', ancestor_attr='id', ancestor_val='list1',
                            child_el='em', resp=resp,
                        )
                        if judge_status == 0:
                            break
                        elif judge_status == 2:
                            continue
                        else:
                            yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                                'notice_type': resp.meta.get('notice_type', ''),
                            }, priority=(max_page - i) * 10)
                
    def parse_list(self, resp):
        """
        获取detail_url, pub_time
        """
        els = resp.xpath('//ul[@id="list1"]/li')
        for n, el in enumerate(els):
            href = el.xpath("./a/@href").get()
            if href:
                pub_time = el.xpath("./a/em/text()").get()
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(url=self.query_url + href, callback=self.parse_item, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'pub_time': pub_time,
                    }, priority=10000 * (len(els) - n))

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="main-text"]').get()
        title_name = resp.xpath('//div[@class="article-title"]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

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
        notice_item["category"] = '采购'
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_80_yankuangzhaocai_spider -a sdt=2021-01-01 -a edt=2021-06-17".split(" "))
    cmdline.execute("scrapy crawl province_80_yankuangzhaocai_spider".split(" "))

