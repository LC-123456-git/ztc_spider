#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-16
# @Describe: 安徽省公共资源交易网 - 全量/增量脚本
import re
import math
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, judge_dst_time_in_interval


def process_request_category(origin):
    if re.search("jsgc", origin):
        classify_show = "工程建设"
        return classify_show
    elif re.search("zfcg", origin):
        classify_show = "政府采购"
        return classify_show
    elif re.search("cqjy", origin):
        classify_show = "产权交易"
        return classify_show
    elif re.search("kyqcr", origin):
        classify_show = "土地矿权"
        return classify_show
    elif re.search("ppp", origin):
        classify_show = "PPP项目"
        return classify_show
    elif re.search("qtjy", origin):
        classify_show = "其他行业"
        return classify_show


class MySpider(CrawlSpider):
    name = 'province_16_anhui_spider'
    area_id = "16"
    area_province = "安徽省公共资源交易服务平台"
    domain_url = "http://ggzy.ah.gov.cn/"
    query_url = "http://ggzy.ah.gov.cn/{}/list"
    # query_page_url = "http://prec.sxzwfw.gov.cn/queryContent_{}-jyxx.jspx"
    allowed_domains = ['ggzy.ah.gov.cn']
    type_list = ["jsgc", "zfcg", "cqjy", "kyqcr", "ppp", "qtjy"]
    jsgc_list = ["A01", "A07", "AAA", "A99"]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        #          页数                    招标项目类型                   公告性质
        # r_dict = {"currentPage": "1", "tenderProjectType": "", "bulletinNature": "1", "jyptId": "", "region": ""}
        # page_dict = {"currentPage": "1"}
        # pro_type_dict = {"tenderProjectType": ""}

        # currentPage=1&bulletinNature=1&jyptId=&region=
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        if self.enable_incr:
            callback_url = self.extract_data_urls
        else:
            callback_url = self.parse_urls
        for item in self.type_list:
            if item == "jsgc":
                for i in self.jsgc_list:
                    for bid_type in ["1", "2", "3"]:
                        query_url = "http://ggzy.ah.gov.cn/{}/list".format(item)
                        yield scrapy.FormRequest(
                            query_url, formdata={"currentPage": "1"} | {"tenderProjectType": "{}".format(i)} |
                                                {"bulletinNature": "{}".format(bid_type)},
                            callback=callback_url, meta={"tenderProjectType": i, "bulletinNature": bid_type})
            else:
                query_url = "http://ggzy.ah.gov.cn/{}/list".format(item)
                for bid_type in ["1", "3"]:
                    yield scrapy.FormRequest(
                        query_url, formdata={"currentPage": "1"} | {"bulletinNature": "{}".format(bid_type)},
                        callback=callback_url, meta={"tenderProjectType": "", "bulletinNature": bid_type})

    def parse_urls(self, response):
        try:
            query_page_url = response.url
            pages = re.search(r"共\d+页", response.text).group(0)
            pages = int(re.search(r"\d+", pages).group(0))
            limit = 10
            total = pages * limit
            self.logger.info(
                f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            for i in range(1, pages):
                yield scrapy.FormRequest(query_page_url, formdata={"currentPage": "{}".format(i)} |
                      {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                callback=self.parse_data_urls, meta={"tenderProjectType": response.meta["bulletinNature"],
                                               "bulletinNature": response.meta.get("bulletinNature")})
        except Exception as e:
            self.logger.error(f"初始链接提取错误：{response.url=} {response.meta=} {e}")

    def extract_data_urls(self, response,):
        url = response.url
        pages = re.search(r"共\d+页", response.text).group(0)
        pages = int(re.search(r"\d+", pages).group(0))
        data_url = re.sub("list", "newDetailSub", url)
        # limit = 10
        # start_limit = 0
        currentPage = 1
        li_list = response.xpath('//div[@class="list clear"]/ul[2]/li')
        for li in range(len(li_list)):
            pub_time = li_list[li].xpath("./span/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
            if x:
                #如果符合条件访问详情页
                info_source = li_list[li].xpath("./a/span[1]/text()").get()
                title_name = li_list[li].xpath("./a/span[2]/@title").get()
                href_url = li_list[li].xpath("./a/@href").get()
                origin = self.domain_url + href_url
                s_url = href_url.split("?")[1]
                url_dict = urllib.parse.parse_qs(s_url)
                guid = url_dict.get("guid")[0]
                type_num = response.meta.get("bulletinNature")
                if re.search("jsgc", url):
                    if type_num == "1":
                        self.type_str = "tender"
                    elif type_num == "2" or type_num == "3":
                        self.type_str = "zbjg"
                    yield scrapy.FormRequest(data_url, formdata={"type": self.type_str} | {"guid": guid} |
                         {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                         callback=self.parse_item, meta={"tenderProjectType": response.meta["bulletinNature"],
                                                         "bulletinNature": response.meta.get("bulletinNature"),
                                                         "info_source": info_source, "title_name": title_name,
                                                         "pub_time": pub_time, "origin": origin})
                elif re.search("zfcg", url) or re.search("ppp", url):
                    if type_num == "1":
                        self.type_str = "bulletin"
                    elif type_num == "3":
                        self.type_str = "zbjg"
                    yield scrapy.FormRequest(data_url, formdata={"type": self.type_str} | {"guid": guid} |
                                                            {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                                         callback=self.parse_item, meta={"tenderProjectType": response.meta["bulletinNature"],
                                                                         "bulletinNature": response.meta.get("bulletinNature"),
                                                                         "info_source": info_source, "title_name": title_name,
                                                                         "pub_time": pub_time, "origin": origin})
                else:
                    yield scrapy.Request(url=origin, callback=self.parse_item,
                                         meta={"tenderProjectType": response.meta["bulletinNature"],
                                               "bulletinNature": response.meta.get("bulletinNature"),
                                               "info_source": info_source, "title_name": title_name,
                                               "pub_time": pub_time, "origin": origin})
                # 并且翻页
                # start_limit += 1
                if li + 1 >= len(li_list):
                    next_page = currentPage + 1
                    if next_page <= pages:
                        yield scrapy.FormRequest(url, formdata={"currentPage": "{}".format(next_page)} |
                                                  {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                                                 callback=self.extract_data_urls, meta={
                                "tenderProjectType": response.meta["bulletinNature"],
                                "bulletinNature": response.meta.get("bulletinNature")})


    def parse_data_urls(self, response):
        li_list = response.xpath('//div[@class="list clear"]/ul[2]/li')
        url = response.url
        data_url = re.sub("list", "newDetailSub", url)
        for li in li_list:
            info_source = li.xpath("./a/span[1]/text()").get()
            title_name = li.xpath("./a/span[2]/@title").get()
            pub_time = li.xpath("./span/text()").get()
            href_url = li.xpath("./a/@href").get()
            origin = self.domain_url + href_url
            s_url = href_url.split("?")[1]
            url_dict = urllib.parse.parse_qs(s_url)
            guid = url_dict.get("guid")[0]
            type_num = response.meta.get("bulletinNature")
            if re.search("jsgc", url):
                if type_num == "1":
                    self.type_str = "tender"
                elif type_num == "2" or type_num == "3":
                    self.type_str = "zbjg"
                yield scrapy.FormRequest(data_url, formdata={"type": self.type_str} | {"guid": guid} |
                                        {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                                         callback=self.parse_item, meta={"tenderProjectType": response.meta["bulletinNature"],
                                                                         "bulletinNature": response.meta.get("bulletinNature"),
                                                                         "info_source": info_source, "title_name": title_name,
                                                                         "pub_time": pub_time, "origin": origin})
            elif re.search("zfcg", url) or re.search("ppp", url):
                if type_num == "1":
                    self.type_str = "bulletin"
                elif type_num == "3":
                    self.type_str = "zbjg"
                yield scrapy.FormRequest(data_url, formdata={"type": self.type_str} | {"guid": guid} |
                                    {"bulletinNature": "{}".format(response.meta["bulletinNature"])},
                                    callback=self.parse_item, meta={"tenderProjectType": response.meta["bulletinNature"],
                                    "bulletinNature": response.meta.get("bulletinNature"),
                                    "info_source": info_source, "title_name": title_name,
                                    "pub_time": pub_time, "origin": origin})
            else:
                yield scrapy.Request(url=origin, callback=self.parse_item,
                                     meta={"tenderProjectType": response.meta["bulletinNature"],
                                           "bulletinNature": response.meta.get("bulletinNature"),
                                           "info_source": info_source, "title_name": title_name,
                                           "pub_time": pub_time, "origin": origin})

    def parse_item(self, response):
        if response.status == 200:
            print("sssss")
            origin = response.meta["origin"]
            title_name = response.xpath('//p[@class="article-title clamp-3 m-b-15"]/text()').get()
            # title_name = response.meta["title_name"]
            pub_time = response.meta["pub_time"]
            info_source = response.meta["info_source"]
            tenderProjectType = response.meta["tenderProjectType"]
            info_list = re.split("-", re.sub("【", "", info_source))
            info_str = info_list[0] + info_list[1]
            info_source = re.sub("市辖区", "", info_str)
            if not title_name:
                title_name = response.xpath('//*[@id="tender"]/p/text()').get()
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            if tenderProjectType == "1":
                self.notice_type = const.TYPE_ZB_NOTICE
            elif tenderProjectType == "2":
                self.notice_type = const.TYPE_WIN_ADVANCE_NOTICE
            elif tenderProjectType == "3":
                self.notice_type = const.TYPE_WIN_NOTICE

            if re.search(r"终止|中止|流标|废标|异常", title_name):
                self.notice_type = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正", title_name):
                self.notice_type = const.TYPE_ZB_ALTERATION
            content = response.xpath("//*[@class='article-text-box m-b-50 m-t-50']").get()
            pub_time = get_accurate_pub_time(pub_time)
            print(origin)
            print(title_name)
            print(pub_time)
            # print(content)

            files_path = []
            # if content:
            #     pub_time_simple = pub_time.split(" ")[0]
            #     if files := re.findall(r"http://www.sxyxcg.com/UploadFile/.*?\"", content):
            #         for item in files:
            #             item = item.replace("\"", "")
            #             file_item = FileItem()
            #             unquote_name = parse.unquote(item).split("/")[-1]
            #             file_item["file_url"] = parse.urljoin(self.domain_url, item)
            #             file_item["file_name"] = unquote_name.split('.')[0]
            #             file_item["file_type"] = unquote_name.split('.')[1]
            #             file_item["file_path"] = fr"{self.name}/{pub_time_simple}/{unquote_name}"
            #             files_path.append(file_item["file_path"])
            #             yield file_item
            classify_show = process_request_category(origin)
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["notice_type"] = self.notice_type
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classify_show
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_16_anhui_spider -a sdt=2021-03-19 -a edt=2021-03-19".split(" "))