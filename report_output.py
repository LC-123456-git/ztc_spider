# author: miaokela
# Date: 2021-04-16 13:01:08
# LastEditTime: 2021-04-16 13:02:24
# Description: 每日采集数量、推送数量统计/指定时间段的采集数量、推送数量 以excel的形式输出
import re
import pymysql
import xlwt
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


class DBQuery(object):
    """
    数据库操作
        MySQL
    """

    __instance = None

    area_map = {
        '0': '全国公共资源交易平台',
        '2': '北京市公共资源交易服务平台',
        '3': '天津市公共资源交易网',
        '4': '河北省公共资源交易平台',
        '5': '山西省公共资源交易平台',
        '6': '内蒙古公共资源交易平台',
        '8': '吉林公共资源交易平台',
        '10': '黑龙江公共资源交易平台',
        '11': '上海市公共资源交易服务平台',
        '13': '江苏省公共资源交易服务平台',
        '14': '浙江省公共资源交易服务平台1',
        '15': '浙江省公共资源交易服务平台2',
        '16': '安徽省公共资源交易服务平台',
        '18': '福建省公共资源交易服务平台',
        '19': '江西省公共资源交易服务平台',
        '21': '山东省公共资源交易服务平台',
        '23': '河南省公共资源交易服务平台',
        '26': '湖北省公共资源交易服务平台',
        '28': '湖南省公共资源交易服务平台',
        '30': '广东省公共资源交易服务平台',
        '33': '广西省公共资源交易服务平台',
        '36': '甘肃省公共资源交易服务平台',
        '39': '重庆省公共资源交易服务平台',
        '40': '四川省公共资源交易服务平台',
        '41': '贵州省公共资源交易服务平台',
        '42': '云南省公共资源交易服务平台',
        '44': '西藏自治区公共资源交易服务平台',
        '45': '陕西省公共资源交易服务平台',
        '47': '青海省公共资源交易服务平台',
        '49': '宁夏回族自治区公共资源交易服务平台',
        '50': '新疆维吾尔族自治区公共资源交易服务平台',
        '51': '新疆生产建设兵团公共资源交易服务平台',
        '52': '嗨招电子招标采购平台',
        '53': '必联网',
        '55': '天工开物',
        '71': '招财进宝',
        '3301': '杭州市公共资源交易平台',
        '3305': '宁波公共资源交易平台',
        '3306': '嘉兴公共资源交易平台',
        '3307': '湖州公共资源交易平台',
        '3308': '衢州公共资源交易平台',
        '3309': '温州公共资源交易平台',
        '3310': '台州公共资源交易平台',
        '3311': '丽水公共资源交易平台',
        '3312': '绍兴公共资源交易平台',
        '3313': '舟山公共资源交易平台',
        '3314': '余杭公共资源交易平台',
        '3315': '柯桥公共资源交易平台',
        '3319': '长兴公共资源交易平台',
        '3303': '浙能集团',
        '3304': '水利厅',
    }

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


