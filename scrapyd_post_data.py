#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/18
# @Author : wwj
# @Describe: pass
import os
import sys
import json
import re
import ast
import time
import datetime
import requests
import threading
import platform
from operator import itemgetter
from sqlalchemy import create_engine
from spider_pro.utils import get_accurate_pub_time

def get_limit_char_from_data(data, name, limit=9999, not_null=False):
    try:
        if data.get(name):
            return data.get(name)[:limit]
            # return pymysql.escape_string(data.get(name)[:limit])
        else:
            return "null" if not_null else ""
    except:
        return "null" if not_null else ""


def process_data_by_type_begin_upload(data, data_type="datetime"):
    """
    待上传数据 格式处理
    :param data: 待处理数据
    :param data_type: 数据类型 datetime, int, double
    :return: data : str
    """
    if data_type == "datetime":
        try:
            if r := datetime.datetime.fromisoformat(data):
                return r.strftime("%Y-%m-%d %H:%M:%S")
            else:
                a = datetime.datetime.strptime(data, "%Y-%m-%d %H:%M")
                return a
        except:
            try:
                a = datetime.datetime.strptime(data, "%Y-%m-%d %H:%M")
                return a
            except:
                return ""

    elif data_type == "email":
        f = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
        if re.match(data, f):
            return data
        else:
            return ""
    elif data_type == "number":
        try:
            data_aft = float(data)
            return data_aft
        except:
            return ""
    else:
        return data


