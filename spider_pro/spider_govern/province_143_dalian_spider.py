# -*- coding: utf-8 -*-
# @file           :province_143_dalian_spider.py
# @description    :大连政府采集网
# @date           :2021/10/18 09:57:50
# @author         :miaokela
# @version        :1.0
import requests
import scrapy
import re
from lxml import etree

from spider_pro import constans, utils, items


class Province143DalianSpiderSpider(scrapy.Spider):
    name = 'province_143_dalian_spider'
    allowed_domains = ['ccgp-dalian.gov.cn']
    start_urls = ['http://ccgp-dalian.gov.cn/']

    basic_area = '辽宁省-大连政府采集网'
    area_id = 143
    query_url = 'http://ccgp-dalian.gov.cn'
    url_map = {
        '招标预告': [
            {  # 采购意向公开
                'url': 'http://www.ccgp-dalian.gov.cn/dlweb/showinfo/bxmoreinfo.aspx?CategoryNum=003006001',
                '__EVENTTARGET': 'MoreInfoList$Pager',
                'table_attr': 'MoreInfoList_DataGrid1',
                'page_attr': 'MoreInfoList_Pager',
            },
        ],
        '招标公告': [
            {  # 单一来源公示
                'url': 'http://www.ccgp-dalian.gov.cn/dlweb/showinfo/bxmoreinfo.aspx?CategoryNum=003004001',
                '__EVENTTARGET': 'MoreInfoList$Pager',
                'table_attr': 'MoreInfoList_DataGrid1',
                'page_attr': 'MoreInfoList_Pager',
            },
            {  # 采购公告及文件公示
                'url': 'http://www.ccgp-dalian.gov.cn/dlweb/showinfo/bxmoreinfo.aspx?CategoryNum=003001001',
                '__EVENTTARGET': 'MoreInfoList$Pager',
                'table_attr': 'MoreInfoList_DataGrid1',
                'page_attr': 'MoreInfoList_Pager',
            },
        ],
        '其他公告': [
            {  # 采购合同公告
                'url': 'http://www.ccgp-dalian.gov.cn/dlweb/showinfo/bxmoreinfo.aspx?CategoryNum=003005001',
                '__EVENTTARGET': 'MoreInfoList$Pager',
                'table_attr': 'MoreInfoList_DataGrid1',
                'page_attr': 'MoreInfoList_Pager',
            },
            {  # 中标及废标公告
                'url': 'http://www.ccgp-dalian.gov.cn/dlweb/showinfo/bxmoreinfo.aspx?CategoryNum=003002001',
                '__EVENTTARGET': 'MoreInfoList$Pager',
                'table_attr': 'MoreInfoList_DataGrid1',
                'page_attr': 'MoreInfoList_Pager',
            },
        ]
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'TIME_DELAY_REQUEST': 0.5,
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

    def start_requests(self):
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                yield scrapy.Request(url=cu['url'], callback=self.parse_urls, meta={
                    'notice_type': notice_type,
                }, cb_kwargs={
                    'url': cu['url'],
                    'event_target': cu['__EVENTTARGET'],
                    'table_attr': cu['table_attr'],
                    'page_attr': cu['page_attr'],
                })

    def parse_urls(self, resp, url, event_target, table_attr, page_attr):
        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)
        pages = resp.xpath(
            '//div[@id="{page_attr}"]/table//tr/td/font/b/text()'.format(page_attr=page_attr)
        ).get()
        init_view_state = resp.xpath('//input[@name="__VIEWSTATE"]/@value').get()
        init_view_state_generator = resp.xpath('//input[@name="__VIEWSTATEGENERATOR"]/@value').get()
        init_event_validation = resp.xpath('//input[@name="__EVENTVALIDATION"]/@value').get()

        try:
            pages = int(pages)
        except ValueError as e:
            self.log(e)
        else:
            event_argument = 1
            if_turn_page = True
            print('当前请求栏目: ', resp.meta.get('notice_type', ''))
            for i in range(1, pages + 1):
                if if_turn_page:
                    try:
                        text = requests.post(url=url, data={
                            '__VIEWSTATE': init_view_state,
                            '__EVENTARGUMENT': event_argument,
                            '__EVENTTARGET': event_target,
                            '__VIEWSTATEENCRYPTED': '',
                            # add
                            '__VIEWSTATEGENERATOR': init_view_state_generator,
                            '__EVENTVALIDATION': init_event_validation,
                            'MoreInfoList$Titletxt': ''
                        }, headers=headers, proxies=proxies).content.decode('gbk')
                    except Exception as e:
                        self.logger.info(e)
                    else:
                        doc = etree.HTML(text)
                        # 获取修改默认参数
                        init_view_state = doc.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
                        init_view_state_generator = doc.xpath('//input[@name="__VIEWSTATEGENERATOR"]/@value')[0]
                        init_event_validation = doc.xpath('//input[@name="__EVENTVALIDATION"]/@value')[0]

                        # 发起详情页请求
                        li_els = doc.xpath('//table[@id="{table_attr}"]/tr'.format(table_attr=table_attr))

                        if li_els:
                            for n, li_el in enumerate(li_els):
                                # for li_el in li_els[0:5]:
                                title_name = li_el.xpath('.//a/@title')[0]
                                title_name = re.sub('【.*?】', '', title_name)
                                pub_time = li_el.xpath('.//td[position()=3]/text()')[0].strip()

                                if all([self.start_time, self.end_time]):
                                    if_crewled, if_turn_page = utils.get_crwal_turn_page_command(
                                        pub_time, self.start_time, self.end_time
                                    )
                                    if not if_crewled:  # 不采
                                        break

                                hrefs = li_el.xpath('.//td[position()=2]/a/@href')
                                if hrefs:
                                    detail_url = self.query_url + hrefs[0]
                                    yield scrapy.Request(url=detail_url, callback=self.parse_item, meta={
                                        'notice_type': resp.meta.get('notice_type', ''),
                                        'title_name': title_name,
                                        'pub_time': pub_time,
                                    }, priority=len(li_els) + 1 - n, dont_filter=True)
                        event_argument += 1
                else:  # 不翻
                    break

    def parse_item(self, resp):
        """
        解析详情页页面数据
        @param {
            resp: 响应
        }
        @return {
            notice_item
        }
        """
        content = resp.xpath('//table[@id="_Sheet1"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url, pub_time=pub_time, resp=resp)

        notice_item = items.NoticesItem()
        notice_item["origin"] = resp.url

        notice_item["title_name"] = title_name
        notice_item["pub_time"] = pub_time

        notice_item["info_source"] = self.basic_area
        notice_item["is_have_file"] = constans.TYPE_HAVE_FILE if files_path else constans.TYPE_NOT_HAVE_FILE
        notice_item["files_path"] = files_path
        notice_item["notice_type"] = notice_types[0] if notice_types else constans.TYPE_UNKNOWN_NOTICE
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = '政府采购'
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_143_dalian_spider -a sdt=2021-09-01 -a edt=2021-10-18".split(" "))
    # cmdline.execute("scrapy crawl province_143_dalian_spider".split(" "))
