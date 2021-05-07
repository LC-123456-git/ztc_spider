#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-18
# @Describe: 广西公共资源交易网
import re
import math
import json
import scrapy
import urllib
import dateutil.parser
import pytz
from datetime import datetime
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


def get_classify_show(category_num):
    if category_num == 84165:
        classify_show = "工程建设"
        return classify_show
    elif category_num == 84129:
        classify_show = "政府采购"
        return classify_show
    elif category_num == 84111:
        classify_show = "国有产权"
        return classify_show
    elif category_num == 84699:
        classify_show = "国有矿权"
        return classify_show
    elif category_num == 84102:
        classify_show = "药械采购"
        return classify_show

def get_notice_type(category_num, title_name):
    # 招标预告
    list_advance_notice_num = ["预公示"]
    # 招标公告
    list_notice_category_num = ["招标公告", "采购公告", "交易公告（地市级)", "交易公告（区本级）"]
    # 资格预审公告
    # list_qualifiction_advance_notice_num = ["002010002"]
    # 招标变更
    list_alteration_category_num = ["澄清变更", "更改公告"]
    # 中标预告
    list_win_advance_category_num = ["中标候选人公示"]
    # 中标公告
    list_win_notice_category_num = ["中标结果公示", "中标公告", "结果公示（区本级）", "结果公示（地市级）"]
    # 其他公告
    list_others_notice_num = ["上限价", "通知公告"]
    if category_num in list_advance_notice_num:
        cb_kwargs = const.TYPE_ZB_ADVANCE_NOTICE
        return cb_kwargs
    elif category_num in list_notice_category_num:
        cb_kwargs = const.TYPE_ZB_NOTICE
        return cb_kwargs
    elif re.search(r"资格预审", title_name):
        cb_kwargs = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        return cb_kwargs
    elif category_num in list_alteration_category_num:
        if category_num in ["002006002", "002008001", "002013002"] and re.search(r"变更", title_name):
            cb_kwargs = const.TYPE_ZB_ALTERATION
            return cb_kwargs
        else:
            cb_kwargs = const.TYPE_ZB_ALTERATION
            return cb_kwargs
    elif re.search(r"终止|中止|流标|废标|异常", title_name):
        cb_kwargs = const.TYPE_ZB_ABNORMAL
        return cb_kwargs
    elif category_num in list_win_advance_category_num or re.search(r"候选人", title_name):
            cb_kwargs = const.TYPE_WIN_ADVANCE_NOTICE
            return cb_kwargs
    elif category_num in list_win_notice_category_num:
        cb_kwargs = const.TYPE_WIN_NOTICE
        return cb_kwargs
    elif category_num in list_others_notice_num:
        cb_kwargs = const.TYPE_OTHERS_NOTICE
        return cb_kwargs


class MySpider(Spider):
    name = "province_33_guangxi_spider"
    area_id = "33"
    area_province = "广西"
    allowed_domains = ['gxggzy.gxzf.gov.cn']
    domain_url = "http://gxggzy.gxzf.gov.cn/"
    page_url = "http://gxggzy.gxzf.gov.cn/igs/front/search/list.html?"
    # info_url = "https://www.jxsggzy.cn/jxggzy/services/JyxxWebservice/getList?"
    # data_url = "https://www.jxsggzy.cn/web/jyxx"
    page_size = "10"

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"filter[DOCTITLE]": "", "pageSize": "1000", "index": "gxggzy_jyfw","type": "jyfw",
        "filter[parentparentid]":"", "filter[parentchnldesc]": "", "filter[chnldesc]": "", "filter[SITEID]": "",
        "orderProperty": "PUBDATE", "orderDirection": "desc", "filter[AVAILABLE]": "true"}
        self.page_dict = {"pageNumber": "1"}

        if kwargs.get("sdt") and kwargs.get("edt"):
            time_dict = {"prepostDate": kwargs.get("sdt"), "nxtpostDate": kwargs.get("edt"), }
        else:
            time_dict = {"prepostDate": "", "nxtpostDate": "", }  # TODO 默认为全量



    def start_requests(self):
        yield scrapy.Request(
            url=f"{self.page_url}{urllib.parse.urlencode(self.r_dict | self.page_dict)}",
            callback=self.parse_page_urls)

    def parse_page_urls(self, response):
        try:
            print("111111")
            pages = json.loads(response.text).get("page").get("totalPages")
            total = json.loads(response.text).get("page").get("total")
            self.logger.info(
                f"初始总数提取成功 {total=} {response.url=} ")
            for i in range(1, pages):
                yield scrapy.Request(
                    url=f"{self.page_url}{urllib.parse.urlencode(self.r_dict | {'pageIndex': str(i)})}",
                    callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            r_list = json.loads(response.text).get("page").get("content")
            for item in r_list:
                data_url = item.get("DOCPUBURL")
                pub_time = item.get("PUBDATE")
                title_name = item.get("DOCTITLE")
                notice_type = item.get("chnldesc")
                local_time = dateutil.parser.parse(pub_time).astimezone(pytz.timezone('Asia/Shanghai'))   # 解析string 并转换为北京时区
                pub_time = datetime.strftime(local_time, '%Y-%m-%d %H:%M:%S')
                classify_show = item.get("parentparentid")

                yield scrapy.Request(url=data_url, callback=self.parse_item, meta={
                     "title_name": title_name, "pub_time": pub_time, "notice_type": notice_type,
                    "classify_show": classify_show})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response):
        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:
            # print(response.text)
            origin = response.url
            title_name = response.meta["title_name"]
            print(origin)
            print(title_name)
            pub_time = response.meta["pub_time"]
            print(pub_time)
            info_source = response.xpath('//div[@class="ewb-details-sub"]/span/text()').get()

            print(info_source)
            if info_source:
                info_text = info_source.split("信息来源：")[1]
                info_source = f"{self.area_province} - {info_text}"
            else:
                info_source = self.area_province

            content = response.xpath('//*[@class="ewb-details-info"]').get()
            # print(content)

            category_num = response.meta["classify_show"]
            classify_show = get_classify_show(category_num)
            notice_type = get_notice_type(response.meta["notice_type"], title_name=title_name)
            files_path = {}
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

            # item
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = notice_type
            notice_item["category"] = classify_show

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_33_guangxi_spider".split(" "))
