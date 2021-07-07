#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-22
# @Describe: 工具类
import re
import hashlib
import random
import requests
import datetime
import base64
from Crypto.Cipher import AES
from spider_pro import constans as const
from dateutil.relativedelta import relativedelta
from spider_pro import rules_clean

from lxml import etree
import html
import uuid
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    }

def remove_element_contained(content, ele_name, attr_name, attr_value, specific_ele):
    """
    删除子节点中包含 指定 元素的节点
    Args:
        @content: html文档
        @ele_name: 元素名称
        @attr_name: 元素属性名
        @attr_value: 元素属性值
    Returns:
        @msg: 错误信息
        @content: 构造后的信息
    """
    msg = ''
    try:
        doc = etree.HTML(content)
        els = doc.xpath('//{ele_name}[@{attr_name}={attr_value}]'.format(**{
            'ele_name': ele_name,
            'attr_name': attr_name,
            'attr_value': attr_value,
        }))
        for el in els:
            c_els = el.xpath('.//{specific_ele}'.format(specific_ele=specific_ele))
            if c_els:
                el.getparent().remove(el)
        content = etree.tounicode(doc, method='html')
    except Exception as e:
        msg = e

    return msg, content.replace('<html><body>', '').replace('</body></html>', '')


def remove_specific_element(content, ele_name, attr_name, attr_value, if_child=False, index=1, text='', **kwargs):
    """
    remove specific html element attribute from content
    params:
        @content: html文档
        @ele_name: 元素名称
        @attr_name: 元素属性名
        @attr_value: 元素属性值
        @index: 指定元素索引删除 index:0统统删除
        @text: 指定包含文本的子节点删除
        @kwargs: if_child 移除的是否子元素
                 child_attr 子元素名称
    """
    msg = ''
    try:
        doc = etree.HTML(content)
        els = doc.xpath('//{ele_name}'.format(**{
            'ele_name': ele_name,
        }))

        if attr_name:
            same = 1
            for el in els:
                if attr_value in el.get(attr_name, ''):
                    if if_child:
                        child_attr = kwargs.get('child_attr')

                        # if not text:
                        child_els = el.xpath('.//{child_attr}'.format(**{'child_attr': child_attr}))

                        if not text:
                            for n, child_el in enumerate(child_els):
                                if n == index - 1:
                                    child_el.getparent().remove(child_el)
                                    break
                        else:
                            for child_el in child_els:
                                child_el_text = ','.join(child_el.xpath('.//text()'))
                                if text in child_el_text:
                                    child_el.getparent().remove(child_el)
                                    break
                    else:
                        if index:
                            if same == index:
                                el.getparent().remove(el)
                                break
                            same += 1
                        else:  # 删除所有匹配节点
                            el.getparent().remove(el)
            content = etree.tounicode(doc, method='html')
        else:  # 无属性元素 指定索引删除
            for n, el in enumerate(els):
                if n + 1 == index:
                    el.getparent().remove(el)
    except Exception as e:
        msg = e

    # return msg, content.replace('<html><body>', '').replace('</body></html>', '')
    return msg, content.replace('<html>', '').replace('<body>', '').replace('</body>', '').replace('</html>', '')


def avoid_escape(content):
    """
    防止html转义
    Args:
        content: html字符串
    Returns:
    """
    return html.unescape(content)


def check_if_http_based(url):
    return True if 'http' in url else False


def clean_file_name(file_name, file_types):
    for file_type in file_types:
        if file_type in file_name:
            file_name_split = file_name.split('.{0}'.format(file_type))
            if len(file_name_split) > 1:
                file_name = '{0}.{1}'.format(file_name_split[0], file_type)
                break
    return file_name


