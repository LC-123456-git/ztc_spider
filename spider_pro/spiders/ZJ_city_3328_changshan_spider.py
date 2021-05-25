# -*- coding: utf-8 -*-
# author: miaokela
# Date: 2021-05-24 11:54:42
# Description: 常山县公共交易资源网
import scrapy
import copy
import re
import random
import requests
from lxml import etree
from datetime import datetime

from spider_pro import utils, constans, items


class ZjCity3328ChangshanSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3328_changshan_spider'
    allowed_domains = ['qzcs.zjzwfw.gov.cn']
    start_urls = ['http://qzcs.zjzwfw.gov.cn/']
    area_id = 3328
    basic_area = '浙江省-衢州市-常山县-常山县公共交易资源网'
    query_url = 'http://qzcs.zjzwfw.gov.cn/module/jpage/dataproxy.jsp?startrecord={startrecord}&perpage=15'
    base_url = 'http://qzcs.zjzwfw.gov.cn'
    keywords_map = {
        '中标|成交|结果': '中标公告',
        '意向': '招标预告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '评标结果': '中标预告',
    }
    url_map = {
        '建设工程': {
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341070/index.html',
        },
        '政府采购': {
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341069/index.html',
        },
        '综合交易': {  # add
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341072/index.html',
        },
        '土地交易': {
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341071/index.html',
        },
        '农村产权': {
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341073/index.html',
        },
        '乡镇平台': {  # add
            'url': 'http://qzcs.zjzwfw.gov.cn/col/col1341074/index.html',
        }
    }
    form_data = {
        'col': '1',
        'appid': '1',
        'webid': '76',
        'path': '/',
        'columnid': '',  # ok
        'sourceContentType': '1',
        'unitid': '4359341',
        'webname': '浙江政务服务网（衢州市常山县）',
        'permissiontype': '0'
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    @property
    def _form_data(self):
        return copy.deepcopy(self.form_data)

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    def judge_in_interval(self, url, method='GET', resp=None, ancestor_el='table', ancestor_attr='id', ancestor_val='',
                          child_el='tr', time_sep='-', doc_type='html', **kwargs):
        """
        判断最末一条数据是否在区间内
        Args:
            resp: scrapy请求响应
            url: 分页链接
            method: 请求方式
            ancestor_el: 祖先元素
            ancestor_attr: 属性
            ancestor_val: 属性值
            child_el: 子孙元素
            time_sep: 时间中间分隔符 默认：-
            doc_type: 文档类型
            **kwargs:
                @data: POST请求体
                @enhance_els: 扩展xpath匹配子节点细节['table', 'tbody'] 连续节点
        Returns:
            status: 结果状态
                1 首条在区间内 可抓、可以翻页
                0 首条不在区间内 停止翻页
                2 末条大于最大时间 continue
        """
        status = 0
        headers = ZjCity3328ChangshanSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'), headers=headers).text
                if text:
                    els = []
                    if doc_type == 'html':
                        doc = etree.HTML(text)

                        # enhance_els
                        enhance_els = kwargs.get('enhance_els', [])

                        enhance_condition = ''
                        if enhance_els:
                            for enhance_el in enhance_els:
                                enhance_condition += '/{0}'.format(enhance_el)

                        _path = '//{ancestor_el}[@{ancestor_attr}="{ancestor_val}"]{enhance_condition}//{child_el}[last()]/text()[not(normalize-space()="")]'.format(
                            **{
                                'ancestor_el': ancestor_el,
                                'ancestor_attr': ancestor_attr,
                                'ancestor_val': ancestor_val,
                                'child_el': child_el,
                                'enhance_condition': enhance_condition
                            })
                        els = doc.xpath(_path)
                    if doc_type == 'xml':
                        doc = etree.XML(text)
                        _path = '//{child_el}/text()'.format(**{
                            'child_el': child_el,
                        })
                        els = doc.xpath(_path)
                    if els:
                        first_el = els[0]
                        final_el = els[-1]

                        el = els[-1]
                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' %
                                           (time_sep, time_sep))

                        first_pub_time = t_com.findall(first_el)
                        final_pub_time = t_com.findall(final_el)

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = datetime.strptime(
                                first_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            final_pub_time = datetime.strptime(
                                final_pub_time[0], '%Y{0}%m{1}%d'.format(time_sep, time_sep)
                            )
                            start_time = datetime.strptime(
                                self.start_time, '%Y-%m-%d')
                            end_time = datetime.strptime(
                                self.end_time, '%Y-%m-%d')
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
                self.log(e)
        else:
            status = 1  # 没有传递时间
        return status

    @staticmethod
    def get_start_record_list(total_record):
        """
        获取分组数据列表
        Args:
            total_record: 总记录数
        Returns:
        """
        start_record_list = [1]
        base_n = 45
        if total_record > base_n:
            counts = total_record // base_n
            for i in range(1, counts + 1):
                start_record_list.append(i * base_n + 1)
        return start_record_list

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
        column_com = re.compile('col(\d+)')
        for category_type, info in self.url_map.items():
            url = info.get('url', '')
            column_ids = column_com.findall(url)
            if column_ids:
                column_id = column_ids[0]

                yield scrapy.Request(url=url, callback=self.get_max_page, meta={
                    'category_type': category_type,
                }, cb_kwargs={
                    'column_id': column_id,
                })

    def get_max_page(self, resp, column_id):
        """
        获取总记录数
        """
        content = resp.text
        total_record_com = re.compile('function.*totalRecord:(.*),openCookies.*barPosition')
        total_records = total_record_com.findall(content)
        if total_records:
            total_record = total_records[0]

            try:
                total_record = int(total_record)
            except ValueError as e:
                self.log(e)
            else:
                start_record_list = ZjCity3328ChangshanSpiderSpider.get_start_record_list(total_record)
                for n, start_record in enumerate(start_record_list):
                    form_data = self._form_data
                    form_data['columnid'] = column_id

                    # 判断是否翻下一个记录
                    # 请求获取最后一条记录的时间
                    c_url = self.query_url.format(startrecord=start_record)
                    judge_status = self.judge_in_interval(
                        c_url, method='POST', child_el='record', doc_type='xml', data=form_data, resp=resp,
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        yield scrapy.FormRequest(
                            url=self.query_url.format(startrecord=start_record),
                            formdata=form_data, callback=self.parse_list,
                            meta={
                                'category_type': resp.meta.get('category_type', ''),
                            }, priority=(len(start_record_list) - n) * 10
                        )

    def parse_list(self, resp):
        """
        获取详情页链接与title
        Args:
            resp:
                <datastore>
                    <totalrecord>6163</totalrecord>
                    <totalpage>309</totalpage>
                    <nextgroup>
                        <![CDATA[<a href="./dataproxy.jsp?page=5&appid=1&webid=3095&path=/&columnid=1229165988&unitid=6101313&webname=杭州余杭门户网站"></a>]]></nextgroup>
                    <recordset>
                        <record>
                            <![CDATA[<li><a href="http://www.yuhang.gov.cn/art/2020/8/14/art_1229179150_1872814.html" target="_blank" title="杭州市公共资源交易中心余杭分中心关于杭州市余杭区人民政府南苑街道办事处办公家具采购项目的公开招标公告"><span>杭州市公共资源交易中心余杭分中心关于杭州市余杭区人民政府南苑街道办事处办公家具采购项目的公开招标公告</span><i>2020-08-14</i></a></li>]]>
                        </record>
                    </recordset>
                </datastore>
        Returns:
        """
        detail_xml = resp.text
        try:
            doc = etree.XML(detail_xml)
        except etree.XMLSyntaxError as e:
            self.log(e)
        else:
            record_set = doc.xpath('//record')

            for record in record_set:
                # 因内容被注释 正则匹配 (链接 标题 时间)
                record_com = re.compile("href='(.*?)'.*?46px\">(.*?)</span>")
                record_infos = record_com.findall(record.text)
                if record_infos:
                    record_info = record_infos[0]
                    url, pub_time = record_info

                    if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                        yield scrapy.Request(url=''.join([self.base_url, url]), callback=self.parse_item, meta={
                            'category_type': resp.meta.get('category_type'),
                            'pub_time': pub_time,
                        }, priority=1000)

    @staticmethod
    def replace_a_without_href(content, attr_name='span'):
        """
        清洗脏数据a标签
        """
        error = ''
        try:
            doc = etree.HTML(content)
            els = doc.xpath('//a[not(@href)]')
            for el in els:
                el_content = etree.tounicode(el)
                n_el_content = el_content.replace('<a', '<span').replace('</a>', '</span>')
                content = content.replace(el_content, n_el_content)
        except Exception as e:
            error = 'error:{0}'.format(e)

        return error, content

    def parse_item(self, resp):
        try:
            content = resp.xpath('//div[@class="wzy_content"]/div').get()
            title_name = resp.xpath('//td[@class="title"]/text()').get()
            category_type = resp.meta.get('category_type')

            # 关键词匹配 修改notice_type
            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type
            else:
                notice_type_ori = '招标公告'

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )
            # REMOVE DATE
            _, content = utils.remove_specific_element(content, 'table', 'align', 'center', if_child=True,
                                                       child_attr='tr',
                                                       index=2)
            # REMOVE WINDOW-CLOSE
            _, content = utils.remove_specific_element(content, 'table', 'align', 'center', index=2)

            content = content.replace('<a/>', '')

            # REPLACE ATTR A WITHOUT HREF TO SPAN
            _, content = ZjCity3328ChangshanSpiderSpider.replace_a_without_href(content)

            # 投标文件
            _, files_path = utils.catch_files(content, self.base_url)

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
            notice_item["category"] = category_type
            print(resp.meta.get('pub_time'), resp.url)
            return notice_item
        except Exception as e:
            self.log('error:{0} \n url:{1}'.format(e, resp.url))


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl ZJ_city_3328_changshan_spider -a sdt=2018-01-01 -a edt=2018-12-24".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3328_changshan_spider".split(" "))
