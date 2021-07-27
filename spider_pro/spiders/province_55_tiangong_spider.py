"""
author: miaokela
Date: 2021-04-25 13:10:47
LastEditTime: 2021-04-25 13:13:44
Description: 天工招采平台
"""
import scrapy
import re
import requests
from datetime import datetime
from lxml import etree
from spider_pro import utils, constans, items


class Province55TiangongSpiderSpider(scrapy.Spider):
    name = 'province_55_tiangong_spider'
    allowed_domains = ['zhaobiao.tgcw.net.cn']
    start_urls = ['http://zhaobiao.tgcw.net.cn/']
    query_url = 'http://zhaobiao.tgcw.net.cn'
    basic_area = '天工开物'
    area_id = 55
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }
    url_map = {
        '招标公告': ['http://zhaobiao.tgcw.net.cn/cms/channel/xmgg/index.htm'],
        '中标预告': ['http://zhaobiao.tgcw.net.cn/cms/channel/bidzbgs/index.htm'],
        '中标公告': ['http://zhaobiao.tgcw.net.cn/cms/channel/bidzbgg/index.htm'],
    }
    keywords_map = {
        '变更': '招标变更',
        '候选人': '中标预告',
        '中标': '中标公告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    def start_requests(self):
        for notice_type, urls in self.url_map.items():
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse_urls, cb_kwargs={
                    'url': url,
                }, meta={
                    'notice_type': notice_type,
                })

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
            **kwargs: POST请求体
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
                    text = requests.post(url=url, data=kwargs.get('data'), headers=self.headers).text
                if text:
                    els = []
                    if doc_type == 'html':
                        doc = etree.HTML(text)
                        _path = '//{ancestor_el}[@{ancestor_attr}="{ancestor_val}"]//{child_el}[last()]/text()[not(normalize-space()="")]'.format(
                            **{
                                'ancestor_el': ancestor_el,
                                'ancestor_attr': ancestor_attr,
                                'ancestor_val': ancestor_val,
                                'child_el': child_el,
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
                            first_pub_time = datetime.strptime(first_pub_time[0],
                                                               '%Y{0}%m{1}%d'.format(time_sep, time_sep))
                            final_pub_time = datetime.strptime(final_pub_time[0],
                                                               '%Y{0}%m{1}%d'.format(time_sep, time_sep))
                            start_time = datetime.strptime(self.start_time, '%Y-%m-%d')
                            end_time = datetime.strptime(self.end_time, '%Y-%m-%d')
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

    def parse_urls(self, resp, url):
        max_page = resp.xpath('//div[@class="pag-link"]/a[last()-2]/text()').get()
        try:
            max_page = int(max_page)
        except ValueError as e:
            self.log(e)
        else:
            for i in range(1, max_page + 1):
                # 最末一条符合时间区间则翻页
                # 解析详情页时再次根据区间判断去采集
                judge_status = self.judge_in_interval(
                    url, method='GET', ancestor_el='div', ancestor_attr='class', ancestor_val='lb-link', child_el='span'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(url='{url}?pageNo={page}'.format(**{
                        'url': url,
                        'page': i,
                    }), callback=self.parse_data_urls, meta={
                        'notice_type': resp.meta.get('notice_type', '')
                    }, priority=(max_page - i) * 10)

    def parse_data_urls(self, resp):
        """
        获取detail_url, pub_time
        """
        els = resp.xpath('//div[@class="lb-link"]/ul/li')
        for el in els:
            href = el.xpath(".//a/@href").get()
            pub_time = el.xpath(".//a/span[last()]/text()").get()

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                yield scrapy.Request(url=self.query_url + href, callback=self.parse_item, meta={
                    'notice_type': resp.meta.get('notice_type'),
                    'pub_time': pub_time,
                }, priority=1000)

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

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="ninfo-con"]').get()
        title_name = resp.xpath('//div[@class="ninfo-title"]/h2/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 移除不必要信息: 发布时间、上下页
        _, content = utils.remove_specific_element(content, 'div', 'class', 'ninfo-title', if_child=True,
                                                   child_attr='span')
        _, content = utils.remove_specific_element(content, 'div', 'class', 'ip-link')

        content = utils.avoid_escape(content)  # 防止转义

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name
        notice_item["pub_time"] = resp.meta.get('pub_time')

        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = ''
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_55_tiangong_spider -a sdt=2021-03-01 -a edt=2021-03-31".split(" "))
    cmdline.execute("scrapy crawl province_55_tiangong_spider".split(" "))