def deal_base_notices_data(data, is_hump=False):
    # 判断驼峰
    if is_hump:
        return {
            "title": get_limit_char_from_data(data, "title", 9999),  # 公告标题
            "projectNumber": get_limit_char_from_data(data, "project_number", 300),  # 项目编号
            "projectName": get_limit_char_from_data(data, "project_name", 100),  # 项目名称
            "tenderee": get_limit_char_from_data(data, "tenderee", 100),  # 招标人
            "biddingAgency": get_limit_char_from_data(data, "bidding_agency", 255),  # 招标代理

            "areaCode": get_limit_char_from_data(data, "area_code", 25),  # 区县编号
            "area": get_limit_char_from_data(data, "area", 85),  # 地区
            "address": get_limit_char_from_data(data, "address", 166),  # 详细地址
            "email": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "email", 255), data_type="email"),  # 电子邮箱
            "description": data.get("description", ""),  # 招标方案说明

            'bidType': get_limit_char_from_data(data, "bid_type", 85),
            'bidModus': get_limit_char_from_data(data, "bid_modus", 85),
            'inspectDept': get_limit_char_from_data(data, "inspect_dept", 85),
            'reviewDept': get_limit_char_from_data(data, "review_dept", 85),
            'noticeNature': get_limit_char_from_data(data, "notice_nature", 85),

            "bidFile": get_limit_char_from_data(data, "bid_file", 500),
            "bidFileStartTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_file_start_time", 100), data_type="datetime"),
            "bidFileEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_file_end_time", 100), data_type="datetime"),
            "applyEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "apply_end_time", 100), data_type="datetime"),
            "noticeStartTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "notice_start_time", 100), data_type="datetime"),

            "noticeEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "notice_end_time", 100), data_type="datetime"),
            "aberrantType": get_limit_char_from_data(data, "aberrant_type", 100),
            "budgetAmount": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "budget_amount", 255), data_type="number"),
            "tenderopenTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "tenderopen_time", 100), data_type="datetime"),

            "publishTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "publish_time"), data_type="datetime"),
            "liaison": get_limit_char_from_data(data, "liaison", 100),
            "contactInformation": get_limit_char_from_data(data, "contact_information", 255),
            "content": data.get("content", ""),  # 公告内容
            "classifyId": data.get("classify_id", ""),

            "classifyName": get_limit_char_from_data(data, "classify_name", 255),
            "projectType": get_limit_char_from_data(data, "project_type", 255),
            "state": get_limit_char_from_data(data, "state", 1) or "0",
            "fileIds": get_limit_char_from_data(data, "file_ids", 100),
            "companyType": get_limit_char_from_data(data, "company_type", 100),

            "successfulBidder": get_limit_char_from_data(data, "successful_bidder", 255),  # 中标方
            "bidAmount": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_amount"), data_type="number"),  # 中标金额
            "signType": get_limit_char_from_data(data, "sign_type", 1) or "2",  # '标讯类型 0-平台发布1-用户发布2-采集发布'
            "source": get_limit_char_from_data(data, "source", 500),  # '来源(采集的公告就填写采集网站、用户和平台发布就用用户名)'
            "sourceUrl": get_limit_char_from_data(data, "source_url", 500),  # 采集发布来源网站URL

            "noticeId": data.get("uuid", ""),
            # "is_upload": get_int_from_data(data, "0")

            "pushTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "push_time"), data_type="datetime"
            ),  # 推送时间
        }
    else:
        return {
            "title": get_limit_char_from_data(data, "title", 9999),  # 公告标题
            "project_number": get_limit_char_from_data(data, "project_number", 300),  # 项目编号
            "project_name": get_limit_char_from_data(data, "project_name", 100),  # 项目名称
            "tenderee": get_limit_char_from_data(data, "tenderee", 100),  # 招标人
            "bidding_agency": get_limit_char_from_data(data, "bidding_agency", 255),  # 招标代理

            "area_code": get_limit_char_from_data(data, "area_code", 25),  # 区县编号
            "area": get_limit_char_from_data(data, "area", 85),  # 地区
            "address": get_limit_char_from_data(data, "address", 166),  # 详细地址
            "email": get_limit_char_from_data(data, "email", 255),  # 电子邮箱
            "description": data.get("description", ""),  # 招标方案说明

            'bid_type': get_limit_char_from_data(data, "bid_type", 85),
            'bid_modus': get_limit_char_from_data(data, "bid_modus", 85),
            'inspect_dept': get_limit_char_from_data(data, "inspect_dept", 85),
            'review_dept': get_limit_char_from_data(data, "review_dept", 85),
            'notice_nature': get_limit_char_from_data(data, "notice_nature", 85),

            "bid_file": get_limit_char_from_data(data, "bid_file", 500),
            "bid_file_start_time": get_limit_char_from_data(data, "bid_file_start_time", 100),
            "bid_file_end_time": get_limit_char_from_data(data, "bid_file_end_time", 100),
            "apply_end_time": get_limit_char_from_data(data, "apply_end_time", 100),
            "notice_start_time": get_limit_char_from_data(data, "notice_start_time", 100),

            "notice_end_time": get_limit_char_from_data(data, "notice_end_time", 100),
            "aberrant_type": get_limit_char_from_data(data, "aberrant_type", 100),
            "budget_amount": get_limit_char_from_data(data, "budget_amount", 255),
            "tenderopen_time": get_limit_char_from_data(data, "tenderopen_time", 100),

            "publish_time": get_limit_char_from_data(data, "publish_time"),
            "liaison": get_limit_char_from_data(data, "liaison", 100),
            "contact_information": get_limit_char_from_data(data, "contact_information", 255),
            "content": data.get("content", ""),  # 公告内容
            "classify_id": data.get("classify_id", ""),

            "classify_name": get_limit_char_from_data(data, "classify_name", 255),
            "project_type": get_limit_char_from_data(data, "project_type", 255),
            "state": get_limit_char_from_data(data, "state", 1) or "0",
            "file_ids": get_limit_char_from_data(data, "file_ids", 100),
            "company_type": get_limit_char_from_data(data, "company_type", 100),

            "successful_bidder": get_limit_char_from_data(data, "successful_bidder", 255),  # 中标方
            "bid_amount": get_limit_char_from_data(data, "bid_amount"),  # 中标金额
            "sign_type": get_limit_char_from_data(data, "sign_type", 1) or "2",  # '标讯类型 0-平台发布1-用户发布2-采集发布'
            "source": get_limit_char_from_data(data, "source", 500),  # '来源(采集的公告就填写采集网站、用户和平台发布就用用户名)'
            "source_url": get_limit_char_from_data(data, "source_url", 500),  # 采集发布来源网站URL

            # 自有字段
            "is_clean": get_limit_char_from_data(data, "is_clean") or "0",

            "push_time": get_limit_char_from_data(data, "push_time"),  # 推送时间
        }


