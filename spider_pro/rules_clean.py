# -*- coding:utf-8 -*-
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import math


import re
import pandas
from spider_pro import utils
import copy
from lxml import etree

regular_plans = {
    # 0: "代\s*理[,|，]名\s*称.*盖\s*章.*[)|）][,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]",
    1: '代\s*理[,|，]名\s*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-+(.*)?|\d{11})[u4e00-u9fa5]',
    2: '代\s*理[,|，]名\s*称.*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    3: '代\s*理[,|，]名\s*称.*盖\s*章.*[)|）].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{5}[,|，]\d[,|，]\d{2}?|\d{11}?)[,|，]',
    4: '代\s*理[,|，]名\s*称[,|，].*?[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    5: '名称[(|（].*盖章[)|）][,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    6: '招\s*标\s*代\s*理[,|，]名称[,|，](?P<tenderee>.*?)[,|，].*?地.*?址[,|，](?P<address>.*?)[,|，].*?联.*?系.*?人[,|，](?P<liaison>.*?)[,|，].*?电.*?话[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    7: '代\s*理\s*机\s*构[:|：].*?[,|，](?P<tenderee>.*?)[,|，].*?联.*?系.*?人[:|：].*?[,|，](?P<liaison>.*?)[,|，].*?电.*?话[:|：].*?[,|，](?P<contact_information>\d{4}-\d{8}?|\d{11}?)[,|，]',
    8: '代\s*理\s*机\s*构\s*名\s*称[:|：].*?(?P<tenderee>.*?)[,|，].*?联.*?系.*?人[:|：].*?(?P<liaison>.*?)[,|，].*?电.*?话[:|：].*?(?P<contact_information>\d{4}-\d{6}[,|，]\d{2}?|\d{11}?)[,|，]',
}


