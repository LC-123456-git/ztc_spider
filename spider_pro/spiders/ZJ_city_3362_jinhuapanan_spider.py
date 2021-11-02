# -*- coding: utf-8 -*-
# @file           :ZJ_city_3362_jinhuapanan_spider.py
# @description    :浙江省金华市磐安县人民政府
# @date           :2021/08/03 08:45:58
# @author         :miaokela
# @version        :1.0
import copy
import re
from lxml import etree
import math

import scrapy

from spider_pro import utils, constans, items


class ZjCity3362JinhuapananSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3362_jinhuapanan_spider'
    allowed_domains = ['www.panan.gov.cn']
    start_urls = ['http://www.panan.gov.cn/']
    basic_area = '浙江省金华市磐安县人民政府'
    base_url = 'http://www.panan.gov.cn'
    query_url = 'http://www.panan.gov.cn/module/jpage/dataproxy.jsp?startrecord={startrecord}&endrecord={endrecord}&perpage=20'
    # http://www.panan.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=60&perpage=20
    # http://www.panan.gov.cn/module/jpage/dataproxy.jsp?startrecord=61&endrecord=120&perpage=20
    area_id = 3362
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '建设工程', 'columnid': '1229500305'},  # 招标公告、文件预公示
        ],
        '招标公告': [
            {'category': '政府采购', 'columnid': '1229170812'},  # 采购公告
            {'category': '建设工程', 'columnid': '1229170806'},  # 招标公告
            {'category': '土地交易', 'columnid': '1229170816'},  # 招标公告
            {'category': '产权交易', 'columnid': '1229170819'},  # 招标公告
            {'category': '乡镇分中心', 'columnid': '1229170822'},  # 招标公告
            {'category': '园区分中心', 'columnid': '1229321833'},  # 招标公告
        ],
        '招标变更': [
            {'category': '建设工程', 'columnid': '1229170807'},  # 更正（补充公告）
        ],
        '中标预告': [
            {'category': '建设工程', 'columnid': '1229170808'},  # 预中标公示
        ],
        '中标公告': [
            {'category': '建设工程', 'columnid': '1229170809'},  # 中标公示
            {'category': '政府采购', 'columnid': '1229170813'},  # 中标成交公告
            {'category': '土地交易', 'columnid': '1229170817'},  # 中标公示
            {'category': '产权交易', 'columnid': '1229170820'},  # 中标公示
            {'category': '乡镇分中心', 'columnid': '1229170823'},  # 中标公示
            {'category': '园区分中心', 'columnid': '1229321837'},  # 中标公示
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self._formdata = {
            'col': '1',
            'appid': '1',
            'webid': '3611',
            'path': '/',
            'columnid': '',
            'sourceContentType': '1',
            'unitid': '6166867',
            'webname': '磐安县人民政府',
            'permissiontype': '0',
        }

    @property
    def formdata(self):
        return copy.deepcopy(self._formdata)

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
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                c_url = self.query_url.format(**{
                    'startrecord': 1,
                    'endrecord': 60,
                })
                c_formdata = self.formdata
                c_formdata['columnid'] = cu['columnid']
                yield scrapy.FormRequest(
                    url=c_url, formdata=c_formdata, callback=self.turn_page, cb_kwargs={
                        'data': c_formdata,
                    }, meta={
                        'notice_type': notice_type,
                        'category': cu['category'],
                    }, dont_filter=True)

    def turn_page(self, resp, data):
        """
        翻页
        """
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)
        try:
            doc = etree.XML(resp.text)
            total_records = doc.xpath('//totalrecord/text()')
            total_record = int(total_records[0])  # 最后一页
            max_page = math.ceil(total_record / 60)
        except (Exception,) as e:
            self.logger.info('error:{}'.format(e))
        else:
            if all([self.start_time, self.end_time]):
                for i in range(max_page):
                    start_record = 1 + 60 * i
                    end_record = 60 * (i + 1) if not i + 1 == max_page else total_record
                    c_url = self.query_url.format(**{
                        'startrecord': start_record,
                        'endrecord': end_record,
                    })
                    judge_status = utils.judge_in_interval(
                        c_url, start_time=self.start_time, end_time=self.end_time, method='POST',
                        proxies=proxies, headers=headers, rule='//record/text()', data=data,
                        doc_type='xml'
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        yield scrapy.FormRequest(
                            url=c_url, formdata=data, callback=self.parse_url,
                            meta=resp.meta, dont_filter=True, priority=max_page - i
                        )
            else:
                for i in range(max_page):
                    start_record = 1 + 60 * i
                    end_record = 60 * (i + 1) if not i + 1 == max_page else total_record
                    c_url = self.query_url.format(**{
                        'startrecord': start_record,
                        'endrecord': end_record,
                    })

                    yield scrapy.FormRequest(
                        url=c_url, formdata=data, callback=self.parse_url,
                        meta=resp.meta, dont_filter=True, priority=max_page - i
                    )

    def parse_url(self, resp):
        try:
            doc = etree.XML(resp.text)
            records = doc.xpath('//record/text()')
        except (Exception,) as e:
            self.logger.info('error:{}'.format(e))
        else:
            """
            <![CDATA[<li style="font-size: 14px;"><span>2021-10-22</span>				 
            <a href="/art/2021/10/22/art_1229321837_59277057.html" target="_blank" title="磐安工业园区塑料产业园挡墙（一期）工程">磐安工业园区塑料产业园挡墙（一期）工程
            </a></li>]]>
            """
            pub_time_com = re.compile(r'<span>(\d{4}-\d{1,2}-\d{1,2})</span>')
            href_com = re.compile(r'href="(.*?)"')
            title_com = re.compile(r'title="(.*?)"')
            for n, record in enumerate(records):
                try:
                    pub_time = pub_time_com.findall(record)[0]
                    href = href_com.findall(record)[0]
                    title = title_com.findall(record)[0]
                except (Exception,) as e:
                    self.logger.info('error:{}'.format(e))
                else:
                    if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                        title = re.sub(r'【.*?】', '', title)
                        resp.meta.update(**{
                            'pub_time': pub_time,
                            'title': title
                        })
                        yield scrapy.Request(
                            url=''.join([self.base_url, href]), callback=self.parse_detail,
                            meta=resp.meta, priority=(len(records) - n) * 10 ** 6,
                        )

    def parse_detail(self, resp):
        title_name = resp.meta.get('title', '')
        content = resp.xpath('//div[@class="gm_tt3"]').get()
        if content:
            content = content.replace('<body>', '').replace('</body>', '')

        notice_type_ori = resp.meta.get('notice_type')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, resp=resp, pub_time=resp.meta.get('pub_time'))

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

    cmdline.execute("scrapy crawl ZJ_city_3362_jinhuapanan_spider -a sdt=2021-01-01 -a edt=2021-11-02".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3362_jinhuapanan_spider".split(" "))
