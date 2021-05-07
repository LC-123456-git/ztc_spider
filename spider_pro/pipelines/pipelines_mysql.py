#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/18
# @Author : wwj
# @Describe: 基础类 数据入库 MYSQL关系型数据库
import json
import uuid
import time
import pandas as pd
import requests
from sqlalchemy import create_engine, MetaData, Table, Column, Index
from sqlalchemy.dialects import mysql
from spider_pro.items import NoticesItem
from spider_pro import constans as const
from spider_pro.utils import deal_base_notices_data


class MysqlPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        name = crawler.spider.name
        area_id = crawler.spider.area_id
        logger = crawler.spider.logger
        return cls(name, area_id, logger, **settings)

    def __init__(self, name, area_id, logger, **kwargs):
        self.table_cols_map = {}
        self.buckets_map = {}
        self.name = name
        self.area_id = area_id
        self.logger = logger
        self.start = 0
        self.rows = 100
        self.upload_all_enable = True if kwargs.get("ENABLE_UPLOAD_ALL_WHEN_START") in const.TRUE_LIST else False
        self.enable = True if kwargs.get("ENABLE_AUTO_UPLOAD") in const.TRUE_LIST else False
        self.bucket_size = kwargs.get("BUCKET_SIZE", 50)
        if kwargs.get("TEST_ENGINE_CONFIG") and kwargs.get("ENGINE_CONFIG"):
            self.engine = create_engine(
                kwargs.get("TEST_ENGINE_CONFIG") if kwargs.get("DEBUG_MODE") else kwargs.get("ENGINE_CONFIG"))
            self.table_name = f"{NoticesItem.table_name}_{self.area_id}"
            self.post_url = kwargs.get("TEST_URL_DATA_CENTER") if kwargs.get("DEBUG_MODE") else kwargs.get(
                "URL_DATA_CENTER")
            if not self.engine.dialect.has_table(self.engine, self.table_name):
                self.create_table()
        else:
            self.engine = None
            self.table_name = None
            self.post_url = None

        self.upload_all_count = 0
        if self.upload_all_enable:
            self.upload_all_clean_done_and_not_upload_data()
            self.logger.info(f"本次启动上传条数: {self.upload_all_count}")

    def create_table(self):
        metadata = MetaData(self.engine)
        my_table = Table(
            self.table_name, metadata,
            # 采集自有字段
            Column('id', mysql.INTEGER(11), primary_key=True, nullable=False, comment="id"),
            Column('origin', mysql.VARCHAR(500), nullable=True, comment="原始链接"),
            Column('title_name', mysql.VARCHAR(2000), nullable=True, comment="标题"),
            Column('pub_time', mysql.DATETIME, nullable=True, comment="发布时间"),
            Column('info_source', mysql.VARCHAR(500), nullable=True, comment="来源"),
            Column('content', mysql.LONGTEXT(), nullable=True, comment="文本"),
            Column('create_time', mysql.DATETIME, nullable=True, comment="创建时间"),
            Column('update_time', mysql.DATETIME, nullable=True, comment="更新时间"),
            Column('is_have_file', mysql.INTEGER(4), nullable=True, comment="是否包含文件 "),
            Column('files_path', mysql.JSON(), nullable=True, comment="文件路径，按英文逗号,分割"),
            Column('notice_type', mysql.INTEGER(4), nullable=True,
                   comment="1#招标公告 5#招标预告 2#招标变更 3#招标异常 4#中标预告 7#中标公告 6#资格预审结果公告 8#其他公告"),
            Column('area_id', mysql.INTEGER(7), nullable=True, comment="地区ID"),
            # 采集新增字段
            Column('category', mysql.VARCHAR(255), nullable=True, comment="种类"),
            Column('business_category', mysql.VARCHAR(255), nullable=True, comment="业务种类"),
            # 弃用字段
            Column('is_storage', mysql.INTEGER(4), nullable=True, comment="弃用 是否入库 0未入库 1入库",
                   server_default="0"),

            # 清洗后字段
            Column('title', mysql.VARCHAR(2000), nullable=True, comment="公告标题"),
            Column('project_number', mysql.VARCHAR(300), nullable=True, comment="项目编号"),
            Column('project_name', mysql.VARCHAR(300), nullable=True, comment="项目名称"),
            Column('tenderee', mysql.VARCHAR(300), nullable=True, comment="招标人"),
            Column('bidding_agency', mysql.VARCHAR(255), nullable=True, comment="招标代理"),

            Column('area_code', mysql.VARCHAR(255), nullable=True, comment="区县编号"),
            Column('area', mysql.VARCHAR(255), nullable=True, comment="地区"),
            Column('address', mysql.VARCHAR(500), nullable=True, comment="详细地址"),
            Column('email', mysql.VARCHAR(255), nullable=True, comment="电子邮箱"),
            Column('description', mysql.TEXT, nullable=True, comment="招标方案说明"),

            Column('bid_type', mysql.VARCHAR(255), nullable=True, comment="招标方式"),
            Column('bid_modus', mysql.VARCHAR(255), nullable=True, comment="招标组织形式"),
            Column('inspect_dept', mysql.VARCHAR(255), nullable=True, comment="监督部门"),
            Column('review_dept', mysql.VARCHAR(255), nullable=True, comment="审核部门"),
            Column('notice_nature', mysql.VARCHAR(255), nullable=True, comment="公告性质"),

            Column('bid_file', mysql.VARCHAR(500), nullable=True, comment="招标文件"),
            Column('bid_file_start_time', mysql.VARCHAR(100), nullable=True, comment="招标文件获取开始时间"),
            Column('bid_file_end_time', mysql.VARCHAR(100), nullable=True, comment="招标文件获取截止时间"),
            Column('apply_end_time', mysql.VARCHAR(100), nullable=True, comment="报名截止时间"),
            Column('notice_start_time', mysql.VARCHAR(100), nullable=True, comment="公告开始时间"),

            Column('notice_end_time', mysql.VARCHAR(100), nullable=True, comment="公告结束时间"),
            Column('aberrant_type', mysql.VARCHAR(100), nullable=True, comment="异常类型"),
            Column('budget_amount', mysql.VARCHAR(255), nullable=True, comment="预算金额"),
            Column('tenderopen_time', mysql.VARCHAR(255), nullable=True, comment="开标时间"),

            Column('publish_time', mysql.VARCHAR(255), nullable=True, comment="发布时间"),
            Column('liaison', mysql.VARCHAR(300), nullable=True, comment="联系人"),
            Column('contact_information', mysql.VARCHAR(255), nullable=True, comment="联系方式"),
            Column('content', mysql.LONGTEXT, nullable=True, comment="公告内容"),
            Column('classify_id', mysql.VARCHAR(255), nullable=True, comment="公告分类id"),

            Column('classify_name', mysql.VARCHAR(255), nullable=True, comment="公告分类名称"),
            Column('project_type', mysql.VARCHAR(255), nullable=True, comment="项目类型"),
            Column('state', mysql.VARCHAR(1), nullable=True, comment="状态0-待发布1-已发布2-已下架3-待审核4-审核拒绝",
                   server_default="0"),
            Column('file_ids', mysql.VARCHAR(100), nullable=True, comment="附件ids"),
            Column('company_type', mysql.VARCHAR(100), nullable=True, comment="单位类型"),

            Column('successful_bidder', mysql.VARCHAR(255), nullable=True, comment="中标方"),
            Column('bid_amount', mysql.VARCHAR(255), nullable=True, comment="中标金额"),
            Column('sign_type', mysql.VARCHAR(1), nullable=True, comment="标讯类型 0-平台发布1-用户发布2-采集发布",
                   server_default="2"),
            Column('source', mysql.VARCHAR(500), nullable=True, comment="来源(采集的公告就填写采集网站、用户和平台发布就用用户名)"),
            Column('source_url', mysql.VARCHAR(500), nullable=True, comment="采集发布来源网站URL"),

            # 标记字段
            Column('is_upload', mysql.INTEGER(4), nullable=True, comment="是否上传 0未上传 1上传",
                   server_default="0"),
            Column('is_clean', mysql.INTEGER(4), nullable=True, comment="是否清洗, 0未清洗 1已清洗",
                   server_default="0"),

            # uuid
            Column('uuid', mysql.VARCHAR(40), nullable=True, comment="UUID"),
        )
        # 索引
        Index("index_push", my_table.c.pub_time, my_table.c.is_upload, my_table.c.is_clean)
        Index("update_time", my_table.c.update_time)
        metadata.create_all()

    def upload_all_clean_done_and_not_upload_data(self):
        rows = 100
        start = 0
        with self.engine.connect() as conn:
            while True:
                results = conn.execute(
                    f"select * from {self.table_name} where is_upload = {const.TYPE_UPLOAD_NOT_DONE} and is_clean = {const.TYPE_CLEAN_DONE} limit {rows} offset {start} ").fetchall()
                for item in results:
                    item_dict = dict(item)
                    item_id = item_dict.get("id")
                    result, reason = self.post_data_to_center(deal_base_notices_data(item_dict, is_hump=True))
                    if result:
                        try:
                            update_sql = f"update {self.table_name} set is_upload = {const.TYPE_UPLOAD_DONE} where id = {item_id}"
                            result_sql = conn.execute(update_sql)
                            if result_sql.rowcount == 1:
                                self.upload_all_count += 1
                            else:
                                self.logger.error(f"启动上传单条失败 更新is_upload失败 {item_id=}")
                        except Exception as e:
                            self.logger.error(f"启动上传单条失败 {e=}")
                    else:
                        self.logger.error(f"启动上传单条失败：{reason=}")

                if len(results) < rows:
                    break
                else:
                    start += rows
                self.logger.info(f"本次启动上传已上传条数: {start}")

    def process_item(self, item, spider):
        """
        :param item:
        :param spider:
        :return: 数据分表入库
        """
        if isinstance(item, NoticesItem):
            if self.table_name in self.buckets_map:
                self.buckets_map[self.table_name].append(item)
            else:
                cols, col_default = [], {}
                col_type = {
                    # 采集字段
                    'origin': mysql.VARCHAR(500),
                    'title_name': mysql.VARCHAR(2000),
                    'pub_time': mysql.DATETIME,
                    'info_source': mysql.VARCHAR(500),
                    'content': mysql.LONGTEXT(),  # 和清洗字段共有
                    'create_time': mysql.DATETIME,
                    'update_time': mysql.DATETIME,
                    'is_have_file': mysql.INTEGER(4),
                    'files_path': mysql.JSON(),
                    'notice_type': mysql.INTEGER(4),
                    'area_id': mysql.INTEGER(7),
                    'category': mysql.VARCHAR(),
                    'business_category': mysql.VARCHAR(),

                    # 弃用字段
                    'is_storage': mysql.INTEGER(4),

                    # 清洗字段
                    'title': mysql.VARCHAR(),
                    'project_number': mysql.VARCHAR(),
                    'project_name': mysql.VARCHAR(),
                    'tenderee': mysql.VARCHAR(),
                    'bidding_agency': mysql.VARCHAR(),
                    'area_code': mysql.VARCHAR(),
                    'area': mysql.VARCHAR(),
                    'address': mysql.VARCHAR(),
                    'email': mysql.VARCHAR(),
                    'description': mysql.VARCHAR(),
                    'bid_type': mysql.VARCHAR(),
                    'bid_modus': mysql.VARCHAR(),
                    'inspect_dept': mysql.VARCHAR(),
                    'review_dept': mysql.VARCHAR(),
                    'notice_nature': mysql.VARCHAR(),
                    'bid_file': mysql.VARCHAR(),
                    'bid_file_start_time': mysql.VARCHAR(),
                    'bid_file_end_time': mysql.VARCHAR(),
                    'apply_end_time': mysql.VARCHAR(),
                    'notice_start_time': mysql.VARCHAR(),
                    'notice_end_time': mysql.VARCHAR(),
                    'aberrant_type': mysql.VARCHAR(),
                    'budget_amount': mysql.VARCHAR(),
                    'tenderopen_time': mysql.VARCHAR(),
                    'publish_time': mysql.DATETIME(),
                    'liaison': mysql.VARCHAR(),
                    'contact_information': mysql.VARCHAR(),
                    'classify_id': mysql.VARCHAR(),
                    'classify_name': mysql.VARCHAR(),
                    'project_type': mysql.VARCHAR(),
                    'state': mysql.VARCHAR(),
                    'file_ids': mysql.VARCHAR(),
                    'company_type': mysql.VARCHAR(),
                    'successful_bidder': mysql.VARCHAR(),
                    'bid_amount': mysql.VARCHAR(),
                    'sign_type': mysql.VARCHAR(),
                    'source': mysql.VARCHAR(),
                    'source_url': mysql.VARCHAR(),

                    # 标记字段
                    'is_upload': mysql.INTEGER(),
                    'is_clean': mysql.INTEGER(),

                    # uuid
                    'uuid': mysql.VARCHAR(),
                }
                for field, value in item.fields.items():
                    cols.append(field)
                    col_default[field] = item.fields[field].get("default", "")
                cols.sort(key=lambda x: item.fields[x].get('idx', 1))
                self.table_cols_map.setdefault(self.table_name, (cols, col_default, col_type))  # 定义表结构、字段顺序、默认值
                self.buckets_map.setdefault(self.table_name, [item])
            self.buckets2db()  # 将满足条件的桶 入库
        return item

    def close_spider(self, spider):
        """
        :param spider:
        :return:  爬虫结束时，将桶里面剩下的数据 入库
        """
        self.buckets2db(1)
        self.engine.dispose()

    def buckets2db(self, bucket_size=None):
        """
        :param bucket_size:  桶大小
        :return: 遍历每个桶，将满足条件的桶，入库并清空桶
        """
        if bucket_size is None:
            bucket_size = self.bucket_size
        for table_name, items in self.buckets_map.items():  # 遍历每个桶，将满足条件的桶，入库并清空桶
            if len(items) >= bucket_size:
                new_items = []
                cols, col_default, col_type = self.table_cols_map.get(table_name)
                for item in items:
                    new_item = {}
                    for field in cols:
                        value = item.get(field, col_default.get(field))
                        new_item[field] = str(value)
                    local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    new_item["create_time"] = local_time
                    new_item["update_time"] = local_time
                    new_item["is_storage"] = "0"  # 已经弃用
                    if new_item["pub_time"] in const.EMPTY_LIST:
                        new_item["pub_time"] = const.DEFAULT_PUB_TIME
                    new_item["uuid"] = str(uuid.uuid4())
                    # 启用推送
                    if self.enable and new_item["is_clean"] == const.TYPE_CLEAN_DONE:
                        result, reason = self.post_data_to_center(deal_base_notices_data(dict(new_item), is_hump=True))
                        if result:
                            new_item["is_upload"] = const.TYPE_UPLOAD_DONE
                        else:
                            new_item["is_upload"] = const.TYPE_UPLOAD_NOT_DONE
                            self.logger.info(f"推送失败: {reason=}")
                    else:
                        new_item["is_upload"] = const.TYPE_UPLOAD_NOT_DONE
                    new_items.append(new_item)

                try:
                    with self.engine.connect() as conn:
                        df = pd.DataFrame(new_items)
                        df.to_sql(table_name, con=conn, index=False, if_exists='append', dtype=col_type)
                        self.logger.info(f"入库成功 <= 表名:{table_name} 记录数:{len(items)}")
                except Exception as e:
                    self.logger.warning(f"重新入库 <= 表名:{table_name} 当前批次入库异常, 自动切换成逐行入库...")
                    for new_item in new_items:
                        try:
                            with self.engine.connect() as conn_single:
                                df = pd.DataFrame([new_item])
                                df.to_sql(table_name, con=conn_single, index=False, if_exists='append', dtype=col_type)
                                self.logger.info(f"入库成功 <= 表名:{table_name} 记录数:1")
                        except Exception as e:
                            self.logger.error(f"丢弃 <= 表名:{table_name} 丢弃原因:{e} ")
                finally:
                    items.clear()  # 清空桶

    def post_data_to_center(self, data):
        try:
            r = requests.post(url=self.post_url, data=data, timeout=5)
            if r.status_code != 200:
                return False, f"{r.status_code=}"
            else:
                r_dict = json.loads(r.text)
                if r_dict.get("code") in [200, "200"]:
                    return True, ""
                else:
                    return False, f"{r_dict.get('code')=} {r_dict.get('message')=}"
        except Exception as e:
            return False, str(e)

    def run_post(self, table_name, post_url, engine_config):
        self.engine = create_engine(engine_config)
        rows = 100
        start = 0
        with self.engine.connect() as conn:
            while True:
                # results = conn.execute(
                #     f"select * from {table_name} where is_upload = 0 and is_clean = 1 limit {rows} offset {start} ").fetchall()
                # results = conn.execute(
                #     f"select * from {table_name} where id = 275 ").fetchall()
                results = conn.execute(
                    f"select * from {table_name}  limit {rows} offset {start} ").fetchall()
                for item in results:
                    item_dict = dict(item)
                    item_id = item_dict.get("id")
                    r = False
                    try:
                        r = requests.post(url=post_url, data=deal_base_notices_data(item_dict, is_hump=True),
                                          timeout=10)
                        if r.status_code != 200:
                            print(r.status_code)
                            r = False
                        else:
                            r_dict = json.loads(r.text)
                            if r_dict.get("code") in [200, "200"]:
                                r = True
                            else:
                                print(r_dict.get("code"))
                                r = False
                        if not r:
                            print("upload", item_id, r)
                        else:
                            pass
                            # print("upload", item_id, r)
                    except Exception as e:
                        print(e)

                    if r:
                        update_sql = f"update {table_name} set is_upload = 1 where id = {item_id}"
                        result = conn.execute(update_sql)
                        if result.rowcount != 1:
                            print("update", item_id, False)
                        else:
                            print("update", item_id, True)
                    else:
                        print("不执行更新操作")

                if len(results) < rows:
                    break
                else:
                    start += rows


if __name__ == "__main__":
    # cp = MysqlPipeline("1", "1", "1", **{})
    #
    # # 测试推数据
    # cp.run_post(table_name="notices_00",
    #             engine_config='mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4',
    #             post_url="http://192.168.1.249:9081/feign/data/v1/notice/addGatherNotice")

    engine_config = 'mysql+pymysql://root:Ly3sa%@D0$pJt0y6@114.67.84.76:8050/test2_data_collection?charset=utf8mb4'
    engine = create_engine(engine_config)
    try:
        with engine.begin() as conn:
            s = conn.execute("insert into area (area, url) values ('dwdqwd', 'dwdqwd')")
            print(s.lastrowid)
            # print(123/0)
    except Exception as e:
        print(e)
        pass
