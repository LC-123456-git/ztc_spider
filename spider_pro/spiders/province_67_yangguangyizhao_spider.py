# -*- coding: utf-8 -*-
"""
@file          :province_67_yangguangyizhao_spider.py
@description   :阳光易招公共资源交易平台
@date          :2021/05/31 10:21:05
@author        :miaokela
@version       :1.0
"""
import scrapy
import re
import requests
from lxml import etree
from datetime import datetime
import random

from spider_pro import items, constans, utils


class Province67YangguangyizhaoSpiderSpider(scrapy.Spider):
    name = 'province_67_yangguangyizhao_spider'
    allowed_domains = ['www.sunbidding.com']
    start_urls = ['http://www.sunbidding.com/']
    query_url = 'http://www.sunbidding.com'
    area_id = 67
    basic_area = '河南省-阳光易招公共资源交易平台'
    keywords_map = {
        '征求意见': '招标预告',
        '单一来源|询价': '招标公告',
        '资格审查': '资格预审结果公告',
        '澄清|变成|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '评标公示|候选人': '中标预告',
        '评审公示': '其他公告',
    }
    url_map = {
        '房建市政': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/jzbgg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jscqgg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jbggg/index.jhtml'},
            {'notice_type': '中标预告', 'url': 'http://www.sunbidding.com/jypbgs/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/jszbgg/index.jhtml'},
        ],
        '政府采购': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/zcggg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/zfcqgg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/zbggg/index.jhtml'},
            {'notice_type': '其他公告', 'url': 'http://www.sunbidding.com/zpsgs/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/zfzbgg/index.jhtml'},
        ],
        '企业采购': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/jqcgg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jqccq/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jqcbg/index.jhtml'},
            {'notice_type': '其他公告', 'url': 'http://www.sunbidding.com/jqcps/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/jqczb/index.jhtml'},
        ],
        '医疗卫生': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/yycggg/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/yybggg/index.jhtml'},
            {'notice_type': '其他公告', 'url': 'http://www.sunbidding.com/yypsgs/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/yyzbgg/index.jhtml'},
        ],
        '交通': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/jjtzb/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jjtbg/index.jhtml'},
            {'notice_type': '中标预告', 'url': 'http://www.sunbidding.com/jjtpb/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/jjtjg/index.jhtml'},
        ],
        '水利': [
            {'notice_type': '招标公告', 'url': 'http://www.sunbidding.com/jslzb/index.jhtml'},
            {'notice_type': '招标变更', 'url': 'http://www.sunbidding.com/jslbg/index.jhtml'},
            {'notice_type': '中标预告', 'url': 'http://www.sunbidding.com/jslpb/index.jhtml'},
            {'notice_type': '中标公告', 'url': 'http://www.sunbidding.com/jsljg/index.jhtml'},
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

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
        headers = Province67YangguangyizhaoSpiderSpider.get_headers(resp)
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

                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' %
                                           (time_sep, time_sep))

                        first_pub_time = t_com.findall(first_el)
                        final_pub_time = t_com.findall(final_el)

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = datetime.strptime(
                                first_pub_time[0], '%Y{0}%m{1}%d'.format(
                                    time_sep, time_sep)
                            )
                            final_pub_time = datetime.strptime(
                                final_pub_time[0], '%Y{0}%m{1}%d'.format(
                                    time_sep, time_sep)
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
        for category_type, urls_data in self.url_map.items():
            for url_data in urls_data:
                url = url_data['url']
                notice_type = url_data['notice_type']

                yield scrapy.Request(url=url, callback=self.get_max_page, meta={
                    'category_type': category_type,
                    'notice_type': notice_type
                }, cb_kwargs = {
                    'url': url,
                })

    def get_max_page(self, resp, url):
        """
        获取总页数
        """
        page_string = resp.xpath('//div[@class="TxtCenter"]/div/text()[1]').get().strip()
        max_page_com = re.compile('/(\d+)页')  # 共1169条记录 1/65页
        max_pages = max_page_com.findall(page_string)
        if max_pages:
            max_page = max_pages[0]
            try:
                max_page = int(max_page)
            except ValueError as e:
                self.log(e)
            else:
                for page in range(1, max_page + 1):
                    c_url = url.replace('index', 'index_{0}'.format(page)) if page > 1 else url

                    # 最末一条符合时间区间则翻页
                    # 解析详情页时再次根据区间判断去采集
                    judge_status = self.judge_in_interval(
                        c_url, method='GET', ancestor_el='div', ancestor_attr='class', ancestor_val='infolist-main',
                        child_el='em', resp=resp,
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                            'notice_type': resp.meta.get('notice_type', ''),
                            'category_type': resp.meta.get('category_type', '')
                        }, priority=max_page - page)
    
    def parse_list(self, resp):
        """
        获取详情页链接与发布时间
        """
        els = resp.xpath('//div[@class="infolist-main"]//a')
        for n, el in enumerate(els):
            href = el.xpath("./@href").get()
            if href:
                pub_time = el.xpath("./em/text()").get()
                url = ''.join([self.query_url, href])
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(url=url, callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'category_type': resp.meta.get('category_type'),
                        'pub_time': pub_time,
                    }, priority=(len(els)-n) * 100)

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="s_content"]').get()
        title_name = resp.xpath('//h2/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # _, content = utils.remove_specific_element(content, 'a', 'href', 'javascript:window.close()')

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
        notice_item["category"] = resp.meta.get('category_type')
        print(resp.meta.get('pub_time'), resp.url)

        return notice_item

if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute(
        "scrapy crawl province_67_yangguangyizhao_spider -a sdt=2021-01-01 -a edt=2021-05-17".split(" ")
    )
    # cmdline.execute("scrapy crawl province_67_yangguangyizhao_spider".split(" "))
