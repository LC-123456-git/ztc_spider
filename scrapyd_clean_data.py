#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import platform
import datetime
import uuid
import threading
import hashlib
from sqlalchemy import create_engine, text
from spider_pro.utils import get_accurate_pub_time


def get_uuid_md5_from_data(title_name, data_time, source):
    try:
        tmp = ""
        if title_name:
            tmp += title_name
        if data_time:
            if datetime.datetime.fromisoformat(data_time).strftime('%Y-%m-%d %H:%M:%S') == "1970-01-01 00:00:00":
                pass
            else:
                tmp += datetime.datetime.fromisoformat(data_time).strftime("%a %b %d %H:%M:%S CST %Y")
        if source:
            tmp += source
        if tmp:
            return hashlib.md5(tmp.encode()).hexdigest()
        else:
            return False
    except:
        return False


# def get_true_datetime(date_time):
#     if not date_time:
#         return date_time
#     else:
#         r_list = date_time.split(" ")
#         if int(r_list[1]) < 10:
#             r_list[1] = "0{}".format(r_list[1])
#         r = "-".join()


class MyClean(object):

    def __init__(self, engine_config):
        self.engine = create_engine(engine_config)

    def run_clean_multi_thead(self, tables_list):
        thread_list = []
        for item in tables_list:
            temp_thread = threading.Thread(
                target=self.run_clean_ex_add_uuid,
                args=(item, ))
            thread_list.append(temp_thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        print("all done...")

    def run_clean_ex_add_uuid(self, table_name, is_clean_default=1):
        # area_id = table_name.strip("_")[-1]
        rows = 10000
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select id,uuid,publish_time from {table_name} limit {rows} offset {start} ").fetchall()
                for item in results:
                    try:
                        item_dict = dict(item)
                        item_id = str(item["id"])
                        uuid_field = item_dict.get("uuid", "")
                        publish_time = get_accurate_pub_time(item_dict.get("publish_time"))
                        b = publish_time.split('-')
                        for i in range(2):
                            b[1] = b[1].zfill(2)  # 左填充
                            b[2] = b[2].zfill(2)
                            publish_time = '-'.join(b)
                        # content = item_dict.get("content")
                        # #
                        # content = content.lstrip("[").rstrip("]")
                        # content = content.lstrip("\'").rstrip("\'")
                        # content = ''.join(content).replace('\\n', '').replace('\\t', '').replace('\\xa0', '').replace('\\r', '')
                        # # print(content)


                        # if uuid_field:
                        #     continue
                        # uuid_field = str(uuid.uuid4())
                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            """publish_time = :publish_time """ +
                            """where id = {} """.format(item_id))
                        # update_sql = text(
                        #     """UPDATE {} set """.format(table_name) +
                        #     """uuid = :uuid """ +
                        #     """where id = {} """.format(item_id))
                        # print(update_sql)

                        result = conn.execute(update_sql, **{"publish_time": publish_time})
                        if result.rowcount != 1:
                            print("error")
                        else:
                            # pass
                            print("true", item_id)

                    except Exception as e:
                        print(f"{e=} {item_id=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                print(start)

    def run_clean_multi_thead_for_md5(self):
        thread_list = []
        temp_thread = threading.Thread(
                target=self.run_clean_ex_add_md5,
                args=("notices_00", 3050850))
        thread_list.append(temp_thread)
        temp_thread = threading.Thread(
                target=self.run_clean_ex_add_md5,
                args=("notices_11", 37896))
        thread_list.append(temp_thread)
        temp_thread = threading.Thread(
                target=self.run_clean_ex_add_md5,
                args=("notices_13", 323576))
        thread_list.append(temp_thread)
        temp_thread = threading.Thread(
                target=self.run_clean_ex_add_md5,
                args=("notices_15", 43293))
        thread_list.append(temp_thread)

        for i in thread_list:
            i.start()

        for i in thread_list:
            i.join()

        print("all done...")

    def run_clean_ex_add_md5(self, table_name, max_id):
        rows = 500
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select id, title, pub_time, source from {table_name} where id > {start} and id <= {start+rows} and id <={max_id} order by id asc").fetchall()
                for item in results:
                    try:
                        item_dict = dict(item)
                        item_id = str(item["id"])
                        r_md5 = get_uuid_md5_from_data(
                            item_dict.get("title"), item_dict.get("pub_time").strftime('%Y-%m-%d %H:%M:%S'), item_dict.get("source"))
                        if not r_md5:
                            continue
                        else:
                            uuid_field = r_md5

                        update_sql = text(
                            """UPDATE {} set """.format(table_name) +
                            """uuid = :uuid """ +
                            """where id = {} """.format(item_id))

                        result = conn.execute(update_sql, **{"uuid": uuid_field})
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

    # 正式洗数据 解开注释需要当心！！！
    cp = MyClean(engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/data_collection?charset=utf8mb4')
    # cp.run_clean_multi_thead_for_md5()
    cp.run_clean_multi_thead(tables_list=[
        # "notices_02",
        # "notices_03",
        # "notices_26",
        "notices_15",
    ])
    # cp.run_clean_ex_add_uuid(table_name="notices_00")

    # # 测试洗数据 默认测试
    # cp = MyClean(engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@192.168.1.248:3306/test2_data_collection?charset=utf8mb4')
    # cp.run_clean_multi_thead(tables_list=[
    #     "notices_02"
    #     # "notices_00",
    #     # "notices_11",
    #     # "notices_13",
    #     # "notices_15",
    # ])
    # cp.run_clean_multi_thead_for_md5()
    # """
    # 00 3050850
    # 11 37896
    # 13 323576
    # 15 43293
    # """
    # cp.run_clean_ex_add_uuid(table_name="notices_00")

    pass
