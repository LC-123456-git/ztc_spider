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

from spider_pro import items


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
            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
            'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 100,
            'spider_pro.middlewares.DelayedRequestMiddleware.DelayedRequestMiddleware': 50,
            'spider_pro.middlewares.UrlDuplicateRemovalMiddleware.UrlDuplicateRemovalMiddleware': 300,
        }
    }
    query_url = 'https://www.qcc.com/gongsi_industry?industryCode={industryCode}&subIndustryCode={subIndustryCode}&p={page}'
    basic_url = 'http://www.qcc.com'
    basic_info_re = '统一社会信用代码,(?P<统一社会信用代码>.*?),企业名称,(?P<企业名称>.*?),法定代表人,(?P<法定代表人>.*?),' \
                    '登记状态,(?P<登记状态>.*?),成立日期,(?P<成立日期>.*?),注册资本,(?P<注册资本>.*?),' + \
                    '实缴资本,(?P<实缴资本>.*?),核准日期,(?P<核准日期>.*?),组织机构代码,(?P<组织机构代码>.*?),' \
                    '工商注册号,(?P<工商注册号>.*?),纳税人识别号,(?P<纳税人识别号>.*?),企业类型,(?P<企业类型>.*?),' \
                    '营业期限,(?P<营业期限始>.*?)至(?P<营业期限末>.*?),纳税人资质,(?P<纳税人资质>.*?),所属行业,(?P<行业>.*?),' \
                    '所属地区,(?P<所属地区>.*?),登记机关,(?P<登记机关>.*?),人员规模,(?P<人员规模>.*?),参保人数,(?P<参保人数>.*?),' + \
                    '曾用名,(?P<曾用名>.*?),英文名,(?P<英文名>.*?),进出口企业代码,(?P<进出口企业代码>.*?),' \
                    '注册地址,(?P<注册地址>.*?),经营范围,(?P<经营范围>.*)'

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    def start_requests(self):
        yield scrapy.Request(url=self.query_url, callback=self.parse_category)

    def parse_category(self, resp):
        """
        行业分类
        """
        category_els = resp.xpath('//div[@class="row"]/div/div/div[1]//div[@class="pills-after"]/a')

        com = re.compile('industry_(.*)')

        # for category_el in category_els[0:1]:
        for category_el in category_els:
            href = category_el.xpath('./@href').get()
            category_name = category_el.xpath('./text()').get()

            category_url = ''.join([self.basic_url, href])

            categories = com.findall(href)
            if categories:
                category = categories[0]

                yield scrapy.Request(url=category_url, callback=self.parse_industry_categories, meta={
                    'category': category,
                    'category_name': category_name,
                }, priority=10)

    def parse_industry_categories(self, resp):
        """
        行业大类
        """
        industry_category_els = resp.xpath('//div[@class="row"]/div/div/div[2]//div[@class="pills-after"]/a')

        com = re.compile('(\d+)')

        # for industry_category_el in industry_category_els[0:1]:
        for industry_category_el in industry_category_els:
            href = industry_category_el.xpath('./@href').get()
            industry_category_name = industry_category_el.xpath('./text()').get()

            # 获取分页
            industry_category_url = ''.join([self.basic_url, href])

            industry_categories = com.findall(href)

            if industry_categories:
                industry_category = industry_categories[0]

                yield scrapy.Request(url=industry_category_url, callback=self.parse_list, meta={
                    'category': resp.meta.get('category', ''),
                    'industry_category': industry_category,

                    'category_name': resp.meta.get('category_name', ''),
                    'industry_category_name': industry_category_name,
                }, priority=20)

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
            self.log('error:{e}'.format(e=e))
        else:
            # for page in range(1, 2):
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
                }, priority=30)

    def parse_detail(self, resp):
        """
        解析详情页地址
        """
        detail_urls = resp.xpath('//section[@id="searchlist"]/table//tr/td[2]/a/@href').extract()
        for detail_url in detail_urls:
            c_url = '/'.join([self.basic_url, detail_url])

            yield scrapy.Request(url=c_url, callback=self.parse_item, meta={
                'category': resp.meta.get('category', ''),
                'industry_category': resp.meta.get('industry_category', ''),

                'category_name': resp.meta.get('category_name', ''),
                'industry_category_name': resp.meta.get('industry_category_name', ''),
            }, priority=40)

    def parse_item(self, resp):
        c_doc = etree.HTML(resp.text)

        c_els = c_doc.xpath('//section[@id="Cominfo"]//table//td')
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

            # 获取发票信息
            # https://www.qcc.com/tax_view?keyno=225093b0546c258a4128f2c2f30bb6d0&ajaxflag=1
            invoice_info_els = resp.xpath('//*[@id="company-top"]/div[3]/div[2]/a[3]/@onclick')
            url = ''
            if invoice_info_els:
                invoice_info_el = invoice_info_els[0]
                # saveInvoiceModal('5afa2b9934cbaf75d11268151c696d0f','河池市宜州区创丰水稻种植专业合作社');zhugeTrack('企业主页头部按钮点击',{'按钮名称':'发票抬头'});
                com = re.compile(r'saveInvoiceModal\(\'(.*?)\',')
                key_no = com.findall(invoice_info_el)
                if key_no:
                    url = 'https://www.qcc.com/tax_view?keyno={keyno}&ajaxflag=1'.format(keyno=key_no[0])

            credit_code = ''
            address = ''
            phone_number = ''
            bank = ''
            bank_account = ''
            if url:
                headers = QccCrawlerSpider.get_headers(resp)
                text = requests.get(url=url, headers=headers).text
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
                try:
                    invoice_info = json.loads(text)
                    success = invoice_info.get('success', False)
                    if success:
                        data = invoice_info.get('data', {})
                        credit_code = data.get('CreditCode', '')
                        address = data.get('Address', '')
                        phone_number = data.get('PhoneNumber', '')
                        bank = data.get('Bank', '')
                        bank_account = data.get('Bankaccount', '')
                except Exception as e:
                    self.log('ERROR:{0}'.format(e))
            print(credit_code, address, phone_number, bank, bank_account)
            """
            [{'统一社会信用代码': '-', '企业名称': '延吉市金鑫冷冻肉食食品经营部', '法定代表人': '许晓萍关联1家企业>', 
            '登记状态': '注销', '成立日期': '1988-08-30', '注册资本': '1万元人民币', '实缴资本': '-', '核准日期': '2449-10-26', 
            '组织机构代码': '-', '工商注册号': '244491026-2', '纳税人识别号': '-', '企业类型': '集体所有制', '营业期限始': '', 
            '营业期限末': '至无固定期限', '纳税人资质': '-', '行业': '农业', '所属地区': '吉林省', '登记机关': '延吉市工商行政管理局', 
            '人员规模': '-', '参保人数': '-', '曾用名': '-', '英文名': '-', '进出口企业代码': '-', '注册地址': '-', 
            '经营范围': '(依法须经批准的项目,经相关部门批准后方可开展经营活动)'}]
            """
            notice_item = items.QCCItem()
            notice_item.update(**{
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
            })
            print(company_info.get('企业名称', ''))
            return notice_item
        else:
            self.log('regular error.')


if __name__ == '__main__':
    from scrapy import cmdline

    cmdline.execute("scrapy crawl qcc_crawler".split(" "))
