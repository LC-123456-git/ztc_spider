# @Time : 2021/5/15 11:37 
# @Author : miaokela
# @File : pipelines_extra.py.py 
# @Description: 企查查数据存储
from sqlalchemy import create_engine, MetaData, Table, Column, Index, UniqueConstraint
from sqlalchemy.dialects import mysql
from twisted.enterprise import adbapi
from pymysql import cursors
from datetime import datetime
import re

from spider_pro import items
from spider_pro.extra_spiders.config import sql


class ExtraPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        name = crawler.spider.name
        logger = crawler.spider.logger
        return cls(name, logger, **settings)

    def __init__(self, name, logger, **kwargs):
        self.name = name
        self.logger = logger
        self.db_name = kwargs.get('MYSQL_TEST_DB_NAME', '') \
            if kwargs.get("DEBUG_MODE") else kwargs.get('MYSQL_DB_NAME', '')

        if kwargs.get("TEST_ENGINE_CONFIG") and kwargs.get("ENGINE_CONFIG"):
            self.engine = create_engine(
                kwargs.get("TEST_ENGINE_CONFIG") if kwargs.get("DEBUG_MODE") else kwargs.get("ENGINE_CONFIG"))
            self.table_name = "{table_name}_{spider_name}".format(table_name=items.QCCItem.table_name,
                                                                  spider_name=self.name)
            if not self.engine.dialect.has_table(self.engine, self.table_name):
                self.create_table()
        else:
            self.engine = None
            self.table_name = None

        self.db_params = {
            'host': kwargs.get('MYSQL_IP', ''),
            'port': kwargs.get('MYSQL_PORT', ''),
            'user': kwargs.get('MYSQL_USER_NAME', ''),
            'password': kwargs.get('MYSQL_PASSWORD', ''),
            'database': self.db_name,
            'charset': 'utf8',
            'cursorclass': cursors.DictCursor
        }
        self.db_pool = adbapi.ConnectionPool('pymysql', **self.db_params)
        # INSERT
        self.insert_sql = sql.COMPANY_INFO_INSERT.format(db_name=self.db_name, table_name=self.table_name)
        # UPDATE
        self.update_sql = sql.COMPANY_INFO_UPDATE.format(db_name=self.db_name, table_name=self.table_name)
        # FETCH
        self.fetch_sql = sql.COMPANY_FETCH_BY_NAME.format(db_name=self.db_name, table_name=self.table_name)

    def create_table(self):
        """
        建表
            检查表中是否有列字段更新 新增表列
        """
        metadata = MetaData(self.engine)
        enterprises = Table(
            self.table_name, metadata,
            Column('id', mysql.INTEGER(11), primary_key=True, nullable=False, comment="id"),
            Column('company_name', mysql.VARCHAR(512), nullable=True, comment="企业名称", unique=True),
            Column('location', mysql.VARCHAR(512), nullable=True, comment="所属地区"),
            Column('legal_representative', mysql.VARCHAR(512), nullable=True, comment="法定代表人"),
            Column('date_of_establishment', mysql.VARCHAR(512), nullable=True, comment="成立日期"),
            Column('operating_status', mysql.VARCHAR(512), nullable=True, comment="登记状态"),
            Column('registered_capital', mysql.VARCHAR(256), nullable=True, comment="注册资本"),
            Column('paid_in_capital', mysql.VARCHAR(256), nullable=True, comment="实缴资本"),
            Column('unified_social_credit_code', mysql.VARCHAR(512), nullable=True, comment="统一社会信用代码"),
            Column('business_registration_number', mysql.VARCHAR(512), nullable=True, comment="工商注册号"),
            Column('organization_code', mysql.VARCHAR(512), nullable=True, comment="组织机构代码"),
            Column('taxpayer_identification_number', mysql.VARCHAR(512), nullable=True, comment="纳税人识别号"),
            Column('taxpayer_qualification', mysql.VARCHAR(512), nullable=True, comment="纳税人资质"),
            Column('type_of_enterprise', mysql.VARCHAR(512), nullable=True, comment="企业类型"),
            Column('industry', mysql.VARCHAR(512), nullable=True, comment="行业"),
            Column('operating_period_std', mysql.VARCHAR(512), nullable=True, comment="营业期限始"),
            Column('operating_period_edt', mysql.VARCHAR(512), nullable=True, comment="营业期限末"),
            Column('staff_size', mysql.VARCHAR(512), nullable=True, comment="人员规模"),
            Column('number_of_participants', mysql.VARCHAR(256), nullable=True, comment="参保人数"),
            Column('english_name', mysql.VARCHAR(512), nullable=True, comment="英文名"),
            Column('former_name', mysql.VARCHAR(512), nullable=True, comment="曾用名"),
            Column('registration_authority', mysql.VARCHAR(512), nullable=True, comment="登记机关"),
            Column('approved_date', mysql.VARCHAR(256), nullable=True, comment="核准日期"),
            Column('registered_address', mysql.VARCHAR(512), nullable=True, comment="注册地址"),
            Column('business_scope', mysql.VARCHAR(2048), nullable=True, comment="经营范围"),
            Column('import_and_export_enterprise_code', mysql.VARCHAR(512), nullable=True, comment="进出口企业代码"),
            Column('category', mysql.VARCHAR(256), nullable=True, comment="行业分类"),
            Column('industry_category', mysql.VARCHAR(256), nullable=True, comment="行业大类"),
            Column('credit_code', mysql.VARCHAR(512), nullable=True, comment="企业税号"),
            Column('address', mysql.VARCHAR(512), nullable=True, comment="企业地址"),
            Column('phone_number', mysql.VARCHAR(512), nullable=True, comment="电话号码"),
            Column('bank', mysql.VARCHAR(512), nullable=True, comment="开户银行"),
            Column('bank_account', mysql.VARCHAR(512), nullable=True, comment="银行账户"),
            Column('create_time', mysql.DATETIME, nullable=True, comment="创建时间"),
            Column('update_time', mysql.DATETIME, nullable=True, comment="更新时间"),
            Column('origin', mysql.VARCHAR(512), nullable=True, comment="网站地址"),
        )
        Index("update_time", enterprises.c.update_time)
        metadata.create_all()
        return enterprises

    def process_item(self, item, spider):
        """
        入库
        """
        defer = self.db_pool.runInteraction(self.write_item, item)
        defer.addErrback(self.handle_error, item, spider)

    def write_item(self, cursor, item):
        # if it exists company_name, cover
        # else insert
        try:
            fetch_sql = self.fetch_sql % item['company_name']
            cursor.execute(fetch_sql)
            ret = cursor.fetchone()
        except Exception as e:
            print(e)
        else:

            com = re.compile('(.*?)关联\d+')

            legal_representatives = com.findall(item['legal_representative'])
            if legal_representatives:
                legal_representative = legal_representatives[0]
            else:
                legal_representative = item.get('legal_representative', '')

            taxpayer_qualification = item.get('taxpayer_qualification', '')
            if taxpayer_qualification in ['-', '增值税一般纳税人']:
                taxpayer_qualification = '一般纳税人'

            default_items = [
                item.get('company_name', ''),
                item.get('location'),
                legal_representative,
                item.get('date_of_establishment', ''),
                item.get('operating_status', ''),
                item.get('registered_capital', ''),
                item.get('paid_in_capital', ''),
                item.get('unified_social_credit_code', ''),
                item.get('business_registration_number', ''),
                item.get('organization_code', ''),
                item.get('taxpayer_identification_number', ''),
                taxpayer_qualification,
                item.get('type_of_enterprise', ''),
                item.get('industry', ''),
                item.get('operating_period_std', ''),
                item.get('operating_period_edt', ''),
                item.get('staff_size', ''),
                item.get('number_of_participants', ''),
                item.get('english_name', ''),
                item.get('former_name', ''),
                item.get('registration_authority', ''),
                item.get('approved_date', ''),
                item.get('registered_address', ''),
                item.get('business_scope', ''),
                item.get('import_and_export_enterprise_code', ''),
                item.get('category', ''),
                item.get('industry_category', ''),

                item.get('credit_code', ''),
                item.get('address', ''),
                item.get('phone_number', ''),
                item.get('bank', ''),
                item.get('bank_account', ''),

                item.get('origin', ''),
            ]

            if ret.get('c'):
                sql = "{0}'{1}'".format(self.update_sql, item.get('company_name', ''))
                default_items.extend(['{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now())])
                cursor.execute(sql, default_items)
            else:
                sql = self.insert_sql
                default_items.extend([
                    '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now()),
                    '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now()),
                ])
                cursor.execute(sql, default_items)
            self.logger.info('INSERT SUCCESS ({0}) SQL: {1}'.format(item.get('company_name', ''), sql))

    def handle_error(self, error, item, spider):
        self.logger.info('DB INSERT ERROR: {0}'.format(error))