def catch_files(content, base_url, **kwargs):
    """
    find doc/excel from content
    """
    msg = ''
    files_path = {}
    # file_types = ['\.pdf|\.rar|\.zip|\.doc|\.docx|\.xls|\.xlsx|\.xml|\.dwg|\.AJZF']
    file_types = [
        'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
        'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF',
    ]
    search_regex = '|'.join(r'\.{0}'.format(file_type) for file_type in file_types)
    try:
        doc = etree.HTML(content)
        # pictures
        img_els = doc.xpath('//img')
        for img_el in img_els:
            src = img_el.attrib.get('src')
            if '.' in src:
                if not check_if_http_based(src):
                    src = ''.join([base_url, src])
                suffix_name = src.split('.')[-1]
                files_path['{uuid}.{suffix_name}'.format(uuid=str(uuid.uuid1()), suffix_name=suffix_name)] = src

        # files
        has_suffix = kwargs.get('has_suffix', False)  # .pdf后有其他符号

        href_els = doc.xpath('//a')
        for href_el in href_els:
            file_name = href_el.xpath('.//text()')

            if file_name:
                file_name = ''.join(file_name).strip()

                # 封装
                if has_suffix:
                    file_name = clean_file_name(file_name, file_types)

                # check file_name exists zip|doc|docx|xls|xlsx
                # RECORDS ALL LINKS EXCEPT CONTENT-TYPE CONTAINS 'text/html'
                file_url = href_el.get('href', '')
                if not check_if_http_based(file_url):
                    file_url = base_url + file_url

                if re.search(search_regex, file_name):
                    files_path[file_name.strip()] = file_url
                else:
                    content_type = requests.get(url=file_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
                                      '(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    }).headers.get('Content-Type')
                    if 'text/html' not in content_type:
                        files_path[file_name.strip()] = file_url
        # iframe_els = doc.xpath('//iframe')
        #
        # for iframe_el in iframe_els:
        #     file_name = iframe_el.get('src', '')
        #
        #     # check file_name exists zip|doc|docx|xls|xlsx
        #     # RECORDS ALL LINKS EXCEPT CONTENT-TYPE CONTAINS 'text/html'
        #     file_url = iframe_el.get('src', '')
        #     if not check_if_http_based(file_url):
        #         file_url = base_url + file_url
        #
        #     if re.search('\.pdf|\.rar|\.zip|\.doc|\.docx|\.xls|\.xlsx|\.xml|\.dwg|\.AJZF', file_name):
        #         files_path[file_name.strip()] = file_url
        #     else:
        #         content_type = requests.get(url=file_url, headers={
        #             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
        #                           '(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        #         }).headers.get('Content-Type')
        #         if 'text/html' not in content_type:
        #             files_path[file_name.strip()] = file_url
    except Exception as e:
        msg = e
    return msg, files_path


def check_range_time(start_time, end_time, content_time):
    """
    check if time between start_time and end_time
    params:
        @start_time: yyyy-mm-dd
        @end_time: yyyy-mm-dd
        @content_time: yyyy-mm-dd
    """
    msg = ''
    status = 1

    if all([start_time, end_time]):
        try:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
            content_time = datetime.datetime.strptime(content_time, '%Y-%m-%d')

            if start_time <= content_time <= end_time:
                pass
            elif start_time > end_time:
                msg = 'params error!'
                status = 0
            else:
                msg = 'not in this period!'
                status = 0

        except Exception as e:
            msg = e
            status = 0

    return status, msg


def add_to_16(s):
    while len(s) % 16 != 0:
        s += (16 - len(s) % 16) * chr(16 - len(s) % 16)
    return str.encode(s)  # 返回bytes

def get_files(domain_url, origin, files_text, keys_a=None):
    files_path = {}
    key_name = 'pdf/img/doc'
    suffix_list = ['html', 'com', 'com/', 'cn', 'cn/', '##', 'cn:8080/', 'htm']
    keys_list = ['前往报名', 'pdf', 'rar', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'xml', 'dwg', 'AJZF',
                 'PDF', 'RAR', 'ZIP', 'DOC', 'DOCX', 'XLS', 'XLSX', 'XML', 'DWG', 'AJZF', 'png',
                 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG', 'ZJYQCF', 'YQZBX']
    [keys_list.append(k_a) for k_a in keys_a]
    if files_text.xpath('//a/@href'):
        files_list = files_text.xpath('//a')
        for cont in files_list:
            if cont.xpath('./@href'):
                values = cont.xpath('./@href')[0]
                if ''.join(values).split('.')[-1] not in suffix_list:
                    if 'http' not in values:
                        value = domain_url + ''.join(values).replace('./', origin[:origin.rindex('/') + 1])
                    else:
                        value = values
                    if cont.xpath('./text()'):
                        keys = ''.join(cont.xpath('./text()')[0]).strip()
                        # 先判断 value 有没有 后缀
                        if value[value.rindex('.') + 1:] in keys_list:          # value 的后缀在 列表中
                            if '.' in keys:    # 在判断 keys 有后缀 点
                                suffix_keys = keys[keys.rindex('.') + 1:]
                                if suffix_keys not in keys_list:      # 判断 keys后缀在不在 列表中
                                    key = keys + value[value.rindex('.'):]
                                else:
                                    key = keys
                            else:
                                key = keys + value[value.rindex('.'):]
                            files_path[key] = value
                        else:          # value 的后缀不在 列表中
                            if '.' in keys:    # 在判断 keys 有后缀 点
                                suffix_keys = keys[keys.rindex('.') + 1:]
                                if suffix_keys in keys_list:  # 判断 keys后缀在不在 列表中
                                    key = keys
                                else:
                                    key = ''
                                if key:
                                    files_path[key] = value

                        # if '.' in keys:
                        #     suffix_keys = keys[keys.rindex('.') + 1:]
                        #     if suffix_keys not in keys_list:
                        #         if ''.join(values).split('.')[-1] not in keys:
                        #             key = keys + '.' + ''.join(values).split('.')[-1].split('&')[0]
                        #         else:
                        #             key = keys
                        #     else:
                        #         key = keys
                        # elif ''.join(values).split('.')[-1] in keys_list:
                        #     key = keys + '.' + ''.join(values).split('.')[-1]
                        # else:
                        #     key = ''
                        # if key:
                        #     files_path[key] = value
    if files_text.xpath('//img/@src'):
        files_list = files_text.xpath('//img')
        for con in files_list:
            values = con.xpath('./@src')[0]
            if 'http:' not in values:
                value = domain_url + values
            else:
                value = values
            if value[value.rindex('.') + 1:] in keys_list:
                key = key_name + value[value.rindex('.'):]
            else:
                key = key_name + '.jpg'
            files_path[key] = value
    return files_path

def get_notice_type(title_name, notice):
    if re.search(r'变更|更正|澄清|补充|取消|延期', title_name):         # 招标变更
        notice_type = const.TYPE_ZB_ALTERATION
    elif re.search(r'终止|中止|废标|流标', title_name):                # 招标异常
        notice_type = const.TYPE_ZB_ABNORMAL
    elif re.search(r'候选人', title_name):                             # 中标预告
        notice_type = const.TYPE_WIN_ADVANCE_NOTICE
    elif re.search(r'采购意向|需求公示', title_name):                   # 招标预告
        notice_type = const.TYPE_ZB_ADVANCE_NOTICE
    elif re.search(r'单一来源|询价|竞争性谈判|竞争性磋商', title_name):  # 招标公告
        notice_type = const.TYPE_ZB_NOTICE
    elif re.search(r'预审', title_name):                               # 资格预审公告
        notice_type = const.TYPE_QUALIFICATION_ADVANCE_NOTICE
    else:
        notice_type = notice
    return notice_type

def get_secret_url(text, key='qnbyzzwmdgghmcnm'):
    aes = AES.new(str.encode(key), AES.MODE_ECB)
    encrypted_text = str(base64.encodebytes(aes.encrypt(add_to_16(text))), encoding='utf8').replace('\n', '')
    encrypted_text = encrypted_text.replace('/', "^")
    return encrypted_text[:-2]


def get_real_url(first_url):
    key = 'qnbyzzwmdgghmcnm'
    # first_url = first_url.split("gov.cn:80")[1]

    aa = first_url.split('/')
    aaa = len(aa)
    bbb = aa[aaa - 1].split('.')
    ccc = bbb[0]
    secret_text = get_secret_url(ccc, key=key)
    first_url = first_url.replace(ccc, secret_text)
    return first_url


def deal_area_data(title_name=None, info_source=None, area_id=None):
    data = title_name + "-" + info_source

    def temp_area_data(province_name, province_code, area_dict, data, info_source=None):
        for city in area_dict["child"]:
            city_name = city["name"]
            city_code = city["code"]
            if re.search(city_name, data):
                area = str(province_name) + str(city_name)
                code = province_code + "-" + city_code
                for county in city["child"]:
                    county_name = county["name"]
                    county_code = county["code"]
                    if re.search(county_name, data):
                        area = str(province_name) + str(city_name) + str(county_name)
                        code = province_code + "-" + city_code + "-" + county_code
                        return {"area": area, "code": str(code)}
                return {"area": area, "code": str(code)}
            else:
                for county in city["child"]:
                    county_name = county["name"]
                    county_code = county["code"]
                    if re.search(county_name, data):
                        area = str(province_name) + str(city_name) + str(county_name)
                        code = province_code + "-" + city_code + "-" + county_code
                        return {"area": area, "code": str(code)}
        return {"area": province_name, "code": str(province_code)}

    area_id = str(area_id)
    if area_id == "0" or area_id == "00":
        for province in const.PROVINCE_LIST:
            province_name = province["name"]
            province_code = province["code"]
            if re.search(province_name, info_source):
                deal_area_dict = temp_area_data(province_name, province_code, province, data)
                return deal_area_dict
            elif re.search(province_name, data):
                deal_area_dict = temp_area_data(province_name, province_code, province, data)
                return deal_area_dict
    elif area_id == "2" or area_id == "02":
        area_dict = const.bei_jing
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["3", "03"]:
        area_dict = const.tian_jin
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["4", "04", "76", "71"]:
        area_dict = const.he_bei
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["5", "05"]:
        area_dict = const.shan_xi_jing
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["6", "06"]:
        area_dict = const.nei_meng_gu
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["8", "08"]:
        area_dict = const.ji_lin
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "10":
        area_dict = const.hei_long_jiang
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["11", "3101", "78"]:
        area_dict = const.shang_hai
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == ["13", '59']:
        area_dict = const.jiang_su
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["14", "15", "52", "77", "3301", "3302", "3303", "3304", "3305", "3306", "3307", "3308", '3309',
                     '3310', '3311', '3312', '3313', '3314', '3315', '3316', '3317', '3318', '3319', '3320', '3321',
                     '3322', '3323', '3324', '3325', '3326', '3327', '3328', '3329']:
        area_dict = const.zhe_jiang
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "16":
        area_dict = const.an_hui
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "18":
        area_dict = const.an_hui
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "19":
        area_dict = const.jiang_xi
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["21", "68"]:
        area_dict = const.shan_dong
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["23", "67"]:
        area_dict = const.he_nan
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "26":
        area_dict = const.hu_bei
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["30", "65"]:
        area_dict = const.guang_dong
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "40":
        area_dict = const.si_chuan
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "41":
        area_dict = const.gui_zhou
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "44":
        area_dict = const.xi_zang
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "47":
        area_dict = const.qing_hai
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "49":
        area_dict = const.ning_xia
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id == "50":
        area_dict = const.xin_jiang
        province_name = area_dict["name"]
        province_code = area_dict["code"]
        deal_area_dict = temp_area_data(province_name, province_code, area_dict, data)
        return deal_area_dict
    elif area_id in ["80"]:
        for province in const.PROVINCE_LIST:
            province_name = province["name"]
            province_code = province["code"]
            if re.search(province_name, title_name):
                deal_area_dict = temp_area_data(province_name, province_code, province, data)
                return deal_area_dict
            elif re.search(province_name, data):
                deal_area_dict = temp_area_data(province_name, province_code, province, data)
                return deal_area_dict
    else:
        for province in const.PROVINCE_LIST:
            province_name = province["name"]
            province_code = province["code"]
            if re.search(province_name, data):
                deal_area_dict = temp_area_data(province_name, province_code, province, data)
                return deal_area_dict


def deal_base_notices_data(data, is_hump=False):
    if is_hump:
        return {
            "title": get_limit_char_from_data(data, "title", 9999),  # 公告标题
            "projectNumber": get_limit_char_from_data(data, "project_number", 300),  # 项目编号
            "projectName": get_limit_char_from_data(data, "project_name", 100),  # 项目名称
            "tenderee": get_limit_char_from_data(data, "tenderee", 100),  # 招标人
            "biddingAgency": get_limit_char_from_data(data, "bidding_agency", 255),  # 招标代理

            "areaCode": get_limit_char_from_data(data, "area_code", 25),  # 区县编号
            "area": get_limit_char_from_data(data, "area", 85),  # 地区
            "address": get_limit_char_from_data(data, "address", 166),  # 详细地址
            "email": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "email", 255), data_type="email"),  # 电子邮箱
            "description": data.get("description", ""),  # 招标方案说明

            'bidType': get_limit_char_from_data(data, "bid_type", 85),
            'bidModus': get_limit_char_from_data(data, "bid_modus", 85),
            'inspectDept': get_limit_char_from_data(data, "inspect_dept", 85),
            'reviewDept': get_limit_char_from_data(data, "review_dept", 85),
            'noticeNature': get_limit_char_from_data(data, "notice_nature", 85),

            "bidFile": get_limit_char_from_data(data, "bid_file", 500),
            "bidFileStartTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_file_start_time", 100), data_type="datetime"),
            "bidFileEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_file_end_time", 100), data_type="datetime"),
            "applyEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "apply_end_time", 100), data_type="datetime"),
            "noticeStartTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "notice_start_time", 100), data_type="datetime"),

            "noticeEndTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "notice_end_time", 100), data_type="datetime"),
            "aberrantType": get_limit_char_from_data(data, "aberrant_type", 100),
            "budgetAmount": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "budget_amount", 255), data_type="number"),
            "tenderopenTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "tenderopen_time", 100), data_type="datetime"),

            "publishTime": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "publish_time"), data_type="datetime"),
            "liaison": get_limit_char_from_data(data, "liaison", 100),
            "contactInformation": get_limit_char_from_data(data, "contact_information", 255),
            "content": data.get("content", ""),  # 公告内容
            "classifyId": data.get("classify_id", ""),

            "classifyName": get_limit_char_from_data(data, "classify_name", 255),
            "projectType": get_limit_char_from_data(data, "project_type", 255),
            "state": get_limit_char_from_data(data, "state", 1) or "0",
            "fileIds": get_limit_char_from_data(data, "file_ids", 100),
            "companyType": get_limit_char_from_data(data, "company_type", 100),

            "successfulBidder": get_limit_char_from_data(data, "successful_bidder", 255),  # 中标方
            "bidAmount": process_data_by_type_begin_upload(
                get_limit_char_from_data(data, "bid_amount"), data_type="number"),  # 中标金额
            "signType": get_limit_char_from_data(data, "sign_type", 1) or "2",  # '标讯类型 0-平台发布1-用户发布2-采集发布'
            "source": get_limit_char_from_data(data, "source", 500),  # '来源(采集的公告就填写采集网站、用户和平台发布就用用户名)'
            "sourceUrl": get_limit_char_from_data(data, "source_url", 500),  # 采集发布来源网站URL

            # "is_upload": get_int_from_data(data, "0")
        }
    else:
        return {
            "title": get_limit_char_from_data(data, "title", 9999),  # 公告标题
            "project_number": get_limit_char_from_data(data, "project_number", 300),  # 项目编号
            "project_name": get_limit_char_from_data(data, "project_name", 100),  # 项目名称
            "tenderee": get_limit_char_from_data(data, "tenderee", 100),  # 招标人
            "bidding_agency": get_limit_char_from_data(data, "bidding_agency", 255),  # 招标代理

            "area_code": get_limit_char_from_data(data, "area_code", 25),  # 区县编号
            "area": get_limit_char_from_data(data, "area", 85),  # 地区
            "address": get_limit_char_from_data(data, "address", 166),  # 详细地址
            "email": get_limit_char_from_data(data, "email", 255),  # 电子邮箱
            "description": data.get("description", ""),  # 招标方案说明

            'bid_type': get_limit_char_from_data(data, "bid_type", 85),
            'bid_modus': get_limit_char_from_data(data, "bid_modus", 85),
            'inspect_dept': get_limit_char_from_data(data, "inspect_dept", 85),
            'review_dept': get_limit_char_from_data(data, "review_dept", 85),
            'notice_nature': get_limit_char_from_data(data, "notice_nature", 85),

            "bid_file": get_limit_char_from_data(data, "bid_file", 500),
            "bid_file_start_time": get_limit_char_from_data(data, "bid_file_start_time", 100),
            "bid_file_end_time": get_limit_char_from_data(data, "bid_file_end_time", 100),
            "apply_end_time": get_limit_char_from_data(data, "apply_end_time", 100),
            "notice_start_time": get_limit_char_from_data(data, "notice_start_time", 100),

            "notice_end_time": get_limit_char_from_data(data, "notice_end_time", 100),
            "aberrant_type": get_limit_char_from_data(data, "aberrant_type", 100),
            "budget_amount": get_limit_char_from_data(data, "budget_amount", 255),
            "tenderopen_time": get_limit_char_from_data(data, "tenderopen_time", 100),

            "publish_time": get_limit_char_from_data(data, "publish_time"),
            "liaison": get_limit_char_from_data(data, "liaison", 100),
            "contact_information": get_limit_char_from_data(data, "contact_information", 255),
            "content": data.get("content", ""),  # 公告内容
            "classify_id": data.get("classify_id", ""),

            "classify_name": get_limit_char_from_data(data, "classify_name", 255),
            "project_type": get_limit_char_from_data(data, "project_type", 255),
            "state": get_limit_char_from_data(data, "state", 1) or "0",
            "file_ids": get_limit_char_from_data(data, "file_ids", 100),
            "company_type": get_limit_char_from_data(data, "company_type", 100),

            "successful_bidder": get_limit_char_from_data(data, "successful_bidder", 255),  # 中标方
            "bid_amount": get_limit_char_from_data(data, "bid_amount"),  # 中标金额
            "sign_type": get_limit_char_from_data(data, "sign_type", 1) or "2",  # '标讯类型 0-平台发布1-用户发布2-采集发布'
            "source": get_limit_char_from_data(data, "source", 500),  # '来源(采集的公告就填写采集网站、用户和平台发布就用用户名)'
            "source_url": get_limit_char_from_data(data, "source_url", 500),  # 采集发布来源网站URL

            # 自有字段
            "is_clean": get_limit_char_from_data(data, "is_clean") or const.TYPE_CLEAN_NOT_DONE,

            "is_have_file": get_limit_char_from_data(data, "is_have_file") or const.TYPE_NOT_HAVE_FILE,
        }


