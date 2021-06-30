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

    elif area_id == "3305":
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name)
        return ke.get_value()

    # elif area_id == "3306":
    # # TODO 还需优化
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
                        Price = str(sum(list(map(int, budgetPrice_list))))
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
                        data_dict[title_header[3]] = str(Price)
                        data_dict[title_header[4]] = p_Time
                    for keys in keys_str_list:
                        value = data_dict.get(keys)
                        if value:
                            return re.sub(" ", "", value)
                    # print(title_header)

                ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id)
                ke.fields_regular = {
                    'project_name': [
                        r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
                    ],
                    'project_number': [
                        r'%s[^ψ：:。，,、]*?[: ：]+?\s*?[ψ]*?([^ψ]+?)ψ',
                        r'%s[ψ：:。，,、]*?[: ：\s]+?\s*[ψ]*?([^ψ]+?)ψ'
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
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id,
                             title=title)
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
        self.keysss = [
            "招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称", "工程名称", "项目名称", "成交价格", "招标工程项目",
            "项目编号", "招标项目编号","招标编号", "招标人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构",
            "项目金额", "预算金额（元）","预算金额（元）", "招标估算价","中标（成交）金额（元）", "联系人", "项目经理（负责人）",
            "建设单位", "中标单位", "中标价", "退付类型",
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
        }
        self.fields_regular_with_symbol = copy.deepcopy(self.fields_regular)
        self._value = ''

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
                    val = ''.join(result[0]).replace('业主：', '')
                else:
                    val = ' '
            if result:
                val = result[0]
                if not re.search("元", val):
                    if unit := re.search("元|万元", key):
                        val_unit = val + unit.group()
                        return val_unit
                    return val
            if val:
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
        if self.field_name == 'contact_information':
            pass
        if self.field_name == 'liaison':
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
                    doc = etree.HTML(self.content)
                    txt_els = [x.strip() for x in doc.xpath('//*//text()')]
                    text = 'ψ'.join(txt_els) if with_symbol else ''.join(txt_els)

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
        except Exception as e:
            print(e)  # get lost
        else:
            if next_val == key:
                next_val = KeywordsExtract.get_h_val(c_index, key, tr)

            return next_val

    @staticmethod
    def get_val_from_table(result, key):
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
                    self._value = KeywordsExtract.get_val_from_table(result, key)
                else:
                    result = list(zip(*result))
                    self._value = KeywordsExtract.get_val_from_table(result, key)
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

        if self.area_id == '3306':
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'bidding_agency':  # 招标代理
                    regular_list = [
                        r'代理机构\s*[: ：](.*?)联系人',
                        r'采购代理机构信息名 称\s*[: ：](.*?)地\s*址',
                        r'代理机构联系方式\s*[: ：](.*?)联系人',
                        r'报名.*?发售地点\s*[: ：](.*?)[( （]',
                        r'招标代理\s*[: ：](.*?)地'
                    ]
                elif self.field_name == 'project_number':  # 项目编号
                    regular_list = [
                        r'项目编号\s*[: ：](.*?)[\u4e00-\u9fa5]'
                        r'项目编号\s*[: ：](.*?)二'
                    ]
                elif self.field_name == "project_name":  # 项目名称
                    regular_list = [
                        r'项目名称\s*[: ：](.*?)三',
                        r'项目名称\s*[: ：](.*?)[\u4e00-\u9fa5]',

                    ]
                elif self.field_name == "tenderee":  # 招标人
                    regular_list = [
                        r'招标人联系方式\s*[: ：](.*?)联系人',
                        r'招标方联系方式\s*[: ：](.*?)联系人',
                        r'招标人\s*[: ：](.*?)联',
                        r'招标人(.*)工程规模',
                        r'联系人[: ：](.*?)联'
                    ]
                elif self.field_name == "liaison":  # 联系人
                    regular_list = [
                        r'联系人\s*（.*?）[: ：](.*?)项目',
                        r'联系人\s*[: ：](.*?)[联系电话 , ， 电话]',
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

                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

        if self.area_id == "3305":
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []
                if self.field_name == 'project_number':  # 项目编号
                    regular_list = [
                        r'公示编号(.*?)土地',
                    ]
                elif self.field_name == "project_name":  # 项目名称
                    regular_list = [
                        r"项目名称(.*?)宗",
                    ]
                elif self.field_name == "bid_amount":  # 中标金额
                    regular_list = [
                        r'成交价格(.*?)[\u4e00-\u9fa5]'
                    ]
                elif self.field_name == "successful_bidder":  # 中标方
                    regular_list = [
                        r'受让人名称(.*?)成交'
                    ]
                self.reset_regular(regular_list, with_symbol=False)

                self._extract_from_text(with_symbol=False)

    def done_after_extract(self):
        """
        通用提取后，根据地区单独提取
        :param val:
        :return:
        """
        if self.area_id == '3320':  # 苍南
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
        extra_units = ['元/m3', '%']
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

            # 预算造价约3.9994亿元
            com = re.compile(r'([0-9 .]+)')
            if re.search('万元|万', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip()) * 10000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('百万元|百万', self._value):
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
            elif re.search('元', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0].strip())))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            else:
                pass

            # 匹配不到任何数值的内容置空
            if not re.search(r'\d+', self._value):
                self._value = ''
        if self.field_name == 'project_name':
            com = re.compile(r'([\[【][\u4e00-\u9fa5]+?[】 \]])')
            suffix_trash = com.findall(self._value)
            if suffix_trash:
                suffix_trash = suffix_trash[0]
                self._value = ''.join(self._value.split(suffix_trash))

        self.set_blank()

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_text()
        self._extract_from_table()
        self.done_after_extract()  # 通用提取后各地区处理
        self.clean_value()
        return self._value


