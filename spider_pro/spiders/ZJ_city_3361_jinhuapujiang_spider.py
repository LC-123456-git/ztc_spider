# -*- coding: utf-8 -*-
# @file           :ZJ_city_3361_jinhuapujiang_spider.py
# @description    :浙江省金华市浦江县人民政府
# @date           :2021/08/02 11:43:56
# @author         :miaokela
# @version        :1.0
import re
import random
import json
import requests
from datetime import datetime
from math import ceil

import scrapy

from spider_pro import utils, constans, items


class ZjCity3361JinhuapujiangSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3361_jinhuapujiang_spider'
    allowed_domains = ['pj.gov.cn', '220.191.229.165:900']
    start_urls = ['http://pj.gov.cn/']
    query_url = 'http://pj.gov.cn'
    query_list_url = 'http://220.191.229.165:900/TPFrame/zhmanagemis/pages/allprojectgonggao/allprojectgonggaolistaction' \
                     '.action?cmd=page_Load&JYType={jy_type}&GGType={gg_type}&isCommondto=true&pagesize={page_size}'
    query_detail_url = 'http://220.191.229.165:900/TPFrame/zhmanagemis/pages/allprojectgonggao/allprojectgonggaoaction.' \
                       'action?cmd=page_Load&RowGuid={row_guid}&JYType={jy_type}&GGType={gg_type}&isCommondto=true'

    basic_area = '浙江省金华市浦江县人民政府'
    area_id = 3361
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '工程建设', 'jy_type': 'JSGC', 'gg_type': 'ZhaoBiaoWJ'},  # 招标文件公示
            {'category': '政府/企业采购', 'jy_type': 'ZFCG', 'gg_type': 'ZhaoBiaoWJ'},  # 采购文件公示
        ],
        '招标公告': [
            {'category': '工程建设', 'jy_type': 'JSGC', 'gg_type': 'ZhaoBiaoGG'},  # 招标公告
            {'category': '产权/要素/服务', 'jy_type': 'CQJY', 'gg_type': 'ZhaoBiaoGG'},  # 招标公告
            {'category': '政府/企业采购', 'jy_type': 'ZFCG', 'gg_type': 'ZhaoBiaoGG'},  # 采购公告
            {'category': '乡镇中心建设工程', 'jy_type': 'XZZXJSGC', 'gg_type': 'ZhaoBiaoGG'},  # 招标公告
            {'category': '乡镇中心建设工程', 'jy_type': 'XZZXJSGC', 'gg_type': 'ZiXingFaBao'},  # 自行发包（邀请招标）
            {'category': '乡镇中心产权交易', 'jy_type': 'XZZXCQJY', 'gg_type': 'ZhaoBiaoGG'},  # 招标公告
        ],
        '招标变更': [
            {'category': '产权/要素/服务', 'jy_type': 'CQJY', 'gg_type': 'BianGengGG'},  # 更正（补充）公告
            {'category': '乡镇中心建设工程', 'jy_type': 'XZZXJSGC', 'gg_type': 'BianGengGG'},  # 更正（补充）公告
            {'category': '乡镇中心产权交易', 'jy_type': 'XZZXCQJY', 'gg_type': 'BianGengGG'},  # 更正（补充）公告
            {'category': '工程建设', 'jy_type': 'JSGC', 'gg_type': 'ZhaoBiaoChengQing'},  # 更正公告
            {'category': '政府/企业采购', 'jy_type': 'ZFCG', 'gg_type': 'BianGengGG'},  # 更正公告
        ],
        '招标异常': [
            {'category': '政府/企业采购', 'jy_type': 'ZFCG', 'gg_type': 'feibiaogg'},  # 废标公告
        ],
        '中标预告': [
            {'category': '工程建设', 'jy_type': 'JSGC', 'gg_type': 'HouXuanRenGongShi'},  # 中标候选人/定标公示
            {'category': '乡镇中心建设工程', 'jy_type': 'XZZXJSGC', 'gg_type': 'HouXuanRenGongShi'},  # 中标候选人公示
        ],
        '中标公告': [
            {'category': '工程建设', 'jy_type': 'JSGC', 'gg_type': 'JieGuoGG'},  # 中标结果公告
            {'category': '政府/企业采购', 'jy_type': 'ZFCG', 'gg_type': 'JieGuoGG'},  # 中标公告
            {'category': '乡镇中心建设工程', 'jy_type': 'XZZXJSGC', 'gg_type': 'JieGuoGG'},  # 中标结果公告
            {'category': '乡镇中心产权交易', 'jy_type': 'XZZXCQJY', 'gg_type': 'JieGuoGG'},  # 中标结果公告
        ],
    }
    l_form_data = json.dumps({
        "commonDto": [
            {"id": "pageNumText", "bind": "pagesize1", "type": "textbox", "value": "", "text": ""},
            {"id": "_common_hidden_viewdata", "type": "hidden", "value": ""}
        ]
    })
    d_form_data = {
        "commonDto": json.dumps([{"id": "gonggaocontent", "bind": "dataBean.gonggaocontent", "type": "outputtext"},
                                 {"id": "_common_hidden_viewdata", "type": "hidden", "value": ""}])
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
                jy_type = cu['jy_type']
                gg_type = cu['gg_type']

                c_url = self.query_list_url.format(
                    jy_type=jy_type,
                    gg_type=gg_type,
                    page_size=0,
                )

                yield scrapy.Request(
                    url=c_url, callback=self.get_max_page, method='POST',
                    body=ZjCity3361JinhuapujiangSpiderSpider.l_form_data, meta={
                        'notice_type': notice_type,
                        'category': cu['category'],
                        'jy_type': jy_type,
                        'gg_type': gg_type,
                    }, dont_filter=True)

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    def is_in_interval(self, url, resp, method='GET', **kwargs):
        status = 0
        headers = ZjCity3361JinhuapujiangSpiderSpider.get_headers(resp)
        proxies = resp.meta.get('proxy')
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers, proxies=proxies).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'), headers=headers, proxies=proxies).text
                if text:
                    ret = json.loads(text)

                    rows = ret['custom']['project']['list']

                    if rows:
                        # 首个时间 末尾时间
                        first_pub_time = rows[0].get('shr_date', '')
                        final_pub_time = rows[-1].get('shr_date', '')

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = utils.convert_to_strptime(first_pub_time)
                            final_pub_time = utils.convert_to_strptime(final_pub_time)
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

    def get_max_page(self, resp):
        json_data = resp.text
        jy_type = resp.meta.get('jy_type', '')
        gg_type = resp.meta.get('gg_type', '')
        notice_type = resp.meta.get('notice_type', '')
        category = resp.meta.get('category', '')
        try:
            ret = json.loads(json_data)
            page_num = ret['custom']['pagenum']

            max_page = ceil(page_num / 16)
        except Exception as e:
            self.logger.info('获取最大页数失败{}'.format(e))
        else:
            for page in range(max_page):
                offset = page * 16
                c_url = self.query_list_url.format(
                    jy_type=jy_type,
                    gg_type=gg_type,
                    page_size=offset,
                )

                # TODO 判断是否翻页
                judge_status = self.is_in_interval(
                    c_url,
                    resp,
                    method='POST',
                    data=ZjCity3361JinhuapujiangSpiderSpider.l_form_data,
                )

                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(
                        url=c_url, callback=self.parse_list, method='POST',
                        body=ZjCity3361JinhuapujiangSpiderSpider.l_form_data, meta={
                            'notice_type': notice_type,
                            'category': category,
                            'jy_type': jy_type,
                            'gg_type': gg_type,
                        }, priority=max_page - page, dont_filter=True)

    def parse_list(self, resp):
        json_data = resp.text
        notice_type = resp.meta.get('notice_type', '')
        category = resp.meta.get('category', '')
        jy_type = resp.meta.get('jy_type', '')
        gg_type = resp.meta.get('gg_type', '')

        try:
            ret = json.loads(json_data)
            data_list = ret['custom']['project']['list']
            assert isinstance(data_list, list), 'data type is not list.'
        except Exception as e:
            self.logger.info('获取详情页列表失败{}'.format(e))
        else:
            for n, dl in enumerate(data_list):
                pub_time = dl.get('shr_date', '')
                if utils.check_range_time(self.start_time, self.end_time, pub_time):
                    open_url = dl.get('url', '')

                    c_com = re.compile(r'window.open\(\'(.*?)\',')
                    detail_urls = c_com.findall(open_url)
                    if detail_urls:
                        detail_url = detail_urls[0]

                        row_guid_com = re.compile(r'RowGuid=(.*?)&')

                        row_guids = row_guid_com.findall(detail_url)
                        if row_guids:
                            row_guid = row_guids[0]
                            c_url = ZjCity3361JinhuapujiangSpiderSpider.query_detail_url.format(
                                jy_type=jy_type,
                                gg_type=gg_type,
                                row_guid=row_guid,
                            )
                            yield scrapy.FormRequest(
                                url=c_url, callback=self.parse_detail,
                                formdata=ZjCity3361JinhuapujiangSpiderSpider.d_form_data, meta={
                                    'notice_type': notice_type,
                                    'category': category,
                                    'pub_time': pub_time,
                                }, priority=len(data_list) * 1000 - n, dont_filter=True)

    def parse_detail(self, resp):
        json_data = resp.text
        try:
            ret = json.loads(json_data)
            content = ret['controls'][0]['value']
            title_name = ret['custom']['ggtitle']
        except Exception as e:
            self.logger.info('获取详情页信息失败{}'.format(e))
        else:
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

    cmdline.execute("scrapy crawl ZJ_city_3361_jinhuapujiang_spider -a sdt=2021-06-20 -a edt=2021-08-02".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3361_jinhuapujiang_spider".split(" "))
