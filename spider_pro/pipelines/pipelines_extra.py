# @Time : 2021/5/15 11:37 
# @Author : miaokela
# @File : pipelines_extra.py.py 
# @Description: 企查查数据存储
from sqlalchemy import create_engine, MetaData, Table, Column, Index, UniqueConstraint
from sqlalchemy.dialects import mysql
from twisted.enterprise import adbapi
from pymysql import cursors

from spider_pro import items


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
        self.db_name = kwargs.get('MYSQL_TEST_DB_NAME', '') if kwargs.get("DEBUG_MODE") else kwargs.get('MYSQL_DB_NAME', '')

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
        # insert
        self.insert_sql = """INSERT INTO {db_name}.{table_name} 
        (QYMC,SSDQ,FDDBR,CLRQ,DJZT,ZCZB,SJZB,TYSHXYDM,GSZCH,ZZJGDM,NSRSBH,NSRZZ,QYLX,HY,YYQXS,YYQXM,RYGM,CBRY,YWM,CYM,DJJG,HZRQ,ZCDZ,JYFW,JCKQYDM,QYFL,HYDL) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """.format(db_name=self.db_name, table_name=self.table_name)
        # update
        self.update_sql = """UPDATE {db_name}.{table_name} SET
        QYMC=%s,SSDQ=%s,FDDBR=%s,CLRQ=%s,DJZT=%s,ZCZB=%s,SJZB=%s,TYSHXYDM=%s,GSZCH=%s,ZZJGDM=%s,NSRSBH=%s,NSRZZ=%s,QYLX=%s,
        HY=%s,YYQXS=%s,YYQXM=%s,RYGM=%s,CBRY=%s,YWM=%s,CYM=%s,DJJG=%s,HZRQ=%s,ZCDZ=%s,JYFW=%s,JCKQYDM=%s,QYFL=%s,HYDL=%s
        WHERE QYMC=""".format(db_name=self.db_name, table_name=self.table_name)
        # fetch
        self.fetch_sql = """SELECT COUNT(QYMC) c FROM {db_name}.{table_name} WHERE QYMC='%s'
        """.format(db_name=self.db_name, table_name=self.table_name)

    def create_table(self):
        """
        建表
        """
        metadata = MetaData(self.engine)
        my_table = Table(
            self.table_name, metadata,
            Column('id', mysql.INTEGER(11), primary_key=True, nullable=False, comment="id"),
            Column('QYMC', mysql.VARCHAR(512), nullable=True, comment="企业名称", unique=True),
            Column('SSDQ', mysql.VARCHAR(512), nullable=True, comment="所属地区"),
            Column('FDDBR', mysql.VARCHAR(512), nullable=True, comment="法定代表人"),
            Column('CLRQ', mysql.VARCHAR(512), nullable=True, comment="成立日期"),
            Column('DJZT', mysql.VARCHAR(512), nullable=True, comment="登记状态"),
            Column('ZCZB', mysql.VARCHAR(256), nullable=True, comment="注册资本"),
            Column('SJZB', mysql.VARCHAR(256), nullable=True, comment="实缴资本"),
            Column('TYSHXYDM', mysql.VARCHAR(512), nullable=True, comment="统一社会信用代码"),
            Column('GSZCH', mysql.VARCHAR(512), nullable=True, comment="工商注册号"),
            Column('ZZJGDM', mysql.VARCHAR(512), nullable=True, comment="组织机构代码"),
            Column('NSRSBH', mysql.VARCHAR(512), nullable=True, comment="纳税人识别号"),
            Column('NSRZZ', mysql.VARCHAR(512), nullable=True, comment="纳税人资质"),
            Column('QYLX', mysql.VARCHAR(512), nullable=True, comment="企业类型"),
            Column('HY', mysql.VARCHAR(512), nullable=True, comment="行业"),
            Column('YYQXS', mysql.VARCHAR(512), nullable=True, comment="营业期限始"),
            Column('YYQXM', mysql.VARCHAR(512), nullable=True, comment="营业期限末"),
            Column('RYGM', mysql.VARCHAR(512), nullable=True, comment="人员规模"),
            Column('CBRY', mysql.VARCHAR(256), nullable=True, comment="参保人数"),
            Column('YWM', mysql.VARCHAR(512), nullable=True, comment="英文名"),
            Column('CYM', mysql.VARCHAR(512), nullable=True, comment="曾用名"),
            Column('DJJG', mysql.VARCHAR(512), nullable=True, comment="登记机关"),
            Column('HZRQ', mysql.VARCHAR(256), nullable=True, comment="核准日期"),
            Column('ZCDZ', mysql.VARCHAR(512), nullable=True, comment="注册地址"),
            Column('JYFW', mysql.VARCHAR(2048), nullable=True, comment="经营范围"),
            Column('JCKQYDM', mysql.VARCHAR(512), nullable=True, comment="进出口企业代码"),
            Column('QYFL', mysql.VARCHAR(256), nullable=True, comment="行业分类"),
            Column('HYDL', mysql.VARCHAR(256), nullable=True, comment="行业大类"),
        )
        metadata.create_all()

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
            if ret.get('c'):
                sql = "{0}'{1}'".format(self.update_sql, item['company_name'])
            else:
                sql = self.insert_sql
            cursor.execute(sql, (
                item['company_name'],
                item['location'],
                item['legal_representative'],
                item['date_of_establishment'],
                item['operating_status'],
                item['registered_capital'],
                item['paid_in_capital'],
                item['unified_social_credit_code'],
                item['business_registration_number'],
                item['organization_code'],
                item['taxpayer_identification_number'],
                item['taxpayer_qualification'],
                item['type_of_enterprise'],
                item['industry'],
                item['operating_period_std'],
                item['operating_period_edt'],
                item['staff_size'],
                item['number_of_participants'],
                item['english_name'],
                item['former_name'],
                item['registration_authority'],
                item['approved_date'],
                item['registered_address'],
                item['business_scope'],
                item['import_and_export_enterprise_code'],
                item['category'],
                item['industry_category'],
            ))

    def handle_error(self, error, item, spider):
        self.logger.info('DB INSERT ERROR: {0}'.format(error))