def get_limit_char_from_data(data, name, limit=9999, not_null=False):
    try:
        if data.get(name):
            return data.get(name)[:limit]
            # return pymysql.escape_string(data.get(name)[:limit])
        else:
            return "null" if not_null else ""
    except Exception as e:
        print(e)
        return "null" if not_null else ""


def process_data_by_type_begin_upload(data, data_type="datetime"):
    """
    待上传数据 格式处理
    :param data: 待处理数据
    :param data_type: 数据类型 datetime, int, double
    :return: data : str
    """
    if data_type == "datetime":
        try:
            r = datetime.datetime.fromisoformat(data)
            return r.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return ""
    elif data_type == "email":
        f = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
        if re.match(data, f):
            return data
        else:
            return ""
    elif data_type == "number":
        try:
            data_aft = float(data)
        except:
            return ""
    else:
        return data


def get_back_date(day):
    """
    获取往日时间格式
    :param day:
    :return:
    """
    day = int(day)
    today = datetime.datetime.now()
    if day == 0:
        return today.strftime("%Y-%m-%d")
    else:
        return (today - datetime.timedelta(days=day)).strftime("%Y-%m-%d")


def get_back_date_by_month(month):
    """
    获取往日时间格式，按月
    :param month: 月数
    :return:
    """
    month = int(month)
    today = datetime.datetime.now()
    if month == 0:
        return today.strftime("%Y-%m-%d")
    else:
        return (today - relativedelta(months=month)).strftime("%Y-%m-%d")


