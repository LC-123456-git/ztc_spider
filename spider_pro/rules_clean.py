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
            "中标（成交）金额（元）", "联系人", "联 系 人", "项目经理（负责人）", "标段编号", "建设单位", "中标单位",
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
                        r'([\u4e00-\u9fa5 （ ）]*?工程)',

                        # r'本招标项目([^，,]*?)[已由 , ，]',
                        # r'项目名称：([0-9 \s \u4e00-\u9fa5]+?)三',
                        # r'根据(.*?)（[\s \u4e00-\u9fa5]*?编号：',
                        # r'本工程项目名称\s*([^，,]*?)\s*[。 , ，]',
                        # r'就([0-9 \s \u4e00-\u9fa5]+?)进行招标',
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                        # r'项目业主为([\s \u4e00-\u9fa5]*?)（下称招标人）',
                        # r'受([\s \u4e00-\u9fa5]*?)委托',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',

                        # r'招标代理[机构]*：([\s \u4e00-\u9fa5]*?)地',
                        # r'委托([^，,。]*?)[进行 , ，]',
                        # r'公告([\s \u4e00-\u9fa5]*?)受',
                    ]
                if self.field_name == 'project_number':
                    regular_list = [
                        # r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':
                    regular_list = [
                        r'预算约\s*(\d+\s*万元)',
                        r'预算约\s*(\d+\s*元)',

                        # r'预算金额.*?为(\d+)万元',
                        # r'本工程投资约(.*?)万元'
                    ]
                if self.field_name == 'bid_amount':
                    regular_list = [
                        r'中标价[: ：]\s*(\d+\s*万元)',
                        r'中标价[: ：]\s*(\d+\s*元)',
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)[招 电话]',
                        # r'电话[: ：]\s*?([0-9 \-]+?)\s*?[\u4e00-\u9fa5 \s]',
                        # r'联系电话：([0-9 \-]+?)[, ，]',
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        # 联系人：孙敏丽电话：
                        r'联\s*系\s*人[: ：]\s*([\u4e00-\u9fa5]+?)[联 电]',
                        # r'异议受理部门[: ：]\s*([\u4e00-\u9fa5]+)联',
                        # r'联系人[: ：]\s*([\u4e00-\u9fa5]+)5',
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
    <td>
        
       <table width="932" border="0" cellspacing="0" cellpadding="0" align="center">
  <tbody><tr>
    <td><table id="tblInfo" cellspacing="1" cellpadding="1" width="100%" align="center" border="0" runat="server">
                    <tbody><tr>
                      <td id="tdTitle" align="center" runat="server" height="70"><font color="" style="font-size: 25px"> <b>
                        长兴县太湖街道南张浜综合农贸市场公寓楼家用电器供货安装及伴随服务项目成交公示
                        </b></font>
                      
                        </td>
                        </tr><tr><td height="29" align="center" bgcolor="#eeeeee">
                        <font color="#545454" class="webfont">【信息时间：
                        2021/4/29
                        &nbsp;&nbsp;阅读次数：
                        <script src="/cxweb/Upclicktimes.aspx?InfoID=b637585f-0ae7-4905-8bf5-f0d773be2838"></script>16
                        】<a href="javascript:void(0)" onclick="window.print();"><font color="#545454" class="webfont">【我要打印】</font></a><a href="javascript:window.close()"><font color="#545454" class="webfont">【关闭】</font></a></font><font color="#000000">
                        
                        </font></td>
                    </tr>
                    <tr>
                      <td height="10"></td>
                    </tr>
                    <tr>
                      <td height="250" align="left" valign="top" class="infodetail" id="TDContent"><div>
                          <p class="MsoNormal" style="TEXT-ALIGN: center" align="center"><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 16pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><!--?xml:namespace prefix = "o" /--><o:p></o:p></span></b></p>
<p class="MsoNormal" style="TEXT-ALIGN: center" align="center"><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 15pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><font face="宋体">长兴县太湖街道南张浜综合农贸市场公寓楼家用电器供货安装及伴随服务项目【中标公示】</font></span></b><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 15pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><o:p></o:p></span></b></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; MARGIN-LEFT: 72.1pt; LINE-HEIGHT: 20pt; TEXT-INDENT: -72pt; mso-para-margin-left: 0.0100gd; mso-char-indent-count: -6.0000; mso-line-height-rule: exactly"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">长兴县太湖街道南张浜综合农贸市场公寓楼家用电器供货安装及伴随服务项目于</font><font face="宋体">2021年4月</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt">28</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">日上午</font><font face="宋体">9:00时在长兴县太湖街道办事处开标室（陈王路299号，太湖街道办事处停车场北侧，原老七小）</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">进行公开开标。根据招标文件规定的程序和评标办法的规定，经评标委员会评定，确定中标候选人如下：</font> </span><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><o:p></o:p></span></b></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24.1pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><o:p></o:p></span></b></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24.1pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><b style="mso-bidi-font-weight: normal"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-ansi-font-weight: bold; mso-font-kerning: 1.0000pt"><font face="宋体">中标人情况</font></span></b><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">：</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">中标人：</font></span><b><u><span style="FONT-SIZE: 12pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt; text-underline: single"><font face="宋体">浙江兴悦机电设备有限公司</font></span></u></b><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">；</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">中标价：</font></span><b><u><span style="FONT-SIZE: 12pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt; text-underline: single"><font face="宋体">304710</font></span></u></b><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">元；</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">质量目标：</font></span><b><u><span style="FONT-SIZE: 12pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt; text-underline: single"><font face="宋体">合格</font></span></u></b><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">；</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">工期：</font></span><b><u><span style="FONT-SIZE: 12pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt; text-underline: single">15</span></u></b><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">日历天。</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">废标情况：无。</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; mso-line-height-rule: exactly"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">特此公示！（公示时间：</font><font face="宋体">202</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt">1</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">年</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt">4</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">月</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">29</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">日至</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt">5</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">月</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt">6</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"><font face="宋体">日）</font></span><span style="FONT-SIZE: 6pt; FONT-FAMILY: 宋体; BACKGROUND: rgb(255,0,0); COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt; mso-highlight: rgb(255,0,0)"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">投诉监督联系电话：</font><font face="宋体">0572-6685939</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal" style="LAYOUT-GRID-MODE: char; TEXT-ALIGN: left; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoPlainText" style="TEXT-ALIGN: right; LINE-HEIGHT: 20pt; TEXT-INDENT: 24pt; mso-char-indent-count: 2.0000; mso-line-height-rule: exactly; mso-layout-grid-align: none" align="right"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); mso-spacerun: 'yes'; mso-font-kerning: 0.0000pt"></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt; mso-bidi-font-family: 'Courier New'"><font face="宋体">长兴县太湖街道南张浜村股份经济合作社</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><o:p></o:p></span></p>
<p class="MsoNormal"><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体"> 2021年4月</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt">28</span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"><font face="宋体">日</font></span><span style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体; mso-spacerun: 'yes'; mso-font-kerning: 1.0000pt"></span></p>
                        </div>
                        <div>
                          
                        </div></td>
                    </tr>
                    <tr>
                      <td align="right">
                      
                      <br>
                        </td>
                    </tr>
                    <tr id="trAttach" runat="server">
                      <td align="left"><table id="filedown" cellspacing="1" cellpadding="1" width="100%" border="0" runat="server">
                          <tbody><tr>
                            <td valign="top" style="font-size: medium;"><b>
                               
                              </b></td>
                          </tr>
                        </tbody></table></td>
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
                  </tbody></table></td>
  </tr>