if __name__ == '__main__':
    content = """
<table id="tblInfo" cellspacing="1" cellpadding="1" width="100%" align="center" border="0" runat="server">
    <tbody>
        <tr>
            <td id="tdTitle" align="center" runat="server" height="70">
                <font color="" style="font-size: 25px"> <b>
                        长兴县和平镇城山路道路工程施工[抽签法]
                    </b></font>

            </td>
        </tr>
        <tr>
            <td height="29" align="center" bgcolor="#eeeeee">
                <font color="#545454" class="webfont">【信息时间：
                    2021/5/11
                    &nbsp;&nbsp;阅读次数：
                    <script src="/cxweb/Upclicktimes.aspx?InfoID=273ce4eb-32e7-4ad3-a59c-2c066caea1db"></script>422
                    】<a href="javascript:void(0)" onclick="window.print();">
                        <font color="#545454" class="webfont">【我要打印】</font>
                    </a><a href="javascript:window.close()">
                        <font color="#545454" class="webfont">【关闭】</font>
                    </a></font>
                <font color="#000000">

                </font>
            </td>
        </tr>
        <tr>
            <td height="10"></td>
        </tr>
        <tr>
            <td height="250" align="left" valign="top" class="infodetail" id="TDContent">
                <div>
                    <p></p>
                    <h1 style="TEXT-ALIGN: center; LINE-HEIGHT: 30pt; MARGIN-TOP: 0pt; MARGIN-BOTTOM: 0pt; mso-line-height-rule: exactly; mso-list: l0 level1 lfo1"
                        align="center"><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 18pt; mso-bidi-font-family: 'Times New Roman'; mso-ansi-font-weight: bold; mso-font-kerning: 22.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">长兴县和平镇城山路道路工程</font>
                            </span></b><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 18pt; mso-bidi-font-family: 'Times New Roman'; mso-ansi-font-weight: bold; mso-font-kerning: 22.0000pt; mso-spacerun: 'yes'">
                                <!--?xml:namespace prefix = o /-->
                                <o:p></o:p>
                            </span></b></h1>
                    <h1 style="TEXT-ALIGN: center; LINE-HEIGHT: 30pt; MARGIN-TOP: 0pt; MARGIN-BOTTOM: 0pt; mso-line-height-rule: exactly"
                        align="center"><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 18pt; mso-bidi-font-family: 'Times New Roman'; mso-ansi-font-weight: bold; mso-font-kerning: 22.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">发包公告</font>
                            </span></b><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 18pt; mso-bidi-font-family: 'Times New Roman'; mso-ansi-font-weight: bold; mso-font-kerning: 22.0000pt; mso-spacerun: 'yes'">
                                <o:p></o:p>
                            </span></b></h1>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">长兴县和平镇城山路道路工程</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">经主管部门同意建设。建设地址位于</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">长兴县和平镇</font>
                            </span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">。项目</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">业主</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">长兴县和平镇人民政府</font>
                            </span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">，资金来源为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">财政</font>
                            </span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">，出资比例为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">100% </font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">。项目已具备发包条件，发包人为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">长兴县和平镇人民政府</font>
                            </span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">，（发包</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">代理机构为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">浙江建询工程管理咨询有限公司</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">）</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">，</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">现对该项目的</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single">
                                <font face="宋体">施工</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">进行公开发包。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">一、本次发包范围：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">1.1</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">长兴县和平镇城山路道路工程</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">
                                ，本次招标范围为设计图纸内的新建道路及雨污水管网工程，包括场地平整、土方开挖、路基填筑、水稳基层、沥青面层摊铺、雨污水管道铺设、雨污水井砌筑等工作内容，具体详见招标文件所附工程量清单及设计施工图纸（电子版）。
                            </font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-highlight: rgb(255,255,0)">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">1.2本工程采用工程量清单计价、随机抽签方式发包；</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">1.3本工程招标控制价为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">2578474</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">元，发包价为</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">2405861</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">元（详见附件工程量清单），计划工期</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">200</font>
                            </span></u><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)"></span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">日历天。质量要求</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">合格</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                                <font face="宋体">二、承包人条件、要求：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">2.1承包人必须为长兴县工程建设项目优秀承包商名录内企业（市政专业），具有</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; text-underline: single; mso-shading: rgb(255,255,255)">
                                <font face="宋体">市政公用工程施工总承包叁级及以上资质的</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">独立法人。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">2.2承包人及其法定代表人控股的其他公司，不得同时参与同一标段抽签。否则，均按无效处理。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; mso-shading: rgb(255,255,255)">
                            <font face="宋体">2.3拟派项目负责人：具有</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">注册在投标人单位的</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single">
                                <font face="宋体">市政公用工程</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">专业</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single">
                                <font face="宋体">贰级（含）以上</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">注册建造师执业资格，并具有</font>
                            <font face="宋体">“三类人员”B类证书，且为本单位正式在职员工。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">2.4已在县公共资源交易中心交纳年度保证金的。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">
                                2.5在抽签时间截止日存在在其他任何在建合同工程上担任项目负责人的，不得以拟派项目负责人的身份参加本次公开交易活动。在建合同工程的开始时间为合同工程中标通知书发出日期（不通过招标、发包方式的，开始时间为合同签订日期），结束时间为该合同工程通过验收或合同解除日期，已被其他项目推荐为第一中标候选人且已公示的项目负责人视为有在建工程。
                            </font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">三、报名：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">有意参加本项目发包抽签的长兴县工程建设项目优秀承包商名录内企业于抽签前登录长兴县公共资源交易网（小额项目）下载相关交易资料进行报名。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal"><b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">四、抽签方式、时间和地点</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">
                                4.1抽签方式：由公证人员对抽签设备及号码球进行检查，确定无异议后，按抽签当日签到的顺序，由每个承包人代表公开抽取代表该承包人的号码球，经签名确认后当场公布；承包人代表抽取的号码球全部收回后，由发包人代表在其中公开随机抽取一个号码球，号码球与之相同的承包人即为签约承包人，并由发包人、签约承包人及监督人员共同签字确认成交结果。本次成交结果在长兴县公共资源交易网上发布成交公告，告知所有参加抽签的承包人。
                            </font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">4.2抽</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">签时间</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">：</font>
                            <font face="宋体">2021年</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">5</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">月</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">18</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">日</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">15</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">时</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">00</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">分</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">4.3抽签地点：长兴县公共资源交易中心4楼</font>
                        </span><u><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'; text-underline: single">
                                <font face="宋体">本项目开标室（具体见开标日交易大厅显示屏安排）。</font>
                            </span></u><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">五、交易保证金：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-bidi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">本项目交易保证金为发包价的</font>
                            <font face="宋体">2%（已在县公共资源交易中心交纳年度保证金的无需缴纳交易保证金）。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-bidi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">六、履约保证金：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">发包价的</font>
                            <font face="宋体">2%，由签约承包人在签订书面合同前提交至发包人账户。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">七、农民工工资保证金：</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">按县有关文件执行，由签约承包人在签订书面合同前提交至县农民工工资保证金专户。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">八、其他</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">
                                已标价工程量清单、项目专项合同、施工图纸（电子版）、承包申请函（格式）及法定代表人身份证明或授权委托书（格式）在长兴县公共资源交易网（小额项目）自行下载查看。</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan" class="p">
                        <b style="mso-bidi-font-weight: normal"><span
                                style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-ansi-font-weight: bold; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                                <font face="宋体">九、联系方式</font>
                            </span></b><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">9.1发包人：</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">长兴县和平镇人民政府</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 42pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">联系人：</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">徐工</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'"></span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 42pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">电话：</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">/</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">9.2代理机构：</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">浙江建询工程管理咨询有限公司</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 42pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">联系人：</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">宋工</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 42pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="p"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">电话：</font>
                            <font face="宋体">0572-</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">6789955</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 0.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan; mso-char-indent-count: 2.0000"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">9.3监督机构：长兴县公共资源交易管理办公室 </font>
                        </span><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="LINE-HEIGHT: 21pt; TEXT-INDENT: 42pt; mso-line-height-rule: exactly; mso-pagination: widow-orphan; mso-char-indent-count: 4.0000"
                        class="MsoNormal"><span
                            style="FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">电话：</font>
                            <font face="宋体">0572-6044639</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <o:p></o:p>
                        </span></p>
                    <p style="TEXT-ALIGN: right; LINE-HEIGHT: 21pt; WORD-BREAK: break-all; mso-line-height-rule: exactly; mso-pagination: widow-orphan"
                        class="MsoNormal" align="right"><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">2021年</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">5</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">月</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">11</font>
                        </span><span
                            style="FONT-FAMILY: 宋体; FONT-SIZE: 10.5pt; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'">
                            <font face="宋体">日</font>
                        </span><span
                            style="FONT-FAMILY: Calibri; FONT-SIZE: 10.5pt; mso-bidi-font-family: 'Times New Roman'; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-fareast-font-family: 宋体">
                            <o:p></o:p>
                        </span></p>
                    <p class="MsoNormal"><span
                            style="FONT-FAMILY: Calibri; BACKGROUND: rgb(255,255,255); FONT-SIZE: 10.5pt; mso-bidi-font-family: 'Times New Roman'; mso-font-kerning: 1.0000pt; mso-spacerun: 'yes'; mso-highlight: rgb(255,255,255); mso-fareast-font-family: 宋体">
                            <o:p></o:p>
                        </span></p>
                </div>
                <div>

                </div>
            </td>
        </tr>
        <tr>
            <td align="right">

                <br>
            </td>
        </tr>
        <tr id="trAttach" runat="server">
            <td align="left">
                <table id="filedown" cellspacing="1" cellpadding="1" width="100%" border="0" runat="server">
                    <tbody>
                        <tr>
                            <td valign="top" style="font-size: medium;"><b>

                                </b></td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td height="30"></td>
        </tr>
        <!--会员或非会员按钮-->
        <tr>
            <td></td>
        </tr>
        <!--答疑变更公告-->
    </tbody>
</table>
    """
    ke = KeywordsExtract(content, [
        # "项目名称",  # project_name
        # "采购项目名称",
        # "招标项目",
        # "工\s*程\s*名\s*称",
        # "招标工程项目",
        # "工程名称",

        # "中标单位",  # successful_bidder

        "联系电话",  # contact_information
        "联系方式",
        "电\s*话",

        # "联系人",  # liaison
        # "联\s*系\s*人",
        # "项目经理",
        # "项目经理（负责人）",
        # "项目负责人",
        # "项目联系人",
        # "填报人",

        # "招标人",  # tenderee
        # "招 标 人",
        # "招&nbsp;标&nbsp;人",
        # "招\s*?标\s*?人：",
        # "招标单位",
        # "采购人信息[ψ \s]*?名[\s]+称",
        # "建设（招标）单位",
        # "建设单位",
        # "采购单位名称",
        # "采购人信息",
        # "建设单位",

        # "招标代理",  # bidding_agency
        # "招标代理机构",
        # "采购代理机构信息[ψ \s]*?名[\s]+称",
        # "代理单位",
        # '招标代理机构（盖章）',
        # "代理公司",
        # "采购代理机构信息",
        # "填报单位",

        # "项目编号",  # project_number
        # "招标项目编号",
        # "招标编号",
        # "编号",
        # "工程编号",

        # "项目金额",  # budget_amount
        # "预算金额（元）",

        # "中标价格",  # bid_amount
        # "中标价",
        # "中标（成交）金额(元)",
        # "报价（元）",
        # "中标价（元）",

        # "招标方式",

        # "开标时间",  # tenderopen_time
        # "开启时间",

        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
        # ], field_name='project_name')
    ], field_name='contact_information', area_id="3319")
    # ], field_name='project_name', area_id="3319", title='')
    # ke = KeywordsExtract(content, ["项目编号"])
    ke.fields_regular = {
        'project_name': [
            r'%s[^ψ：:。，,、]*?[: ： \s]+?\s*?[ψ]*?([^ψ]+?)ψ',
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

    print(ke.get_value())
