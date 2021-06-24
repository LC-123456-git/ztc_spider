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
    elif area_id in ["3309", "3320"]:
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
                        r'预算金额.*?为(\d+)万元',
                        r'本工程投资约(.*?)万元'
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
                        r'联.*系.*人[: ：]\s*([\u4e00-\u9fa5]+?)[监督投诉 电]',
                        r'异议受理部门[: ：]\s*([\u4e00-\u9fa5]+)联',
                        r'联系人[: ：]\s*([\u4e00-\u9fa5]+)5',
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

    def remove_several_symbols(self):
        """
        去除符号/替换空格为一个
        """
        symbols = ['？', '?']

        try:
            for symbol in symbols:
                self._value = ''.join(self._value.split(symbol))
            self._value = re.sub('\s+', ' ', self._value)
        except:
            pass

    def get_value(self):
        self.done_before_extract()  # 通用提取前各地区处理
        self._extract_from_text()
        self._extract_from_table()
        self.done_after_extract()  # 通用提取后各地区处理
        self.remove_several_symbols()
        return self._value


if __name__ == '__main__':
    content = """
    <tr>
    <td>
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td style="padding:10px;">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td height="120">
                                <table width="100%" height="120" border="0" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td height="30" />
                                    </tr>
                                    <tr>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td height="500" align="left" valign="top">
                                <table height="100%" width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td valign="top" class="infodetail" id="TDContent" align="left">
                                            <div style=" padding-left:40px; padding-right:40px;">
                                                <h1 style="MARGIN-BOTTOM: 0pt; MARGIN-TOP: 0pt; PAGE-BREAK-BEFORE: always; TEXT-ALIGN: center"
                                                    align="center"><b><span
                                                            style="FONT-SIZE: 22pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: bold; COLOR: rgb(0,0,0)">
                                                            <font face="宋体">招标公告</font>
                                                        </span></b></h1>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 200%"
                                                    align="center"><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">编号：</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">A3303270480001356001001</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体"> </span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 150%; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: normal">1.
                                                        <font face="黑体">招标条件</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">　　</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">本招标项目</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">苍南县灵溪新区派出所综合楼建设项目室内装修工程</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">已由</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">苍南县发展和改革局</font>
                                                        </span></u><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">以</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt; text-underline: single">
                                                            <font face="宋体">（</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">苍发改投</font>
                                                            <font face="宋体">[20</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">18</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">]</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">46</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt; text-underline: single">
                                                            <font face="宋体">）</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">号</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">批准建设</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">，项目业主为</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">苍南县城市建设投资有限公司</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">，建设资金</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">来</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt">
                                                        <font face="宋体">自</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt; text-underline: single">
                                                            <font face="宋体">自筹</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt">
                                                        <font face="宋体">，</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt">
                                                        <font face="宋体">项目出资比例为</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt; text-underline: single">
                                                            <font face="Times New Roman">100%</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.15pt">
                                                        <font face="宋体">，</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">招标人为</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">苍南县城市建设投资有限公司</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">。项目已具备招标条件，现对该项目的施工进行</font>
                                                    </span><b><span
                                                            style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                            <font face="宋体">公开招标</font>
                                                        </span></b><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">。</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">2.
                                                        <font face="黑体">项目概况与招标范围</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">　　</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">苍南县灵溪新区派出所综合楼建设项目室内装修工程</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">，</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">本次</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">招标内容包括</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">
                                                                拆除部分墙体，新砌隔墙，安装墙、地、天棚装饰面层，安装门窗，安装插座照明管线及灯具、给排水配件安装，搭设脚手架
                                                            </font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">等</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">。具体以工程量清单及施工图纸为准。</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">本工程</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">投资约</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">620</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">万元，本工程计划工期为</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">100日历天</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">，</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.3pt; text-underline: single">
                                                            <font face="宋体">建设地点为苍南县县城新区。</font>
                                                        </span></u></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">3.
                                                        <font face="黑体">投标人资格要求</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-AUTOSPACE: ; TEXT-INDENT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">3.1</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)"> 
                                                        <font face="宋体">本次招标要求投标人须具备：</font></span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">(1)</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">按住建部颁发的建市【</font>
                                                            <font face="宋体">2014】159号《建筑业企业资质标准》要求取得</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">建筑装修装饰工程专业承包贰级及以上资质</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">，</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">并在人员、设备、资金等方面具有相应的施工能力；</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">(2)</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">项目负责人：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">建筑工程专业</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">二级及以上注册建造师执业资格，</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">同时具</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">有</font>
                                                        <font face="宋体">“三类人员”安全生产考核B类合格证，并无在建工程，且符合浙政发【2014】39号文件规定。
                                                        </font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">(3)</font>
                                                    </span><b><span
                                                            style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; COLOR: rgb(0,0,0)">
                                                            <font face="宋体">浙江省外投标人必须持有《省外企业进浙承接业务备案证明》且在有效期内。</font>
                                                        </span></b></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-AUTOSPACE: ; TEXT-INDENT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">3.2
                                                        本次招标</span><b><span
                                                            style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; FONT-WEIGHT: bold; COLOR: rgb(0,0,0)">
                                                            <font face="宋体">不接受</font>
                                                        </span></b><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">联合体投标</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">，</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">应满足下列要求：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: 2.4pt; text-underline: single"> 
                                                            <font face="宋体">无</font></span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: 2.5pt"> 
                                                        <font face="宋体">。</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-AUTOSPACE: ; TEXT-INDENT: 21pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">3.3 其他要求：①在投标截止时间前，投标人未被人民法院列入限制失信被执行人投标资格名单的企业；
                                                        </font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">②</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; LETTER-SPACING: -0.15pt">
                                                        <font face="宋体">投标企业已录入浙江省建筑市场监管与诚信信息平台</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">。</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">4.
                                                        <font face="黑体">招标文件的获取</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 17.95pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">4.1 凡有意参加投标者，</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">请予本公告发布之日起至本项目投标截止时间前直接在苍南县公共资源交</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">易网上下载招标文件件及其他资料（网址为</font>
                                                        <font face="宋体">http://ggzy.cncn.gov.cn/TPFrontNe</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">w/）。 </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 10.5pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">4.2</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">本工程招标文件的质疑、澄清、修改、补充等内容在温州市公共资源交易网苍南县分网（网址：
                                                        </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt">
                                                    <span><a href="http://ggzy.cncn.gov.cn/TPFrontNew/"><span
                                                                style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                                <font face="宋体">http://ggzy.cncn.gov.cn/TPFrontNew/
                                                                </font>
                                                            </span></a></span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">）上发布信息向所有投标人公布。</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 'Times New Roman'; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">5.
                                                        <font face="黑体">投标文件的递交</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">5.</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">1</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)"> 
                                                        <font face="宋体">投标文件递交的截止时间（投标截止时间，下同）</font></span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">为</font>
                                                        <font face="宋体">2021年</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single"> 
                                                            <font face="宋体">6 </font></span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">月</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single"> 
                                                            <font face="宋体">9 </font></span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">日</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">0</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">9</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">时</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">:</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); text-underline: single">
                                                            <font face="宋体">30</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">分</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">，</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">地点（或网址）为温州市公共资源交易网苍南县分网（网址：</font>
                                                        <font face="宋体">http://ggzy.cncn.gov.cn/TPFrontNew/）。</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt">
                                                    <span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">5.</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">2</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)"> 
                                                        <font face="宋体">逾期送达的或者未送达指定地点的投标文件，招标人不予受理。</font></span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 黑体; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">
                                                        <font face="Times New Roman">6. </font>
                                                        <font face="黑体">发布公告的媒介</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 10.5pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">本次招标公告同时在浙江省公共资源交易服务平台和温州市公共资源交易网苍南县分网（网址：
                                                        </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 10.5pt">
                                                    <span><a href="http://ggzy.cncn.gov.cn/TPFrontNew/"><span
                                                                style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                                <font face="Times New Roman">
                                                                    http://ggzy.cncn.gov.cn/TPFrontNew/</font>
                                                            </span></a></span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">）上发布。</font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 14pt; MARGIN-BOTTOM: 0pt; FONT-FAMILY: 'Times New Roman'; MARGIN-TOP: 0pt; PAGE-BREAK-AFTER: avoid; FONT-WEIGHT: normal; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; LINE-HEIGHT: 21pt; TEXT-INDENT: 15.9pt">
                                                    <span
                                                        style="FONT-SIZE: 14pt; FONT-FAMILY: 黑体; FONT-WEIGHT: normal; COLOR: rgb(0,0,0)">
                                                        <font face="Times New Roman">7. </font>
                                                        <font face="黑体">其他说明</font>
                                                        <font face="Times New Roman">   </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">
                                                            7.1此项目采用电子招标投标，请登录苍南县公共资源网上交易系统填写投标信息并确认投标状态。凡有意参加此项目的投标人，必须于投标截止时间之前完成温州市建设工程招标投标交易主体信息库入库工作，否则，其投标文件将被拒绝，后果由投标人自负。
                                                        </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">7</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">.2</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">未在温州市建设工程招标投标交易主体信息库入库的单位，请按照温州市公共资源交易网</font>
                                                        <font face="宋体">
                                                            --苍南分网最新公告《关于停止办理建设工程企业库入库和基本信息变更的通知》的要求到温州市公共资源交易网登记入库和信息变更（网址：https://ggzy.wzzbtb.com/wzcms/jsxmjyl/2355.htm）。
                                                        </font>
                                                    </span></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 21pt; TEXT-INDENT: 21pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">7</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">.</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">3</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">本项目投标保证金采用网</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">上收退系统（</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">银行保函除外</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">），详见招标文件前附表</font>
                                                        <font face="宋体">3.4.1款。</font>
                                                    </span></p>
                                                <h6
                                                    style="MARGIN-BOTTOM: 0pt; MARGIN-TOP: 7.9pt; TEXT-ALIGN: left; MARGIN-RIGHT: 0pt">
                                                    <b><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 黑体; FONT-WEIGHT: bold; LETTER-SPACING: -0.1pt">
                                                            <font face="黑体">8.</font>
                                                        </span></b><b><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 黑体; FONT-WEIGHT: bold; LETTER-SPACING: -0.1pt">
                                                            <font face="黑体">联系方式</font>
                                                        </span></b></h6>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 11.6pt 0pt 0pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">招标人：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">苍南县城市建设投资有限公司</font>
                                                        </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">  </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">招标代理机构</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: 0.2pt">
                                                        <font face="宋体">：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">杭州天恒投资建设管理有限公司</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: 1.1pt; text-underline: single"> </span></u>
                                                </p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0.35pt 0pt 0pt">
                                                     </p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.8pt 0pt 0pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">地址：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.2pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">苍南县灵溪镇</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">  </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">               </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">地址：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">苍南县灵溪镇上江小区</font>
                                                            <font face="宋体">28栋1单元302室</font>
                                                        </span></u></p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; TEXT-INDENT: 21pt">
                                                     </p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.85pt 0pt 0pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">联</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.1pt"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">系</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.1pt"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">人：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.1pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">许先生</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single"> </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">                   </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">   </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">联</font>
                                                        <font face="宋体">系</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; LETTER-SPACING: -0.1pt"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">人：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.05pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">董女士</font>
                                                        </span></u></p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0.35pt 0pt 0pt">
                                                     </p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.85pt 0pt 0pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">电话：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.2pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">0577-59909057</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single"> </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">               </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">  </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">电</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">   </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">话：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: -0.3pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">0577-68800058  18815114195</font>
                                                        </span></u></p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0.35pt 0pt 0pt">
                                                     </p>
                                                <p
                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.8pt 0pt 0pt">
                                                    <span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">传真：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">0577-59909057</font>
                                                        </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single"> </span></u><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">                </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">   </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">传</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体">
                                                        <font face="宋体">真：</font>
                                                    </span><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; LETTER-SPACING: 0.05pt; text-underline: single"> </span></u><u><span
                                                            style="FONT-SIZE: 10.5pt; TEXT-DECORATION: underline; FONT-FAMILY: 宋体; text-underline: single">
                                                            <font face="宋体">0577-64798998</font>
                                                        </span></u></p>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: right; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt 23.75pt 0pt 0pt; LINE-HEIGHT: 150%; punctuation-trim: leading"
                                                    align="right"> </p>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: right; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt 23.75pt 0pt 0pt; LINE-HEIGHT: 150%; punctuation-trim: leading"
                                                    align="right"> </p>
                                                <p
                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; TEXT-INDENT: 10.5pt">
                                                     </p>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: right; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt 23.75pt 0pt 0pt; LINE-HEIGHT: 150%; punctuation-trim: leading"
                                                    align="right"><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); LINE-HEIGHT: 150%"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; BACKGROUND: rgb(255,255,255); COLOR: rgb(0,0,0); LINE-HEIGHT: 150%">
                                                        <font face="宋体">苍南县城市建设投资有限公司</font>
                                                    </span></p>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: right; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt 23.75pt 0pt 0pt; LINE-HEIGHT: 150%; punctuation-trim: leading"
                                                    align="right"><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%"> </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0); LINE-HEIGHT: 150%">
                                                        <font face="宋体">杭州天恒投资建设管理有限公司</font>
                                                    </span></p>
                                                <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Times New Roman'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt"
                                                    align="center"><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">                                                                                                                                         
                                                           </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">20</span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">21年</font>
                                                    </span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)"> 
                                                        <font face="宋体">5 </font></span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">月</font>
                                                    </span><span style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体"> <font
                                                            face="宋体">12 </font></span><span
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; COLOR: rgb(0,0,0)">
                                                        <font face="宋体">日</font>
                                                    </span></p>
                                            </div>
                                            <div> </div>
                                        </td>
                                    </tr>
                                    <tr style="display:none;">
                                        <td align="right">
                                            <br />
                                        </td>
                                    </tr>
                                    <tr>
                                        <td />
                                    </tr>
                                    <tr>
                                        <td height="10" />
                                    </tr>
                                    <tr>
                                        <td valign="bottom"><span class="infodetailattach">附件：</span>
                                            <table id="filedown" cellspacing="1" cellpadding="1" width="100%" border="0"
                                                runat="server">
                                                <tr>
                                                    <td>1、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%5BA3303270480001356001001%5D%E8%8B%8D%E5%8D%97%E5%8E%BF%E7%81%B5%E6%BA%AA%E6%96%B0%E5%8C%BA%E6%B4%BE%E5%87%BA%E6%89%80%E7%BB%BC%E5%90%88%E6%A5%BC%E5%BB%BA%E8%AE%BE%E9%A1%B9%E7%9B%AE%E5%AE%A4%E5%86%85%E8%A3%85%E4%BF%AE%E5%B7%A5%E7%A8%8B.ZJCNZF"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">
                                                                [A3303270480001356001001]苍南县灵溪新区派出所综合楼建设项目室内装修工程.ZJCNZF
                                                            </font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>2、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%5BA3303270480001356001001%5D%E8%8B%8D%E5%8D%97%E5%8E%BF%E7%81%B5%E6%BA%AA%E6%96%B0%E5%8C%BA%E6%B4%BE%E5%87%BA%E6%89%80%E7%BB%BC%E5%90%88%E6%A5%BC%E5%BB%BA%E8%AE%BE%E9%A1%B9%E7%9B%AE%E5%AE%A4%E5%86%85%E8%A3%85%E4%BF%AE%E5%B7%A5%E7%A8%8B.ZJCNZF"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">
                                                                [A3303270480001356001001]苍南县灵溪新区派出所综合楼建设项目室内装修工程.ZJCNZF
                                                            </font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>3、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%5BA3303270480001356001001%5D%E8%8B%8D%E5%8D%97%E5%8E%BF%E7%81%B5%E6%BA%AA%E6%96%B0%E5%8C%BA%E6%B4%BE%E5%87%BA%E6%89%80%E7%BB%BC%E5%90%88%E6%A5%BC%E5%BB%BA%E8%AE%BE%E9%A1%B9%E7%9B%AE%E5%AE%A4%E5%86%85%E8%A3%85%E4%BF%AE%E5%B7%A5%E7%A8%8B.ZJCNZF"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">
                                                                [A3303270480001356001001]苍南县灵溪新区派出所综合楼建设项目室内装修工程.ZJCNZF
                                                            </font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>4、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%E6%8B%9B%E6%A0%87%E6%96%87%E4%BB%B6.pdf"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">招标文件.pdf</font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>5、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%E6%8B%9B%E6%A0%87%E6%96%87%E4%BB%B6.pdf"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">招标文件.pdf</font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>6、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/J070/b3298c73-bca4-4292-95f8-e7a6221fd69d/%E6%8B%9B%E6%A0%87%E6%96%87%E4%BB%B6.pdf"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">招标文件.pdf</font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>7、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/ZBTuZhi/b3298c73-bca4-4292-95f8-e7a6221fd69d/ZJWJ/%E6%96%BD%E5%B7%A5%E5%9B%BE.rar"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">施工图.rar</font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>8、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/ZBTuZhi/b3298c73-bca4-4292-95f8-e7a6221fd69d/ZJWJ/%E6%96%BD%E5%B7%A5%E5%9B%BE.rar"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">施工图.rar</font>
                                                        </a></td>
                                                </tr>
                                                <tr>
                                                    <td>9、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202105/ZBTuZhi/b3298c73-bca4-4292-95f8-e7a6221fd69d/ZJWJ/%E6%96%BD%E5%B7%A5%E5%9B%BE.rar"
                                                            target="_blank">
                                                            <font class="infodetailattachfile">施工图.rar</font>
                                                        </a></td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td height="4" />
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td height="1">
                                <hr size="1" color="#dedede" />
                            </td>
                        </tr>
                        <tr>
                            <td height="30" align="center">
                                <table width="200" border="0" cellspacing="0" cellpadding="0" align="center">
                                    <tr>
                                        <td width="25" align="center"><img
                                                src="http://file.zhaotx.cn/view?systemUrl=webfile/20210512/jpg/420E083D9A104DAFB38626F3E6DE8269.jpg"
                                                width="17" height="16" /></td>
                                        <td />
                                        <td width="25" align="center"><img
                                                src="http://file.zhaotx.cn/view?systemUrl=webfile/20210512/jpg/263C905F07824390B2494567C5FA95F3.jpg"
                                                width="16" height="16" /></td>
                                        <td />
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td height="20" />
                        </tr>
                        <tr>
                            <td> </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </td>
</tr>
    """

    ke = KeywordsExtract(content, [
        # "项目名称",  # project_name
        # "招标项目",
        # "工程名称",
        # "招标工程项目",

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

        "招标代理",  # bidding_agency
        "采购代理机构信息[ψ \s]*?名[\s]+称",

        # "项目编号",  # project_number
        # "招标项目编号",
        # "招标编号",
        # "编号",
        # "标段编号",

        "项目金额",  # budget_amount
        "预算金额（元）",

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
        # ], field_name='bidding_agency')
    ], field_name='budget_amount', area_id="3320")
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

    # def get_accurate_pub_time(pub_time):
    #     if not pub_time:
    #         return ""
    #     if pub_time_str := re.search(r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group(0)
    #     elif pub_time_str := re.search(r"\d{4}-\d{1,2}-\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group(0)
    #     elif pub_time_str := re.search(r"\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group(0).replace(".", "-")
    #     elif pub_time_str := re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group(0).replace(".", "-")
    #     elif pub_time_str := re.search(r"\d{4}/\d{1,2}/\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group(0).replace("/", "-")
    #     elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日\d{1,2}:\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group().replace("年", "-").replace("月", "-").replace("日", " ")
    #     elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{1,2}", pub_time):
    #         pub_time_a = pub_time_str.group().replace("年", "-").replace("月", "-").replace("日", " ")
    #     elif pub_time_str := re.search(r"\d{4}年\d{1,2}月\d{1,2}日", pub_time):
    #         pub_time_a = pub_time_str.group(0).replace("年", "-").replace("月", "-").replace("日", "")
    #     else:
    #         pub_time_a = ""
    #     return pub_time_a

    # print(get_accurate_pub_time('2021年05月10日      09:00'))
