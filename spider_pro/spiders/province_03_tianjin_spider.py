#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2020-12-10
# @Describe: 天津市公共资源交易服务平台
import base64
from Crypto.Cipher import AES
import re
import urllib
from urllib import parse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider_pro.items import *
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date
# TODO 天津请求时间需要特殊处理


def add_to_16(s):
    while len(s) % 16 != 0:
        s += (16 - len(s) % 16) * chr(16 - len(s) % 16)
    return str.encode(s)  # 返回bytes


def get_secret_url(text, key='qnbyzzwmdgghmcnm'):
    aes = AES.new(str.encode(key), AES.MODE_ECB)
    encrypted_text = str(base64.encodebytes(aes.encrypt(add_to_16(text))), encoding='utf8').replace('\n', '')
    encrypted_text = encrypted_text.replace('/', "^")
    return encrypted_text[:-2]


def get_real_url(first_url):
    key = 'qnbyzzwmdgghmcnm'
    # first_url = first_url.split("gov.cn:80")[1]

    aa = first_url.split('/')
    aaa = len(aa)
    bbb = aa[aaa - 1].split('.')
    ccc = bbb[0]
    secret_text = get_secret_url(ccc, key=key)
    first_url = first_url.replace(ccc, secret_text)
    return first_url


def process_value_a(value):
    try:
        value = value.split("location='")[1]
        value = value.split("gov.cn:80")[1]
        return value
    except:
        return value


def process_value_s(value):
    try:
        value = value.split("location.href='")[0] + re.search("index_\d+\.jhtml", value).group(0)
        # add_list(value)
        return value
    except:
        return value


test_list = []


def add_list(s):
    test_list.append(s)
    print(test_list)


