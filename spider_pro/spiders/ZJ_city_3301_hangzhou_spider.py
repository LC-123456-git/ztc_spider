#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-30
# @Describe: 杭州公共资源交易网
import re
import math
import json
import scrapy
import urllib
import requests
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date


class MySpider(Spider):
    name = "ZJ_city_3301_hangzhou_spider"
    area_id = "3301"
    area_province = "浙江-杭州市"
    allowed_domains = ['hzctc.cn']
    domain_url = "https://ggzy.hzctc.hangzhou.gov.cn/"
    count_url = "https://ggzy.hzctc.hangzhou.gov.cn/SecondPage/GetNotice"
    data_url = "https://ggzy.hzctc.hangzhou.gov.cn/afficheshow/Home?"
    flie_url = "https://ggzy.hzctc.hangzhou.gov.cn:20001/UService/DownloadAndShow.aspx?dirtype=3&filepath="
    page_size = "10"
    # 招标公告
    list_notice_category_num = ["22", "27", "39", "58", "34"]
    # 招标变更
    list_alteration_category_num = ["23", "465", "466", "29", "40", "467", "96", "468", "469", "499"]
    # 中标预告
    list_win_advance_notice_num = ["25", "37"]
    # 中标公告
    list_win_notice_category_num = ["28", "32", "42", "97"]
    # 其他公告
    list_other_notice = ["486", "26"]

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_advance_notice_num +\
                            list_win_notice_category_num + list_other_notice
    # project_category_dict = {
    #     "002001": "工程建设",
    #     "002002": "政府采购",
    #     "002003": "药品采购",
    #     "002004": "产权交易",
    #     "002005": "土地及矿业权"}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {'area': '', 'IsToday': '', 'title': '', 'proID': '', 'number': '',
                  '_search': 'false', 'nd': '1617083532556', 'rows': '10', 'sidx': 'PublishStartTime',
                  'sord': 'desc'}
        # if day := kwargs.get("day"):
        #     time_dict = {"sdt": "" if day == "0" else get_back_date(int(day) - 1),
        #                  "edt": "" if day == "0" else get_back_date(0)}
        # elif kwargs.get("sdt") and kwargs.get("edt"):
        #     time_dict = {"sdt": kwargs.get("sdt"), "edt": kwargs.get("edt"), }
        # else:
        #     # time_dict = {"sdt": get_back_date(0), "edt": get_back_date(0), }
        #     time_dict = {"sdt": "", "edt": "", }  # TODO 默认为全量
        # self.info_dict = {"pageSize": self.page_size} | r_dict | time_dict
        # self.count_dict = r_dict | time_dict

    def start_requests(self):
        for item in self.list_all_category_num:
        #     temp_dict = self.r_dict | {"afficheType": str(item)} | {'page': '1'}
        #     yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_urls, priority=7,
        #                              meta={"afficheType": str(item)})
        # item = 22
            temp_dict = self.r_dict | {"afficheType": str(item)} | {'page': '1'}
            yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_urls, priority=7,
                                     meta={"afficheType": str(item)})

    def parse_urls(self, response):
        try:
            response_text = json.loads(response.text)
            ttlrow = response_text.get("records", "")
            current_page = response_text.get("page", "")
            pages = response_text.get("total", "")
            afficheType = response.meta["afficheType"]
            self.logger.info(f"本次获取总条数为：{ttlrow},当前为第{current_page}页，共有{pages}页")
            for i in range(1, pages):
                temp_dict = self.r_dict | {"afficheType": response.meta["afficheType"]} | {'page': str(i)}
                yield scrapy.FormRequest(self.count_url, formdata=temp_dict, dont_filter=True, priority=8,
                                         callback=self.parse_data_urls, meta={"afficheType": afficheType})
                # yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_data_urls, priority=8,
                #                          meta={"afficheType": response.meta["afficheType"]})
            # temp_dict = self.r_dict | {"afficheType": response.meta["afficheType"]} | {'page': '1'}
            # print(temp_dict)
            # yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            response_text = json.loads(response.text)
            temp_list = response_text.get("rows", "")
            afficheType = response.meta["afficheType"]
            for item in temp_list:
                info_source = item.get("CodeName", "")
                title_name = item.get("TenderName", "")
                AfficheID = item.get("ID", "")
                IsInner = item.get("IsInner", "")
                pub_time = item.get("PublishStartTime", "")
                category_num = response.meta["afficheType"]
                if category_num in self.list_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
                elif category_num in self.list_alteration_category_num:
                    self.cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
                elif category_num in self.list_win_notice_category_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
                elif category_num in self.list_win_advance_notice_num:
                    self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
                elif category_num in self.list_other_notice:
                    self.cb_kwargs = {"name": const.TYPE_OTHERS_NOTICE}
                else:
                    self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

                if afficheType in ["22", "23", "465", "486", "25", "28"]:
                    self.classifyShow = "工程建设"
                elif afficheType in ["27", "26", "466", "29", "32"]:
                    self.classifyShow = "政府采购"
                elif afficheType in ["39", "40", "467", "42"]:
                    self.classifyShow = "土地矿业"
                elif afficheType in ["58", "96", "468", "97"]:
                    self.classifyShow = "产权交易"
                elif afficheType in ["34", "496", "499", "37"]:
                    self.classifyShow = "综合其他"

                data_dict = {"AfficheID": AfficheID, "IsInner": IsInner, "ModuleID": afficheType}
                # url = "https://ggzy.hzctc.hangzhou.gov.cn/afficheshow/Home?Affic...sInner=3&ModuleID=32"
                # yield scrapy.Request(url=url,
                #                      callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                #                      meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                #                            "classifyShow": self.classifyShow, "pub_time": pub_time,
                #                            "title_name":title_name})
                yield scrapy.Request(url=f"{self.data_url}{urllib.parse.urlencode(data_dict)}", priority=10,
                                     callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                           "classifyShow": self.classifyShow, "pub_time": pub_time,
                                           "title_name": title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            info_source = response.meta.get("info_source")
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            if info_source:
                if info_source in ["桐庐"]:
                    info_city = info_source + "县"
                elif info_source in ["建德"]:
                    info_city = info_source + "市"
                elif info_source in ["钱塘"]:
                    info_city = info_source + "新区"
                else:
                    info_city = info_source + "区"
                info_source = f"{self.area_province}-{info_city}"
            else:
                info_source = self.area_province
            # content = response.xpath("/html/body/div[4]/div[2]/div[5]").get()
            content = response.xpath('//div[@class="MainList"]').get()
            # if re.search(r"gb2312", content):
            #     self.temp_content = re.sub("gb2312", "utf-8", content)
            files_path = {}
            try:
                if re.search(r'相关公告', content):
                    pattern = re.compile(r'<div style="margin-bottom:50px;border-top:1px dashed #d4d4d4;border-bottom:1px dashed #d4d4d4;padding:8px 0;".*?>(.*?)</ul>', re.S)
                    content = content.replace(re.findall(pattern, content)[0], '')

                if re.search(r"网上提疑", content):
                    rule = re.compile(r'<table class="MsoNormalTable" style="border: none; border-collapse: collapse;".*?>(.*?)</table>', re.S)
                    content = content.replace(re.findall(rule, content)[0], '')


                is_clean = True
            # 判断是pdf页面
                files_list = []
                if url_str := re.search(r'''<iframe frameborder="0" src=".*?" style=''', response.text):
                    url_pdf_str = url_str.group(0).split(r'''<iframe frameborder="0" src="''')[1].split(r'''" style=''')[0]
                    iframe_pdf = url_pdf_str.replace("&amp;", "&")
                    files_path["{}".format(iframe_pdf)] = iframe_pdf
                else:
                    # url_pdf_str_list = [self.domain_url]
                    # url_pdf_str_list.extend(url_pdf_str.split('/')[-3:])
                    # url_pdf = '/'.join(url_pdf_str_list)
                    # url_pdf_date = url_pdf.split('/')[-2]
                    # file_item = FileItem()
                    # unquote_name = parse.unquote(url_pdf).split("/")[-1]
                    # file_item["file_url"] = url_pdf
                    # file_item["file_name"] = unquote_name.split('.')[0]
                    # file_item["file_type"] = unquote_name.split('.')[1]
                    # file_item["file_path"] = fr"{self.name}/{url_pdf_date}/{unquote_name}"
                    # files_path.append(file_item["file_path"])
                    is_clean = False
                    # TODO 替换成本站链接
                    # content = get_iframe_pdf_div_code(url=url_pdf)
                    # yield file_item

                if a_list := response.xpath('//ul[@class="fjxx"]//a'):
                    for item in a_list:
                        value = item.xpath('./@href').get()
                        key = item.xpath('./text()').get()
                        files_path[key] = value
                if a_list := response.xpath("//div[@style='border-top:1px dashed #d4d4d4;padding:8px 0;']/ul//a"):
                    for item in a_list:
                        if file_text := item.xpath("./@onclick").get():
                            file_text = file_text.split("('")[1].split("')")[0].replace("'", "")
                            file_desc = file_text.split(",")[0]
                            file_path_num = file_text.split(",")[1].replace(" ", "")
                            url = "https://ggzy.hzctc.hangzhou.gov.cn/AfficheShow/GetDownLoadUrl?FileDesc={}&FilePath={}&DirType=3".format(file_desc, file_path_num)
                            payload = {}
                            headers = {}
                            url_str = requests.request("POST", url, headers=headers, data=payload)
                            file_path_str = "<a href='{}'>{}</a>".format(response.text, file_desc)
                            files_list.append(file_path_str)
                            key = file_path_num
                            files_path[key] = str(url_str.text)
                        else:
                            continue
                file_paths = "<br/>".join(files_list)
                com = re.compile('<li style.*>.*</li>', re.S)
                content = com.sub(file_paths, content)
            except Exception as e:
                print(e)
                pass
            if re.search(r"候选人", title_name):
                self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
            elif re.search(r"变更|更正", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "null" if not files_path else files_path
            notice_item["notice_type"] = name
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["category"] = classifyShow
            # TODO 产品要求推送，故注释
            # if not is_clean:
            #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl ZJ_city_3301_hangzhou_spider -a std=2021-06-09 -a edt=2021-06-09".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3301_hangzhou_spider".split(" "))
