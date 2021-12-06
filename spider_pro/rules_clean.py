# -*- coding:utf-8 -*-
import decimal
import math
import re
import cn2an
import pandas
import copy

from lxml import etree
from decimal import Decimal
from html_table_extractor.extractor import Extractor
from functools import wraps

from spider_pro import utils


def get_keys_value_from_content_ahead(content, keys, area_id="00", _type="", field_name=None, title=None, **kwargs):
    ke = KeywordsExtract(
        content, keys, field_name, area_id=area_id, title=title, **kwargs
    )
    return ke.get_value()


def catch_title_before_method(func):
    @wraps(func)
    def inner(self, *arg, **kwargs):
        if self.field_name == 'project_name':
            method_name = func.__name__
            owners = self.before_map.get(method_name, [])

            # + area_id不在总规则范围内：方法为done_before_extract调用
            # + 否则规则调用
            all_rules = []
            for bv in self.before_map.values():
                all_rules.extend(bv)
            if self.area_id not in all_rules and method_name == 'done_before_extract':
                self.get_val_from_title()
            else:
                if self.area_id in owners:
                    self.get_val_from_title()
        func(self, *arg, **kwargs)

    return inner


class KeywordsExtract(object):
    """
    根据若干个关键字 权衡匹配出对应的值 返回首个匹配结果
    规则：
        1.纯文本提取（默认）；
        2.html文档提取；
    """

    def __init__(self, content, keys, field_name, area_id=None, title=None, **kwargs):
        # - yaml文件配置
        self.br_cf = kwargs.get('br_cf', '')
        self.cr_cf = kwargs.get('cr_cf', '')
        self.pb_cf = kwargs.get('pb_cf', '')
        self.before_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.br_cf, field_name)]
        self.common_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.cr_cf, field_name)]
        self.liaison_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'LIAISON')]
        self.symbols_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'SYMBOLS')]
        self.head_tail_symbols_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'HEAD_TAIL_SYMBOLS')]
        self.company_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'COMAPNY')]
        self.amount_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'AMOUNT')]
        self.project_name_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'PROJECT_NAME')]
        self.contact_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'CONTACT')]
        self.liaison_union_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'LIAISON_UNION')]
        self.contact_union_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.pb_cf, 'CONTACT_UNION')]
        self.isolated_unit = utils.get_keywords(self.pb_cf, 'ISOLATED_UNIT')
        self.project_priority = utils.get_keywords(self.pb_cf, 'PROJECT_PRIORITY')
        self.last_part = utils.get_keywords(self.pb_cf, 'LAST_PART')
        self.project_number_from_title = utils.get_keywords(self.pb_cf, 'PROJECT_NUMBER_FROM_TITLE')
        self.project_priority_cg = utils.get_keywords(self.pb_cf, 'PROJECT_PRIORITY_CG')
        self.project_number = utils.get_keywords(self.pb_cf, 'PROJECT_NUMBER')
        self.wrapped_project_name = utils.get_keywords(self.pb_cf, 'WRAPPED_PROJECT_NAME_REG')
        self.vertical_key = utils.get_keywords(self.pb_cf, 'VERTICAL_KEYS')

        self.content = content.replace('\xa0', ' ').replace('\n', '').replace('\u3000', ' ')
        self.keys = keys if isinstance(keys, list) else [keys]
        self.area_id = area_id
        self.field_name = field_name
        self.title = title
        self.msg = ''
        # 各字段对应的规则
        self.fields_regular = {
            'project_name': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_number': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'budget_amount': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderee': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bidding_agency': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'liaison': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
            ],
            'contact_information': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
            ],
            'successful_bidder': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bid_amount': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderopen_time': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_leader': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_contact_information': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'agent_contact': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bidding_contact': [
                r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
        }
        self.fields_regular_with_symbol = copy.deepcopy(self.fields_regular)
        self._value = ''

        # 倍数
        self.multi_number = 1
        # 在提取project_name时，指定位置(指定方法前)调用:self.get_val_from_title
        self.before_map = {
            '_extract_from_table': [],
            'clean_value': ['120', '123', '124', '131', '126', '128', '132', '133', '145'],
        }

    def reset_regular_by_field(self):
        """
        - conf/common_regular/*.yaml
        - 根据字段修改正则列表
        """
        if self.common_regulars:
            self.fields_regular.update(**{
                self.field_name: self.common_regulars
            })

    @staticmethod
    def strQ2B(ustring):
        """全角转半角"""
        rstring = ""
        for uchar in ustring:
            inside_code = ord(uchar)
            if inside_code == 12288:  # 全角空格直接转换
                inside_code = 32
            elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化
                inside_code -= 65248

            rstring += chr(inside_code)
        return rstring

    def reload_multi_number(self, key):
        """
        - 取到值并处理之后，根据 key 中包含 千万 百万 十万 万 设置倍率
        """
        if self.field_name in ['bid_amount', 'budget_amount']:
            if '千万' in key:
                self.multi_number *= 10000000
            elif '百万' in key:
                self.multi_number *= 1000000
            elif '十万' in key:
                self.multi_number *= 100000
            elif '万' in key:
                self.multi_number *= 10000
            else:
                pass

    def _regular_match(self, text, key, with_symbol=True):
        """
        正则匹配
        Args:
            text ([string]): [文章处理后的文本]
            key ([string]): [关键字]
            with_symbol (bool, optional): [文章处理是否通过符号切分]. Defaults to True.

        Returns:
            [string]: [匹配出的值]
        """
        val = ''
        c_regular = self.fields_regular if with_symbol else self.fields_regular_with_symbol
        re_list = c_regular.get(self.field_name, [])
        for rl in re_list:
            re_string = rl % key if with_symbol else rl
            com = re.compile(re_string)
            result = com.findall(text)
            if result:  # 处理一个例外：匹配的就是一个空字符串，而不是没匹配到
                if result[0].strip():
                    val = ''.join(result[0])
                else:
                    val = ' '

            if val:
                if with_symbol:
                    self.reload_multi_number(key)
                else:
                    self.reload_multi_number(val)
                break
        return val

    def _extract_from_text(self, with_symbol=True):
        """
        纯文本中提取字段值
        Args:
            with_symbol (bool, optional): [文本是否通过符号切分]. Defaults to True.
        """
        if not self._value:
            for key in self.keys:
                try:
                    doc = etree.HTML(self.content.replace('&nbsp;', ' '))
                    txt_els = [x for x in doc.xpath('//*//text()')]
                    text = 'ψ'.join(txt_els) if with_symbol else ''.join(txt_els)
                    self._value = self._regular_match(text, key, with_symbol=with_symbol)
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)

                if self._value:
                    break

    @property
    def value(self):
        return self._value

    def is_horizon(self, t_data):
        """
        判断tr下td数是否相同
        """
        count = 0
        try:
            t_data = t_data[0]
        except (Exception,) as e:
            self.msg = 'error:{0}'.format(e)
        else:
            for t_data_key in t_data:
                try:
                    t_data_key = ''.join(t_data_key.split())
                except (Exception,):
                    t_data_key = ''
                if t_data_key in self.vertical_key:
                    count += 1
        return True if count >= 2 else False

    @staticmethod
    def get_child_tables(doc_el):
        return doc_el.xpath('.//table')

    @staticmethod
    def get_h_val(c_index, key, tr, table=None, tr_index=None):
        c_index += 1
        try:
            next_val = tr[c_index].replace('\u3000', '')  # 判断值所在td如果是个table，如果还嵌套一个table，直接取所有内容
        except (Exception,):
            pass
        else:
            if next_val == key:
                next_val = KeywordsExtract.get_h_val(c_index, key, tr)

            if not next_val and table is not None:
                val_table = table.xpath(
                    './/tr[not(contains(@style, "line-height:0px"))][position()=%d]/td[position()=%d]' % (
                        c_index + 1, tr_index
                    )
                )
                if val_table:
                    child_table = val_table[0].xpath('./table')
                    if child_table:
                        next_val = val_table[0].xpath('string(.)')

            return next_val

    def get_val_from_table(self, result, key, table=None):
        for tr_index, tr in enumerate(result):
            for c_index, td in enumerate(tr):
                try:
                    td = ''.join(td.split())
                except (Exception,):
                    td = ''
                if td == key:
                    # next
                    # 需要两个参数 tr_index td_index(tr需要排除height="0px"的情况)
                    next_val = KeywordsExtract.get_h_val(c_index, key, tr, table=table, tr_index=tr_index + 1)
                    if next_val:
                        self.reload_multi_number(key)
                        return next_val
        return ''

    def recurse_parse_table(self, table_els, key, doc):
        c_doc = copy.deepcopy(doc)
        copy_table_els = copy.deepcopy(table_els)
        for n, table_el in enumerate(table_els):
            c_child_tables = KeywordsExtract.get_child_tables(table_el)

            # REMOVE CHILD TABLE
            for c_child_table in c_child_tables:
                c_child_table.getparent().remove(c_child_table)

            # REMOVE TR WITHOUT HEIGHT
            trs_without_height = table_el.xpath('.//tr[contains(@style, "line-height:0px")]')
            for tr in trs_without_height:
                tr.getparent().remove(tr)

            # REMOVE TR WITHOUT TD
            trs_without_td = table_el.xpath('.//tr')
            for tr in trs_without_td:
                if not tr.xpath('.//text()'):
                    tr.getparent().remove(tr)

            table_txt = etree.tounicode(table_el, method='html')
            try:
                t_data = pandas.read_html(table_txt)[0]
            except (Exception,) as e:
                self.msg = 'error:{0}'.format(e)
            else:
                # 判断横向|纵向
                # tr下td数一致     横向
                # tr下td数不一致    纵向
                # 可能存在无法解析的字段(如表格)
                # 值中再无table，取table所有文本作为值
                key = ''.join(key.split())
                extractor = Extractor(table_txt.replace('\n', ''))
                extractor.parse()
                result = extractor.return_list()

                # table首列
                # key
                # t_data = [['序号', '1']]
                # key = '中标供应商名称'
                # result = [
                #     ['序号','中标（成交）金额(元)','中标供应商名称','中标供应商地址'],
                #     ['1',	'最终报价:1728800.00(元)',	'浙江长兴市政建设有限公司',	'浙江省湖州市长兴县画溪街道城南路1号']
                # ]

                if self.is_horizon(t_data) or len(result) == 1:
                    self._value = self.get_val_from_table(result, key, table=copy_table_els[n])
                else:
                    result = list(zip(*result))
                    self._value = self.get_val_from_table(result, key, table=copy_table_els[n])
                if self._value:
                    return True
            child_tables = KeywordsExtract.get_child_tables(table_el)
            if child_tables:
                self.recurse_parse_table(child_tables, key, c_doc)
        return False

    @catch_title_before_method
    def _extract_from_table(self):
        """
        处理文章中table的信息
        """
        if not self._value:
            for key in self.keys:
                doc = etree.HTML(self.content)
                table_els = doc.xpath('//table')

                if self.recurse_parse_table(table_els, key, doc):
                    return

    def reset_regular(self, regular_list, with_symbol=True):
        """
        重置指定字段匹配规则
        Args:
            regular_list ([list]): [字段的规则列表]
            with_symbol (bool, optional): [文本是否通过符号切分]. Defaults to True.
        """
        if with_symbol:
            self.fields_regular.get(self.field_name, []).clear()
            self.fields_regular[self.field_name] = regular_list
        else:
            self.fields_regular_with_symbol.get(self.field_name, []).clear()
            self.fields_regular_with_symbol[self.field_name] = regular_list

    def brackets_contained(self, name):
        """
        判断 name 是否仅出现一次，且在括号里出现
        :param name:
        :return:
        """
        c_regular = r'[\[ \( （ 【]\s*[\u4e00-\u9fa5]*?{name}[\u4e00-\u9fa5]*?\s*[\] \) ） 】]'.format(
            name=name,
        )
        if re.search(c_regular, self.title) and len(re.findall(name, self.title)) == 1:
            return True
        return False

    def get_val_from_title(self):
        """
        从标题获取项目名称
            1.从前截取掉一部分丢弃
            2.关键词匹配包含
                另外: 如果在self.wrapped_list列表中的站点，先以 "关于... ... 的结果公告" 等来提取
        """
        if self.field_name == 'project_name' and self.title and not self._value.strip():
            # 关于 ... 公告过滤
            for wpn_reg in self.wrapped_project_name:
                ret = re.findall(r'%s' % wpn_reg, self.title)
                if ret:
                    self._value = ret[0]
                    return

            # 根据关键字优先级匹配项目名称
            title_list = self.project_priority_cg if '采购' in self.title else self.project_priority
            for name in title_list:
                if name in self.title:
                    # 判断项目关键字是否在（）【】 [] 内
                    if self.brackets_contained(name):
                        continue

                    self._value = ''.join([self.title.split(name)[0], name])
                    delete_chars = ['【】']
                    for dc in delete_chars:
                        self._value = self._value.replace(dc, '')
                    break

            # 标题包含：取后半部分
            for lp in self.last_part:
                c_v = self._value.split(lp)
                if len(c_v) == 2:
                    self._value = c_v[1]

    @catch_title_before_method
    def done_before_extract(self):
        """
        - 通用提取前，根据地区单独提取
        """
        self._value = self._value if self._value else ''
        if not self._value.strip():
            regular_list = self.before_regulars
            self.reset_regular(regular_list, with_symbol=False)
            self._extract_from_text(with_symbol=False)

    @staticmethod
    def remove_rest_zero(decimal_obj):
        return decimal_obj.to_integral() if decimal_obj == decimal_obj.to_integral() else decimal_obj.normalize()

    def is_isolated_unit(self):
        """
        - 特殊单位的处理
        :return:
        """
        extra_units = self.isolated_unit
        for extra_unit in extra_units:
            if extra_unit in self._value:
                return True
        return False

    @staticmethod
    def remove_rest_suffix(val):
        """
        - 删除 元 后多余字符
        """
        com = re.compile(r'.*元')
        vals = com.findall(val)
        return vals[0] if vals else val

    @staticmethod
    def remove_chars_by_regs(reg_list, val, replace_str=None):
        """
        - 根据正则列表对剔除符合条件的内容
            @reg_list:正则列表
            @val:处理前的值
            @repalce_str(缺省):替换为指定字符串
        """
        for reg in reg_list:
            val = re.sub(reg, '' if not replace_str else replace_str, val)
        return val

    @staticmethod
    def remove_head_or_tail_symbols(symbols, val):
        for symbol in symbols:
            symbol_length = len(symbol)
            val_length = len(val)
            if val.startswith(symbol):
                val = val[symbol_length:]
            if val.endswith(symbol):
                val = val[:val_length - symbol_length]
        return val

    @staticmethod
    def union_several_vals_by_regs(reg_list, val, union_str="，"):
        """
        - 提供正则匹配出多个值拼接
        """
        for c_re in reg_list:
            c_com = re.compile(c_re)
            c_value = union_str.join(c_com.findall(val))
            if c_value:
                val = c_value
                break
        return val

    def money_ending(self, value):
        str_bool = value.endswith('元')
        str_val = value + '整' if str_bool else value
        if u'\u4e00' <= str_val <= u'\u9fa5':
            try:
                value = cn2an.cn2an(str_val)
                self.multi_number = 1
            except (Exception,):
                pass
        return str(value)

    @staticmethod
    def format_tenderopen_time(bf_time):
        regs = [
            r'(?P<year>[\d\s]+?)[\u4e00-\u9fa5\-—－一](?P<month>[\d\s]+?)[\u4e00-\u9fa5\-—－一](?P<day>[\d\s]+?\d)[\u4e00-\u9fa5\s]+?(?P<hour>[\d\s]+?)[:：\u4e00-\u9fa5](?P<minute>[\d\s]+)',
            r'(?P<year>[\d\s]+?)[\u4e00-\u9fa5\-—－一](?P<month>[\d\s]+?)[\u4e00-\u9fa5\-—－一](?P<day>[\d\s]+?\d)[\u4e00-\u9fa5\s]+?(?P<hour>[\d\s]+?)[:：\u4e00-\u9fa5](?P<minute>[\d\s]+?)[:：\u4e00-\u9fa5](?P<seconds>[\d\s]+)',
        ]
        for reg in regs:
            com = re.compile(reg)
            ret = [m.groupdict() for m in re.finditer(com, bf_time)]

            if ret:
                date_dict = ret[0]

                left_info = {k: v.strip() for k, v in date_dict.items() if k in ['year', 'month', 'day']}
                right_info = {k: v.strip() for k, v in date_dict.items() if k in ['hour', 'minute', 'second']}

                bf_time = ' '.join(['-'.join(left_info.values()), ':'.join(right_info.values())]).replace('：', ':')

                if bf_time.strip():
                    break

        return bf_time

    @staticmethod
    def handle_multi_dot(value):
        """
        异常示例：1533.1646.61万元
        处理多个小数点的示例
        """
        val_list = value.split('.')
        if len(val_list) > 2:
            value = '.'.join([''.join(val_list[:-1]), val_list[-1]])

        return value

    @catch_title_before_method
    def clean_value(self):
        """
        - 对提取的字段数据进行清洗
            + 去除符号/替换空格为一个
            + bid_amount/budget_amount 处理万元/元
            + 特定字段 特殊字符串清理
        """
        # 多空格转化成单个
        self._value = KeywordsExtract.remove_chars_by_regs([r'\s+'], self._value, replace_str=' ')
        if self.field_name == 'tenderopen_time':
            _value = KeywordsExtract.format_tenderopen_time(self._value)
            self._value = KeywordsExtract.strQ2B(_value)
        if self.field_name in ['tenderee', 'bidding_agency', 'successful_bidder']:
            self._value = KeywordsExtract.remove_chars_by_regs(self.company_regulars, self._value)
            if len(''.join(self._value.split(' '))) <= 3:
                self._value = ''
        if self.field_name in ['bid_amount', 'budget_amount']:
            if self.is_isolated_unit():
                self._value = ''
                return

            self._value = KeywordsExtract.remove_chars_by_regs(self.amount_regulars, self._value)
            self._value = self.money_ending(self._value)
            self._value = KeywordsExtract.remove_rest_suffix(self._value)
            self._value = KeywordsExtract.handle_multi_dot(self._value)

            handled = True
            com = re.compile(r'([0-9 .]+)')
            if re.search('百万元|百万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 1000000))
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('千万元|千万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 10000000))
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('亿元|亿', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 100000000))
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('万元|万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 10000))
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('元', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip())))
                except (Exception,) as e:
                    self.msg = 'error:{0}'.format(e)
            else:
                handled = False

            # 匹配不到任何数值的内容置空
            if not re.search(r'\d+', self._value):
                self._value = ''

            # 数值最终值处理
            try:
                assert Decimal(self._value), '非数字'
            except (Exception,):
                pass
            else:
                self._value = '{}'.format(KeywordsExtract.remove_rest_zero(
                    self.multi_number * Decimal(self._value) if not handled else Decimal(self._value)))
                if Decimal(self._value) < 400:
                    self._value = ''
        if self.field_name == 'project_name':
            self._value = KeywordsExtract.remove_chars_by_regs(self.project_name_regulars, self._value)
            if not self._value:
                self._value = self.title
        if self.field_name == 'project_number':
            # 从标题中取
            if not self._value:
                for reg in self.project_number_from_title:
                    c_com = re.compile(r'%s' % reg)
                    pro_ns = c_com.findall(self.title)
                    if pro_ns:
                        self._value = pro_ns[0]
                        break
            self._value = KeywordsExtract.remove_chars_by_regs(self.project_number, self._value)
        if self.field_name in ['agent_contact', 'bidding_contact', 'project_leader']:
            # 符合正则列表的内容剔除
            self._value = KeywordsExtract.remove_chars_by_regs(self.liaison_regulars, self._value)
            # 提取N个联系人，通过逗号连接            
            self._value = KeywordsExtract.union_several_vals_by_regs(self.liaison_union_regulars, self._value)
        if self.field_name in ['contact_information', 'liaison', 'project_contact_information']:
            self._value = self.remove_chars_by_regs(self.contact_regulars, self._value)
            # N个联系方式
            self._value = KeywordsExtract.union_several_vals_by_regs(self.contact_union_regulars, self._value)
            if not re.findall(r'\d', self._value):  # 联系方式中没有数字清空
                self._value = ''
            # 联系方式不少于6个符号
            if len(self._value) < 6:
                self._value = ''
        # 最终结果去除特殊符号
        self._value = KeywordsExtract.remove_chars_by_regs(self.symbols_regulars, self._value)
        # 去除收尾连接符
        self._value = KeywordsExtract.remove_head_or_tail_symbols(self.head_tail_symbols_regulars, self._value)

    def get_value(self):
        self.reset_regular_by_field()  # 自定义字段正则列表覆盖默认正则列表
        self.done_before_extract()  # 多规则预先匹配
        self._extract_from_table()  # 表格数据
        self._extract_from_text()  # 默认规则匹配
        self.clean_value()  # 匹配结果清理
        return self._value.strip()


