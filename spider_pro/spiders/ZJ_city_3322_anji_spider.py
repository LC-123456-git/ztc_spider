"""
@file          :ZJ_city_3322_anji_spider.py
@description   :安吉
@date          :2021/05/11 14:58:10
@author        :miaokela
@version       :1.0
"""
import re
import requests
from lxml import etree
from datetime import datetime
from math import ceil

import scrapy

from spider_pro import utils, constans, items


class ZjCity3322AnjiSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3322_anji_spider'
    allowed_domains = ['ggzy.anji.gov.cn']
    start_urls = ['http://ggzy.anji.gov.cn/']
    query_url = 'http://ggzy.anji.gov.cn'
    basic_area = '浙江省-湖州市-安吉县-安吉公共资源交易中心'
    area_id = 3322
    keywords_map = {
        '变更|答疑|澄清|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|预成交|中标公示|结果公示': '中标预告',
        '中标结果|成交|出让结果|交易结果': '中标公告',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }
    url_map = {
        '招标预告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001007/'},
        ],
        '招标公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001001/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011001/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005001/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007001/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008001/'},
            {'category': '其他项目', 'url': 'http://ggzy.anji.gov.cn/jyxx/003012/003012001/'},
        ],
        '招标变更': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001002/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005003/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007002/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008003/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005002/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011002/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008002/'},
        ],
        '招标异常': [],
        '中标预告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001005/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007004/'},
            {'category': '微型工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003011/003011003/'},
        ],
        '中标公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001006/'},
            {'category': '产权交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003005/003005004/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007005/'},
            {'category': '资源要素交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003008/003008004/'},
            {'category': '其他项目', 'url': 'http://ggzy.anji.gov.cn/jyxx/003012/003012002/'},
        ],
        '其他公告': [
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001008/'},
            {'category': '建设工程', 'url': 'http://ggzy.anji.gov.cn/jyxx/003001/003001004/'},
            {'category': '小额交易', 'url': 'http://ggzy.anji.gov.cn/jyxx/003007/003007003/'},
        ]
    }
    max_page_com = re.compile('\<script\>.*?\$\("#page"\).pagination.*?pageSize:\s*(.*?),.*?total:\s*(.*?),')

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

    def judge_in_interval(self, url, method='GET', ancestor_el='table', ancestor_attr='id', ancestor_val='',
                          child_el='tr', time_sep='-', doc_type='html', **kwargs):
        """
        判断最末一条数据是否在区间内
        Args:
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
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=self.headers).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'), headers=self.headers).text
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
                                first_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            final_pub_time = datetime.strptime(
                                final_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            start_time = datetime.strptime(
                                self.start_time, '%Y-%m-%d')
                            end_time = datetime.strptime(
                                self.end_time, '%Y-%m-%d')
                            # end_time < first_pub_time continue
                            # start_time > final_pub_time break
                            # else crawl and continue
                            # 0 break 2 continue 1 crawl and continue
                            if start_time > final_pub_time:
                                status = 0
                            elif end_time < first_pub_time:
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
                c_url = ''.join([cu['url'], 'moreinfo.html'])
                yield scrapy.Request(url=c_url, callback=self.parse_urls, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                }, cb_kwargs={
                    'url': cu['url'],
                })

    def parse_urls(self, resp, url):
        """
        js通过正则匹配最大页数
        """
        match_pages = self.max_page_com.findall(resp.text.replace('\t', '').replace('\n', '').replace('\r\n', ''))
        if match_pages:
            match_page = match_pages[0]

            page_size, total = match_page
            page_size = int(page_size)
            total = int(total)

            max_page = ceil(total / page_size)  # 最大页数

            c_url = ''.join([url, 'moreinfo.html'])
            for i in range(1, max_page + 1):
                # 最末一条符合时间区间则翻页
                # 解析详情页时再次根据区间判断去采集
                judge_status = self.judge_in_interval(
                    c_url, method='GET', ancestor_el='ul', ancestor_attr='class', ancestor_val='ewb-notice-items',
                    child_el='span'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    if i > 1:
                        c_url = ''.join([url, '{0}.html'.format(i)])
                    else:
                        c_url = ''.join([url, 'moreinfo.html'])
                    yield scrapy.Request(url=c_url,
                                            callback=self.parse_data_urls,
                                            meta={
                                                'notice_type': resp.meta.get('notice_type', ''),
                                                'category': resp.meta.get('category', '')
                                            }, priority=(max_page - i) * 10, dont_filter=True)
        else:
            # fetch first page
            yield scrapy.Request(url=url, callback=self.parse_data_urls, meta={
                'notice_type': resp.meta.get('notice_type', ''),
                'category': resp.meta.get('category', '')
            })

    def parse_data_urls(self, resp):
        """
        获取detail_url, pub_time
        """
        els = resp.xpath('//ul[@class="ewb-notice-items"]/li')
        for el in els:
            href = el.xpath(".//a/@href").get()
            if href:
                pub_time = el.xpath(".//span[last()]/text()").get()
                pub_time = pub_time.replace('.', '-') if pub_time else ''
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    yield scrapy.Request(url=self.query_url + href, callback=self.parse_item, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'category': resp.meta.get('category'),
                        'pub_time': pub_time,
                    }, priority=10000)

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="ewb-container"]').get()
        title_name = resp.xpath('//div[@class="detail-tt"]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 移除不必要信息: 删除第一个正文title/发布时间、打印关闭
        _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-info')
        _, content = utils.remove_specific_element(content, 'div', 'class', 'ewb-route')
        _, content = utils.remove_specific_element(content, 'div', 'class', 'detail-tt')

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

    cmdline.execute("scrapy crawl ZJ_city_3322_anji_spider -a sdt=2021-01-01 -a edt=2021-05-11".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3322_anji_spider".split(" "))
