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
                if re.findall("金额", key):
                    return str(int(ke.get_value()) / 10000)
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
            "招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称", "工程名称", "项目名称", "成交价格", "招标工程项目", "项目编号", "招标项目编号",
            "招标编号", "招标人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构", "项目金额", "预算金额（元）", "招标估算价",
            "中标（成交）金额（元）", "联系人", "项目经理（负责人）", "建设单位", "中标单位", "中标价", "退付类型",
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
            if val:
                break
        return val

    def format_fields(self):
        """
        - 符合条件的格式化结果
        - 不符合条件的置空
        """
        if re.search('[:：]', self._value):
            self._value = ''

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
            project_priority = ['转让', '出租', '转租', '拍卖', '出让', '公告', '公示', '项目', '工程']
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
                        r'预算约\s*(\d+\.\d+?万元)',
                        r'预算约\s*(\d+\s*元)',
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\.\d+?万元)',
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
                    # 招 标 人：龙游县双江水利开发有限公司 招标
                    regular_list = [
                        r'招\s*标\s*人[:：]([\u4e00-\u9fa5 （ ）]+?)招标'
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'project_number':
                    # 项目编号：LYSYZD-2021-001 社阳
                    regular_list = [
                        r'项目代码[: ：\s]*([0-9 \-]*?)[^\d+-]',
                        r'招标编号[：:]([0-9 A-Z a-z \- \s]+?)1\. 招标',
                        r'编号[：:]([0-9 A-Z a-z \- \s]+?)[\)\(（）]',
                        r'项目编号[：:]([0-9 A-Z a-z \- \s]*?)[\u4e00-\u9fa5]{1}',
                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'投资限额约\s*(\d+\s*万元)',
                        r'预算造价约\s*([0-9 \.]+?\s*亿元)',
                        r'预算价：审定价\s*([0-9 \.]+?\s*元)',
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
                        r'电\s*话[:：]([^\u4e00-\u9fa5]+?)[\u4e00-\u9fa5。，,]',
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
            # 预算造价约3.9994亿元
            com = re.compile(r'([0-9 .]+)')
            if re.search('万元', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0]) * 10000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('亿元|亿', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0]) * 100000000))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            elif re.search('元', self._value):
                try:
                    values = com.findall(self._value)
                    self._value = str(KeywordsExtract.remove_rest_zero(Decimal(values[0])))
                except Exception as e:
                    self.msg = 'error:{0}'.format(e)
            else:
                pass
        if self.field_name == 'project_name':
            com = re.compile(r'([\[【][\u4e00-\u9fa5]+?[】 \]])')
            suffix_trash = com.findall(self._value)
            if suffix_trash:
                suffix_trash = suffix_trash[0]
                self._value = ''.join(self._value.split(suffix_trash))

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_text()
        self._extract_from_table()
        self.done_after_extract()  # 通用提取后各地区处理
        self.clean_value()
        return self._value


