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
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 1.5em; TEXT-INDENT:
                                                        0px; font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><strong
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; TEXT-ALIGN: justify">一、项目编号：</strong><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: 黑体, SimHei"> <span
                                                                class="bookmark-item uuid-1596280499822 code-00004 addWord single-line-text-input-box-cls">CNDL2021185</span> </span> 
                                                                       </p>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 1.5em; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span style="FONT-SIZE: 18px"><strong>二、项目名称：</strong> <span
                                                                class="bookmark-item uuid-1591615489941 code-00003 addWord single-line-text-input-box-cls">苍南县沿浦湾海岸线整治修复工程涉海前期专题服务采购项目</span> </span><span> </span> 
                                                                         </p>
                                                    <p style="FONT-SIZE: medium; MARGIN-BOTTOM: 10px; FONT-FAMILY: "
                                                        Microsoft YaHei"; WHITE-SPACE: normal; WORD-SPACING: 0px;
                                                        MARGIN-TOP: 10px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR:
                                                        rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2; WIDOWS: 2;
                                                        LETTER-SPACING: normal; LINE-HEIGHT: 1.5em; TEXT-INDENT: 0px;
                                                        font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word">
                                                        <strong><span
                                                                style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif">三、中标（成交）信息</span></strong><span> </span> 
                                                                         </p>
                                                    <div
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2; WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 20px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial">
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word"><span
                                                                style="FONT-SIZE: 18px">   1.中标结果：</span>  </p>
                                                        <table
                                                            class="template-bookmark uuid-1599570948000 code-AM014zbcj001 text-中标/成交结果信息"
                                                            style="WIDTH: 718px; BORDER-COLLAPSE: collapse">
                                                            <thead>
                                                                <tr class="firstRow">
                                                                    <th
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; BACKGROUND-COLOR: rgb(255,255,255); break-inside: avoid">
                                                                        序号</th>
                                                                    <th
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; BACKGROUND-COLOR: rgb(255,255,255); break-inside: avoid">
                                                                        中标（成交）金额(元)</th>
                                                                    <th
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; BACKGROUND-COLOR: rgb(255,255,255); break-inside: avoid">
                                                                        中标供应商名称</th>
                                                                    <th
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; BACKGROUND-COLOR: rgb(255,255,255); break-inside: avoid">
                                                                        中标供应商地址</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                <tr style="TEXT-ALIGN: center" width="100%">
                                                                    <td class="code-sectionNo"
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid">
                                                                        1</td>
                                                                    <td class="code-summaryPrice"
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid">
                                                                        最终报价:1248000(元)</td>
                                                                    <td class="code-winningSupplierName"
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid">
                                                                        杭州希澳环境科技有限公司</td>
                                                                    <td class="code-winningSupplierAddr"
                                                                        style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid">
                                                                        中联大厦2幢1204室</td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <p
                                                            style="MARGIN-TOP: 5px; LINE-HEIGHT: normal; overflow-wrap: break-word">
                                                               2.废标结果:  </p>
                                                        <p class="sub"
                                                            style="MARGIN-BOTTOM: 5px; LINE-HEIGHT: normal; overflow-wrap: break-word">
                                                               </p>
                                                        <table class="form-panel-input-cls" width="100%">
                                                            <tbody>
                                                                <tr class="firstRow" style="TEXT-ALIGN: center"
                                                                    width="100%">
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">序号</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">标项名称</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">废标理由</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">其他事项</td>
                                                                </tr>
                                                                <tr style="TEXT-ALIGN: center" width="100%">
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">/</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">/</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">/</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="25%">/</td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                         
                                                        <p style="overflow-wrap: break-word" />
                                                    </div>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span
                                                            style="FONT-SIZE: 18px"><strong>四、主要标的信息</strong></span><span> </span> 
                                                                         </p>
                                                    <div
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2; WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 20px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial">
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word"><span
                                                                style="FONT-SIZE: 18px"> 
                                                                 1.货物类主要标的信息：</span><span> </span>   </p>
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word">     </p>
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word"> 
                                                             2.工程类主要标的信息：</p>
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word">      </p>
                                                        <p style="LINE-HEIGHT: normal; overflow-wrap: break-word"> 
                                                             3.服务类主要标的信息：</p>
                                                        <p class="sub"
                                                            style="LINE-HEIGHT: normal; overflow-wrap: break-word">    </p>
                                                        <table class="form-panel-input-cls" width="100%">
                                                            <tbody>
                                                                <tr class="firstRow" style="TEXT-ALIGN: center"
                                                                    width="100%">
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">序号</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">标项名称</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">标的名称</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">服务范围</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">服务要求</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">服务时间</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">服务标准</td>
                                                                </tr>
                                                                <tr style="TEXT-ALIGN: center" width="100%">
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">1</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">苍南县沿浦湾海岸线整治修复工程涉海前期专题服务</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">苍南县沿浦湾海岸线整治修复工程涉海前期专题服务</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">
                                                                        内容包含：海洋水文动力环境现状调查、岸滩稳定性分析及数值模型预测专题报告编制、海洋环境影响评价报告编制、海域使用论证报告编制。
                                                                    </td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">按采购文件要求</td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">中标人需在合同签订后3个月内完成所有工作，并提交相关部门审查通过。
                                                                    </td>
                                                                    <td style="BORDER-TOP: rgb(221,221,221) 1px solid; BORDER-RIGHT: rgb(221,221,221) 1px solid; BORDER-BOTTOM: rgb(221,221,221) 1px solid; WORD-BREAK: break-all; PADDING-BOTTOM: 5px; PADDING-TOP: 5px; PADDING-LEFT: 10px; BORDER-LEFT: rgb(221,221,221) 1px solid; PADDING-RIGHT: 10px; break-inside: avoid"
                                                                        width="14.29%">按采购文件要求</td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                         
                                                        <p style="overflow-wrap: break-word" />
                                                    </div>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span
                                                            style="FONT-SIZE: 18px"><strong>五、评审专家（单一来源采购人员）名单：</strong></span><span> </span> 
                                                                         </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; TEXT-INDENT: 0px;
                                                        font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                              <span
                                                                class="bookmark-item uuid-1589193390811 code-85005 addWord multi-line-text-input-box-cls">饶大举,李丕阜,郑世东</span> </span><span> </span> 
                                                                         </p>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span
                                                            style="FONT-SIZE: 18px"><strong>六、代理服务收费标准及金额：</strong></span> 
                                                                       </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; TEXT-INDENT: 0px;
                                                        font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                             1.代理服务收费标准：<span
                                                                class="bookmark-item uuid-1591615554332 code-AM01400039 addWord multi-line-text-input-box-cls">按标准</span> </span><span> </span> 
                                                                         </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; TEXT-INDENT: 0px;
                                                        font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                             2.代理服务收费金额（元）：<span
                                                                class="bookmark-item uuid-1591615558580 code-AM01400040 addWord numeric-input-box-cls readonly">19000</span> </span> 
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span
                                                            style="FONT-SIZE: 18px"><strong>七、公告期限</strong></span><span> </span> 
                                                                         </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; TEXT-INDENT: 0px;
                                                        font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                             自本公告发布之日起1个工作日。</span><span> </span>                   </p>
                                                    <p
                                                        style="FONT-SIZE: medium; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span style="FONT-SIZE: 18px"><strong>八、其他补充事宜</strong></span>     
                                                                     </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 1.5em; TEXT-INDENT:
                                                        0px; font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                             
                                                            1.各参加政府采购活动的供应商认为该中标/成交结果和采购过程等使自己的权益受到损害的，可以自本公告期限届满之日（本公告发布之日后第2个工作日）起7个工作日内，以书面形式向采购人或受其委托的采购代理机构提出质疑。质疑供应商对采购人、采购代理机构的答复不满意或者采购人、采购代理机构未在规定的时间内作出答复的，可以在答复期满后十五个工作日内向同级政府采购监督管理部门投诉。质疑函范本、投诉书范本请到浙江政府采购网下载专区下载。</span> 
                                                                  </p>
                                                    <p style="FONT-SIZE: medium; FONT-FAMILY: " Microsoft YaHei";
                                                        WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none;
                                                        FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2;
                                                        WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 1.5em; TEXT-INDENT:
                                                        0px; font-variant-ligatures: normal; font-variant-caps: normal;
                                                        -webkit-text-stroke-width: 0px; text-decoration-style: initial;
                                                        text-decoration-color: initial; overflow-wrap: break-word"><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong; LINE-HEIGHT: 20px"> 
                                                              2.其他事项：  </span><span> </span>                   </p>
                                                    <p
                                                        style="FONT-SIZE: 18px; FONT-FAMILY: SimHei, sans-serif; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; TEXT-ALIGN: justify; ORPHANS: 2; WIDOWS: 2; MARGIN: 10px 0px; LETTER-SPACING: normal; LINE-HEIGHT: 32px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial; overflow-wrap: break-word; break-after: avoid">
                                                        <span
                                                            style="FONT-SIZE: 18px"><strong>九、对本次公告内容提出询问、质疑、投诉，请按以下方式联系</strong><span
                                                                style="FONT-SIZE: 16px; FONT-FAMILY: sans-serif">　　　</span></span><span
                                                            style="FONT-SIZE: 18px; FONT-FAMILY: FangSong"> 
                                                             </span><span> </span>       </p>
                                                    <div
                                                        style="FONT-SIZE: medium; FONT-FAMILY: FangSong; WHITE-SPACE: normal; WORD-SPACING: 0px; TEXT-TRANSFORM: none; FONT-WEIGHT: 400; COLOR: rgb(0,0,0); FONT-STYLE: normal; ORPHANS: 2; WIDOWS: 2; LETTER-SPACING: normal; LINE-HEIGHT: 30px; TEXT-INDENT: 0px; font-variant-ligatures: normal; font-variant-caps: normal; -webkit-text-stroke-width: 0px; text-decoration-style: initial; text-decoration-color: initial">
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  1.采购人信息</span>           </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  名    称：<span
                                                                    class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly">苍南县自然资源和规划局</span>  </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  地    址：<span
                                                                    class="bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls">苍南县灵溪镇工人文化宫南侧</span> </span> 
                                                                   </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  传    真：<span
                                                                    class="bookmark-item uuid-1596004680354 code-00017 addWord single-line-text-input-box-cls">0577-59909673</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  项目联系人（询问）：<span
                                                                    class="bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly">徐女士</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  项目联系方式（询问）：<span
                                                                    class="bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly">(0577)
                                                                    599-09673</span>  </span>         </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  质疑联系人：<span
                                                                    class="bookmark-item uuid-1596004703774 code-AM014cg001 addWord single-line-text-input-box-cls">徐玉宣</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  质疑联系方式：<span
                                                                    class="bookmark-item uuid-1596004712085 code-AM014cg002 addWord single-line-text-input-box-cls">15869466005</span> </span> 
                                                                       </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                 <br />
                                                                    2.采购代理机构信息</span><span> </span>           </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  名    称：<span
                                                                    class="bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls">温州超然招标代理有限公司</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  地    址：<span
                                                                    class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly">苍南县灵溪镇上江小区1-7幢1单元202室</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  传    真：<span
                                                                    class="bookmark-item uuid-1596004736097 code-00012 addWord single-line-text-input-box-cls">0577-68803069</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  项目联系人（询问）：<span
                                                                    class="bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly">陈仕盈（13587830757）</span>  </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  项目联系方式（询问）：<span
                                                                    class="bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls">0577-68803069</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  质疑联系人：<span
                                                                    class="bookmark-item uuid-1596004761573 code-AM014cg003 addWord single-line-text-input-box-cls">陈奇</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  质疑联系方式：<span
                                                                    class="bookmark-item uuid-1596004769998 code-AM014cg004 addWord single-line-text-input-box-cls">15727866665</span> 　　　　　　　　　　</span> 
                                                             <span style="FONT-SIZE: 18px">   </span></p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                 <br />
                                                                    3.同级政府采购监督管理部门</span><span> </span>           </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  名    称：<span
                                                                    class="bookmark-item uuid-1596004778916 code-00019 addWord single-line-text-input-box-cls">苍南县政府采购监督管理办公室</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  地    址：<span
                                                                    class="bookmark-item uuid-1596004787211 code-00023 addWord single-line-text-input-box-cls">苍南县灵溪镇春晖路555号</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  传    真：<span
                                                                    class="bookmark-item uuid-1596004796586 code-00022 addWord single-line-text-input-box-cls">0577-59867927</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  联系人 ：<span
                                                                    class="bookmark-item uuid-1596004804824 code-00020 addWord single-line-text-input-box-cls">陈先生</span> </span><span> </span> 
                                                                     </p>
                                                        <p style="overflow-wrap: break-word"><span style="FONT-SIZE: 18px"> 
                                                                  监督投诉电话：<span
                                                                    class="bookmark-item uuid-1596004812886 code-00021 addWord single-line-text-input-box-cls">0577-59867927</span></span>
                                                        </p>
                                                    </div>
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
                                            <td valign="bottom"> </td>
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
                                                    src="http://file.zhaotx.cn/view?systemUrl=webfile/20210513/jpg/E918082ECECF4898AE2D5C650DAEF128.jpg"
                                                    width="17" height="16" /></td>
                                            <td />
                                            <td width="25" align="center"><img
                                                    src="http://file.zhaotx.cn/view?systemUrl=webfile/20210513/jpg/8FA73C75D0D1443ABD19014BE717165A.jpg"
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

        "招标人",  # tenderee
        "招 标 人",
        "招&nbsp;标&nbsp;人",
        "招\s*?标\s*?人：",
        "招标单位",
        "采购人信息[ψ \s]*?名[\s]+称",
        "建设（招标）单位",
        "建设单位",

        # "招标代理",  # bidding_agency
        # "采购代理机构信息[ψ \s]*?名[\s]+称",

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
        
        # "中标人",  # successful_bidder
        # "中标人名称",
        # "中标单位",
        # "供应商名称",
    # ], field_name='bidding_agency')
    ], field_name='tenderee', area_id="3320")
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