#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-04
# @Describe: 重公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time
# TODO 完成

def get_info_name(name):
    if '[' in name:
        name = ''.join(re.findall('(.*)]', name)).replace('[', '').strip()
    else:
        name = ''.join(name).strip()
    return name

def get_title_name(name):
    if ']' in name:
        name = ''.join(re.findall('](.*)', name))
    else:
        name = ''.join(name).strip()
    return name


class MySpider(Spider):
    name = "province_10_heilongjiang_spider"
    area_id = "10"
    allowed_domains = ['hljggzyjyw.gov.cn']
    domain_url = "http://hljggzyjyw.gov.cn"
    count_url = "http://hljggzyjyw.gov.cn/trade/tradezfcg?"
    area_province = "黑龙江省公共资源交易服务平台"
    project_category_dict = {
        "16": "工程建设信息",
        "17": "政府采购信息",
        "18": "土地及矿产权信息",
        "19": "国有产权信息",
        "20": "医疗卫生集中采购信息",
        "21": "煤炭产能置换指标交易"
    }

    #工程建设信息
    project_type_list = [1, 3, 4, 5, 7, 8]
    #政府采购信息
    purchase_type_list = [1, 3, 4, 5, 7]
    #土地及矿产权信息
    land_type_list = [1, 3, 4, 5, 7, 10]
    #国有产权信息
    owned_type_list = [1, 3, 4, 5, 7, 11]
    #医疗卫生集中采购信息
    medical_type_list = [1, 3, 4, 5, 7]
    #煤炭产能置换指标交易
    coal_type_list = [1, 3, 4, 5, 7]

    all_cid = [16, 18, 19, 20]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        for cid in self.all_cid:
            if cid == 16:
                for type in self.project_type_list:
                    yield scrapy.Request(
                            url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
                            callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            # if cid == 17:
            #     for type in self.purchase_type_list:
            #         yield scrapy.Request(
            #                 url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
            #                 callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            if cid == 18:
                for type in self.purchase_type_list:
                    yield scrapy.Request(
                        url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
                        callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            if cid == 19:
                for type in self.purchase_type_list:
                    yield scrapy.Request(
                        url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
                        callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            if cid == 20:
                for type in self.purchase_type_list:
                    yield scrapy.Request(
                        url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
                        callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            # if cid == 21:
            #     for type in self.purchase_type_list:
            #         yield scrapy.Request(
            #             url=f"{self.count_url}{urllib.parse.urlencode({'cid': cid} | {'type': type})}",
            #             callback=self.parse_page_urls, meta={'type': type, 'cid': cid})
            continue

    def parse_page_urls(self, response):
        try:
            if self.enable_incr:
                page = 1
                li_list = response.xpath('//div[@class="right_box"]/ul/li')
                num = 0
                for li in range(len(li_list)):
                    pub_time = li_list[li].xpath('./span[@class="date"]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        num += 1
                        base_url = response.url + '&pageNo={}'
                        if num >= len(li_list):
                            page += 1
                        else:
                            page = 1
                        yield scrapy.Request(url=base_url.format(page), callback=self.parse_data_urls,
                                             meta={'cid': response.meta.get('cid'), 'type': response.meta.get('type')})
            else:
                pages = response.xpath('//div[@class="page"]/span[2]/b[2]/text()').get()  #页数
                total = response.xpath('//div[@class="page"]/span[1]/b/text()').get()      #总条数
                base_url = response.url + '&pageNo={}'
                self.logger.info(
                    f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for i in range(1, int(pages) + 1):
                    yield scrapy.Request(url=base_url.format(i), callback=self.parse_data_urls,
                                         meta={'cid': response.meta.get('cid'), 'type': response.meta.get('type')})

        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath('/html/body/div/div[2]/div[2]/div[3]/div/ul/li')
            for li in li_list:
                title_list = li.xpath('./a/text()').get()
                if 'testceshi' in get_title_name(title_list) or '关于此栏目没有信息或信息更新不及时的说明' in get_title_name(title_list):
                    continue
                else:
                    base_all_url = self.domain_url + li.xpath('./a/@href').get()
                    info_source = get_info_name(title_list)
                    title_name = get_title_name(title_list)
                    pub_time = li.xpath('./span[@class="date"]/text()').get()
                    pub_time = get_accurate_pub_time(pub_time)
                    yield scrapy.Request(url=base_all_url, callback=self.parse_item,
                                         meta={'info_source': info_source, 'title_name': title_name, 'pub_time': pub_time,
                                            'cid': response.meta.get('cid'), 'type': response.meta.get('type')})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """

        if response.status == 200:
            origin = response.url
            info_source = response.meta["info_source"]
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            pub_time = response.meta["pub_time"]
            content = response.xpath('//div[@id="contentdiv"]').get()
            contents = re.sub('<a href=.*>.*</a>', '', content)
            content = re.sub('<span class="partook1">分享：</span>', '',
                      re.sub('<a class"bds_more">.*</a>', "",
                      re.sub('<a class="bds_qzone">.*</a>', "",
                      re.sub('<a class="bds_tsina">.*</a>', "",
                      re.sub('<a class="bds_tqq">.*</a>', '',
                      re.sub('<a class="bds_renren">.*</>', '',
                      re.sub('<a class="bds_weixin">.*</a>', "", contents)))))))
            title_name = response.meta['title_name']
            if response.meta['cid'] == 16:
                self.category = '工程建设信息'
            if response.meta['cid'] == 18:
                self.category = '土地及矿产权信息'
            if response.meta['cid'] == 19:
                self.category = '国有产权信息'
            if response.meta['cid'] == 20:
                self.category = '医疗卫生集中采购信息'

            if response.meta['type'] == 1 and response.meta['cid'] in [16, 18, 19, 20]:
                if re.search(r'终止公告|中止公告|废标公告|流标公告|异常公告', title_name):
                    self.notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    self.notice_type = const.TYPE_ZB_NOTICE               # 招标公告

            elif response.meta['type'] == 7 and response.meta['cid'] in [16, 18, 19, 20]:
                if re.search(r'终止公告|中止公告|废标公告|流标公告|异常公告', title_name):
                    self.notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    self.notice_type = const.TYPE_ZB_ALTERATION           #招标变更
            elif response.meta['type'] == 4 and response.meta['cid'] in [16, 18, 19, 20]:
                if re.search(r"候选人", title_name):
                    self.notice_type = const.TYPE_WIN_ADVANCE_NOTICE  # 中标预告
                elif re.search(r'终止公告|中止公告|废标公告|流标公告|异常公告', title_name):
                    self.notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    self.notice_type = const.TYPE_WIN_NOTICE          # 中标公告
            elif response.meta['type'] == 3 and response.meta['cid'] in [16, 18, 19, 20]:
                if re.search(r'终止公告|中止公告|废标公告|流标公告|异常公告', title_name):
                    self.notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    self.notice_type = const.TYPE_WIN_NOTICE              # 中标公告

            elif response.meta['type'] == 5 and response.meta['cid'] in [16, 18, 19, 20]:
                self.notice_type = const.TYPE_ZB_ABNORMAL             # 招标异常

            elif response.meta['type'] in [8, 10] and response.meta['cid'] == 16:
                if re.search(r'终止公告|中止公告|废标公告|流标公告|异常公告', title_name):
                    self.notice_type = const.TYPE_ZB_ABNORMAL
                else:
                    self.notice_type = const.TYPE_OTHERS_NOTICE            # 其他公告
            else:
                pass

            files_path = []
            # full_content = response.xpath("/html/body/div[2]/div[1]/div[2]").get()
            # if full_content:
            #     if files := re.findall(r"/ningxiaweb/uploadfile/.*?\"", full_content):
            #         pub_time_simple = pub_time.split(" ")[0]
            #         for item in files:
            #             item = item.replace("\"", "")
            #             file_item = FileItem()
            #             unquote_name = parse.unquote(item).split("/")[-1]
            #             file_item["file_url"] = parse.urljoin(self.domain_url, item)
            #             file_item["file_name"] = unquote_name.split('.')[0]
            #             file_item["file_type"] = unquote_name.split('.')[1]
            #             file_item["file_path"] = fr"{self.name}/{pub_time_simple}/{item.split('/')[-2]}/{unquote_name}"
            #             files_path.append(file_item["file_path"])
            #             yield file_item
            # print(type(origin), type(title_name), type(pub_time), type(content), type(info_source), type(self.notice_type), type(self.category))
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = self.notice_type
            notice_item["category"] = self.category
            # print(notice_item)
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_10_heilongjiang_spider -a sdt=2021-05-20 -a edt=2021-05-21".split(" "))
