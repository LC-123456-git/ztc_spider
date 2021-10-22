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


def get_keys_value_from_content_ahead(content: str, keys, area_id="00", _type="", field_name=None, title=None, **kwargs):
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

    elif area_id in ["3300", '3306', '3307', '3313', '3312', '3331', '3334', '3337', '3343', '3344', '3346',
                     '3347', '3350', '3360', '3361']:
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id, title=title, **kwargs)
        return ke.get_value()
    elif area_id in ["3309", "3320", "3319", "3326"]:
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id, title=title, **kwargs)
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

    def __init__(self, content, keys, field_name, area_id=None, title=None, **kwargs):
        # - yaml文件配置
        self.br_cf = kwargs.get('br_cf', '')
        self.cr_cf = kwargs.get('cr_cf', '')
        self.rm_cf = kwargs.get('rm_cf', '')
        self.before_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.br_cf, field_name)]
        self.common_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.cr_cf, field_name)]
        self.liaison_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'LIAISON')]
        self.symbols_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'SYMBOLS')]
        self.company_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'COMAPNY')]
        self.amount_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'AMOUNT')]
        self.project_name_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'PROJECT_NAME')]
        self.contact_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'CONTACT')]
        self.liaison_union_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'LIAISON_UNION')]
        self.contact_union_regulars = [r'{}'.format(r) for r in utils.get_keywords(self.rm_cf, 'CONTACT_UNION')]
        self.isolated_unit = utils.get_keywords(self.rm_cf, 'ISOLATED_UNIT')
        self.project_priority = utils.get_keywords(self.rm_cf, 'PROJECT_PRIORITY')
        self.last_part = utils.get_keywords(self.rm_cf, 'LAST_PART')

        self.content = content
        self.keys = keys if isinstance(keys, list) else [keys]
        self.area_id = area_id
        self.field_name = field_name
        self.title = title
        self.msg = ''
        self.keysss = [
            "招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称", "工程名称", "项目名称", "成交价格", "招标工程项目",
            "项目编号", "招标项目编号", "招标编号", "招标人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构",
            "项目金额", "预算金额（元）", "预算金额（元）", "招标估算价", "中标（成交）金额（元）", "联系人", "项目经理（负责人）",
            "建设单位", "中标单位", "中标价", "退付类型", "建设单位联系人", "建设单位联系人", "工程名称", "代建单位联系人", "项目负责人",
            "项目经理", "中标造价", "中标造价（元）", "项目负责人：", "1工程名称", "2招标编号", "中标价（元/年）", "承包价（元）",
            "竞包报价（元）", "承包金额（元）", "承包价", "中标价（%）", "中标价（元）", "标段（包）编号", "承包单位", "中选单位", "标段编号",
            "承包人", "成交单位", "入围单位"
        ]
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

    def reset_regular_by_field(self):
        """
        - conf/common_regular/*.yaml
        - 根据字段修改正则列表
        """
        if self.common_regulars:
            self.fields_regular.update(**{
                self.field_name: self.common_regulars
            })

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
                    doc = etree.HTML(self.content.replace('&nbsp;', ''))
                    txt_els = [x.strip() for x in doc.xpath('//*//text()')]
                    text = 'ψ'.join(txt_els) if with_symbol else ''.join(txt_els).replace(' ', '')
                    self._value = self._regular_match(text, key, with_symbol=with_symbol)
                except Exception as e:
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
        except Exception as e:
            self.msg = 'error:{0}'.format(e)
        else:
            for t_data_key in t_data:
                try:
                    t_data_key = ''.join(t_data_key.split())
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
        except Exception:
            pass
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
            # 标题包含：取后半部分
            for lp in self.last_part:
                c_v = self.title.split(lp)
                if len(c_v) == 2:
                    self.title = c_v[1]
            # 根据关键字优先级匹配项目名称
            for name in self.project_priority:
                if name in self.title:
                    # 判断项目关键字是否在（）【】 [] 内
                    if self.brackets_contained(name):
                        continue

                    self._value = ''.join([self.title.split(name)[0], name])
                    delete_chars = ['【】']
                    for dc in delete_chars:
                        self._value = self._value.replace(dc, '')
                    break

    def done_before_extract(self):
        """
        - 通用提取前，根据地区单独提取
        """
        self.get_val_from_title()
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

    def clean_value(self):
        """
        - 对提取的字段数据进行清洗
            + 去除符号/替换空格为一个
            + bid_amount/budget_amount 处理万元/元
            + 特定字段 特殊字符串清理
        """
        # 多空格转化成单个
        self._value = KeywordsExtract.remove_chars_by_regs([r'\s+'], self._value, replace_str=' ')
        if self.area_id != '3313':
            if self.field_name in ['tenderee', 'bidding_agency']:
                self._value = KeywordsExtract.remove_chars_by_regs(self.company_regulars, self._value)
        if self.field_name in ['bid_amount', 'budget_amount']:
            if self.is_isolated_unit():
                self._value = ''
                return

            self._value = KeywordsExtract.remove_chars_by_regs(self.amount_regulars, self._value)
            # 删除"元"之后多余字符
            self._value = KeywordsExtract.remove_rest_suffix(self._value)

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
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            else:
                handled = False

            # 匹配不到任何数值的内容置空
            if not re.search(r'\d+', self._value):
                self._value = ''

            # 数值最终值处理
            try:
                assert Decimal(self._value), '非数字'
            except Exception:
                pass
            else:
                self._value = '{}'.format(KeywordsExtract.remove_rest_zero(
                    self.multi_number * Decimal(self._value) if not handled else Decimal(self._value)))
                if Decimal(self._value) < 100:
                    self._value = ''
        if self.field_name == 'project_name':
            self._value = KeywordsExtract.remove_chars_by_regs(self.project_name_regulars, self._value)
            if not self._value:
                self._value = self.title
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

        # 最终结果去除特殊符号
        self._value = KeywordsExtract.remove_chars_by_regs(self.symbols_regulars, self._value)

    def get_value(self):
        self.reset_regular_by_field()  # 自定义字段正则列表覆盖默认正则列表
        self.done_before_extract()  # 多规则预先匹配
        self._extract_from_table()  # 表格数据
        self._extract_from_text()  # 默认规则匹配
        self.clean_value()  # 匹配结果清理
        return self._value


if __name__ == '__main__':
    content = '''

              '''
    area_id = "3343"
    br_cf = utils.init_yaml('before_regular', area_id)
    cr_cf = utils.init_yaml('common_regular', area_id)
    kw_cf = utils.init_yaml('keyword', area_id)
    rm_cf = utils.init_yaml('public_regular', file_name='remove_chars')
    regular_params = {
        'br_cf': br_cf,
        'cr_cf': cr_cf,
        'rm_cf': rm_cf,
    }
    ke = KeywordsExtract(
        content, kw_cf['budget_amount'], field_name='budget_amount', area_id=area_id, **regular_params
    )
    # ], field_name='project_name', area_id="3319", title='')
    # ke = KeywordsExtract(content, ["项目编号"])

    print(ke.get_value())
