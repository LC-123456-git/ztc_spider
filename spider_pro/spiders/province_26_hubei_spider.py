#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2020-12-30
# @Describe: 湖北省公共资源交易网
import re
import scrapy
import math
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, judge_dst_time_in_interval


def process_request_category(request, response):
    r_url = request.url
    for item in ["004001001", "004002001", "004003001", "004004001", "004005001", "004006001", "004007001"]:
        if item in r_url:
            request.meta["classify_show"] = "房建市政"
            return request
    for item in ["004001002", "004002002", "004003002", "004004002", "004005002", "004006002", "004007002"]:
        if item in r_url:
            request.meta["classify_show"] = "水利工程"
            return request
    for item in ["004001003", "004002003", "004003003", "004004003", "004005003", "004006003", "004007003"]:
        if item in r_url:
            request.meta["classify_show"] = "交通工程"
            return request
    for item in ["004001004", "004002004", "004003004", "004004004", "004005004", "004006004", "004007004"]:
        if item in r_url:
            request.meta["classify_show"] = "铁路工程"
            return request
    for item in ["004001005", "004002005", "004003005", "004004005", "004005005", "004006005", "004007005"]:
        if item in r_url:
            request.meta["classify_show"] = "土地整治"
            return request
    for item in ["004001006", "004002006", "004003006", "004004006", "004005006", "004006006", "004007006"]:
        if item in r_url:
            request.meta["classify_show"] = "其它工程"
            return request
    for item in ["004001007", "004002007", "004003007", "004004007", "004005007", "004006007", "004007007"]:
        if item in r_url:
            request.meta["classify_show"] = "政府采购"
            return request

