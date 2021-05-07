#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-04
# @Describe: 吉林公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import  judge_dst_time_in_interval, get_accurate_pub_time


class MySpider(Spider):
    name = "province_08_jilin_spider"
    area_id = "08"
    allowed_domains = ['jl.gov.cn']
    domain_url = "http://www.jl.gov.cn"
    count_url = "http://was.jl.gov.cn/was5/web/search?"
    page_size = "17"
    area_province = "吉林省公共资源交易服务平台"

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False
        self.r_dict = {"channelid": "237687", "prepage": "17", "searchword": "", "callback": "result",
                       "_": "1614851549199"}

    def start_requests(self):
        yield scrapy.Request(
            url=f"{self.count_url}{urllib.parse.urlencode(self.r_dict | {'page': '1'})}",
            callback=self.parse_page_urls)

    def parse_page_urls(self, response):
        try:
            response_text = json.loads(response.text.split("(", 1)[1].rsplit(")", 1)[0])
            total = response_text.get("recordnum")
            self.logger.info(
                f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
            pages = math.ceil(int(total) / int(self.page_size))
            print(pages)
            for i in range(1, pages):
                yield scrapy.Request(
                    url=f"{self.count_url}{urllib.parse.urlencode(self.r_dict | {'page': '{}'.format(i)})}",
                    callback=self.parse_data_urls)
        except Exception as e:
            self.logger.error(f"初始总数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            response_text = json.loads(response.text.split("(", 1)[1].rsplit(")", 1)[0])
            data_list = response_text.get("datas")
            if self.enable_incr:
                for item in data_list:
                    pub_time = item.get("timestamp")
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        title = item.get("title")
                        notice_type = item.get("iType")
                        area = item.get("area")
                        pub_time = item.get("timestamp")
                        origin = item.get("docpuburl")
                        classify_show = item.get("tType")
                        if notice_type in ["采购公告", "招标公告", "出让公告", "挂牌披露"]:
                            notice_type = const.TYPE_ZB_NOTICE
                        elif notice_type in ["变更公告"]:
                            notice_type = const.TYPE_ZB_ALTERATION
                        elif notice_type in ["中标候选人公示"]:
                            notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                        elif notice_type in ["中标公告", "中标结果公告", "成交宗地", "出让结果", "交易结果"]:
                            notice_type = const.TYPE_WIN_NOTICE
                        elif notice_type in ["合同公示", "单一来源论证公示"]:
                            notice_type = const.TYPE_OTHERS_NOTICE
                        elif notice_type in ["终止（废标）公告"]:
                            notice_type = const.TYPE_ZB_ABNORMAL

                        if area in ["122201004232188615", "01382732-2", "1222010056393822XT", "12220100MB10780025"]:
                            self.info_source = "长春市"
                        elif area in ["12220000412759478T", "73700954-4", "12220100423200207X", "122200005740930828"]:
                            self.info_source = "吉林省"
                        elif area in ["12220200782609514F"]:
                            self.info_source = "吉林市"
                        elif area in ["34004150-3", "12220400412763282Y"]:
                            self.info_source = "辽源市"
                        elif area in ["112203007645929828", "122030000105", "112203000135292377", "41270618-1", "112203000135298353",
                                      "11220300413126808N", "12220300MB0125428T"]:
                            self.info_source = "四平市"
                        elif area in ["66011618-0", "12220700MB1837064Y"]:
                            self.info_source = "松原市"
                        elif area in ["73256854-X" , "11222400MB14602364"]:
                            self.info_source = "延边朝鲜族自治州"
                        elif area in ["73256678-X", "12220500MB1143476B" ]:
                            self.info_source = "通化市"
                        elif area in ["66429601-9", "12220800MB11528661"]:
                            self.info_source = "白城市"
                        elif area in ["12220600737041237Q"]:
                            self.info_source = "白山市"
                        elif area in ["112200007710693483"]:
                            self.info_source = "长白山"
                        yield scrapy.Request(url=origin, callback=self.parse_item, meta={"info_source": self.info_source,
                         "title": title, "notice_type": notice_type, "pub_time": pub_time, "classify_show": classify_show})
                    else:
                        continue
            else:
                for item in data_list:
                    title = item.get("title")
                    notice_type = item.get("iType")
                    area = item.get("area")
                    pub_time = item.get("timestamp")
                    origin = item.get("docpuburl")
                    classify_show = item.get("tType")
                    if notice_type in ["采购公告", "招标公告", "出让公告", "挂牌披露"]:
                        notice_type = const.TYPE_ZB_NOTICE
                    elif notice_type in ["变更公告"]:
                        notice_type = const.TYPE_ZB_ALTERATION
                    elif notice_type in ["中标候选人公示"]:
                        notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                    elif notice_type in ["中标公告", "中标结果公告", "成交宗地", "出让结果", "交易结果"]:
                        notice_type = const.TYPE_WIN_NOTICE
                    elif notice_type in ["合同公示", "单一来源论证公示"]:
                        notice_type = const.TYPE_OTHERS_NOTICE
                    elif notice_type in ["终止（废标）公告"]:
                        notice_type = const.TYPE_ZB_ABNORMAL

                    if area in ["122201004232188615", "01382732-2", "1222010056393822XT", "12220100MB10780025"]:
                        self.info_source = "长春市"
                    elif area in ["12220000412759478T", "73700954-4", "12220100423200207X", "122200005740930828"]:
                        self.info_source = "吉林省"
                    elif area in ["12220200782609514F"]:
                        self.info_source = "吉林市"
                    elif area in ["34004150-3", "12220400412763282Y"]:
                        self.info_source = "辽源市"
                    elif area in ["112203007645929828", "122030000105", "112203000135292377", "41270618-1", "112203000135298353",
                                  "11220300413126808N", "12220300MB0125428T"]:
                        self.info_source = "四平市"
                    elif area in ["66011618-0", "12220700MB1837064Y"]:
                        self.info_source = "松原市"
                    elif area in ["73256854-X" , "11222400MB14602364"]:
                        self.info_source = "延边朝鲜族自治州"
                    elif area in ["73256678-X", "12220500MB1143476B" ]:
                        self.info_source = "通化市"
                    elif area in ["66429601-9", "12220800MB11528661"]:
                        self.info_source = "白城市"
                    elif area in ["12220600737041237Q"]:
                        self.info_source = "白山市"
                    elif area in ["112200007710693483"]:
                        self.info_source = "长白山"
                    yield scrapy.Request(url=origin, callback=self.parse_item, meta={"info_source": self.info_source,
                             "title": title, "notice_type": notice_type, "pub_time": pub_time, "classify_show": classify_show})
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
            title_name = response.xpath("//*[@id='content_Height']/div/div[2]/div[2]/h3/text()").get()
            if not title_name:
                title_name = response.meta["title"]

            info_source = response.meta["info_source"]
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            pub_time = response.meta["pub_time"]
            pub_time = get_accurate_pub_time(pub_time)
            content = response.xpath('//*[@id="content_Height"]/div/div[2]/div[2]/div[2]').get()
            if not content:
                content = response.xpath('//div[@class="ewb-article-info"]').get()
            # print(info_source)
            # print(pub_time)
            # print(content)
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


            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else ",".join(files_path)
            notice_item["content"] = content
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = response.meta["notice_type"]
            notice_item["category"] = response.meta["classify_show"]
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_08_jilin_spider -a sdt=2021-03-08 -a edt=2021-03-08".split(" "))
