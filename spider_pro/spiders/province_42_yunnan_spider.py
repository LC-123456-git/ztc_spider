# author: miaokela
# Date: 2021-04-14 16:24:06
# Description: 云南省公共资源中心
from lxml import etree
import scrapy
import re

from spider_pro import items, constans, utils


class Province42YunnanSpiderSpider(scrapy.Spider):
    name = 'province_42_yunnan_spider'
    allowed_domains = ['ggzy.yn.gov.cn']
    start_urls = ['http://ggzy.yn.gov.cn/']
    query_url = 'http://ggzy.yn.gov.cn'
    keywords_map = {
        '终止|中止|流标|废标|异常': '招标变更',
        '资格预审': '资格预审结果公告',
        '候选人': '中标预告',
    }
    url_map = {
        '招标公告': {
            'url': [
                'http://ggzy.yn.gov.cn/jyxx/jsgcZbgg?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/zfcg/cggg?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/tdsyq/cjqr?area=000',
                'http://ggzy.yn.gov.cn/jyxx/kyqcr/zpgCrgg?area=000',
                'http://ggzy.yn.gov.cn/jyxx/cqjy/crgg?area=000',
            ],
            'keywords': [],
        },
        '资格预审结果公告': {
            'url': [],
        },
        '招标变更': {
            'url': [
                'http://ggzy.yn.gov.cn/jyxx/jsgcBgtz?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/zfcg/gzsx?area=000&secondArea=',
            ],
        },
        '中标预告': {
            'url': ['http://ggzy.yn.gov.cn/jyxx/jsgcpbjggs?area=000&secondArea='],
        },
        '中标公告': {
            'url': [
                'http://ggzy.yn.gov.cn/jyxx/jsgcZbjggs?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/zfcg/zbjggs?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/tdsyq/crgg?area=000',
                'http://ggzy.yn.gov.cn/jyxx/kyqcr/zpgCrjggs?area=000',
            ],
            'keywords': [],
        },
        '其他公告': {
            'url': [
                'http://ggzy.yn.gov.cn/jyxx/zfcg/htgs?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/kyqcr/qtCrgsxx?area=000'
            ],
            'keywords': [],
        }
    }
    area_id = 42
    basic_area = '云南省公共资源中心'

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    def start_requests(self):
        """
        url
            pages node
            params: currentPage
        keywords
        """
        for notice_type, url_or_keys in self.url_map.items():
            urls = url_or_keys['url']
            # 链接抓取
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse_urls, meta={
                    'notice_type': notice_type
                })

    def parse_urls(self, resp):
        """
        get max pages
        """
        total_page = resp.xpath('//input[@name="totalPage"]/@value').get()
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)
        try:
            total_page = int(total_page)
        except ValueError as e:
            total_page = 1
            self.log(e)

        if all([self.start_time, self.end_time]):
            for p in range(1, total_page + 1):
                judge_status = utils.judge_in_interval(
                    resp.url, start_time=self.start_time, end_time=self.end_time, method='POST',
                    data={'currentPage': str(p)}, proxies=proxies, headers=headers,
                    rule='//table[@id="data_tab"]/tbody/tr[position()>1]/td[4]/text()'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.FormRequest(
                        url=resp.url, formdata={'currentPage': str(p)}, callback=self.parse_data_urls, meta={
                            'notice_type': resp.meta.get('notice_type')
                        }, dont_filter=True, priority=total_page - p)
        else:
            for p in range(1, total_page + 1):
                yield scrapy.FormRequest(
                    url=resp.url, formdata={'currentPage': str(p)}, callback=self.parse_data_urls, meta={
                        'notice_type': resp.meta.get('notice_type')
                    }, dont_filter=True, priority=total_page - p)

    def parse_data_urls(self, resp):
        els = resp.xpath('//table[@id="data_tab"]/tbody/tr[position()>1]')
        title_com = re.compile(r'\[(.*?)\](.*)')

        for n, el in enumerate(els):
            detail_url = el.xpath('.//a/@href').get()
            pub_time = el.xpath('./td[4]/text()').get().strip()

            art_title_ori = el.xpath('./td[3]/a/text()').get()
            art_title = re.sub(r'\s|\t|\n', '', art_title_ori if art_title_ori else '')

            # 处理pub_time，判断在start_time与end_time区间内
            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                art_titles = title_com.findall(art_title)
                title_split = art_titles[0] if art_titles else [art_title]

                if len(title_split) == 2:
                    sub_area, _ = title_split
                    info_source = self.basic_area + '-' + sub_area
                elif len(title_split) == 1:
                    info_source = self.basic_area
                else:
                    info_source = self.basic_area

                yield scrapy.Request(url=self.query_url + detail_url, callback=self.parse_item, meta={
                    'notice_type': resp.meta.get('notice_type'),
                    'pub_time': pub_time,
                    'info_source': info_source.strip(),
                }, dont_filter=True, priority=10000 * (len(els) - n))

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
        content = resp.xpath('//div[@class="detail_contect"]').get()
        title_name = resp.xpath('//h3[@class="detail_t"]/text()').get()
        pub_time = resp.meta.get('pub_time')
        # 去除温馨提示
        _, content = utils.remove_specific_element(content, 'div', 'class', 'receipt_box')
        # 投标文件
        _, files_path = utils.catch_files(content, self.query_url, pub_time=pub_time, resp=resp)

        category = resp.xpath('/html/body/div[4]/div/a[3]/text()').get()
        notice_type_ori = resp.meta.get('notice_type')

        # 关键词匹配 修改notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url
        notice_item["title_name"] = title_name
        notice_item["pub_time"] = pub_time

        notice_item["info_source"] = resp.meta.get('info_source')
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = category

        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_42_yunnan_spider -a sdt=2021-08-10 -a edt=2021-08-29".split(" "))
    cmdline.execute("scrapy crawl province_42_yunnan_spider".split(" "))
