# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-05-07
# @Describe: 河北建投集团电子招投标交易平台 - 全量/增量脚本

import re, ast, requests
import math
import scrapy
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, judge_dst_time_in_interval, remove_specific_element


class MySpider(CrawlSpider):
    name = 'province_56_hebeijiantou_spider'
    area_id = "56"
    domain_url = "https://www.jtsww.com"
    query_url = "https://ecs.jtsww.com/externalLink/"
    base_url = ''
    allowed_domains = ['www.jtsww.com']
    area_province = "河北建投集团电子招投标交易平台"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    }

    # 招标公告
    list_notice_category_num = ['招标公告', '物资采购公告', '工程采购公告']
    # 中标公告
    list_win_notice_category_num = ['中标公示', '成交结果公示']
    # 招标异常
    list_alteration_category_num = []
    # 招标变更
    list_zb_abnormal_num = []
    # 中标预告
    list_win_advance_notice_num = []
    # 资格预审结果公告
    list_qualification_num = []
    # 其他公告
    list_others_notice_num = []
    
    classifyShow_list = ['招标公告', '中标公告', '成交结果公告']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
    def get_iframe(self, url):
        html = requests.get(url=url, headers=self.headers)
        return html

    def start_requests(self):
       yield scrapy.Request(url=self.domain_url, callback=self.parse_urls)


    def parse_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="s-grid-section-content _cell-spacing-small _magazine "]/div/div/div/div/div/div/a')
            for li in li_list:
                info_url = li.xpath('./@href').get()
                type_name = li.xpath('.//p/strong/text()').get()
                classifyShow = type_name if type_name not in self.classifyShow_list else ''
                if type_name in self.list_notice_category_num:
                    notice = const.TYPE_ZB_NOTICE                             # 招标公告
                else:
                    notice = const.TYPE_WIN_NOTICE                            # 中标公告
                yield scrapy.Request(url=info_url, callback=self.parse_data_info, dont_filter=True,
                                     meta={'notice': notice, 'classifyShow': classifyShow})
        except Exception as e:
            self.logger.error(f"parse_urls: 发起数据请求失败 {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            if self.enable_incr:
                pn = 1
                num = 1
                li_list = response.xpath('//ul[@class="list"]/li')
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./span/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                    info_url = response.url + '?gopage={}'
                    if num >= len(li_list):
                        pn += 1
                    else:
                        pn = 1
                    yield scrapy.Request(url=info_url.format(pn), callback=self.parse_info, dont_filter=True,
                                         meta={'notice': response.meta['notice'],
                                               'classifyShow': response.meta['classifyShow']})
            else:
                total = ast.literal_eval(re.findall('(\(.*\))', response.xpath('//div[@class="page"]/script/text()').get())[0])[1]
                pages = math.ceil(int(total)/25)
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(1, pages+1):
                    info_url = response.url + '?gopage={}'.format(num)
                    yield scrapy.Request(url=info_url, callback=self.parse_info, dont_filter=True,
                                         meta={'notice': response.meta['notice'],
                                               'classifyShow': response.meta['classifyShow']})
        except Exception as e:
            self.logger.error(f"parse_data_info:初始总页数提取错误 {response.meta=} {e} {response.url=}")



    def parse_info(self, response):
        try:
            li_list = response.xpath('//ul[@class="list"]/li')
            for li in li_list:
                info_url = self.query_url + li.xpath('./a/@href').get()
                info_title = li.xpath('./a/@title').get()
                pub_time = li.xpath('./span/text()').get()
                if re.search(r"变更|更正", info_title):
                    notice_type = const.TYPE_ZB_ALTERATION       # 招标变更
                elif re.search(r"废标|流标", info_title):
                    notice_type = const.TYPE_ZB_ABNORMAL         # 招标异常
                elif re.search(r"候选人|评标结果", info_title):
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE  # 中标预告
                elif re.search(r"中标", info_title):
                    notice_type = const.TYPE_WIN_NOTICE          # 中标公告
                else:
                    notice_type = response.meta['notice']

                yield scrapy.Request(url=info_url, callback=self.parse_item, priority=15, dont_filter=True,
                                     meta={'classifyShow': response.meta['classifyShow'],
                                     'info_title': info_title, 'notice_type': notice_type,
                                     'pub_time': pub_time})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        try:
            if response.status == 200:
                pub_time = response.meta['pub_time']
                pub_time = get_accurate_pub_time(pub_time)
                origin = response.url
                info_source = self.area_province
                title_name = response.meta['info_title']
                classifyShow = response.meta['classifyShow']
                notice_type = response.meta['notice_type']

                if response.xpath('//iframe[@id="external-frame"]/@src'):
                    html_url = response.xpath('//iframe[@id="external-frame"]/@src').get()
                    contents = self.get_iframe(html_url).text
                    pattern = re.compile(r'<head>(.*?)</head>', re.S)
                    contents = contents.replace(''.join(re.findall(pattern, contents)), '')

                    # 去除 titie
                    _, content = remove_specific_element(contents, 'p', 'class', 'MsoNormal', index=1)

                    pattern = re.compile(r'<p .*?>(.*?)</h1>', re.S)
                    content = contents.replace(''.join(re.findall(pattern, contents)), '')
                    content = re.sub(r'(本公告发布媒体.*?)</span>', '', content)


                    pattern = re.compile(r'发布公告的媒介(.*?)</span></p>', re.S)
                    content = contents.replace(''.join(re.findall(pattern, content)), '')
                elif response.xpath('//div[@class="cont"]'):
                    contents = response.xpath('//div[@class="cont"]').get()
                    content = ''.join(contents).replace('我要报价', '')
                else:
                    content = ''

                files_path = {}
                if response.xpath('//div[@class="ewb-right-txt"]/span[@class="infodetail"]/a/@href'):
                    con_list = response.xpath('//div[@class="ewb-right-txt"]/span[@class="infodetail"]/a')
                    for con in con_list:
                        value = con.xpath('./@href').get()
                        key = con.xpath('./text()').get()
                        files_path[key] = value
                if content:
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

        except Exception as e:
            print(e, response.url)


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_56_hebeijiantou_spider".split(" "))