def judge_dst_time_greater_than_src_time(dst_time: str, src_time: str):
    try:
        src_time = datetime.datetime.fromisoformat(src_time)
        dst_time = datetime.datetime.fromisoformat(dst_time)
        if dst_time >= src_time:
            return True
    except:
        return False
    return False


def get_uuid_md5_from_data(title_name, content):
    try:
        tmp = ""
        if title_name:
            tmp += title_name
        # if data_time:
        #     if datetime.datetime.fromisoformat(data_time).strftime('%Y-%m-%d %H:%M:%S') == "1970-01-01 00:00:00":
        #         pass
        #     else:
        #         tmp += datetime.datetime.fromisoformat(data_time).strftime("%a %b %d %H:%M:%S CST %Y")
        if content:
            tmp += content
        if tmp:
            return hashlib.md5(tmp.encode()).hexdigest()
        else:
            return False
    except:
        return False


def judge_dst_time_in_interval(dst_time: str, sdt: str, edt: str):
    """
    :param dst_time:
    :param sdt:
    :param edt:
    :return: (x, y, z) x:是否在时间区间内 y:是否比开始时间晚 z: 是否比结束时间早
    """
    try:
        sdt = datetime.datetime.fromisoformat(sdt)
        edt = datetime.datetime.fromisoformat(edt)
        edt = edt.replace(hour=23, minute=59, second=59)
        dst_time = datetime.datetime.fromisoformat(dst_time)
        return sdt <= dst_time <= edt, dst_time < sdt, dst_time > edt
    except:
        return False, False, False


