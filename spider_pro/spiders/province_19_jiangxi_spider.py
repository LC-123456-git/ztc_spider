#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-08
# @Describe: 江西省公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


def get_classify_show( category_num):
    if category_num[0:6] == "002001":
        classify_show = "房建及市政工程"
        return classify_show
    elif category_num[0:6] == "002002":
        classify_show = "交通工程"
        return classify_show
    elif category_num[0:6] == "002003":
        classify_show = "水利工程"
        return classify_show
    elif category_num[0:6] == "002005":
        classify_show = "重点工程"
        return classify_show
    elif category_num[0:6] == "002006":
        classify_show = "政府采购"
        return classify_show
    elif category_num[0:6] == "002007":
        classify_show = "国土资源交易"
        return classify_show
    elif category_num[0:6] == "002008":
        classify_show = "产权交易"
        return classify_show
    elif category_num[0:6] == "002009":
        classify_show = "林权交易"
        return classify_show
    elif category_num[0:6] == "002010":
        classify_show = "医药采购"
        return classify_show
    elif category_num[0:6] == "002013":
        classify_show = "其它项目"
        return classify_show


def get_notice_type(category_num, title_name):
    # 招标预告
    list_advance_notice_num = ["002002006", "002006007"]
    # 招标公告
    list_notice_category_num = ["002001001", "002002002", "002003001", "002005001", "002006001", "002006005", "002007001",
                                "002008001", "002009001", "002010001", "002013001"]
    # 资格预审公告
    list_qualifiction_advance_notice_num = ["002010002"]
    # 招标变更
    list_alteration_category_num = ["002001002", "002002003", "002003002", "002005002", "002006002", "002006003",
                                    "002008001", "002013002"]
    # 招标异常
    list_zb_abnormal = ["002013002", "002006004", "002006002"]
    # 中标预告
    list_win_advance_category_num = ["002001004", "002002005", "002003004", "002005004", "002006004"]
    # 中标公告
    list_win_notice_category_num = ["002001004", "002002005", "002003005", "002005004", "002006004", "002007002",
                                    "002008002", "002009002", "002010002", "002013002"]
    # 其他公告
    list_others_notice_num = ["002001003", "002003003", "002005003", "002006006"]
    all_list = list_advance_notice_num + list_notice_category_num + list_qualifiction_advance_notice_num + \
               list_alteration_category_num + list_zb_abnormal + list_win_advance_category_num + \
               list_win_notice_category_num + list_others_notice_num

    if category_num in list_advance_notice_num:
        cb_kwargs = const.TYPE_ZB_ADVANCE_NOTICE
        return cb_kwargs
    elif category_num in list_notice_category_num:
        cb_kwargs = const.TYPE_ZB_NOTICE
        return cb_kwargs
    elif category_num in list_qualifiction_advance_notice_num and re.search(r"审核结果", title_name):
        cb_kwargs = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
        return cb_kwargs
    elif category_num in list_alteration_category_num:
        if category_num in ["002006002", "002008001", "002013002"] and re.search(r"变更", title_name):
            cb_kwargs = const.TYPE_ZB_ALTERATION
            return cb_kwargs
        else:
            cb_kwargs = const.TYPE_ZB_ALTERATION
            return cb_kwargs
    elif category_num in list_zb_abnormal and re.search(r"终止|中止|流标|废标|异常", title_name):
        cb_kwargs = const.TYPE_ZB_ABNORMAL
        return cb_kwargs
    elif category_num in list_win_advance_category_num:
        if category_num in ["002001004", "002002005", "002005004", "002006004"] and re.search(r"结果|候选人", title_name):
            cb_kwargs = const.TYPE_WIN_ADVANCE_NOTICE
            return cb_kwargs
        elif category_num in ["002010002"] and re.search(r"候选人", title_name):
            cb_kwargs = const.TYPE_WIN_ADVANCE_NOTICE
            return cb_kwargs
        elif category_num in ["002013002"] and re.search(r"中标|结果|成交", title_name):
            cb_kwargs = const.TYPE_WIN_ADVANCE_NOTICE
            return cb_kwargs
    elif category_num in list_win_notice_category_num:
        cb_kwargs = const.TYPE_WIN_NOTICE
        return cb_kwargs
    elif category_num in list_others_notice_num:
        cb_kwargs = const.TYPE_OTHERS_NOTICE
        return cb_kwargs


