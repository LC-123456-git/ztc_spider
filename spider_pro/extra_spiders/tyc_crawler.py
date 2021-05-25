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
    name = 'tyc_crawler'  # 写入企查查表
    area_id = 9999999
    allowed_domains = ['www.tianyancha.com']
    start_urls = ['http://www.tianyancha.com/']
    domain = 'https://www.tianyancha.com/'
    search_url = 'https://www.tianyancha.com/search?key={key}'
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
    basic_info_re = '法定代表人.*?经营状态,(?P<FDDBR>.*?),成立日期,(?P<CLRQ>.*?),注册资本,(?P<ZCZB>.*?),' + \
                    '实缴资本,(?P<SJZB>.*?),工商注册号,(?P<GSZCH>.*?),统一社会信用代码,(?P<TYSHXYDM>.*?),' + \
                    '纳税人识别号,(?P<NSRSBH>.*?),组织机构代码,(?P<ZZJGDM>.*?),营业期限,(?P<YYQXS>.*?)至(?P<YYQXM>.*?),纳税人资质,(?P<NSRZZ>.*?),' + \
                    '核准日期,(?P<HZRQ>.*?),公司类型,(?P<QYLX>.*?),行业,(?P<HY>.*?),人员规模,(?P<RYGM>.*?),参保人数,(?P<CBRY>.*?),' + \
                    '登记机关,(?P<DJJG>.*?),曾用名,(?P<CYM>.*?),英文名称,(?P<YWM>.*?),注册地址,(?P<ZCDZ>.*?),经营范围,(?P<JYFW>.*)'

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
            detail_xpath = '//*[@id="search_company_0"]//div[@class="header"]//a/@href'
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
            company_els = doc.xpath('//*[@id="company_web_top"]//div[@class="header"]/h1/text()')
            company = company_els[0] if company_els else ''

            els = doc.xpath('//div[@id="_container_baseInfo"]')

            if els and qymc == company:
                doc_content = etree.tounicode(els[0])

                _, content = TycCrawlerSpider.remove_specific_element(
                    doc_content, 'div', 'class', 'data-describe ', index=0)

                c_doc = etree.HTML(content)

                c_els = c_doc.xpath('//tr/*')
                t = []
                for el in c_els:
                    t.append(''.join(
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
                else:
                    self.log('{0}公司 没匹配着关键字'.format(company))
            else:
                self.log('{0}公司没找到'.format(company))
        except Exception as e:
            self.log('error:{e}'.format(e=e))


if __name__ == '__main__':
    from scrapy import cmdline

    cmdline.execute("scrapy crawl tyc_crawler".split(" "))
