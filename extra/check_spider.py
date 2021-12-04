# @Time    : 2021/12/3 11:20 AM
# @Author  : miaokela
# @description: 检测出采集可能出现问题的网站: 一周没有最新数据
import pymysql
from pymysql import cursors
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


class DBQuery(object):
    """
    数据库操作
        MySQL
    """

    __instance = None

    def __new__(cls, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, **kwargs):
        self.db_name = kwargs.get('db')
        self.port = kwargs.get('port')
        self.host = kwargs.get('host')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.msg = ''
        self.dict_cursor = cursors.DictCursor

    def close(self, connection):
        try:
            connection.close()
        except (Exception,) as e:
            self.msg = 'close cause error:{}'.format(e)
            traceback.print_exc()

    def connect(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            charset='utf8mb4',
            port=self.port if self.port else 3306
        )

    def fetch_all(self, connection, sql):
        ret = []
        if connection:
            try:
                with connection.cursor(self.dict_cursor) as cursor:
                    cursor.execute(sql)
                    ret = cursor.fetchall()
            except (Exception,) as e:
                self.msg = 'fetcha_all cause error:{}'.format(e)
                traceback.print_exc()
        else:
            self.msg = 'execute SQL({0}) throws connection does not exist.'.format(sql)
        return ret

    def exec_sql(self, connection, sql):
        ret = True
        try:
            with connection.cursor(self.dict_cursor) as cursor:
                cursor.execute(sql)
            connection.commit()
        except (Exception,) as e:
            self.msg = 'exec_sql cause error:{}'.format(e)
            traceback.print_exc()
            ret = False
        return ret

    def multi_exec_sql(self, connection, sql, data):
        ret = True
        try:
            with connection.cursor(self.dict_cursor) as cursor:
                cursor.executemany(sql, data)
            connection.commit()
        except (Exception,) as e:
            self.msg = 'multi_exec_sql cause error:{}'.format(e)
            traceback.print_exc()
            ret = False
        return ret


def check_task(dbq, table_name):
    """
    当个爬虫检测任务
    """
    con = dbq.connect()
    days_before = '{:%Y-%m-%d}'.format(datetime.now() + timedelta(days=-14))
    search_sql = f"""SELECT id FROM {table_name} WHERE update_time >= '{days_before}'"""
    std_time = datetime.now()
    result = dbq.fetch_all(con, search_sql)
    dbq.close(con)
    print(f'表 {table_name} 查询执行时长: {(datetime.now() - std_time).total_seconds()}')
    if len(result) == 0:
        return table_name
    else:
        return None


def main():
    # 查看所有数据表
    db_name = 'data_collection'
    db_sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema='{db_name}'"
    db_config = {
        'host': '114.67.84.76',
        'user': 'root',
        'password': 'Ly3sa%@D0$pJt0y6',
        'db': 'data_collection',
        'port': 8050,
    }
    dbq = DBQuery(**db_config)
    con = dbq.connect()
    tables_info = dbq.fetch_all(con, db_sql)
    dbq.close(con)
    tbs = [tb['table_name'] for tb in tables_info if tb['table_name'].startswith('notices')]

    pool = ThreadPoolExecutor(max_workers=6)
    tasks = [pool.submit(check_task, dbq, tb) for tb in tbs]

    error_table = []

    for futures in as_completed(tasks):
        if futures.result():
            error_table.append(futures.result())

    print('以下爬虫两周内未采集数据', '\n', error_table)


if __name__ == '__main__':
    main()
