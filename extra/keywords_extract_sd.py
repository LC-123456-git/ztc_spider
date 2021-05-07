"""
author: miaokela
Date: 2021-05-02 09:28:51
LastEditTime: 2021-05-03 10:00:07
Description: 提取招采进宝站点关键词: 山东
"""
import requests
import gevent
import re
from functools import wraps
from openpyxl import Workbook
from lxml import etree
from datetime import datetime


def time_count(func):
    @wraps(func)
    def inner(self):
        start_time = datetime.now()
        func(self)
        # 统计执行时间
        print((datetime.now() - start_time).total_seconds())

    return inner


class KeywordsExtract(object):
    """
    提取站点内容关键词
    """
    domain_url = 'http://sd.zcjb.com.cn/'  # 山东
    query_url = 'http://sd.zcjb.com.cn/cms/index.htm'
    # domain_url = 'http://ah.zcjb.com.cn/'  # 安徽
    # query_url = 'http://ah.zcjb.com.cn/cms/index.htm'
    # domain_url = 'http://xj.zcjb.com.cn'  # 新疆
    # query_url = 'http://xj.zcjb.com.cn/cms/index.htm'
    notice_types = ['招标公告', '采购公告', '中标公告', '成交公告', '公示公告']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    }
    title_list = ['城市', '代理公司', '联系人', '地址', '电话', '时间', '匹配规则', '地址']

    def __init__(self, f_name, r_plans):
        self.msg = ''
        self.pages = []  # [{'url': '', 'page_num': ''}]
        self.detail_info = []  # [{'url': c_url,'city': city,'sub_time': sub_time}]
        self.excel_data = []
        self.file_name = f_name
        self.regular_plans = r_plans
        self.w = Workbook()
        self.ws = self.w.active

    def match_key_words(self, content, detail_url, city='', sub_time=''):
        """
        根据正则规则库循环匹配关键词
        Args:
            sub_time: 发布时间
            city: 城市
            detail_url: 访问地址
            content: 内容
        Returns:
        """
        agency, contacts, address, phone = '', '', '', ''
        c_regular = ''
        for rg in range(1, len(self.regular_plans) + 1):
            status, data = self.regular_match(content, rg)
            if status:
                agency = data.get('agency', '')
                contacts = data.get('contacts', '')
                address = data.get('address', '')
                phone = data.get('phone', '')
                c_regular = rg  # 匹配规则
                break

        # print(contacts, address, phone, c_regular, detail_url)
        print(contacts, '\n', address, '\n', phone, '\n', c_regular, '\n', detail_url, '\n')
        return [
            city,
            agency,
            contacts,
            address,
            phone,
            sub_time,
            c_regular if c_regular else '无',
            detail_url
        ]

    def regular_match(self, content, plan=0):
        """
        正则匹配字段内容
        Args:
            plan: 方案
            content:

        Returns:

        """
        status = False  # True表示获取成功 False表示获取失败
        data = {}
        doc = etree.HTML(content)
        p_els = doc.xpath('//div[@class="main-text"]/*')
        info_list = []
        for data_info in p_els:
            info = ''.join(data_info.xpath('.//text()'))
            info_list.append(info)

        text = ','.join(info_list).replace('\n', '').replace('\r\n', '')

        pl_reg = self.regular_plans.get(plan, '')
        if pl_reg:
            pl_com = re.compile(pl_reg)
            ret = [m.groupdict() for m in re.finditer(pl_com, text)]
            if ret:
                ret = ret[-1]
                data['agency'] = ret.get('agency', '')
                data['address'] = ret.get('address', '')
                data['phone'] = ret.get('phone')
                data['contacts'] = ret.get('contacts', '')
                status = True

        return status, data

    @classmethod
    def get_page(cls, url, method='GET', **kwargs):
        ret = ''
        headers = kwargs.get('headers', '')
        headers = headers if headers else cls.headers
        if method == 'GET':
            ret = requests.get(url=url, headers=headers).content.decode('utf-8')
        if method == 'POST':
            ret = requests.post(
                url=url, headers=headers, data=kwargs.get('data', {})
            ).content.decode('utf-8')
        return ret

    def get_notice_task(self, el):
        """
        招标类型对应的链接与分页数
        Args:
            el: 招标类型节点
        Returns:
        """
        try:
            notice_name = el.xpath('./span/text()')[0]
            notice_url = self.domain_url + el.xpath('./div/a/@href')[0]
        except Exception as e:
            self.msg = 'error:{e}'.format(e=e)
            print(self.msg)
        else:
            if notice_name in self.notice_types:
                ret = KeywordsExtract.get_page(notice_url)
                doc = etree.HTML(ret)
                page_nums = doc.xpath('//div[@class="pages"]/span[last()]/text()')

                self.pages.append({
                    'url': notice_url,
                    'page_num': page_nums[0] if page_nums else 0
                })

    def get_list_task(self, url, page):
        """
        获取所有详情页链接的任务
        Args:
            url: 列表页地址
            page: 分页数
        Returns:
        """
        data = {
            'pageNo': str(page),
            'city': '',
            'bidType': '',
            'timeType': ''
        }
        headers = dict(self.headers, **{'Referer': url})
        ret = self.get_page(url, method='POST', data=data, headers=headers)

        doc = etree.HTML(ret)

        els = doc.xpath('//div[@class="infolist-main bidlist"]//a')

        for el in els:
            c_url = self.domain_url + el.attrib.get('href')
            city = el.xpath('.//span[contains(@class, "bidLink3")]//text()')
            city = ''.join(city).strip()[1:-1]
            sub_time = el.xpath('./em/text()')
            sub_time = sub_time[0] if sub_time else ''
            # print(c_url)
            self.detail_info.append({
                'url': c_url,
                'city': city,
                'sub_time': sub_time,
            })

    def parse_els(self):
        """
        根据节点类型 获取节点链接
        Returns:
            @el_urls: 节点链接 主入口
        """
        self.pages = []  # 置空
        content = KeywordsExtract.get_page(self.query_url)
        try:
            doc = etree.HTML(content)
            els = doc.xpath('//div[@class="slideTxt slideBlock"]/div[1]/ul/li')
            gevent.joinall([gevent.spawn(self.get_notice_task, el) for el in els])

        except Exception as e:
            self.msg = 'error:{e}'.format(e=e)
            print(self.msg)
        return self.pages

    def parse_list(self, pages):
        """
        获取所有详情页链接
        Args:
            pages:
        Returns:
        """
        tasks = []
        for page in pages:
            page_num = page['page_num']
            url = page['url']

            try:
                page_num = int(page_num)
            except ValueError as e:
                self.msg = 'error:{e}'.format(e=e)
            else:
                for p in range(1, page_num + 1):
                    tasks.append(gevent.spawn(self.get_list_task, url, p))
        gevent.joinall(tasks)

    def parse_items(self, detail_info):
        """
        解析详情页 根据正则匹配指定关键字
        Args:
            detail_info: 详情页相关参数
        Returns:
        """
        url = detail_info['url']
        city = detail_info['city']
        sub_time = detail_info['sub_time']

        text = self.get_page(url)

        # 循环匹配规则
        ret = self.match_key_words(text, url, city=city, sub_time=sub_time)
        # 城市、代理公司、联系人、地址、电话、时间、参考业务量

        # 写入excel
        self.ws.append(ret)
        self.w.save(filename=self.file_name)

    @time_count
    def run(self):
        # 栏目
        for n, title in enumerate(self.title_list):
            self.ws.cell(row=1, column=n + 1, value=title)

        # 站点主入口
        pages = self.parse_els()

        # 翻页 列表页
        self.parse_list(pages)

        # 处理详情页信息
        gevent.joinall([gevent.spawn(self.parse_items, di) for di in self.detail_info])

    def check_web(self, url):
        """
        检测单页面匹配情况
        Args:
            url: 详情页地址
        Returns:
        """
        text = self.get_page(url)
        # 循环匹配规则
        self.match_key_words(text, url)


