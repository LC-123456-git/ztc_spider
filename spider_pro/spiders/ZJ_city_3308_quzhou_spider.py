#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: zzq
# @Date: 2021-03-30
# @Describe: 衢州公共资源交易网
import re
import math
import json
import scrapy
import urllib
from urllib import parse

from lxml import etree
from scrapy.spiders import Spider
from spider_pro.items import NoticesItem, FileItem
from spider_pro import constans as const
from spider_pro.utils import get_accurate_pub_time, get_back_date, judge_dst_time_in_interval


class MySpider(Spider):
    name = "ZJ_city_3308_quzhou_spider"
    area_id = "3308"
    area_province = "浙江-衢州市公共资源交易服务平台"
    allowed_domains = ['ggzy.qz.gov.cn']
    domain_url = "http://ggzy.qz.gov.cn"
    count_url = "http://ggzy.qz.gov.cn/EWB-FRONT/rest/commonSearch/getInfoListTrade"
    # data_url = "https://www.hzctc.cn/afficheshow/Home?"
    # flie_url = "https://www.hzctc.cn:20001/UService/DownloadAndShow.aspx?dirtype=3&filepath="
    page_size = "10"
    # 招标公告
    list_notice_category_num = ["002001001", "002002001", "002003001", "002004001", "002005001", "002006001", "002007001"]
    # 招标变更
    list_alteration_category_num = ["002001002", "002003002", "002004002", "002005002", "002006002", "002007002"]
    # 招标异常
    list_zb_abnormal = ['002004004']

    # 中标预告
    list_win_advance_notice_num = ["002001004", "002007006"]
    # 中标公告
    list_win_notice_category_num = ["002001005", "002002002", "002003003", "002004003", "002005003", "002006004", "002007004"]
    # 其他公告
    list_other_notice = ["002001003", "002001006", "002002003", "002002004", "002007007", "002006003"]

    list_all_category_num = list_notice_category_num + list_alteration_category_num + list_zb_abnormal \
                            + list_win_advance_notice_num + list_win_notice_category_num + list_other_notice

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        self.r_dict = {"title": "", "xiaqu": "", "projectnum": "",
                       "pageSize": "100"}
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False

    def start_requests(self):
        for item in self.list_all_category_num:
            temp_info_dict = self.r_dict | {"categorynum": str(item)} | {"pageIndex": "0"}
            temp_dict = {"params": json.dumps(temp_info_dict)}
            yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_urls,
                                     meta={"afficheType": str(item)})

    def parse_urls(self, response):
        try:
            if self.enable_incr:
                response_text = json.loads(response.text)
                temp_list = response_text.get("infodata", "")
                category_num = response.meta["afficheType"]
                afficheType = category_num[0:6]
                for item in temp_list:
                    pub_time = item.get("infodate", "")
                    pub_time = get_accurate_pub_time(pub_time)
                    x, y, z = judge_dst_time_in_interval(pub_time, self.sdt_time, self.edt_time)
                    if x:
                        info_source = item.get("zhuanzai", "")
                        title_name = item.get("title", "")
                        infourl = item.get("infourl")
                        pub_time = item.get("infodate", "")
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
                        elif category_num in self.list_zb_abnormal:
                            self.cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
                        else:
                            self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

                        if afficheType in ["002001"]:
                            self.classifyShow = "建设工程"
                        elif afficheType in ["002002"]:
                            self.classifyShow = "政府采购"
                        elif afficheType in ["002003"]:
                            self.classifyShow = "产权"
                        elif afficheType in ["002004"]:
                            self.classifyShow = "土地"
                        elif afficheType in ["002005"]:
                            self.classifyShow = "排污权"
                        elif afficheType in ["002006"]:
                            self.classifyShow = "农村产权"
                        elif afficheType in ["002007"]:
                            self.classifyShow = "其他交易"
                        info_url = self.domain_url + infourl
                        yield scrapy.Request(url=info_url, callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                             meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                                   "classifyShow": self.classifyShow, "pub_time": pub_time,
                                                   "title_name":title_name})
                    else:
                        continue

            else:
                response_text = json.loads(response.text)
                ttlrow = response_text.get("Totle", "")
                pages = math.ceil(ttlrow / 100)
                self.logger.info(f"本次获取总条数为：{ttlrow},共有{pages}页")
                for i in range(0, pages):
                    temp_info_dict = self.r_dict | {"categorynum": response.meta["afficheType"]} | {"pageIndex": str(i)}
                    temp_dict = {"params": json.dumps(temp_info_dict)}
                    yield scrapy.FormRequest(self.count_url, formdata=temp_dict, callback=self.parse_data_urls,
                                             meta={"afficheType": response.meta["afficheType"]})
        except Exception as e:
            self.logger.error(f"初始总页数提取错误 {response.meta=} {e} {response.url=}")

    def parse_data_urls(self, response):
        try:
            response_text = json.loads(response.text)
            temp_list = response_text.get("infodata", "")
            category_num = response.meta["afficheType"]
            afficheType = category_num[0:6]
            for item in temp_list:
                info_source = item.get("zhuanzai", "")
                title_name = item.get("title", "")
                infourl = item.get("infourl")
                pub_time = item.get("infodate", "")
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
                elif category_num in self.list_zb_abnormal:
                    self.cb_kwargs = {"name": const.TYPE_ZB_ABNORMAL}
                else:
                    self.cb_kwargs = {"name": const.TYPE_UNKNOWN_NOTICE}

                if afficheType in ["002001"]:
                    self.classifyShow = "建设工程"
                elif afficheType in ["002002"]:
                    self.classifyShow = "政府采购"
                elif afficheType in ["002003"]:
                    self.classifyShow = "产权"
                elif afficheType in ["002004"]:
                    self.classifyShow = "土地"
                elif afficheType in ["002005"]:
                    self.classifyShow = "排污权"
                elif afficheType in ["002006"]:
                    self.classifyShow = "农村产权"
                elif afficheType in ["002007"]:
                    self.classifyShow = "其他交易"
                info_url = self.domain_url + infourl
                # info_url = "http://ggzy.qz.gov.cn/jyxx/002001/002001001/20171023/72a05665-7405-46bc-a8a2-289f88ceb225.html"
                yield scrapy.Request(url=info_url,callback=self.parse_item, cb_kwargs=self.cb_kwargs, dont_filter=True,
                                     priority=10, meta={"cb_kwargs": self.cb_kwargs, "info_source": info_source,
                                           "classifyShow": self.classifyShow, "pub_time": pub_time,
                                           "title_name":title_name})
        except Exception as e:
            self.logger.error(f"发起数据请求失败 {e} {response.url=}")

    def parse_item(self, response, name):
        global info_city
        if response.status == 200:
            origin = response.url
            print(origin)
            info_source = response.meta.get("info_source", "")
            classifyShow = response.meta.get("classifyShow", "")
            title_name = response.meta.get("title_name", "")
            pub_time = response.meta.get("pub_time", "")
            info_city = response.meta.get("info_source", "")
            if info_source:
                info_source = f"{self.area_province}-{info_city}"
            else:
                info_source = self.area_province
            # content = response.xpath("/html/body/div[4]/div[2]/div[5]").get()
            content = response.xpath('//div[@class="ewb-detail-content"]').get()
            doc = etree.HTML(content)
            els = doc.xpath('//div[@class="ewb-article-share"]' or '//div[@class="jy hidden"]')
            for el in els:
                el.getparent().remove(el)
                content = etree.tounicode(doc)
            try:
                # if re.search(r'相关公告', self.temp_content):
                #     pattern = re.compile(r'<div style="margin-bottom:50px;border-top:1px dashed #d4d4d4;border-bottom:1px dashed #d4d4d4;padding:8px 0;".*?>(.*?)</ul>', re.S)
                #     self.temp_content = content.replace(re.findall(pattern, content)[0], '')
                #
                # if re.search(r"网上提疑", self.temp_content):
                #     rule = re.compile(r'<table class="MsoNormalTable" style="border: none; border-collapse: collapse;".*?>(.*?)</table>', re.S)
                #     sss = re.findall(rule, self.temp_content)
                #     print(sss)
                #     self.temp_content = self.temp_content.replace(re.findall(rule, self.temp_content)[0], '')

                files_path = {}
                is_clean = True
                # 判断是pdf页面
                if jpg_path := response.xpath('//div[@class="ewb-detail-content"]//img'):
                    info_jpg_url = jpg_path.xpath('./@src').get()
                    files_path["info_jpg"] = info_jpg_url
                if response.xpath('//div[@class="file"]'):
                    if a_list := response.xpath('//div[@class="file"]//a'):
                        for item in a_list:
                            if "http" in item.xpath("./@href").get():
                                value = item.xpath('./@href').get()

                            else:
                                value = self.domain_url + item.xpath("./@href").get()
                            key = item.xpath('./text()').get()
                            files_path[key] = value
                    else:
                        content = re.sub("附件:", "", content)


                file_text = response.xpath("//div[@class='ewb-detail-content']//p//span")
                for itmes in file_text:
                    if itmes.xpath("./text()").get() == "附件：":
                        if a_list := itmes.xpath('./a'):
                            for item in a_list:
                                if "http" in item.xpath("./@href").get():
                                    value = item.xpath('./@href').get()
                                else:
                                    value = self.domain_url + item.xpath("./@href").get()
                                key = item.xpath('./text()').get()
                                files_path[key] = value
                        else:
                            content = re.sub("附件:", "", content)

                    # if a_list := response.xpath("//div[@style='border-top:1px dashed #d4d4d4;padding:8px 0;']/ul//a"):
                    #     for item in a_list:
                    #         if file_text := item.xpath("./@onclick").get():
                    #             file_text = file_text.split("('")[1].split("')")[0].replace("'", "")
                    #             key = item.xpath("./text()").get()
                    #             value = self.flie_url + file_text.split(",")[1].replace(" ", "")
                    #             files_path[key] = value
                    #         else:
                    #             continue
                # if url_str := re.search(r'''<iframe frameborder="0" src=".*?" style=''', response.text):
                #     url_pdf_str = url_str.group(0).split(r'''<iframe frameborder="0" src="''')[1].split(r'''" style=''')[0]
                #     iframe_pdf = url_pdf_str.replace("&amp;", "&")
                #     files_path["iframe_pdf"] = iframe_pdf
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
                # is_clean = False
                # TODO 替换成本站链接
                # content = get_iframe_pdf_div_code(url=url_pdf)
                # yield file_item
            except Exception as e:
                print(e)
                pass
            if re.search(r"招标|谈判|磋商|出让|招租", title_name):
                name = const.TYPE_ZB_NOTICE
            elif re.search(r"候选人|评标结果", title_name):
                name = const.TYPE_WIN_ADVANCE_NOTICE
            elif re.search(r"终止|中止|流标|废标|异常", title_name):
                name = const.TYPE_ZB_ABNORMAL
            elif re.search(r"变更|更正|澄清|修正|补充", title_name):
                name = const.TYPE_ZB_ALTERATION

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
            # print(type(files_path))
            # print(notice_item)
            # # TODO 产品要求推送，故注释
            # # if not is_clean:
            # #     notice_item['is_clean'] = const.TYPE_CLEAN_NOT_DONE
            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    # cmdline.execute("scrapy crawl ZJ_city_3308_quzhou_spider -a std=2020-01-04 -a edt=2020-01-04".split(" "))
    cmdline.execute("scrapy crawl ZJ_city_3308_quzhou_spider".split(" "))