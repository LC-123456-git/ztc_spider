#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2021/01/14
# @Author : wwj
# @Describe: notices item数据清洗
import re
import html
import time
import urllib
import requests
import datetime
from ast import literal_eval
from urllib import parse

from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import (
    deal_base_notices_data,
    deal_area_data,
    get_accurate_pub_time,
    init_yaml,
    get_keywords,
)
from sqlalchemy import create_engine, text
from spider_pro.rules_clean import get_keys_value_from_content_ahead

class CleanPipeline(object):

    def __init__(self, name, area_id, logger, **kwargs):
        self.name = name
        self.area_id = area_id
        self.logger = logger
        self.is_have_file = False
        self.test_file = True
        self.clean_all_enable = True if kwargs.get("ENABLE_CLEAN_ALL_WHEN_START") in const.TRUE_LIST else False
        self.enable = True if kwargs.get("ENABLE_AUTO_CLEAN") in const.TRUE_LIST else False
        self.clean_filed_list = ['title', "content", 'project_number', 'project_name', 'tenderee', 'bidding_agency',
                                 'area_code', 'area', 'address', 'email', 'description', 'bid_type', 'bid_modus',
                                 'inspect_dept', 'review_dept', 'notice_nature', 'bid_file', 'bid_file_start_time',
                                 'bid_file_end_time', 'apply_end_time', 'notice_start_time', 'notice_end_time',
                                 'aberrant_type', 'budget_amount', 'tenderopen_time', 'publish_time', 'liaison',
                                 'contact_information', 'classify_id', 'classify_name', 'project_type', 'state',
                                 'file_ids', 'company_type', 'successful_bidder', 'bid_amount', 'sign_type', 'source',
                                 'source_url', 'is_have_file']

        if kwargs.get("TEST_ENGINE_CONFIG") and kwargs.get("ENGINE_CONFIG"):
            self.engine = create_engine(
                kwargs.get("TEST_ENGINE_CONFIG") if kwargs.get("DEBUG_MODE") else kwargs.get("ENGINE_CONFIG"))
            self.table_name = f"{NoticesItem.table_name}_{self.area_id}"
        else:
            self.engine = None
            self.table_name = None
        if kwargs.get("DEBUG_MODE"):
            self.test_file = True
        else:
            self.test_file = False

        self.clean_all_count = 0
        if self.clean_all_enable and self.engine.dialect.has_table(self.engine, self.table_name):
            self.clean_all_not_clean_done_data()
            self.logger.info(f"本次启动清洗总共条数: {self.clean_all_count}")

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        name = crawler.spider.name
        area_id = crawler.spider.area_id
        logger = crawler.spider.logger
        return cls(name, area_id, logger, **settings)

    def clean_all_not_clean_done_data(self):
        rows = 100
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select * from {self.table_name} where is_clean = {const.TYPE_CLEAN_NOT_DONE} limit {rows} offset {start} ").fetchall()
                for item in results:
                    try:
                        item_id = str(item["id"])
                        pre_process_dict = self.get_pre_process_data(item)
                        deal_data = self.extract_data(pre_data=pre_process_dict, area_id=self.area_id)
                        deal_data = deal_base_notices_data(deal_data)

                        update_sql = text(
                            """UPDATE {} set """.format(self.table_name) +
                            """ , """.join(["""{} = :{}""".format(var, var) for var in self.clean_filed_list]) +
                            """, is_clean = {} """.format(const.TYPE_CLEAN_DONE) +
                            """where id = {} """.format(item_id))

                        result = conn.execute(update_sql, **deal_data)
                        if result.rowcount == 1:
                            self.clean_all_count += 1
                        else:
                            self.logger.error(f"启动清洗单条失败 更新数据失败 {item_id=}")

                    except Exception as e:
                        self.logger.error(f"启动清洗单条失败： {e=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                self.logger.info(f"本次启动清洗已清洗条数: {start}")

    def process_item(self, item, spider):
        """
        主要清洗逻辑
        :param item:
        :param spider:
        :return:
        """
        try:
            if isinstance(item, NoticesItem) and self.enable:
                # 处理未知公告不清洗
                if str(item["notice_type"]) == const.TYPE_UNKNOWN_NOTICE:
                    return self.deal_data_not_clean(item)

                # TODO 暂时标记is_clean 为0 则不清洗
                if dict(item).get("is_clean", const.TYPE_CLEAN_DONE) == const.TYPE_CLEAN_NOT_DONE:
                    return self.deal_data_not_clean(item)
                self.is_have_file = False
                pre_process_dict = self.get_pre_process_data(item)
                deal_data = self.extract_data(pre_data=pre_process_dict, area_id=self.area_id)
                deal_data = deal_base_notices_data(deal_data)
                for var in self.clean_filed_list:
                    item[var] = deal_data.get(var, "")
                item["is_clean"] = const.TYPE_CLEAN_DONE
                return item
            else:
                return item
        except Exception as e:
            self.logger.error(f"清洗异常 {e=}")
            return self.deal_data_not_clean(item)

    def request_download(self, files_path, content, id=None, is_have_file=None):
        """
        请求服务器下载接收相应
        修改数据库content
        """
        msg = ''
        if is_have_file == "1":
            files_path = str(files_path)
        elif is_have_file == 1:
            files_path = literal_eval(files_path)
        if self.test_file:
            ret = requests.post(url=const.TEST_FILE_SERVER, data={"jsonString": files_path}, timeout=3)
        else:
            ret = requests.post(url=const.FILE_SERVER, data={"jsonString": files_path}, timeout=3)
        cur_files_path = literal_eval(files_path)
        """
        [{"name":"成交公示内容.pdf","systemUrl":"http://192.168.1.220:8002/sapi/webfile/getWebFilesBySystemUrl?systemUrl=webf
        ile/20210415/pdf/84F38E57E4E44833893F9178A87F7B0E.pdf", "code":201,"text":"重复文件任务"}]
        """
        if ret.status_code == 200:
            data = ret.json()
            try:
                for dt in data:
                    name = dt['name']
                    system_url = dt['systemUrl']
                    if dt['code'] in [200, 201]:
                        # replace content
                        for fp, v in cur_files_path.items():
                            # {'涉企服务平台合同.zip': 'https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1014AN/fb1d
                            # 2a9b-8e2d-486a-ae03-a4efebadefa6.zip'}
                            if fp == name:
                                web_url_without_domain = self.get_url_without_domain(v)
                                web_url = v
                                content = content.replace(web_url, system_url).replace(web_url_without_domain,
                                                                                       system_url)
                    else:
                        text = dt['text']
                        code = dt['code']
                        msg = f"文件服务替换失败({code}):{text}"
                        self.logger.error(f"文件服务替换失败({code}):{text}")
                        break
            except Exception as e:
                msg = f"文件服务替换失败 {e} "
                self.logger.error(f"文件服务替换失败 {e} ")
        else:
            msg = f"文件服务替换失败, 请求状态码: {0}".format(ret.status_code)
            self.logger.error(f"文件服务替换失败, 请求状态码: {0}".format(ret.status_code))
        return msg, content

    def get_url_without_domain(self, url):
        if 'http' in url:
            com = re.compile('http://.*?(/.*)')
            urls = com.findall(url)
            url = urls[0] if urls else url
        return urllib.parse.quote(url) if self.is_chinese(url) else url

    def is_chinese(self, string):
        """
        检查整个字符串是否包含中文
        """
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    def deal_data_not_clean(self, item):
        try:
            deal_data = deal_base_notices_data({})
            for var in self.clean_filed_list:
                item[var] = deal_data.get(var, "")
            item["is_clean"] = const.TYPE_CLEAN_NOT_DONE
            return item
        except Exception as e:
            return item

    def get_id_by_project_category(self, category_str):
        if not category_str:
            return ""
        if category_str in const.CATEGORY_ENGINEERING_LIST:
            return const.ID_CATEGORY_ENGINEERING
        elif category_str in const.CATEGORY_PURCHASE_LIST:
            return const.ID_CATEGORY_PURCHASE
        elif category_str in const.CATEGORY_PROPERTY_LIST:
            return const.ID_CATEGORY_PROPERTY
        elif category_str in const.CATEGORY_OTHERS_LIST:
            return const.ID_CATEGORY_OTHERS
        else:
            return ""

    def get_pre_process_data(self, item):
        try:
            item["content"] = html.unescape(item["content"])
            if item["title_name"] is None:
                area_deal_dict = deal_area_data(info_source=item["info_source"], area_id=item["area_id"]) or {}
            elif item["info_source"] is None:
                area_deal_dict = deal_area_data(title_name=item["title_name"], area_id=item["area_id"]) or {}
            else:
                area_deal_dict = deal_area_data(title_name=item["title_name"], info_source=item["info_source"],
                                                area_id=item["area_id"]) or {}
            # content_str = item["content"]
            if item["is_have_file"] == "1" or item["is_have_file"] == 1:
                self.is_have_file = True
                content_str = item["content"]
                # msg, content_str = self.request_download(files_path=str(item["files_path"]), content=item["content"],
                #                                          is_have_file=item["is_have_file"])
                # # 请求失败 修改 is_have_file
                # # msg = 'test file request error'
                # if msg:
                #     item['is_have_file'] = "2"

        except Exception as e:
            self.logger.error(f"文件服务替换失败 {e} ")
        return {
            "source_url": item["origin"],
            "title": item["title_name"],
            "publish_time": "" if const.DEFAULT_PUB_TIME in str(item["pub_time"]) else str(item["pub_time"]),
            "source": "" if item["info_source"] in const.EMPTY_LIST else item["info_source"],
            "classify_id": str(item["notice_type"]),
            "classify_name": const.TYPE_NOTICE_DICT.get(str(item["notice_type"]), ""),
            "area_code": area_deal_dict.get("code", ""),
            "area": area_deal_dict.get("area", ""),
            "content": content_str if self.is_have_file else item["content"],
            "project_type": self.get_id_by_project_category(dict(item).get("category", "")),
            "is_have_file": item['is_have_file'],
        }

    def extract_data(self, pre_data, area_id="00"):
        br_cf = init_yaml('before_regular', area_id=area_id)
        cr_cf = init_yaml('common_regular', area_id=area_id)
        kw_cf = init_yaml('keyword', area_id=area_id)
        rm_cf = init_yaml('public_regular', area_id=area_id, file_name='remove_chars')
        regular_params = {
            'br_cf': br_cf,
            'cr_cf': cr_cf,
            'rm_cf': rm_cf,
        }

        data = pre_data.get("content")
        # 提取特有字段 11
        notice_nature = bid_file = bid_file_start_time = bid_file_end_time = apply_end_time = bid_amount = ""
        notice_start_time = notice_end_time = aberrant_type = tenderopen_time = successful_bidder = project_leader = ""
        if pre_data.get("classify_id") == const.TYPE_ZB_NOTICE:
            notice_nature = "正常公告"
            bid_file = self.get_keys_value_from_content(data, "招标文件", area_id=area_id)
            notice_start_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "公告开始时间", area_id=area_id))
            notice_end_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "公告结束时间", area_id=area_id))
            bid_file_start_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "招标文件获取开始时间", area_id=area_id))
            bid_file_end_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "招标文件获取截止时间", area_id=area_id))
            apply_end_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "报名截止时间", area_id=area_id))

            tenderopen_time_tags = get_keywords(kw_cf, 'tenderopen_time')
            tenderopen_times = get_accurate_pub_time(self.get_keys_value_from_content(data, tenderopen_time_tags,
                                                     area_id=area_id, field_name='tenderopen_time', **regular_params))  # √
            # 特殊处理 未获取到值则使用开标时间
            if not notice_end_time:
                notice_end_time = tenderopen_times
            if not apply_end_time:
                apply_end_time = tenderopen_times
            if re.findall('.*(\d{4}.*\d{1,2}.*\d{1,2}.*\d{2}[: ：]\d{2}).*', tenderopen_times):
                tenderopen_time = re.findall('.*(\d{4}.*\d{1,2}.*\d{1,2}.*\d{2}[: ：]\d{2}).*', tenderopen_times)[0]
            else:
                tenderopen_time = tenderopen_times

        elif pre_data.get("classify_id") == const.TYPE_ZB_ADVANCE_NOTICE:
            notice_nature = "正常公告"
        elif pre_data.get("classify_id") == const.TYPE_ZB_ALTERATION:
            notice_nature = "正常公告"
        elif pre_data.get("classify_id") == const.TYPE_ZB_ABNORMAL:
            aberrant_type = self.get_keys_value_from_content(data, ["异常类型"], area_id=area_id)
        elif pre_data.get("classify_id") == const.TYPE_WIN_ADVANCE_NOTICE:
            notice_start_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, ["公告开始时间"], area_id=area_id))
            notice_end_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, ["公告结束时间"], area_id=area_id))
        elif pre_data.get("classify_id") == const.TYPE_WIN_NOTICE:

            successful_bidder_tags = get_keywords(kw_cf, 'successful_bidder')
            successful_bidder = self.get_keys_value_from_content(data, successful_bidder_tags, area_id=area_id,
                                 field_name='successful_bidder', **regular_params)  # √
            bid_amount_tags = get_keywords(kw_cf, 'bid_amount')
            bid_amount = self.get_keys_value_from_content(data, bid_amount_tags, area_id=area_id,
                                                          field_name='bid_amount', **regular_params)  # √

            project_leader_tags = get_keywords(kw_cf, 'project_leader')
            project_leader = self.get_keys_value_from_content(data, project_leader_tags, area_id=area_id,
                                                              field_name='project_leader', **regular_params)
        elif pre_data.get("classify_id") == const.TYPE_QUALIFICATION_ADVANCE_NOTICE:
            pass
        elif pre_data.get("classify_id") == const.TYPE_OTHERS_NOTICE:
            pass

        # 采集自有字段 9
        title = pre_data.get("title")  # 公告标题
        source = pre_data.get("source")  # 来源(采集的公告就填写采集网站、用户和平台发布就用用户名)
        source_url = pre_data.get("source_url")  # 采集发布来源网站URL
        publish_time = get_accurate_pub_time(pre_data.get("publish_time"))  # 发布时间
        classify_id = pre_data.get("classify_id")  # 公告分类id
        classify_name = pre_data.get("classify_name")  # 公告分类名称
        area_code = pre_data.get("area_code")  # 区县编号
        area = pre_data.get("area")  # 地区
        content = pre_data.get("content")  # 公告内容
        project_type = pre_data.get("project_type")  # 类型
        is_have_file = pre_data.get("is_have_file")  # 修改是否含有文件

        # 默认字段 2
        state = const.TYPE_UPLOAD_NOTICES_STATE_WAIT  # 状态0-待发布1-已发布2-已下架3-待审核4-审核拒绝
        sign_type = const.TYPE_UPLOAD_NOTICES_SIGN_COLLECT  # 标讯类型 0-平台发布1-用户发布2-采集发布

        # 公共提取字段 15

        project_contact_information_tags = get_keywords(kw_cf, 'project_contact_information')

        project_contact_information = self.get_keys_value_from_content(content, project_contact_information_tags,
                                     area_id=area_id, field_name='project_contact_information', **regular_params)

        project_name_tags = get_keywords(kw_cf, 'project_name')
        project_name = self.get_keys_value_from_content(content, project_name_tags, area_id=area_id,
                                                        field_name='project_name', title=title, **regular_params)  # √

        project_number_tags = get_keywords(kw_cf, 'project_number')
        project_numbers = self.get_keys_value_from_content(content, project_number_tags, area_id=area_id,
                                                           field_name='project_number', **regular_params)  # √
        if re.findall(r'.*\/(.*)', project_numbers):
            project_number = project_numbers
        else:
            project_number = project_numbers

        tenderee_tags = get_keywords(kw_cf, 'tenderee')
        tenderee = self.get_keys_value_from_content(content, tenderee_tags, area_id=area_id,
                                                    field_name='tenderee', **regular_params)  # √
        if len(tenderee) < 2:
            tenderee = ''

        liaison_tags = get_keywords(kw_cf, 'liaison')
        liaison = self.get_keys_value_from_content(content, liaison_tags, area_id=area_id,
                                                   field_name='liaison', **regular_params)

        bidding_contact_tags = get_keywords(kw_cf, 'bidding_contact')
        bidding_contact = self.get_keys_value_from_content(content, bidding_contact_tags, area_id=area_id,
                                                           field_name='bidding_contact', **regular_params)
        bidding_agency_tags = get_keywords(kw_cf, 'bidding_agency')
        bidding_agency = self.get_keys_value_from_content(content, bidding_agency_tags, area_id=area_id,
                                                          field_name='bidding_agency', **regular_params)  # √
        contact_information_tags = get_keywords(kw_cf, 'contact_information')
        contact_information = self.get_keys_value_from_content(content, contact_information_tags, area_id=area_id,
                                                          field_name='contact_information', **regular_params)  # √

        agent_contact_tags = get_keywords(kw_cf, 'agent_contact')
        agent_contact = self.get_keys_value_from_content(content, agent_contact_tags, area_id=area_id,
                                                          field_name='agent_contact', **regular_params)  # √

        budget_amount_tags = get_keywords(kw_cf, 'budget_amount')
        budget_amount = self.get_keys_value_from_content(content, budget_amount_tags, area_id=area_id,
                                                          field_name='budget_amount', **regular_params)  # √

        email = self.get_keys_value_from_content(content, ["电子邮箱"], area_id=area_id)
        address = self.get_keys_value_from_content(content, ["详细地址", "采购单位地址"], area_id=area_id)
        description = self.get_keys_value_from_content(content, ["招标范围", "招标方式", "招标组织形式"], area_id=area_id)
        bid_type = self.get_keys_value_from_content(content, "招标方式", area_id=area_id)
        bid_modus = self.get_keys_value_from_content(content, "招标组织形式", area_id=area_id)
        inspect_dept = self.get_keys_value_from_content(content, "监督部门", area_id=area_id)
        review_dept = self.get_keys_value_from_content(content, "审核部门", area_id=area_id)
        company_type = self.get_keys_value_from_content(content, "单位类型", area_id=area_id)

        # print('项目名称: ', project_name, '***',
        #       '项目编号: ', project_number, '***',
        #       '预算金额: ', budget_amount, '***',
        #       '招标联系人: ', bidding_contact, '***',
        #       '招标人联系方式: ', liaison, '***',  # 招标人联系方式
        #       '招标单位: ', tenderee, '***', '\n',
        #       '代理联系人: ', agent_contact,
        #       '代理机构: ', bidding_agency, '***',
        #       '招标代理联系方式: ', contact_information, '***',  # 招标代理联系方式
        #       '开标时间: ', tenderopen_time, '***',
        #       '项目负责人: ', project_leader, '***',
        #       '项目负责人联系方式: ', project_contact_information, '***'
        #       )
        # print('**************'*10)

        # 暂未使用字段
        file_ids = ""
        return {'title': title,
                'project_number': project_number,
                'project_name': project_name,
                'tenderee': tenderee,
                'bidding_agency': bidding_agency,
                'area_code': area_code,
                'area': area,
                'address': address,
                'email': email,
                'description': description,
                'bid_type': bid_type,
                'bid_modus': bid_modus,
                'inspect_dept': inspect_dept,
                'review_dept': review_dept,
                'notice_nature': notice_nature,
                'bid_file': bid_file,
                'bid_file_start_time': bid_file_start_time,
                'bid_file_end_time': bid_file_end_time,
                'apply_end_time': apply_end_time,
                'notice_start_time': notice_start_time,
                'notice_end_time': notice_end_time,
                'aberrant_type': aberrant_type,
                'budget_amount': budget_amount,
                'tenderopen_time': tenderopen_time,
                'publish_time': publish_time,
                'liaison': liaison,
                'contact_information': contact_information,
                'content': content,
                'classify_id': classify_id,
                'classify_name': classify_name,
                'project_type': project_type,
                'state': state,
                'file_ids': file_ids,
                'company_type': company_type,
                'successful_bidder': successful_bidder,
                'bid_amount': bid_amount,
                'sign_type': sign_type,
                'source': source,
                'source_url': source_url,
                'is_have_file': is_have_file,
                'project_leader': project_leader,
                'project_contact_information': project_contact_information,
                'bidding_contact': bidding_contact,
                'agent_contact': agent_contact
                }

    def get_keys_value_from_content(self, content, keys, area_id="00", field_name=None, title=None, **kwargs):
        value = get_keys_value_from_content_ahead(
            content, keys, area_id=area_id, field_name=field_name, title=title, **kwargs
        )
        # 再次针对性清洗数据
        try:
            if ">" in value:
                return value.split(">")[-1].strip()
            return value
        except:
            return value

    def run_clean(self, table_name, engine_config, is_clean_default=1):
        area_id = table_name.split("_")[-1]
        self.engine = create_engine(engine_config)
        rows = 10000
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(f"SELECT * FROM {table_name} WHERE id=465").fetchall()
                # results = conn.execute(f"SELECT * FROM {table_name} WHERE (project_type='5' or project_type='6') and classify_name='中标公告'").fetchall()
                # results = conn.execute(f"SELECT * FROM {table_name} WHERE (project_type='1') and classify_name='招标公告'").fetchall()
                # results = conn.execute(f"SELECT * FROM {table_name} WHERE (project_type='5' or project_type='6') and classify_name='中标公告' and (files_path not like '%%pdf/img/doc0.jpg%%')").fetchall()
                results = [dict(zip(result.keys(), result)) for result in results]
                for item in results:
                    try:
                        if str(item["notice_type"]) == const.TYPE_UNKNOWN_NOTICE:
                            continue
                        item_id = str(item["id"])
                        self.is_have_file = False
                        pre_process_dict = self.get_pre_process_data(item)
                        deal_data = self.extract_data(pre_data=pre_process_dict, area_id=area_id)
                        deal_data = deal_base_notices_data(deal_data, is_hump=False)
                        # 指定需要更新的字段
                        update_fields = [
                            'project_name',
                            'project_number',
                            'budget_amount',
                            'tenderee',
                            'bidding_agency',
                            'liaison',  # 招标人联系方式
                            'contact_information',  # 招标代理联系方式
                            'successful_bidder',
                            'bid_amount',
                            'tenderopen_time',
                            'project_leader',
                            'project_contact_information',
                            'bidding_contact',
                            'agent_contact',
                        ]
                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            """ , """.join(["""{} = :{}""".format(var, var) for var in update_fields]) +
                            """, is_clean = {} """.format(is_clean_default) +
                            """where id = {} """.format(item_id))
                        print('item_id:{0}'.format(item_id))
                        deal_data = {k: deal_data[k] for k in update_fields}
                        result = conn.execute(update_sql, **deal_data)
                        if result.rowcount != 1:
                            print("error")
                        else:
                            print("success update.", item_id)

                    except Exception as e:
                        print(f"{e=} {item_id=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                print(start)

    def run_clean_ex(self, table_name, engine_config, is_clean_default=1):
        area_id = table_name.split("_")[-1]
        self.engine = create_engine(engine_config)
        rows = 500
        start = 0
        # push_time  获取当天时间   从数据库取出等于当天时间的数据  做清洗
        push_time = '{0:%Y-%m-%d}'.format(datetime.datetime.now())
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select * from {table_name} where is_clean =1 and is_upload=0 and pub_time='{push_time}' limit {start}, {rows}").fetchall()
                results = [dict(zip(result.keys(), result)) for result in results]
                for item in results:
                    try:
                        if str(item["notice_type"]) == const.TYPE_UNKNOWN_NOTICE:
                            continue
                        item_id = str(item["id"])
                        self.is_have_file = False
                        pre_process_dict = self.get_pre_process_data(item)
                        deal_data = self.extract_data(pre_data=pre_process_dict, area_id=area_id)
                        deal_data = deal_base_notices_data(deal_data, is_hump=False)
                        # 指定需要更新的字段
                        update_fields = [
                            'project_name',
                            'project_number',
                            'budget_amount',
                            'tenderee',
                            'bidding_agency',
                            'liaison',
                            'contact_information',
                            'successful_bidder',
                            'bid_amount',
                            'tenderopen_time',
                        ]
                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            """ , """.join(["""{} = :{}""".format(var, var) for var in update_fields]) +
                            """, is_clean = {} """.format(is_clean_default) +
                            """where id = {} """.format(item_id))
                        print('item_id:{0}'.format(item_id))
                        deal_data = {k: deal_data[k] for k in update_fields}
                        result = conn.execute(update_sql, **deal_data)
                        if result.rowcount != 1:
                            print("error")
                        else:
                            print("success update.", item_id)

                    except Exception as e:
                        print(f"{e=} {item_id=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                print(start)


if __name__ == "__main__":
    cp = CleanPipeline("1", "1", "1")
    # 正式洗数据 解开注释需要当心！！！
    # cp.run_clean_ex(table_name="notices_00", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_00", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/data_collection?charset=utf8mb4')

    cp.test_file = True  # 本地测试清洗test_file为true 是测试库 反之 正式库
    engine = 'test2_data_collection' if cp.test_file else 'data_collection'
    cp.run_clean(
        table_name="notices_3312",
        engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/{}?charset=utf8mb4'.format(engine),
    )

    # # 测试洗数据 默认测试
    # cp.run_clean_ex(table_name="notices_47", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4')

    pass
