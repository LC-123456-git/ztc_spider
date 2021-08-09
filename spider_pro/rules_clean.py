# -*- coding:utf-8 -*-
import math
import re
import pandas
import copy
from lxml import etree
from decimal import Decimal
from html_table_extractor.extractor import Extractor

from spider_pro import utils

regular_plans = {
    # 0: "代\s*理[,|
    # ，]名\s*称.*盖\s*章.*[)|）][,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]",
    1: '代\s*理[,|，]名\s*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-+(.*)?|\d{11})[u4e00-u9fa5]',
    2: '代\s*理[,|，]名\s*称.*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    3: '代\s*理[,|，]名\s*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{5}[,|，]\d[,|，]\d{2}?|\d{11}?)[,|，]',
    4: '代\s*理[,|，]名\s*称[,|，].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    5: '名称[(|（].*盖章[)|）][,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    6: '招\s*标\s*代\s*理[,|，]名称[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    7: '代\s*理\s*机\s*构[:|：].*?[,|，](?P<tenderee>.*?)[,|，].*?联.*?系.*?人[:|：].*?[,|，](?P<liaison>.*?)[,|，].*?电.*?话[:|：].*?[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    8: '代\s*理\s*机\s*构\s*名\s*称[:|：].*?(?P<tenderee>.*?)[,|，].*?联.*?系.*?人[:|：].*?(?P<liaison>.*?)[,|，].*?电.*?话[:|：].*?(?P<contact_information>\d{4}-\d{6}[,|，]\d{2}?|\d{11}?)[,|，]',
}


def get_keys_value_from_content_ahead(content: str, keys, area_id="00", _type="", field_name=None, title=None):
    # keys 需要清洗字段名称  例：招标人、项目编号等
    if area_id == "00":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                else:
                    return ""
        except Exception as e:
            return ""

    elif area_id in ["3300", '3306', '3307', '3313', '3331', '3334']:  # 3305
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id, title=title)
        # ke.fields_regular = {
        #     'bidding_agency': [
        #         # r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+.*?)ψψ',
        #         r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+.*?)ψψ'
        #     ]
        # }
        return ke.get_value()

    # elif area_id == "3306":
    # # 还需优化
    #     try:
    #         if isinstance(keys, str):
    #             keys_str_list = [keys]
    #         elif isinstance(keys, list):
    #             keys_str_list = keys
    #         else:
    #             return ""
    #         contents = content.replace("</td>", " </td>")
    #         for key in keys_str_list:
    #             # 先判断content中 是否包含key的文本
    #             if len(key) == 0 or not content or not key:
    #                 continue
    #             if re.search(fr"{key}", content):
    #                 all_results = re.findall(fr"{key}\s+?(.*?)[(|（]", contents)
    #                 if all_results:
    #                     for item in all_results:
    #                         value = re.findall('<.*>(.*?)</.*>', item)[0]
    #                         if value.strip():
    #                             return value.strip()
    #                             # print({key}, ":  ", value.strip())
    #                 all_results = re.findall(fr"{key}[:|：].*?</.*?>", contents)
    #                 if all_results:
    #                     for item in all_results:
    #                         if item.split(":")[-1].split("：")[-1]:
    #                             value = re.findall('<.*>(.*)</.*>', item.split(":")[-1].split("：")[-1])[0]
    #                         else:
    #                             value = item.split(":")[-1].split("：")[-1].split("<")[0]
    #                         if value.strip():
    #                             return value.strip()
    #                             # print({key}, ":  ", value.strip())
    #                         # tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
    #                         # if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
    #                         #     value = value_str.group().split(">")[-2].split("</")[0]
    #                         #     if value.strip():
    #                         #         print(value.strip())
    #
    #                 # # 匹配带空格开始的文本内容
    #                 # all_results = re.findall(fr"{key}\s+?<", contents)
    #                 # if all_results:
    #                 #     for item in all_results:
    #                 #         value_list = item.split(" ")
    #                 #         for v_item in value_list:
    #                 #             if v_item.strip():
    #                 #                 return v_item.strip()
    #
    #                 all_results = re.findall(fr"{key}</.*?>", contents)
    #                 if all_results:
    #                     for item in all_results:
    #                         tag = item.split("</")[-1].split(">")[0]
    #                         if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", contents):
    #                             value = value_str.group().split(">")[-2].split("</")[0]
    #                             if value.strip():
    #                                 return value.strip()
    #                 all_results = re.findall(fr"{key}.*?</.*>\s*<.*>.*?</.*>", contents)
    #                 if all_results:
    #                     for itme in all_results:
    #                         if re.findall(fr'{key}[:|：](.*?)<', itme):
    #                             value = re.findall(fr'{key}[:|：](.*?)<', itme)[0]
    #                             if value.strip():
    #                                 return value.strip()
    #                         else:
    #                             value = ''.join(re.findall('<.*>(.*?)</.*>', itme)[-1]).strip()
    #                             if value.strip():
    #                                 return value.strip()
    #                 all_results = re.findall(fr"{key}\s*(.*?)[)|）]", contents)
    #                 if all_results:
    #                     for item in all_results:
    #                         value = re.findall("</.*>(.*)<.*>", item)[0]
    #                         if value.strip():
    #                             return value.strip()
    #
    #         return ""
    #     except Exception as e:
    #         print(e)

    elif area_id == '52':
        utils.match_key_words(content, regular_plans)
    # elif area_id == '3305':
    #     if isinstance(keys, str):
    #         keys_str_list = [keys]
    #     elif isinstance(keys, list):
    #         keys_str_list = keys
    #     else:
    #         return ""
    #
    #     for key in keys_str_list:
    #         # print({key}, ': ')
    #         # 先判断content中 是否包含key的文本
    #         if len(key) == 0 or not content or not key:
    #             continue
    #         if re.search(fr"{key}", content):
    #             # 匹配带冒号开始的文本内容
    #             all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
    #             if all_results:
    #                 for item in all_results:
    #                     value = item.split(":")[-1].split("：")[-1].split("<")[0]
    #                     if value.strip():
    #                         return value.strip()
    #                     tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
    #                     if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
    #                         value = value_str.group().split(">")[-2].split("</")[0]
    #                         if value.strip():
    #                             return value.strip()
    #
    #             # 匹配带空格开始的文本内容
    #             all_results = re.findall(fr"{key}\s+?<", content)
    #             if all_results:
    #                 for item in all_results:
    #                     value_list = item.split(" ")
    #                     for v_item in value_list:
    #                         if v_item.strip():
    #                             return v_item.strip()
    #
    #             # 匹配不带任何开始标记的文本内容
    #             all_results = re.findall(fr"{key}</.*?>", content)
    #             if all_results:
    #                 for item in all_results:
    #                     tag = item.split("</")[-1].split(">")[0]
    #                     if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
    #                         value = value_str.group().split(">")[-2].split("</")[0]
    #                         if value.strip():
    #                             return value.strip()
    #
    #             # 匹配table里面有前后两个td的文本内容
    #             all_results = re.findall(fr"{key}</.*?>(.*?)</.*>", content)
    #             if all_results:
    #                 for item in all_results:
    #                     value = item.split(">")[-1].split(">")[0]
    #                     if value.strip():
    #                         return value.strip()
    #
    #
    #         # if key == '项目名称' or key == '招标项目':
    #         #     regular_plan = {
    #         #         1: '招\s*标\s*项\s*目\s*[,|，](?P<{}>.*?)[,|，]'.format(keys),
    #         #         2: '工\s*程\s*名\s*称\s*(?P<{}>.*[u4e00-u9fa5].*?)[,|，]'.format(keys),
    #         #         3: '项\s*目\s*名\s*称[:|：]\s*[,|，](?P<{}>.*?)[,|，]'.format(keys),
    #         #     }
    #         # else:
    #         #     regular_plan = ''
    #         # utils.match_key_re(content, regular_plan, keys)
    #         #
    #         # return ""
    elif area_id == "02":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "03":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                for cont in content:
                    if re.search(fr"{key}", cont):
                        # 匹配带冒号开始的文本内容
                        all_results = re.findall(fr"{key}[:|：].*?</.*?>", cont)
                        if all_results:
                            for item in all_results:
                                value = item.split(":")[-1].split("：")[-1].split("<")[0]
                                if value.strip():
                                    return value.strip()
                                tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                                if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", cont):
                                    value = value_str.group().split(">")[-2].split("</")[0]
                                    if value.strip():
                                        return value.strip()

                        # 匹配带空格开始的文本内容
                        all_results = re.findall(fr"{key}\s+?<", cont)
                        if all_results:
                            for item in all_results:
                                value_list = item.split(" ")
                                for v_item in value_list:
                                    if v_item.strip():
                                        return v_item.strip()

                        # 匹配不带任何开始标记的文本内容
                        all_results = re.findall(fr"{key}</.*?>", cont)
                        if all_results:
                            for item in all_results:
                                tag = item.split("</")[-1].split(">")[0]
                                if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", cont):
                                    value = value_str.group().split(">")[-2].split("</")[0]
                                    if value.strip():
                                        return value.strip()

                return ""
        except Exception as e:
            print(e)
            return ""
    elif area_id == "04":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "05":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "08":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "11":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "13":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "15":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "19":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "23":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            return ""
    elif area_id == "26":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue

                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                return ""
        except Exception as e:
            print(e)
            return ""
    elif area_id == "1102":
        pass
    elif area_id == "3301":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue

                if re.search(fr"{key}", content):
                    # # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    # print(v_item.strip())
                                    return v_item.strip()

                    # 匹配带表格标记的文本内容
                if re.findall(fr"</td>", content):
                    data_dict = {}
                    doc = etree.HTML(content)
                    content_list = doc.xpath("//div[@class='WordSection1']//tr//text()")

                    if not content_list:
                        content_list = doc.xpath("//div[@class='Section0']//text()")
                        if "工程概况" in content_list:
                            content_list.remove("工程概况")
                        b_list = content_list[1::2]
                        c_list = content_list[0::2]
                        for i, t in zip(b_list, c_list):
                            data_dict[t] = i
                        for keys in keys_str_list:
                            value = data_dict.get(keys)
                            if value:
                                if re.search("万元", keys):
                                    value = str(Decimal(value) * 10000)
                                return value
                        return value
                    else:
                        a_list = []
                        content_list = re.sub("\n", "", "".join(content_list))
                        content_list = content_list.strip().split(" ")
                        for item in content_list:
                            if re.search(("\S+"), item):
                                a_list.append(item)
                        item_str = "ψ".join(a_list)
                        for keys in keys_str_list:
                            if info_list := re.search("{}ψ(\w+?)ψ".format(keys), item_str):
                                info_list = info_list.group().split("ψ")
                                key = info_list[0]
                                value = info_list[1]
                                if key == "开标时间":
                                    if not re.search("\d+/\d+/\d+ \d+:\d+:\d+", value):
                                        return ""
                                return value

                        #         b_list = a_list[1::2]
                        #         c_list = a_list[0::2]
                        #         for i, t in zip(b_list, c_list):
                        #             data_dict[t] = i
                        # for keys in keys_str_list:
                        #     value = data_dict.get(keys)
                        #     if value:
                        #         if re.search("万元", keys):
                        #             value = str(Decimal(value) * 10000)
                        #         return value
                        # return value


            ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id)
            ke.fields_regular = {
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
            return ke.get_value()
        except Exception as e:
            print("清洗出错")
            print(e)
            return ""
    elif area_id == "3302":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                # 匹配带冒号开始的文本内容
                data_dict = {}
                doc = etree.HTML(content)
                # 如果是意向采购需求
                if doc.xpath(
                        "//table[@class='template-bookmark uuid-1609312554335 code-publicNoticeOfPurchaseIntentionDetailTable text-意向公开明细']"):
                    title_header = doc.xpath("//th//text()")
                    sectionNo_list = doc.xpath("//td[@class='code-sectionNo']//text()")
                    purchaseProjectName_list = doc.xpath("//td[@class='code-purchaseProjectName']//text()")
                    purchaseRequirementDetail_list = doc.xpath("//td[@class='code-purchaseRequirementDetail']//text()")
                    budgetPrice_list = doc.xpath("//td[@class='code-budgetPrice']//text()")
                    estimatedPurchaseTime_list = doc.xpath("//td[@class='code-estimatedPurchaseTime']//text()")
                    if len(sectionNo_list) > 1:
                        p_Name = ";".join(purchaseProjectName_list)
                        p_Detail = ";".join(purchaseRequirementDetail_list)
                        p_Time = ";".join(estimatedPurchaseTime_list)
                        Price = str(sum(list(map(int, budgetPrice_list))) / 10000)
                        data_dict[title_header[1]] = p_Name
                        data_dict[title_header[2]] = p_Detail
                        data_dict[title_header[3]] = Price
                        data_dict[title_header[4]] = p_Time
                    else:
                        p_Name = purchaseProjectName_list[0]
                        p_Detail = purchaseRequirementDetail_list[0]
                        p_Time = estimatedPurchaseTime_list[0]
                        Price = budgetPrice_list[0]
                        data_dict[title_header[1]] = p_Name
                        data_dict[title_header[2]] = p_Detail
                        data_dict[title_header[3]] = str(int(Price) / 10000)
                        data_dict[title_header[4]] = p_Time
                    for keys in keys_str_list:
                        value = data_dict.get(keys)
                        if value:
                            return value
                    # print(title_header)

                ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id)
                ke.fields_regular = {
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
                return ke.get_value()

                # 匹配带表格标记的文本内容
                # if re.findall(fr"</td>", content):
                #     data_dict = {}
                #     doc = etree.HTML(content)
                #     content_list = doc.xpath("//div[@class='WordSection1']//tr//text()")
                #
                #     if not content_list:
                #         content_list = doc.xpath("//div[@class='Section0']//text()")
                #         content_list.remove("工程概况")
                #         b_list = content_list[1::2]
                #         c_list = content_list[0::2]
                #         for i, t in zip(b_list, c_list):
                #             data_dict[t] = i
                #         for keys in keys_str_list:
                #             value = data_dict.get(keys)
                #             if value:
                #                 return value
                #     else:
                #         # content_list.remove("工程概况")
                #         a_list = []
                #         for item in content_list:
                #             if re.search(("\S+"), item):
                #                 a_list.append(item)
                #                 b_list = a_list[1::2]
                #                 c_list = a_list[0::2]
                #                 for i, t in zip(b_list, c_list):
                #                     data_dict[t] = i
                #                 for keys in keys_str_list:
                #                     value = data_dict.get(keys)
                #                     if value:
                #                         return value
                # info_list = content_str.split("\n  \n \n \n  \n  ")
                # for keys in keys_str_list:
                #     for item in info_list:
                #         data_dict[item.split("\n  \n  \n  ")[0]] = item.split("\n  \n  \n  ")[1]
                #         value = data_dict.get(keys)
                #         if value:
                #             return value
                # return value

                # data_dict = {}
                # doc = etree.HTML(content)
                # content_str = doc.xpath("//div[@class='MainList']/div[2]/div//text()")
        except Exception as e:
            print("清洗出错")
            print(e)
            return ""
    elif area_id == "3303":
        # TODO 还需优化
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue

                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()
                    # 匹配table里面有前后两个td的文本内容
                    all_results = re.findall(fr"{key}</.*?>(.*?)</.*>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(">")[-1].split(">")[0]
                            if value.strip():
                                return value.strip()

                return ""
        except Exception as e:
            print(e)
            return ""
    elif area_id in ["3309", "3320", "3319", "3326"]:
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id, title=title)
        ke.fields_regular = {
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
        }
        return ke.get_value()
    elif area_id == "3333":
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</p>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                    if re.findall(fr"</table>", content):
                        data_dict = {}
                        doc = etree.HTML(content)
                        content_list = doc.xpath("//*[@id='zoom']/table//text()")
                        b_list = content_list[1::2]
                        c_list = content_list[0::2]
                        for i, t in zip(b_list, c_list):
                            data_dict[t] = i
                        for keys in keys_str_list:
                            value = data_dict.get(keys)
                            if value:
                                return value.strip()
            return ""
        except Exception as e:
            return ""
    else:
        try:
            if isinstance(keys, str):
                keys_str_list = [keys]
            elif isinstance(keys, list):
                keys_str_list = keys
            else:
                return ""

            for key in keys_str_list:
                # 先判断content中 是否包含key的文本
                if len(key) == 0 or not content or not key:
                    continue
                if re.search(fr"{key}", content):
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(":")[-1].split("：")[-1].split("<")[0]
                            if value.strip():
                                return value.strip()
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()

                    # 匹配table里面有前后两个td的文本内容
                    all_results = re.findall(fr"{key}</.*?>(.*?)</.*>", content)
                    if all_results:
                        for item in all_results:
                            value = item.split(">")[-1].split(">")[0]
                            if value.strip():
                                return value.strip()

                return ""
        except Exception as e:
            return ""


class KeywordsExtract:
    """
    根据若干个关键字 权衡匹配出对应的值 返回首个匹配结果
    规则：
        1.纯文本提取（默认）；
        2.html文档提取；
    """

    def __init__(self, content, keys, field_name, area_id=None, title=None):
        """
        Args:
            content ([string]): [文章内容]
            keys ([list]): [关键字列表]
            field_name ([string]): [指定匹配字段]
            area_id ([string], optional): [地区ID]. Defaults to None.
        """
        self.content = content
        self.keys = keys if isinstance(keys, list) else [keys]
        self.area_id = area_id
        self.field_name = field_name
        self.title = title
        self.msg = ''
        self.field = ['bidding_contact', 'liaison', 'agent_contact', 'contact_information']
        self.table_name_list = []
        self.keysss = [
            "招标联系人", "代理机构", "招标代理:", "招标单位", "招标代理机构", "中标单位", "建设单位", "招标联系人", "单位名称", "招标人",
            "招标项目", "中标供应商名称", "工程名称", "项目名称", "招标工程项目",
            "项目编号", "招标项目编号", "标段编号", "招标编号",
            "中标（成交）金额(元)", "成交价格", "项目金额", "预算金额（元）", "招标估算价", "投资总额(万元)", '中交价格(万元)',
            "中标（成交）金额（元）", "中标价", "预算金额（元）", "退付类型", "投标报价（元）", "中标价（元）",
            "发布时间", "成交时间", "工期", "开标时间",
            "联系人", "项目经理（负责人）", "公告号", "竞得人", "序号", "备注"
        ]
        # 各字段对应的规则
        self.fields_regular = {
            'project_name': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_number': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'budget_amount': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderee': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bidding_agency': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'liaison': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'contact_information': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'successful_bidder': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bid_amount': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'tenderopen_time': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_leader': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'project_contact_information': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'agent_contact': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
            'bidding_contact': [
                r'%sψ?[^ψ ：:。，,、”“"]?[: ：]\s*?[ψ]*?([^ψ]+?)ψ',
            ],
        }
        self.fields_regular_with_symbol = copy.deepcopy(self.fields_regular)
        self._value = ''
        # 倍数
        self.multi_number = 1

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
            if result:
                val = result[0]
            else:
                val = ''
            if val:
                if with_symbol:
                    self.reload_multi_number(key)
                else:
                    self.reload_multi_number(val)
                break
        return val

    def validate_fields(self):
        """
        - 符合条件的格式化结果
        """
        if self.field_name == 'project_name':
            pass
        if self.field_name == 'tenderee':
            pass
        if self.field_name == 'bidding_agency':
            pass
        if self.field_name == 'project_number':
            pass
        if self.field_name == 'budget_amount':
            pass
        if self.field_name == 'bid_amount':
            pass
        if self.field_name == 'contact_information':                  # 招标代理联系方式
            pass
        if self.field_name == 'liaison':                              # 招标人联系方式
            pass
        if self.field_name == 'project_leader':                       # 项目负责人
            pass
        if self.field_name == 'project_contact_information':          # 项目负责人联系方式
            pass

    def _extract_from_text(self, with_symbol=True):
        """
        纯文本中提取字段值
        Args:
            with_symbol (bool, optional): [文本是否通过符号切分]. Defaults to True.
        """
        if not self._value:
            for key in self.keys:
                try:
                    doc = etree.HTML(self.content.replace('&nbsp;', ''))
                    txt_els = [x.strip() for x in doc.xpath('//*//text()')]
                    text = 'ψ'.join(txt_els) if with_symbol else ''.join(txt_els).replace(' ', '')

                    self._value = self._regular_match(text, key, with_symbol=with_symbol)
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)

                if self._value:
                    # 判断当前字段是否具备字段的约束条件/或者做相应的字符调整
                    self.validate_fields()
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
        except Exception as e:
            self.msg = 'error:{0}'.format(e)
        else:
            for t_data_key in t_data:
                try:
                    t_data_key = ''.join(t_data_key.split()).replace(':', '').replace("：", "")
                except:
                    t_data_key = ''
                if t_data_key in self.keysss:
                    count += 1
        return True if count >= 2 else False

    def is_vertical(self, t_data):
        """
        判断 tr下只有一个 td 或者 th
        """
        try:
            count = 0
            for i in t_data[:1]:
                if t_data[:1][i][0] in self.keysss:
                    count += 1
            return True if count >= 2 else False
        except Exception as e:
            print(e)

    @staticmethod
    def get_child_tables(doc_el):
        return doc_el.xpath('.//table')

    @staticmethod
    def get_h_val(c_index, key, tr):
        c_index += 1
        try:
            next_val = ''.join(tr[c_index].split())
        except Exception as e:
            print(e)  # get lost
        else:
            if next_val == key:
                next_val = KeywordsExtract.get_h_val(c_index, key, tr)

            return next_val

    def get_val_from_table(self, result, key):
        for tr in result:
            for c_index, td in enumerate(tr):
                try:
                    td = ''.join(td.split())
                except:
                    td = ''
                if td == key:
                    # next
                    next_val = KeywordsExtract.get_h_val(c_index, key, tr)
                    if next_val:
                        self.reload_multi_number(key)
                        return next_val
        return ''

    def recurse_parse_table(self, table_els, key, doc):
        c_doc = copy.deepcopy(doc)
        for table_el in table_els:
            c_child_tables = KeywordsExtract.get_child_tables(table_el)

            # REMOVE CHILD TABLE
            for c_child_table in c_child_tables:
                c_child_table.getparent().remove(c_child_table)

            # REMOVE TR WITHOUT HEIGHT
            trs_without_height = table_el.xpath('.//tr[contains(@style, "line-height:0px")]')
            for tr in trs_without_height:
                tr.getparent().remove(tr)

            table_txt = etree.tounicode(table_el, method='html')
            try:
                t_data = pandas.read_html(table_txt)[0]
            except Exception as e:
                self.msg = 'error:{0}'.format(e)
            else:
                # 判断横向|纵向
                # tr下td数一致     横向
                # tr下td数不一致    纵向
                key = ''.join(key.split())
                extractor = Extractor(table_txt.replace('\n', ''))
                extractor.parse()
                result = extractor.return_list()
                if self.is_horizon(t_data):
                    self._value = self.get_val_from_table(result, key)
                else:
                    result = list(zip(*result))
                    self._value = self.get_val_from_table(result, key)
                if self._value:
                    return True
            child_tables = KeywordsExtract.get_child_tables(table_el)
            if child_tables:
                self.recurse_parse_table(child_tables, key, c_doc)
        return False

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
        """
        if self.field_name == 'project_name' and self.title:
            project_priority = ['项目', '工程', '转让', '出租', '转租', '拍卖', '出让', '公告', '公示']
            for name in project_priority:
                if name in self.title:
                    # 判断项目关键字是否在（）【】 [] 内
                    if self.brackets_contained(name):
                        continue
                    self._value = ''.join([self.title.split(name)[0], name])
                    break
                else:
                    self._value = self.title

    def done_before_extract(self):
        """
        通用提取前，根据地区单独提取
        :param val:
        :return:
        """

        if self.area_id == '3309':  # 温州
            self.get_val_from_title()
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'budget_amount':  # 本工程预算金额约为479万元。
                    regular_list = [
                        r'投资金额约\s*(\d+\s*万元)',
                        r'预算金额.*?为\s*(\d+\s*万元)',
                        r'预算金额.*?为\s*(\d+\.\d+?万元)',
                        r'预算金额.*?为\s*(\d+\s*元)',
                        r'本工程投资约\s*(\d+\s*万元)',
                        r'本工程投资约\s*(\d+\.\d+?万元)',
                        r'本工程投资约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\.\d+?万元)',
                        r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联\s*系\s*人[: ：]\s*([\u4e00-\u9fa5]+?)\s*[联 电 质]',
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3320':  # 苍南
            self.get_val_from_title()
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []

                if self.field_name == 'project_name':
                    regular_list = [
                        r'本招标项目([^，,]*?)[已由 , ，]',
                        r'项目名称：([0-9 \s \u4e00-\u9fa5]+?)三',
                        r'根据(.*?)（[\s \u4e00-\u9fa5]*?编号：',
                        r'本工程项目名称\s*([^，,]*?)\s*[。 , ，]',
                        r'就([0-9 \s \u4e00-\u9fa5]+?)进行招标',
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                        r'招标人([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                        r'项目业主为([\s \u4e00-\u9fa5]*?)（下称招标人）',
                        r'受([\s \u4e00-\u9fa5]*?)委托',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理[机构]*：([\s \u4e00-\u9fa5]*?)地',
                        r'委托([^，,。]*?)[进行 , ，]',
                        r'公告([\s \u4e00-\u9fa5]*?)受',
                    ]
                if self.field_name == 'project_number':  # 项目代码：2020-330327-48-01-167360）批准建  目（编号：A3303270480001353001001）招标文件（以
                    regular_list = [
                        r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':  # 本工程预算金额约为479万元。
                    regular_list = [
                        r'投资金额约\s*(\d+\s*万元)',
                        r'预算金额.*?为\s*(\d+\s*万元)',
                        r'预算金额.*?为\s*(\d+\.\d+?万元)',
                        r'预算金额.*?为\s*(\d+\s*元)',
                        r'本工程投资约\s*(\d+\s*万元)',
                        r'本工程投资约\s*(\d+\.\d+?万元)',
                        r'本工程投资约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\.\d+?万元)',
                        r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)传',
                        r'电话[: ：]\s*?([0-9 \-]+?)\s*?[\u4e00-\u9fa5 \s]',
                        # r'联系电话：0577-68885883，135661051925',
                        r'联系电话：([0-9 \-]+?)[, ，]',
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联.*?系.*?人[: ：]\s*([\u4e00-\u9fa5]+?)[监督投诉 电]',
                        r'异议受理部门[: ：]\s*([\u4e00-\u9fa5]+)联',
                        r'联系人[: ：]\s*([\u4e00-\u9fa5]+)5',
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3319':  # 长兴
            self.get_val_from_title()
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []

                if self.field_name == 'project_name':
                    regular_list = [
                        r'概况[：:]([\u4e00-\u9fa5 \s]*?项目)[， ,]',
                        r'([\u4e00-\u9fa5（）、]+?)经批准同意建设，',
                        r'项目名称[：:]([0-9\u4e00-\u9fa5\(（]+?）)'
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构为([\u4e00-\u9fa5]+?)[, ， 。]',
                    ]
                if self.field_name == 'project_number':
                    regular_list = [
                        r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':
                    # 概算总造价约326万元
                    regular_list = [
                        r'预算约\s*(\d+\s*万元)',
                        r'预算约\s*(\d+\.\d+?万元)',
                        r'预算约\s*(\d+\s*元)',
                        r'投资估算约\s*(\d+\s*万元)',
                        r'投资估算约\s*(\d+\.\d+?万元)',
                        r'投资估算约\s*(\d+\s*元)',
                        r'概算总造价约\s*(\d+\s*万元)',
                        r'概算总造价约\s*(\d+\.\d+?万元)',
                        r'概算总造价约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\.\d+?万元)',
                        r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'电话[: ：]([^\u4e00-\u9fa5]+?)2021年5月12日',
                        r'电话[: ：]([^\u4e00-\u9fa5]+?)9.3监督机构',
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)[\u4e00-\u9fa5]',
                        r'联\s*系\s*人：[\u4e00-\u9fa5]+?\s*([0-9 \-]+?)\s*[\u4e00-\u9fa5]',
                        r'咨询[:：][\u4e00-\u9fa5]*?([\- 0-9 \s]+?)标的',
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联\s*系\s*人[: ：]\s*([\u4e00-\u9fa5]+?)[联 电 质]',
                        r'项目经理：([\u4e00-\u9fa5]+?)\s*质量',
                        r'咨询[:：]([\u4e00-\u9fa5]*?)\d+',
                    ]
                if self.field_name == 'successful_bidder':
                    # 中标人：长兴宇诚建设有限公司 中标价：597912元 工期
                    regular_list = [
                        r'中标人[: ：]\s*([\u4e00-\u9fa5]+)\s*中标价',
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3326':
            self.get_val_from_title()
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []

                if self.field_name == 'project_name':
                    regular_list = [
                        r'本招标项目([^，,]*?)[已由 , ，]',
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招\s*标\s*人[:：]([\u4e00-\u9fa5 （ ）]+?)\s*招标',
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',

                        r'招标单位([[\u4e00-\u9fa5]*?)确认以下单位为中标单位',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'project_number':
                    # 招标编号：LYXHZZ2021-056 1. 招标条件
                    regular_list = [
                        r'项目代码[: ：\s]*([0-9 \-]*?)[^\d+-]',
                        r'招标[序编]号[：:]([0-9 A-Z a-z \- \s \u4e00-\u9fa5]+?)1[\.,、]\s*招标',
                        r'编号[：:]([0-9 A-Z a-z \- \s]+?)[\)\(（）]',
                        r'项目编号[：:]([0-9 A-Z a-z \- \s]*?)[\u4e00-\u9fa5]{1}',
                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'投资限额约\s*(\d+\s*万元)',
                        r'预算造价约\s*([0-9 \.]+?\s*亿元)',
                        r'预算价：审定价\s*([0-9 \.]+?\s*元)',
                        r'预算价\s*([0-9 \.]+?\s*元)',
                        # r'预算约\s*(\d+\s*万元)',
                        # r'预算约\s*(\d+\.\d+?万元)',
                        # r'预算约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'暂定\s*(\d+\s*元)',
                        # r'中标价[: ：]\s*(\d+\.\d+?万元)',
                        # r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'联系电话：([0-9 \- \s]+)（代理机构）',
                        r'联系电话：[0-9 \- \s]+（县监管办督查科）([0-9 \- \s]+)（代理机构）',
                        r'电\s*话[:：]([^\u4e00-\u9fa5]+?)[\u4e00-\u9fa5。，,\(（]',
                    ]
                if self.field_name == 'liaison':
                    # 联系人：叶工　 联系电话
                    regular_list = [
                        r'联\s*系\s*人[: ：]\s*([\u4e00-\u9fa5 \s]+?)[联 电 质]',
                    ]
                if self.field_name == 'successful_bidder':
                    regular_list = [
                        r'中标单位[: ：]\s*([\u4e00-\u9fa5]+)\s*项目',
                        # r'中标人[: ：]\s*([\u4e00-\u9fa5]+)\s*中标价',
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == "3305":
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'project_number':                          # 项目编号
                    regular_list = [
                        r'公示编号[: ：]{0,1}(.*?)土地',
                    ]
                elif self.field_name == 'bidding_agency':                          # 招标代理
                    regular_list = [
                        r'招标代理的名称和地址[: ：]\s*.* ?室(.*?[(司)(单位)])[\u4e00-\u9fa5]',
                        r'代理名称[: ：]{0,1}[( （]盖章[) ）]\s*(.*?)联系地址',
                        r'采购代理机构信息名称[: ：]{0,1}\s*(.*?)地址',

                    ]
                elif self.field_name == "project_name":                            # 项目名称
                    regular_list = [
                        r"项目名称[: ：]{0,1}(.*?)[项目|宗|交易登记]",
                    ]
                elif self.field_name == "tenderee":                                 # 招标人
                    regular_list = [
                        r'业主的名称和办公室地址[：:].*?[: ：]\s*(.*?[(室) (单位)])[\u4e00-\u9fa5]',
                        r'单位名称[( （]盖章[) ）][: ：]{0,1}\s*(.*?)地点',
                        r'采购人信息名称[: ：]{0,1}\s*(.*?)地址',

                    ]
                elif self.field_name == "bid_amount":                               # 中标金额
                    regular_list = [
                        r'成交价格[: ：]{0,1}(.*?)[\u4e00-\u9fa5]',
                        r'中标价[: ：]{0,1}\s*¥(.*[元 万元])?[( （][\u4e00-\u9fa5]',
                        r'成交总价[: ：]{0,1}(.*?)三'
                    ]
                elif self.field_name == "successful_bidder":                         # 中标方
                    regular_list = [
                        r'受让人名称[: ：]{0,1}(.*?)成交'
                    ]
                elif self.field_name == 'contact_information':                       # 联系方式
                    regular_list = [
                        r'联\s*系\s*电\s*话\s*[: ：]{0,1}(.*?)[\u4e00-\u9fa5]',
                        r'电\s*话[: ：]{0,1}\s*(.*?)[\u4e00-\u9fa5]'
                    ]
                if self.field_name == "liaison":                                   # 联系人
                    regular_list = [
                        r'联\s*系\s*方\s*式[: ：]{0,1}(.*?)\d',
                        r'联\s*系\s*人\s*[: ：]{0,1}(.*?)[联\s*系\s*电\s*话 , ， 电话]',

                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'估\s*算\s*价\s*.*?(\d+\.\d+\s*[元 万元])[\u4e00-\u9fa5]',
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3306':
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'bidding_agency':  # 招标代理
                    regular_list = [
                        r'代理机构\s*[: ：](.*?)[联系人 地址]',
                        r'采购代理机构信息名 称\s*[: ：](.*?)地\s*址',
                        r'代理机构联系方式\s*[: ：](.*?)联系人',
                        r'报名.*?发售地点\s*[: ：](.*?)[( （]',
                        r'招标代理\s*[: ：](.*?)地',
                        r'代理名称[( （]盖章[) ）]\s*(.*?)联系地址',
                        # r'名称\s*[: ：](.*?)'
                    ]
                elif self.field_name == 'project_number':  # 项目编号
                    regular_list = [
                        r'项目编号\s*[: ：](.*?)[\u4e00-\u9fa5]',
                        r'项目编号\s*[: ：](.*?)[二 三]'
                    ]
                elif self.field_name == "project_name":  # 项目名称
                    regular_list = [
                        r'工程名称\s*[: ：]{0,1}(.*?)工程情况',
                        # r'项目名称\s*[: ：]{0,1}(.*?)\d',
                        r'项目名称\s*[: ：]{0,1}(.*?)[二、 三、]',
                        r'项目名称\s*[: ：]{0,1}(.*?)[\u4e00-\u9fa5]',
                    ]
                elif self.field_name == "tenderee":  # 招标人
                    regular_list = [
                        r'采购单位\s*[: ：](.*?)招标代理',
                        r'招标单位\s*[: ：](.*?)[联系人 五]',
                        r'受(.*?[公司|委员会|单位|合作社])的{0,1}委托',
                        r'招标人联系方式\s*[: ：](.*?)联系人',
                        r'招标方联系方式\s*[: ：](.*?)联系人',
                        r'招标人\s*[: ：](.*?)联',
                        r'招标人(.*)工程规模',
                        # r'联系人[: ：](.*?)联',
                        r'单位名称[( （]盖章[) ）]\s*(.*?)地点',
                        r'招标人名称[（ (]盖章[) ）](.*?)联系地址'
                    ]
                elif self.field_name == "liaison":  # 联系人
                    regular_list = [
                        r'联系人\s*（.*?）[: ：](.*?)项目',
                        r'联系人\s*[: ：](.*?)[联系电话 , ， 电话]',
                        r'联\s*系\s*人\s*(.*?)[联\s*系\s*电\s*话 , ， 电话]',
                        # r'联系人\s*[: ：](.*?)[, ，]',
                        # r'联系人\s*[: ：](.*?)联系电话',
                    ]
                elif self.field_name == "bid_amount":  # 中标金额
                    regular_list = [
                        r'项目估算金额\s*[: ：](.*?)。'
                    ]
                elif self.field_name == 'contact_information':  # 联系方式
                    regular_list = [
                        r'电话([0-9 \- \s*]+?)[\u4e00-\u9fa5]',
                        r'电话[: ：]([0-9 \-]+?)[\u4e00-\u9fa5]',
                        r'联系人.*?联系电话\s*[: ：](.*?)传',
                        r'联系电话\s*[: ：](.*?)[, ，]',
                        r'联系电话\s*[: ：](.*?)[\u4e00-\u9fa5]',
                        r'联\s*系\s*电\s*话\s*(.*?)[\u4e00-\u9fa5]',
                    ]
                elif self.field_name == 'budget_amount':                             # 预算金额
                    regular_list = [
                        r'估\s*算\s*价\s*.*?(\d+\.\d+\s*[元 万元])[\u4e00-\u9fa5]',
                    ]
                elif self.field_name == "successful_bidder":                          # 中标方
                    regular_list = [
                        r'受让人名称(.*?)成交',
                        r'竞\s*得\s*人(.*?)地理'
                    ]
                elif self.field_name == "tenderopen_time":
                    regular_list = [
                        r'开标时间[:：]{0,1}(.*?)[(（]',

                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == "3307":
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'bidding_agency':       # 采购人
                    regular_list = [
                        r'采购代理机构信息名称[: ：](.*?)地址'
                    ]
                if self.field_name == 'tenderee':              # 招标人
                    pass
                    # regular_list = [
                    #     r'采购人信息名称[: ：](.*?)地址'
                    # ]
                if self.field_name == 'tenderopen_time':
                   regular_list = [
                       r'开标时间[: ：](.*?[) ）])',
                   ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3334':
            # self.table_name_list.append(self.area_id)
            self._value = self._value if self._value else ''
            self.get_val_from_title()
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'bidding_contact':      # 招标联系人
                    regular_list = [
                        r'采购单位[: ：].*?联系人[: ：](.*?)联',
                        r'招标单位[: ：].*?联系人[: ：](.*?)联',
                        r'采购单位名称[: ：].*?联系人[: ：](.*?)联',
                        r'采购人信息.*?项目联系人（询问）[: ：](.*?)项'
                    ]
                if self.field_name == 'liaison':              # 招标人联系方式
                    regular_list = [
                        r'采购单位[: ：].*?电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'采购人信息.*?项目联系方式（询问）[: ：](.*?)质'
                    ]
                if self.field_name == 'agent_contact':         # 招标代理联系人
                    regular_list = [
                        r'招标代理[: ：].*?联系人[: ：](.*?)联',
                        r'代理机构[: ：].*?联系人[: ：](.*?)联',
                        r'招标代理单位[: ：].*?联系人[: ：](.*?)联',
                        r'代理单位[: ：].*?联系人[: ：](.*?)联',
                        r'代理单位名称[: ：].*?联系人[: ：](.*?)联',
                        r'采购代理机构信息.*?项目联系人（询问）[: ：](.*?)项',
                        r'采购代理机构.*?联系人[: ：](.*?)联',
                    ]
                if self.field_name == 'contact_information':   # 招标代理联系方式
                    regular_list = [
                        r'采购代理机构.*?联系电话及传真[: ：](\d{11}?)',
                        r'招标代理[: ：].*?电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'代理机构[: ：].*?电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'采购代理机构.*?电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'采购代理机构信息.*?项目联系方式（询问）[: ：](.*?)质',

                    ]
                if self.field_name == 'tenderopen_time':       # 开标时间
                    regular_list = [
                        r'本次招标将于(.*?)分.*?开标',
                        r'本次磋商将于(.*?)整.*?开标'
                    ]
                if self.field_name == 'project_number':
                    regular_list = [
                        # r'项目编号\s*[: ：](.*?)[\u4e00-\u9fa5]',
                        r'项目编号\s*[: ：](.*?)[二|三|四|项]'
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'采购人名称[: ：](.*?)[二]',
                        r'采购人信息名\s*称[: ：](.*?)地',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'采购代理机构信息名\s*称[: ：](.*?)地',
                        r'采购代理机构名\s*称[: ：](.*?)地'
                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'最高限价(.*?[(元)|(万元)])'
                    ]


                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == '3337':
            self._value = self._value if self._value else ''
            self.get_val_from_title()
            if not self._value.strip():
                regular_list = []
                # 代理联系人
                if self.field_name == 'agent_contact':
                    regular_list = [
                        r'招标代理机构[: ：].*联系人[: ：](.*?)电话',
                        r'采购代理机构信息名.*?项目联系人（询问）[: ：](.*?)项'
                    ]
                # 代理联系方式
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'招标代理机构[: ：].*电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'采购代理机构信息名.*?项目联系方式（询问）[: ：](.*?)质',
                    ]
                # 代理单位
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'采购代理机构信息名\s*称[: ：](.*?)地',
                        r'采购代理机构名称.*?联系人[: ：](.*)联'
                    ]
                # 招标人联系方式
                if self.field_name == 'liaison':
                    regular_list = [
                        r'招标代理机构[: ：].*?电话[: ：](.*?)[\u4e00-\u9fa5]',
                        r'采购人信息.*?项目联系方式（询问）[: ：](.*?)质'
                    ]
                # 招标单位（招标人）
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人[: ：](.*?)招标代理机构',
                        r'采购人信息名\s*称[: ：](.*?)地'
                    ]
                # 招标联系人
                if self.field_name == 'bidding_contact':
                    regular_list = [
                        r'采购人信息.*?项目联系人（询问）[: ：](.*?)项'
                    ]


                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

    def done_after_extract(self):
        """
        通用提取后，根据地区单独提取
        :param val:
        :return:
        """
        if self.area_id == '3305':  # 苍南
            pass
        if self.area_id == '3334':  # 富阳区
            pass

    @staticmethod
    def remove_rest_zero(decimal_obj):
        return decimal_obj.to_integral() if decimal_obj == decimal_obj.to_integral() else decimal_obj.normalize()

    def set_blank(self):
        """
        - blank_tags表示可能出现的其他空字符
        :return:
        """
        blank_tags = ['/']
        for bt in blank_tags:
            if self._value.strip() == bt:
                self._value = ''
                break

        # 除中标时间外匹配结果出现 冒号 置空
        if re.search('[:：]', self._value) and self.field_name != 'tenderopen_time':
            self._value = ''

    def is_isolated_unit(self):
        """
        - 特殊单位的处理
        :return:
        """
        extra_units = ['元/m3', '%', '单页', '元/平方米', '元/亩']
        for extra_unit in extra_units:
            if extra_unit in self._value:
                return True
        return False

    def clean_value(self):
        """
        - 去除符号/替换空格为一个
        - bid_amount/budget_amount 处理万元/元
        """
        symbols = ['？', '?']

        try:
            for symbol in symbols:
                self._value = ''.join(self._value.split(symbol))
            self._value = re.sub(r'\s+', ' ', self._value)
        except Exception as e:
            self.msg = 'error:{0}'.format(e)

        if self.field_name in ['bid_amount', 'budget_amount']:
            if self.is_isolated_unit():
                self._value = ''
                return

            # if self._value in re.findall('\d+.*[元|万元]', self._value):
                # 预算造价约3.9994亿元
            handled = True
            com = re.compile(r'([0-9 .]+)')
            if re.search('百万元|百万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 1000000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('千万元|千万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 10000000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('亿元|亿', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 100000000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('万元|万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 10000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('元', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip())))
                    self._value = str(Decimal(values[-1]))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            else:
                handled = False

            # 匹配不到任何数值的内容置空
            if not re.search(r'\d+', self._value):
                self._value = ''

            try:
                assert Decimal(self._value), '非数字'
            except Exception as e:
                print(e)
            else:
                self._value = '{}'.format(KeywordsExtract.remove_rest_zero(self.multi_number * Decimal(self._value) if not handled else Decimal(self._value)))

        if self.field_name == 'project_name':
            com = re.compile(r'([\[【][\u4e00-\u9fa5]+?[】 \]])')
            suffix_trash = com.findall(self._value)
            if suffix_trash:
                suffix_trash = suffix_trash[0]
                self._value = ''.join(self._value.split(suffix_trash))

        if self.field_name == 'liaison':
            self._value = '' if u'\u4e00' <= self._value <= u'\u9fff' else self._value

        if self.field_name in ['bidding_agency', 'tenderee', ]:
            self._value = ''.join(self._value).replace('（盖章）', '').replace('业主：', '').replace('（重新招标）', '')

        if self.field_name in ['agent_contact', 'bidding_contact', 'project_leader']:
            # N个联系人
            # """唐爱平（村）15988409931魏菊琴（镇）15990089781"""
            # """汪佳胤 15867186206/667206（政府网）0571-65089396程霞敏13968113786/613786（政府网）"""
            self._value = re.sub(r'（[\u4e00-\u9fa5]+）', ' ', self._value)
            c_re_list = [
                r'(?P<lianxiren>[\u4e00-\u9fa5]+)\s*[\d（]',
                r'联系人[:：](?P<lianxiren>[\u4e00-\u9fa5]+)联系电话[:：][\d /，,]+',
            ]
            for c_re in c_re_list:
                c_com = re.compile(c_re)
                c_value = '，'.join(c_com.findall(self._value))
                if c_value:
                    self._value = c_value
                    break

        if self.field_name in ['contact_information', 'liaison', 'project_contact_information']:
            # N个联系方式
            self._value = re.sub(r'（[\u4e00-\u9fa5]+）', ' ', self._value)
            c_re_list = [
                r'[\u4e00-\u9fa5]+(?P<lianxifangshi>[\d /，\-（）]+)',
                r'联系人[:：][\u4e00-\u9fa5]+联系电话[:：]([\d /，,]+)',
            ]
            for c_re in c_re_list:
                c_com = re.compile(c_re)
                c_value = '，'.join(c_com.findall(self._value))
                if c_value:
                    self._value = c_value
                    break


        self.set_blank()

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_table()
        self._extract_from_text()
        self.done_after_extract()  # 通用提取后各地区处理
        self.clean_value()
        return self._value


if __name__ == '__main__':
    content = '''<div class="col-md-20 top20 border-infodetail">
<div id="ivs_content" class="infocontent">
           <!--ZJEG_RSS.content.begin--><meta name="ContentStart"><p style="text-align: center; line-height: 27px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 黑体; font-size: 21px;">建德市更楼街道绿化养护服务采购项目</span></strong></p><p style="text-align: center; line-height: 27px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 黑体; font-size: 21px;">预中标结果公示</span></strong></p><p style="text-align: center; line-height: 20px; text-indent: 4px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">公示日期：2021年6月30日</span></strong></p><p style="margin: 0px 0px 8px 28px;"><span style="font-family: Calibri;"> </span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; text-indent: 0px; -ms-layout-grid-mode: char;"><span style="color: black; font-family: 宋体; font-size: 16px;">一．</span><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">采购人名称：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">建德市城南城建开发有限公司</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">采购项目名称：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">建德市更楼街道绿化养护服务采购项目</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">采购项目编号：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">XAJF2021B-017</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">四．采购组织类型：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">分散采购委托代理</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">五．采购方式：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">公开招标</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">六．采购公告发布日期：</span></strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">2021</span><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">年6月9日</span></p><p style="margin: 4px 4px 4px 0px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><strong><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">七．预中标结果：</span></strong></p><div align="center"><table style="border-collapse: collapse;" border="0" cellspacing="0" cellpadding="0"><tbody><tr style="height: 29px; page-break-inside: avoid;"><td width="57" height="29" valign="top" style="padding: 0px 7px; border: 1px solid windowtext; border-image: none; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 4px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">序号</span></p></div></td><td width="237" height="29" valign="top" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 4px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">预中标单位</span></p></div></td><td width="106" height="29" valign="top" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 0px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">投标报价（万元）</span></p></div></td><td width="91" height="29" valign="top" style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; border-image: none; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 4px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">综合得分</span></p></div></td></tr><tr style="height: 33px; page-break-inside: avoid;"><td width="57" height="33" style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; border-image: none; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 4px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">1</span></p></div></td><td width="237" height="33" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px; text-align: center; vertical-align: middle;"><span style="color: black; font-family: 宋体; font-size: 16px;">建德市中振建设有限公司</span></p></td><td width="106" height="33" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><div style="padding: 0px; border: 1px rgb(99, 99, 99); border-image: none; margin-right: 4px; margin-left: 4px;"><p style="margin: 4px 0px; padding: 0px; border: currentColor; border-image: none; text-align: center; line-height: 24px;"><span style="color: black; font-family: 宋体; font-size: 16px;">59.7618</span></p></div></td><td width="91" height="33" style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;"><p style="margin: 0px; text-align: center; vertical-align: middle;"><a></a><span style="color: black; font-family: 宋体; font-size: 16px;">79.18 </span></p></td></tr></tbody></table></div><p style="margin: 4px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;"> </span></p><p style="margin: 4px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">八．其它事项：</span></p><p style="margin: 4px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">各参加政府采购供应商对该预中标结果和采购过程等有异议的，可以自本公示之日起7个工作日内，以书面形式向采购人或其委托的采购代理机构提出质疑。同时也可向建德市公共资源交易中心新安江分中心反应</span></p><p style="margin: 4px; text-align: left; line-height: 24px; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">九.联系方式：</span></p><p style="margin: 8px 57px 0px 0px; text-align: left; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">1</span><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">、采购代理机构名称: 耀华建设管理有限公司</span></p><p style="margin: 8px 57px 0px 0px; text-align: left; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">联系人：柴文琪    联系电话及传真：19957823508 </span></p><p style="background: white; margin: 4px 4px 4px 0px; text-align: left; line-height: 24px;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">2</span><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">、监管部门：建德市公共资源交易中心新安江分中心</span></p><p style="background: white; margin: 4px 4px 4px 0px; text-align: left; line-height: 24px;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;">监督投诉电话：0571-64787970</span></p><p style="background: white; margin: 4px; text-align: left; line-height: 24px; text-indent: 36px;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;"> </span></p><p style="margin: 8px 57px 0px 0px; text-align: left; -ms-layout-grid-mode: char;"><span style="background: white; color: black; font-family: 宋体; font-size: 16px;"> </span></p><p><a href="http://tfile.zhaotx.cn/files/webfile/20210707/doc/C3DDE5C689574F8ABBFC723254D8109C.doc"><img style="border: currentColor; border-image: none;" src="http://tfile.zhaotx.cn/files/webfile/20210707/png/EF0F2CAFA1514BBDBACF6A96672A5E03.png">XAJF2021B-017中标公式.doc</a></p><meta name="ContentEnd"><!--ZJEG_RSS.content.end-->
        </div>
        <div class="infoattach">
            
        </div>

 
      </div>'''
    ke = KeywordsExtract(content, [
        # "投标报价（万元）",          # bid_amount

        # "项目名称",                 # project_name
        # "采购项目名称",
        # "招标项目",
        # "工\s*程\s*名\s*称",
        # "招标工程项目",
        # "工程名称",
        # "标段名称"

        # '项目负责人',                # project_leader
        # "电话",                     # liaison
        # "项目联系方式（询问）",        # contact_information
        # "联系电话",
        # "咨询代理单位",
        # "联系方式",
        # "代理联系电话",  # 3331
        # "咨询代理联系人及联系电话"

        # "联系人",                    # bidding_contact
        # "项目经理",
        # "项目经理（负责人）",
        # "项目负责人",
        # "项目联系人",
        # "填报人",
        # "项目联系人（询问）",
        # "招标联系电话"

        # "采购单位",                   # tenderee
        # "采购人信息",
        # "招标人",
        # "招标联系人",   # 3331
        # "单位名称",     # 3331  中标公告
        # "建设单位",     # 3331  中标公告
        #
        # # "招标代理",                    # bidding_agency
        # # "招标代理机构",
        # # "代理单位",
        # # '招标代理机构（盖章）',
        # # "代理公司",
        # # "招标代理公司",
        # # "采购代理机构",
        # # "填报单位",
        #
        # # "项目编号",                    # project_number
        # # "招标项目编号",
        # # "招标编号",
        # # "标段编号",
        # # "编号",
        # # "工程编号",

        # "投资总额(万元)",
        # "项目金额",                     # budget_amount
        # "预算金额（元）",
        # "预算价",
        # "项目概况",
        # "预算价(万元)",

        # "中标价格",                     # bid_amount
        # "投标报价(万元)",     # 3331
        # "投标报价（万元）",    # 3331
        # "报价（元）",
        # "中标价（元）",

        # "招标方式",

        # "联系人",                       # agent_contact
        "代理联系电话",
        "咨询代理联系人及联系电话"

        # "开标时间",                      # tenderopen_time
        # "开启时间",
        # "投标截止时间（开标时间）",  # 3331
        # "预计采购时间（填写到月）",
        # "开标日期",               # 3331
        # "备\s*注"

        # "中标人",                        # successful_bidder
        # "单位名称",
        # "中标人名称",
        # "中标单位",
        # "供应商名称",

        # "项目负责人"                      # project_leader

        # "建设单位联系人",                  # bidding_contact
        # "招标联系人",
        # "招标单位联系人",    # 3334
        # "采购单位联系人",    # 3334
        # "联系人",


        # '咨询代理单位',  # 3334
        # "代理公司",  # 3331
        # "代理机构",  # 3331
        # "招标代理公司"  # 3331
        # "采购代理机构",  # 3334
        # "招标代理",  # 3334
        # "代理单位",  # 3334
        # "代理单位名称",


    ], field_name='contact_information', area_id="3334")
    # ], field_name='tenderopen_time', area_id="3307")
    # ], field_name='project_name', area_id="3319", title='')
    # ke = KeywordsExtract(content, ["项目编号"])
    # ke.fields_regular = {
    #         'project_name': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'project_number': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'budget_amount': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'tenderee': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'bidding_agency': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'liaison': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
    #         ],
    #         'contact_information': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ。，,]+?)ψ',
    #         ],
    #         'successful_bidder': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'bid_amount': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'tenderopen_time': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'project_contact_information': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #         'project_leader': [
    #             r'%s[^ψ：:。，,、”“"]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
    #         ],
    #     }
    print(ke.get_value())
