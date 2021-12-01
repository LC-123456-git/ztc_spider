# author: miaokela
# Date: 2021-04-20 10:11:20
# Description: 必联网
import scrapy
import copy
import re
from collections import OrderedDict

from spider_pro import items, constans, utils


class Province53BilianSpiderSpider(scrapy.Spider):
    name = 'province_53_bilian_spider'
    allowed_domains = ['ss.ebnew.com']
    start_urls = ['http://ss.ebnew.com/']
    area_id = 53
    query_url = 'https://ss.ebnew.com/tradingSearch/index.html'
    base_url = 'https://ss.ebnew.com'
    basic_area = '必联网'
    keywords_map = OrderedDict({
        '意向|需求': '招标预告',
        '变更|澄清|更正|补充': '招标变更',
        '废标|流标': '招标异常',
        '评标结果': '中标预告',
        '中标|结果': '中标公告',
    })
    url_map = {
        '招标预告': {
            'info_class_code': ['zbyg'],
            # 'keywords': ['意向', '需求'],
        },
        '招标公告': {
            'info_class_code': ['zbgg'],
            # 'keywords': ['招标', '谈判', '磋商'],
        },
        '招标变更': {
            'info_class_code': ['zbbggg'],
            # 'keywords': ['变更', '澄清', '更正', '补充'],
        },
        '招标异常': {
            'info_class_code': [],
            # 'keywords': ['废标', '流标'],
        },
        '中标预告': {
            'info_class_code': ['pbjggs'],
            # 'keywords': ['评标结果'],
        },
        '中标公告': {
            'info_class_code': ['zbjggg'],
            # 'keywords': ['中标', '结果'],
        }
    }
    form_data = {
        'infoClassCodes': '',
        'projectType': 'bid',
        'pubDateBegin': '',
        'pubDateEnd': '',
        'sortMethod': 'timeDesc',
        'key': '',
        'currentPage': '1'
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    @property
    def copy_form_data(self):
        return copy.deepcopy(self.form_data)

    def set_incr_time(self, form_data):
        """
        指定时间区间
        """
        if all([self.start_time, self.end_time]):
            form_data['pubDateBegin'] = self.start_time
            form_data['pubDateEnd'] = self.end_time
        return form_data

    def start_requests(self):
        for notice_type, code_or_keys in self.url_map.items():
            codes = code_or_keys['info_class_code']

            # 类别抓取
            for code in codes:
                form_data = self.copy_form_data
                form_data['infoClassCodes'] = code
                form_data = self.set_incr_time(form_data)
                yield scrapy.FormRequest(url=self.query_url, formdata=form_data, callback=self.parse_urls, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'form_data': form_data
                }, dont_filter=True)

    def parse_urls(self, resp, form_data):
        """
        获取页码后响应所有列表页
        """
        total_page = resp.xpath('//*[@id="pagerSubmitForm"]/a[last()-1]/text()').get()
        try:
            total_page = int(total_page)
        except Exception as e:
            total_page = 1
        # for p in range(1, 2):
        for p in range(1, total_page + 1):
            form_data['currentPage'] = '%d' % p
            yield scrapy.FormRequest(url=self.query_url, formdata=form_data, callback=self.parse_data_urls, meta={
                'notice_type': resp.meta.get('notice_type'),
            }, dont_filter=True)

    def parse_data_urls(self, resp):
        """
        获取所有详情页链接构造Request对象
        """
        els = resp.xpath('//div[@class="ebnew-content-list"]/div')
        pub_time_com = re.compile(r'(\d+-\d+-\d+)')

        # for el in els[0:2]:
        for el in els:
            pub_time_ori = el.xpath('.//i[position()=2]').get()
            pub_time = ''
            try:
                pub_time = pub_time_com.findall(pub_time_ori)[0]
            except Exception as e:
                self.log(e)
            detail_url = el.xpath('.//a/@href').get()

            # 获取地区
            area_els = el.xpath('./div[2]/div[2]/p[2]/span[2]/text()')
            area_name = area_els[0].get() if area_els else ''
            yield scrapy.Request(url=detail_url, callback=self.parse_item, meta={
                'notice_type': resp.meta.get('notice_type'),
                'pub_time': pub_time,
                'area_name': area_name,
            }, dont_filter=True, priority=10)

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
        content = resp.xpath('//div[contains(@class, "ebnew-details-content")]').get()
        # title 被省略 从内容页获取
        title_name = resp.xpath('//h2[@class="details-title"]/text()').get().strip()

        notice_type_ori = resp.meta.get('notice_type')

        # 关键词匹配 修改notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 内容防止转义字符
        content = utils.avoid_escape(content)

        # 去除发布时间
        _, content = utils.remove_specific_element(content, 'div', 'class', 'details-widget')

        # 去除解析字段position-relative
        _, content = utils.remove_specific_element(content, 'div', 'class', 'position-relative', index=2)

        # 去除标题
        _, content = utils.remove_specific_element(content, 'h2', 'class', 'details-title')

        # 投标文件
        _, files_path = utils.catch_files(content, self.base_url, resp=resp)

        area_name = resp.meta.get('area_name', '')
        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url
        notice_item["title_name"] = title_name
        notice_item["pub_time"] = resp.meta.get('pub_time')
        notice_item["info_source"] = '-'.join([area_name, self.basic_area]) if area_name else self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = ''
        print(resp.url, resp.meta.get('pub_time'))
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_53_bilian_spider -a sdt=2021-04-01 -a edt=2021-04-15".split(" "))
    cmdline.execute("scrapy crawl province_53_bilian_spider".split(" "))
