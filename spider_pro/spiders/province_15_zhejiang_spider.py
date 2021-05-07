#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-09
# @Describe: 浙江省公共资源交易网
import re
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, judge_dst_time_in_interval


class MySpider(CrawlSpider):
    name = "province_15_zhejiang_spider"
    area_id = "15"
    allowed_domains = ['zmctc.com']
    # 招标预告
    list_advance_notice_num = ["004003001", "004003002", "004003003"]

    # 招标公告
    list_notice_category_num = ["004001001", "004001002", "004001003", "004011001", "004011002",
                                "004011003"]
    # 资格预审公告
    list_qualifiction_advance_notice_num = ["004005001", "004005002", "004005003"]
    # 招标变更
    list_alteration_category_num = ["004002001", "004002002", "004002003"]
    # 中标预告
    list_win_advance_category_num = ["004006001", "004006002", "004006003"]
    # 中标公告
    list_win_notice_category_num = ["004010001", "004010002", "004010003"]
    # 其他公告
    list_others_notice_num = ["004004001", "004004002", "004004003", "004009001", "004009002", "004009003",
                              "004007"]
    # 其他公告_合同备案情况特殊处理 编号为004007
    url_type_almost = "1"
    url_type_contract = "2"
    area_province = "浙江省公共资源交易服务平台"

    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num + \
                            list_win_advance_category_num + list_win_notice_category_num + \
                            list_qualifiction_advance_notice_num + list_others_notice_num

    rules = (
        # 招标预告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400300([1-4]{1})',
        ], unique=True),
            cb_kwargs={"name": const.TYPE_ZB_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 招标公告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400100([1-4]{1})',
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00401100([1-4]{1})',
        ], unique=True),
            cb_kwargs={"name": const.TYPE_ZB_NOTICE}, callback="parse_item", follow=False),
        # 资格预审公告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400500([1-4]{1})',
        ], unique=True),
            cb_kwargs={"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 招标变更
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400200([1-4]{1})'
        ], unique=True),
            cb_kwargs={"name": const.TYPE_ZB_ALTERATION}, callback="parse_item", follow=False),
        # 中标预告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400600([1-4]{1})'
        ], unique=True),
            cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 中标公告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00401000([1-4]{1})'
        ], unique=True),
            cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_item", follow=False),
        # 其他公告
        Rule(LinkExtractor(allow=[
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400400([1-4]{1})',
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=00400900([1-4]{1})',
            r'/zjgcjy/InfoDetail/\?InfoID=.*\-.*\-.*\-.*\-.*\&CategoryNum=004007',
        ], unique=True),
            cb_kwargs={"name": const.TYPE_OTHERS_NOTICE}, callback="parse_item", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

        # self.enable_incr = True
        # self.sdt_time = "2021-01-25"
        # self.edt_time = "2021-01-25"

    def start_requests(self):
        for item in self.list_all_category_num:
            if item == "004007":
                current_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/".format(item)
                yield scrapy.Request(
                    url=current_url, callback=self.parse_page_urls, meta={
                        "cont_id": item, "_type": self.url_type_contract
                    })
            else:
                current_item = item[0:6]
                current_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/{}/".format(current_item, item)
                yield scrapy.Request(
                    url=current_url, callback=self.parse_page_urls, meta={
                        "cont_id": item, "_type": self.url_type_almost
                    })

    def parse_page_urls(self, response):
        category_num = response.meta['cont_id']
        _type = response.meta['_type']
        if pages := re.search(r"totalPageNums = \d+", response.text):
            pages = int(re.search(r"\d+", pages.group(0)).group(0))
            if pages >= 1:
                if _type == self.url_type_almost:
                    if self.enable_incr:
                        info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/{}/?Paging={}".format(
                            category_num[0:6], category_num, 1)
                        yield scrapy.Request(url=info_url, meta={
                            "current_page": 1,
                            "cont_id": category_num,
                            "total_page": pages,
                            "_type": self.url_type_almost
                        }, callback=self.extract_data_urls)
                    else:
                        info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/{}/?Paging={}"
                        pages += 1
                        for i in range(1, pages):
                            yield scrapy.Request(
                                url=info_url.format(category_num[0:6], category_num, i)
                            )
                elif _type == self.url_type_contract:
                    if self.enable_incr:
                        info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/?Paging={}".format(category_num, 1)
                        yield scrapy.Request(url=info_url, meta={
                            "current_page": 1,
                            "cont_id": category_num,
                            "total_page": pages,
                            "_type": self.url_type_contract
                        }, callback=self.extract_data_urls)
                    else:
                        info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/?Paging={}"
                        pages += 1
                        for i in range(1, pages):
                            yield scrapy.Request(
                                url=info_url.format(category_num, i)
                            )
                else:
                    return
            else:
                self.logger.error(f"初始链接翻页提取为0：{response.url=} {category_num=}")
                return
        else:
            self.logger.error(f"初始链接翻页提取异常：{response.url=} {category_num=}")
            return

    def extract_data_urls(self, response):
        is_in_interval = True
        date_list = re.findall(r'\[\d{4}-\d{2}-\d{2}]', response.text)
        current_page = response.meta["current_page"]
        total_page = response.meta["total_page"]
        _type = response.meta["_type"]
        category_num = response.meta["cont_id"]
        for item in date_list:
            item_ture_time = item.split("[")[-1].split("]")[0]
            x, y, z = judge_dst_time_in_interval(item_ture_time, self.sdt_time, self.edt_time)
            if x:
                pass
            elif y:
                is_in_interval = False
                break
        if is_in_interval:
            next_page = current_page + 1
            if next_page <= total_page:
                if _type == self.url_type_almost:
                    info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/{}/?Paging={}".format(
                        category_num[0:6], category_num, next_page)
                    yield scrapy.Request(url=info_url, meta={
                        "current_page": next_page,
                        "cont_id": category_num,
                        "total_page": total_page,
                        "_type": self.url_type_almost
                    }, callback=self.extract_data_urls)
                elif _type == self.url_type_contract:
                    info_url = "http://www.zmctc.com/zjgcjy/jyxx/{}/?Paging={}".format(category_num, next_page)
                    yield scrapy.Request(url=info_url, meta={
                        "current_page": next_page,
                        "cont_id": category_num,
                        "total_page": total_page,
                        "_type": self.url_type_contract
                    }, callback=self.extract_data_urls)

        seen = set()
        for rule_index, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            for link in rule.process_links(links):
                seen.add(link)
                request = self._build_request(rule_index, link)
                request.meta["cb_kwargs"] = rule.cb_kwargs
                yield rule.process_request(request, response)

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("//*[@id='tdTitle']/font[1]/b/text()").get() or ""
            pub_time = response.xpath("//*[@id='tdTitle']/font[2]/text()").getall()
            pub_time = get_accurate_pub_time(str(pub_time))
            info_source = self.area_province
            content = response.xpath('//*[@id="TDContent"]').get()

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name.strip()
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = ""
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            if re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = name
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_15_zhejiang_spider -a sdt=2021-03-25 -a edt=2021-03-26".split(" "))