class MySpider(CrawlSpider):
    name = 'province_03_tianjin_spider'
    area_id = "03"
    area_province = "天津市公共资源交易网"
    allowed_domains = ['ggzy.zwfwb.tj.gov.cn']
    count_url = "http://ggzy.zwfwb.tj.gov.cn/queryContent-jyxx.jspx?"
    page_url = "http://ggzy.zwfwb.tj.gov.cn/queryContent_{}-jyxx.jspx?"
    start_urls = ['http://ggzy.zwfwb.tj.gov.cn/jyxx/index.jhtml']
    # 招标公告
    list_notice_category_num = ["86", "87", "81", "238", "97", "248", "304", "241", "309", "312", "306", "315", "244"]
    # 招标变更
    list_alteration_category_num = ["90", "246", "242"]

    # 中标公告
    list_win_notice_category_num = ["88", "83", "239", "100", "249", "250", "251", "305", "310", "313", "307", "316",
                                    "245"]
    # 其他公告
    list_others_notice_num = ["176"]
    # 农村产权需要特殊处理
    list_country = ["255"]
    list_country_type = ["招标公告", "中标公告", "中标通知书", "变更公告"]

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_win_notice_category_num + \
                            list_others_notice_num + list_country
    headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    # "Cookie": clientlanguage=zh_CN; _gscu_148910830=14152193ksxozr21; _gscbrs_148910830=1; _gscs_148910830=141521934r3sgf21|pv:60; JSESSIONID=7F136030498BF439BC495AD64EC78B10
    "Host": "ggzy.zwfwb.tj.gov.cn",
    "Referer": "http://ggzy.zwfwb.tj.gov.cn/jyxxzfcg/index.jhtml",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36]"}
    # rules = (
    #     Rule(LinkExtractor(allow=r'/jyxx\w+\/index.jhtml', tags=('h3'), attrs=('onclick'),
    #                        process_value=process_value_a), follow=True),
    #     Rule(LinkExtractor(allow=r'/index_\d+\.jhtml', attrs=('href', "onclick"), process_value=process_value_s),
    #          follow=True),
    #     # 招标公告
    #     Rule(LinkExtractor(allow=[r'/jyxxxqgg/.*\.jhtml', r'/jyxxcggg/.*\.jhtml', r'/jyxxzbgg/.*\.jhtml',
    #                               r'/jyxxtdgg/.*\.jhtml', r'/jyxxcqzr/.*\.jhtml', r'/jyxxjsxm/.*\.jhtml',
    #                               r"queryContent_\d+\-jyxx.jspx?title=&inDates=&ext=招标公告&ext1=&origin=&channelId=256&beginTime=&endTime=",
    #                               r'/jyxxcrgg/.*\.jhtml', r'/jyxxelcg/.*\.jhtml', r'/jyxxtzgg/.*\.jhtml',
    #                               r'/jyxxtpgg/.*\.jhtml', r'/jyxxlqxx/.*\.jhtml'],
    #                        attrs=('url'), process_value=get_real_url),
    #          cb_kwargs={"name": const.TYPE_ZB_NOTICE},
    #          callback="parse_item", follow=False),
    #     # 招标变更
    #     Rule(LinkExtractor(allow=[r'/jyxxzcgz/.*\.jhtml', r'/jyxxtdbc/.*\.jhtml'], attrs=('url'),
    #                        process_value=get_real_url), cb_kwargs={"name": const.TYPE_ZB_ALTERATION},
    #                        callback="parse_item", follow=False),
    #     # 中标公告
    #     Rule(LinkExtractor(allow=[r'/jyxxcgjg/.*\.jhtml', r'/jyxxzbjb/.*\.jhtml', r'/jyxxtdjg/.*\.jhtml',
    #                               r'/jyxxqyzc/.*\.jhtml', r'/jyxxxdjy/.*\.jhtml', r'/jyxxncjy/.*\.jhtml',
    #                               r"queryContent_\d+\-jyxx.jspx?title=&inDates=&ext=中标公告&ext1=&origin=&channelId=256&beginTime=&endTime=",
    #                               r'/jyxxjtzy/.*\.jhtml', r'/jyxxjggs/.*\.jhtml', r'/jyxxelzb/.*\.jhtml',
    #                               r'/jyxxtpjg/.*\.jhtml', r'/jyxxlqcj/.*\.jhtml', ], attrs=('url'), process_value=get_real_url),
    #          cb_kwargs={"name": const.TYPE_WIN_NOTICE},
    #          callback="parse_item", follow=False),
    #     # 其他公告
    #     Rule(LinkExtractor(allow=r'/{}/.*\.jhtml'.format("jyxxncqt"), attrs=('url'), process_value=get_real_url),
    #          cb_kwargs={"name": const.TYPE_OTHERS_NOTICE},
    #          callback="parse_item", follow=False),
    # )

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.ext_dict = {"ext": ""}
        self.channelld_dict = {"channelId": ""}
        r_dict = {"title": "", "inDates": "", "ext1": "", "origin": ""}
        if day := kwargs.get("day"):
            time_dict = {"beginTime": "" if day == "0" else get_back_date(int(day) - 1),
                         "endTime": "" if day == "0" else get_back_date(0)}
        elif kwargs.get("sdt") and kwargs.get("edt"):
            time_dict = {"beginTime": kwargs.get("sdt"), "endTime": kwargs.get("edt"), }
        else:
            time_dict = {"beginTime": "", "endTime": "", }  # TODO 默认为全量
        self.count_dict = r_dict | time_dict

    def start_requests(self):
        for channelId in self.list_all_category_num:
            if channelId == "255":
                pass
            else:
                info_dict = self.count_dict | self.ext_dict | {"channelId": channelId}
                yield scrapy.Request(
                    url=f"{self.count_url}{urllib.parse.urlencode(info_dict)}",priority=1,
                    callback=self.parse_page_urls, meta={"channelId": channelId, "info_dict": info_dict})

    def parse_page_urls(self, response):
        channelId = response.meta['channelId']
        ttlrow = re.search(r"共\d+条", response.text)
        pages_str = re.search(r"/\d+页", response.text)
        pages = int(re.search(r"\d+", pages_str.group(0)).group(0))
        self.logger.info(f"本次获取总条数为：{ttlrow} 总页数为：{pages_str}")
        for i in range(1, pages):
            if not i == 1:
                self.query_url = "http://ggzy.zwfwb.tj.gov.cn/queryContent_{}-jyxx.jspx?".format(i)
            else:
                self.query_url = "http://ggzy.zwfwb.tj.gov.cn/queryContent-jyxx.jspx?"
            info_dict = response.meta['info_dict']
            yield scrapy.Request(
                url=f"{self.query_url}{urllib.parse.urlencode(info_dict)}",priority=8,
                callback=self.parse_data_urls, meta={"channelId": channelId})


    def parse_data_urls(self, response):
        channelId = response.meta['channelId']
        try:
            li_list = response.xpath("/html/body/div[2]/div[3]/div/ul/li").getall()
            if channelId in self.list_notice_category_num:
                self.cb_kwargs = {"name": const.TYPE_ZB_NOTICE}
            elif channelId in self.list_alteration_category_num:
                self.cb_kwargs = {"name": const.TYPE_ZB_ALTERATION}
            elif channelId in self.list_win_notice_category_num:
                self.cb_kwargs = {"name": const.TYPE_WIN_NOTICE}
            elif channelId in self.list_others_notice_num:
                self.cb_kwargs = {"name": const.TYPE_OTHERS_NOTICE}
            elif channelId == "255":
                pass
            else:
                self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

            if channelId in ["86", "87", "90", "88", "176"]:
                self.classify_show = "政府采购"
            elif channelId in ["81", "83"]:
                self.classify_show = "工程建设"
            elif channelId in ["238", "239", "246"]:
                self.classify_show = "土地使用权"
            elif channelId in ["97", "100"]:
                self.classify_show = "国有产权"
            elif channelId in ["248", "249", "250", "251"]:
                self.classify_show = "矿业权交易"
            elif channelId in ["304", "305"]:
                self.classify_show = "二类疫苗"
            elif channelId in ["241", "242"]:
                self.classify_show = "药品采购"
            elif channelId in ["309", "310"]:
                self.classify_show = "碳排放权"
            elif channelId in ["312", "313"]:
                self.classify_show = "排污权"
            elif channelId in ["306", "307"]:
                self.classify_show = "林权交易"
            elif channelId in ["315", "316"]:
                self.classify_show = "知识产权"
            elif channelId in ["244", "245"]:
                self.classify_show = "其他"
            elif channelId in ["255"]:
                self.classify_show = "农村产权"
            for item in li_list:
                data_url = re.search(r"http://ggzy.zwfwb.tj.gov.cn:80/\w+/\d+\.jhtml", item).group(0)
                data_url = get_real_url(data_url)

                yield scrapy.Request(url=data_url, callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     priority=10, meta={"cb_kwargs": self.cb_kwargs, "classify_show": self.classify_show,
                                           "channelId": channelId})
        except Exception as e:
            print(e)

    def parse_item(self, response, name):
        if response.status == 200:
            origin = response.url
            title_name = response.xpath("//div[@class='content-title']/text()").get()
            print(title_name)
            pub_time = response.xpath("//span[@id='time']/text()").get()
            info_source = response.xpath("//div[@class='content-title2']/span/a/text()").get()
            if info_source:
                info_source = f"{self.area_province}-{info_source}"
            else:
                info_source = self.area_province
            content = response.xpath("//*[@id='content']").getall()
            content_text = content[0].replace("\r", "").replace("\t", "").replace("\n", "")
            # accessory_url = response.xpath("//div[@id='content']/p/a/@href").getall()
            # accessory_name = response.xpath("//div[@id='content']/p/a/@href/text()").getall()
            classify_show = response.meta.get("classify_show")
            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = ""
            notice_item["content"] = content_text
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = name
            notice_item["category"] = classify_show
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline

    cmdline.execute("scrapy crawl province_03_tianjin_spider -a sdt=2021-05-21 -a edt=2021-05-21".split(" "))
