# @Time : 2021/5/21
# @Author : lc
# @File : daili_xinxi.py
# @Description: 代理基本信息导出excel


from datetime import datetime
import pandas as pd
import pymysql
import re, xlwt, time
from lxml import etree
from ceshi import config_zhengze
class DLXXToExcel(object):

    def __init__(self, **credit):
        self.conn = pymysql.connect(
            host=credit.get('host', ''),
            user=credit.get('user', ''),
            password=credit.get('password', ''),
            db=credit.get('db', ''),
            charset='utf8mb4',
            port=credit.get('port', 8050),
        )
        self.cur = self.conn.cursor()
        self.regular_plans = regular_plans
        # self.header = (
        #     '序号', '企业名称', '所属地区', '法定代表人', '成立日期', '登记状态', '注册资本', '实缴资本', '统一社会信用代码',
        #     '工商注册号', '组织机构代码', '纳税人识别号', '纳税人资质', '企业类型', '行业', '营业期限始', '营业期限末',
        #     '人员规模', '参保人数', '英文名', '曾用名', '登记机关', '核准日期', '注册地址', '经营范围', '进出口企业代码',
        #     '企业分类', '行业大类', '创建时间', '更新时间'
        # )
        self.header = [
            '代理名称', '地址', '联系人', '电话号码', '时间', '城市', '正则第几个', 'url'
        ]

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def fetchall(self, fetch_sql):
        self.cur.execute(fetch_sql)
        ret = self.cur.fetchall()
        return ret

    def get_sql(self, table_name):
        results_sql = f"select * from {table_name} where is_have_file = 0 and classify_name = '招标公告' " \
                      f"UNION ALL select * from {table_name} where is_have_file = 0 and classify_name = '中标公告'"
        # results_sql = f"select * from data_collection.notices_52 where origin='https://www.hibidding.com/Detail/42'"

        results = self.fetchall(results_sql)
        for item in results:
            content_dict = {'content': item[5], 'id': item[1], 'city': item[21], 'pub_time': item[3]}
            self.match_key_words(content_dict)

    def match_key_words(self, content_dict):
        """
        results   根据正则规则库循环匹配关键词
        Returns:
        """
        c_regular = ''
        info_data = []
        for rg in range(1, len(self.regular_plans)):
            try:
                status, data = self.regular_match(content_dict['content'], rg)
                if status:
                    tenderee = data.get('tenderee', '')
                    liaison = data.get('liaison', '')
                    address = data.get('address', '')
                    contact_information = data.get('contact_information', '')
                    url = content_dict['id']
                    city = content_dict['city']
                    pub_time = content_dict['pub_time']
                    c_regular = rg  # 匹配规则
                    print('代理：', tenderee,
                          '地址：', address,
                          '联系人：', liaison,
                          '联系电话：', contact_information,
                          # '城市：', city,
                          # '发布时间：', pub_time,
                          '正则规则', c_regular,
                          'url', url, '\n', '***************************')
                    info_data.append([tenderee, address, liaison, contact_information, city, pub_time, c_regular, url])
                    break
            except Exception as e:
                print(e)

        # self.get_excel(info_data)


    def get_excel(self, info_data):

        file_name = '代理基本信息{0:%Y-%m-%d}.csv'.format(datetime.now())

        df_data = pd.DataFrame.from_records(info_data)

        df_data.to_csv(file_name, index=False, header=False, mode='a')

    def regular_match(self, content, plan=0):
        """
        正则匹配字段内容
        Args:
            plan: 方案
            content:
        Returns:

        """
        status = False  # True表示获取成功 False表示获取失败
        data = {}
        doc = etree.HTML(content)
        # 品茗的text
        # p_els = doc.xpath('//div[@class="content-right"]//p/*') or doc.xpath('//div[@class="content-right"]//td/*')

        # 必联
        p_els = doc.xpath('//div[@id="notLogin"]//p')
                # or doc.xpath('//div[@id="notLogin"]')
        info_list = []
        for data_info in p_els:
            info = ''.join(data_info.xpath('.//text()'))
            info_list.append(info)

        text = ','.join(info_list).replace('\n', '').replace('\r', '').replace('\t', '')

        pl_reg = self.regular_plans.get(plan, '')

        if pl_reg:
            try:
                pl_com = re.compile(pl_reg)
                ret = [m.groupdict() for m in re.finditer(pl_com, text)]
                if ret:
                    ret = ret[-1]
                    if re.findall('(.*)\/\d+', ''.join(ret.get('liaison', '')).replace(',', '').strip()):
                        data['liaison'] = re.findall('(.*?)\/\d+', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
                        data['contact_information'] =  re.findall('.*\/(\d{11})', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
                        data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
                        data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''

                    elif re.findall('(.*)\s*\d{4}-\d{7,8}|\d{11}', ''.join(ret.get('liaison', '')).replace(',', '').strip()):
                        data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
                        data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''
                        data['liaison'] = re.findall('(.*)\s*\d{4}-\d{7,8}|\d{11}', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''
                        data['contact_information'] = re.findall('.*\s*(\d{4}-\d{7,8}|\d{11})', ''.join(ret.get('liaison', '')).replace(',', '').strip())[0] or ''

                    # elif re.findall('(.*?)\d{3,4}-\d{7,8}?|\d{11}', ''.join(ret.get('contact_information', '')).replace(',', '').strip()):
                    #     data['liaison'] = re.findall('(.*?)\d+', ''.join(ret.get('contact_information', '')).replace(',', '').strip())[0] or ''
                    #     data['contact_information'] = re.findall('.*(\d{11})', ''.join(ret.get('contact_information', '')).replace(',', '').strip())[0] or ''
                    #     data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
                    #     data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''

                    else:
                        data['tenderee'] = ''.join(ret.get('tenderee', '')).replace(',', '').strip() or ''
                        data['address'] = ''.join(ret.get('address', '')).replace(',', '').strip() or ''
                        data['contact_information'] = ''.join(ret.get('contact_information')).replace(',', '').strip() or ''
                        data['liaison'] = ''.join(ret.get('liaison', '')).replace(',', '').strip() or ''
                    status = True

                return status, data

            except Exception as e:
                print(e)




if __name__ == '__main__':
    credit = {
        'host': '114.67.84.76',
        'user': 'root',
        'password': 'Ly3sa%@D0$pJt0y6',
        'db': 'data_collection',
        'port': 8050,
        'table_name': 'notices_53',
    }

    regular_plans = config_zhengze.bilian_regular_plans

    table_name = 'notices_53'
    qcc_to_excel = DLXXToExcel(**credit)
    qcc_to_excel.get_sql(table_name)





