# @Time : 2021/5/18 22:27 
# @Author : miaokela
# @File : qcc_to_excel.py 
# @Description: 企查查基本信息导出excel
from datetime import datetime
import pandas as pd
import pymysql
import re


class QCCToExcel(object):

    def __init__(self, **credit):
        self.conn = pymysql.connect(
            host=credit.get('host', ''),
            user=credit.get('user', ''),
            password=credit.get('password', ''),
            db=credit.get('db', ''),
            charset='utf8mb4',
            port=credit.get('port', 3306),
        )
        self.cur = self.conn.cursor()
        # self.header = (
        #     '序号', '企业名称', '所属地区', '法定代表人', '成立日期', '登记状态', '注册资本', '实缴资本', '统一社会信用代码',
        #     '工商注册号', '组织机构代码', '纳税人识别号', '纳税人资质', '企业类型', '行业', '营业期限始', '营业期限末',
        #     '人员规模', '参保人数', '英文名', '曾用名', '登记机关', '核准日期', '注册地址', '经营范围', '进出口企业代码',
        #     '企业分类', '行业大类', '创建时间', '更新时间'
        # )
        self.header = (
            '序号', '统一社会信用代码', '企业名称', '工商注册号', '组织机构代码', '纳税人识别号', '纳税人资质', '行业', '法定代表人', '企业类型',
            '成立日期', '注册资本', '实缴资本', '核准日期', '营业期限始', '营业期限末', '登记机关', '注册地址', '经营范围',
            '创建时间', '更新时间',
        )

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def fetchall(self, fetch_sql):
        self.cur.execute(fetch_sql)
        ret = self.cur.fetchall()
        return ret

    def run(self):
        """
        'company_name': company_info.get('企业名称', ''),
        'location': company_info.get('所属地区', ''),
        'legal_representative': company_info.get('法定代表人', ''),
        'date_of_establishment': company_info.get('成立日期', ''),
        'operating_status': company_info.get('登记状态', ''),
        'registered_capital': company_info.get('注册资本', ''),
        'paid_in_capital': company_info.get('实缴资本', ''),
        'unified_social_credit_code': company_info.get('统一社会信用代码', ''),
        'business_registration_number': company_info.get('工商注册号', ''),
        'organization_code': company_info.get('组织机构代码', ''),
        'taxpayer_identification_number': company_info.get('纳税人识别号', ''),
        'taxpayer_qualification': company_info.get('纳税人资质', ''),
        'type_of_enterprise': company_info.get('企业类型', ''),
        'industry': company_info.get('行业', ''),
        'operating_period_std': company_info.get('营业期限始', ''),
        'operating_period_edt': company_info.get('营业期限末', ''),
        'staff_size': company_info.get('人员规模', ''),
        'number_of_participants': company_info.get('参保人数', ''),
        'english_name': company_info.get('英文名', ''),
        'former_name': company_info.get('曾用名', ''),
        'registration_authority': company_info.get('登记机关', ''),
        'approved_date': company_info.get('核准日期', ''),
        'registered_address': company_info.get('注册地址', ''),
        'business_scope': company_info.get('经营范围', ''),
        'import_and_export_enterprise_code': company_info.get('进出口企业代码', ''),
        'category': resp.meta.get('category_name', ''),
        'industry_category': resp.meta.get('industry_category_name', ''),
        :return:
        """
        # qcc_sql = """SELECT id, QYMC, SSDQ, FDDBR, CLRQ, DJZT, ZCZB, SJZB, TYSHXYDM, GSZCH, ZZJGDM, NSRSBH, NSRZZ, QYLX, HY,
        # YYQXS, YYQXM, RYGM, CBRY, YWM, CYM, DJJG, HZRQ, ZCDZ, JYFW, JCKQYDM, QYFL, HYDL, create_time, update_time
        # FROM data_collection.QCC_qcc_crawler"""
        qcc_sql = """SELECT id, TYSHXYDM, QYMC, GSZCH, ZZJGDM, NSRSBH, NSRZZ,HY, FDDBR, QYLX, CLRQ, ZCZB, SJZB, HZRQ, YYQXS,
        YYQXM, DJJG, ZCDZ, JYFW, create_time, update_time
        FROM data_collection.QCC_qcc_crawler"""

        file_name = '企业基本信息{0:%Y-%m-%d}.xlsx'.format(datetime.now())

        qcc_data = self.fetchall(qcc_sql)

        # DATA CUSTOM
        qcc_data = [
            [
                qd[0], qd[1], qd[2], qd[3], qd[4], qd[5], qd[6], qd[7], qd[8], qd[9],
                qd[10], qd[11], qd[12], qd[13], qd[14], qd[15], qd[16], qd[17], qd[18], qd[19], qd[20],
            ] for qd in qcc_data]

        df_data = pd.DataFrame.from_records(qcc_data)

        df_data.to_excel(file_name, index=False, header=self.header)


if __name__ == '__main__':
    credit = {
        'host': '114.67.84.76',
        'user': 'root',
        'password': 'Ly3sa%@D0$pJt0y6',
        'db': 'data_collection',
        'port': 8050,
    }
    qcc_to_excel = QCCToExcel(**credit)
    qcc_to_excel.run()
