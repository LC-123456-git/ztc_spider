#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-23
# @Describe: 福建公共资源交易平台 - 全量/增量脚本
#
import re
import scrapy
from lxml import etree
from scrapy.spiders import CrawlSpider
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, get_iframe_pdf_div_code, \
                             get_real_url, get_files

class MySpider(CrawlSpider):
    name = 'province_18_fujian_spider'
    area_id = "18"
    domain_url = "https://fjggzyjy.cn"
    query_url = "https://fjggzyjy.cn/queryContent_{}-jygk.jspx?title=&origin=&channelId={}&ext="
    basr_url = 'https://fjggzyjy.cn/queryContent_1-jygk.jspx?title=&origin=&channelId={}&ext='
    allowed_domains = ['fjggzyjy.cn']
    area_province = '福建'

    # 招标公告
    list_notice_category_code = ['3682', '3691', '3695', '3776', '3771', '3759', '3776', '3781', '3784', '3787', '3714', '3716', '3718', '3720']
    # 招标变更
    list_zb_abnormal_code = ['3726', '3684', '3688', '3761', '3773', '3778', '3697', '3692', '3782', '3785', '3788']
    # 中标预告
    list_win_advance_notice_code = ['3727', '3693', '3698', '3779', '3774', '3762']
    # 中标公告
    list_win_notice_category_code = ['3719', '3717', '3715', '3713', '3728', '3690', '3685', '3763', '3780', '3701', '3699', '3694', '3789', '3786', '3783']
    # 其他
    list_qita_code = ['3721', '3725', '3683', '3687', '3756', '3696', '3777', '3772', '3760']

    list_all_category_code = list_notice_category_code + list_zb_abnormal_code + list_win_advance_notice_code + \
                             list_win_notice_category_code + list_qita_code



    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        for code in self.list_all_category_code:
            if code in self.list_notice_category_code:
                notice = const.TYPE_ZB_NOTICE
            elif code in self.list_zb_abnormal_code:
                notice = const.TYPE_ZB_ALTERATION
            elif code in self.list_win_advance_notice_code:
                notice = const.TYPE_WIN_ADVANCE_NOTICE
            elif code in self.list_win_notice_category_code:
                notice = const.TYPE_WIN_NOTICE
            elif code in self.list_qita_code:
                notice = const.TYPE_OTHERS_NOTICE
            else:
                notice = ''
            if notice:
                info_url = self.basr_url.format(code)
                yield scrapy.Request(url=info_url, callback=self.parse_urls,
                                     meta={"notice": notice})

    def parse_urls(self, response):
        try:
            category_name = (response.xpath('//ul[@id="sx_nav"]/li[@class="on"]/text()').get()).strip()
            code = re.findall('.*=(\d+)', response.url[:response.url.rindex('&')])[0]
            if self.enable_incr:
                li_list = response.xpath('//ul[@class="list-body"]/li')
                nums = 0
                for li in range(len(li_list)):
                    li_url = li_list[li].xpath('./p[1]/a/@href').get()
                    title_name = ''.join(li_list[li].xpath('./p[1]/a/text()').extract()).strip()
                    put_time = li_list[li].xpath('./p[2]/text()').get()
                    put_time = get_accurate_pub_time(put_time)
                    x, y, z = judge_dst_time_in_interval(put_time, self.sdt_time, self.edt_time)
                    if x:
                        nums += 1
                        yield scrapy.Request(url=li_url, callback=self.parse_item,
                                             meta={"category": category_name,
                                                   'title_name': title_name,
                                                   'put_time': put_time,
                                                   'notice': response.meta['notice']})
                    if nums >= len(li_list):
                        page_num = int(re.findall('\w+_(\d+)-\w+', response.url[response.url.rindex('/') + 1:])[0])
                        page_num += 1
                        total = int(len(li_list))
                        if total == None:
                            return
                        self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        data_url = self.query_url.format(page_num, code)
                        yield scrapy.Request(url=data_url, callback=self.parse_urls, dont_filter=True,
                                             meta={"notice": response.meta['notice'],
                                                   'category': category_name})

            else:
                pages = response.xpath('//ul[@class="pages-list"]/li[@class="select_page"]/select/option[last()]/text()').get()
                self.logger.info(f"本次获取总条数为：{int(pages) * 10}")
                for num in range(1, int(pages) + 1):
                    data_urls = self.query_url.format(num, code)
                    yield scrapy.Request(url=data_urls, callback=self.parse_data_urls, priority=100,
                                         meta={"notice": response.meta['notice'],
                                               'category': category_name})

        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath('//ul[@class="list-body"]/li')
            for li in li_list:
                li_url = li.xpath('./p[1]/a/@href').get()
                put_time = li.xpath('./p[2]/text()').get()
                title_name = ''.join(li.xpath('./p[1]/a/text()').extract()).strip()
                yield scrapy.Request(url=li_url, callback=self.parse_item, priority=150,
                                     meta={"category": response.meta['category'],
                                           'title_name': title_name,
                                           'put_time': put_time,
                                           'notice': response.meta['notice']})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        if response.status == 200:
            origin = response.url
            source = (response.xpath('//div[@class="title"]/p[2]/span[2]/text()').get()).replace('来源：', '')
            if source:
                info_source = self.area_province + source
            else:
                info_source = self.area_province
            category = response.meta.get("category")
            title_name = response.meta['title_name']
            pub_time = response.meta['put_time']
            pub_time = get_accurate_pub_time(pub_time)

            content = response.xpath('//div[@class="report-text"]').get()
            pattern = re.compile(r'<div class="title"*?>(.*?)</div>', re.S)
            content_text = content.replace(re.findall(pattern, content)[0], '')

            patterns = re.compile(r'<div class="other".*?>(.*?)</div>', re.S)
            contents = content_text.replace(re.findall(patterns, content_text)[0], '')
            files_text = etree.HTML(content)
            keys_a = ['jhtml']
            files_path = get_files(self.domain_url, origin, files_text, keys_a=keys_a)
            if re.search(r'终止|中止|异常|废标|流标', title_name):
                notice_type = const.TYPE_ZB_ABNORMAL
            else:
                notice_type = response.meta['notice']

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "NULL" if not files_path else files_path
            notice_item["notice_type"] = notice_type
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["category"] = category
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl province_18_fujian_spider".split(" "))
    cmdline.execute("scrapy crawl province_18_fujian_spider -a sdt=2021-04-01 -a edt=2021-07-11".split(" "))