if __name__ == '__main__':
    content = """
<div class="detContent">
    <p>&nbsp;&nbsp;<span
            style="letter-spacing: -1px; font-family: 宋体; font-size: 19px; -ms-layout-grid-mode: line;"><strong>LYSG2021-069-048</strong></span>
    </p>
    <p>　　1. 招标条件</p>
    <p>　　龙游县庙下溪(西源)重点山洪沟防洪治理工程已由浙水灾防[2021]10号批准建设，建设资金来源为财政拨款。项目法人为龙游县双江水利开发有限公司，招标代理机构为浙江中际工程项目管理有限公司。项目已具备招标条件，现对本项目的施工标进行公开招标。
    </p>
    <p>　　2.项目概况与招标范围</p>
    <p>　　2.1项目概况：龙游县庙下溪(西源)重点山洪沟防洪治理工程治理范围为龙游县庙下乡严村村、梅林村附近河道。本工程共计治理河道长1.63km，共涉及2个行政村;工程实施后，直接保护人口2200人，保护农田465亩。通过岸坡整治，提高岸坡抗冲能力，稳定岸线。工程任务以防洪为主，通过护坡整治等措施，提高河道的防冲能力，降低洪涝灾害对周围居民的危害。
    </p>
    <p>　　2.2本次招标范围：治理河道长1.63km，共新建护岸2.008km，其中左岸1.012km，右岸0.996km，新建下河台阶5座，新建排水涵管8处等，具体以施工图纸及工程量清单为准，财政审定预算造价为9561327元(其中暂列金450000元)。
    </p>
    <p>　　3.投标人资格要求</p>
    <p>　　3.1本次招标要求投标人具备水利水电工程施工总承包叁级及以上资质。</p>
    <p>　　3.2项目负责人具有水利水电工程二级及以上建造师注册证书，B证，无在建工程。</p>
    <p>　　3.3其他条件详见附表。</p>
    <p>　　3.4本次招标不接受联合体投标。</p>
    <p>　　4.招标文件的获取</p>
    <p>　　4.1凡有意参加投标者，应当在龙游县公共资源电子交易平台进行企业注册(网址：http://47.114.123.93:8480/login)，然后方可登陆该系统参与下载招标文件等业务操作，未登录电子交易系统的业务操作行为一律无效。
    </p>
    <p>　　4.2完成企业注册后，请及时通过互联网使用账号登录“龙游县公共资源电子交易平台”，明确所投标段并下载招标文件、工程量清单文件(若有)、施工图纸(若有)。</p>
    <p>　　4.3根据国家相关法律法规的要求，龙游县公共资源电子交易系统不再单独设立网上投标报名操作，投标人下载标书、缴纳投标保证金后即视为已确认参与项目投标。</p>
    <p>　　4.4龙游县公共资源电子交易系统操作手册请各投标人自行前往龙游县公共资源交易中心门户网站(网站地址：http://ztb.longyou.gov.cn/)下载查阅。</p>
    <p>　　4.5招标文件400元/份，开标现场缴纳，售后不退。</p>
    <p>　　4.6本工程水利工程商务报价实行电子辅助评标，龙游县公共资源交易中心电子评标辅助系统采用杭州品茗公司软件，评标软件技术服务费200元/套，技术支持联系电话：18268884008 程之童，开标现场缴纳，售后不退。</p>
    <p>　　5.投标保证金</p>
    <p>　　5.1本工程投标保证金金额为壹拾陆万元，投标保证金支付必须登陆龙游县公共资源电子交易平台获取投标保证金缴纳说明，并严格按照该说明的信息进行保证金的缴纳;未登录电子交易平台获取保证金缴纳说明的投标企业，评标专家委员会可认为该企业未按照招标文件要求正确缴纳投标保证金，并否决其投标。
    </p>
    <p>　　5.2投标保证金的缴纳方式：</p>
    <p>　　①转账(电汇或网银)请不要使用“支付宝”等第三方支付平台)，并通过“龙游县公共资源电子交易平台”取得相应的银行账号后支付，具体详见龙游县公共资源交易中心网站“龙游县公共资源电子交易平台网上缴纳保证金操作示意卡”。</p>
    <p>　　②保函(具体详见龙游县公共资源交易中心网站“关于电子交易平台电子保函(保单)的通知”)，咨询电话：4006-613-069。</p>
    <p>　　5.3投标保证金缴纳必须使用“龙游县公共资源电子交易平台”，并在投标保证金缴纳截止时间前到账(因各银行系统到账时间不同，请尽量提前缴纳)。</p>
    <p>　　5.4投标单位汇出账号必须是“龙游县公共资源电子交易平台”中注册登记的银行基本账户账号。</p>
    <p>　　5.5因投标人未规范操作引起的保证金递交无效或系统验证匹配失败的，其投标文件不予接收。</p>
    <p>　　温馨提醒：以下情形可能造成投标保证金未及时到账或被系统验证匹配失败：</p>
    <p>　　⑴投标保证金以收款人的银行到账时间为准，在途资金无效，视为未按时缴纳。</p>
    <p>　　⑵账号根据不同工程(标段)由系统随机生成，此虚拟账号只在本工程(标段)中使用有效，请注意核对。账号漏填、混填或错填均视为未按时缴纳保证金。</p>
    <p>　　(3)保证金要求单笔付款，并且与“缴纳订单”中的金额一致。</p>
    <p>　　(4)为确保保证金及时到账，建议使用电汇加急或网银加急方式进行汇款(人民银行系统开放时间为周一至周五9:00至17:00，若周一为投标截止期的，请在上周五确保资金到账)。</p>
    <p>　　⑸投标人已获取或未获取虚拟账号，而使用其他企业的虚拟账号进行转账的，应认定为串通投标行为，其投标作无效标处理。</p>
    <p>　　出现提醒未尽情况，请咨询品茗公司技术服务人员：蒋文瑞 15068085526。</p>
    <p>　　5.6本项目投标保证金缴纳截止时间为：2021年6月8日15时00分00秒;请投标人在截止时间前完成投标保证金缴纳并确认成功入账。</p>
    <p>　　6.投标文件的递交</p>
    <p>　　6.1投标文件递交的截止时间(投标截止时间，下同)： 2021 年 6 月 9 日 9 时 30 分整;地点：龙游县公共资源交易中心 2 楼 1 号开标室(龙游县龙翔路378号，原香溢市场西侧)。</p>
    <p>　　6.2逾期送达的或者未送达指定地点的或不按照招标文件要求密封的投标文件，招标人将予以拒收。</p>
    <p>　　7.开标现场相关注意事项</p>
    <p>　　7.1根据疫情防控需要限定参与人数要求，每家投标企业只委托一名人员参与现场投标。参与现场投标人员应当携带身份证等户籍证明原件，必须具有浙江省健康码(绿码)，并对健康码(绿码)真实性负责，因投标人员未能提供浙江省健康码(绿码)或体温不正常(发烧)等现象的，投标文件将拒绝接收。现场投标人员全程佩戴口罩，做好自身防护措施。进入门岗出示健康码，配合做好体温测量方可进入，进开标室如实做好登记。
    </p>
    <p>　　7.2因本次项目投标现场需测量体温等相关事宜，请各投标人合理安排时间，尽量提早到场。</p>
    <p>　　8. 发布公告的媒介</p>
    <p>　　本次招标公告同时在浙江省公共资源交易服务平台、龙游县公共资源交易中心网上发布。</p>
    <p>　　9. 联系方式</p>
    <p>　　招 标 人：龙游县双江水利开发有限公司</p>
    <p>　　招标代理人：浙江中际工程项目管理有限公司</p>
    <p>　　联 系 人：许先生</p>
    <p>　　联 系 电 话：13957027071(687071)</p>
    <p>　　2021年5月18日</p>
    <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    </p>
    <p style="margin: 8px 0px; text-align: center;"><strong><span
                style="font-family: 宋体; -ms-layout-grid-mode: line;">投标人资格条件要求附表</span></strong></p>
    <table cellspacing="0" cellpadding="0">
        <tbody>
            <tr class="firstRow" style="height: 40px;">
                <td width="49" height="40"
                    style="padding: 0px 7px; border: 1px solid windowtext; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">序号</span></strong>
                    </p>
                </td>
                <td width="569" height="40"
                    style="border-width: 1px 1px 1px 0px; border-style: solid solid solid none; border-color: windowtext windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">资
                                格 条 件 内 容</span></strong></p>
                </td>
            </tr>
            <tr style="height: 30px;">
                <td width="49" height="30"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">一</span></strong>
                    </p>
                </td>
                <td width="569" height="30"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">企业</span></strong>
                    </p>
                </td>
            </tr>
            <tr style="height: 42px;">
                <td width="49" height="42"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">1</span>
                    </p>
                </td>
                <td width="569" height="42"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">应具备水利水电工程施工总承包叁级及以上资质，具有有效的营业执照和安全生产许可证。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 37px;">
                <td width="49" height="37"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">2</span>
                    </p>
                </td>
                <td width="569" height="37"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">应未被项目所在地区（县级或市级或省级）水利建设市场限制投标。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 37px;">
                <td width="49" height="37"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">3</span>
                    </p>
                </td>
                <td width="569" height="37"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">投标人被列为失信被执行人的，因串通投标等行为被立案调查的，谢绝参与投标。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">二</span></strong>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">拟派项目组主要人员</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">1</span>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">项目负责人应持有水利水电工程二级及以上建造师注册证书，并在投标截止日不得在其他任何在建合同工程中担任项目负责人（符合浙政发【2021】5号文件规定）。其他在建合同工程的开始时间为合同工程中标通知书发出之日（不通过招标方式的，开始时间为合同签订之日），结束时间为该合同工程通过验收或合同解除之日。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 34px;">
                <td width="49" height="34"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">2</span>
                    </p>
                </td>
                <td width="569" height="34"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">项目负责人应未被项目所在地区（县级或市级或省级）水利建设市场限制投标。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">3</span>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">项目技术负责人应具有水利中级及以上职称证书。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">4</span>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">项目安全员、质检员和施工员必须持有省级及以上水行政主管部门颁发或认可的上岗证。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><strong><span
                                style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">三</span></strong>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">其它</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 47px;">
                <td width="49" height="47"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">1</span>
                    </p>
                </td>
                <td width="569" height="47"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">申请人的“三类人员”（企业主要负责人、项目负责人、专职安全生产管理人员）必须持有省级及以上水行政主管部门颁发的安全生产考核合格证书（A、B、C证），其中企业技术负责人、总经理、分管安全生产的副总经理应有任命文件；专职安全生产管理人员不少于1人。
                        </span></p>
                </td>
            </tr>
            <tr style="height: 84px;">
                <td width="49" height="84"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">2</span>
                    </p>
                </td>
                <td width="569" height="84"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="-ms-layout-grid-mode: char;"><span
                            style="font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">拟派项目组主要人员（指项目负责人、项目技术负责人、专职安全生产管理人员、安全员、质检员、施工员，下同）必须已在
                            “浙江省水利建设市场信息平台”上公示，外地进浙施工企业的委托代理人必须是在“浙江省水利建设市场信息平台”上已经公示的授权委托人。</span></p>
                </td>
            </tr>
            <tr style="height: 93px;">
                <td width="49" height="93"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">3</span>
                    </p>
                </td>
                <td width="569" height="93"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">投标人及其拟派项目负责人近三年（2018年1月1日以来）无行贿犯罪记录。招标人在定标前将通过中国裁判文书网（http://wenshu.court.gov.cn/）按照招标文件约定对拟中标单位及其拟派项目负责人的行贿犯罪记录进行查询，查询结果以网站页面显示内容为准。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 74px;">
                <td width="49" height="74"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">4</span>
                    </p>
                </td>
                <td width="569" height="74"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">项目负责人、项目技术负责人、施工员、质检员、安全员、专职安全生产管理人员应为不同的人员担任</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 57px;">
                <td width="49" height="57"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">5</span>
                    </p>
                </td>
                <td width="569" height="57"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">投标人及其法人控股其他公司，不得参加同一标段或未划分标段的同一招标项目投标，否则按否决投标处理。</span>
                    </p>
                </td>
            </tr>
            <tr style="height: 74px;">
                <td width="49" height="74"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">6</span>
                    </p>
                </td>
                <td width="569" height="74"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">根据《浙江省水利厅关于全面启用水利水电施工企业“三类人员”电子证书的公告》（浙水监督[2020]1
                            号）规定，由浙江省水利厅颁发的企业主要负责人、项目负责人、专职安全生产管理人员的安全生产考核合格证书（A、B、C
                            证），以浙江省水利厅颁发的电子证书为准，原浙江省水利厅颁发的纸质证书不予认可。 &nbsp; </span></p>
                </td>
            </tr>
            <tr style="height: 74px;">
                <td width="49" height="74"
                    style="border-width: 0px 1px 1px; border-style: none solid solid; border-color: rgb(0, 0, 0) windowtext windowtext; padding: 0px 7px; background-color: transparent;">
                    <p style="text-align: center; line-height: 125%;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">7</span>
                    </p>
                </td>
                <td width="569" height="74"
                    style="border-width: 0px 1px 1px 0px; border-style: none solid solid none; border-color: rgb(0, 0, 0) windowtext windowtext rgb(0, 0, 0); padding: 0px 7px; -ms-word-break: break-all; background-color: transparent;">
                    <p style="line-height: 125%; -ms-layout-grid-mode: char;"><span
                            style="line-height: 125%; font-family: 宋体; font-size: 14px; -ms-layout-grid-mode: line;">涉及投标人资质延续相关事宜，依据住房与城乡建设部发布的《住房和城乡建设部办公厅关于建设工程企业资质延续有关事项的通知》建办市函〔2020〕334
                            号文件执行。</span></p>
                </td>
            </tr>
        </tbody>
    </table>
    <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p>
    <p></p>
    <p style="line-height: 16px;"><img src="/plugins/editor/dialogs/attachment/fileTypeImages/icon_pdf.gif"> <a
            target="_blank" style="font-size:12px; color:#0066cc;" href="/public/gateway/202105/16213301811260.pdf"
            title="招标公告附件.pdf">招标公告附件.pdf</a></p>
</div>
    """
    ke = KeywordsExtract(content, [
        # "项目名称",  # project_name
        # "采购项目名称",
        # "招标项目",
        # "工\s*程\s*名\s*称",
        # "招标工程项目",
        # "工程名称",

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
        # "项目联系人",
        # "填报人",

        "招标人",  # tenderee
        "招 标 人",
        "招&nbsp;标&nbsp;人",
        "招\s*?标\s*?人：",
        "招标单位",
        "采购人信息[ψ \s]*?名[\s]+称",
        "建设（招标）单位",
        "建设单位",
        "采购单位名称",
        "采购人信息",
        "建设单位",

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

        # "开标时间",
        # "开启时间",

        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
        # ], field_name='project_name')
    ], field_name='tenderee', area_id="3326")
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
