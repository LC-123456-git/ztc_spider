# @Time : 2021/5/21 14:20 
# @Author : miaokela
# @File : db.py 
# @Description: 数据库操作
import pymysql


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

    def __del__(self):
        self.con.close()

    def __init__(self, **kwargs):
        self.db_name = kwargs.get('db')
        self.con = pymysql.connect(
            host=kwargs.get('host'),
            user=kwargs.get('user'),
            password=kwargs.get('password'),
            db=self.db_name,
            charset='utf8mb4',
            port=8050,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.msg = ''

    def fetch_all(self, sql):
        ret = []
        if self.con:
            try:
                with self.con.cursor() as cursor:
                    cursor.execute(sql)
                    ret = cursor.fetchall()
            except Exception as e:
                self.msg = '数据库链接失败: {0}'.format(e)
        else:
            self.msg = '查询SQL({0})时链接断开.'.format(sql)
        return ret

    def exec_sql(self, sql):
        ret = True
        try:
            with self.con.cursor() as cursor:
                cursor.execute(sql)
            self.con.commit()
        except Exception as e:
            self.msg = '{0}执行失败: {1}'.format(sql, e)
            ret = False
        return ret

    def multi_exec_sql(self, sql, data):
        ret = True
        try:
            with self.con.cursor() as cursor:
                cursor.executemany(sql, data)
            self.con.commit()
        except Exception as e:
            self.msg = '{0}执行失败: {1}'.format(sql, e)
            ret = False
        return ret


if __name__ == '__main__':
    pass