def get_keys_value_from_content_ahead(content: str, keys, area_id="00", _type="", field_name=None):
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
    elif area_id == '3305':
        if isinstance(keys, str):
            keys_str_list = [keys]
        elif isinstance(keys, list):
            keys_str_list = keys
        else:
            return ""

        for key in keys_str_list:
            # print({key}, ': ')
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

            # if key == '项目名称' or key == '招标项目':
            #     regular_plan = {
            #         1: '招\s*标\s*项\s*目\s*[,|，](?P<{}>.*?)[,|，]'.format(keys),
            #         2: '工\s*程\s*名\s*称\s*(?P<{}>.*[u4e00-u9fa5].*?)[,|，]'.format(keys),
            #         3: '项\s*目\s*名\s*称[:|：]\s*[,|，](?P<{}>.*?)[,|，]'.format(keys),
            #     }
            # else:
            #     regular_plan = ''
            # utils.match_key_re(content, regular_plan, keys)
            #
            # return ""
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
                    # 匹配带冒号开始的文本内容
                    all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
                    # if all_results:
                    #     for item in all_results:
                    #         value = item.split(":")[-1].split("：")[-1].split("<")[0]
                    #         if value.strip():
                    #             return value.strip()
                    #             # print(value.strip())
                    #         tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                    #         if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                    #             value = value_str.group().split(">")[-2].split("</")[0]
                    #             if value.strip():
                    #                 return value.strip()
                    #                 # print(value.strip())
                    #
                    # # 匹配带冒号开始的文本内容后面有标签且换行的
                    # if key in str(re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)):
                    #     all_results_value = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[1::2]
                    #     all_results_key = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[::2]
                    #     for value, key_keys in zip(all_results_value, all_results_key):
                    #         if key in key_keys:
                    #             value = value.replace('\xa0', '')
                    #             if value.strip():
                    #                 # print(value.strip())
                    #                 return value.strip()
                    #
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
                            content_list.remove("工程概况")
                            b_list = content_list[1::2]
                            c_list = content_list[0::2]
                            for i, t in zip(b_list, c_list):
                                data_dict[t] = i
                            for keys in keys_str_list:
                                value = data_dict.get(keys)
                                if value:
                                    return value
                        else:
                            # content_list.remove("工程概况")
                            a_list = []
                            for item in content_list:
                                if re.search(("\S+"), item):
                                    a_list.append(item)
                                    b_list = a_list[1::2]
                                    c_list = a_list[0::2]
                                    for i, t in zip(b_list, c_list):
                                        data_dict[t] = i
                                    for keys in keys_str_list:
                                        value = data_dict.get(keys)
                                        if value:
                                            return value
                            # info_list = content_str.split("\n  \n \n \n  \n  ")
                            # for keys in keys_str_list:
                            #     for item in info_list:
                            #         data_dict[item.split("\n  \n  \n  ")[0]] = item.split("\n  \n  \n  ")[1]
                            #         value = data_dict.get(keys)
                            #         if value:
                            #             return value
                        # return value

                    data_dict = {}
                    doc = etree.HTML(content)
                    content_str = doc.xpath("//div[@class='MainList']/div[2]/div//text()")
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
                if doc.xpath("//table[@class='template-bookmark uuid-1609312554335 code-publicNoticeOfPurchaseIntentionDetailTable text-意向公开明细']"):
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
                        Price = str(sum(list(map(int, budgetPrice_list)))/10000)
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
                        data_dict[title_header[3]] = str(int(Price)/10000)
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
                if re.findall("金额", key):
                    return str(int(ke.get_value())/10000)
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
    # elif area_id == "3302":
    #     try:
    #         if isinstance(keys, str):
    #             keys_str_list = [keys]
    #         elif isinstance(keys, list):
    #             keys_str_list = keys
    #         else:
    #             return ""
    #
    #         for key in keys_str_list:
    #             # 先判断content中 是否包含key的文本
    #             if len(key) == 0 or not content or not key:
    #                 continue
    #
    #             data_dict = {}
    #             doc = etree.HTML(content)
    #             content_str = doc.xpath("//tr//text()")
    #
    #             if re.search(fr"{key}", content):
    #                 # 匹配带冒号开始的文本内容
    #                 all_results = re.findall(fr"{key}[:|：].*?</.*?>", content)
    #                 if all_results:
    #                     for item in all_results:
    #                         value = item.split(":")[-1].split("：")[-1].split("<")[0]
    #                         if value.strip():
    #                             return value.strip()
    #                             # print(value.strip())
    #                         tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
    #                         if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
    #                             value = value_str.group().split(">")[-2].split("</")[0]
    #                             if value.strip():
    #                                 return value.strip()
    #                                 # print(value.strip())
    #
    #                 # 匹配带冒号开始的文本内容后面有标签且换行的
    #                 if key in str(re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)):
    #                     all_results_value = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[1::2]
    #                     all_results_key = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[::2]
    #                     for value, key_keys in zip(all_results_value, all_results_key):
    #                         if key in key_keys:
    #                             value = value.replace('\xa0', '')
    #                             if value.strip():
    #                                 # print(value.strip())
    #                                 return value.strip()
    #
    #                 # # 匹配带空格开始的文本内容
    #                 # all_results = re.findall(fr"{key}\s+?<", content)
    #                 # if all_results:
    #                 #     for item in all_results:
    #                 #         value_list = item.split(" ")
    #                 #         for v_item in value_list:
    #                 #             if v_item.strip():
    #                 #                 # print(v_item.strip())
    #                 #                 return v_item.strip()
    #
    #                 # 匹配带表格标记的文本内容
    #                 if re.findall(fr"</td>", content):
    #                     a_list = []
    #                     data_dict = {}
    #                     doc = etree.HTML(content)
    #                     content_list = doc.xpath("//text()")
    #                     print(content_list)
    #                     for item in content_list:
    #                         if re.search(("\S+"), item):
    #                             a_list.append(item)
    #                     print(a_list)
    #                     if not content_list:
    #                         content_list = doc.xpath("//div[@class='Section0']//text()")
    #                         b_list = content_list[1::2]
    #                         c_list = content_list[0::2]
    #                         for i, t in zip(b_list, c_list):
    #                             data_dict[t] = i
    #                         for keys in keys_str_list:
    #                             value = data_dict.get(keys)
    #                             if value:
    #                                 return value
    #                     else:
    #                         a_list = []
    #                         for item in content_list:
    #                             if re.search(("\S+"), item):
    #                                 a_list.append(item)
    #                                 b_list = a_list[1::2]
    #                                 c_list = a_list[0::2]
    #                                 for i, t in zip(b_list, c_list):
    #                                     data_dict[t] = i
    #                                 for keys in keys_str_list:
    #                                     value = data_dict.get(keys)
    #                                     if value:
    #                                         return value
    #                         # info_list = content_str.split("\n  \n \n \n  \n  ")
    #                         # for keys in keys_str_list:
    #                         #     for item in info_list:
    #                         #         data_dict[item.split("\n  \n  \n  ")[0]] = item.split("\n  \n  \n  ")[1]
    #                         #         value = data_dict.get(keys)
    #                         #         if value:
    #                         #             return value
    #                     # return value
    #
    #                 data_dict = {}
    #                 doc = etree.HTML(content)
    #                 content_str = doc.xpath("//div[@class='MainList']/div[2]/div//text()")
    #     except Exception as e:
    #         print("清洗出错")
    #         print(e)
    #         return ""

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
    elif area_id in ["3309", "3320", "3319"]:
        ke = KeywordsExtract(content.replace('\xa0', '').replace('\n', ''), keys, field_name, area_id=area_id)
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

    def __init__(self, content, keys, field_name, area_id=None):
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
        self.msg = ''
        self.keysss = [
            "招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称", "工程名称", "项目名称", "成交价格", "招标工程项目", "项目编号", "招标项目编号",
            "招标编号", "招标人", "招 标 人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构", "项目金额", "预算金额（元）", "招标估算价",
            "中标（成交）金额（元）", "联系人", "联 系 人", "项目经理（负责人）", "建设单位", "中标单位",
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
            if result:
                val = result[0]
            if val:
                break
        return val

    def format_fields(self):
        """
        修改self._value
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
                    # TODO 判断当前字段是否具备字段的约束条件/或者做相应的字符调整
                    self.format_fields()
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
            assert t_data[0], 'TH NODE.'
        except:
            pass
        else:
            for t_data_key in t_data[0]:
                if t_data_key in self.keysss:
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

    @staticmethod
    def check_has_table(doc_el):
        return True if doc_el.xpath('.//table') else False

    def _extract_from_table(self):
        """
        处理文章中table的信息
        """
        if not self._value:
            for key in self.keys:
                try:
                    doc = etree.HTML(self.content)
                    table_els = doc.xpath('//table')

                    for table_el in table_els:

                        # 判断是否有table
                        if KeywordsExtract.check_has_table(table_el):
                            continue

                        table_txt = etree.tounicode(table_el, method='html')
                        t_data = pandas.read_html(table_txt)
                        if t_data:
                            t_data = t_data[0]
                            t_dics = t_data.to_dict()

                            # 判断横向|纵向
                            # tr下td数一致     横向
                            # tr下td数不一致    纵向
                            if self.is_horizon(t_data):
                                c_index = 1
                                for _, t_dic in t_dics.items():
                                    tag = c_index % 2
                                    # 单数key  双数value
                                    if tag:  # 单数
                                        for t_index, td in t_dic.items():
                                            com = re.compile(key)
                                            ks = com.findall(td)
                                            if ks or td == key:
                                                c_key_dic = t_dics.get(c_index)
                                                self._value = c_key_dic.get(t_index)
                                                if isinstance(self._value, float):
                                                    if math.isnan(self._value):
                                                        self._value = ''
                                                        continue
                                                return
                                    c_index += 1
                            else:
                                for t_key, t_dic in t_dics.items():
                                    try:
                                        assert isinstance(t_key, int), 'TH NODE.'
                                    except:
                                        com = re.compile(key)
                                        ks = com.findall(t_key)
                                        if ks or t_key == key:
                                            self._value = t_dic.get(0, '')

                                            if isinstance(self._value, float):
                                                if math.isnan(self._value):
                                                    self._value = ''
                                                    continue
                                            return
                                    else:
                                        t_dic_len = len(t_dic)
                                        if t_dic_len > 1:
                                            c_key = t_dic.get(0, '')

                                            for t in range(1, len(t_dic)):
                                                com = re.compile(key)
                                                ks = com.findall(c_key)
                                                if ks or key == c_key:
                                                    self._value = t_dic.get(t, '')

                                                    if isinstance(self._value, float):
                                                        if math.isnan(self._value):
                                                            self._value = ''
                                                            continue
                                                    return
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)

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

    def done_before_extract(self):
        """
        通用提取前，根据地区单独提取
        :param val:
        :return:
        """
        if self.area_id == '3320':  # 苍南
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
                        r'预算金额.*?为\s*(\d+\s*万元)',
                        r'预算金额.*?为\s*(\d+\s*元)',
                        r'本工程投资约\s*(\d+\s*万元)'
                        r'本工程投资约\s*(\d+\s*元)'
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
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
            self._value = self._value if self._value else ''
            if not self._value.strip():
                regular_list = []

                if self.field_name == 'project_name':
                    regular_list = [
                        r'概况[：:]([\u4e00-\u9fa5 \s]*?项目)[， ,]',
                        r'([\u4e00-\u9fa5 （ ）]*?工程)',
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'project_number':
                    regular_list = [
                        r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'预算约\s*(\d+\s*万元)',
                        r'预算约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)[\u4e00-\u9fa5]',
                        r'联\s*系\s*人：[\u4e00-\u9fa5]+?\s*([0-9 \-]+?)\s*[\u4e00-\u9fa5]'
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联\s*系\s*人[: ：]\s*([\u4e00-\u9fa5]+?)[联 电 质]',
                        r'项目经理：([\u4e00-\u9fa5]+?)\s*质量',
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

    def clean_value(self):
        """
        - 去除符号/替换空格为一个
        - bid_amount/budget_amount 处理万元/元
        """
        symbols = ['？', '?']

        try:
            for symbol in symbols:
                self._value = ''.join(self._value.split(symbol))
            self._value = re.sub('\s+', ' ', self._value)
        except:
            pass

        if self.field_name in ['bid_amount', 'budget_amount']:
            for unit in ['万元', '元']:
                if unit in self._value:
                    sp_data = self._value.split(unit)
                    if sp_data:
                        self._value = sp_data[0]
                        if unit == '元':
                            try:
                                self._value = str(int(self._value)/10000)
                            except Exception as e:
                                self._value = ''

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_text()
        self._extract_from_table()
        self.done_after_extract()  # 通用提取后各地区处理
        self.clean_value()
        return self._value


if __name__ == '__main__':
    content = """
<table width="932" border="0" cellspacing="0" cellpadding="0" align="center">
    <tbody>
    <tr>
        <td>
            <table id="tblInfo" cellspacing="1" cellpadding="1" width="100%" align="center" border="0" runat="server">
                <tbody>
                <tr>
                    <td id="tdTitle" align="center" runat="server" height="70"><font color="" style="font-size: 25px">
                        <b>
                            长兴县和平镇城南工业园区污水管道疏通与检测服务项目交易公告
                        </b></font>

                    </td>
                </tr>
                <tr>
                    <td height="29" align="center" bgcolor="#eeeeee">
                        <font color="#545454" class="webfont">【信息时间：
                            2021/4/30
                            &nbsp;&nbsp;阅读次数：
                            <script src="/cxweb/Upclicktimes.aspx?InfoID=bad034ba-4744-4a9e-8de1-e028c919d22a"></script>
                            137
                            】<a href="javascript:void(0)" onclick="window.print();"><font color="#545454"
                                                                                          class="webfont">【我要打印】</font></a><a
                                    href="javascript:window.close()"><font color="#545454"
                                                                           class="webfont">【关闭】</font></a></font><font
                            color="#000000">

                    </font></td>
                </tr>
                <tr>
                    <td height="10"></td>
                </tr>
                <tr>
                    <td height="250" align="left" valign="top" class="infodetail" id="TDContent">
                        <div>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 5pt; MARGIN-TOP: 5pt; WORD-BREAK: break-all; TEXT-ALIGN: center; LINE-HEIGHT: 20pt; mso-margin-top-alt: auto; mso-margin-bottom-alt: auto; mso-pagination: widow-orphan"
                               align="center"><b><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">长兴县和平镇城南工业园区污水管道疏通与检测服务项目</font></span></b><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><!--?xml:namespace prefix = "o" /--><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 5pt; MARGIN-TOP: 5pt; WORD-BREAK: break-all; TEXT-ALIGN: center; LINE-HEIGHT: 20pt; mso-margin-top-alt: auto; mso-margin-bottom-alt: auto; mso-pagination: widow-orphan"
                               align="center"><b><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">【发包公告】</font></span></b><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">本发包项目</font><font face="宋体">“长兴县和平镇城南工业园区污水管道疏通与检测服务项目”已批准实施，发包人为长兴县和平镇人民政府，资金来源：自筹，项目已具备发包条件，现对该项目进行公开发包。</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">1. 项目概况与发包范围：和平镇城南工业园区内20公里污水管道清淤疏通、窨井清理、封堵、抽水、CCTV检测（制作光盘及书面报告）及部分管道堵头拆除等工作内容。工程量总价低于50万元，具体内容详见发包文件。</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">2. 承包人资格要求：（1）具有独立承担民事责任的能力；（2）具有良好的商业信誉和今后服务；（3）具有履行合同所必需的设备和专业技术能力；（4）具有独立法人资格，具有排水管道养护资质证书，具有CCTV检测资质；（5）此项目不接受联合体投标。</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">3.公告及报名受理时间：</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">承包申请人报名者须带以下材料（复印件须盖单位公章）：</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">（</font><font face="宋体">1）单位介绍信（原件并注明企业联系电话及传真）；</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">（</font><font
                                        face="宋体">2）企业营业执照、企业资质证书复印件（复印件加盖单位公章）；</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">（</font><font face="宋体">3）</font></span><b><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">授权委托书，授权委托人为本公司正式员工，需提供身份证及有效社保证明（原件及复印件）。</font></span></b><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">报名时间和地点：</font><font face="宋体">2021年04月30日至 2021年05月07日，每日上午8：30-11：00，下午14：00-16：30（双休日除外）截止时间后恕不受理。到湖州卓然工程管理有限公司（长兴县太湖街道中央大道2598号交通投资集团大厦A座18楼南1818室）报名（截止时间后恕不受理），报名费300元。</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">4.联系方式：</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">发包人：长兴县和平镇人民政府</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">发包代理机构：湖州卓然工程管理有限公司</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none">
                                <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                        face="宋体">联系人：江工</font> <font face="宋体">联系电话：</font><font
                                        face="宋体">0572-6517626</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: right; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none"
                               align="right"><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">长兴县和平镇人民政府</font> </span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: right; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none"
                               align="right"><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">湖州卓然工程管理有限公司</font> </span><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: right; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none"
                               align="right"><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">长兴县和平镇招投标中心</font></span><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
                            <p class="MsoNormal"
                               style="MARGIN-BOTTOM: 7.8pt; MARGIN-TOP: 7.8pt; LAYOUT-GRID-MODE: char; TEXT-ALIGN: right; LINE-HEIGHT: 150%; TEXT-INDENT: 21pt; mso-pagination: widow-orphan; mso-para-margin-top: 0.5000gd; mso-para-margin-bottom: 0.5000gd; mso-layout-grid-align: none"
                               align="right"><span
                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font
                                    face="宋体">2021年04月30日</font></span><span
                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span>
                            </p>
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
        </td>
    </tr>
    </tbody>
</table>
    """
    ke = KeywordsExtract(content, [
        "项目名称",  # project_name
        "招标项目",
        "工程名称",
        "招标工程项目",
        "标项名称",

        # "中标单位",  # successful_bidder
        #
        # "联系电话",  # contact_information
        # "联系方式",
        # "电\s*话",

        # "联系人",  # liaison
        # "联\s*系\s*人",
        # "项目经理",
        # "项目经理（负责人）",
        # "项目负责人",


        # "招标人",  # tenderee
        # "招&nbsp;标&nbsp;人",
        # "招标单位",
        # "采购人信息[ψ \s]*?名[\s]+称",
        # "招标代理机构",

        # "招标代理",  # bidding_agency
        # "采购代理机构信息[ψ \s]*?名[\s]+称",

        # "项目编号",  # project_number
        # "招标项目编号",
        # "招标编号",
        # "编号",

        # "项目金额",  # budget_amount
        # "预算金额（元）",

        # "中标价格",  # bid_amount
        # "中标价",
        # "中标（成交）金额(元)",

        # "招标方式",

        # "开标时间",  # tenderee
        # "开启时间",

        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
    # ], field_name='project_name')
    ], field_name='project_name', area_id="3319")
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


