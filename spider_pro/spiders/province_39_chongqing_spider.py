#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: lc
# @Date: 2021-03-18
# @Describe: 重庆市公共资源交易服务平台
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
from spider_pro.utils import judge_dst_time_in_interval, get_accurate_pub_time, remove_specific_element


# TODO 完成
def get_time(str):
    name = ''.join(re.findall('\d{4}-\d{2}-\d{2}', str)).replace('-', '')
    return name

def get_url(name):
    str = ''.join(re.findall('(.*)\/\w+.\w+', name)).strip()
    return str


class MySpider(Spider):
    name = "province_39_chongqing_spider"
    area_id = "39"
    allowed_domains = ['cqggzy.com']
    domain_url = "https://www.cqggzy.com"
    count_url = "https://www.cqggzy.com/jyxx/jyxx-page.html"
    data_url = 'https://www.cqggzy.com/interface/rest/inteligentSearch/getFullTextData'
    base_url = 'https://ggzydl.cqggzy.com/CQTPBidder/jsgcztbmis2/pages/zbfilelingqu_hy/cQZBFileDownAttachAction.action?cmd=download&AttachGuid='
    area_province = "重庆市公共资源交易服务平台"

    # 招标预告
    list_advance_category_num = ["https://www.cqggzy.com/xxhz/014001/014001019/sub-page.html",
                                 'https://www.cqggzy.com/xxhz/014005/014005008/sub-page.html']
    #招标公告
    list_notice_category_num = ['https://www.cqggzy.com/xxhz/014001/014001001/zbggjyxx-page.html', 'https://www.cqggzy.com/xxhz/014002/014002001/transaction-page.html',
                                'https://www.cqggzy.com/xxhz/014004/014004001/zbggjyxx-page.html', 'https://www.cqggzy.com/xxhz/014005/014005001/sub-page.html',
                                'https://www.cqggzy.com/xxhz/014008/014008001/sub-page.html', 'https://www.cqggzy.com/xxhz/014010/014010001/sub-page.html',
                                "https://www.cqggzy.com/xxhz/014001/014001014/sub-page.html"]

    # 招标异常
    list_alteration_category_num = ["https://www.cqggzy.com/xxhz/014001/014001016/sub-page.html", "https://www.cqggzy.com/xxhz/014002/014002002/sub-page.html",
                                    "https://www.cqggzy.com/xxhz/014008/014008014/sub-page.html"]
    # 中标公告
    list_win_notice_category_num = ["https://www.cqggzy.com/xxhz/014001/014001004/sub-page.html", "https://www.cqggzy.com/xxhz/014002/014002004/sub-page.html",
                                    "https://www.cqggzy.com/xxhz/014003/014003004/sub-page.html", "https://www.cqggzy.com/xxhz/014004/014004004/sub-page.html",
                                    "https://www.cqggzy.com/xxhz/014005/014005004/sub-page.html", "https://www.cqggzy.com/xxhz/014006/014006004/sub-page.html",
                                    "https://www.cqggzy.com/xxhz/014008/014008003/sub-page.html", "https://www.cqggzy.com/xxhz/014009/014009004/sub-page.html",
                                    "https://www.cqggzy.com/xxhz/014010/014010002/sub-page.html"]
    #招标变更
    list_zb_abnormal = ['https://www.cqggzy.com/xxhz/014001/014001002/sub-page.html', 'https://www.cqggzy.com/xxhz/014004/014004011/sub-page.html',
                        'https://www.cqggzy.com/xxhz/014008/014008002/sub-page.html', 'https://www.cqggzy.com/xxhz/014005/014005002/sub-page.html']
    #中标预告
    list_win_advance_notice_num = ['https://www.cqggzy.com/xxhz/014001/014001003/sub-page.html', 'https://www.cqggzy.com/xxhz/014008/014008013/sub-page.html']
    # 其他公告
    list_others_notice_num = ["https://www.cqggzy.com/xxhz/014008/014008012/sub-page.html",
                              "https://www.cqggzy.com/xxhz/014011/014011001/sub-page.html", "https://www.cqggzy.com/xxhz/014011/014011002/sub-page.html"]

    r_dict = "{\"token\":\"\",\"pn\":0,\"rn\":18,\"sdt\":\"\",\"edt\":\"\",\"wd\":\" \",\"inc_wd\":\"\",\"exc_wd\":\"\",\"fields\":\"title\",\"cnum\":\"001\",\"sort\":\"{\\\"istop\\\":0,\\\"ordernum\\\":0,\\\"webdate\\\":0,\\\"rowid\\\":0}\",\"ssort\":\"title\",\"cl\":200,\"terminal\":\"\",\"condition\":[{\"fieldName\":\"categorynum\",\"notEqual\":null,\"equalList\":null,\"notEqualList\":null,\"isLike\":true,\"likeType\":2}],\"time\":null,\"highlights\":\"title\",\"statistics\":null,\"unionCondition\":null,\"accuracy\":\"\",\"noParticiple\":\"0\",\"searchRange\":null,\"isBusiness\":\"1\"}"


    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__()
        if kwargs.get("sdt") and kwargs.get("edt"):
            self.enable_incr = True
            self.sdt_time = kwargs.get("sdt")
            self.edt_time = kwargs.get("edt")
        else:
            self.enable_incr = False


    def start_requests(self):
        # info_url = 'https://www.cqggzy.com/xxhz/014001/014001001/014001001002/20210517/ff879236-09a7-491e-b786-0532837d3737.html'
        # yield scrapy.Request(url=info_url, callback=self.parse_itme)
        yield scrapy.Request(url=self.count_url, callback=self.parse_categoy_urls)

    def parse_categoy_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="wb-border wb-menu-bd wb-subbg"]/ul/li')
            for li in li_list:
                categoy = li.xpath('./a/h3/text()').get()
                if 'http' in li.xpath('./a/@href').get():
                    base_url = li.xpath('./a/@href').get()
                else:
                    base_url = self.domain_url + li.xpath('./a/@href').get()

                yield scrapy.Request(url=base_url, callback=self.parse_categoy_data_urls,
                                     meta={'categoy': categoy})
        except Exception as e:
            self.logger.error(f"parse_categoy_urls: 获取的url错误 {response.meta=} {e} {response.url=}")

    def parse_categoy_data_urls(self, response):
        try:
            if 'http' in response.xpath('//div[@class="ewb-htt"]/div/a/@href').get():
                base_all_list = response.xpath('//div[@class="ewb-htt"]/div/a/@href').get()
            else:
                base_all_list = self.domain_url + response.xpath('//div[@class="ewb-htt"]/div/a/@href').get()

            yield scrapy.Request(url=base_all_list, callback=self.parse_all_urls,
                                 meta={'categoy': response.meta.get('categoy')})
        except Exception as e:
            self.logger.error(f"parse_categoy_data_urls:发起数据请求失败 {e} {response.url=}")

    def parse_all_urls(self, response):
        try:
            li_list = response.xpath('//div[@class="wb-border wb-menu-bd wb-subbg"]/ul/li')
            for li in li_list:
                if 'http' in li.xpath('./a/@href').get():
                    all_urls = li.xpath('./a/@href').get()
                else:
                    all_urls = self.domain_url + li.xpath('./a/@href').get()

                if all_urls in self.list_advance_category_num:          # 招标预告
                    notice = const.TYPE_ZB_ADVANCE_NOTICE
                elif all_urls in self.list_notice_category_num:         # 招标公告
                    notice = const.TYPE_ZB_NOTICE
                elif all_urls in self.list_alteration_category_num:     # 招标异常
                    notice = const.TYPE_ZB_ABNORMAL
                elif all_urls in self.list_win_notice_category_num:     # 中标公告
                    notice = const.TYPE_WIN_NOTICE
                elif all_urls in self.list_zb_abnormal:                 # 招标变更
                    notice = const.TYPE_ZB_ALTERATION
                elif all_urls in self.list_win_advance_notice_num:      # 中标预告
                    notice = const.TYPE_WIN_ADVANCE_NOTICE
                elif all_urls in self.list_others_notice_num:           # 其他公告
                    notice = const.TYPE_OTHERS_NOTICE
                else:
                    notice = ''
                if re.findall('\d{8,9}', all_urls) and '0140' in all_urls:
                    equal = re.findall('\d{8,9}', all_urls)[0]
                    info_dict = json.loads(self.r_dict)
                    equal_dict = info_dict['condition'][0] | {'equal': equal}
                    pages_dict = {'condition': [equal_dict]}
                    type_dict = info_dict | pages_dict
                    yield scrapy.Request(url=self.data_url, callback=self.parse_all_data, body=json.dumps(type_dict),
                                         method="POST", dont_filter=True, priority=100,
                                         meta={'categoy': response.meta.get('categoy'),
                                               'equal': equal, 'notice': notice,
                                               'all_urls': all_urls})

        except Exception as e:
            self.logger.error(f"parse_all_urls:发起数据请求失败 {e} {response.url=}")

    def parse_all_data(self, response):
        try:
            pn = 0
            if self.enable_incr:
                nums_count = 1
                if response.json()['result']['records']:
                    s_num = response.json()['result']['records']
                    for num in range(len(s_num)):
                        put_time = s_num[num]['pubinwebdate']
                        put_time = get_accurate_pub_time(put_time)
                        x, y, z = judge_dst_time_in_interval(put_time, self.sdt_time, self.edt_time)
                        if x:
                            nums_count += 1
                            total = response.json()['result']['totalcount']  # 总条数
                            if total == None:
                                return
                            self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                        if num >= nums_count:
                            pn += 18
                        else:
                            pn = 0
                        pn_dict = {"pn": pn}
                        info_dict = json.loads(self.r_dict)
                        info_dicts = info_dict | pn_dict
                        equal_dict = info_dicts['condition'][0] | {'equal': response.meta['equal']}
                        pages_dict = {'condition': [equal_dict]}
                        type_dicts = info_dicts | pages_dict

                        yield scrapy.Request(url=self.data_url, callback=self.parse_data_info,
                                             body=json.dumps(type_dicts), method="POST", priority=150,
                                             meta={'categoy': response.meta.get('categoy'),
                                                   'equal': response.meta['equal'],
                                                   'notice': response.meta['notice'],
                                                   'all_urls': response.meta['all_urls']})

            else:
                total = response.json()['result']['totalcount']        # 总条数
                if total % 18 != 0:
                    pages = total // 18 + 1
                else:
                    pages = total // 18
                if total == None:
                    return
                self.logger.info(f"初始总数提取成功 {total=} {response.url=} {response.meta.get('proxy')}")
                for num in range(pages):
                    if num == 0:
                        pn = 0
                    else:
                        pn += 18
                    pn_dict = {"pn": pn}
                    info_dict = json.loads(self.r_dict)
                    info_dicts = info_dict | pn_dict
                    equal_dict = info_dicts['condition'][0] | {'equal': response.meta['equal']}
                    pages_dict = {'condition': [equal_dict]}
                    type_dicts = info_dicts | pages_dict

                    yield scrapy.Request(url=self.data_url, callback=self.parse_data_info,
                                         body=json.dumps(type_dicts), method="POST", priority=150,
                                         meta={'categoy': response.meta.get('categoy'),
                                               'equal': response.meta['equal'],
                                               'notice': response.meta['notice'],
                                               'all_urls': response.meta['all_urls']})

        except Exception as e:
            self.logger.error(f"parse_all_data:发起数据请求失败 {e} {response.url=}")

    def parse_data_info(self, response):
        try:
            info_url = response.meta['all_urls']
            infoid_list = response.json()['result']['records']
            for num in range(len(infoid_list)):
                categorynum = infoid_list[num]['categorynum']
                times = get_time(infoid_list[num]['pubinwebdate'])
                infoid = infoid_list[num]['infoid']
                pub_time = infoid_list[num]['pubinwebdate']
                pub_time = get_accurate_pub_time(pub_time)
                title_name = infoid_list[num]['title']

                if re.search(r'资格预审', title_name):                           # 资格预审结果公告
                    notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
                elif re.search(r'终止|中止|异常|废标|流标', title_name):          # 招标异常
                    notice_type = const.TYPE_ZB_ABNORMAL
                elif re.search(r'候选人', title_name):                           # 中标预告
                    notice_type = const.TYPE_WIN_ADVANCE_NOTICE
                elif re.search(r'变更|更正|澄清|补遗', title_name):               # 招标变更
                    notice_type = const.TYPE_ZB_ALTERATION
                elif re.search(r'中标|成交|结果', title_name):                    # 中标公告
                    notice_type = const.TYPE_WIN_NOTICE
                else:
                    notice_type = response.meta['notice']
                if notice_type:
                    base_url = get_url(info_url) + '/' + categorynum + '/' + times + '/' + infoid + '.html'
                    yield scrapy.Request(url=base_url, callback=self.parse_itme, priority=200,
                                         meta={'categoy': response.meta.get('categoy'), 'title_name': title_name,
                                               'pub_time': pub_time, 'notice_type': notice_type})

        except Exception as e:
            self.logger.error(f"parse_data_info:发起数据请求失败 {e} {response.url=}")

    def parse_itme(self, response):

        """
        :param response: response
        :param name: 类别
        :return: 回调函数
        """
        if response.status == 200:

            origin = response.url
            info_source = self.area_province
            pub_time = response.meta["pub_time"]

            title_name = response.meta['title_name']
            category = response.meta['categoy']
            notice_type = response.meta['notice_type']

            content = response.xpath('//div[@class="detail-block"]').get()
            # 去除 title
            _, content = remove_specific_element(content, 'h3', 'class', 'article-title')
            _, content = remove_specific_element(content, 'div', 'class', 'gonggaotitle')
            # 去除 info信息 来源等信息
            _, content = remove_specific_element(content, 'div', 'class', 'info-source')

            _, content = remove_specific_element(content, 'div', 'class', 'hide')

            patterns = re.compile(r'<a target="_blank" .*?>(.*?)</div>', re.S)
            contents = content.replace(''.join(re.findall(patterns, content)), '')

            files_path = {}
            files_text = etree.HTML(contents)
            suffix_list = ['html', 'com', 'com/', 'cn', 'cn/']
            if files_text.xpath('//a[@class="ewb-blue-a"]'):
                for cont in files_text.xpath('//a[@class="ewb-blue-a"]'):
                    if cont.xpath('./@onclick'):
                        values = cont.xpath('./@onclick')[0]
                        guid = ''.join(re.findall('downloadAttach\((.*)\)', values)).replace("'", '').split(',')
                        value = self.base_url + guid[0] + '&FileCode' + guid[1] + '&ClientGuid' + guid[2]
                        keys = cont.xpath('./text()')[0]
                        files_path[keys] = value
                        contents = re.sub('<a class="ewb-blue-a" onclick=.*?>', '<a class="ewb-blue-a" href="{}">'.format(value), contents)

            elif files_text.xpath('//div[@id="yewuxitong"]//a/@href'):
                for cont in files_text.xpath('//div[@id="yewuxitong"]//a'):
                    if cont.xpath('./@href'):
                        values = cont.xpath('./@href')[0]
                        if ''.join(values).split('.')[-1] not in suffix_list:
                            if cont.xpath('./text()'):
                                keys = cont.xpath('./text()')[0]
                                files_path[keys] = values
            else:
                files_path = ''

            notice_item = NoticesItem()
            notice_item["origin"] = origin
            notice_item["title_name"] = title_name
            notice_item["pub_time"] = pub_time
            notice_item["info_source"] = info_source
            notice_item["is_have_file"] = const.TYPE_HAVE_FILE if files_path else const.TYPE_NOT_HAVE_FILE
            notice_item["files_path"] = "" if not files_path else files_path
            notice_item["content"] = contents
            notice_item["area_id"] = self.area_id
            notice_item["notice_type"] = notice_type
            notice_item["category"] = category

            yield notice_item


if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl province_39_chongqing_spider".split(" "))
    # cmdline.execute("scrapy crawl province_39_chongqing_spider -a sdt=2021-05-01 -a edt=2021-06-01".split(" "))
