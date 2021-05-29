# @Time : 2021/5/14 9:02 
# @Author : miaokela
# @File : __init__.py.py 
# @Description: 导入配置文件
import configparser
import os

cf = configparser.RawConfigParser()
cf.read(os.path.join(os.path.join(os.path.dirname(__file__), 'config'), 'sql.ini'))
