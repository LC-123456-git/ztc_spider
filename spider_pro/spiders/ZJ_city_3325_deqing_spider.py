# -*- coding: utf-8 -*-
import re
import requests
import scrapy
import copy
import json
import random
from datetime import datetime
from lxml import etree

from spider_pro import items, constans, utils


class ZjCity3325DeqingSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_deqing_spider'
    allowed_domains = ['116.62.168.209']
    start_urls = ['http://116.62.168.209/']
    query_url = 'http://116.62.168.209'
    basic_area = '浙江省-湖州市-德清县-德清县公共资源交易平台'
    area_id = 3325
    keywords_map = {
        '变更|答疑|澄清|补充|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|预成交': '中标预告',
        '中标|成交': '中标公告',
        '预公示': '招标预告',
    }
    url_map = {
        '招标公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbgg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/cggg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/zfcgzxuj/index.htm'},
            {'category': '土地交易', 'url': 'http://116.62.168.209/churgg/index.htm'},
            {'category': '产权交易', 'url': 'http://116.62.168.209/chuanrgg/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nczrgg/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/ynjygg/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwjygg/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqzbgg/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fzfcgzbgg/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmzzgg/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjyjygg/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fsqjyjygg/index.htm'},
        ],
        '资格预审公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zsgs/index.htm'},
        ],
        '招标变更': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/dy/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/yndycq/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwdycq/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqdybc/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fzfcgdybc/index.htm'},
            {'category': '镇街道限额以下', 'url': 'http://116.62.168.209/xzdybc/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmdybc/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjyjggs/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fsqjyjggs/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmdybc/index.htm'},
        ],
        '招标异常': [
            # {'category': '工程交易', 'url': 'http://116.62.168.209/dy/index.htm'},
        ],
        '中标预告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbhxrgs/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqpbjjgs/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fcfcgpbjggs/index.htm'},
            {'category': '镇街道限额以下', 'url': 'http://116.62.168.209/xzpbjggg/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmpbjggg/index.htm'},
        ],
        '中标公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbjggg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/zzbgs/index.htm'},
            {'category': '土地交易', 'url': 'http://116.62.168.209/chengjgs/index.htm'},
            {'category': '产权交易', 'url': 'http://116.62.168.209/cqcjgs/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nccjgs/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/yncjgg/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwcjgg/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjybggg/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nccjgs/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fsqjybggg/index.htm'},
        ],
        '其他公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zgxj/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/yjzq/index.htm'},
        ]
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
        headers = ZjCity3325DeqingSpiderSpider.get_headers(resp)
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
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                yield scrapy.Request(url=cu['url'], callback=self.get_max_page, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                }, cb_kwargs={
                    'url': cu['url'],
                })

    def get_max_page(self, resp, url):
        max_page_str = resp.xpath('//div[@class="pgPanel clearfix"]/div/text()[not(normalize-space()="")]').get()
        max_page_com = re.compile('共\d+条')

        max_pages = max_page_com.findall(max_page_str)

        try:
            max_page = int(max_pages[0])
        except Exception as e:
            self.log('error:{0}'.format(e))
        else:
            for i in range(max_page):
                page = i + 1

                if page > 1:
                    url = url.replace('index.htm', 'index%d.htm' % page)

                yield scrapy.Request(url=url, callback=self.parse_list, meta={
                    'notice_type': resp.get('notice_type', ''),
                    'category': resp.get('category', ''),
                }, priority=5 * (max_page - i))

    def parse_list(self, resp):
        detail_els = resp.xpath('//div[@class="ListNews FloatL hidden"]/ul/li')
        for n, d_el in enumerate(detail_els):
            pub_time = d_el.xpath('./span').get()
            c_href = d_el.xpath('./a/@href').get()
            
            yield scrapy.Request(url=''.join([self.query_url, c_href]), callback=self.parse_detail, meta={
                'notice_type': resp.get('notice_type', ''),
                'category': resp.get('category', ''),
                'pub_time': pub_time,
            }, priority=10 * (len(detail_els) - n))

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="Content_Border hidden"]').get()
        title_name = resp.xpath('//div[@class="Content_Border hidden"]/div[2]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 移除不必要信息: 删除面包屑导航, 发布时间
        _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-info')
        _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-info')

        # 删除表单
        _, content = utils.remove_specific_element(content, 'div', 'class', 'clearfix hidden', index=0)
        _, content = utils.remove_specific_element(content, 'input', 'id', 'souceinfoid')

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

    cmdline.execute("scrapy crawl ZJ_city_3325_deqing_spider -a sdt=2021-01-01 -a edt=2021-05-17".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3325_deqing_spider".split(" "))