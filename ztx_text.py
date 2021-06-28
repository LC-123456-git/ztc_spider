
# 备份 项目清洗解析代码
class KeywordsExtract:
    """
    根据若干个关键字 权衡匹配出对应的值 返回首个匹配结果
    规则：
        1.纯文本提取（默认）；
        2.html文档提取；
    """

    def __init__(self, content, keys, field_name, area_id=None):
        self.content = content
        self.keys = keys if isinstance(keys, list) else [keys]
        self.area_id = area_id
        self.field_name = field_name
        self.msg = ''
        self.keysss = ["招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称",  "工程名称", "项目名称", "成交价格",
                       "招标工程项目", "项目编号", "招标项目编号", "招标编号",
                       "招标人", "招 标 人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构",
                       "项目金额", "预算金额（元）", "招标估算价", "中标（成交）金额（元）", "联系人", "联 系 人",
                       "项目经理（负责人）"]
        # 各字段对应的规则
        self.fields_regular = {
            'project_name': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_number': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'budget_amount': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderee': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bidding_agency': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'liaison': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
            ],
            'contact_information': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
            ],
            'successful_bidder': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bid_amount': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderopen_time': [
                r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
            ],
        }
        self._value = ''

    def _regular_match(self, text, key):
        val = ''
        re_list = self.fields_regular.get(self.field_name, [])
        for rl in re_list:
            re_string = rl % key
            com = re.compile(re_string)
            result = com.findall(text)
            # val = ''.join(result)
            if result:
                val = ''.join(result[0]).strip()
            if val:
                break
        return val

    def _extract_from_text(self):
        if not self._value:
            for key in self.keys:
                try:
                    doc = etree.HTML(self.content)
                    txt_els = doc.xpath('//*//text()')
                    text = 'ψ'.join(txt_els)

                    self._value = self._regular_match(text, key)
                except Exception as e:
                    print(e)
                    self.msg = 'error:{0}'.format(e)
                if self._value:
                    break

    def is_horizon(self, t_data):
        """
        判断tr下td数是否相同
        """
        count = 0
        for i in t_data[:1]:
            if t_data[:1][i][0] in self.keysss:
                count += 1
        return True if count >= 2 else False


        # status = 1
        # try:
        #     doc = etree.HTML(table_content)
        #     tr_els = doc.xpath('//tr')
        #     tds = []
        #     for tr_el in tr_els:
        #         td_els = tr_el.xpath('./td') or tr_el.xpath('./th')
        #         tds.append(len(td_els))
        #     if len(set(tds)) == 1:
        #         status = 0
        # except Exception as e:
        #     print(e)
        # return status

    def _extract_from_table(self):
        if not self._value:
            for key in self.keys:
                try:
                    doc = etree.HTML(self.content)
                    table_els = doc.xpath('//table')

                    for table_el in table_els:
                        table_txt = etree.tounicode(table_el, method='html')
                        t_data = pandas.read_html(table_txt)
                        if t_data:
                            t_data = t_data[0]
                            t_dics = t_data.to_dict()
                            #  对比 纵向表格
                            count = 0
                            for i in t_data[:1]:
                                if t_data[:1][i][0] in self.keysss:
                                    count += 1
                            if count >= 2:
                                # 满足要求 的纵向表格
                                for _, t_dic in t_dics.items():
                                        t_dic_len = len(t_dic)
                                        if t_dic_len > 1:
                                            c_key = t_dic.get(0, '')
                                            for t in range(1, len(t_dic)):
                                                self._value = t_dic.get(t, '')
                                                com = re.compile(key)
                                                ks = com.findall(c_key)
                                                if ks:
                                                    if isinstance(self._value, float):
                                                        if math.isnan(self._value):
                                                            continue
                                                    return
                            count = 0
                            for t_data_key in t_data[0]:
                                if t_data_key in self.keysss:
                                    count += 1

                                # 横向的表格
                            if count >= 1:
                                c_index = 1
                                for _, t_dic in t_dics.items():
                                    tag = c_index % 2
                                    # 单数key  双数value
                                    if tag:  # 单数
                                        for t_index, td in t_dic.items():
                                            com = re.compile(key)
                                            ks = com.findall(td)
                                            if ks:
                                                c_key_dic = t_dics.get(c_index)
                                                self._value = c_key_dic.get(t_index)
                                                if isinstance(self._value, float):
                                                    if math.isnan(self._value):
                                                        continue
                                                return
                                    c_index += 1





                except Exception as e:
                    print(e)
                    self.msg = 'error:{0}'.format(e)

    def done_before_extract(self):
        """
        通用提取后，根据地区单独提取
        :param val:
        :return:
        """
        if self.area_id == '3320':  # 苍南
            pass

    def done_after_extract(self):
        """
        通用提取后，根据地区单独提取
        :param val:
        :return:
        """
        if self.area_id == '3320':  # 苍南
            if self.field_name == 'project_name' and not self._value:
                c_com = re.compile('本招标项目(.*?)[已由 , ，]')
                vals = c_com.findall(self.content)
                if vals:
                    self._value = vals[0]

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_text()
        self._extract_from_table()
        self.done_after_extract()  # 通用提取后各地区处理
        return self._value

