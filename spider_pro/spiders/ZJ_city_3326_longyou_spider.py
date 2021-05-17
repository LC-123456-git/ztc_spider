# -*- coding: utf-8 -*-
import re
import requests
import scrapy
import copy
import json
from datetime import datetime
from scrapy.utils.project import get_project_settings

from spider_pro import items, constans, utils


class ZjCity3326LongyouSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3326_longyou_spider'
    allowed_domains = ['ztb.longyou.gov.cn']
    start_urls = ['http://http://ztb.longyou.gov.cn/']
    query_url = 'http://ztb.longyou.gov.cn'
    basic_area = '浙江省-衢州市-龙游县-龙游县公共资源交易平台'
    area_id = 3326
    keywords_map = {
        '澄清|变更|补充': '招标变更',
        '废标|流标|终止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001009'},
        ],
        '招标公告': [
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001002'},
            {'category': '政府采购', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005002002'},
            {'category': '土地交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005003001'},
            {'category': '产权交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005004001'},
            {'category': '乡镇(部门)交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005007001'},
            {'category': '农村产权', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005008001001'},
        ],
        '中标预告': [
            {'category': '乡镇(部门)交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005007005'},
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001003'},
        ],
        '中标公告': [
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001004'},
            {'category': '产权交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005004002'},
            {'category': '乡镇(部门)交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005007004'},
            {'category': '农村产权', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005008002001'},
        ],
        '其他公告': [
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001008'},
            {'category': '政府采购', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005002005'},
            {'category': '乡镇(部门)交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005007003'},
        ]
    }
    payload = {
        "filter": {
            "date": "",
            "regionCode": "",
            "tenderProjectType": ""
        },
        "page": 1,
        "rows": 10,
        "searchKey": ""
    }
    settings = get_project_settings()

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self.headers = self.settings.get('DEFAULT_REQUEST_HEADERS', '')

    @property
    def _payload(self):
        return copy.deepcopy(self.payload)

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

    def is_in_interval(self, url, method='GET', time_sep="-", **kwargs):
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
                    ret = json.loads(text)

                    rows = ret.get('rows', [])

                    if rows:
                        # 首个时间 末尾时间
                        first_pub_time = rows[0].get('publishTime', '')
                        final_pub_time = rows[-1].get('publishTime', '')

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = datetime.strptime(first_pub_time,
                                                               '%Y{0}%m{1}%d %H:%M:%S'.format(time_sep, time_sep))
                            final_pub_time = datetime.strptime(final_pub_time,
                                                               '%Y{0}%m{1}%d %H:%M:%S'.format(time_sep, time_sep))
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
                self.log('error:{0}'.format(e))
        else:
            status = 1  # 没有传递时间
        return status

    def start_requests(self):
        self.headers['Content-Type'] = 'application/json'
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                yield scrapy.Request(
                    url=cu['url'], method='POST', body=json.dumps(self._payload), callback=self.get_max_page,
                    meta={'notice_type': notice_type, 'category': cu['category']}, cb_kwargs={'url': cu['url']},
                    headers=self.headers,
                )

    def get_max_page(self, resp, url):
        """
        {
            "pageIndex":3,
            "pageSize":10,
            "rows":[
                {
                "areaCode":"330825","areaName":"龙游县","bidSectionCodes":"HZGS2021-001 001","canBid":false,"categoryCode":"703",
                "categoryName":"开标信息","comeFrom":"龙游县公共资源交易平台","createTime":"2021-04-29 16:10:01","createUser":"system",
                "date":0,"delFlag":false,"distanceOpenBidTime":0,"id":"64777879999547d78cc0103f8d606669","isnew":false,
                "needAudit":false,"parentCode":"TRADE_CODE_QTJY","platformCode":"78bb4cf1f2d74b38b0e980861c69b298",
                "publish":true,"publishTime":"2021-04-29 16:10:00","showTop":false,"tenderBulletinCode":"1619683799470001",
                "tenderProjectCode":"A3308250980001991001","title":"柳园小学珍贵树种提升工程增加项目","tradeType":"7",
                "updateTime":"2021-04-29 16:10:01","updateUser":"system"
                },...
            ],
            "total":429,
            "totalItemCount":429,
            "totalPageCount":43
        }
        Returns:

        """
        ret = json.loads(resp.text)

        max_pages = ret.get('totalPageCount', 0)
        for page in range(1, max_pages + 1):
            data = self._payload
            data['page'] = page
            # 请求当前页 判断时间区间
            judge_status = self.is_in_interval(url, method='POST', data=json.dumps(data))

            if judge_status == 0:
                break
            elif judge_status == 2:
                continue
            else:
                yield scrapy.Request(url=url, method='POST', body=json.dumps(data), callback=self.parse_list, meta={
                    'notice_type': resp.meta.get('notice_type', ''),
                    'category': resp.meta.get('category', ''),
                }, cb_kwargs={'url': url}, headers=self.headers, priority=max_pages + 1 - page)

    def parse_list(self, resp, url):
        ret = json.loads(resp.text)

        rows = ret.get('rows', [])

        for n, row in enumerate(rows):
            pub_time = row.get('publishTime', '')
            detail_id = row.get('id', '')

            if pub_time:
                c_pub_time = '{0:%Y-%m-%d}'.format(datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S'))

                if utils.check_range_time(self.start_time, self.end_time, c_pub_time)[0]:
                    yield scrapy.Request(url='/'.join([url, detail_id]), method='POST', callback=self.parse_detail,
                                         meta={
                                             'notice_type': resp.meta.get('notice_type', ''),
                                             'category': resp.meta.get('category', ''),
                                             'pub_time': pub_time,
                                         }, priority=(len(rows) + 1 - n) * 10)

    @staticmethod
    def check_has_body(content):
        com = re.compile('<body[^>]*>([\s\S]*)<\/body>')
        ret = com.findall(content)

        return ret[0] if ret else content

    def parse_detail(self, resp):
        ret = json.loads(resp.text)

        data = ret.get('data', {})
        if data:
            content = data.get('content', '').replace('\r\n', '').replace('\t', '')
            content = ZjCity3326LongyouSpiderSpider.check_has_body(content)

            title_name = data.get('title')
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
                'category': resp.meta.get('category'),
            })
            print(resp.meta.get('pub_time'), resp.url)
            return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl ZJ_city_3326_longyou_spider -a sdt=2021-01-01 -a edt=2021-05-17".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3326_longyou_spider".split(" "))
