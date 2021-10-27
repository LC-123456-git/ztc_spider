# -*- coding: utf-8 -*-
# @file           :province_151_zhonggangzb_spider.py
# @description    :中钢招标有限责任公司
# @date           :2021/10/25 10:02:36
# @author         :miaokela
# @version        :1.0
import json
import math
import re
import copy

import scrapy

from spider_pro import constans, utils, items


class Province151ZhonggangzbSpiderSpider(scrapy.Spider):
    name = 'province_151_zhonggangzb_spider'
    allowed_domains = ['tendering.sinosteel.com']
    start_urls = ['https://tendering.sinosteel.com/']

    basic_area = '中钢招标有限责任公司'
    area_id = 151
    base_url = 'https://tendering.sinosteel.com'
    query_url = 'https://tendering.sinosteel.com/EpointWebBuilder/rest/frontAppCustomAction/getPageInfoListNew'

    """
    {"controls":[],"custom":{"count":1,"infodata":[{"categorynum":"005001","infotype":"News","strcomment":"中钢招标有限责任公司受中国农业发展银行的委托，现对中国农业发展银行总行数据中心租赁项目进行单一来源采前公示，公示内容如下：一、采购单位中国农业发展银行二、采购项目名称中国农业发展银行总行数据中心租赁项目三、采购内容采购总行数据中心租赁服务四、单一来源邀请供应商中国移动通信集团北京有限公司 北京市东城","infoid":"e27bace0-7ef3-41cb-989e-e35d645fdae5",
    "recommend":0,"title":"中国农业发展银行总行数据中心租赁项目 单一来源采前公示","titletype":"Text","infourl":"/zgzb/zbzq/005001/20211018/e27bace0-7ef3-41cb-989e-e35d645fdae5.html","customtitle":null,"shixiao":null,"baomingdate":"2021-10-18 17:00:00","urlname":null,"infodate":"2021-10-18"}]},"status":{"code":1,"top":false,"text":"操作成功","url":""}}
    """

    url_map = {
        '招标公告': [
            {'code': '005001'},  # 招标公告
        ],
        '中标预告': [
            {'code': '005003'},  # 中标候选人公示
        ],
        '中标公告': [
            {'code': '005004'},  # 结果公告
        ],
    }
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')
        self.page_size = 8
        self._form_data = {
            'params': '{{"siteGuid":"7eb5f7f1-9041-43ad-8e13-8fcb82ea831a","categoryNum":"{category_num}","kw":"","con":"",' + \
                      '"pageIndex":{page_index},"pageSize":%d,"startDate":"%s","endDate":"%s"}}' % (
                          self.page_size, self.start_time, self.end_time)
        }

    @property
    def form_data(self):
        return copy.deepcopy(self._form_data)

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
        for notice_type, params in self.url_map.items():
            for param in params:
                code = param.get('code', '')
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': 0
                }))

                yield scrapy.FormRequest(
                    url=self.query_url, callback=self.turn_page, formdata=form_data,
                    meta={
                        'notice_type': notice_type,
                    }, cb_kwargs={
                        'code': code,
                    }
                )

    def turn_page(self, resp, code):
        content = json.loads(resp.text)

        headers = utils.get_headers(resp)
        proxies = utils.get_proxies(resp)

        total = content.get('custom', {}).get('count', 0)

        max_page = math.ceil(total / self.page_size)

        if all([self.start_time, self.end_time]):
            for i in range(max_page):
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': i
                }))

                judge_status = utils.judge_in_interval(
                    self.query_url, start_time=self.start_time, end_time=self.end_time, method='POST', data=form_data,
                    proxies=proxies, headers=headers,
                    rule='//infodata/infodate/text()', doc_type='json'
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.FormRequest(
                        url=self.query_url, callback=self.parse_list, meta=resp.meta, formdata=form_data,
                        priority=(max_page - i) * 10,
                        dont_filter=True
                    )
        else:
            for i in range(max_page):
                form_data = self.form_data
                form_data.update(params=form_data['params'].format(**{
                    'category_num': code,
                    'page_index': i
                }))
                yield scrapy.FormRequest(
                    url=self.query_url, callback=self.parse_list, meta=resp.meta, formdata=form_data,
                    priority=(max_page - i) * 10,
                    dont_filter=True
                )

    def parse_list(self, resp):
        content = json.loads(resp.text)
        result = content.get('custom', {}).get('infodata', [])

        for n, r in enumerate(result):
            pub_time = r.get('infodate', '')
            title_name = r.get('title', '')
            info_url = r.get('infourl', '')
            c_url = ''.join([self.base_url, info_url])

            if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                resp.meta.update(**{
                    'pub_time': pub_time,
                    'title_name': title_name
                })
                yield scrapy.Request(
                    url=c_url, callback=self.parse_detail, meta=resp.meta,
                    priority=(len(result) - n) * 10 ** 6
                )

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="ewb-article-content"]').get()
        title_name = resp.meta.get('title_name')
        notice_type_ori = resp.meta.get('notice_type')
        pub_time = resp.meta.get('pub_time')

        content = utils.avoid_escape(content)
        # 删除指定内容
        content = re.sub(
            r'七、其他.*?本项目.*?账号：<span>[0-9\s]+</span>\s*</p>',
            '七、其他</b></p>', content.replace('\n', ''),
            re.DOTALL
        )
        content = re.sub(
            r'．发布渠道.*?发布。</span>\s*</p>',
            '．发布渠道</span></b></p>',
            content.replace('\n', ''),
            re.DOTALL
        )
        content = re.sub(
            r'．发布渠道.*?发布。<br>',
            '．发布渠道<br>',
            content.replace('\n', ''),
            re.DOTALL
        )
        # 关键字重新匹配 notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
        )

        # 匹配文件
        _, files_path = utils.catch_files(content, self.base_url, pub_time=pub_time, resp=resp)

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
        notice_item["category"] = ''
        print(resp.meta.get('pub_time'), resp.url)
        return notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_151_zhonggangzb_spider -a sdt=2021-01-01 -a edt=2021-10-25".split(" "))
    cmdline.execute("scrapy crawl province_151_zhonggangzb_spider".split(" "))