if __name__ == '__main__':
    # 优先级设置： 关键字多排在前
    regular_plans = {  # 正则必须命名:agency, contacts, address, phone
        # 1: '代理机构[:|：](?P<agency>.*?)[,|，]地.*?址.*?地.*?址[:|：](?P<address>.*?)[,|，].*?联系人.*?联系人[:|：](?P<contacts>.*?)[,|，|\s*].*?电.*?话.*?电.*?话[:|：](?P<phone>.*?)[,|，]',
        1: '代理机构[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+].*?电.*?话[:|：|\s+](?P<phone>.*?)[,|，]',
        2: '代理机构[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?电.*?话[:|：|\s+](?P<phone>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+]电子邮箱',
        3: '代理机构[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+].*电.*?话[:|：|\s+](?P<phone>.*?)[,|，]咨询电话',
        4: '代理机构[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+].*电.*?话[:|：|\s+](?P<phone>.*?)[,|，]若供应商',
        5: '代理机构[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+].*?[联系 \s*]电.*?话[:|：|\s+](?P<phone>.*?)[,|，]',
        6: '代理机构[:|：](?P<agency>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>[\u4E00-\u9FA5]{2,4})[123330-9 -]*.*?[,|，|\s+].*?电.*?话[:|：](?P<phone>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，]',
        7: '代理机构.*?名.*?称[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)[,|，].*?联系人[:|：](?P<contacts>.*?)[,|，|\s*].*电.*?话[:|：](?P<phone>.*?)[,|，].*?电子邮箱',
        8: '代理机构.*?名.*?称[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?)联.*?系.*?方.*?式[,|，].*?联系人[:|：](?P<contacts>.*?)[,|，|\s*].*?电.*?话[:|：](?P<phone>.*?)[,|，]',
        9: '代理机构.*?名.*?称[:|：](?P<agency>.*?)[,|，].*?地.*?址[:|：](?P<address>.*?).*?联.*?系.*?方.*?式[,|，].*?联系人[:|：](?P<contacts>.*?)[,|，|\s*].*?电.*?话[:|：](?P<phone>.*?)[,|，]',
        10: '代理机构[:|：](?P<agency>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s*]联系地址[:|：](?P<address>.*?)[,|，|\s*].*?联.*?系.*?电.*?话[:|：](?P<phone>.*?)[,|，]',
        11: '代理机构[:|：](?P<agency>.*?)[,|，].*?联.*?系.*?人[:|：](?P<contacts>.*?)[,|，|\s+].*?电.*?话[:|：](?P<phone>.*?)[,|，]',
    }
    # file_name = './新疆{date:%Y-%m-%d}.xls'.format(date=datetime.now())
    # file_name = './安徽{date:%Y-%m-%d}.xls'.format(date=datetime.now())
    file_name = './山东{date:%Y-%m-%d}.xls'.format(date=datetime.now())
    ke = KeywordsExtract(file_name, regular_plans)
    # ke.run()
    url = 'http://sd.zcjb.com.cn//cms/channel/zd8=zfcggg/2101468.htm'
    ke.check_web(url)
