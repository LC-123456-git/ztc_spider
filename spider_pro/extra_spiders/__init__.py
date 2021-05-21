# @Time : 2021/5/14 9:02 
# @Author : miaokela
# @File : __init__.py.py 
# @Description: 导入配置文件
import configparser


cf = configparser.ConfigParser()
cf.read('./config/sql.ini')
