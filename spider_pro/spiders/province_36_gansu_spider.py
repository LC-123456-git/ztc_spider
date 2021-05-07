import scrapy
import re
import base64
from scrapy.http.request import Request

from spider_pro.items import NoticesItem
from spider_pro import constans


class Province36GansuSpiderSpider(scrapy.Spider):
    name = 'province_36_gansu_spider'
    allowed_domains = ['ggzyjy.gansu.gov.cn']
    start_urls = ['https://ggzyjy.gansu.gov.cn']
    area_id = 36

    def __init__(self, *args, **kwargs):
        super(Province36GansuSpiderSpider, self).__init__()

        self.start_url = 'https://ggzyjy.gansu.gov.cn'
        self.area_map = {
            # '省级平台(省局)': '620000',
            '兰州': '620100',
            # '嘉峪关': '620200',
            # '金昌': '620300',
            # '白银': '620400',
            # '天水': '620500',
            # '武威': '620600',
            # '张掖': '620700',
            # '平凉': '620800',
            # '酒泉': '620900',
            # '庆阳': '621000',
            # '定西': '621100',
            # '陇南': '621200',
            # '临夏': '622900',
            # '甘南': '623000',
            # '省级平台(兰州新区)': '620001',
        }

        self.project_type_map = {
            # '工程建设': {
            #     'tag': 'A',
            #     'target': '/f/newprovince/annogoods/getAnnoList',
            # },
            # '政府采购': {
            #     'tag': 'D',
            #     'target': '/f/newprovince/annogoods/getAnnoList',
            # },
            '土地和矿业权': {
                'tag': 'B',
                'target': '/f/newprovince/annogoodsmine/getLandAnnoList',  # 省级
                'extra_target': '/f/province/annogoods/getAnnoList',  # 非省级
            },
            # '药品采购': {
            #     'tag': '',
            #     'target': ''
            # },
            # '重大项目': {
            #     'tag': 'I',
            #     'target': '/f/newprovince/annogoodsmine/getLandAnnoList',
            # },
            # '国有产权': {
            #     'tag': 'C',
            #     'target': '/f/newprovince/annogoodsmine/getLandAnnoList',
            # },
            # '协议供货阳光采购': {
            #     'tag': 'purchase',
            #     'target': '/f/purchase/purchaseAnnoment/getAnnoList?type=purchase&annomentTitle='
            # },
            # '限额以下工程建设': {
            #     'tag': 'engineer',
            #     'target': '/f/purchase/purchaseAnnoment/getAnnoList?type=engineer&annomentTitle='
            # },
            # '政府采购限额以下': {
            #     'tag': 'gover',
            #     'target': '/f/purchase/purchaseAnnoment/getAnnoList?type=gover&annomentTitle='
            # },
        }

        self.base_url = 'https://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/getAnnoList'
        self.flow_urls = [
            'https://ggzyjy.gansu.gov.cn/f/newprovince/tenderproject/flowpage',
            'https://ggzyjy.gansu.gov.cn/f/newprovince/tenderproject/flowBidpackage'
        ]
        self.extra_urls = [
            # 药品采购
            'https://ggzyjy.gansu.gov.cn/f/front/information/infoitemList?siteitemid=37&selecteditem=125&selected=2',
            'https://ggzyjy.gansu.gov.cn/f/front/information/infoitemList?siteitemid=37&selecteditem=242&selected=2',
            'https://ggzyjy.gansu.gov.cn/f/front/information/infoitemList?siteitemid=37&selecteditem=243&selected=2',
            'https://ggzyjy.gansu.gov.cn/f/front/information/infoitemList?siteitemid=37&selecteditem=252&selected=2',
        ]
        self.form_data = {
            'pageNo': '0',
            'pageSize': '10',
            'area': '620001',
            'projecttype': 'A',
            'prjpropertynewI': 'I',
            'prjpropertynewA': 'A',
            'prjpropertynewD': 'D',
            'prjpropertynewC': 'C',
            'prjpropertynewB': 'B',
            'prjpropertynewE': 'E',
            'projectname': ''
        }
        self.notice_map = {
            '项目信息': '0',
            '公告信息': '1',
            '专家抽取申请': '3',
            '开评标信息': '4',
            '公示信息': '5',
            '中标结果公告': '6',
            '保证金退还': '7',
            '中标见证书': '8',
            '合同': '9',
        }

    def start_requests(self):
        for area in self.area_map.values():
            for projecttypename, ptm in self.project_type_map.items():
                if not ptm['tag']:
                    pass  # TODO 药品采购
                else:
                    self.form_data['area'] = area
                    self.form_data['projecttype'] = ptm['tag']

                    # ** 特殊情况：土地和产业权 省级、非省级
                    if area in ['620000', '620001'] and ptm['tag'] == 'B':
                        ptm['target'] = ptm['extra_target']

                    yield scrapy.FormRequest(url=self.start_url + ptm['target'], formdata=self.form_data,
                                             callback=self.parse_base,
                                             meta={
                                                 'projecttype': ptm['tag'],
                                                 'projecttypename': projecttypename,
                                                 'area': area
                                             })

    def get_base64_url(self, p_id, suffix):
        return self.start_url + '/f/newprovince/tenderproject/{0}/{1}'.format(
            str(base64.b64encode(p_id.encode('utf8')), encoding='utf-8'),
            suffix
        )

    def parse_base(self, response):
        if response.status == 200:
            projecttype = response.meta.get('projecttype')
            projecttypename = response.meta.get('projecttypename')
            area = response.meta.get('area')

            # onclick属性 loadTender('32467','37027','1','') 提取4个参数
            els = response.xpath('//dl[contains(@class,"sDisclosurLeftConDetailList")]')

            com = re.compile("'([0-9 a-z A-Z]*)'")

            for el in els:
                title_name = el.xpath('.//a/@title').get()
                pub_time = el.xpath('.//i/text()').get()
                onclick_href = el.xpath('.//a/@onclick').get()
                link_href = el.xpath('.//a/@href').get()
                try:
                    # origin title_name pub_time
                    if area in ['620000', '620001'] and projecttype in ['I', 'A', 'D', 'C', 'B']:
                        if projecttype != 'B':  # 非土地矿业权 + 省级
                            tender_project_id, annogoods_id, bidding_type, type = com.findall(onclick_href)

                            # custom detail urls
                            if type == 'load':
                                if bidding_type and bidding_type != 15 and bidding_type != 13 and bidding_type != 16:
                                    detail_url = self.get_base64_url(tender_project_id, 'tenderprojectIndex?type=load')
                                elif bidding_type == 0:
                                    detail_url = self.get_base64_url(annogoods_id, 'loadTprjIndexBybiddingType')
                                elif bidding_type in [15, 16, 13]:
                                    detail_url = self.get_base64_url(tender_project_id, 'loadTenderprojectIndex')
                                else:
                                    detail_url = self.get_base64_url(tender_project_id, 'tenderprojectIndex?type=load')
                            else:
                                detail_url = self.get_base64_url(tender_project_id, 'tenderprojectIndex')
                        else:
                            href_com = re.compile('/(\d+)/')
                            tender_project_id = href_com.findall(link_href)[0]
                            detail_url = self.start_url + link_href

                        yield Request(url=detail_url, callback=self.parse_onclick_list, meta={
                            'projecttype': projecttype, 'tender_project_id': tender_project_id,
                            'origin': detail_url, 'title_name': title_name, 'pub_time': pub_time,
                            'projecttypename': projecttypename,
                        })
                    if area == '620000' and projecttype in ['purchase', 'engineer', 'gover']:
                        # 省级平台（省局）
                        # 协议供货阳光采购/限额以下工程建设/政府采购限额以下
                        detail_url = self.start_url + link_href

                        # TODO 只要采购公告

                        # yield Request(url=detail_url, callback=self.parse_href_list, meta={
                        #     'projecttype': projecttype, 'origin': detail_url, 'title_name': title_name,
                        #     'pub_time': pub_time, 'projecttypename': projecttypename,
                        # })
                    # 非省级 + 工程建设|政府采购|土地矿业权
                    if area not in ['620000', '620001'] and projecttype in ['A', 'D', 'B']:
                        if projecttype == 'B':
                            # TODO 土地矿业权
                            detail_url = self.start_url + link_href
                            yield Request(url=detail_url, callback=self.parse_land_page, meta={
                                'origin': detail_url, 'title_name': title_name,
                                'pub_time': pub_time, 'projecttypename': projecttypename,
                            })
                        else:
                            # TODO 工程建设|政府采购
                            pass
                        print('href TODO')

                except Exception as e:
                    self.log(e)

    def parse_onclick_list(self, response):
        """
        判断是否有交易流程
            招标公告
                项目信息、公告信息 药品采购
            资格预审结果公告
                资格预审公告信息、预审结果
            中标预告
                公示信息
            中标公告
                中标见证书
        """
        tender_project_id = response.meta.get('tender_project_id')
        trade_els = response.xpath('//li[contains(@class, "jxMenu") and not(@style)]')

        # TODO
        #   content split
        #   if clicked
        for trade_el in trade_els:
            c_notice = trade_el.xpath('./p/text()').extract_first()
            if c_notice in ['项目信息', '公告信息', '药品采购', '资格预审公告信息', '预审结果', '公示信息', '正标见证书']:
                index = self.notice_map.get(c_notice, '')
                for flow_url in self.flow_urls:  # TODO 内容页上下文 参数不同
                    yield scrapy.FormRequest(url=flow_url, formdata={
                        'index': index,
                        'tenderprojectid': tender_project_id,
                        'bidpackages': ''
                    }, callback=self.parse_flow_page, meta={
                        'origin': response.meta.get('origin'),
                        'title_name': response.meta.get('title_name'),
                        'pub_time': response.meta.get('pub_time'),
                        'category': response.meta.get('projecttypename'),
                        'notice': c_notice,
                    })

    def parse_href_list(self, response):
        """
        #协议供货阳光采购(采购公告、竞价过程、竞价结果、成交公示、合同) (href)
        /f/purchase/purchaseAnnoment/40/getAnnoDetail?annoId=40
        https://ggzyjy.gansu.gov.cn/f/purchase/purchaseAnnoment/getPurchaseByProject
        projectId: 40
        annoId: 40

        # 限额以下工程建设(采购公告、竞价过程、竞价结果、成交公示、合同) (href)
        /f/engineer/engineerAnnoment/46630/flowpage?pageIndex=1&amp;annogoodsId=46632
        https://ggzyjy.gansu.gov.cn/f/engineer/engineerAnnoment/getAnnoDetail
        projectId: 46618
        annogoodsId: 46620

        # 限额以下政府采购(采购公告、竞价过程、竞价结果、成交公示、合同) (href)
        /f/gover/annoment/46/goverflowpage?annogoodsId=48
        https://ggzyjy.gansu.gov.cn/f/gover/annoment/getAnnoDetail
        projectId: 69
        annogoodsId: 71
        """

        pass

    def parse_flow_page(self, response):
        notice = response.meta.get('notice')

        if notice in ['项目信息', '公告信息']:  # 招标公告
            notice_type = constans.TYPE_ZB_NOTICE
        elif notice in ['公示信息', '中标结果公告']:  # 资格预审结果公告
            notice_type = constans.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice == '公示信息':  # 中标预告
            notice_type = constans.TYPE_WIN_ADVANCE_NOTICE
        elif notice == '中标见证书':  # 中标公告
            notice_type = constans.TYPE_WIN_NOTICE
        else:
            notice_type = ''

        content = response.text
        notice_item = NoticesItem()
        notice_item["origin"] = response.meta.get('origin')
        notice_item["title_name"] = response.meta.get('title_name')
        notice_item["pub_time"] = response.meta.get('pub_time')
        # notice_item["info_source"] = info_source
        # notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
        # notice_item["files_path"] = "NULL" if not files_path else files_path
        notice_item["notice_type"] = notice_type
        notice_item["content"] = content
        notice_item["area_id"] = self.area_id
        notice_item["category"] = response.meta.get('category')
        yield notice_item

    def parse_land_page(self, response):
        """
        解析非省级 土地矿业权
        """
        notice = response.meta.get('notice')

        head = response.xpath('//div[@class="jxTradingMainLeftHead"]').get()
        body = response.xpath('//div[contains(@class, "jxTradingMainMiddleYes")]').get()

        if notice in ['项目信息', '公告信息']:  # 招标公告
            notice_type = constans.TYPE_ZB_NOTICE
        elif notice in ['公示信息', '中标结果公告']:  # 资格预审结果公告
            notice_type = constans.TYPE_QUALIFICATION_ADVANCE_NOTICE
        elif notice == '公示信息':  # 中标预告
            notice_type = constans.TYPE_WIN_ADVANCE_NOTICE
        elif notice == '中标见证书':  # 中标公告
            notice_type = constans.TYPE_WIN_NOTICE
        else:
            notice_type = ''

        notice_item = NoticesItem()
        notice_item["origin"] = response.meta.get('origin')
        notice_item["title_name"] = response.meta.get('title_name')
        notice_item["pub_time"] = response.meta.get('pub_time')
        # notice_item["info_source"] = info_source
        # notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
        # notice_item["files_path"] = "NULL" if not files_path else files_path
        notice_item["notice_type"] = notice_type
        notice_item["content"] = head + body
        notice_item["area_id"] = self.area_id
        notice_item["category"] = response.meta.get('category')
        yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_36_gansu_spider".split(" "))
