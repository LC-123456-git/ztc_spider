import pandas as pd

path = r"E:\ztc\extra\代理基本信息2021-05-24.csv"
import csv
import xlwt


def csv_to_xlsx():
    with open(path, 'r') as f:
        read = csv.reader(f)
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('data')  # 创建一个sheet表格
        l = 0
        for line in read:
            print(line)
            r = 0
            for i in line:
                print(i)
                sheet.write(l, r, i)  # 一个一个将单元格数据写入
                r = r + 1
            l = l + 1

        workbook.save('E:\ztc\extra\代理基本信息2021-05-24.xlsx')  # 保存Excel

if __name__ == '__main__':
    csv_to_xlsx()