#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-04-09
# @Describe: 丽水公共资源交易网
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


class MySpider(Spider):
    name = "ZJ_city_3311_lishui_spider"
    area_id = "3311"
    area_province = "浙江-丽水市公共资源交易服务平台"
    allowed_domains = ['lssggzy.lishui.gov.cn']
    domain_url = "http://lssggzy.lishui.gov.cn"
    # count_url = "https://www.hzctc.cn/SecondPage/GetNotice"
    # data_url = "https://www.hzctc.cn/afficheshow/Home?"
    # flie_url = "https://www.hzctc.cn:20001/UService/DownloadAndShow.aspx?dirtype=3&filepath="
    page_size = "10"
    # 招标公告
    list_notice_category_num = ['071001001001', '071001001002', '071001001003', '071001001004', '071001001005',
                                '071001001006', '071001001007', '071001001008', '071001001009', '071001001010',
                                '071002002001', '071002002002', '071002002003', '071002002004', '071002002005',
                                '071002002006', '071002002007', '071002002008', '071002002009', '071002002010',
                                '071003001001', '071003001002', '071003001003', '071003001004', '071003001005',
                                '071003001006', '071003001007', '071003001008', '071003001009', '071003001010',
                                '071004001001', '071004001002', '071004001003', '071004001004', '071004001005',
                                '071004001006', '071004001007', '071004001008', '071004001009', '071004001010',
                                '071005001001', '071005001002', '071005001003', '071005001004', '071005001005',
                                '071005001006', '071005001007', '071005001008', '071005001009', '071005001010']

    # 招标变更
    list_alteration_category_num = ['071001002001', '071001002002', '071001002003', '071001002004', '071001002005',
                                    '071001002006', '071001002007', '071001002008', '071001002009', '071001002010',
                                    '071002003001', '071002003002', '071002003003', '071002003004', '071002003005',
                                    '071002003006', '071002003007', '071002003008', '071002003009', '071002003010']
    # 中标预告
    list_win_advance_notice_num = ['071001004001', '071001004002', '071001004003', '071001004004', '071001004005',
                                   '071001004006', '071001004007', '071001004008', '071001004009', '071001004010']
    # 中标公告
    list_win_notice_category_num = ['071001005001', '071001005002', '071001005003', '071001005004', '071001005005',
                                    '071001005006', '071001005007', '071001005008', '071001005009', '071001005010',
                                    '071002005001', '071002005002', '071002005003', '071002005004', '071002005005',
                                    '071002005006', '071002005007', '071002005008', '071002005009', '071002005010',
                                    '071003003001', '071003003002', '071003003003', '071003003004', '071003003005',
                                    '071003003006', '071003003007', '071003003008', '071003003009', '071003003010',
                                    '071004003001', '071004003002', '071004003003', '071004003004', '071004003005',
                                    '071004003006', '071004003007', '071004003008', '071004003009', '071004003010',
                                    '071005003001', '071005003002', '071005003003', '071005003004', '071005003005',
                                    '071005003006', '071005003007', '071005003008', '071005003009', '071005003010']
    # 其他公告
    list_other_notice = ['071001003001', '071001003002', '071001003003', '071001003004', '071001003005', '071001003006',
                         '071001003007', '071001003008', '071001003009', '071001003010', '071002001001', '071002001002',
                         '071002001003', '071002001004', '071002001005', '071002001006', '071002001007', '071002001008',
                         '071002001009', '071002001010']


    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_advance_notice_num + \
                            list_win_notice_category_num + list_other_notice
    project_category_dict = {
        "071001": "建设工程",
        "071002": "政府采购",
        "071003": "产权交易",
        "071004": "国土交易",
        "071005": "其他交易"}
    info_dict = {"01": "市级",
                 "02": "莲都",
                 "03": "龙泉",
                 "04": "青田",
                 "05": "云和",
                 "06": "庆元",
                 "07": "缙云",
                 "08": "遂昌",
                 "09": "松阳",
                 "10": "景宁"}

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()

    def start_requests(self):
        for item in self.list_all_category_num:
        # item = "071001001001"
            count_url = "http://lssggzy.lishui.gov.cn/lsweb/jyxx/{}/{}/{}/".format(item[0:6], item[0:9], item[0:12])
            yield scrapy.Request(count_url, callback=self.parse_urls, priority=0,
                                 meta={"afficheType": str(item)})

    def parse_urls(self, response):
        try:
            # response_text = json.loads(response.text)
            afficheType = response.meta["afficheType"]
            pages_text = response.xpath("//td[@class='huifont']/text()").get()
            pages = pages_text.split('/')[1]
            self.logger.info(f"本次获取共有{pages}页")
            for i in range(1, int(pages)):
                if i == 1:
                    count_url = "http://lssggzy.lishui.gov.cn/lsweb/jyxx/{}/{}/{}/".format(afficheType[0:6],
                                                                                           afficheType[0:9],
                                                                                           afficheType[0:12])
                    yield scrapy.Request(count_url, callback=self.parse_data_urls, priority=6,
                                         meta={"afficheType": str(afficheType)})
                else:
                    count_url = "http://lssggzy.lishui.gov.cn/lsweb/jyxx/{}/{}/{}/?Paging={}".format(afficheType[0:6],
                                                                                                     afficheType[0:9],
                                                                                                     afficheType[0:12], str(i))
                    yield scrapy.Request(count_url, callback=self.parse_data_urls, priority=5,
                                         meta={"afficheType": str(afficheType)})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")


    def parse_data_urls(self, response):
        try:
            temp_list = response.xpath("//table[@cellspacing='3']/tr")
            for item in temp_list:
                info_url = item.xpath("./td[2]/a/@href").get()
                title_name = item.xpath("./td[2]/a/@title").get()
                pub_time = item.xpath("./td[3]/font/text()").get()
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

                classifyShow = self.project_category_dict.get(category_num[0:6], "")
                info_source_num = category_num[10:12]
                info_source = self.info_dict.get(info_source_num)
                data_url = self.domain_url + info_url
                # data_dict = {"AfficheID": AfficheID, "IsInner": IsInner, "ModuleID": afficheType}
                # url = "https://www.hzctc.cn/afficheshow/Home?AfficheID=1221f9da-2efa-4017-8808-7484994b802e&IsInner=0&ModuleID=22"
                # yield scrapy.Request(url=url,
                #                      callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                #                      meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                #                            "classifyShow": self.classifyShow, "pub_time": pub_time,
                #                            "title_name":title_name})
                yield scrapy.Request(url=data_url, callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     priority=10, meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                                        "classifyShow": classifyShow, "pub_time": pub_time,
                                                        "title_name": title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")


    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            print(origin)
            info_source = response.meta.get("info_source")
            classifyShow = response.meta.get("classifyShow")
            title_name = response.meta.get("title_name")
            pub_time = response.meta.get("pub_time")
            if not pub_time:
                pub_time = response.xpath("/html/body/div[3]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[2]/td/p/text()").get()
            pub_time = get_accurate_pub_time(pub_time)
            if info_source:
                if info_source in ["青田", "缙云", "遂昌", "松阳", "云和", "庆元", ""]:
                    info_city = info_source + "县"
                elif info_source in ["莲都"]:
                    info_city = info_source + "区"
                elif info_source in ["景宁"]:
                    info_city = info_source + "畲族自治县"
                else:
                    info_city = ""
                if not info_city:
                    info_source = f"{self.area_province}"
                else:
                    info_source = f"{self.area_province}-{info_city}"
            else:
                info_source = self.area_province
            # content = response.xpath("/html/body/div[4]/div[2]/div[5]").get()
            content = response.xpath('//table[@height="100%"]').get()

            try:
                files_path = {}
                is_clean = True
                # 判断是pdf页面
                if file_down_url := response.xpath("//table[@id='filedown']"):
                    if a_list := file_down_url.xpath("./tr"):
                        for item in a_list:
                            value = item.xpath('./td/a/@href').get()
                            key = item.xpath('./td/a//text()').get()
                            files_path[key] = self.domain_url + value
                else:
                    files_path = {}
            except Exception as e:
                print(e)
                pass
            if re.search(r"候选人|评标结果", title_name):
                self.cb_kwargs = {"name": const.TYPE_WIN_ADVANCE_NOTICE}
            elif re.search(r"资格预审", title_name):
                self.cb_kwargs = {"name": const.TYPE_QUALIFICATION_ADVANCE_NOTICE}
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
            elif re.search(r"变更|更正|澄清|修正|补充", title_name):
                self.cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
            elif re.search(r"成交|结果|中标", title_name):
                self.cb_kwargs = {"name": const.TYPE_WIN_NOTICE}

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
            print(type(files_path))
            print(notice_item)
            # TODO 产品要求推送，故注释
            # if not is_clean:
            #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    # cmdline.execute("scrapy crawl ZJ_city_3311_lishui_spider -a std=2020-01-04 -a edt=2020-01-04".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3311_lishui_spider".split(" "))