if __name__ == '__main__':
    content = """
        <div class="zw">
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 10.5pt; -ms-layout-grid-mode: char; -ms-text-autospace: ideograph-numeric; -ms-text-justify: inter-ideograph;">
            </p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <b><span
                        style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal; font-weight: bold;">
                        <font face="宋体">湖州市人才集团三号人才公寓设计方案</font>-施工图设计项目
                    </span></b><b><span
                        style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal; font-weight: bold;">(重新公告）</span></b><b><span
                        style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal; font-weight: bold;">
                        <font face="宋体">比选公告</font>
                    </span></b></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目编号：</font>330502-1719-0583
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目单位：湖州立城投资建设有限公司</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目名称：湖州市人才集团三号人才公寓设计方案</font>-施工图设计项目
                </span><span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">（</font>
                </span><span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">重新公告</font>
                </span><span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">）</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">招标项目建设地点：本项目拟对湖州市吴兴区高新技术产业园区内。</font>
                    <font face="宋体">工程规模：总用地面积</font>7亩，总建筑面积10602平方米，本项目总投约1000万元。
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">招标范围：</font> 1、设计阶段： 方案设计（包括方案优化）、施工图设计、施工配合服务等全过程设计工作。 2、设计服务范围：
                    中标单位实行设计总负责制，承担本项目各设计阶段过程中所有的专业设计工作。
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">服务周期：自合同签订之日起至最终设计成果获得相关部门确认或审批，协助发包人进行工程招标答疑，做好后期配合服务直至完成竣工验收。</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">中介机构资格要求：</font>1、在中华人民共和国境内注册的设计企业，具有独立法人资格；
                    2、投标人须具备工程设计综合资质或具备建筑装饰工程设计专项乙级及以上资质或建筑行业（建筑工程）设计甲级及以上资质（不接受联合体投标，浙江省外进浙企业须经备案）；
                    3、省外申请人必须持有浙江省住房和城乡建设厅出具的《外省勘察设计企业进入浙江省承接业务登记备案证明》；
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目负责人资格要求：须具备一级注册建筑师资格（浙江省外进浙拟参加投标项目负责人须经备案）</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">选取方式：公开比选</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">服务费用：</font> 700000元
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">选取时间：</font>2021年3月24日9时00分00秒（以电子交易平台时间为准）
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目业主联系人：杨若桢、崔伟平</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">项目业主咨询电话：</font>0572-2392963
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">代理公司联系人：毕艳利</font>
                </span></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 12pt; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;">
                    <font face="宋体">代理公司联系电话：</font>0572-2557282
                </span></p>
            <p
                style="margin: 0pt; text-align: justify; font-family: Calibri; font-size: 10.5pt; -ms-text-justify: inter-ideograph;">
            </p>
            <p></p>
            <p align="justify"
                style="background: rgb(255, 255, 255); margin: 0pt; padding: 0pt; text-align: justify; line-height: 200%; font-family: Calibri; font-size: 10.5pt; -ms-layout-grid-mode: char; -ms-text-autospace: ideograph-numeric; -ms-text-justify: inter-ideograph;">
                <span
                    style="background: rgb(255, 255, 255); color: rgb(51, 51, 51); text-transform: none; line-height: 200%; letter-spacing: 0pt; font-family: 宋体; font-size: 14pt; font-style: normal;"><br></span>
            </p>
            <div id="divDS_F954EF0D_82BC_4BEE_B5FF_904108DD4BE3" class="DSDiv"
                style="position: absolute; right:400px;top:900px"><img id="imgQianZhang_F954EF0D_82BC_4BEE_B5FF_904108DD4BE3"
                    alt="金业一 签于 2021/3/17 16:15:24"
                    src="http://49.4.49.208:8050/Hzztb/NetZtbMis/Pages/Signature/ShowQianZhang.aspx?Type=1&amp;RowGuid=F954EF0D-82BC-4BEE-B5FF-904108DD4BE3&amp;n=8"
                    width="150" height="150"></div><iframe width="980" style="border:0px;"
                src="http://49.4.53.110/HZfront/fwzx/CustomQyInfo/GGList.aspx?infoid=5153b879-0db0-41ba-b637-a78a7b8d0665"></iframe><br><a
                href="http://49.4.53.110/HZfront//AttachStorage/202103/J070/5153b879-0db0-41ba-b637-a78a7b8d0665/ZJWJ/毛坯建筑图.rar"
                target="_blank">毛坯建筑图.rar</a><br><a
                href="http://49.4.53.110/HZfront//AttachStorage/202103/J702/5153b879-0db0-41ba-b637-a78a7b8d0665/比选文件--湖州市人才集团三号人才公寓设计方案-施工图设计项目公开选取（重新招标）.docx"
                target="_blank">比选文件--湖州市人才集团三号人才公寓设计方案-施工图设计项目公开选取（重新招标）.docx</a><br>
            <br>

        </div>
    """

    # Clean
    area_id = "3309"
    br_cf = utils.init_yaml('before_regular', area_id)
    cr_cf = utils.init_yaml('common_regular', area_id)
    kw_cf = utils.init_yaml('keyword', area_id)
    pb_cf = utils.init_yaml('extra_regular', area_id, file_name='remove_chars')
    regular_params = {
        'br_cf': br_cf,
        'cr_cf': cr_cf,
        'pb_cf': pb_cf,
    }
    ke = KeywordsExtract(
        content, kw_cf['project_name'], field_name='project_name', area_id=area_id, title='[查看招标公告]:泰顺县中医院门诊预检导引系统招标公告',
        **regular_params
    )
    # ], field_name='project_name', area_id="3319", title='')
    # ke = KeywordsExtract(content, ["项目编号"])

    print(ke.get_value())