</tbody></table>
 
        
        </td>
    """

    ke = KeywordsExtract(content, [
        # "项目名称",  # project_name
        # "招标项目",
        # "工程名称",
        # "招标工程项目",
        # "标项名称",

        # "中标单位",  # successful_bidder

        # "联系电话",  # contact_information
        # "联系方式",
        # "电\s*话",

        # "联系人",  # liaison
        # "联\s*系\s*人",
        # "项目经理",
        # "项目经理（负责人）",
        # "项目负责人",

        # "招标人",  # tenderee
        # "招 标 人",
        # "招&nbsp;标&nbsp;人",
        # "招\s*?标\s*?人：",
        # "招标单位",
        # "采购人信息[ψ \s]*?名[\s]+称",
        # "建设（招标）单位",
        # "建设单位",

        # "招标代理",  # bidding_agency
        # "采购代理机构信息[ψ \s]*?名[\s]+称",

        # "项目编号",  # project_number
        # "招标项目编号",
        # "招标编号",
        # "编号",
        # "标段编号",

        # "项目金额",  # budget_amount
        # "预算金额（元）",

        "中标价格",  # bid_amount
        "中标价",
        "中标（成交）金额(元)",

        # "招标方式",

        # "开标时间",  # tenderee
        # "开启时间",

        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
        # ], field_name='project_name')
    ], field_name='bid_amount', area_id="3319")
    # ke = KeywordsExtract(content, ["项目编号"])
    ke.fields_regular = {
        'project_name': [
            r'%s[^ψ：:。，,、”“"]*?[: ： \s]+?\s*?[ψ]*?([^ψ]+?)ψ',
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

    print(ke.get_value())
