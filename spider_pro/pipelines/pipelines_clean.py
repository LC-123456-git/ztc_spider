#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2021/01/14
# @Author : wwj
# @Describe: notices item数据清洗
import re
import time
import urllib
import requests
from ast import literal_eval
from urllib import parse
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import deal_base_notices_data, deal_area_data, get_accurate_pub_time
from sqlalchemy import create_engine, text
from spider_pro.rules_clean import get_keys_value_from_content_ahead


class CleanPipeline(object):

    def __init__(self, name, area_id, logger, **kwargs):
        self.name = name
        self.area_id = area_id
        self.logger = logger
        self.is_have_file = False
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
        ret = requests.post(url=const.FILE_SERVER, data={"jsonString": files_path})
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
                                content = content.replace(web_url, system_url).replace(
                                    web_url_without_domain, system_url)
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
            if item["title_name"] is None:
                area_deal_dict = deal_area_data(info_source=item["info_source"], area_id=item["area_id"]) or {}
            elif item["info_source"] is None:
                area_deal_dict = deal_area_data(title_name=item["title_name"], area_id=item["area_id"]) or {}
            else:
                area_deal_dict = deal_area_data(title_name=item["title_name"], info_source=item["info_source"],
                                                area_id=item["area_id"]) or {}
            if item["is_have_file"] == "1" or item["is_have_file"] == 1:
                self.is_have_file = True
                # self.content_str = item["content"]
                msg, content_str = self.request_download(files_path=str(item["files_path"]), content=item["content"],
                                                         is_have_file=item["is_have_file"])
                # 请求失败 修改 is_have_file
                # msg = 'test file request error'
                if msg:
                    item['is_have_file'] = "2"

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
        data = pre_data.get("content")
        # 提取特有字段 11
        notice_nature = bid_file = bid_file_start_time = bid_file_end_time = apply_end_time = bid_amount = ""
        notice_start_time = notice_end_time = aberrant_type = tenderopen_time = successful_bidder = ""
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
            tenderopen_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "开标时间", area_id=area_id))

            # 特殊处理 未获取到值则使用开标时间
            if not notice_end_time:
                notice_end_time = tenderopen_time
            if not apply_end_time:
                apply_end_time = tenderopen_time
        elif pre_data.get("classify_id") == const.TYPE_ZB_ADVANCE_NOTICE:
            notice_nature = "正常公告"
        elif pre_data.get("classify_id") == const.TYPE_ZB_ALTERATION:
            notice_nature = "正常公告"
        elif pre_data.get("classify_id") == const.TYPE_ZB_ABNORMAL:
            aberrant_type = self.get_keys_value_from_content(data, "异常类型", area_id=area_id)
        elif pre_data.get("classify_id") == const.TYPE_WIN_ADVANCE_NOTICE:
            notice_start_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "公告开始时间", area_id=area_id))
            notice_end_time = get_accurate_pub_time(
                self.get_keys_value_from_content(data, "公告结束时间", area_id=area_id))
        elif pre_data.get("classify_id") == const.TYPE_WIN_NOTICE:
            successful_bidder = self.get_keys_value_from_content(data, ["中标人", "中标人名称", "中标单位"], area_id=area_id)
            bid_amount = self.get_keys_value_from_content(data, "中标价格", area_id=area_id)
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
        project_name = self.get_keys_value_from_content(content, ["项目名称", "招标项目", "工程名称", "招标工程项目"], area_id=area_id)
        project_number = self.get_keys_value_from_content(content, ["项目编号", "招标项目编号", "招标编号"], area_id=area_id)
        tenderee = self.get_keys_value_from_content(content, ["招标人", "招&nbsp;标&nbsp;人", "招标单位"], area_id=area_id)
        bidding_agency = self.get_keys_value_from_content(content, "招标代理", area_id=area_id)
        budget_amount = self.get_keys_value_from_content(content, "项目金额", area_id=area_id)
        address = self.get_keys_value_from_content(content, "详细地址", area_id=area_id)
        liaison = self.get_keys_value_from_content(content, "联系人", area_id=area_id)
        contact_information = self.get_keys_value_from_content(content, "联系电话", area_id=area_id)
        email = self.get_keys_value_from_content(content, "电子邮箱", area_id=area_id)
        description = self.get_keys_value_from_content(content, ["招标范围", "招标方式", "招标组织形式"], area_id=area_id)
        bid_type = self.get_keys_value_from_content(content, "招标方式", area_id=area_id)
        bid_modus = self.get_keys_value_from_content(content, "招标组织形式", area_id=area_id)
        inspect_dept = self.get_keys_value_from_content(content, "监督部门", area_id=area_id)
        review_dept = self.get_keys_value_from_content(content, "审核部门", area_id=area_id)
        company_type = self.get_keys_value_from_content(content, "单位类型", area_id=area_id)

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
                }

    def get_keys_value_from_content(self, content: str, keys, area_id="00"):
        value = get_keys_value_from_content_ahead(content, keys, area_id=area_id)
        # 再次针对性清洗数据
        try:
            if ">" in value:
                return value.split(">")[-1].strip()
            return value
        except:
            return value

    def run_clean(self, table_name, engine_config, is_clean_default=1):
        area_id = table_name.strip("_")[-1]
        self.engine = create_engine(engine_config)
        rows = 5000
        start = 0
        with self.engine.connect() as conn:
            while True:
                # results = conn.execute(
                #     f"select * from {table_name} where is_clean = {const.TYPE_CLEAN_NOT_DONE} limit {rows} offset {start} ").fetchall()
                # results = conn.execute(
                #     f"select * from {table_name} where is_clean =0 and is_upload=0  limit {start}, {rows}").fetchall()
                results = conn.execute(
                    f"select * from {table_name} where is_have_file = 1").fetchall()
                for item in results:
                    try:
                        if str(item["notice_type"]) == const.TYPE_UNKNOWN_NOTICE:
                            continue
                        item_id = str(item["id"])
                        self.is_have_file = False
                        pre_process_dict = self.get_pre_process_data(item)
                        deal_data = self.extract_data(pre_data=pre_process_dict, area_id=area_id)
                        deal_data = deal_base_notices_data(deal_data, is_hump=False)

                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            """ , """.join(["""{} = :{}""".format(var, var) for var in self.clean_filed_list]) +
                            """, is_clean = {} """.format(is_clean_default) +
                            """where id = {} """.format(item_id))

                        result = conn.execute(update_sql, **deal_data)
                        if result.rowcount != 1:
                            print("error")
                        else:
                            pass
                            # print("true", item_id)

                    except Exception as e:
                        print(f"{e=} {item_id=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                print(start)

    def run_clean_ex(self, table_name, engine_config, is_clean_default=1):
        area_id = table_name.strip("_")[-1]
        self.engine = create_engine(engine_config)
        rows = 1000
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select id,category from {table_name} limit {rows} offset {start} ").fetchall()
                for item in results:
                    try:
                        # if str(item["notice_type"]) == const.TYPE_UNKNOWN_NOTICE:
                        #     continue
                        item_id = str(item["id"])
                        project_type = self.get_id_by_project_category(dict(item).get("category", ""))
                        # deal_data = self.extract_data(pre_data=pre_process_dict, area_id=area_id)
                        # deal_data = deal_base_notices_data(deal_data, is_hump=False)

                        if not project_type:
                            continue

                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            # """ , """.join(["""{} = :{}""".format(var, var) for var in self.clean_filed_list]) +
                            """project_type = {} """.format(project_type) +
                            # """, is_clean = {} """.format(is_clean_default) +
                            """where id = {} """.format(item_id))

                        result = conn.execute(update_sql, **{"project_type": project_type})
                        if result.rowcount != 1:
                            print("error")
                        else:
                            pass
                            # print("true", item_id)

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
    # cp.run_clean_ex(table_name="notices_00", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_00", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_02", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_11", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_13", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    # cp.run_clean(table_name="notices_15", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4')
    cp.run_clean(table_name="notices_3307",
                 engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4')

    # # 测试洗数据 默认测试
    # cp.run_clean_ex(table_name="notices_47", engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/test2_data_collection?charset=utf8mb4')

    pass
