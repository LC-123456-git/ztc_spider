# -*- coding: utf-8 -*-
import scrapy


class CreditInfoCrawlerSpider(scrapy.Spider):
    name = 'credit_info_crawler'
    area_id = 8888888
    allowed_domains = ['www.gsxt.gov.cn']
    start_urls = ['http://www.gsxt.gov.cn/']
    custom_settings = {
        'ITEM_PIPELINES': {
            # 'spider_pro.pipelines.pipelines_qcc_json.JsonPipeline': 100,
            # 'spider_pro.pipelines.pipelines_extra.ExtraPipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'spider_pro.middlewares.UserAgentMiddleware.UserAgentMiddleware': 500,
            'spider_pro.middlewares.ProxyMiddleware.ProxyMiddleware': 100,
        }
    }

    def start_requests(self):
        """
        数据库中采集企查查网站名称
        逐个采集信用认证信息
        Returns:

        """

        pass
