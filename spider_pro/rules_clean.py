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
                # 中纬工程管理咨询有限公司受苍南县教育局委托
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                        r'项目业主为([\s \u4e00-\u9fa5]*?)（下称招标人）',
                        r'受([\s \u4e00-\u9fa5]*?)委托',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理：([\s \u4e00-\u9fa5]*?)地',
                        r'委托([^，,。]*?)[进行 , ，]',
                        r'公告([\s \u4e00-\u9fa5]*?)受',
                    ]
                if self.field_name == 'project_number':  # 项目代码：2020-330327-48-01-167360）批准建  目（编号：A3303270480001353001001）招标文件（以
                    regular_list = [
                        r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':  # 本工程预算金额约为479万元。
                    regular_list = [
                        r'预算金额.*?为(\d+)万元'
                    ]
                if self.field_name == 'contact_information':
                    regular_list = [
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)传',
                        r'电话[: ：]\s*?([0-9]+?)\s*?[\u4e00-\u9fa5]',
                        # r'联系电话：0577-68885883，135661051925',
                        r'联系电话：([0-9 \-]+?)[\s , ，]',
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联.*系.*人[: ：]\s*([\u4e00-\u9fa5]+?)电',
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
                <tbody>
                    <tr>
                        <td style="padding:10px;">
                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tbody>
                                    <tr>
                                        <td height="120">
                                            <table width="100%" height="120" border="0" cellpadding="0" cellspacing="0">
                                                <tbody>
                                                    <tr>
                                                        <td height="30"></td>
                                                    </tr>
                                                    <tr>
                                                        <td id="tdTitle" align="center" runat="server" valign="middle">
                                                            <div
                                                                style="line-height 30px; background url(/TPFrontNew/template/deflaut/images/child_rightbg.gif) repeat-x top">
                                                                <font color="" style="font-size: 25px"><b>
                                                                        [意见征询]关于2021年苍南县教育局新型教学空间采购项目文件公开征询意见的公告</b>
                                                                </font>
                                                            </div>
                                                            <div style="height: 30px; line-height: 30px;"> </div>
                                                            <div style="height: 20px; line-height: 20px;">
                                                                <font color="#000000" class="webfont"> 发布时间：
                                                                    2021/6/1
                                                                    &nbsp;&nbsp;访问次数：
                                                                    <script
                                                                        src="/TPFrontNew//Upclicktimes.aspx?InfoID=f3742dea-d8af-43f9-a5ce-c63b7ce6c30c">
                                                                    </script>146
                                                                    &nbsp;&nbsp;

                                                                </font><span>
                                                                    <!--  <label style="margin-left: 4px;">&nbsp;&nbsp;字体: </label>
                            【<span onClick="document.getElementById('TDContent').className='infodetailbig'" style="cursor: hand">大</span> <span onClick="document.getElementById('TDContent').className='infodetailmiddle'"
                                                                                                                                                                                            style="cursor: hand">中</span> <span onClick="document.getElementById('TDContent').className='infodetailsmall'"
                                                                                                                                                                                                                                style="cursor: hand">小</span>】 </span> </div>-->
                                                                    <div style="height:50px;"></div>
                                                                </span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td height="500" align="left" valign="top">
                                            <table height="100%" width="100%" cellpadding="0" cellspacing="0" border="0">
                                                <tbody>
                                                    <tr>
                                                        <td valign="top" class="infodetail" id="TDContent" align="left">
                                                            <div style=" padding-left:40px; padding-right:40px;">
                                                                <p style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: center; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric"
                                                                    align="center"><b><span
                                                                            style="FONT-SIZE: 18pt; FONT-FAMILY: 微软雅黑; COLOR: rgb(74,74,74); LINE-HEIGHT: 150%">
                                                                            <font face="微软雅黑">关于</font>
                                                                        </span></b><b><span
                                                                            style="FONT-SIZE: 18pt; FONT-FAMILY: 微软雅黑; COLOR: rgb(74,74,74); LINE-HEIGHT: 150%">
                                                                            <font face="微软雅黑">2021年苍南县教育局新型教学空间采购项目</font>
                                                                        </span></b><b><span
                                                                            style="FONT-SIZE: 18pt; FONT-FAMILY: 微软雅黑; COLOR: rgb(74,74,74); LINE-HEIGHT: 150%">
                                                                            <font face="微软雅黑">文件公开征询意见的公告</font>
                                                                        </span></b></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 21pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">中纬工程管理咨询有限公司</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">受</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">苍南县教育局</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">委托，就</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">2021年苍南县教育局新型教学空间采购项目</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">
                                                                            进行招标，为避免采购人的采购需求不合法或带有倾向性，现将招标文件征求意见稿（详见</font>
                                                                        <font face="宋体">“附件下载”）公布如下,以公开征求意见。</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">一</font>
                                                                        <font face="宋体">.征求意见范围：</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">1、是否出现明显的倾向性意见和特定的功能指标； </font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">2、影响政府采购“公开、公平、公正”原则的其他情况。</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">二</font>
                                                                        <font face="宋体">.征求意见回复：</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">1、意见递交时间：202</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">1</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">-</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">6</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">-</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">4</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">&nbsp;下午17:00前</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">2、意见递交方式：现场递交、邮寄&nbsp;</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">3、意见接收机构：</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">中纬工程管理咨询有限公司</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">4、联系人：</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">杨</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">先生</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">5、联系电话：0577-68885883，13566105192
                                                                        </font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">5、联系邮箱：</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">475531348</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">@qq.com</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">四</font>
                                                                        <font face="宋体">.合格的修改意见和建议书要求</font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">
                                                                            1、供应商提出修改意见和建议的，书面材料须加盖单位公章和经法人代表签字确认，是授权代理人签字的，必须出具针对该项目的法人代表授权书及联系电话。
                                                                        </font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">
                                                                            2、专家提出修改意见和建议的，须出具本人与该项目相关专业证书复印件及联系电话。 </font>
                                                                    </span></p>
                                                                <p
                                                                    style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: left; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 24pt">
                                                                    <span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">
                                                                            3、各供应商及专家提出修改意见和建议内容必须是真实的，并附相关依据，如发现存在提供虚假材料或恶意扰乱政府采购正常秩序的，一经查实将提请有关政府采购管理机构，列入不良行为记录。
                                                                        </font>
                                                                    </span></p>
                                                                <p style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: justify; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric; TEXT-INDENT: 21pt"
                                                                    align="justify"><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">五</font>
                                                                        <font face="宋体">.&nbsp;注意事项：</font>
                                                                    </span></p>
                                                                <p style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: justify; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric"
                                                                    align="justify"><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">&nbsp;&nbsp;&nbsp;
                                                                            各供应商及专家提出修改意见和建议的，请于202</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">1</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">年</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">6</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">月</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">4</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">日下午</font>
                                                                        <font face="宋体">17时前送达</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">中纬工程管理咨询有限公司</font>
                                                                    </span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">
                                                                            (温州市苍南县灵溪镇中驰御景园7-9-11幢101)。同时将有关意见建议的电子文档发送至以下信箱：
                                                                        </font>
                                                                    </span><span><a href="mailto:734397477@qq.com"><span
                                                                                style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                                <font face="宋体">475531348</font>
                                                                            </span><span
                                                                                style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                                <font face="宋体">@qq.com</font>
                                                                            </span></a></span><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 宋体; TEXT-TRANSFORM: none; COLOR: rgb(74,74,74); LETTER-SPACING: 0pt; LINE-HEIGHT: 150%">
                                                                        <font face="宋体">。对逾期送达的意见、建议书恕不接受。</font>
                                                                    </span></p>
                                                                <p style="FONT-SIZE: 12pt; FONT-FAMILY: Calibri; PADDING-BOTTOM: 0pt; TEXT-ALIGN: justify; PADDING-TOP: 0pt; PADDING-LEFT: 0pt; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 150%; PADDING-RIGHT: 0pt; TEXT-AUTOSPACE: ideograph-numeric"
                                                                    align="justify"><span
                                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: Calibri; COLOR: rgb(74,74,74); LINE-HEIGHT: 150%">&nbsp;</span>
                                                                </p>
                                                                <p
                                                                    style="FONT-SIZE: 10.5pt; FONT-FAMILY: Calibri; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0pt; LINE-HEIGHT: 150%; TEXT-AUTOSPACE: ideograph-numeric">
                                                                    &nbsp;</p>
                                                            </div>
                                                            <div> </div>
                                                        </td>
                                                    </tr>
                                                    <tr style="display:none;">
                                                        <td align="right">
                                                            <br>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td></td>
                                                    </tr>
                                                    <tr>
                                                        <td height="10"></td>
                                                    </tr>
                                                    <tr>
                                                        <td valign="bottom"><span class="infodetailattach">附件：</span>
                                                            <table id="filedown" cellspacing="1" cellpadding="1"
                                                                width="100%" border="0" runat="server">
                                                                <tbody>
                                                                    <tr>
                                                                        <td>1、<a href="http://122.228.139.57///TPFrontNew///AttachStorage/202106/J181/f3742dea-d8af-43f9-a5ce-c63b7ce6c30c/意见征询—2021年苍南县教育局新型教学空间采购项目（1）.doc"
                                                                                target="_blank">
                                                                                <font class="infodetailattachfile">
                                                                                    意见征询—2021年苍南县教育局新型教学空间采购项目（1）.doc</font>
                                                                            </a></td>
                                                                    </tr>
                                                                </tbody>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td height="4"></td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td height="1">
                                            <hr size="1" color="#dedede">
                                        </td>
                                    </tr>
                                    <tr>
                                        <td height="30" align="center">
                                            <table width="200" border="0" cellspacing="0" cellpadding="0" align="center">
                                                <tbody>
                                                    <tr>
                                                        <td width="25" align="center"><img
                                                                src="/TPFrontNew/Template/Default/images/printpic.jpg"
                                                                width="17" height="16"></td>
                                                        <td><a href="javascript:void(0)" onclick="window.print();">【打印】</a>
                                                        </td>
                                                        <td width="25" align="center"><img
                                                                src="/TPFrontNew/Template/Default/images/closepic.jpg"
                                                                width="16" height="16"></td>
                                                        <td><a href="javascript:window.close()">【关闭】</a></td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td height="20"></td>
                                    </tr>
                                    <tr>
                                        <td> </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </tbody>
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
        # "招&nbsp;标&nbsp;人",
        # "招标单位",
        # "采购人信息[ψ \s]*?名[\s]+称",
        # "招标代理机构",

        "招标代理",  # bidding_agency
        "采购代理机构信息[ψ \s]*?名[\s]+称",

        # "项目编号",  # project_number
        # "招标项目编号",
        # "招标编号",
        # "编号",
        # "标段编号",

        # "项目金额",  # budget_amount
        # "预算金额（元）",

        # "中标价格",  # bid_amount
        # "中标价",
        # "中标（成交）金额(元)",

        # "招标方式",
        
        # "开标时间",  # tenderee
        # "开启时间",
    # ], field_name='bidding_agency')
    ], field_name='bidding_agency', area_id="3320")
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