class MySpider(CrawlSpider):
    name = "province_26_hubei_spider"
    area_id = "26"
    area_province = "湖北省公共资源交易服务平台"
    allowed_domains = ['hbbidcloud.cn']
    # 招标预告
    list_advance_notice_num = ["004001001", "004001002", "004001003", "004001004", "004001005", "004001006",
                               "004001007"]
    # 招标公告
    list_notice_category_num = ["004002001", "004002002", "004002003", "004002004", "004002005", "004002006",
                                "004002007"]
    # 招标变更
    list_alteration_category_num = ["004003001", "004003002", "004003003", "004003004", "004003005", "004003006",
                                    "004003007"]
    # 中标预告
    list_win_advance_category_num = ["004004001", "004004002", "004004003", "004004004", "004004005", "004004006",
                                     "004004007"]
    # 中标公告
    list_win_notice_category_num = ["004005001", "004005002", "004005003", "004005004", "004005005", "004005006",
                                    "004005007"]
    list_all_category_num = list_advance_notice_num + list_notice_category_num + list_alteration_category_num + list_win_advance_category_num + list_win_notice_category_num

    rules = (
        # 招标预告
        Rule(LinkExtractor(allow=[
            r'/shengbenji/jyxx/004001/00400100([1-7]){1}//\d{4}\d{1,2}\d{1,2}/.*\-.*\-.*\-.*\-.*\.html',
        ], unique=True), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_ZB_ADVANCE_NOTICE}, callback="parse_item", follow=False),

        # 招标公告
        Rule(LinkExtractor(allow=[
            r'/shengbenji/jyxx/004002/00400200([1-7]){1}/\d{4}\d{1,2}\d{1,2}/.*\-.*\-.*\-.*\-.*\.html'
        ], unique=True), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_ZB_NOTICE}, callback="parse_item", follow=False),
        # 招标变更 招标异常也在本规则下，根据标题标题中带有“中止，终止，流标，废标异常”关键词归类
        Rule(LinkExtractor(allow=[
            r'/shengbenji/jyxx/004003/00400300([1-7]){1}/\d{4}\d{1,2}\d{1,2}/.*\-.*\-.*\-.*\-.*\.html'
        ], unique=True), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_ZB_ALTERATION}, callback="parse_item", follow=False),
        # 中标预告
        Rule(LinkExtractor(allow=[
            r'/shengbenji/jyxx/004004/00400400([1-7]){1}/\d{4}\d{1,2}\d{1,2}/.*\-.*\-.*\-.*\-.*\.html'
        ], unique=True), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_WIN_ADVANCE_NOTICE}, callback="parse_item", follow=False),
        # 中标公告
        Rule(LinkExtractor(allow=[
            r'/shengbenji/jyxx/004005/00400500([1-7]){1}/\d{4}\d{1,2}\d{1,2}/.*\-.*\-.*\-.*\-.*\.html'
        ], unique=True), process_request=process_request_category,
            cb_kwargs={"name": const.TYPE_WIN_NOTICE}, callback="parse_item", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for item in self.list_all_category_num:
            current_item = item[0:6]
            self.current_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/about.html".format(current_item, item)
            yield scrapy.Request(
                url=self.current_url, callback=self.parse_page_urls, meta={"cont_id": item})
        # item = "004002001"
        # current_item = item[0:6]
        # self.current_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/about.html".format(current_item, item)
        # yield scrapy.Request(
        #     url=self.current_url, callback=self.parse_page_urls, meta={"cont_id": item})

    def parse_page_urls(self, response):
        category_num = response.meta['cont_id']
        if count_str := re.search(r"total: \d+", response.text):
            limit = 10
            count = int(re.search(r"\d+", count_str.group(0)).group(0))
            if limit_str := re.search(r"pageSize: \d+", response.text):
                limit = int(re.search(r"\d+", limit_str.group(0)).group(0))
            self.logger.info(f"start_page_is_success： id={response.meta['cont_id']} {count=} ")
            pages = math.ceil(count / limit)
            if self.enable_incr:
                i = "about"
                info_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/{}.html".format(category_num[0:6],category_num, i)
                yield scrapy.Request(url=info_url, callback=self.extract_data_urls, meta={"current_page": 1,
                                                                                          "cont_id": category_num,
                                                                                          "total_page": pages
                                                                                          }, dont_filter=True)
            else:
                for i in range(1, pages):
                        if i == 1:
                            i = "about"
                        info_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/{}.html".format(category_num[0:6], category_num, i)
                        yield scrapy.Request(url=info_url)
        else:
            try:
                self.info_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/about.html".format(category_num[0:6], category_num)
                yield scrapy.Request(url=self.info_url)
            except Exception as e:
                self.logger.error(f"start_page_is_error：{response.url=}{e} {response.meta=}")

    def extract_data_urls(self, response):
        is_in_interval = True
        date_list = re.findall(r'\d{4}-\d{2}-\d{2}', response.text)
        current_page = response.meta["current_page"]
        total_page = response.meta["total_page"]
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
                self.info_url = "http://www.hbbidcloud.cn/shengbenji/jyxx/{}/{}/{}.html".format(category_num[0:6], category_num, next_page)
                yield scrapy.Request(url=self.info_url, meta={
                    "current_page": 1,
                    "cont_id": category_num,
                    "total_page": total_page,
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
            title_name = response.xpath("/html/body/div[2]/div[2]/div/h3/text()").get()
            if not title_name:
                title_name = ""
            pub_time = response.xpath("/html/body/div[2]/div[2]/div/div[1]").getall()
            pub_time = get_accurate_pub_time(str(pub_time))
            info_source = self.area_province
            content = response.xpath('//*[@class="ewb-article-info"]').get()
            classify_show = response.meta.get("classify_show", "")
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = ""
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classify_show
            if name == const.TYPE_ZB_ALTERATION and re.search(r"终止|中止|流标|废标|异常", title_name):
                notice_item["notice_type"] = const.TYPE_ZB_ABNORMAL
            else:
                notice_item["notice_type"] = name
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl province_26_hubei_spider".split(" "))
    cmdline.execute("scrapy crawl province_26_hubei_spider -a sdt=2021-05-20 -a edt=2021-05-21".split(" "))
