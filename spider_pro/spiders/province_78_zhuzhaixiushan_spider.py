# -*- coding: utf-8 -*-
"""
@file          :province_78_zhuzhaixiushan_spider.py
@description   :上海市-住宅修缮工程招投标
@date          :2021/06/08 11:08:55
@author        :miaokela
@version       :1.0
"""
import scrapy
import re
import requests
import random
from urllib import parse
from datetime import datetime
from lxml import etree

from spider_pro import utils, items, constans


class Province78ZhuzhaixiushanSpiderSpider(scrapy.Spider):
    name = 'province_78_zhuzhaixiushan_spider'
    allowed_domains = ['xsjypt.fgj.sh.gov.cn']
    start_urls = ['http://xsjypt.fgj.sh.gov.cn/']
    basic_area = '上海市-住宅修缮工程招投标'
    area_id = 78
    query_url = 'http://xsjypt.fgj.sh.gov.cn'
    keywords_map = {
        '资格审核': '资格预审结果公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标公告': {
            'category_tag': 'ZBGG',
            'first_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!query.do?type=ZBGG',
            'extra_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!query.do?type={category_tag}&&businessId=&&biddingType=&&dateType=' + \
                         '&&pricingQuota=&&_packageCode%23projectCode_like=&&name=&&address=&&bidtype=&&_projectProperty=&PAGE={page}&PAGESIZE=12',
        },
        '招标变更': {
            'category_tag': 'INFORM',
            'first_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!informQuery.do?type=INFORM',
            'extra_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!informQuery.do?type={category_tag}&&businessId=&&biddingType=&&dateType=' + \
                         '&&pricingQuota=&&informType=&&_packageCode%23projectCode_like=&&name=&&_projectVestingAddress_like=&&bidtype=&&_projectProperty=&PAGE={page}&PAGESIZE=12',
        },
        '中标预告': {
            'category_tag': 'ZBHXRGS',
            'first_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!query.do?type=ZBHXRGS',
            'extra_url': 'http://xsjypt.fgj.sh.gov.cn/sh-tender-notice!query.do?type={category_tag}&&businessId=&&biddingType=&&dateType=' + \
                         '&&pricingQuota=&&_packageCode%23projectCode_like=&&name=&&address=&&bidtype=&&_projectProperty=&PAGE={page}&PAGESIZE=12',
        },
        '中标公告': {
            'category_tag': 'ZZXS',
            'first_url': 'http://xsjypt.fgj.sh.gov.cn/sh-bidder!show.do',
            'extra_url': 'http://xsjypt.fgj.sh.gov.cn/sh-bidder!show.do?_packageCode_notnull=true&_platformType={category_tag}&_auditStatus=PASSED&_packageId_notnull=true' + \
                         '&_bidState=1&ORDERBY=+submitDate+desc+&_projectVestingAddress_eq=&PAGE={page}&PAGESIZE=12',
        },
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
        headers = Province78ZhuzhaixiushanSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers).content.decode('utf-8')
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'), headers=headers).content.decode('utf-8')
                if text:
                    els = []
                    if doc_type == 'html':
                        doc = etree.HTML(text)

                        # enhance_els
                        # [{
                        #     'enhance_el': '',
                        #     'option': 'last()'
                        # }]
                        enhance_els = kwargs.get('enhance_els', [])

                        enhance_condition = ''
                        if enhance_els:
                            for ee in enhance_els:
                                enhance_el = ee.get('enhance_el', '')
                                option = ee.get('option', '')
                                option = '[{0}]'.format(option) if option else ''
                                enhance_condition += '//{0}{1}'.format(enhance_el, option)

                        # //div[@id="content"]//tbody//td[last()]/div[last()]//text()[not(normalize-space()="")]
                        _path = '//{ancestor_el}[normalize-space(@{ancestor_attr})="{ancestor_val}"]{enhance_condition}//{child_el}[position()=2]/text()[not(normalize-space()="")]'.format(
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
        for notice_type, urls in self.url_map.items():
            first_url = urls.get('first_url', '')
            extra_url = urls.get('extra_url', '')
            category_tag = urls.get('category_tag', '')

            yield scrapy.FormRequest(url=first_url, callback=self.turn_page, meta={
                'notice_type': notice_type,
                'extra_url': extra_url,
                'category_tag': category_tag,
            })

    def turn_page(self, resp):
        notice_type = resp.meta.get('notice_type', '')
        max_page_el = resp.xpath('//div[@class="page_manu r"]//a[last()]/@onclick').get()  # turnCostumerpage(3717)
        max_page_com = re.compile('(\d+)')
        max_page = max_page_com.findall(max_page_el)
        c_url = resp.url

        extra_url = resp.meta.get('extra_url', '')
        category_tag = resp.meta.get('category_tag', '')

        try:
            max_page = int(max_page[0])
        except Exception as e:
            self.log('error:{0}'.format(e))
        else:
            for page in range(1, max_page + 1):
                if page > 1:
                    c_url = extra_url.format(**{
                        'category_tag': category_tag,
                        'page': page,
                    })
                enhance_els = [
                    {'enhance_el': 'td', 'option': 'last()'},
                ] if notice_type != '招标变更' else [
                    {'enhance_el': 'tr', 'option': 'position()=1'},
                ]
                judge_status = self.judge_in_interval(
                    c_url, method='POST', ancestor_el='table', ancestor_attr='class', ancestor_val='tab_tb2',
                    child_el='div' if notice_type != '招标变更' else 'td', resp=resp, enhance_els=enhance_els,
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.FormRequest(url=c_url, callback=self.parse_list, meta={
                        'notice_type': notice_type,
                    }, priority=(max_page - page) * 100, dont_filter=True)

    def parse_list(self, resp):
        notice_type = resp.meta.get('notice_type', '')
        table_els = resp.xpath('//table')
        for n, table_el in enumerate(table_els):
            href = table_el.xpath('.//td[position()=1]//a/@href').get()
            title_name = table_el.xpath('.//td[position()=1]//a/text()').get()
            if href:
                pub_time_pre = table_el.xpath('.//td[position()=2]//div[position()=2]/text()').get()
                if notice_type == '招标变更':
                    pub_time_pre = table_el.xpath(
                        './/tr[position()=1]//td[last()]/text()[not(normalize-space()="")]').get()
                com = re.compile('(\d+-\d+-\d+)')
                pub_time = com.findall(pub_time_pre)
                pub_time = pub_time[0] if pub_time else ''

                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    c_url = ''.join([self.query_url, href])
                    yield scrapy.Request(url=c_url, callback=self.parse_detail, meta={
                        'notice_type': notice_type,
                        'pub_time': pub_time,
                        'title_name': title_name,
                    }, priority=(len(table_els) - n) * 100000)

    @staticmethod
    def parse_zz(content):
        """
        企业资质URL解码
        """
        msg = ''

        try:
            doc = etree.HTML(content)
            zz_els = doc.xpath('//div[@id="zizhi_div"]')
            if zz_els:
                zz_el = zz_els[0]
                html_code = parse.unquote(zz_el.text)
                p_zz_el = zz_el.getparent()
                p_zz_el.remove(zz_el)
                p_zz_el.insert(1, etree.HTML(html_code))

            # 移除class="none"的节点
            none_els = doc.xpath('//span[@class="none"]')
            for none_el in none_els:
                none_el.getparent().remove(none_el)

            content = etree.tounicode(doc, method='html')
        except Exception as e:
            msg = 'error:{0}'.format(e)

        return msg, content.replace('<html><body>', '').replace('</body></html>', '')

    def parse_detail(self, resp):
        title_name = resp.meta.get('title_name', '')
        title_trs = resp.xpath('//tr')
        content = resp.xpath('//form[@id="detailForm"]').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 提取内容页标题
        for title_tr in title_trs:
            check_text = title_tr.extract()
            com = re.compile('招标.*?名称')
            if check_text:
                if com.search(check_text):
                    if notice_type_ori == '招标公告':
                        title_name = title_tr.xpath('./td[position()=2]//text()').get()
                    if notice_type_ori in ['中标预告', '中标公告']:
                        title_name = title_tr.xpath('./td[position()=2]/*/text()').get()
                    title_name = title_name.strip() if title_name else ''
                    break

        if notice_type_ori == '中标预告':
            # 公开招标公告行|下载回标报告行 删除
            _, content = utils.remove_specific_element(
                content, 'table', 'class', 'table_s', if_child=True, child_attr='tr', text='下载回标报告'
            )
            _, content = utils.remove_specific_element(
                content, 'table', 'class', 'table_s', if_child=True, child_attr='tr', text='公开招标公告行'
            )

        if notice_type_ori == '招标变更':
            _, content = utils.remove_specific_element(
                content, 'form', 'id', 'detailForm', if_child=True, child_attr='a', text='点击下载补充招标文件'
            )
            _, content = utils.remove_specific_element(
                content, 'div', 'class', 'tex_center', index=2
            )
            content = content.replace('下载文件：', '')

            # ADD TITLE
            c_com = re.compile('招标.*?名称[:|：](.*?)\<')
            title_names = c_com.findall(content)
            if title_names:
                title_name = title_names[0].strip()
                title_name = title_name.strip() if title_name else ''
        
        if notice_type_ori == '招标公告':
            _, content = Province78ZhuzhaixiushanSpiderSpider.parse_zz(content)  # 企业资质
            # 报表信息
            _, content = utils.remove_specific_element(
                content, 'div', 'style', 'text-align:center;', index=0,
            )
            _, content = utils.remove_specific_element(
                content, 'div', 'style', 'text-align:center; position:relative', index=0,
            )

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
        notice_item.update(**{
            'origin': resp.url,
            'title_name': title_name,
            'pub_time': resp.meta.get('pub_time'),
            'info_source': self.basic_area,
            'is_have_file': constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE,
            'files_path': files_path,
            'notice_type': notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE,
            'content': content,
            'area_id': self.area_id,
            'business_category': '工程',
        })
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_78_zhuzhaixiushan_spider -a sdt=2021-01-01 -a edt=2021-06-08".split(" "))
    # cmdline.execute("scrapy crawl province_78_zhuzhaixiushan_spider".split(" "))