class ScrapyDataPost(object):

    def __init__(self, table_name, engine_config, post_url):
        self.table_name = table_name
        self.engine_config = engine_config
        self.post_url = post_url
        self.engine = create_engine(engine_config, pool_size=105)  # TODO pool_size need add

    @staticmethod
    def reset_file_url(content, files_path_string):
        """
        替换文件下载的地址为原站点地址
            0 下载中 不推送
            1 成功
            2 失败 替换站点
        Args:
            content:
            files_path_string:
        Returns:
            content:
        """
        if_push = True
        try:
            files_path = ast.literal_eval(files_path_string)
            ret = requests.post(url='http://tfile.zhaotx.cn/sapi/webfile/addWebFileTask', data={
                'jsonString': files_path
            })
            if ret.status_code == 200:
                res = json.loads(ret.content)
                error_download = False
                for r in res:
                    if r['downloadState'] == "2":
                        error_download = True
                        break
                if error_download:
                    for r in res:
                        content = content.replace(r['systemUrl'], r['sourceUrl'])
                else:
                    for r in res:
                        if r['downloadState'] == "0":  # 下载中
                            if_push = False
                            break
            else:
                if_push = False
        except Exception as e:
            print(e)
        return if_push, content

    def run_post(self, d_time="1970-01-01", table_name=None, e_time=None):
        table_name = table_name if table_name else self.table_name
        rows = 300
        err_start = 0
        with self.engine.connect() as conn:
            while True:
                print("start query data")
                """ # 正式推  放开
                # if not e_time:
                #     results = conn.execute(
                #         f"select * from {table_name} where is_clean = 1 and is_upload = 0 and pub_time >= '{d_time}' limit {err_start},{rows} ").fetchall()
                # else:
                #     results = conn.execute(
                #         f"select * from {table_name} where is_clean = 1 and is_upload = 0 and pub_time >= '{d_time}' and pub_time < '{e_time}' limit {err_start},{rows} ").fetchall()
                """
                results = conn.execute(
                    # f"-- select * from {table_name} where is_clean = 1 and is_upload = 0 and is_have_file = 1 and pub_time >= '{d_time}' and pub_time < '{e_time}'limit {err_start},{rows} ").fetchall()
                    f"select * from {table_name} where is_clean = 1 and is_upload = 0 and pub_time > '{d_time}' and pub_time <= '{e_time}'limit {err_start},{rows} ").fetchall()
                if len(results) != 0:
                    area_id = results[0]['area_id']
                    push_time = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
                    push_day = datetime.date.today()
                    itme_num = 0
                    for item in results:
                        item_dict = dict(item)
                        item_id = item_dict.get("id")
                        if item_dict['is_have_file'] != 0:
                            if_push, item_dict['content'] = ScrapyDataPost.reset_file_url(item_dict['content'], item_dict['files_path'])
                            if not if_push:
                                continue

                        publish_time = get_accurate_pub_time(item_dict.get("publish_time"))
                        b = publish_time.split('-')
                        for i in range(2):
                            b[1] = b[1].zfill(2)  # 左填充
                            b[2] = b[2].zfill(2)
                            sss = '-'.join(b)
                        item_dict["publish_time"] = sss
                        r = False
                        try:
                            data = deal_base_notices_data(item_dict, is_hump=True)
                            # 因为浙江没有项目类型，这里做特殊处理
                            # if table_name == "notices_15" or table_name == "notices_3304" or table_name == "notices_3324" or table_name == 'notices_53' or table_name == 'notices_65':
                            if table_name in [
                                'notices_15',
                                'notices_3304',
                                'notices_3324',
                                'notices_52',
                                'notices_53',
                                'notices_65',
                                'notices_77',
                                'notices_78',
                                'notices_83',
                                'notices_85',
                            ]:
                                keys = ["title", "content", "classifyName", "area", "publishTime", "sourceUrl"]
                            elif table_name in ['notices_79', 'notices_82']:   #  目前不需要 传后台 数据中心
                                keys = ["title", "content", "classifyName", "publishTime", "sourceUrl"]
                            else:
                                keys = ["title", "content", "projectType", "classifyName", "area", "publishTime",
                                        "sourceUrl"]

                            out = list(itemgetter(*keys)(data))
                            if not all(out):
                                pass
                            else:
                                r = requests.post(url=self.post_url, data=data, timeout=10)
                                if r.status_code != 200:
                                    print(r.status_code)
                                    r = False
                                else:
                                    r_dict = json.loads(r.text)
                                    if r_dict.get("code") in [200, "200"]:
                                        r = True
                                        itme_num += 1
                                    elif r_dict.get("code") in [411, "411"]:  # 重复数据，is_upload为2
                                        r = False
                                        update_sql = f"update {table_name} set is_upload = 2 where id = {item_id}"  # 推送
                                        result = conn.execute(update_sql)
                                        if result.rowcount != 2:
                                            print("update", item_id, False)
                                        else:
                                            print("update", item_id, True)
                                    else:
                                        print(r_dict.get("code"))
                                        r = False

                                if not r:
                                    print("upload", item_id, r)
                                else:
                                    pass
                                    print("upload", item_id, r)
                        except Exception as e:
                            print(e)
                        if r:
                            try:
                                update_sql = f"update {table_name} set is_upload = 1 where id = {item_id}"  # 推送
                                result = conn.execute(update_sql)
                                if result.rowcount != 1:
                                    print("update", item_id, False)
                                else:
                                    print("update", item_id, True)

                            except:
                                pass
                        else:
                            err_start += 1
                            print(item_id, "不执行更新操作")

                    count = itme_num
                    result = conn.execute(
                        f"select * from statistical where area_id={area_id} and push_day='{push_day}'").fetchall()
                    if result:
                        count_num = conn.execute(f"select count from statistical where area_id={area_id} and push_day='{push_day}'").fetchone()[0] + count
                        conn.execute(f"update statistical set count='{count_num}', push_time='{push_time}' where area_id={area_id}")
                    else:
                        conn.execute(
                            f"INSERT INTO statistical (area_id, count, push_time, push_day) values ('{area_id}', '{count}', '{push_time}', '{push_day}')")
                if len(results) < rows:
                    break
                else:
                    print("没有数据可执行更新操作")
                    break



    def run_post_today_all_spider_data(self, tables_list):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        thread_list = []
        for item in tables_list:
            temp_thread = threading.Thread(
                target=self.run_post,
                args=(today, item))
            thread_list.append(temp_thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        print("all done...")

    def run_post_before_today_all_spider_data(self, tables_list):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        thread_list = []
        for item in tables_list:
            temp_thread = threading.Thread(
                target=self.run_post,
                args=("2021-02-03", item, today))
            thread_list.append(temp_thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        print("all done...")

    def run_multi_thead_prepare(self, st=None, et=None):
        if not st:
            st = datetime.datetime.now()
        else:
            st = datetime.datetime.fromisoformat(st)
        if not et:
            et = datetime.datetime.now() + datetime.timedelta(days=1)
        else:
            et = datetime.datetime.fromisoformat(et)

        time_list = []
        while True:
            time_list.append(st.strftime("%Y-%m-%d %H:%M:%S"))
            next_day = st + datetime.timedelta(days=1)
            # print(next_day.strftime("%Y-%m-%d %H:%M:%S"))
            if next_day > et:
                break
            st = next_day

        thread_list = []
        for index, item in enumerate(time_list):
            temp_thread = threading.Thread(
                target=self.run_multi_thead_post,
                args=(
                    item,
                    (datetime.datetime.fromisoformat(item) + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    int(index)))
            thread_list.append(temp_thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        print("all done...")

    def run_multi_thead_post(self, s_datetime, e_datetime, i_id):
        rows = 500
        err_start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select * from {self.table_name} where is_clean = 1 and is_upload = 0 and pub_time >='{s_datetime}' "
                    f"and pub_time < '{e_datetime}' limit {err_start},{rows} ").fetchall()
                for item in results:
                    item_dict = dict(item)
                    item_id = item_dict.get("id")
                    r = False
                    try:
                        r = requests.post(url=self.post_url, data=deal_base_notices_data(item_dict, is_hump=True),
                                          timeout=10)
                        if r.status_code != 200:
                            print(i_id, r.status_code)
                            r = False
                        else:
                            r_dict = json.loads(r.text)
                            if r_dict.get("code") in [200, "200"]:
                                r = True
                            else:
                                print(i_id, r_dict.get("code"))
                                r = False
                        if not r:
                            pass
                            print(f"upload_{i_id}", item_id, r)
                        else:
                            pass
                            print(f"upload_{i_id}", item_id, r)
                    except Exception as e:
                        print(e)

                    if r:
                        try:
                            push_time = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
                            update_sql = f"update {self.table_name} set is_upload = 1,push_time = '{push_time}' where id = {item_id}"
                            result = conn.execute(update_sql)
                            if result.rowcount != 1:
                                pass
                                print(f"update_{i_id}", item_id, False)
                            else:
                                pass
                                print(f"update_{i_id}", item_id, True)
                        except:
                            pass
                    else:
                        err_start += 1
                        print(f"{i_id} {item_id}不执行更新操作")

                if len(results) < rows:
                    print(f"{i_id} done")
                    break


def test_current_is_running():
    if "Linux" in platform.platform():
        name = os.path.basename(sys.argv[0])
        cmd_str = f"ps -ef|grep {name}|grep python3|grep -v grep"
        with os.popen(cmd_str) as r:
            t = r.read().split('\n')
            if len(t) > 2:
                return True
            else:
                return False
    else:
        return False


if __name__ == "__main__":
    if test_current_is_running():
        sys.exit(0)

    # 正式推数据 解开注释需要当心！！！
    # cp = ScrapyDataPost(
    #     table_name="notices_11",
    #     # engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/data_collection?charset=utf8mb4',
    #     engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/data_collection?charset=utf8mb4',
    #     # post_url="http://192.168.1.243:30007/feign/data/v1/notice/addGatherNotice"
    #     post_url="https://data-center.zhaotx.cn/feign/data/v1/notice/addGatherNotice"
    # )
    # # cp.run_post(d_time='2018-01-01', e_time='2021-05-27')
    # cp.run_post()

    #'You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'14:02:50)\' at line 1'
    # 正式多线程推数据 解开注释需要当心！！！
    # cp.run_multi_thead_prepare(st='2019-03-01', et='2019-04-01')

    # 正式批量推数据 解开注释需要当心！！！
    # cp.run_post_today_all_spider_data(tables_list=[
    #     # "notices_00",
    #     # "notices_11",
    #     # "notices_13",
    #     # "notices_15",
    #     # "notices_02",
    #     # "notices_03",
    #     # "notices_04",
    #     # "notices_05",
    #     # "notices_08",
    #     # "notices_26",
    #     "notices_21"
    # ])
    # 正式批量推今天之前的数据 解开注释需要当心！！！
    # cp.run_post_before_today_all_spider_data(tables_list=[
        # "notices_21"
        # "notices_00",
        # "notices_11",
        # "notices_13",
        # "notices_15",
    # ])

    # 测试推数据
    cp = ScrapyDataPost(table_name="notices_146",
                        engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4',
                        post_url="http://192.168.1.243:30007/feign/data/v1/notice/addGatherNotice")
    # cp.run_post(d_time='2021-06-20', e_time='2021-07-08')
    cp.run_post()
    # # 测试多线程推数据
    # cp.run_multi_thead_prepare(st='2018-10-08', et='2018-12-31')
    # # 测试批量推数据
    # # cp.run_post_today_all_spider_data()
    # cp.run_post_before_today_all_spider_data([
    #     "notices_02",
    #     "notices_03",
    #     "notices_26",
    #     # "notices_15",
    # ])
    pass
