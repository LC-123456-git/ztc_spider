# author: miaokela
# Date: 2021-04-21 13:04:42
# Description: 余杭门户网站
import scrapy
import re
import copy
import requests
from lxml import etree
from datetime import datetime

from spider_pro import items, constans, utils


class ZjCity3314YuhangSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3314_yuhang_spider'
    allowed_domains = ['www.yuhang.gov.cn']
    start_urls = ['http://www.yuhang.gov.cn/']
    area_id = 3314
    basic_area = '浙江-杭州市-余杭区-门户网站'
    query_url = 'http://www.yuhang.gov.cn/module/jpage/dataproxy.jsp?startrecord={startrecord}&perpage=20'
    base_url = 'http://www.yuhang.gov.cn'
    url_map = {  # columnid unitid 6101313 6089351
        '招标公告': [
            {'url': 'http://www.yuhang.gov.cn/col/col1229165988/index.html', 'category_type': '政府集中采购',
             'unitid': '6101313', 'columnid': '1229165988'},  # 招标公告
            {'url': 'http://www.yuhang.gov.cn/col/col1229165993/index.html', 'category_type': '工程建设项目招投标',
             'unitid': '6101313', 'columnid': '1229165993'},  # 招标信息
            {'url': 'http://www.yuhang.gov.cn/col/col1229165985/index.html', 'category_type': '国有土地使用权出让',
             'unitid': '6089351', 'columnid': '1229165985'}  # 出让公告
        ],
        '招标变更': [
            {'url': 'http://www.yuhang.gov.cn/col/col1229165990/index.html', 'category_type': '政府集中采购',
             'unitid': '6101313', 'columnid': '1229165990'}
        ],
        '中标公告': [
            {'url': 'http://www.yuhang.gov.cn/col/col1229165994/index.html', 'category_type': '工程建设项目招投标',
             'unitid': '6101313', 'columnid': '1229165994'},  # 中标信息
            {'url': 'http://www.yuhang.gov.cn/col/col1229165989/index.html', 'category_type': '政府集中采购',
             'unitid': '6101313', 'columnid': '1229165989'},  # 中标公告
            {'url': 'http://www.yuhang.gov.cn/col/col1229165986/index.html', 'category_type': '国有土地使用权出让',
             'unitid': '6089351', 'columnid': '1229165986'}  # 成交公示
        ],
        '其他公告': [
            {'url': 'http://www.yuhang.gov.cn/col/col1229165987/index.html', 'category_type': '国有土地使用权出让',
             'unitid': '6089351', 'columnid': '1229165987'}
        ]
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }

    form_data = {
        'col': '1',
        'appid': '1',
        'webid': '3095',
        'path': '/',
        'columnid': '',  # ok
        'sourceContentType': '1',
        'unitid': '',  # ok
        'webname': '杭州余杭门户网站',
        'permissiontype': '0'
    }
    record_com = re.compile('href="(.*?)".*?title="(.*?)".*?<i>(.*?)</i>')
    total_record_com = re.compile('function.*totalRecord:(.*),openCookies.*barPosition')
    keywords_map = {
        '预审': '资格预审公告',
        '变更|澄清|延期|更正|补充|答疑': '招标变更',
        '废标|流标': '招标异常',
        '评标结果': '中标预告',
        '中标': '中标公告',
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.start_time = kwargs.get('sdt', '')
        self.end_time = kwargs.get('edt', '')

    @property
    def _form_data(self):
        return copy.deepcopy(self.form_data)

    def start_requests(self):
        for notice_type, urls_data in self.url_map.items():
            for url_data in urls_data:
                url = url_data['url']
                category_type = url_data['category_type']

                column_id = url_data['columnid']
                unit_id = url_data['unitid']

                yield scrapy.Request(url=url, callback=self.parse_urls, meta={
                    'category_type': category_type,
                    'notice_type': notice_type
                }, cb_kwargs={
                    'column_id': column_id,
                    'unit_id': unit_id,
                })

    @staticmethod
    def get_start_record_list(total_record):
        """
        获取分组数据列表
        Args:
            total_record: 总记录数
        Returns:
        """
        start_record_list = [1]
        base_n = 60
        if total_record > base_n:
            counts = total_record // 60
            for i in range(1, counts + 1):
                start_record_list.append(i * 60 + 1)
        return start_record_list

    def judge_in_interval(self, url, method='GET', ancestor_el='table', ancestor_attr='id', ancestor_val='',
                          child_el='tr', time_sep='-', doc_type='html', **kwargs):
        """
        判断最末一条数据是否在区间内
        Args:
            url: 分页链接
            method: 请求方式
            ancestor_el: 祖先元素
            ancestor_attr: 属性
            ancestor_val: 属性值
            child_el: 子孙元素
            time_sep: 时间中间分隔符 默认：-
            doc_type: 文档类型
            **kwargs: POST请求体
        Returns:
            status: 结果状态
                1 首条在区间内 可抓、可以翻页
                0 首条不在区间内 停止翻页
                2 末条大于最大时间 continue
        """
        status = 0
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=self.headers).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get('data'), headers=self.headers).text
                if text:
                    els = []
                    if doc_type == 'html':
                        doc = etree.HTML(text)
                        _path = '//{ancestor_el}[@{ancestor_attr}="{ancestor_val}"]//{child_el}[last()]/text()[not(normalize-space()="")]'.format(
                            **{
                                'ancestor_el': ancestor_el,
                                'ancestor_attr': ancestor_attr,
                                'ancestor_val': ancestor_val,
                                'child_el': child_el,
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
                        t_com = re.compile('(\d+%s\d+%s\d+)' % (time_sep, time_sep))

                        first_pub_time = t_com.findall(first_el)
                        final_pub_time = t_com.findall(final_el)

                        if all([first_pub_time, final_pub_time]):
                            first_pub_time = datetime.strptime(first_pub_time[0],
                                                               '%Y{0}%m{1}%d'.format(time_sep, time_sep))
                            final_pub_time = datetime.strptime(final_pub_time[0],
                                                               '%Y{0}%m{1}%d'.format(time_sep, time_sep))
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
                self.log(e)
        else:
            status = 1  # 没有传递时间
        return status

    def parse_urls(self, resp, column_id, unit_id):
        """
        获取总记录数
        """
        content = resp.text
        total_records = self.total_record_com.findall(content)
        if total_records:
            total_record = total_records[0]

            try:
                total_record = int(total_record)
            except ValueError as e:
                self.log(e)
            else:
                # 构造 form_data
                # 计算 startrecord
                start_record_list = ZjCity3314YuhangSpiderSpider.get_start_record_list(total_record)
                for n, start_record in enumerate(start_record_list):
                    form_data = self._form_data
                    form_data['columnid'] = column_id
                    form_data['unitid'] = unit_id

                    # 判断是否翻下一个记录
                    # 请求获取最后一条记录的时间
                    c_url = self.query_url.format(startrecord=start_record)
                    judge_status = self.judge_in_interval(
                        c_url, method='POST', child_el='record', doc_type='xml', data=form_data,
                    )
                    if judge_status == 0:
                        break
                    elif judge_status == 2:
                        continue
                    else:
                        yield scrapy.FormRequest(
                            url=c_url, formdata=form_data, callback=self.parse_data_urls, meta={
                                'category_type': resp.meta.get('category_type'),
                                'notice_type': resp.meta.get('notice_type'),
                            }, priority=(len(start_record_list) - n) * 10)

    def parse_data_urls(self, resp):
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
                record_infos = self.record_com.findall(record.text)
                if record_infos:
                    record_info = record_infos[0]
                    url, title_name, pub_time = record_info
                    if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                        yield scrapy.Request(url=url, callback=self.parse_item, meta={
                            'category_type': resp.meta.get('category_type'),
                            'notice_type': resp.meta.get('notice_type'),
                            'title_name': title_name,
                            'pub_time': pub_time,
                        }, priority=1000)

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
        content = resp.xpath('//div[@class="article-body"]').get()
        category_type = resp.meta.get('category_type')
        title_name = resp.meta.get('title_name')

        notice_type_ori = resp.meta.get('notice_type')

        # 关键词匹配 修改notice_type
        matched, match_notice_type = self.match_title(title_name)
        if matched:
            notice_type_ori = match_notice_type

        notice_types = list(
            filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT))
        # 去除底部链接div
        _, content = utils.remove_specific_element(content, 'div', 'class', 'article-tools')

        # 内容防止转义字符
        content = utils.avoid_escape(content)

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


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl ZJ_city_3314_yuhang_spider -a sdt=2021-03-01 -a edt=2021-03-31".split(" "))
    # cmdline.execute("scrapy crawl ZJ_city_3314_yuhang_spider".split(" "))
