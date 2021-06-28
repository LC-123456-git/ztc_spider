import pymysql, logging

class BaseConn:
    def __init__(self, database=None):
        self.server = '114.67.84.76'
        self.port = 8050
        self.user = 'root'
        self.password = 'Ly3sa%@D0$pJt0y6'
        self.database = 'test2_data_collection'

    def open_connection(self):
        return pymysql.connect(host=self.server, user=self.user, password=self.password, database=self.database, port=self.port, autocommit=True)

    def execute_sql(self, sql, conn):
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        return result

    def insert_table(self, conn, item: ..., table_name: str):
        '''
        插入信息表
        '''
        try:
            # conn = self.open_connection()
            conn.set_charset('utf8mb4')
            cur = conn.cursor()
            def sql(col, placeholder, tablename):
                return """insert into {tablename} ({col}) values ({placeholder})""".format(tablename=tablename, col=col, placeholder=placeholder)
            keys = list(item.keys())
            args = tuple([item[key] for key in keys])
            select_sql = "select {} from {} WHERE {}=%s".format(keys[0], table_name, keys[0])
            result = cur.execute(select_sql, (keys[0]))
            try:
                if result == 1:
                    pass
                else:
                    cur.execute(sql(','.join(keys), ','.join(['%s '] * len(keys)), table_name), args)
                    conn.commit()
                    return '插入成功'

            except Exception as e:
                pass
            conn.close()
            cur.close()
        except Exception as e:
            logging.error(e)
            raise e


class BaseConn_mysql2:
    def __init__(self, database=None):
        self.server = '114.67.84.76'
        self.port = 8050
        self.user = 'root'
        self.password = 'Ly3sa%@D0$pJt0y6'
        self.database = 'test2_data_collection'

    def open_connection(self):
        return pymysql.connect(host=self.server, user=self.user, password=self.password, database=self.database, port=self.port, autocommit=True)

    def execute_sql(self, sql, conn):
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        return result

    def insert_table(self, conn, item: ..., table_name: str):
        '''
        插入信息表
        '''
        try:
            # conn = self.open_connection()
            conn.set_charset('utf8mb4')
            cur = conn.cursor()
            def sql(col, placeholder, tablename):
                return """insert into {tablename} ({col}) values ({placeholder})""".format(tablename=tablename, col=col, placeholder=placeholder)
            keys = list(item.keys())
            args = tuple([item[key] for key in keys])
            cur.execute(sql(','.join(keys), ','.join(['%s '] * len(keys)), table_name), args)
            cur.close()
            return '插入成功'
        except Exception as e:
            logging.error(e)
            raise e


