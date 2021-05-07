from dbutils.pooled_db import PooledDB
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pymysql
import re
import urllib
import threading

lock = threading.Lock()

db_name = 'test2_data_collection'
sheet_name = 'notices_3314'
config = {
    'host': '192.168.1.248',
    'port': 3306,
    'user': 'root',
    'password': 'Ly3sa%@D0$pJt0y6',
    'database': db_name,
    'charset': 'utf8mb4',
}

file_server = 'http://192.168.1.220:8002/sapi/webfile/addWebFileTask'


class MySQLPool(object):
    pool = PooledDB(creator=pymysql, **config)

    def __enter__(self):
        self.conn = MySQLPool.pool.connection()
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()


def pool_wrapper(func):
    def wrapper(*args, **kwargs):
        with MySQLPool() as db:
            result = func(db, *args, **kwargs)
        return result

    return wrapper


def get_url_without_domain(url):
    if 'http' in url:
        com = re.compile('http://.*?(/.*)')
        urls = com.findall(url)
        url = urls[0] if urls else url
    return urllib.parse.quote(url) if is_chinese(url) else url


def is_chinese(string):
    """
    检查整个字符串是否包含中文
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True

    return False


def request_download(db, files_path, content, id):
    """
    请求服务器下载接收相应
    修改数据库content
    """
    ret = requests.post(url=file_server, data={"jsonString": files_path})
    cur_files_path = literal_eval(files_path)
    """
    [{"name":"成交公示内容.pdf","systemUrl":"http://192.168.1.220:8002/sapi/webfile/getWebFilesBySystemUrl?systemUrl=webf
    ile/20210415/pdf/84F38E57E4E44833893F9178A87F7B0E.pdf", "code":201,"text":"重复文件任务"}]
    """
    if ret.status_code == 200:
        data = ret.json()
        with lock:
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
                                web_url_without_domain = get_url_without_domain(v)
                                web_url = v
                                # print(web_url)
                                content = content.replace(web_url, system_url).replace(
                                    web_url_without_domain, system_url
                                )
                                # print(system_url)
                # update one record
                sql_update = """
                UPDATE {db_name}.{sheet_name} SET content='{content}' WHERE id={id}
                """.format(**{
                    'db_name': db_name,
                    'sheet_name': sheet_name,
                    # 'content': re.sub("\'", "\\'", content),
                    'content': content.replace("\'", "\\'"),
                    'id': id,
                })
                # print(sql_update)
                db.cursor.execute(sql_update)
            except Exception as e:
                print(e)
                db.conn.rollback()
            else:
                db.conn.commit()
    else:
        print('request error!')
    return id


@pool_wrapper
def update_db(db, *args, **kwargs):
    fetch_sql = 'SELECT id, files_path, content FROM {db_name}.{sheet_name} WHERE is_have_file=1'.format(**{
        'db_name': db_name,
        'sheet_name': sheet_name,
    })
    db.cursor.execute(fetch_sql)

    ret = db.cursor.fetchall()[0:10]

    p = ThreadPoolExecutor()

    tasks = [p.submit(request_download, db, literal_eval(r['files_path']), r['content'], r['id']) for r in ret]

    for future in as_completed(tasks):
        if future.done():
            # print('SQL 记录ID{0}更新执行成功'.format(future.result()))
            pass


if __name__ == '__main__':
    update_db()
