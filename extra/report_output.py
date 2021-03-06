"""
author: miaokela
Date: 2021-04-16 13:01:08
LastEditTime: 2021-05-01 14:29:31
Description: 每日采集数量、推送数量统计/指定时间段的采集数量、推送数量 以excel的形式输出
"""
import pymysql
import re
import gevent
import os

from datetime import datetime, timedelta
from openpyxl import Workbook, styles
from openpyxl.styles import Border, Side


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
            port=8050
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
    area_map = {
        '00': '全国公共资源交易平台',
        '01': '中国招标投标公共服务平台',
        '02': '北京市公共资源交易服务平台',
        '03': '天津市公共资源交易网',
        '04': '河北省公共资源交易平台',
        '05': '山西省公共资源交易平台',
        '06': '内蒙古公共资源交易平台',  # ×
        '07': '辽宁省公共资源交易平台',  # ×
        '08': '吉林公共资源交易平台',
        '10': '黑龙江公共资源交易平台',
        '11': '上海市公共资源交易服务平台',
        '12': '上海建设工程交易服务中心',  # ×
        '13': '江苏省公共资源交易服务平台',
        '14': '浙江省公共资源交易服务平台1',
        '15': '浙江省公共资源交易服务平台2',
        '16': '安徽省公共资源交易服务平台',
        '17': '福建省公共资源交易电子公共服务平台',  # ×
        '18': '福建省公共资源交易服务平台',
        '19': '江西省公共资源交易服务平台',
        '20': '江西省公共资源交易服务平台',    # ×
        '21': '山东省公共资源交易服务平台',
        '22': '山东省公共资源交易中心',  # ×
        '23': '河南省公共资源交易服务平台',
        '24': '河南省公共资源交易中心门户网',  # ×
        '25': '招投标信息_河南省水利厅',  # ×
        '26': '湖北省公共资源交易服务平台',
        '27': '湖北省公共资源电子交易服务系统',  # ×
        '28': '湖南省公共资源交易服务平台',
        '30': '广东公共资源交易平台',
        '33': '广西省公共资源交易服务平台',
        '36': '甘肃省公共资源交易服务平台',
        '39': '重庆省公共资源交易服务平台',
        '41': '贵州省公共资源交易服务平台',
        '42': '云南省公共资源交易服务平台',  # ×
        '44': '西藏自治区公共资源交易服务平台',
        '45': '陕西省公共资源交易服务平台',
        '47': '青海省公共资源交易服务平台',  # ×
        '49': '宁夏回族自治区公共资源交易网',
        '50': '新疆维吾尔族自治区公共资源交易服务平台',
        '51': '新疆生产建设兵团公共资源交易服务平台',  # ×
        '52': '嗨招电子招标采购平台',
        '53': '必联网',
        '55': '天工开物',
        '56': '河北建投集团电子招投标交易平台',
        '54': 'E共享交易平台',
        '57': '精彩纵横',
        '59': '鑫智链交易平台',
        '62': '新点电子交易平台',
        '65': '国e平台',
        '67': '阳光易招',
        '68': '齐鲁招采网',
        '71': '招财进宝',
        '78': '住宅修缮工程招投标',
        '76': 'e招冀成',
        '77': '招必得',
        '79': '信e采招标采购电子交易平台',
        '80': '兖矿集团电子招投标采购平台',
        '82': '比德电子采购平台',
        '83': '旺采网',
        '85': '安装信息网',
        '114': '广咨电子招投标交易平台',
        '117': '中国河北政府采购网',
        '118': '中国河南政府采购网',
        '119': '湖北省政府采购网',
        '120': '湖南省政府采购网',
        '121': '山西省政府采购网',
        '122': '山东省政府采购网',
        '123': '黑龙江省政府采购网',
        '124': '吉林省政府采购网',

        '126': '海南省政府采购网',
        '127': '内蒙古政府采购网',
        '128': '广东省政府采购网',
        '129': '湖北省政府采购网',
        '130': '甘肃省政府采购网',
        '131': '青海省政府采购网',
        '132': '宁夏回族自治区政府采购网',
        '133': '江西省政府采购网',
        '141': '安徽省政府采购网',
        '143': '大连政府采购网',
        '145': '青岛省政府采购网',
        '146': '兵团政府采购网',
        '148': '中国通用招标网',
        '149': '中招联合招标采购网',
        '150': '冀招标全流程电子交易平台',
        '151': '中钢招标有限责任公司',
        '152': '中煤易购',

        '3101': '上海市政府采购网',
        '3301': '杭州市公共资源交易平台',
        '3302': '浙江政府采购网',
        '3303': '浙能集团电子招标投标交易平台',
        '3304': '浙江省水利厅',
        '3305': '宁波公共资源交易平台',
        '3306': '嘉兴公共资源交易平台',
        '3307': '湖州公共资源交易平台',
        '3308': '衢州公共资源交易平台',  # ×
        '3309': '温州公共资源交易平台',
        '3310': '台州公共资源交易平台',  # ×
        '3311': '丽水公共资源交易平台',
        '3312': '绍兴公共资源交易平台',
        '3313': '舟山公共资源交易平台',
        '3314': '余杭公共资源交易平台',
        '3315': '柯桥公共资源交易平台',
        '3316': '诸暨市公共资源交易服务平台',
        '3318': '金华市公共资源交易中心',
        '3319': '长兴公共资源交易平台',
        '3320': '苍南公共资源交易平台',
        '3321': '浙江临海市公告资源交易中心',
        '3322': '安吉公共资源交易中心',
        '3323': '萧山政府门户网站',
        '3324': '南浔区公共资源交易平台',
        '3325': '德清县公共资源交易平台',
        '3326': '龙游政府门户网站',
        '3327': '平阳公共资源交易平台',
        '3331': '富阳区公共资源交易中心',
        '3332': '淳安县公共资源交易平台',
        '3333': '浙江交通运输厅',  # 没爬虫

        '3328': '常山县公共交易资源网',
        '3334': '杭州市公共资源交易中心建德分中心',
        '3335': '浙江省温州市鹿城区人民政府',
        '3336': '浙江省温州市乐清市人民政府',
        '3337': '浙江瑞安市人民政府',
        '3338': '浙江省温州市永嘉县人民政府',
        '3339': '浙江省温州市洞头区人民政府',
        '3340': '浙江省温州市文成县人民政府',
        '3341': '浙江省温州市泰顺县人民政府',
        '3342': '浙江省绍兴市上虞区人民政府',
        '3343': '浙江省绍兴市新昌县人民政府',
        '3344': '浙江省绍兴市越城区人民政府',
        '3345': '浙江省绍兴嵊州市人民政府',
        '3346': '浙江省湖州吴兴市人民政府',
        '3347': '台州市温岭市公共资源交易',
        '3348': '台州市三门县公共资源交易',
        '3350': '台州市仙居县公共资源交易',
        '3351': '金华市婺城区公共资源交易',
        '3352': '金华市金东区公共资源交易网',
        '3353': '金华市兰溪市公共资源交易',
        '3354': '金华市东阳市公共资源交易',
        '3355': '金华市永康市公共资源交易网',
        '3356': '浙江省金华义乌市公共资源交易中心',
        '3357': '衢州衢江区公共资源交易网',
        '3358': '衢州开化县公共资源交易网',
        '3359': '衢州柯城区公共资源交易网',
        '3360': '浙江省金华市武义县人民政府',
        '3361': '浙江省金华市浦江县人民政府',
        '3362': '浙江省金华市磐安县人民政府',
    }
    border_type = Side(border_style="medium", color='FF000000')
    border = Border(left=border_type,
                    right=border_type,
                    top=border_type,
                    bottom=border_type,
                    diagonal=border_type,
                    diagonal_direction=0,
                    outline=border_type,
                    vertical=border_type,
                    horizontal=border_type
                    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sdt = kwargs.get('sdt')
        self.edt = kwargs.get('edt')
        self.tb_sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='{db_name}'".format(
            db_name=kwargs.get('db', '')
        )
        self.area_sql = "SELECT area_id FROM {db_name}.%s LIMIT 1".format(
            db_name=kwargs.get('db', ''),
        )
        self.data_list = []
        self.w = Workbook()
        self.ws = self.w.active
        self.start = 2  # 合并单元格起始行
        self.end = 1  # 合并单元格结束行

        self.download_sum = 0
        self.push_sum = 0
        self.pub_sum = 0

        self.cwd = os.getcwd()
        self.file_path = os.path.join(os.path.join(self.cwd, 'files'),'统计{0:%Y-%m-%d}.xls'.format(datetime.now()))

    def get_statistic_data(self, date, table_with_area, serial_number):
        table_name = table_with_area['table_name']
        area_id = table_with_area['area_id']
        result = []

        # if area_id not in [14, 8, 3305]:
        today = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.strptime(date, '%Y-%m-%d'))
        tomorrow = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1, seconds=-1))
        download_sql = """SELECT area_id n, COUNT(id) c FROM {db_name}.{table_name}
        WHERE update_time BETWEEN '{today}' AND '{tomorrow}'
        GROUP BY area_id;""".format(**{
            'today': today,
            'tomorrow': tomorrow,
            'table_name': table_name,
            'db_name': self.db_name,
        })
        pub_sql = """SELECT area_id n, COUNT(id) c FROM {db_name}.{table_name}
        WHERE pub_time BETWEEN '{today}' AND '{tomorrow}'
        GROUP BY area_id;""".format(**{
            'today': today,
            'tomorrow': tomorrow,
            'table_name': table_name,
            'db_name': self.db_name,
        })
        push_sql = """SELECT area_id n, sum(count) FROM {db_name}.statistical
        WHERE date_format(push_time,'%Y-%m-%d')='{cdt}' AND area_id={area_id}
        """.format(**{
            'db_name': self.db_name,
            'area_id': area_id,
            'cdt': date,
        })
        print(download_sql + '\n')
        print(pub_sql + '\n')
        print(push_sql + '\n')
        download_data = self.fetch_all(download_sql)  # [(area_id, n),]
        pub_data = self.fetch_all(pub_sql)
        push_data = self.fetch_all(push_sql)

        try:
            download_n = int(download_data[0][1])
        except Exception as e:
            download_n = 0
        try:
            pub_n = int(pub_data[0][1])
        except Exception as e:
            pub_n = 0
        try:
            push_n = int(push_data[0][1])
        except Exception as e:
            push_n = 0

        # - 异常分析()
        errors = []
        if push_n > pub_n:
            errors.append('ERROR: 推送异常;')
        # if push_n < pub_n:
        #     errors.append('WARNING: 请检查部分未推送原因(重复);')
        # if pub_n == 0:
        #     errors.append('INFO: 今日未站点未发布文章;')
        # if download_n == 0:
        #     errors.append('INFO: 今日未采集到文章;')
        # if push_n == 0:
        #     errors.append('INFO: 今日未推送文章;')
        if pub_n > 0 and push_n == 0:
            errors.append('WARNING: 请检查文章未推送原因;')
        if pub_n > download_n:
            errors.append('WARNING: 请检查是否当日未采集完,第二天采集完造成;')

        error = ''.join(errors)
        error = ''

        result.append(
            [date, serial_number, area_id, pub_n, download_n, push_n, '', '', error]
        )

        self.data_list.extend([[x[0], x[1], self.area_map.get(str(x[2]), x[2]), x[3], x[4], x[5], x[6], x[7], x[8]] for x in result])

    @property
    def table_info(self):
        """
        表名对应的area_id
        Returns:

        """
        com = re.compile('(\d+)')
        ta = []
        tables = [n[0] for n in self.fetch_all(self.tb_sql) if n and n[0].startswith('notices')]
        for t in tables:
            area_ids = com.findall(t)
            # area_ids = self.fetch_all(self.area_sql % t)
            if area_ids:
                ta.append({
                    'table_name': t,
                    'area_id': area_ids[0]
                })
        return ta

    @staticmethod
    def get_date_list(sdt, edt):
        date_list = []
        if sdt == edt:
            date_list = ['{0:%Y-%m-%d}'.format(sdt)]
        if edt > sdt:
            days = (edt - sdt).days
            for _ in range(0, days + 1):
                date_list.append('{0:%Y-%m-%d}'.format(sdt))
                sdt += timedelta(days=1)
        return date_list

    def output(self, **kwargs):
        tts = ['日期', '序号', '网站名称', '站点发布数', '采集数量', '推送数量', '发布数量', '待发布数量', '异常分析']
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
            table_info = self.table_info

            # DATA
            for date in date_list:
                print(date)
                self.data_list = []

                gevent.joinall([gevent.spawn(self.get_statistic_data, date, table_with_area, serial_number + 1) for
                                serial_number, table_with_area in enumerate(table_info)])

                try:
                    self.to_excel(tts, self.data_list)
                except Exception as e:
                    print(e)
                    self.msg = e
            # 合计
            for n, v in enumerate(['合计', '', '', self.pub_sum, self.download_sum, self.push_sum, '']):
                self.ws.cell(row=self.end + 1, column=n + 1, value=v)
            self.ws['A{0}'.format(self.end + 1)].border = self.border
            self.w.save(self.file_path)

    def to_excel(self, tts, data_list):
        """
        输出excel报表
        @result: [
            ['2021-04-16','医疗采购', 575， 1],
            ['2021-04-16','工程建设', 138， 2],
            ['2021-04-17','测试1', 157，0],
            ['2021-04-17','测试2', 3，0],
        ]
        params:
            @tts: 表头列表
            @data_list: 表体数据
            @date_list: 合并时间
        """
        for n, tt in enumerate(tts):
            self.ws.cell(row=1, column=n + 1, value=tt)

        for n, dl in enumerate(data_list):
            self.ws.append(dl)
            self.end += 1

            self.pub_sum += dl[3]
            self.download_sum += dl[4]
            self.push_sum += dl[5]

        # 合并
        self.ws.merge_cells('A{start}:A{end}'.format(start=self.start, end=self.end))
        # 居中
        self.ws['A{start}'.format(start=self.start)].alignment = styles.Alignment(
            horizontal="center", vertical="center"
        )
        # 样式
        for col in ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1']:
            self.ws[col].border = self.border
        for row in self.ws['A']:
            row.border = self.border

        self.w.save(self.file_path)
        self.start = self.end + 1


if __name__ == '__main__':
    data = {
        'host': '114.67.84.76',
        'user': 'root',
        'password': 'Ly3sa%@D0$pJt0y6',
        # 'db': 'test2_data_collection',
        'db': 'data_collection',
    }
    rpt = ReportOutput(**data)
    start_time = datetime.now()
    rpt.output(sdt='2021-12-01', edt='2021-12-01')
    # print((datetime.now() - start_time).total_seconds())
