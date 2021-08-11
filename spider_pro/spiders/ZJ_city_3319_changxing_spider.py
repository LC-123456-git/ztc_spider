'''
author: miaokela
Date: 2021-04-26 09:05:50
LastEditTime: 2021-04-27 22:12:07
Description:
'''
import requests
import scrapy
import re
from lxml import etree

from spider_pro import constans, utils, items


class ZjCity3319ChangxingSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3319_changxing_spider'
    allowed_domains = ['ggzy.zjcx.goc.cn']
    start_urls = ['http://ggzy.zjcx.goc.cn/']
    basic_area = '浙江省-湖州市-长兴县'
    area_id = 3319
    query_url = 'http://ggzy.zjcx.gov.cn'
    url_map = {
        '招标公告': [
            {
                'category': '工程交易',
                # 'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002001/012002001001/',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/showinfo/zbgg.aspx',
                '__EVENTTARGET': 'Pager',
                'table_attr': 'DataGrid1',
                'page_attr': 'Pager',
            },
            {
                'category': '产权交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002003/012002003001/MoreInfo.aspx?CategoryNum=012002003001',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '国土交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002004/012002004002/MoreInfo.aspx?CategoryNum=012002004002',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '限额以下',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002007/012002007001/MoreInfo.aspx?CategoryNum=012002007001',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '限额以下',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002007/012002007003/MoreInfo.aspx?CategoryNum=012002007003',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '限额以下',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002007/012002007004/MoreInfo.aspx?CategoryNum=012002007004',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '政府采购',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002002/012002002008/012002002008003/MoreInfo.aspx?CategoryNum=012002002008003',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '资格预审结果公告': [
            {
                'category': '工程交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002001/012002001007/MoreInfo.aspx?CategoryNum=012002001007',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '招标变更': [
            {
                'category': '工程交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002001/012002001008/MoreInfo.aspx?CategoryNum=012002001008',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '招标异常': [
            {
                'category': '政府采购',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002002/012002002008/012002002008004/MoreInfo.aspx?CategoryNum=012002002008004',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '中标预告': [
            {
                'category': '工程交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002001/012002001010/MoreInfo.aspx?CategoryNum=012002001010',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '中标公告': [
            {
                'category': '工程交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002001/012002001006/MoreInfo.aspx?CategoryNum=012002001006',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '产权交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002003/012002003003/MoreInfo.aspx?CategoryNum=012002003003',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '产权交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002003/012002003004/MoreInfo.aspx?CategoryNum=012002003004',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '国土交易',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002004/012002004003/MoreInfo.aspx?CategoryNum=012002004003',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '限额以下',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002007/012002007002/MoreInfo.aspx?CategoryNum=012002007002',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
            {
                'category': '政府采购',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002002/012002002008/012002002008005/MoreInfo.aspx?CategoryNum=012002002008005',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ],
        '其他公告': [
            {
                'category': '政府采购',
                'url': 'http://ggzy.zjcx.gov.cn/cxweb/ggzy/012002/012002002/012002002008/012002002008006/MoreInfo.aspx?CategoryNum=012002002008006',
                '__EVENTTARGET': 'MoreInfoList1$Pager',
                'table_attr': 'MoreInfoList1_DataGrid1',
                'page_attr': 'MoreInfoList1_Pager',
            },
        ]
    }
    keywords_map = {
        '变更|答疑|澄清|补充|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|评标结果': '中标预告',
        '中标|成交': '中标公告',
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
                    'category': cu['category'],
                }, cb_kwargs={
                    'url': cu['url'],
                    'event_target': cu['__EVENTTARGET'],
                    'table_attr': cu['table_attr'],
                    'page_attr': cu['page_attr'],
                })

    def parse_urls(self, resp, url, event_target, table_attr, page_attr):
        '''
        获取最大分页
        循环获取token请求解析详情页链接构造详情页请求
        @param {
            resp
            url
        }
        @return {*}
        '''
        pages = resp.xpath(
            '//div[@id="{page_attr}"]/table/tr/td/font/b/text()'.format(page_attr=page_attr)).get()
        init_view_state = resp.xpath('//input[@name="__VIEWSTATE"]/@value').get()
        event_argument = 1
        view_state_encrypted = ''

        try:
            pages = int(pages)
        except ValueError as e:
            self.log(e)
        else:
            # for i in range(1, 2):
            if_turn_page = True
            for i in range(1, pages + 1):
                if if_turn_page:
                    # print('%d翻页%d' % (pages, i))
                    try:
                        text = requests.post(url=url, data={
                            '__VIEWSTATE': init_view_state,
                            '__EVENTARGUMENT': event_argument,
                            '__EVENTTARGET': event_target,
                            '__VIEWSTATEENCRYPTED': view_state_encrypted,
                        }, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                        }).text
                    except Exception as e:
                        self.log(e)
                    else:
                        doc = etree.HTML(text)
                        # 获取修改默认参数
                        init_view_state = doc.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
                        # 发起详情页请求
                        li_els = doc.xpath('//table[@id="{table_attr}"]/tr'.format(table_attr=table_attr))

                        for li_el in li_els:
                            # for li_el in li_els[0:5]:
                            title_name = li_el.xpath('.//a/@title')[0]
                            pub_time = li_el.xpath('.//td[position()=3]/text()')[0].strip()

                            if all([self.start_time, self.end_time]):
                                # 阻止往下翻页
                                x, y, _ = utils.judge_dst_time_in_interval(pub_time, self.start_time, self.end_time)

                                if x:
                                    pass
                                elif y:
                                    if_turn_page = False
                                    break
                                else:
                                    continue
                            hrefs = li_el.xpath('.//td[position()=2]/a/@href')
                            if hrefs:
                                detail_url = self.query_url + hrefs[0]
                                yield scrapy.Request(url=detail_url, callback=self.parse_item, meta={
                                    'notice_type': resp.meta.get('notice_type', ''),
                                    'category': resp.meta.get('category', ''),
                                    'title_name': title_name,
                                    'pub_time': pub_time,
                                }, priority=pages + 1 - i, dont_filter=True)
                        event_argument += 1
                else:
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
        content = resp.xpath('//table[@id="tblInfo"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')

        # 移除不必要信息: 发布时间、上下页tdTitle
        _, content = utils.remove_specific_element(content, 'td', 'id', 'tdTitle')
        _, content = utils.remove_specific_element(content, 'table', 'id', 'tblInfo', if_child=True,
                                                   child_attr='tr', index=2)

        content = utils.avoid_escape(content)  # 防止转义

        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))

        # 匹配文件
        _, files_path = utils.catch_files(content, self.query_url, resp=resp)

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
        notice_item["category"] = resp.meta.get('category', '')
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl ZJ_city_3319_changxing_spider -a sdt=2021-03-01 -a edt=2021-05-10".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3319_changxing_spider".split(" "))
