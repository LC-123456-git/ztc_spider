#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-01-07
# @Describe: 山东公共资源交易平台 - 全量/增量脚本
#
import re
import math
import json
import scrapy
import urllib
import datetime
from urllib import parse
from spider_pro.utils import get_real_url
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_iframe_pdf_div_code


class MySpider(CrawlSpider):
    name = 'province_21_shandong_spider'
    area_id = "21"
    domain_url = "http://ggzyjy.shandong.gov.cn"
    query_url = "http://ggzyjy.shandong.gov.cn/queryContent-jyxxgk.jspx"
    allowed_domains = ['ggzyjy.shandong.gov.cn']
    # 招标公告
    list_notice_category_num = ["招标/资审公告", "采购/资审公告", "出让公示", "挂牌披露", "采购公告", "交易公告",
                                "交易公告"]
    # 中标预告
    list_win_advance_category_num = ["中标候选人公示"]
    list_win_notice_category_num = ["中标公示"]

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"title": "", "origin": "", "channelId": "151", "ext": "",
                       "inDates": kwargs.get("day") if not kwargs.get("day") == "0" else "3650", }

    def start_requests(self):
        self.r_dict = {k: v if v else '' for k, v in self.r_dict.items()}
        yield scrapy.FormRequest(self.query_url, formdata=self.r_dict, callback=self.parse_urls, priority=6)

    def parse_urls(self, response):
        try:
            ttlrow = re.search(r"共\d+条", response.text)
            self.logger.info(f"本次获取总条数为：{ttlrow}")
            if pages_str := re.search(r"totalPage = \d+", response.text):
                pages = int(re.search(r"\d+", pages_str.group(0)).group(0))
                pages = int(pages) + 1
                for i in range(1, pages):
                    if not i == 1:
                        self.query_url = "http://ggzyjy.shandong.gov.cn/queryContent_{}-jyxxgk.jspx".format(i)
                    else:
                        self.query_url = "http://ggzyjy.shandong.gov.cn/queryContent-jyxxgk.jspx"
                    yield scrapy.FormRequest(self.query_url, formdata=self.r_dict, callback=self.parse_data_urls, priority=8)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            li_list = response.xpath("/html/body/div[4]/div[2]/div/ul/li")
            for item in li_list:
                data_url = item.xpath("./div/a/@href").get()
                data_url = get_real_url(data_url)
                title_name_list = item.xpath("./div/a/text()").getall()
                title_name = "".join(title_name_list[2:])
                pub_time = item.xpath("./div/div[@class='list-times']/text()").get()
                item_1 = item.xpath("./div[@class='article-list3-t2']").get()
                info_source = re.search(r"信息来源：\w+", item_1).group(0)
                info_source = info_source.split("信息来源：")[1]
                classifyShow = re.search(r"业务类型：\w+", item_1).group(0)
                classifyShow = classifyShow.split("业务类型：")[1]
                category_num = item_1.split("信息分类：")[1]
                category_num = category_num.split("</div>")[0]
                if category_num in self.list_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif category_num in self.list_win_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
                elif category_num in self.list_win_advance_category_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
                else:
                    self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

                yield scrapy.Request(url=data_url, callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     priority=10, meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                                        "title_name": title_name, "pub_time": pub_time,
                                                        "classifyShow": classifyShow})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            print(title_name)
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//table[@class="gycq-table"]').get()
            files_path = {}
            is_clean = True
            # 判断是pdf页面
            try:
                if url_str := re.search(r'''<a id='pdfUrl' href=".*?">''', response.text):
                    url_pdf_str = url_str.group(0).split(r'''<a id='pdfUrl' href="''')[1].split(r'''">''')[0]
                    url_pdf_str_list = [self.domain_url]
                    url_pdf_str_list.extend(url_pdf_str.split('/')[-3:])
                    url_pdf = '/'.join(url_pdf_str_list)
                    url_pdf_date = url_pdf.split('/')[-2]
                    file_item = FileItem()
                    unquote_name = parse.unquote(url_pdf).split("/")[-1]
                    file_item["file_url"] = url_pdf
                    file_item["file_name"] = unquote_name.split('.')[0]
                    file_item["file_type"] = unquote_name.split('.')[1]
                    file_item["file_path"] = fr"{self.name}/{url_pdf_date}/{unquote_name}"
                    # files_path.append(file_item["file_path"])
                    is_clean = False
                    # TODO 替换成本站链接
                    content = get_iframe_pdf_div_code(url=url_pdf)
                    yield file_item
            except Exception as e:
                pass
            if re.search(r"候选人", title_name):
                name = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                name = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正", title_name):
               name = const.TYPE_ZB_ALTERATION

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = response.meta.get("info_source")
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["notice_type"] = name
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = response.meta.get("classifyShow")

            # TODO 产品要求推送，故注释
            # # if not is_clean:
            #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_21_shandong_spider -a day=1".split(" "))
    # cmdline.execute("scrapy crawl province_21_shandong_spider -a sdt=2021-03-01 -a edt=2021-03-01".split(" "))
    # cmdline.execute("scrapy crawl province_21_shandong_spider".split(" "))
