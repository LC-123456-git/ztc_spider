# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-12
# @Describe: 新点电子交易平台 - 全量/增量脚本
import re
import math
import json

import requests
import scrapy, string
import random
import datetime
from urllib import parse
from lxml import etree
from urllib.parse import quote
import xmltodict
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = 'province_62_xindian_spider'
    area_id = "62"
    domain_url = "https://www.etrading.cn"
    query_url = "https://www.etrading.cn/jyxx/002001/002001001/notice_jyxxzbgg.html"
    base_url = 'https://www.etrading.cn/hxepointwebbuilder/epointInformationDetailAction.action?cmd=getInfolist&{}&siteguid=7eb5f7f1-9041-43ad-8e13-8fcb82ea831a'
    details_url = 'https://www.etrading.cn/noticeDetails_jyxx.html?'
    data_url = 'https://www.etrading.cn/hxepointinteligentsearchweb/rest/inteligentSearch/getFullTextData'
    allowed_domains = ['www.etrading.cn']
    area_province = "新点电子交易平台"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }


    # 招标公告
    list_notice_category_num = ['招标公告']
    # 中标公告
    list_win_notice_category_num = ['中标公示', '成交公示']
    # 招标异常
    list_alteration_category_num = ['中标/流标公示']
    # 招标变更
    list_zb_abnormal_num = ['澄清/变更公告']
    # 中标预告
    list_win_advance_notice_num = ['中标候选人公示']
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = []
    equal_list = ['002001001', '002001002', '002001003', '002001004',
                  '002002001', '002002002', '002002003', '002002005',
                  '002003001', '002003002', '002003003', '002003004',
                  '002008001', '002008002', '002008003', '002008004']

    r_dict = '{"token":"","pn":0,"rn":20,"sdt":"","edt":"","wd":"","inc_wd":"","exc_wd":"","fields":"title;content","cnum":"002","sort":"{infodate:0}",' \
             '"ssort":"title","cl":500,"terminal":"","condition":[{"equal":"002","fieldName":"categorynum","isLike":"true","likeType":"2"},{"equal":"",' \
             '"fieldName":"infod","isLike":"true","likeType":"2"}],' \
             '"time":[{"fieldName":"infodate", "startTime": "", "endTime": ""}],"highlights":"title;content",' \
             '"statistics":null,"unionCondition":null,"accuracy":"","noParticiple":"","searchRange":null,"isBusiness":"1"}'

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def get_content(self, url):
        content = requests.get(url=url, headers=self.headers)
        content = etree.HTML(content.content)
        return content

    def get_iframe(self, url):
        info_code = re.findall('(.*)&title', url[url.rindex('?')+1:])[0]
        response = requests.get(url=self.base_url.format(info_code), headers=self.headers).text
        html_list = [num['urlpath'] for num in json.loads(json.loads(response)['custom'])]
        if len(html_list) <= 4:
            return html_list


    def start_requests(self):
        for equal in self.equal_list:
            equal_dict = json.loads(self.r_dict)['condition'][0] | {'equal': equal}
            info_equal = json.loads(self.r_dict) | {'condition': [equal_dict]}
            yield scrapy.Request(url=self.data_url, method='POST', body=json.dumps(info_equal),
                                 callback=self.parse_urls, dont_filter=True, priority=20)

    def parse_urls(self, response):
        try:
            total = json.loads(response.text)['result']['totalcount']
            self.logger.info(f"post 初始总数提取成功 {total=} {response.url=}")
            pages = math.ceil(int(total) / 20)
            for num in range(pages):
                pn_dict = json.loads(self.r_dict) | {'pn': str(num*10)}
                yield scrapy.Request(url=self.data_url, method='POST', body=json.dumps(pn_dict),
                                     callback=self.parse_info, dont_filter=True, priority=20,
                                     )
        except Exception as e:
            self.logger.error(f"parse_urls 发起数据请求失败 {e} {response.url=}")


    def parse_info(self, response):
        try:
            info_lsit = json.loads(response.text)['result']['records']
            for info in info_lsit:
                # _url = self.domain_url + info['linkurl']
                _url = 'https://www.etrading.cn/jyxx/002001/002001003/20210508/ae9ac5f0-3cae-4288-a123-fcd5322733c4.html'
                code = re.search('(\d{9})', _url)[0]
                # t_name = info['title']
                t_name = '宁夏固原市隆德县中药材国家农村产业融合发展示范园基础设施建设项目（新建工程）—示范园核心区集中供能（蒸汽管网）扩建工程中标候选人公示'
                if code in ['002002001', '002001001', '002003001', '002008001']:
                    notice = const.TYPE_ZB_NOTICE                     # 招标公告
                elif code in ['002002002', '002001002', '002003002', '002008002']:
                    notice = const.TYPE_ZB_ALTERATION                 # 招标变更
                elif code in ['002002003', '002001003', '002003003', '002008003']:
                    notice = const.TYPE_WIN_ADVANCE_NOTICE            # 中标预告
                else:
                    notice = const.TYPE_WIN_NOTICE                    # 中标公告

                if re.search(r"终止|中止|流标|废标|暂停", t_name):    # 招标变更
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r"变更|答疑|澄清|补充|延期", t_name):  # 招标异常
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r"候选人|预成交", t_name):             # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r"中标|成交|成交公示", t_name):        # 中标公告
                    notice_type = const.TYPE_WIN_NOTICE
                else:
                    notice_type = notice

                info_url = quote(_url, safe=string.printable)

                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=100,
                                     meta={'t_name': t_name, 'notice_type': notice_type})
        except Exception as e:
            self.logger.error(f"parse_data_info 发起数据请求失败  {response.meta=} {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            info_source = self.area_province
            classifyShow = ''
            title_name = response.meta.get("t_name") or ''
            notice_type = response.meta.get("notice_type") or ''
            origin = response.url
            pub_time = response.xpath('//p[@class="ewb-info-source02"]/span[1]/text()').get().replace('信息时间：', '')
            pub_time = get_accurate_pub_time(pub_time)

            files_path = {}
            if response.xpath('//div[@class="content"]'):
                content = response.xpath('//div[@class="content"]').get()
                pattern = re.compile(r'<div style="display:none;">(.*?)</div>', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                pattern = re.compile(r'<div class="ewb-countdown".*?>(.*?)<div class="ewb-info-main">', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                pattern = re.compile(r'<div class="baoming".*?>(.*?)<div class="ewb-info-footer">', re.S)
                content = content.replace(''.join(re.findall(pattern, content)), '')
                contents = content.replace('display:none;', 'display:block;').replace('class="ewb-enclosure"', 'style="display:block;"')
                respon = etree.HTML(contents)

                # 判断content 里面是否有正文                 if ''.join(respon.xpath('//div[@id="attach"]//text()')).strip() not in '暂无相关附件':
                if ''.join(respon.xpath('//div[@class="ewb-info-main"]//text()')).strip() not in ['/', '.']:
                    content = contents
                    if respon.xpath("//div[@id='attach']//a/@href"):
                        str_content = respon.xpath("//div[@id='attach']//a")
                        for con in str_content:
                            # 判断href 是否带 http头
                            if con.xpath('./@href'):
                                if 'http' not in con.xpath('./@href')[0]:
                                # 判断href 是不是email
                                    if con.xpath('./@href')[0] not in re.findall('.*[a-zA-Z0-9]{0,19}@[a-zA-Z0-9].*', con.xpath('./@href')[0]):
                                        value = self.domain_url + con.xpath('./@href')[0]
                                        keys = ''.join(con.xpath('.//text()')[0]).strip()
                                        files_path[keys] = value
                                else:
                                    if con.xpath('./@href')[0] not in re.findall('.*[a-zA-Z0-9]{0,19}@[a-zA-Z0-9].*', con.xpath('./@href')[0]):
                                        value = con.xpath('./@href')[0]
                                        keys = ''.join(con.xpath('.//text()')[0]).strip()
                                        files_path[keys] = value

                    notice_item = NoticesItem()
                    notice_item["origin"] = origin
                    notice_item["title_name"] = title_name
                    notice_item["pub_time"] = pub_time
                    notice_item["info_source"] = info_source
                    notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
                    notice_item["files_path"] = "" if not files_path else files_path
                    notice_item["notice_type"] = notice_type
                    notice_item["content"] = content
                    notice_item["area_id"] = self.area_id
                    notice_item["category"] = classifyShow

                    yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_62_xindian_spider".split(" "))




