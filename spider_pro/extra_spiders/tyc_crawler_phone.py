# -*- coding: utf-8 -*-
import re
import requests
import random
from lxml import etree

import scrapy
from scrapy.utils.project import get_project_settings

from spider_pro.extra_spiders import cf
from spider_pro import items
from spider_pro.extra_spiders.public import db


class TycCrawlerSpider(scrapy.Spider):
    name = 'tyc_crawler_phone'
    area_id = 9999999
    allowed_domains = ['m.tianyancha.com']
    start_urls = ['http://m.tianyancha.com/']
    domain = 'https://m.tianyancha.com/'
    search_url = 'https://m.tianyancha.com/search?key={key}'
    custom_settings = {
        'ITEM_PIPELINES': {
            'spider_pro.pipelines.pipelines_extra.ExtraPipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
            'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 100,
        }
    }
    settings = get_project_settings()
    debug = settings.get('DEBUG_MODE', True)
    db_name = settings.get('MYSQL_TEST_DB_NAME', '') if debug else settings.get('MYSQL_DB_NAME', '')
    dbq = db.DBQuery(**{
        'host': settings.get('MYSQL_IP', ''),
        'user': settings.get('MYSQL_USER_NAME', ''),
        'password': settings.get('MYSQL_PASSWORD', ''),
        'db': db_name,
    })
    # QYMC,SSDQ,FDDBR,CLRQ,DJZT,ZCZB,SJZB,TYSHXYDM,GSZCH,ZZJGDM,NSRSBH,NSRZZ,QYLX,HY,YYQXS,YYQXM,RYGM,CBRY,
    # YWM,CYM,DJJG,HZRQ,ZCDZ,JYFW,JCKQYDM,QYFL,HYDL
    basic_info_re = '法定代表人,.*?,(?P<FDDBR>.*?),.*?成立日期,(?P<CLRQ>.*?),经营状态,(?P<DJZT>.*?),注册资本,(?P<ZCZB>.*?),' + \
                    '实缴资本,(?P<SJZB>.*?),统一社会信用代码,(?P<TYSHXYDM>.*?),工商注册号,(?P<GSZCH>.*?),组织机构代码,(?P<ZZJGDM>.*?),' + \
                    '纳税人识别号,(?P<NSRSBH>.*?),纳税人资质,(?P<NSRZZ>.*?),企业类型,(?P<QYLX>.*?),行业,(?P<HY>.*?),' + \
                    '营业期限,(?P<YYQXS>.*?)至(?P<YYQXM>.*?),人员规模,(?P<RYGM>.*?),参保人数,(?P<CBRY>.*?),' + \
                    '英文名称,(?P<YWM>.*?),曾用名,(?P<CYM>.*?),登记机关,(?P<DJJG>.*?),核准日期,(?P<HZRQ>.*?),注册地址,(?P<ZCDZ>.*?),经营范围,(?P<JYFW>.*)'

    @staticmethod
    def get_headers(resp):
        default_headers = resp.request.headers
        headers = {k: random.choice(v) if all([isinstance(v, list), v]) else v for k, v in default_headers.items()}
        return headers

    def start_requests(self):
        """
        轮询QCC所有企业名称
        Returns:
        """
        qcc_sql = cf.get('QCC', 'COMPANY_NAMES').format(db_name=self.db_name, table_name='QCC_qcc_crawler')
        companies = self.dbq.fetch_all(qcc_sql)

        for n, company in enumerate(companies):
            c_name = company.get('QYMC', '')

            c_url = self.search_url.format(key=c_name)

            yield scrapy.Request(url=c_url, callback=self.parse_list, priority=10 * (len(companies) - n), meta={
                'qcc_data': company,
            })

    def parse_list(self, resp):
        try:
            doc = etree.HTML(resp.text)
            detail_xpath = '//div[@class="search-name"]/a/@href'
            detail_urls = doc.xpath(detail_xpath)
            if detail_urls:
                detail_url = detail_urls[0]

                yield scrapy.Request(url=detail_url, callback=self.parse_detail, meta={
                    'qcc_data': resp.meta.get('qcc_data', {})
                })
        except Exception as e:
            self.log('error:{e}'.format(e=e))

    def parse_detail(self, resp):
        """
        统一社会信用代码|企业名称|注册号|组织机构代码|纳税人识别号|所属行业|法定代表人|公司类型|
        成立日期|注册资本|实缴资本|核准日期|营业期限自|营业期限至|登记机关|登记状态|注册地址|经营范围|

        企业名称|法定代表人 单独获取
        Returns:
        """
        try:
            qcc_data = resp.meta.get('qcc_data', {})
            qymc = qcc_data.get('QYMC', '')
            doc = etree.HTML(resp.text)
            # 企业名称
            company_els = doc.xpath('//div[@class="inner-name inner-title"]/text()')
            company = company_els[0] if company_els else ''

            els = doc.xpath('//div[@class="content" and position()=1]')

            if els and qymc == company:
                doc_content = etree.tounicode(els[0])

                c_doc = etree.HTML(doc_content)

                c_els = c_doc.xpath('//div[@class="divide-content"]/*')
                t = []
                for el in c_els:
                    t.append(','.join(
                        el.xpath('.//text()')
                    ).strip().replace(' ', '').replace('\n', ''))

                data = ','.join(t)

                com = re.compile(self.basic_info_re)

                ret = [m.groupdict() for m in re.finditer(com, data)]

                if ret:
                    tyc_data = ret[0]

                    for qcc_k, qcc_v in qcc_data.items():
                        if not qcc_v or qcc_v == '-':  # 覆盖
                            self.log('本次有更新：{0} {1}'.format(qcc_k, qcc_v))
                            qcc_data[qcc_k] = tyc_data.get(qcc_k)
                    notice_item = items.QCCItem()
                    notice_item.update(**{
                        'company_name': qymc,
                        'location': qcc_data.get('SSDQ', ''),
                        'legal_representative': qcc_data.get('FDDBR', ''),
                        'date_of_establishment': qcc_data.get('CLRQ', ''),
                        'operating_status': qcc_data.get('DJZT', ''),
                        'registered_capital': qcc_data.get('ZCZB', ''),
                        'paid_in_capital': qcc_data.get('SJZB', ''),
                        'unified_social_credit_code': qcc_data.get('TYSHXYDM', ''),
                        'business_registration_number': qcc_data.get('GSZCH', ''),
                        'organization_code': qcc_data.get('ZZJGDM', ''),
                        'taxpayer_identification_number': qcc_data.get('NSRSBH', ''),
                        'taxpayer_qualification': qcc_data.get('NSRZZ', ''),
                        'type_of_enterprise': qcc_data.get('QYLX', ''),
                        'industry': qcc_data.get('HY', ''),
                        'operating_period_std': qcc_data.get('YYQXS', ''),
                        'operating_period_edt': qcc_data.get('YYQXM', ''),
                        'staff_size': qcc_data.get('RYGM', ''),
                        'number_of_participants': qcc_data.get('CBRY', ''),
                        'english_name': qcc_data.get('YWM', ''),
                        'former_name': qcc_data.get('CYM', ''),
                        'registration_authority': qcc_data.get('DJJG', ''),
                        'approved_date': qcc_data.get('HZRQ', ''),
                        'registered_address': qcc_data.get('ZCDZ', ''),
                        'business_scope': qcc_data.get('JYFW', ''),
                        'import_and_export_enterprise_code': qcc_data.get('JCKQYDM', ''),
                        'category': resp.meta.get('QYFL', ''),
                        'industry_category': resp.meta.get('HYDL', ''),
                    })
                    print(qcc_data.get('QYMC', ''))
                    return notice_item
        except Exception as e:
            self.log('error:{e}'.format(e=e))


if __name__ == '__main__':
    from scrapy import cmdline

    cmdline.execute("scrapy crawl tyc_crawler_phone".split(" "))