class ReportOutput(DBQuery):
    """
    采集信息输出
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_type = kwargs.get('output_type', 'json')  # 默认以json的形式输出
        self.sdt = kwargs.get('sdt')
        self.edt = kwargs.get('edt')
        self.tb_sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='{db_name}'".format(
            db_name=kwargs.get('db', '')
        )
        self.area_sql = "SELECT area_id FROM {db_name}.%s LIMIT 1".format(
            db_name=kwargs.get('db', ''),
        )
        self.pool = ThreadPoolExecutor()
        self.data_list = []

    def get_statistic_data(self, date, table_with_area):
        table_name = table_with_area['table_name']
        area_id = table_with_area['area_id']
        result = []

        if area_id not in [14]:
            today = date
            tomorrow = '{0:%Y-%m-%d}'.format(datetime.strptime(today, '%Y-%m-%d') + timedelta(days=1))
            download_sql = """SELECT area_id n, COUNT(id) c FROM {db_name}.{table_name}
            WHERE update_time BETWEEN '{today}' AND '{tomorrow}'
            GROUP BY area_id;""".format(**{
                'today': today,
                'tomorrow': tomorrow,
                'table_name': table_name,
                'db_name': self.db_name,
            })
            push_sql = """SELECT area_id n, count FROM {db_name}.statistical
            WHERE push_time='{cdt}' AND area_id={area_id}
            """.format(**{
                'db_name': self.db_name,
                'area_id': area_id,
                'cdt': date,
            })
            print(download_sql + '\n')
            print(push_sql + '\n')
            download_data = self.fetch_all(download_sql)  # [(area_id, n),]
            push_data = self.fetch_all(push_sql)

            if all([download_data, push_data]):
                result.append([date, download_data[0][0], download_data[0][1], push_data[0][1]])
            if download_data and not push_data:
                result.append([date, download_data[0][0], download_data[0][1], 0])
            if not download_data and push_data:
                result.append([date, push_data[0][0], 0, push_data[0][1]])
            if not any([download_data, push_data]):
                result.append([date, area_id, 0, 0])
        return [[x[0], self.area_map.get(str(x[1]), x[1]), x[2], x[3]] for x in result]

    @property
    def table_with_area_id(self):
        """
        表名对应的area_id
        Returns:

        """
        ta = []
        tables = [n[0] for n in self.fetch_all(self.tb_sql) if n and n[0].startswith('notices')]
        for t in tables:
            area_ids = self.fetch_all(self.area_sql % t)
            if area_ids:
                ta.append({
                    'table_name': t,
                    'area_id': area_ids[0][0]
                })
        return ta

    @staticmethod
    def get_date_list(sdt, edt):
        date_list = []
        if sdt == edt:
            date_list = ['{0:%Y-%m-%d}'.format(sdt)]
        if edt > sdt:
            days = (edt - sdt).days
            for i in range(0, days + 1):
                date_list.append('{0:%Y-%m-%d}'.format(sdt))
                sdt += timedelta(days=1)
        return date_list

    def output(self, **kwargs):
        tts = ['日期', '网站名称', '采集数量', '推送数量', '发布数量', '待发布数量']
        sdt = kwargs.get('sdt')
        edt = kwargs.get('edt')

        try:
            sdt = datetime.strptime(sdt, '%Y-%m-%d')
            edt = datetime.strptime(edt, '%Y-%m-%d')
        except ValueError:
            pass
        else:
            # datetime list
            date_list = ReportOutput.get_date_list(sdt, edt)

            # get all notices table_name
            table_with_areas = self.table_with_area_id

            # DATA
            data_list = []
            for date in date_list:
                for table_with_area in table_with_areas:
                    result = self.get_statistic_data(date, table_with_area)
                    data_list.extend(result)

            # EXCEL
            try:
                ReportOutput.to_excel(tts, data_list, date_list)
            except Exception as e:
                print(e)
                self.msg = e

    @staticmethod
    def to_excel(tts, data_list, date_list):
        """
        输出excel报表
        params:
            @tts: 表头列表
            @data_list: 表体数据
            @date_list: 合并时间
        """
        ex = xlwt.Workbook(encoding='ascii')
        ex_sh = ex.add_sheet('sheet01')

        borders = xlwt.Borders()  # Create borders

        borders.left = xlwt.Borders.MEDIUM
        borders.right = xlwt.Borders.MEDIUM
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.MEDIUM

        font = xlwt.Font()
        font.bold = True

        al = xlwt.Alignment()
        al.horz = 0x02  # 设置水平居中
        al.vert = 0x01  # 设置垂直居中

        style = xlwt.XFStyle()  # Create style
        style.borders = borders  # Add borders to style
        style.alignment = al
        style.font = font

        for n, tt in enumerate(tts):
            ex_sh.write(0, n, tt, style)
        # @result: [
        #     ['2021-04-16','医疗采购', 575， 1],
        #     ['2021-04-16','工程建设', 138， 2],
        #     ['2021-04-17','测试1', 157，0],
        #     ['2021-04-17','测试2', 3，0],
        # ]

        download_sum = 0
        push_sum = 0
        for n, dl in enumerate(data_list):
            # ex_sh.write(n + 1, 0, dl[0])
            ex_sh.write(n + 1, 1, dl[1])
            ex_sh.write(n + 1, 2, dl[2])
            ex_sh.write(n + 1, 3, dl[3])
            download_sum += dl[2]
            push_sum += dl[3]

        # 合计
        ex_sh.write(len(data_list) + 1, 0, '合计', style=style)
        ex_sh.write(len(data_list) + 1, 1, '')
        ex_sh.write(len(data_list) + 1, 2, download_sum)
        ex_sh.write(len(data_list) + 1, 3, push_sum)

        # date 统计 合并
        date_merge = []

        pre_date = ''
        n = 0
        for date in date_list:
            data_exists = False
            for dl in data_list:
                if date == dl[0]:
                    n += 1
                    data_exists = True
            if data_exists:
                date_merge.append({
                    'date': date,
                    'n': n
                })

            if date != pre_date:
                n = 0

            pre_date = date

        upper_n = 0
        lower_n = 1
        for dm in date_merge:
            upper_n += dm['n']
            ex_sh.write_merge(lower_n, upper_n, 0, 0, dm['date'], style=style)
            lower_n += dm['n']

        ex.save('统计{0:%Y-%m-%d}.xls'.format(datetime.now()))

    @staticmethod
    def if_contains_match(name, data_set):
        status = False
        n = 0
        for ds in data_set:
            if name == ds[0]:
                status = True
                n = ds[1]
                break
        return status, n


if __name__ == '__main__':
    data = {
        'host': '114.67.84.76',
        'user': 'root',
        'password': 'Ly3sa%@D0$pJt0y6',
        # 'db': 'test2_data_collection',
        'db': 'data_collection',
        'output_type': 'json',
    }
    #
    rpt = ReportOutput(**data)
    rpt.output(sdt='2021-04-01', edt='2021-04-28')
