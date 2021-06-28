#!/usr/bin/env python
# coding=utf-8
# @Time : 2021/5/21
# @Author : lc
# @File : quanguo.py
# @Description: 代理基本信息导出excel
import re

import requests, json, pymysql
from openpyxl import Workbook
import concurrent.futures, threading
from ceshi import create_db


class Agency_Info:
    def __init__(self):
        self.cur = cur
        self.client = client
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36',
            # 'Referer': 'http://jczy.ccgp.gov.cn/gs1/gs1agentreg/pubListIndex.regx'
        }
        # self.data_info = data_info
        self.url = url
        # 将数据写入Excel
        self.a = Workbook()
        self.table_name = 'quanguo'
        # 新建一个表
        self.ws1 = self.a.active

    def get_start(self, data_info):
        info_list = []
        s = requests.session()
        ret = s.post(url=self.url, data=data_info, headers=self.headers, allow_redirects=False).text
        try:
            data = json.loads(ret)['rows']
            for data_num in data:
                if len(data_num['orgCode']) == 9:
                    institutional = data_num['orgCode']
                    society_code = ''
                else:
                    society_code = data_num['orgCode']
                    institutional = ''
                agency = data_num['agentNm']
                liaison = data_num['contactNm']
                contact_information = data_num['corpTel']
                address = data_num['regAddr']
                put_time = data_num['regValidDateStr']
                city = data_num['auditPlace']



                item = {
                    'society_code': society_code,
                    'agency': agency,
                    'liaison': liaison,
                    'contact_information': contact_information,
                    'address': address,
                    'put_time': put_time,
                    'city': city,
                    'institutional': institutional
                }

                info_list.append(item)
            # return item

                # base.insert_table(self.conn, item, table_name='quanguo')
                # row = [society_code, agency, liaison, contact_information, address, pub_time, city]
                # info_list.append(item)

        except Exception as e:
            print(e, data_info)


        return info_list

    def get_db(self, info_list):
        # 存数据库
        for _data in info_list:
            try:
                def sql(col, placeholder, tablename):
                    return """insert into {tablename} ({col}) values ({placeholder})""".format(tablename=tablename, col=col,
                                                                                               placeholder=placeholder)
                keys = list(_data.keys())
                args = tuple([_data[key] for key in keys])
                self.cur.execute(sql(','.join(keys), ','.join(['%s '] * len(keys)), self.table_name), args)
                self.client.commit()

            except Exception as e:
                print(e)

    def get_excel(self, info_list):
        # 设置Excel文件名
        dest_filename = 'E:\lc\全国代理.xlsx'

        # 设置表头
        titleList = ['社会信用码', '机构名称', '联系人', '联系电话', '地址', '时间', '城市']

        for row in range(len(titleList)):
            c = row + 1
            self.ws1.cell(row=1, column=c, value=titleList[row])
        # 填写表内容
        for listIndex in range(len(info_list)):
            self.ws1.append(info_list[listIndex])

        self.a.save(filename=dest_filename)

    def get_run(self, data_info):
        info_list = self.get_start(data_info)
        return info_list


if __name__ == '__main__':
    client = pymysql.connect(
        host='114.67.84.76',
        user='root',
        password='Ly3sa%@D0$pJt0y6',
        db='data_collection',
        port=8050,
        charset='utf8mb4',)
    cur = client.cursor()
    url = 'http://jczy.ccgp.gov.cn/gs1/gs1agentreg/getPubList.regx?provinceCode='
    info_dice = {'page': '1', 'rows': '50', 'sort': 'regValidDate', 'order': 'desc'}
    page_list = [info_dice | {'page': page} for page in range(1, 588)]
    threads = []
    srart = Agency_Info()
    for data_info in page_list:
        print(data_info)
        g = srart.get_run(data_info)
        srart.get_db(g)
        # t1 = threading.Thread(target=srart.get_db, args=(srart.get_run(data_info),))
        # t1.start()
    cur.close()
    client.close()












