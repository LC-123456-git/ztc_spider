# author: miaokela
# Date: 2021-04-14 16:24:06
# Description: 云南
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
            # 'keywords': ['资格预审'],
        },
        '招标变更': {
            'url': [
                'http://ggzy.yn.gov.cn/jyxx/jsgcBgtz?area=000&secondArea=',
                'http://ggzy.yn.gov.cn/jyxx/zfcg/gzsx?area=000&secondArea=',
            ],
            # 'keywords': ['中止', '终止', '异常', '废标', '流标'],
        },
        '中标预告': {
            'url': ['http://ggzy.yn.gov.cn/jyxx/jsgcpbjggs?area=000&secondArea='],
            # 'keywords': ['候选人'],
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
    basic_area = '云南'

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

    def parse_urls(self, response):
        """
        get max pages
        """
        total_page = response.xpath('//input[@name="totalPage"]/@value').get()
        try:
            total_page = int(total_page)
        except ValueError as e:
            total_page = 1
            self.log(e)

        for p in range(1, 2):
            # for p in range(1, total_page + 1):
            yield scrapy.FormRequest(url=response.url, formdata={'currentPage': str(p)}, callback=self.parse_data_urls,
                                     meta={
                                         'notice_type': response.meta.get('notice_type')
                                     })

    def parse_data_urls(self, response):
        # find pub_time index
        pub_time_positions = response.xpath('//*[@id="data_tab"]/tbody/tr[position()=1]/th')
        pub_time_index = 1
        title_index = 1
        for n, pub_time_position in enumerate(pub_time_positions):
            title = pub_time_position.xpath('./text()').get()
            if title == '发布时间':
                pub_time_index = n + 1
                break
        for n, pub_time_position in enumerate(pub_time_positions):
            title = pub_time_position.xpath('./text()').get()
            if title in ['公告标题', '变更标题', '公告名称', '采购项目名称', '公示标题', '项目名称', '矿山/项目名称']:
                title_index = n + 1
                break
        els = response.xpath('//*[@id="data_tab"]/tbody/tr[position()>1]')
        title_com = re.compile('\[(.*?)\](.*)')

        for el in els:
            detail_url = el.xpath('.//a/@href').get()
            pub_time = el.xpath('./td[position()={0}]/text()'.format(pub_time_index)).get().strip()

            try:
                pub_time = int(pub_time)
            except ValueError:
                self.log(pub_time_index)

            art_title_ori = el.xpath('./td[position()={0}]/a/text()'.format(title_index)).get()

            art_title = re.sub('\s|\t|\n', '', art_title_ori if art_title_ori else '')

            # 处理pub_time，判断在start_time与end_time区间内
            if utils.check_range_time(self.start_time, self.end_time, pub_time):
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
                    'notice_type': response.meta.get('notice_type'),
                    'pub_time': pub_time,
                    'info_source': info_source.strip(),
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

    def parse_item(self, response):
        content = response.xpath('//div[contains(@class, "page_contect")]').get()
        # title_name包含省略号 需要从文章获取
        title_name = response.xpath('//h3[@class="detail_t"]/text()').get()

        # 内容防止转义字符
        content = utils.avoid_escape(content)
        # 去除温馨提示
        _, content = utils.remove_specific_element(content, 'div', 'class', 'receipt_box')
        # 投标文件
        _, files_path = utils.catch_files(content, self.query_url)

        category = response.xpath('/html/body/div[4]/div/a[3]/text()').get()
        notice_type_ori = response.meta.get('notice_type')

        # title_name = response.meta.get('title_name')
        # 关键词匹配 修改notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        notice_item = items.NoticesItem()
        notice_item["origin"] = response.url
        notice_item["title_name"] = title_name
        notice_item["pub_time"] = response.meta.get('pub_time')

        notice_item["info_source"] = response.meta.get('info_source')
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = category

        print('yield to pipeline')
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_42_yunnan_spider -a sdt=2021-04-10 -a edt=2021-04-14".split(" "))
    cmdline.execute("scrapy crawl province_42_yunnan_spider".split(" "))
