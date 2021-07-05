# -*- coding: utf-8 -*-
"""
@file          :qcc_crawler.py
@description   :企查查
@date          :2021/05/29 08:41:16
@author        :miaokela
@version       :1.0
"""
import scrapy
import re
import random
import requests
import json
from lxml import etree

from scrapy.utils.project import get_project_settings

from spider_pro import items
from spider_pro.extra_spiders.public import db


class QccCrawlerSpider(scrapy.Spider):
    name = 'qcc_crawler'
    area_id = 9999999
    allowed_domains = ['www.qcc.com']
    start_urls = ['http://www.qcc.com/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'spider_pro.pipelines.pipelines_extra.ExtraPipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 'spider_pro.middlewares.DelayedRequestMiddleware.DelayedRequestMiddleware': 50,
            'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
            'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 100,
            # 'spider_pro.middlewares.RefererMiddleware.RefererMiddleware': 400,
        },
        'DOWNLOAD_DELAY': 2,
        'CONCURREN_REQUESTS': 8,
        'CONCURRENT_RTEQUESTS_PER_IP': 8,
        "ENABLE_PROXY_USE": True,
        # "ENABLE_PROXY_USE": False,
        "COOKIES_ENABLED": False,  # 禁用cookie 避免cookie反扒
        'RETRY_TIMES': 5,
    }
    query_url = 'https://www.qcc.com/gongsi_industry?industryCode={industryCode}&subIndustryCode={subIndustryCode}&p={page}'
    # start_url = 'https://www.qcc.com/industry_A'
    basic_url = 'https://www.qcc.com'
    basic_info_re = '统一社会信用代码,(?P<统一社会信用代码>.*?),企业名称,(?P<企业名称>.*?),法定代表人,(?P<法定代表人>.*?),' \
                    '登记状态,(?P<登记状态>.*?),成立日期,(?P<成立日期>.*?),注册资本,(?P<注册资本>.*?),' + \
                    '实缴资本,(?P<实缴资本>.*?),核准日期,(?P<核准日期>.*?),组织机构代码,(?P<组织机构代码>.*?),' \
                    '工商注册号,(?P<工商注册号>.*?),纳税人识别号,(?P<纳税人识别号>.*?),企业类型,(?P<企业类型>.*?),' \
                    '营业期限,(?P<营业期限始>.*?)至(?P<营业期限末>.*?),纳税人资质,(?P<纳税人资质>.*?),所属行业,(?P<行业>.*?),' \
                    '所属地区,(?P<所属地区>.*?),登记机关,(?P<登记机关>.*?),人员规模,(?P<人员规模>.*?),参保人数,(?P<参保人数>.*?),' + \
                    '曾用名,(?P<曾用名>.*?),英文名,(?P<英文名>.*?),进出口企业代码,(?P<进出口企业代码>.*?),' \
                    '注册地址,(?P<注册地址>.*?),经营范围,(?P<经营范围>.*)'
    settings = get_project_settings()
    debug = settings.get('DEBUG_MODE', True)
    # debug = False
    db_name = settings.get('MYSQL_TEST_DB_NAME', '') if debug else settings.get('MYSQL_DB_NAME', '')
    search_url = 'https://www.qcc.com/web/search?key={key}'

    node_tree = [
        {
            'category': 'A',
            'category_name': '农、林、牧、渔业',
            'industry_category_list': [
                {'industry_category': '01', 'industory_category_name': '农业', 'url': '/industry_A_01'},
                {'industry_category': '02', 'industory_category_name': '林业', 'url': '/industry_A_02'},
                {'industry_category': '03', 'industory_category_name': '畜牧业', 'url': '/industry_A_03'},
                {'industry_category': '04', 'industory_category_name': '渔业', 'url': '/industry_A_04'},
                {'industry_category': '05', 'industory_category_name': '农、林、牧、渔专业及辅助性活动', 'url': '/industry_A_05'},
            ]
        },
        {
            'category': 'B',
            'category_name': '采矿业',
            'industry_category_list': [
                {'industry_category': '06', 'industory_category_name': '煤炭开采和洗选业', 'url': '/industry_B_06'},
                {'industry_category': '07', 'industory_category_name': '石油和天然气开采业', 'url': '/industry_B_07'},
                {'industry_category': '08', 'industory_category_name': '黑色金属矿采选业', 'url': '/industry_B_08'},
                {'industry_category': '09', 'industory_category_name': '有色金属矿采选业', 'url': '/industry_B_09'},
                {'industry_category': '10', 'industory_category_name': '非金属矿采选业', 'url': '/industry_B_10'},
                {'industry_category': '11', 'industory_category_name': '开采专业及辅助性活动', 'url': '/industry_B_11'},
                {'industry_category': '12', 'industory_category_name': '其他采矿业', 'url': '/industry_B_12'},
            ]
        },
        {
            'category': 'C',
            'category_name': '制造业',
            'industry_category_list': [
                {'industry_category': '13', 'industory_category_name': '农副食品加工业', 'url': '/industry_C_13'},
                {'industry_category': '14', 'industory_category_name': '食品制造业', 'url': '/industry_C_14'},
                {'industry_category': '15', 'industory_category_name': '酒、饮料和精制茶制造业', 'url': '/industry_C_15'},
                {'industry_category': '16', 'industory_category_name': '烟草制品业', 'url': '/industry_C_16'},
                {'industry_category': '17', 'industory_category_name': '纺织业', 'url': '/industry_C_17'},
                {'industry_category': '18', 'industory_category_name': '纺织服装、服饰业', 'url': '/industry_C_18'},
                {'industry_category': '19', 'industory_category_name': '皮革、毛皮、羽毛及其制品和制鞋业', 'url': '/industry_C_19'},
                {'industry_category': '20', 'industory_category_name': '木材加工和木、竹、藤、棕、草制品业', 'url': '/industry_C_20'},
                {'industry_category': '21', 'industory_category_name': '家具制造业', 'url': '/industry_C_21'},
                {'industry_category': '22', 'industory_category_name': '造纸和纸制品业', 'url': '/industry_C_22'},
                {'industry_category': '23', 'industory_category_name': '印刷和记录媒介复制业', 'url': '/industry_C_23'},
                {'industry_category': '24', 'industory_category_name': '文教、工美、体育和娱乐用品制造业', 'url': '/industry_C_24'},
                {'industry_category': '25', 'industory_category_name': '石油、煤炭及其他燃料加工业', 'url': '/industry_C_25'},
                {'industry_category': '26', 'industory_category_name': '化学原料和化学制品制造业', 'url': '/industry_C_26'},
                {'industry_category': '27', 'industory_category_name': '医药制造业', 'url': '/industry_C_27'},
                {'industry_category': '28', 'industory_category_name': '化学纤维制造业', 'url': '/industry_C_28'},
                {'industry_category': '29', 'industory_category_name': '橡胶和塑料制品业', 'url': '/industry_C_29'},
                {'industry_category': '30', 'industory_category_name': '非金属矿物制品业', 'url': '/industry_C_30'},
                {'industry_category': '31', 'industory_category_name': '黑色金属冶炼和压延加工业', 'url': '/industry_C_31'},
                {'industry_category': '32', 'industory_category_name': '有色金属冶炼和压延加工业', 'url': '/industry_C_32'},
                {'industry_category': '33', 'industory_category_name': '金属制品业', 'url': '/industry_C_33'},
                {'industry_category': '34', 'industory_category_name': '通用设备制造业', 'url': '/industry_C_34'},
                {'industry_category': '35', 'industory_category_name': '专用设备制造业', 'url': '/industry_C_35'},
                {'industry_category': '36', 'industory_category_name': '汽车制造业', 'url': '/industry_C_36'},
                {'industry_category': '37', 'industory_category_name': '铁路、船舶、航空航天和其他运输设备制造业', 'url': '/industry_C_37'},
                {'industry_category': '38', 'industory_category_name': '电气机械和器材制造业', 'url': '/industry_C_38'},
                {'industry_category': '39', 'industory_category_name': '计算机、通信和其他电子设备制造业', 'url': '/industry_C_39'},
                {'industry_category': '40', 'industory_category_name': '仪器仪表制造业', 'url': '/industry_C_40'},
                {'industry_category': '41', 'industory_category_name': '其他制造业', 'url': '/industry_C_41'},
                {'industry_category': '42', 'industory_category_name': ' 废弃资源综合利用业', 'url': '/industry_C_42'},
                {'industry_category': '43', 'industory_category_name': '金属制品、机械和设备修理业', 'url': '/industry_C_43'},
            ]
        },
        {
            'category': 'D',
            'category_name': '电力、热力、燃气及水生产和供应业',
            'industry_category_list': [
                {'industry_category': '44', 'industory_category_name': '电力、热力生产和供应业', 'url': '/industry_D_44'},
                {'industry_category': '45', 'industory_category_name': '电力、热力生产和供应业', 'url': '/industry_D_45'},
                {'industry_category': '46', 'industory_category_name': '电力、热力生产和供应业', 'url': '/industry_D_46'},
            ]
        },
        {
            'category': 'E',
            'category_name': '建筑业',
            'industry_category_list': [
                {'industry_category': '47', 'industory_category_name': '房屋建筑业', 'url': '/industry_E_47'},
                {'industry_category': '48', 'industory_category_name': '土木工程建筑业', 'url': '/industry_E_48'},
                {'industry_category': '49', 'industory_category_name': '建筑安装业', 'url': '/industry_E_49'},
                {'industry_category': '50', 'industory_category_name': '建筑装饰、装修和其他建筑业', 'url': '/industry_E_50'},
            ]
        },
        {
            'category': 'F',
            'category_name': '批发和零售业',
            'industry_category_list': [
                {'industry_category': '51', 'industory_category_name': '批发业', 'url': '/industry_F_51'},
                {'industry_category': '52', 'industory_category_name': '零售业', 'url': '/industry_F_52'},
            ]
        },
        {
            'category': 'G',
            'category_name': '交通运输、仓储和邮政业',
            'industry_category_list': [
                {'industry_category': '53', 'industory_category_name': '铁路运输业', 'url': '/industry_G_53'},
                {'industry_category': '54', 'industory_category_name': '道路运输业', 'url': '/industry_G_54'},
                {'industry_category': '55', 'industory_category_name': '水上运输业', 'url': '/industry_G_55'},
                {'industry_category': '56', 'industory_category_name': '航空运输业', 'url': '/industry_G_56'},
                {'industry_category': '57', 'industory_category_name': '管道运输业', 'url': '/industry_G_57'},
                {'industry_category': '58', 'industory_category_name': '多式联运和运输代理业', 'url': '/industry_G_58'},
                {'industry_category': '59', 'industory_category_name': '装卸搬运和仓储业', 'url': '/industry_G_59'},
                {'industry_category': '60', 'industory_category_name': '邮政业', 'url': '/industry_G_60'},
            ]
        },
        {
            'category': 'H',
            'category_name': '住宿和餐饮业',
            'industry_category_list': [
                {'industry_category': '61', 'industory_category_name': '住宿业', 'url': '/industry_H_61'},
                {'industry_category': '62', 'industory_category_name': '餐饮业', 'url': '/industry_H_62'},
            ]
        },
        {
            'category': 'I',
            'category_name': '信息传输、软件和信息技术服务业',
            'industry_category_list': [
                {'industry_category': '63', 'industory_category_name': '电信、广播电视和卫星传输服务', 'url': '/industry_I_63'},
                {'industry_category': '64', 'industory_category_name': '互联网和相关服务', 'url': '/industry_I_64'},
                {'industry_category': '65', 'industory_category_name': '软件和信息技术服务业', 'url': '/industry_I_65'},
            ]
        },
        {
            'category': 'J',
            'category_name': '金融业',
            'industry_category_list': [
                {'industry_category': '66', 'industory_category_name': '货币金融服务', 'url': '/industry_J_66'},
                {'industry_category': '67', 'industory_category_name': '资本市场服务', 'url': '/industry_J_67'},
                {'industry_category': '68', 'industory_category_name': '保险业', 'url': '/industry_J_68'},
                {'industry_category': '69', 'industory_category_name': '其他金融业', 'url': '/industry_J_69'},
            ]
        },
        {
            'category': 'K',
            'category_name': '房地产业',
            'industry_category_list': [
                {'industry_category': '70', 'industory_category_name': '房地产业', 'url': '/industry_K_70'},
            ]
        },
        {
            'category': 'L',
            'category_name': '租赁和商务服务业',
            'industry_category_list': [
                {'industry_category': '71', 'industory_category_name': '租赁业', 'url': '/industry_L_71'},
                {'industry_category': '72', 'industory_category_name': '商务服务业', 'url': '/industry_L_72'},
            ]
        },
        {
            'category': 'M',
            'category_name': '科学研究和技术服务业',
            'industry_category_list': [
                {'industry_category': '73', 'industory_category_name': '研究和试验发展', 'url': '/industry_M_73'},
                {'industry_category': '74', 'industory_category_name': '专业技术服务业', 'url': '/industry_M_74'},
                {'industry_category': '75', 'industory_category_name': '科技推广和应用服务业', 'url': '/industry_M_75'},
            ]
        },
        {
            'category': 'N',
            'category_name': '水利、环境和公共设施管理业',
            'industry_category_list': [
                {'industry_category': '76', 'industory_category_name': '水利管理业', 'url': '/industry_N_76'},
                {'industry_category': '77', 'industory_category_name': '生态保护和环境治理业', 'url': '/industry_N_77'},
                {'industry_category': '78', 'industory_category_name': '公共设施管理业', 'url': '/industry_N_78'},
                {'industry_category': '79', 'industory_category_name': '土地管理业', 'url': '/industry_N_79'},
            ]
        },
        {
            'category': 'O',
            'category_name': '居民服务、修理和其他服务业',
            'industry_category_list': [
                {'industry_category': '80', 'industory_category_name': '居民服务业', 'url': '/industry_O_80'},
                {'industry_category': '81', 'industory_category_name': '机动车、电子产品和日用产品修理业', 'url': '/industry_O_81'},
                {'industry_category': '82', 'industory_category_name': '其他服务业', 'url': '/industry_O_82'},
            ]
        },
        {
            'category': 'P',
            'category_name': '教育',
            'industry_category_list': [
                {'industry_category': '83', 'industory_category_name': '教育', 'url': '/industry_P_83'},
            ]
        },
        {
            'category': 'Q',
            'category_name': '卫生和社会工作',
            'industry_category_list': [
                {'industry_category': '84', 'industory_category_name': '卫生', 'url': '/industry_Q_84'},
                {'industry_category': '85', 'industory_category_name': '社会工作', 'url': '/industry_Q_85'},
            ]
        },
        {
            'category': 'R',
            'category_name': '文化、体育和娱乐业',
            'industry_category_list': [
                {'industry_category': '86', 'industory_category_name': '新闻和出版业', 'url': '/industry_R_86'},
                {'industry_category': '87', 'industory_category_name': '广播、电视、电影和录音制作业', 'url': '/industry_R_87'},
                {'industry_category': '88', 'industory_category_name': '文化艺术业', 'url': '/industry_R_88'},
                {'industry_category': '89', 'industory_category_name': '体育', 'url': '/industry_R_89'},
                {'industry_category': '90', 'industory_category_name': '娱乐业', 'url': '/industry_R_90'},
            ]
        },
        {
            'category': 'S',
            'category_name': '公共管理、社会保障和社会组织',
            'industry_category_list': [
                {'industry_category': '91', 'industory_category_name': '中国共产党机关', 'url': '/industry_S_91'},
                {'industry_category': '92', 'industory_category_name': '国家机构', 'url': '/industry_S_92'},
                {'industry_category': '93', 'industory_category_name': '人民政协、民主党派', 'url': '/industry_S_93'},
                {'industry_category': '94', 'industory_category_name': '社会保障', 'url': '/industry_S_94'},
                {'industry_category': '95', 'industory_category_name': '群众团体、社会团体和其他成员组织', 'url': '/industry_S_95'},
                {'industry_category': '96', 'industory_category_name': '基层群众自治组织及其他组织', 'url': '/industry_S_96'},
            ]
        },
        {
            'category': 'T',
            'category_name': '国际组织',
            'industry_category_list': [
                {'industry_category': '97', 'industory_category_name': '国际组织', 'url': '/industry_T_97'},
            ]
        },
    ]

    @staticmethod
    def remove_specific_element(content, ele_name, attr_name, attr_value, if_child=False, index=1, text='', **kwargs):
        """
        remove specific html element attribute from content
        params:
            @content: html文档
            @ele_name: 元素名称
            @attr_name: 元素属性名
            @attr_value: 元素属性值
            @index: 指定元素索引删除
            @text: 指定包含文本的子节点删除
            @kwargs: if_child 移除的是否子元素
                    child_attr 子元素名称
        """
        msg = ''
        try:
            doc = etree.HTML(content)
            els = doc.xpath('//{ele_name}'.format(**{
                'ele_name': ele_name,
            }))

            if attr_name:
                same = 1
                for el in els:
                    if attr_value in el.get(attr_name, ''):
                        if if_child:
                            child_attr = kwargs.get('child_attr')

                            # if not text:
                            child_els = el.xpath(
                                './/{child_attr}'.format(**{'child_attr': child_attr}))

                            if not text:
                                for n, child_el in enumerate(child_els):
                                    if n == index - 1:
                                        child_el.getparent().remove(child_el)
                                        break
                            else:
                                for child_el in child_els:
                                    child_el_text = ','.join(
                                        child_el.xpath('.//text()'))
                                    if text in child_el_text:
                                        child_el.getparent().remove(child_el)
                                        break
                        else:
                            if index:
                                if same == index:
                                    el.getparent().remove(el)
                                    break
                                same += 1
                            else:  # index = 0 删除所有匹配节点
                                el.getparent().remove(el)
                content = etree.tounicode(doc)
            else:  # 无属性元素 指定索引删除
                for n, el in enumerate(els):
                    if n + 1 == index:
                        el.getparent().remove(el)
        except Exception as e:
            msg = e

        return msg, content.replace('<html><body>', '').replace('</body></html>', '')

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    @property
    def db_query(self):
        debug = self.settings.get('DEBUG_MODE', True)
        db_name = self.settings.get('MYSQL_TEST_DB_NAME', '') if debug else self.settings.get(
            'MYSQL_DB_NAME', ''
        )
        dbq = db.DBQuery(**{
            'host': self.settings.get('MYSQL_IP', ''),
            'user': self.settings.get('MYSQL_USER_NAME', ''),
            'password': self.settings.get('MYSQL_PASSWORD', ''),
            'db': db_name,
        })
        return dbq

    # def start_requests(self):
    #     """
    #     3种方式采集：
    #         - 列表顺序采集
    #         - 自补充发票信息 根据origin匹配
    #         - 代理信息中企业信息采集
    #     """
    #     methods = ['origin', 'agency', 'order']
    #     for method in methods:
    #         # c_url = ''
    #         if method == 'order':
    #             yield scrapy.Request(url=self.query_url.format(**{
    #                 'industryCode': '',
    #                 'subIndustryCode': '',
    #                 'page': '',
    #             }), callback=self.parse_category, meta={
    #                 'tag': method,
    #             })
    #
    #         # if method in ['origin', 'agency']:
    #             # dbq = self.db_query
    #
    #             # companies = []
    #             # if method == 'origin':
    #             #     qcc_sql = sql.COMPANY_NAMES_WITHOUT_ORIGIN.format(
    #             #         db_name=self.db_name, table_name='QCC_qcc_crawler'
    #             #     )
    #             #     companies = dbq.fetch_all(qcc_sql)
    #
    #             # if method == 'agency':
    #             #     qcc_sql = sql.COMPANY_NAMES_FROM_AGENT.format(
    #             #         db_name=self.db_name, table_name='quanguo'
    #             #     )
    #             #     companies = dbq.fetch_all(qcc_sql)
    #             # if method == 'agency':
    #             #     qcc_sql = sql.AGENCY_NOT_IN_QCC
    #             #     companies = dbq.fetch_all(qcc_sql)
    #             # del dbq
    #
    #             # for n, company in enumerate(companies):
    #             #     c_name = company.get('company_name', '')
    #
    #             #     c_url = self.search_url.format(key=c_name)
    #
    #             #     if c_url:
    #             #         yield scrapy.Request(
    #             #             url=c_url, callback=self.parse_search_list, priority=10 * (len(companies) - n), meta={
    #             #                 'tag': method,
    #             #                 'company': c_name,
    #             #             },
    #             #         )
    #
    # def parse_search_list(self, resp):
    #     doc = etree.HTML(resp.text)
    #     detail_xpath = '//div[@class="maininfo"]//a/@href'
    #     detail_urls = doc.xpath(detail_xpath)
    #     if detail_urls:
    #         detail_url = detail_urls[0]
    #
    #         yield scrapy.Request(url=detail_url, callback=self.parse_item, priority=1000000, meta={
    #             'tag': resp.meta.get('tag', ''),
    #             'company': resp.meta.get('company', '')
    #         })
    #
    # def parse_category(self, resp):
    #     """
    #     行业分类
    #     """
    #     category_els = resp.xpath('//div[@class="row"]/div/div/div[1]//div[@class="pills-after"]/a')
    #
    #     com = re.compile('industry_(.*)')
    #
    #     # for category_el in category_els[0:1]:
    #     for n, category_el in enumerate(category_els):
    #         if n < 1:
    #             href = category_el.xpath('./@href').get()
    #             category_name = category_el.xpath('./text()').get()
    #
    #             category_url = ''.join([self.basic_url, href])
    #
    #             categories = com.findall(href)
    #             if categories:
    #                 category = categories[0]
    #
    #                 yield scrapy.Request(url=category_url, callback=self.parse_industry_categories, meta={
    #                     'category': category,
    #                     'category_name': category_name,
    #                     'tag': resp.meta.get('tag', ''),
    #                 }, priority=len(category_els) - n)

    # def parse_industry_categories(self, resp):
    #     """
    #     行业大类
    #     """
    #     industry_category_els = resp.xpath('//div[@class="row"]/div/div/div[2]//div[@class="pills-after"]/a')
    #
    #     com = re.compile('(\d+)')
    #
    #     # for industry_category_el in industry_category_els[0:1]:
    #     for n, industry_category_el in enumerate(industry_category_els):
    #         if n < 1:
    #             href = industry_category_el.xpath('./@href').get()
    #             industry_category_name = industry_category_el.xpath('./text()').get()
    #
    #             # 获取分页
    #             industry_category_url = ''.join([self.basic_url, href])
    #
    #             industry_categories = com.findall(href)
    #
    #             if industry_categories:
    #                 industry_category = industry_categories[0]
    #
    #                 yield scrapy.Request(url=industry_category_url, callback=self.parse_list, meta={
    #                     'category': resp.meta.get('category', ''),
    #                     'industry_category': industry_category,
    #
    #                     'category_name': resp.meta.get('category_name', ''),
    #                     'industry_category_name': industry_category_name,
    #
    #                     'tag': resp.meta.get('tag', ''),
    #                 }, priority=len(industry_category_els) - n)

    def start_requests(self):
        """
        节点树
        :return:
        """
        for i, node in enumerate(self.node_tree):
            category = node.get('category', '')
            category_name = node.get('category_name', '')
            industry_category_list = node.get('industry_category_list', [])

            for j, industry_category_node in enumerate(industry_category_list):
                industry_category = industry_category_node.get('industry_category', '')
                industry_category_name = industry_category_node.get('industory_category_name', '')
                c_url = industry_category_node.get('url', '')
                url = ''.join([self.basic_url, c_url])
                yield scrapy.Request(url=url, callback=self.parse_list, meta={
                    'category': category,
                    'industry_category': industry_category,

                    'category_name': category_name,
                    'industry_category_name': industry_category_name,
                }, priority=len(self.node_tree) - i)

    def parse_list(self, resp):
        """
        获取最大分页 获取所有列表页
        """
        max_page = resp.xpath('//ul[@class="pagination pagination-md"]//a[@class="end"]/text()').get()
        category = resp.meta.get('category', '')
        industry_category = resp.meta.get('industry_category', '')
        try:
            max_page = int(max_page)
        except (ValueError, IndexError, TypeError) as e:
            self.logger.info('error:{e}'.format(e=e))
        else:
            # for page in range(1, 2):
            if max_page > 10:  # 只抓10 页
                max_page = 10

            for page in range(1, max_page + 1):
                list_url = self.query_url.format(**{
                    'industryCode': category,
                    'subIndustryCode': industry_category,
                    'page': page,
                })
                yield scrapy.Request(url=list_url, callback=self.parse_detail, meta={
                    'category': resp.meta.get('category', ''),
                    'industry_category': resp.meta.get('industry_category', ''),

                    'category_name': resp.meta.get('category_name', ''),
                    'industry_category_name': resp.meta.get('industry_category_name', ''),

                    'tag': resp.meta.get('tag', ''),
                }, priority=max_page - page)

    def parse_detail(self, resp):
        """
        解析详情页地址
        """
        detail_urls = resp.xpath('//section[@id="searchlist"]/table//tr/td[2]/a/@href').extract()
        for n, detail_url in enumerate(detail_urls):
            c_url = ''.join([self.basic_url, detail_url])

            yield scrapy.Request(url=c_url, callback=self.parse_item, meta={
                'category': resp.meta.get('category', ''),
                'industry_category': resp.meta.get('industry_category', ''),

                'category_name': resp.meta.get('category_name', ''),
                'industry_category_name': resp.meta.get('industry_category_name', ''),

                'tag': resp.meta.get('tag', ''),
            }, priority=len(detail_urls) - n)

    @classmethod
    def get_invoice_info(cls, resp):
        """
        获取发票信息
            https://www.qcc.com/firm/ed9e3157b77b7f5a1a846132da93b626.html 提取出 keyno 拼接链接
            https://www.qcc.com/tax_view?keyno=225093b0546c258a4128f2c2f30bb6d0&ajaxflag=1
        :param resp:
        :return:
        """
        error = ''
        referer_url = resp.url
        com = re.compile(r'firm/(.*?)\.html')
        key_no = com.findall(referer_url)

        url = 'https://www.qcc.com/tax_view?keyno={keyno}&ajaxflag=1'.format(keyno=key_no[0]) if key_no else ''

        invoice_info_dict = {}
        if url:
            headers = cls.get_headers(resp)
            proxy = resp.meta.get('proxy', {})
            proxies = {}
            if proxy:
                if proxy.startswith('https'):
                    proxies = {'https': proxy}
                else:
                    proxies = {'http': proxy}

            try:
                text = requests.get(url=url, headers=headers, proxies=proxies, verify=False).text
                """
                {
                    data: {
                    "Name": "江门市姆斯皮园林绿化有限公司",
                    "CreditCode": "91440703MA51T6BYXY",
                    "Address": "江门市蓬江区江门万达广场16幢1506室之三",
                    "PhoneNumber": null,
                    "Bank": null,
                    "Bankaccount": null
                    },
                    success: true
                }
                """
                invoice_info = json.loads(text)
                success = invoice_info.get('success', False)
                if success:
                    data = invoice_info.get('data', {})
                    invoice_info_dict.update(**{
                        'credit_code': data.get('CreditCode', ''),
                        'address': data.get('Address', ''),
                        'phone_number': data.get('PhoneNumber', ''),
                        'bank': data.get('Bank', ''),
                        'bank_account': data.get('Bankaccount', ''),
                    })
            except Exception as e:
                error = 'ERROR:{0}'.format(e)
        else:
            error = 'ERROR: 缺少key_no.'
        return error, {k: v if v else '' for k, v in invoice_info_dict.items()}

    def parse_item(self, resp):   
        content = resp.text
        
        _, content = QccCrawlerSpider.remove_specific_element(resp, 'span', 'class', 'headimg')
           
        c_doc = etree.HTML(content)

        c_els = c_doc.xpath('//section[@id="cominfo"]//table//td')
        t = []
        for el in c_els:
            t.append(''.join(
                el.xpath('.//text()')
            ).strip().replace(' ', '').replace('\n', ''))

        data = ','.join(t)

        com = re.compile(self.basic_info_re)

        ret = [m.groupdict() for m in re.finditer(com, data)]
        if ret:
            company_info = ret[0]

            company_info_items = {
                'company_name': company_info.get('企业名称', ''),
                'location': company_info.get('所属地区', ''),
                'legal_representative': company_info.get('法定代表人', ''),
                'date_of_establishment': company_info.get('成立日期', ''),
                'operating_status': company_info.get('登记状态', ''),
                'registered_capital': company_info.get('注册资本', ''),
                'paid_in_capital': company_info.get('实缴资本', ''),
                'unified_social_credit_code': company_info.get('统一社会信用代码', ''),
                'business_registration_number': company_info.get('工商注册号', ''),
                'organization_code': company_info.get('组织机构代码', ''),
                'taxpayer_identification_number': company_info.get('纳税人识别号', ''),
                'taxpayer_qualification': company_info.get('纳税人资质', ''),
                'type_of_enterprise': company_info.get('企业类型', ''),
                'industry': company_info.get('行业', ''),
                'operating_period_std': company_info.get('营业期限始', ''),
                'operating_period_edt': company_info.get('营业期限末', ''),
                'staff_size': company_info.get('人员规模', ''),
                'number_of_participants': company_info.get('参保人数', ''),
                'english_name': company_info.get('英文名', ''),
                'former_name': company_info.get('曾用名', ''),
                'registration_authority': company_info.get('登记机关', ''),
                'approved_date': company_info.get('核准日期', ''),
                'registered_address': company_info.get('注册地址', ''),
                'business_scope': company_info.get('经营范围', ''),
                'import_and_export_enterprise_code': company_info.get('进出口企业代码', ''),
                'category': resp.meta.get('category_name', ''),
                'industry_category': resp.meta.get('industry_category_name', ''),
                'origin': resp.url,
            }

            err, invoice_info = QccCrawlerSpider.get_invoice_info(resp)

            if err:
                self.logger.info(err)
            else:
                company_info_items.update(**invoice_info)
            """
            [{'统一社会信用代码': '-', '企业名称': '延吉市金鑫冷冻肉食食品经营部', '法定代表人': '许晓萍关联1家企业>', 
            '登记状态': '注销', '成立日期': '1988-08-30', '注册资本': '1万元人民币', '实缴资本': '-', '核准日期': '2449-10-26', 
            '组织机构代码': '-', '工商注册号': '244491026-2', '纳税人识别号': '-', '企业类型': '集体所有制', '营业期限始': '', 
            '营业期限末': '至无固定期限', '纳税人资质': '-', '行业': '农业', '所属地区': '吉林省', '登记机关': '延吉市工商行政管理局', 
            '人员规模': '-', '参保人数': '-', '曾用名': '-', '英文名': '-', '进出口企业代码': '-', '注册地址': '-', 
            '经营范围': '(依法须经批准的项目,经相关部门批准后方可开展经营活动)'}]
            """
            notice_item = items.QCCItem()
            notice_item.update(**company_info_items)
            self.logger.info(
                '关键词:{0}; 企业:{1}; 当前采集类型: {2}'.format(resp.meta.get('company', ''), company_info.get('企业名称', ''),
                                                      resp.meta.get('tag', '')))
            print('企业:{0}; 当前采集类型: {1}'.format(company_info.get('企业名称', ''), resp.meta.get('tag', '')))
            return notice_item
        else:
            self.logger.info('regular error.')


if __name__ == '__main__':
    from scrapy import cmdline

    cmdline.execute("scrapy crawl qcc_crawler".split(" "))