def get_accurate_pub_time(pub_time):
    if not pub_time:
        return ""
    if pub_time_str := re.search(r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group(0)
    elif pub_time_str := re.search(r"\d{4}-\d{1,2}-\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group(0)
    elif pub_time_str := re.search(r"\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group(0).replace(".", "-")
    elif pub_time_str := re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group(0).replace(".", "-")
    elif pub_time_str := re.search(r"\d{4}/\d{1,2}/\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group(0).replace("/", "-")
    elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日\d{1,2}:\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group().replace("年", "-").replace("月", "-").replace("日", " ")
    elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{1,2}", pub_time):
        pub_time_a = pub_time_str.group().replace("年", "-").replace("月", "-").replace("日", " ")
    elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日", pub_time):
        pub_time_a = pub_time_str.group(0).replace("年", "-").replace("月", "-").replace("日", "")
    else:
        pub_time_a = ""
    return pub_time_a


def get_int(int_str: str):
    return int(int_str)


def check_first_char_is_chinese(var):
    if not var and not isinstance(var, str):
        return False
    if '\u4e00' <= var[:1] <= '\u9fff':
        return True
    return False


def deal_address_excel():
    ff = ""
    g1 = "全国"
    g2 = "全国"
    gg = []
    t = False
    for index, item in enumerate(ff):
        if "http" not in item:
            pass
        else:
            h = item.replace("\"", "").replace("\t", " ").replace(" - ", "-").strip()
            h_list = h.split(" ")
            if len(h_list) == 4:
                a1 = h_list[0]
                a2 = h_list[1]
                a3 = h_list[2]
                a4 = h_list[3]
                if not t:
                    if not a2:
                        a2 = g1
                    if not a3:
                        a3 = g2
                    g1 = a2
                    g2 = a3
                if t:
                    gg.append({
                        "area": "",
                        "address": "",
                        "name": a2,
                        "url": a4,
                    })
                else:
                    gg.append({
                        "area": a2,
                        "address": a3,
                        "name": "",
                        "url": a4,
                    })
                if a1 == "33":
                    t = True
            else:
                a = h_list[0]
                gg.append({
                    "area": g1,
                    "address": g2,
                    "name": "",
                    "url": a,
                })


def get_url_title(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            s = r.content.decode("utf-8")
            t = re.search(r"<title>.*</title>", s).group(0)
            return t.split("<title>")[1].split("</title>")[0]
        return ""
    except:
        return ""


def get_random_name(num=8, simple=False):
    if not simple:
        seed = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    else:
        seed = 'abcdefghijklmnopqrstuvwxyz0123456789'
    name = ''.join([random.choice(seed) for i in range(num)])
    return name


def get_iframe_pdf_div_code(url):
    return f'''<div style="width: 100%; height: 300px;" id="pdf-div"><iframe id="displayPdfIframe" width="100%" height="100%" src="{url}"></iframe></div>'''


def match_key_words(content, regular_plans):
    """
    根据正则规则库循环匹配关键词
    Returns:
    """
    c_regular = ''
    for rg in range(1, len(regular_plans) + 1):
        status, data = regular_match(content, rg)
        if status:
            tenderee = data.get('tenderee', '')
            liaison = data.get('liaison', '')
            address = data.get('address', '')
            contact_information = data.get('contact_information', '')
            c_regular = rg  # 匹配规则

            return tenderee, liaison, address, contact_information


def match_key_re(content, regular_plan, keys):
    for rg in range(1, len(regular_plan) + 1):
        status, data = regular_match(keys, content, rg)
        if status:
            keys = data.get('keys', '')
        return keys

def regular_match(keys, content, plan=0):
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
    p_els = doc.xpath('//div[@class="content-right"]//p/*') or doc.xpath('//div[@class="content-right"]//td/*')
    info_list = []
    for data_info in p_els:
        info = ''.join(data_info.xpath('.//text()'))
        info_list.append(info)

    text = ','.join(info_list).replace('\n', '').replace('\r\n', '')

    pl_reg = rules_clean.regular_plans.get(plan, '')
    if pl_reg:
        pl_com = re.compile(pl_reg)
        ret = [m.groupdict() for m in re.finditer(pl_com, text)]
        if ret:
            ret = ret[-1]
            data['keys'] = ret.get('keys', '')
            # data['tenderee'] = ret.get('tenderee', '')
            # data['address'] = ''.join(ret.get('address', '')).strip()
            # data['contact_information'] = ''.join(ret.get('contact_information')).replace(',', '')
            # data['liaison'] = ret.get('liaison', '')
            status = True
    return status, data

def get_url(strst_url, cid):
    cid_url = "{}/cms/attachment_url.jspx?cid={}&n=1".format(strst_url, cid)
    response = requests.get(url=cid_url, headers=headers).content.decode('utf-8').replace('["', '').replace('"]', '')

    return response




if __name__ == "__main__":
    # print(get_real_url('http://ggzyjy.shandong.gov.cn:80/jsgczbgg/4795851.jhtml'))
    # pass
    title_name = '黄骅市第七中学建设项目设计中标候选人公示'
    info_source = '河北-廊坊市'
    area_id = '04'
    ret = deal_area_data(title_name, info_source, area_id)
    print(ret)
