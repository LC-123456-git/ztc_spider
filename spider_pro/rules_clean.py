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
                    # 联系电话: 7023931 (手机:1785821930
                    regular_list = [
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
<div id="app" style="display: block;">
    <div>
        <h2 style="text-align: center;">龙游县模环乡坞坎村垦造耕地项目二2021</h2>
        <!---->
        <h3 class="time">发布时间：2021-06-11&nbsp;&nbsp;&nbsp;&nbsp;阅读次数：148&nbsp;&nbsp;&nbsp;&nbsp;<span>【打印】</span> 分享：
            <i title="分享到微信" class="weiIcon"></i> <i title="分享到微博" class="boIcon"></i></h3>
        <div class="qrCodeBox" style="display: none;">
            <div class="qrCode">
                <div class="title">
                    <h4>分享到微信朋友圈</h4> <span class="closeQR">x</span>
                </div>
                <div id="qrcode"></div>
                <p>打开微信，点击底部的“发现”，</p>
                <p>使用“扫一扫”即可将网页分享至朋友圈。</p>
            </div>
        </div>
        <!---->
        <!---->
        <div class="detContent">


            <meta http-equiv="Content-Type" content="text/html;charset=utf-8">


            <p style="font-size:20px;font-weight:bold;text-align:center;padding:10px 0px;">
                龙游县模环乡坞坎村垦造耕地项目二2021（龙游县模环乡坞坎村垦造耕地项目二2021）开标记录表
            </p>
            <p>
                <span style="float:left;">开标时间：2021-06-11 11:00:00</span>
            </p>
            <p>（一）唱标记录</p>
            <p>
                <table style="width:100%;line-height:30px;boder:0px;" border="1px" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr>
                            <th>
                                序号
                            </th>
                            <th>
                                投标人名称
                            </th>
                            <th>
                                密封情况
                            </th>
                            <th>
                                投标保证金
                            </th>
                            <th>
                                投标报价
                            </th>
                            <th>
                                工期（日历天）
                            </th>
                            <th>
                                质量目标
                            </th>
                            <th>
                                项目经理
                            </th>
                        </tr>


                        <tr>
                            <td>
                                1
                            </td>
                            <td>
                                衢州迅捷建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                王文潮
                            </td>
                        </tr>
                        <tr>
                            <td>
                                2
                            </td>
                            <td>
                                衢州艺洋建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格标准，且通过省级验收
                            </td>
                            <td>
                                许碧肖
                            </td>
                        </tr>
                        <tr>
                            <td>
                                3
                            </td>
                            <td>
                                浙江龙游永恒建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                陈安莉
                            </td>
                        </tr>
                        <tr>
                            <td>
                                4
                            </td>
                            <td>
                                龙游天辰环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格标准，且通过省级验收
                            </td>
                            <td>
                                孙浩
                            </td>
                        </tr>
                        <tr>
                            <td>
                                5
                            </td>
                            <td>
                                浙江晨烨建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                方伟平
                            </td>
                        </tr>
                        <tr>
                            <td>
                                6
                            </td>
                            <td>
                                浙江鹤宇建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                唐小琴
                            </td>
                        </tr>
                        <tr>
                            <td>
                                7
                            </td>
                            <td>
                                浙江创惠建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吴安月
                            </td>
                        </tr>
                        <tr>
                            <td>
                                8
                            </td>
                            <td>
                                浙江宏捷建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格 ，且通过省级验收
                            </td>
                            <td>
                                吴娟
                            </td>
                        </tr>
                        <tr>
                            <td>
                                9
                            </td>
                            <td>
                                浙江龙建建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吕晓峰
                            </td>
                        </tr>
                        <tr>
                            <td>
                                10
                            </td>
                            <td>
                                浙江龙游锦瑞环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                平夏英
                            </td>
                        </tr>
                        <tr>
                            <td>
                                11
                            </td>
                            <td>
                                浙江衢州巨能建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐林英
                            </td>
                        </tr>
                        <tr>
                            <td>
                                12
                            </td>
                            <td>
                                龙游飞凌生态建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                刘欢
                            </td>
                        </tr>
                        <tr>
                            <td>
                                13
                            </td>
                            <td>
                                浙江龙游汉晟建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                邱怀益
                            </td>
                        </tr>
                        <tr>
                            <td>
                                14
                            </td>
                            <td>
                                衢州晟天建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐海霞
                            </td>
                        </tr>
                        <tr>
                            <td>
                                15
                            </td>
                            <td>
                                浙江培华建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                余建娜
                            </td>
                        </tr>
                        <tr>
                            <td>
                                16
                            </td>
                            <td>
                                浙江龙游大汇建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吴建忠
                            </td>
                        </tr>
                        <tr>
                            <td>
                                17
                            </td>
                            <td>
                                龙游高盛环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                王梅
                            </td>
                        </tr>
                        <tr>
                            <td>
                                18
                            </td>
                            <td>
                                浙江衢州盈鑫环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                邵亚卿
                            </td>
                        </tr>
                        <tr>
                            <td>
                                19
                            </td>
                            <td>
                                龙游亿中顺环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                胡柏卿
                            </td>
                        </tr>
                        <tr>
                            <td>
                                20
                            </td>
                            <td>
                                浙江璟瑞建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                琚红燕
                            </td>
                        </tr>
                        <tr>
                            <td>
                                21
                            </td>
                            <td>
                                浙江万明建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                方柳梅
                            </td>
                        </tr>
                        <tr>
                            <td>
                                22
                            </td>
                            <td>
                                龙游凤舞建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐臣彬
                            </td>
                        </tr>
                        <tr>
                            <td>
                                23
                            </td>
                            <td>
                                浙江龙游万壑建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                金小亮
                            </td>
                        </tr>
                        <tr>
                            <td>
                                24
                            </td>
                            <td>
                                浙江龙游天泓建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                杨建伟
                            </td>
                        </tr>
                        <tr>
                            <td>
                                25
                            </td>
                            <td>
                                龙游晨鑫建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                张金峰
                            </td>
                        </tr>
                        <tr>
                            <td>
                                26
                            </td>
                            <td>
                                龙游露鑫建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐松青
                            </td>
                        </tr>
                        <tr>
                            <td>
                                27
                            </td>
                            <td>
                                浙江旭宏建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                姚旱军
                            </td>
                        </tr>
                        <tr>
                            <td>
                                28
                            </td>
                            <td>
                                浙江欧骏建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                陈建
                            </td>
                        </tr>
                        <tr>
                            <td>
                                29
                            </td>
                            <td>
                                浙江通衢水电建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吴祺立
                            </td>
                        </tr>
                        <tr>
                            <td>
                                30
                            </td>
                            <td>
                                浙江龙游振宇建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                叶飞
                            </td>
                        </tr>
                        <tr>
                            <td>
                                31
                            </td>
                            <td>
                                龙游凤翔洲建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                温彬彬
                            </td>
                        </tr>
                        <tr>
                            <td>
                                32
                            </td>
                            <td>
                                浙江伟正建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                缪建雄
                            </td>
                        </tr>
                        <tr>
                            <td>
                                33
                            </td>
                            <td>
                                浙江同纬建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                赖慧君
                            </td>
                        </tr>
                        <tr>
                            <td>
                                34
                            </td>
                            <td>
                                浙江山铁园林建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                徐建祥
                            </td>
                        </tr>
                        <tr>
                            <td>
                                35
                            </td>
                            <td>
                                浙江意林建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                江凯丽
                            </td>
                        </tr>
                        <tr>
                            <td>
                                36
                            </td>
                            <td>
                                浙江通辉建筑有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                杨梅
                            </td>
                        </tr>
                        <tr>
                            <td>
                                37
                            </td>
                            <td>
                                浙江聚辉建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                马观福
                            </td>
                        </tr>
                        <tr>
                            <td>
                                38
                            </td>
                            <td>
                                龙游县通程建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                席锡荣
                            </td>
                        </tr>
                        <tr>
                            <td>
                                39
                            </td>
                            <td>
                                衢州同豪建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                陈彬
                            </td>
                        </tr>
                        <tr>
                            <td>
                                40
                            </td>
                            <td>
                                浙江龙游旭峰环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                李阳
                            </td>
                        </tr>
                        <tr>
                            <td>
                                41
                            </td>
                            <td>
                                浙江龙游熠华建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                夏旭红
                            </td>
                        </tr>
                        <tr>
                            <td>
                                42
                            </td>
                            <td>
                                浙江鑫品建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                胡金平
                            </td>
                        </tr>
                        <tr>
                            <td>
                                43
                            </td>
                            <td>
                                浙江龙游鸿宇环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                郑秦燕
                            </td>
                        </tr>
                        <tr>
                            <td>
                                44
                            </td>
                            <td>
                                浙江泰宇建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                方群
                            </td>
                        </tr>
                        <tr>
                            <td>
                                45
                            </td>
                            <td>
                                浙江衢州晨涵建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                郑志成
                            </td>
                        </tr>
                        <tr>
                            <td>
                                46
                            </td>
                            <td>
                                浙江衢州雨林建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                陈玲敏
                            </td>
                        </tr>
                        <tr>
                            <td>
                                47
                            </td>
                            <td>
                                浙江龙游泰安爆破工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                蒋朝晖
                            </td>
                        </tr>
                        <tr>
                            <td>
                                48
                            </td>
                            <td>
                                衢州盈益建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                邱盈
                            </td>
                        </tr>
                        <tr>
                            <td>
                                49
                            </td>
                            <td>
                                浙江鸿飞环境工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                王超然
                            </td>
                        </tr>
                        <tr>
                            <td>
                                50
                            </td>
                            <td>
                                浙江龙游锦鹏环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                翁秀娣
                            </td>
                        </tr>
                        <tr>
                            <td>
                                51
                            </td>
                            <td>
                                浙江龙游森凯建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐晓东
                            </td>
                        </tr>
                        <tr>
                            <td>
                                52
                            </td>
                            <td>
                                浙江龙游瑞晟建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                张洪财
                            </td>
                        </tr>
                        <tr>
                            <td>
                                53
                            </td>
                            <td>
                                浙江龙游安瑞建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐兵
                            </td>
                        </tr>
                        <tr>
                            <td>
                                54
                            </td>
                            <td>
                                龙游宝吉建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                胡婷
                            </td>
                        </tr>
                        <tr>
                            <td>
                                55
                            </td>
                            <td>
                                浙江利兴建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                阮洁莹
                            </td>
                        </tr>
                        <tr>
                            <td>
                                56
                            </td>
                            <td>
                                浙江玖龙建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                张露莉
                            </td>
                        </tr>
                        <tr>
                            <td>
                                57
                            </td>
                            <td>
                                浙江六为建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                夏方园
                            </td>
                        </tr>
                        <tr>
                            <td>
                                58
                            </td>
                            <td>
                                衢州市晟民建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                徐项斌
                            </td>
                        </tr>
                        <tr>
                            <td>
                                59
                            </td>
                            <td>
                                浙江龙游和中建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                叶子挺
                            </td>
                        </tr>
                        <tr>
                            <td>
                                60
                            </td>
                            <td>
                                衢州诺泽建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收 合格，并通过省级验收
                            </td>
                            <td>
                                琚根生
                            </td>
                        </tr>
                        <tr>
                            <td>
                                61
                            </td>
                            <td>
                                浙江畅达建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吕星
                            </td>
                        </tr>
                        <tr>
                            <td>
                                62
                            </td>
                            <td>
                                衢州市晟佳建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天。
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收 ;
                            </td>
                            <td>
                                冯小美
                            </td>
                        </tr>
                        <tr>
                            <td>
                                63
                            </td>
                            <td>
                                衢州方源建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                林尚想
                            </td>
                        </tr>
                        <tr>
                            <td>
                                64
                            </td>
                            <td>
                                浙江龙游晟达建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                郭姝博
                            </td>
                        </tr>
                        <tr>
                            <td>
                                65
                            </td>
                            <td>
                                衢州锦华环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                翁立珍
                            </td>
                        </tr>
                        <tr>
                            <td>
                                66
                            </td>
                            <td>
                                龙游新宸建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                陈荣财
                            </td>
                        </tr>
                        <tr>
                            <td>
                                67
                            </td>
                            <td>
                                衢州明宇建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                季小牛
                            </td>
                        </tr>
                        <tr>
                            <td>
                                68
                            </td>
                            <td>
                                浙江欣茂环境工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐越
                            </td>
                        </tr>
                        <tr>
                            <td>
                                69
                            </td>
                            <td>
                                浙江锦昌建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                曾华
                            </td>
                        </tr>
                        <tr>
                            <td>
                                70
                            </td>
                            <td>
                                龙游美阁环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                郭敏华
                            </td>
                        </tr>
                        <tr>
                            <td>
                                71
                            </td>
                            <td>
                                龙游明翔建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                蓝君
                            </td>
                        </tr>
                        <tr>
                            <td>
                                72
                            </td>
                            <td>
                                浙江禾源建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                张凤英
                            </td>
                        </tr>
                        <tr>
                            <td>
                                73
                            </td>
                            <td>
                                龙游欢灿建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                蓝海涛
                            </td>
                        </tr>
                        <tr>
                            <td>
                                74
                            </td>
                            <td>
                                浙江久顺环境工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                王炜
                            </td>
                        </tr>
                        <tr>
                            <td>
                                75
                            </td>
                            <td>
                                浙江衢州榕森环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                邵瑞卿
                            </td>
                        </tr>
                        <tr>
                            <td>
                                76
                            </td>
                            <td>
                                浙江龙游仁泰建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                季爱文
                            </td>
                        </tr>
                        <tr>
                            <td>
                                77
                            </td>
                            <td>
                                衢州大诚建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                楼素雅
                            </td>
                        </tr>
                        <tr>
                            <td>
                                78
                            </td>
                            <td>
                                浙江龙游茂源建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收 ;
                            </td>
                            <td>
                                祝妙
                            </td>
                        </tr>
                        <tr>
                            <td>
                                79
                            </td>
                            <td>
                                衢州泓泰建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐珍
                            </td>
                        </tr>
                        <tr>
                            <td>
                                80
                            </td>
                            <td>
                                浙江龙游金森环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                邱朝盛
                            </td>
                        </tr>
                        <tr>
                            <td>
                                81
                            </td>
                            <td>
                                浙江宏睿建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                张小松
                            </td>
                        </tr>
                        <tr>
                            <td>
                                82
                            </td>
                            <td>
                                龙游吉祥园林建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                陆婷玉
                            </td>
                        </tr>
                        <tr>
                            <td>
                                83
                            </td>
                            <td>
                                浙江衢州奥盛建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                应培峰
                            </td>
                        </tr>
                        <tr>
                            <td>
                                84
                            </td>
                            <td>
                                浙江龙游九鑫建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                余鑫
                            </td>
                        </tr>
                        <tr>
                            <td>
                                85
                            </td>
                            <td>
                                浙江龙游金澜建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                胡茂连
                            </td>
                        </tr>
                        <tr>
                            <td>
                                86
                            </td>
                            <td>
                                东欣建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                国家质量一次性验收合格标准，且通过省级验收，安全生产无事故
                            </td>
                            <td>
                                吴晓忠
                            </td>
                        </tr>
                        <tr>
                            <td>
                                87
                            </td>
                            <td>
                                衢州万坤环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐海燕
                            </td>
                        </tr>
                        <tr>
                            <td>
                                88
                            </td>
                            <td>
                                浙江龙游泰德建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                姜仁旺
                            </td>
                        </tr>
                        <tr>
                            <td>
                                89
                            </td>
                            <td>
                                衢州强晟建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吕决胜
                            </td>
                        </tr>
                        <tr>
                            <td>
                                90
                            </td>
                            <td>
                                浙江龙游晟鑫建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                杨勇
                            </td>
                        </tr>
                        <tr>
                            <td>
                                91
                            </td>
                            <td>
                                浙江龙游顺畅建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                胡晓媛
                            </td>
                        </tr>
                        <tr>
                            <td>
                                92
                            </td>
                            <td>
                                浙江龙游宏业建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐国华
                            </td>
                        </tr>
                        <tr>
                            <td>
                                93
                            </td>
                            <td>
                                衢州跃航建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                沈勤前
                            </td>
                        </tr>
                        <tr>
                            <td>
                                94
                            </td>
                            <td>
                                浙江龙游禾亿环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格 标准，且通过省级验收 安全生产无事故
                            </td>
                            <td>
                                吴剑
                            </td>
                        </tr>
                        <tr>
                            <td>
                                95
                            </td>
                            <td>
                                浙江万杰建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                方秀慧
                            </td>
                        </tr>
                        <tr>
                            <td>
                                96
                            </td>
                            <td>
                                浙江通平建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                蒋伟兰
                            </td>
                        </tr>
                        <tr>
                            <td>
                                97
                            </td>
                            <td>
                                浙江衢州建欣建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                冯骁
                            </td>
                        </tr>
                        <tr>
                            <td>
                                98
                            </td>
                            <td>
                                龙游欣远建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                袁森伟
                            </td>
                        </tr>
                        <tr>
                            <td>
                                99
                            </td>
                            <td>
                                浙江昊达建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                姜飞
                            </td>
                        </tr>
                        <tr>
                            <td>
                                100
                            </td>
                            <td>
                                浙江衢州驰翔建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吕卡
                            </td>
                        </tr>
                        <tr>
                            <td>
                                101
                            </td>
                            <td>
                                衢州春平建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                俞剑
                            </td>
                        </tr>
                        <tr>
                            <td>
                                102
                            </td>
                            <td>
                                龙游宝宸建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收 合格并通过省级验收
                            </td>
                            <td>
                                周路忞
                            </td>
                        </tr>
                        <tr>
                            <td>
                                103
                            </td>
                            <td>
                                衢州中锦建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                姜挺
                            </td>
                        </tr>
                        <tr>
                            <td>
                                104
                            </td>
                            <td>
                                龙游博悦环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                季巧凤
                            </td>
                        </tr>
                        <tr>
                            <td>
                                105
                            </td>
                            <td>
                                浙江传岐建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                合格
                            </td>
                            <td>
                                王金龙
                            </td>
                        </tr>
                        <tr>
                            <td>
                                106
                            </td>
                            <td>
                                衢州广驰建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                叶珊
                            </td>
                        </tr>
                        <tr>
                            <td>
                                107
                            </td>
                            <td>
                                浙江大玖建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                高俊鹏
                            </td>
                        </tr>
                        <tr>
                            <td>
                                108
                            </td>
                            <td>
                                龙游琪达建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                刘国红
                            </td>
                        </tr>
                        <tr>
                            <td>
                                109
                            </td>
                            <td>
                                衢州鼎振建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                江爱凤
                            </td>
                        </tr>
                        <tr>
                            <td>
                                110
                            </td>
                            <td>
                                浙江昱恒建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                吴雯
                            </td>
                        </tr>
                        <tr>
                            <td>
                                111
                            </td>
                            <td>
                                浙江龙游久京建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                周霞
                            </td>
                        </tr>
                        <tr>
                            <td>
                                112
                            </td>
                            <td>
                                浙江顶天建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，且通过省级验收
                            </td>
                            <td>
                                舒国庆
                            </td>
                        </tr>
                        <tr>
                            <td>
                                113
                            </td>
                            <td>
                                浙江千叶环境工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                毕根明
                            </td>
                        </tr>
                        <tr>
                            <td>
                                114
                            </td>
                            <td>
                                衢州长鑫环境建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                叶乐
                            </td>
                        </tr>
                        <tr>
                            <td>
                                115
                            </td>
                            <td>
                                浙江龙游通嵘建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                周大群
                            </td>
                        </tr>
                        <tr>
                            <td>
                                116
                            </td>
                            <td>
                                浙江晟俊建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                刘宣蓉
                            </td>
                        </tr>
                        <tr>
                            <td>
                                117
                            </td>
                            <td>
                                浙江艺轩园林建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                洪佳
                            </td>
                        </tr>
                        <tr>
                            <td>
                                118
                            </td>
                            <td>
                                浙江鼎鲲建设工程有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                余惠瑛
                            </td>
                        </tr>
                        <tr>
                            <td>
                                119
                            </td>
                            <td>
                                浙江龙游富鑫建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60日历天
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                徐丹
                            </td>
                        </tr>
                        <tr>
                            <td>
                                120
                            </td>
                            <td>
                                浙江泽能建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                郑云
                            </td>
                        </tr>
                        <tr>
                            <td>
                                121
                            </td>
                            <td>
                                衢州顺恒建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格
                            </td>
                            <td>
                                袁秋仁
                            </td>
                        </tr>
                        <tr>
                            <td>
                                122
                            </td>
                            <td>
                                衢州勤晟建设有限公司
                            </td>
                            <td>

                            </td>
                            <td>

                            </td>
                            <td>
                                3207867
                            </td>
                            <td>
                                60
                            </td>
                            <td>
                                一次性验收合格，并通过省级验收
                            </td>
                            <td>
                                余孝红
                            </td>
                        </tr>


                    </tbody>
                </table>
            </p>


        </div>
        <!---->
        <!---->
        <!---->
        <!---->
    </div>
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

        "开标时间",  # tenderopen_time
        "开启时间",

        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
        # ], field_name='project_name')
    ], field_name='tenderopen_time', area_id="3326")
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