class MySpider(Spider):
    name = "province_19_jiangxi_spider"
    area_id = "19"
    area_province = "江西公共资源交易服务平台"
    allowed_domains = ['jxsggzy.cn']
    domain_url = "https://www.jxsggzy.cn/"
    page_url = "https://www.jxsggzy.cn/jxggzy/services/JyxxServicesForWeb/getListByCount?"
    info_url = "https://www.jxsggzy.cn/jxggzy/services/JyxxServicesForWeb/getList?"
    data_url = "https://www.jxsggzy.cn/web/jyxx"
    page_size = "22"
    # 招标预告
    list_advance_notice_num = ["002002006", "002006007"]
    # 招标公告
    list_notice_category_num = ["002001001", "002002002", "002003001", "002005001", "002006001", "002006005", "002007001",
                                "002008001", "002009001", "002010001", "002013001"]
    # 资格预审公告
    list_qualifiction_advance_notice_num = ["002010002"]
    # 招标变更
    list_alteration_category_num = ["002001002", "002002003", "002003002", "002005002", "002006002", "002006003",
                                    "002008001", "002013002"]
    # 招标异常
    list_zb_abnormal = ["002013002", "002006004", "002006002"]
    # 中标预告
    list_win_advance_category_num = ["002001004", "002002005", "002003004", "002005004", "002006004"]
    # 中标公告
    list_win_notice_category_num = ["002001004", "002002005", "002003005", "002005004", "002006004", "002007002",
                                    "002008002", "002009002", "002010002", "002013002"]
    # 其他公告
    list_others_notice_num = ["002001003", "002003003", "002005003", "002006006"]
    all_list = list_advance_notice_num + list_notice_category_num + list_qualifiction_advance_notice_num + \
               list_alteration_category_num + list_zb_abnormal + list_win_advance_category_num + \
               list_win_notice_category_num + list_others_notice_num

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        r_dict = {"response": "application/json", "area": "", "xxTitle": "", "pageSize": "22", "categorynum": ""}
        # self.page_dict = {"pageIndex": "", "pageSize": "22"}

        if kwargs.get("sdt") and kwargs.get("edt"):
            time_dict = {"prepostDate": kwargs.get("sdt"), "nxtpostDate": kwargs.get("edt"), }
        else:
            time_dict = {"prepostDate": "", "nxtpostDate": "", }  # TODO 默认为全量

        self.info_dict = r_dict | time_dict

    def start_requests(self):
        for item in self.all_list:
            yield scrapy.Request(
                url=f"{self.page_url}{urllib.parse.urlencode(self.info_dict | {'categorynum':item})}",
                priority=5, callback=self.parse_page_urls)

    def parse_page_urls(self, response):
        try:
            total = json.loads(response.text).get("return")
            pages = total // 22 + 1
            self.logger.info(
                f"初始总数提取成功 {total=} {response.url=} ")
            for i in range(1, pages):
                yield scrapy.Request(
                    url=f"{self.info_url}{urllib.parse.urlencode(self.info_dict | {'pageIndex': str(i)})}",
                    priority=8, callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            r_list = json.loads(json.loads(response.text).get('return')).get('Table')
            for item in r_list:
                pub_time = item.get("postdate")
                title_name = item.get("title")
                category_num = item.get("categorynum")
                info_id = item.get("infoid")
                if pub_time_str := re.search(r"\d{4}-\d{1,2}-\d{1,2}", pub_time):
                    self.pub_time_a = pub_time_str.group(0).replace("-", "")
                temp_url = "/".join([self.data_url, category_num[0:6], category_num, self.pub_time_a, info_id + ".html"])
                yield scrapy.Request(url=temp_url, callback=self.parse_item, priority=10, meta={
                     "title_name": title_name, "pub_time": pub_time, "category_num": category_num})
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
            title_name = response.meta["title_name"]
            title_name = re.sub("^\[.*?\]", "", re.sub("<.*?>", "", re.sub("\[非网招\]", "",
                         re.sub("\[线下\]", "", re.sub("\[.*?\[\d+\].*?]", "",
                         re.sub("\[.*?\【\d+\】.*?]", "", title_name))))))
            print("处理后：~~~~~~~~~~~~~~~~~~~~" + title_name)
            pub_time = response.meta["pub_time"]
            info_source = self.area_province
            content = response.xpath('//*[@class="con"]').get()
            # contents = re.split('<div class="buttonDiv">', content)[0]
            # 正则去掉向左偏移量，去掉多余字符串，去掉按钮
            content = re.sub("margin-left: -\d+px;", "", re.sub("招标投标格式文本二", "",
                      re.sub('<div class="buttonDiv"><a.*?金融服务</a></div>', "",
                      re.sub('<div class="buttonDiv"><a.*?查看操作说明</a></div>', "",
                      re.sub('<div class="buttonDiv"><a.*?交易主体登录</a></div>', "",
                      re.sub('<input type="button".*?value="打 印">', "",
                      re.sub('<a class="buttomlink".*?>查看操作说明</a>', "",
                      re.sub('<a class="buttomlink".*?>交易主体登录</a>', "", content))))))))
            # print(content)

            category_num = response.meta["category_num"]
            classify_show = get_classify_show(category_num)
            notice_type = get_notice_type(category_num, title_name=title_name)
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

            # item
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = notice_type
            notice_item["category"] = classify_show

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_19_jiangxi_spider".split(" "))
