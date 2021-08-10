# @file           :ZJ_city_3356_jinhuayiwu_spider.py
# @description    :浙江省金华义乌市公共资源交易中心
# @date           :2021/07/26 11:24:29
# @author         :miaokela
# @version        :1.0
import re
import requests
from lxml import etree
import random
from datetime import datetime

import scrapy

from spider_pro import utils, constans, items


class ZjCity3356JinhuayiwuSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_3356_jinhuayiwu_spider'
    allowed_domains = ['ggfw.ywjypt.yw.gov.cn']
    start_urls = ['http://ggfw.ywjypt.yw.gov.cn/']
    query_url = 'http://ggfw.ywjypt.yw.gov.cn'

    basic_area = '浙江省金华义乌市公共资源交易中心'
    area_id = 3356
    keywords_map = {
        '采购意向|需求公示': '招标预告',
        '单一来源|询价|竞争性谈判|竞争性磋商': '招标公告',
        '澄清|变更|补充|取消|更正|延期': '招标变更',
        '流标|废标|终止|中止': '招标异常',
        '候选人': '中标预告',
    }
    url_map = {
        '招标预告': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001016/list3gc.html'},  # 招标文件公示
            {'category': '政府采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070002/070002004/list3.html'},  # 意见征询
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008007/list3qt.html'},  # 镇采预告
        ],
        '招标公告': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001001/list3gc.html'},  # 招标公告
            {'category': '政府采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070002/070002001/list3.html'},  # 采购项目公告
            {'category': '土地矿产交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070003/070003004/list3.html'},  # 出让公告
            {'category': '国有产权交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070004/070004001/list3.html'},  # 交易公告
            {'category': '农村产权交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070006/070006001/list3.html'},  # 交易公告
            {'category': '资源要素交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070007/070007001/list3.html'},  # 交易公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008001/list3qt.html'},  # 交易公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008004/list3qt.html'},  # 镇采公告
        ],
        '资格预审结果公告': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001002/list3gc.html'},  # 资审公告
        ],
        '招标变更': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001006/list3gc.html'},  # 更正公告
            {'category': '政府采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070002/070002003/list3.html'},  # 更正公告
            {'category': '土地矿产交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070003/070003003/list3.html'},  # 更正公告
            {'category': '国有产权交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070004/070004003/list3.html'},  # 更正公告
            {'category': '国企采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070005/070005002/list3.html'},  # 更正公告
            {'category': '农村产权交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070006/070006002/list3.html'},  # 更正公告
            {'category': '资源要素交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070007/070007002/list3.html'},  # 更正公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008002/list3qt.html'},  # 更正公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008005/list3qt.html'},  # 镇采变更
        ],
        '招标异常': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001007/list3gc.html'},  # 废标公告
        ],
        '中标预告': [
            {'category': '国企采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070005/070005006/list3.html'},  # 中标候选人公示
            {'category': '国企采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070005/070005010/list3.html'},  # 定标公示
        ],
        '中标公告': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001005/list3gc.html'},  # 中标结果公告
            {'category': '政府采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070002/070002002/list3.html'},  # 采购结果
            {'category': '土地矿产交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070003/070003002/list3.html'},  # 成交结果公布
            {'category': '国有产权交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070004/070004002/list3.html'},  # 成交公告
            {'category': '资源要素交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070007/070007003/list3.html'},  # 成交公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008003/list3qt.html'},  # 成交公告
            {'category': '其他交易', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070008/070008006/list3qt.html'},  # 镇采结果
        ],
        '其他公告': [
            {'category': '工程招投标', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070001/070001011/list3gc.html'},  # 合同签订公告
            {'category': '政府采购', 'url': 'http://ggfw.ywjypt.yw.gov.cn/jyxx/070002/070002006/list3.html'},  # 采购合同公告
        ]
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
        headers = ZjCity3356JinhuayiwuSpiderSpider.get_headers(resp)
        if all([self.start_time, self.end_time]):
            try:
                text = ''
                if method == 'GET':
                    text = requests.get(url=url, headers=headers, proxies=resp.meta.get('proxy') if resp else None).text
                if method == 'POST':
                    text = requests.post(url=url, data=kwargs.get(
                        'data'
                    ), headers=headers, proxies=resp.meta.get('proxy') if resp else None).text
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

                        _path = '//{ancestor_el}[contains(@{ancestor_attr},"{ancestor_val}")]{enhance_condition}/{child_el}[last()]/text()[not(normalize-space()="")]'.format(
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

                        # 解析出时间
                        t_com = re.compile('(\d+%s\d+%s\d+)' % (time_sep, time_sep))

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

    def start_requests(self):
        for notice_type, category_urls in self.url_map.items():
            for cu in category_urls:
                c_url = cu['url']
                yield scrapy.Request(url=c_url, callback=self.parse_list, meta={
                    'notice_type': notice_type,
                    'category': cu['category'],
                }, cb_kwargs={
                    'url': c_url,
                })

    def parse_list(self, resp, url):
        """
        - 获取最大页数
        - 翻页获取链接
        """
        end_href = resp.xpath(
            '//li[@class="ewb-page-li ewb-page-next"][last()]/a/@href').get()  # /jyxx/070001/070001001/194.html
        c_com = re.compile(r'/(\d+)\.html')

        try:
            max_page = c_com.findall(end_href)[0].strip()
            max_page = int(max_page)
        except Exception as e:
            self.logger.info(e)
        else:
            for i in range(1, max_page + 1):
                if i > 1:  # 第二页开始修改链接 正则替换
                    c_url = re.sub(r'/\w+\.html', '/{0}.html'.format(i + 1), url)
                else:
                    c_url = url
                judge_status = self.judge_in_interval(
                    c_url, method='GET', ancestor_el='ul', ancestor_attr='class',
                    ancestor_val='ewb-nbd-items',
                    child_el='li/span', resp=resp,
                )
                if judge_status == 0:
                    break
                elif judge_status == 2:
                    continue
                else:
                    yield scrapy.Request(url=c_url, callback=self.parse_urls, meta={
                        'notice_type': resp.meta.get('notice_type', ''),
                        'category': resp.meta.get('category', '')
                    }, priority=max_page - i)

    def parse_urls(self, resp):
        els = resp.xpath('//ul[contains(@class,"ewb-nbd-items")]/li')
        for n, el in enumerate(els):
            href = el.xpath(".//a/@href").get()
            if href:
                pub_time = el.xpath("./span[last()]/text()").get()
                if pub_time:
                    pub_time = pub_time.strip()
                if utils.check_range_time(self.start_time, self.end_time, pub_time)[0]:
                    d_url = ''.join([self.query_url, href])
                    yield scrapy.Request(url=d_url, callback=self.parse_detail, meta={
                        'notice_type': resp.meta.get('notice_type'),
                        'category': resp.meta.get('category'),
                        'pub_time': pub_time,
                    }, priority=(len(els)-n)*1000)

    def parse_detail(self, resp):
        content = resp.xpath('//div[@class="news-article-para"]').get()
        title_name = resp.xpath('//h6[@class="news-article-tt"]/text()').get()

        # 标题携带 重要通知 开标记录公示 测试 不采集
        if not any(["重要通知" in title_name, "开标记录公示" in title_name, "测试" in title_name]):
            notice_type_ori = resp.meta.get('notice_type')

            # 关键字重新匹配 notice_type
            matched, match_notice_type = self.match_title(title_name)
            if matched:
                notice_type_ori = match_notice_type

            notice_types = list(
                filter(lambda k: constans.TYPE_NOTICE_DICT[k] == notice_type_ori, constans.TYPE_NOTICE_DICT)
            )

            # 匹配文件
            _, files_path = utils.catch_files(content, self.query_url, pub_time=resp.meta.get('pub_time'))

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

    # cmdline.execute("scrapy crawl ZJ_city_3356_jinhuayiwu_spider -a sdt=2021-06-01 -a edt=2021-07-20".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3356_jinhuayiwu_spider".split(" "))
