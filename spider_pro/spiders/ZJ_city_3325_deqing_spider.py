# -*- coding: utf-8 -*-
import re
import requests
import scrapy
import copy
import json
from datetime import datetime
from scrapy.utils.project import get_project_settings

from spider_pro import items, constans, utils


class ZjCity3325DeqingSpiderSpider(scrapy.Spider):
    name = 'ZJ_city_deqing_spider'
    allowed_domains = ['116.62.168.209']
    start_urls = ['http://116.62.168.209/']
    query_url = 'http://116.62.168.209'
    basic_area = '浙江省-湖州市-德清县-德清县公共资源交易平台'
    area_id = 3325
    keywords_map = {
        '变更|答疑|澄清|补充|延期': '招标变更',
        '废标|流标': '招标异常',
        '候选人|预成交': '中标预告',
        '中标|成交': '中标公告',
        '预公示': '招标预告',
    }
    url_map = {
        '招标公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbgg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/cggg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/zfcgzxuj/index.htm'},
            {'category': '土地交易', 'url': 'http://116.62.168.209/churgg/index.htm'},
            {'category': '产权交易', 'url': 'http://116.62.168.209/chuanrgg/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nczrgg/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/ynjygg/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwjygg/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqzbgg/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fzfcgzbgg/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmzzgg/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjyjygg/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fsqjyjygg/index.htm'},
        ],
        '资格预审公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zsgs/index.htm'},
        ],
        '招标变更': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/dy/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/yndycq/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwdycq/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqdybc/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fzfcgdybc/index.htm'},
            {'category': '镇街道限额以下', 'url': 'http://116.62.168.209/xzdybc/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmdybc/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjyjggs/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fsqjyjggs/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmdybc/index.htm'},
        ],
        '招标异常': [
            # {'category': '工程交易', 'url': 'http://116.62.168.209/dy/index.htm'},
        ],
        '中标预告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbhxrgs/index.htm'},
            {'category': '工程建设交易', 'url': 'http://116.62.168.209/gxqpbjjgs/index.htm'},
            {'category': '非政府采购项目', 'url': 'http://116.62.168.209/fcfcgpbjggs/index.htm'},
            {'category': '镇街道限额以下', 'url': 'http://116.62.168.209/xzpbjggg/index.htm'},
            {'category': '部门限额以下', 'url': 'http://116.62.168.209/bmpbjggg/index.htm'},
        ],
        '中标公告': [
            {'category': '工程交易', 'url': 'http://116.62.168.209/zbjggg/index.htm'},
            {'category': '政府采购', 'url': 'http://116.62.168.209/zzbgs/index.htm'},
            {'category': '土地交易', 'url': 'http://116.62.168.209/chengjgs/index.htm'},
            {'category': '产权交易', 'url': 'http://116.62.168.209/cqcjgs/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nccjgs/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/yncjgg/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwcjgg/index.htm'},
            {'category': '集体产权', 'url': 'http://116.62.168.209/sqjybggg/index.htm'},
            {'category': '农村集体产权', 'url': 'http://116.62.168.209/nccjgs/index.htm'},
            {'category': '排污权交易', 'url': 'http://116.62.168.209/pwcjgg/index.htm'},
            {'category': '用能指标总量交易', 'url': 'http://116.62.168.209/pwcjgg/index.htm'},
        ],
        '其他公告': [
            {'category': '建设工程', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005001008'},
            {'category': '政府采购', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005002005'},
            {'category': '乡镇(部门)交易', 'url': 'http://ztb.longyou.gov.cn/front/bidcontent/9005007003'},
        ]
    }

    def parse(self, response):
        pass
