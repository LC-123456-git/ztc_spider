# author: miaokela
# Date: 2021-04-19 10:04:42
# Description: 品茗网
import scrapy
import re
import requests
from lxml import etree
from datetime import datetime

from spider_pro import items, constans, utils


class Province52PinmingSpiderSpider(scrapy.Spider):
    name = 'province_52_pinming_spider'
    allowed_domains = ['www.hibidding.com']
    start_urls = ['http://www.hibidding.com/']
    query_url = 'http://www.hibidding.com'
    area_id = 52
    basic_area = '浙江-嘉兴市-嗨招电子招标采购平台'
    keywords_map = {
        '变更': '招标变更',
        '废标|流标': '招标异常',
        '候选人': '中标预告',
        '中标': '中标公告',
    }
    url_map = {
        '招标公告': {
            'url': [
                'https://www.hibidding.com/BidNotice/zbcgxx/zbgg',
            ],
        },
        '招标变更': {
            'url': [
                'https://www.hibidding.com/BidNotice/zbcgxx/bggg'
            ],
        },
        '招标异常': {
            'url': [],
        },
        '中标预告': {
            'url': [],
        },
        '中标公告': {
            'url': ['https://www.hibidding.com/BidNotice/zbcgxx/zbgs'],
        }
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }

    # keywords_search_url = 'https://www.hibidding.com/Search/Index?searchKey={keyword}'

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    def start_requests(self):
        for notice_type, url_or_keys in self.url_map.items():
            urls = url_or_keys['url']
            for url in urls:
                yield scrapy.Request(url=url, cb_kwargs={
                    "if_search": False,
                }, callback=self.parse_urls, meta={
                    'notice_type': notice_type
                })

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
                          child_el='tr', time_sep='-', **kwargs):
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
            **kwargs: POST请求体
        Returns:
            status: 结果状态
                1 末条在区间内 可以翻页
                0 末条不在区间内 停止翻页
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
                    doc = etree.HTML(text)
                    _path = '//{ancestor_el}[@{ancestor_attr}="{ancestor_val}"]//{child_el}[last()]/text()'.format(**{
                        'ancestor_el': ancestor_el,
                        'ancestor_attr': ancestor_attr,
                        'ancestor_val': ancestor_val,
                        'child_el': child_el,
                    })
                    els = doc.xpath(_path)
                    if els:
                        el = els[-1]
                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' % (time_sep, time_sep))
                        pub_time = t_com.findall(el)
                        if pub_time:
                            pub_time = datetime.strptime(pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep))
                            start_time = datetime.strptime(self.start_time, '%Y-%m-%d')
                            end_time = datetime.strptime(self.end_time, '%Y-%m-%d')
                            # 比最大时间大 continue
                            # 比最小时间小 break
                            if pub_time > end_time:  # 翻页不抓
                                status = 2
                            elif pub_time < start_time:  # 停止翻页
                                status = 0
                            else:
                                status = 1
            except Exception as e:
                self.log(e)
        else:
            status = 1  # 没有传递时间
        return status

    def parse_urls(self, resp, if_search):
        """
        获取页码后响应所有列表页
        """
        suffix_href = resp.xpath('//*[@id="bootstrappager"]/li[last()]/a/@href').get()
        max_page_com = re.compile('pageIndex=(\d+)')
        total_page = 1
        try:
            total_page = int(max_page_com.findall(suffix_href)[0])
        except (ValueError, IndexError, TypeError) as e:
            pass

        if if_search:
            tag = '&'
        else:
            tag = '?'

        # for p in range(1, 2):
        for p in range(1, total_page + 1):
            # 最末一条符合时间区间则翻页
            # 解析详情页时再次根据区间判断去采集
            judge_status = self.judge_in_interval(resp.url + '{tag}pageIndex={pageIndex}'.format(
                **{'tag': tag, 'pageIndex': p}
            ), method='GET', ancestor_el='ul', ancestor_attr='class', ancestor_val='list-news', child_el='dt',
                                                  time_sep='/')
            if judge_status == 0:
                break
            elif judge_status == 2:
                continue
            else:
                yield scrapy.Request(url=resp.url + '{tag}pageIndex={pageIndex}'.format(**{'tag': tag, 'pageIndex': p}),
                                     callback=self.parse_data_urls, meta={
                        'notice_type': resp.meta.get('notice_type')
                    })

    def parse_data_urls(self, response):
        """
        获取所有详情页链接构造Request对象
        """
        els = response.xpath('//ul[@class="list-news"]/li')
        pub_time_com = re.compile(r'(\d+/\d+/\d+)')

        # for el in els[0:2]:
        for el in els:
            dt_info = el.xpath('.//a/dl/dt').get()

            pub_time = ''
            try:
                pub_time = pub_time_com.findall(dt_info)[0]
            except Exception as e:
                self.log(e)
            pub_time = utils.get_accurate_pub_time(pub_time)
            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                detail_url = el.xpath('.//a/@href').get()
                yield scrapy.Request(url=self.query_url + detail_url, callback=self.parse_item, meta={
                    'notice_type': response.meta.get('notice_type'),
                    'pub_time': pub_time,
                }, priority=10)

    def parse_item(self, resp):
        content = resp.xpath('//div[@class="content-right"]').get()
        # title 被省略 从内容页获取
        title_name = resp.xpath('//div[@class="content-title"]/text()[not(normalize-space()="")]').get().strip()

        notice_type_ori = resp.meta.get('notice_type')

        # 关键词匹配 修改notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 内容防止转义字符
        content = utils.avoid_escape(content)

        # 移除信息时间
        _, content = utils.remove_specific_element(content, 'div', 'class', 'content-title', if_child=True,
                                                   child_attr='span')

        # 投标文件
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

    cmdline.execute("scrapy crawl province_52_pinming_spider -a sdt=2021-03-01 -a edt=2021-03-31".split(" "))
    # cmdline.execute("scrapy crawl province_52_pinming_spider".split(" "))
