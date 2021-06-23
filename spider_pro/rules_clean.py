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
        self.keysss = ["招标项目", "中标（成交）金额(元)", "代理机构", "中标供应商名称", "工程名称", "项目名称", "成交价格", "招标工程项目", "项目编号", "招标项目编号",
                       "招标编号",
                       "招标人", "招 标 人", "发布时间", "招标单位", "招标代理:", "招标代理：", "招标代理机构",
                       "项目金额", "预算金额（元）", "招标估算价", "中标（成交）金额（元）", "联系人", "联 系 人",
                       "项目经理（负责人）"]
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
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                        r'项目业主为([\s \u4e00-\u9fa5]*?)（下称招标人）',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理：([\s \u4e00-\u9fa5]*?)地',
                        r'委托([^，,。]*?)[进行 , ，]',
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
                        r'电\s*话[: ：]([^\u4e00-\u9fa5]+?)传'
                    ]
                if self.field_name == 'liaison':
                    regular_list = [
                        r'联.*系.*人[: ：]\s*([\u4e00-\u9fa5]+?)电'
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
    <div class="Content-Main FloatL">
        <span class="Bold" id="title">浙江策鼎工程项目管理有限公司关于2021年瑞安市桥梁常规检测、护栏升级改造检测及道路塌陷、脱空隐患排查评估(重1)的竞争性磋商公告</span>
        <div class="Content-news">
            <em>&nbsp; 发布时间：2021-04-26 &nbsp;</em>
            <div class="share">
                <div id="share-2" class="share-component social-share">
                    <div class="pic"></div>
                    <a class="social-share-icon icon-weibo" target="_blank" onclick="shareTo('sina')"></a>
                    <a class="social-share-icon icon-wechat" tabindex="-1" onclick="shareTo('wechat')"></a>
                    <a class="social-share-icon icon-qzone" onclick="shareTo('qzone')">
                    </a>
                </div>
            </div><br><br><br>
            <p>温馨提示:本网站以下公告内容来源于浙江政府采购网，具体内容以浙江政府采购网为准，浙江政府采购网网址：https://zfcg.czt.zj.gov.cn/。</p>
        </div>
        <div class="Main-p" id="imgPic">
            <style id="fixTableStyle" type="text/css">
                th,
                td {
                    border: 1px solid #DDD;
                    padding: 5px 10px;
                }
            </style>
            <div id="fixTableStyle" type="text/css" cdata_tag="style"
                cdata_data="th,td {border:1px solid #DDD;padding: 5px 10px;}" _ue_custom_node_="true"></div>
            <div>
                <div>
                    <div>
                        <div>
                            <div>
                                <div>
                                    <div>
                                        <div style="border:2px solid">
                                            <div style="font-family:FangSong;">
                                                <p style="margin-bottom: 10px;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                        项目概况</span> &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
                                                    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
                                                    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
                                                <p><span style="font-size: 18px; line-height:30px; ">&nbsp; &nbsp; <span
                                                            class="bookmark-item uuid-1595987346914 code-00003 addWord single-line-text-input-box-cls">2021年瑞安市桥梁常规检测、护栏升级改造检测及道路塌陷、脱空隐患排查评估(重1)</span></span><span
                                                        style="font-size: 18px;">采购项目的潜在供应商应在<span
                                                            class="bookmark-item uuid-1595987856888 code-25007 editDisable single-line-text-input-box-cls readonly">登录浙江政府采购网（http：//zfcg.czt.zj.gov.cn）申请获取采购文件。</span></span><span
                                                        style="font-size: 18px;">获取（下载）采购文件，并于<span
                                                            class="bookmark-item uuid-1595988328924 code-25011 addWord date-time-selection-cls">2021年05月10日
                                                            09:00</span></span><span
                                                        style="font-size: 18px;">（北京时间）前提交（上传）响应文件。</span>&nbsp; &nbsp;
                                                    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
                                                    &nbsp; &nbsp;&nbsp;</p>
                                            </div>
                                        </div>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>一、项目基本情况</strong></span></p>
                                    <div style="font-family:FangSong;line-height:20px;">
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 项目编号：<span
                                                    class="bookmark-item uuid-1595987359344 code-00004 addWord single-line-text-input-box-cls">ZJCDRACG-20210402</span>&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 项目名称：<span
                                                    class="bookmark-item uuid-1595987369689 code-00003 addWord single-line-text-input-box-cls">2021年瑞安市桥梁常规检测、护栏升级改造检测及道路塌陷、脱空隐患排查评估(重1)</span>&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 采购方式：竞争性磋商</span>&nbsp;</p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 预算金额（元）：<span
                                                    class="bookmark-item uuid-1595987387629 code-AM01400034 addWord numeric-input-box-cls">1289100</span>&nbsp;&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 最高限价（元）：<span
                                                    class="bookmark-item uuid-1589437289226 code-AM014priceCeiling addWord single-line-text-input-box-cls">1289100</span>&nbsp;</span>&nbsp;
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 采购需求：<br></span></p>
                                        <div>
                                            <div style="padding: 10px"
                                                class="template-bookmark uuid-1596252080953 code-AM014jzx08 text-竞争性磋商公告-对象面板-新 object-panel-cls">
                                                &nbsp; <span style="font-size: 18px;">&nbsp;<span
                                                        class="bookmark-item uuid-1596252109084 code-AM014sectionNo editDisable "></span>&nbsp;<br>&nbsp;
                                                    &nbsp;数量：<span
                                                        class="bookmark-item uuid-1596252133269 code-AM014bidItemCount editDisable single-line-text-input-box-cls">1</span>&nbsp;</span>
                                                <p><span style="font-size: 18px;">&nbsp; &nbsp;预算金额（元）：<span
                                                            class="bookmark-item uuid-1596252138981 code-AM014budgetPrice editDisable single-line-text-input-box-cls">1289100</span>&nbsp;</span>
                                                </p>
                                                <p><span style="font-size: 18px;">&nbsp; &nbsp;单位：<span
                                                            class="bookmark-item uuid-1596252143569 code-AM014bidItemUnit editDisable single-line-text-input-box-cls">项</span>&nbsp;</span>
                                                </p>
                                                <p><span style="font-size: 18px;">&nbsp; &nbsp;简要规格描述：<span
                                                            class="bookmark-item uuid-1596252148371 code-AM014briefSpecificationDesc editDisable single-line-text-input-box-cls">2021年瑞安市桥梁常规检测、护栏升级改造检测及道路塌陷、脱空隐患排查评估(重1)（详见磋商文件第三部分）。</span>&nbsp;</span>
                                                </p>
                                                <p><span style="font-size: 18px;">&nbsp; &nbsp;备注：<span
                                                            class="bookmark-item uuid-1596252152299 code-AM014remarks editDisable single-line-text-input-box-cls">1289100元（其中：桥梁常规检测、护栏升级改造检测最高限价为789100元；
                                                            桥梁结构检测最高限价为200000元；道路塌陷、脱空隐患排查评估最高限价为300000元。）
                                                        </span>&nbsp;</span></p>
                                            </div>
                                        </div>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 合同履约期限：<span
                                                    class="bookmark-item uuid-1589437299696 code-AM014ContractPerformancePeriod addWord single-line-text-input-box-cls">标项
                                                    1，合同签订之日起60日内完成（包括出具检测报告并通过专家评审，录入检测数据、资料及出具道路塌陷、脱空隐患排查评估报告）。</span>&nbsp;</span>&nbsp;<br>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 本项目（<span
                                                    class="bookmark-item uuid-1589181188930 code-AM014cg005 addWord single-line-text-input-box-cls">否</span>）接受联合体投标。</span>&nbsp;&nbsp;
                                        </p>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>二、申请人的资格要求：</strong></span></p>
                                    <div style="font-family:FangSong;line-height:20px;">
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 1.满足《中华人民共和国政府采购法》第二十二条规定；<span
                                                    style="font-family: FangSong; font-size: 18px;">未被“信用中国”（www.creditchina.gov.cn)、中国政府采购网（www.ccgp.gov.cn）列入失信被执行人、重大税收违法案件当事人名单、政府采购严重违法失信行为记录名单。</span></span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 2.落实政府采购政策需满足的资格要求：<span
                                                    class="bookmark-item uuid-1595987425520 code-23021 editDisable multi-line-text-input-box-cls readonly">无</span>&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 3.本项目的特定资格要求：<span
                                                    class="bookmark-item uuid-1596276761070 code-22002 editDisable multi-line-text-input-box-cls readonly">标项1:（1）具备省级及以上建设行政主管部门颁发的建设工程质量检测机构资质证书（检测范围须包含市政桥梁检测和市政（道路）工程材料见证取样检测（或见证取样检测（通用））；
                                                    （2）具备省级及以上计量主管部门颁发的含有桥梁、道路（或路基路面）检测项目的CMA计量认证证书； </span>&nbsp;</span>
                                        </p>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>三、获取（下载）采购文件</strong></span></p>
                                    <div style="font-family:FangSong;line-height:20px;">
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; </span><span
                                                style="font-size: 18px; text-decoration: none;">时间：<span
                                                    class="bookmark-item uuid-1595987985571 code-25003 addWord date-selection-cls">/</span>至<span
                                                    class="bookmark-item uuid-1595987959773 code-25004 editDisable date-selection-cls readonly">2021年05月10日</span>，每天上午<span
                                                    class="bookmark-item uuid-1595988019709 code-25005 addWord morning-time-section-selection-cls">00:00至12:00</span>，下午<span
                                                    class="bookmark-item uuid-1595988030421 code-25006 addWord afternoon-time-section-selection-cls">12:00至23:59</span>（北京时间，线上获取法定节假日均可，线下获取文件法定节假日除外）</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 地点（网址）：<span
                                                    class="bookmark-item uuid-1595988073673 code-25007 editDisable single-line-text-input-box-cls readonly">登录浙江政府采购网（http：//zfcg.czt.zj.gov.cn）申请获取采购文件。</span>&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 方式：<span
                                                    class="bookmark-item uuid-1595988080611 code-25008 editDisable single-line-text-input-box-cls readonly">供应商登录浙江政府采购网（http://www.zfcg.czt.zj.gov.cn）申请获取采购文件。</span>&nbsp;</span>
                                        </p>
                                        <p><span style="font-size: 18px;">&nbsp; &nbsp; 售价（元）：<span
                                                    class="bookmark-item uuid-1595988095908 code-25009 addWord numeric-input-box-cls">0</span>&nbsp;</span>
                                        </p>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>四、响应文件提交（上传）</strong></span>&nbsp;</p>
                                    <div style="font-family:FangSong; font-size:18px; line-height:20px;">
                                        <p>&nbsp; &nbsp; 截止时间：<span
                                                class="bookmark-item uuid-1595988122451 code-25011 addWord date-time-selection-cls">2021年05月10日
                                                09:00</span>（北京时间）</p>
                                        <p>&nbsp; &nbsp; 地点（网址）：<span
                                                class="bookmark-item uuid-1595988200124 code-25012 editDisable single-line-text-input-box-cls readonly">磋商供应商应当在磋商截止时间前将电子磋商响应文件上传到“政采云”平台。</span>&nbsp;
                                        </p>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>五、响应文件开启</strong></span>&nbsp;</p>
                                    <div style="font-size:18px; font-family:FangSong; line-height:20px;">
                                        <p>&nbsp; &nbsp; 开启时间：<span
                                                class="bookmark-item uuid-1595988227171 code-25011 addWord date-time-selection-cls">2021年05月10日
                                                09:00</span>&nbsp;（北京时间）</p>
                                        <p>&nbsp; &nbsp; 地点（网址）：<span
                                                class="bookmark-item uuid-1595988252461 code-25015 editDisable single-line-text-input-box-cls readonly">瑞安市公共资源交易中心（瑞安市外滩满庭芳大楼三楼）。</span>&nbsp;
                                        </p>
                                    </div>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;line-height:20px;"><strong>六、公告期限</strong></span></p>
                                    <p><span style="font-size: 18px; font-family:FangSong;">&nbsp; &nbsp;
                                            自本公告发布之日起3个工作日。</span></p>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 30px;break-after: avoid;font-size: 18px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>七、其他补充事宜</strong></span>&nbsp;</p>
                                    <p style="line-height: 1.5em;"><span
                                            style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp; &nbsp;
                                            1.供应商认为采购文件使自己的权益受到损害的，可以自获取采购文件之日或者采购文件公告期限届满之日（公告期限届满后获取采购文件的，以公告期限届满之日为准）起7个工作日内，<span
                                                style="font-family: FangSong; font-size: 18px; background-color: #FFFFFF;">对采购文件需求的以书面形式向采购人提出质疑，对其他内容的以书面形式向采购人和采购代理机构提出质疑。</span>质疑供应商对采购人、采购代理机构的答复不满意或者采购人、采购代理机构未在规定的时间内作出答复的，可以在答复期满后十五个工作日内向同级政府采购监督管理部门投诉。质疑函范本、投诉书范本请到浙江政府采购网下载专区下载。<br>&nbsp;
                                            &nbsp; 2.其他事项：<span
                                                class="bookmark-item uuid-1589194982864 code-31006 addWord multi-line-text-input-box-cls">1、供应商认为采购文件使自己的权益受到损害的，可以自获取采购文件之日或者采购文件公告期限届满之日（公告期限届满后获取采购文件的，以公告期限届满之日为准）起7个工作日内，以书面形式向采购人和采购代理机构提出质疑。供应商应当在法定质疑期内须一次性提出针对同一采购程序环节的质疑，否则采购代理机构有权拒绝第一次质疑以外其他所有质疑。质疑供应商对采购人、采购代理机构的答复不满意或者采购人、采购代理机构未在规定的时间内作出答复的，可以在答复期满后十五个工作日内向同级政府采购监督管理部门投诉。质疑函范本、投诉书范本请到浙江政府采购网下载专区下载。
                                                2、潜在供应商应当按照规定方式获取采购文件，未按照规定方式获取采购文件的，不得对采购文件提起质疑投诉。
                                                3、本项目采取电子招投标，电子招投标有关事项说明如下： (1)
                                                本项目实行电子投标，磋商供应商无须提交纸质磋商响应文件，无须授权代表参加开标会议。应按照本项目磋商文件和政采云平台的要求编制、加密并递交磋商响应文件。供应商在使用系统进行投标的过程中遇到涉及平台使用的任何问题，可致电政采云平台技术支持热线咨询，联系方式：400-881-7190。
                                                (2)
                                                磋商供应商应在开标前完成CA数字证书办理。（办理流程详见http://zfcg.czt.zj.gov.cn/bidClientTemplate/2019-05-27/12945.html）。
                                                完成CA数字证书办理预计一周左右，建议各磋商供应商抓紧时间办理。 (3)
                                                磋商供应商通过政采云平台电子投标工具制作磋商响应文件，电子投标工具请供应商自行前往浙江省政府采购网下载并安装，
                                                （下载网址：http://zfcg.czt.zj.gov.cn/bidClientTemplate/2019-05-27/12946.html），电子投标具体流程详见《供应商-政府采购项目电子交易操作指南》
                                                （网址：https://help.zcygov.cn/web/site_2/2018/12-28/2573.html)（以下简称《操作指南》）。 (4)
                                                考虑到系统兼容性建议磋商供应商在操作电子投标流程时使用windows7 64位或以上操作系统。 (5)
                                                磋商供应商用CA数字证书（制作本项目电子磋商响应文件的同一个CA）在电脑上完成磋商响应文件解密等事宜。解密时长为从磋商截止时间起30分钟。
                                                4、根据《浙江省政府采购供应商注册登记和诚信管理暂行办法》，中标成交的磋商供应商，必须事先申请加入“浙江省政府采购供应商库”；请磋商供应商登入“浙江政府采购网”进行登记注册。
                                                5、 本项目执行促进中小企业发展（监狱企业、残疾人福利性单位视同小型、微型企业）、优先采购节能产品、优先采购环境标志产品政策。
                                            </span>&nbsp;</span><span
                                            style="font-size: 18px;font-family:FangSong;line-height:20px;">&nbsp;</span></p>
                                    <p
                                        style="margin: 17px 0;text-align: justify;line-height: 32px;break-after: avoid;font-size: 21px;font-family: SimHei, sans-serif;white-space: normal">
                                        <span style="font-size: 18px;"><strong>八、凡对本次招标提出询问、质疑、投诉，请按以下方式联系</strong></span>
                                    </p>
                                    <div style="font-family:FangSong;line-height:30px;">
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                1.采购人信息</span></p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                名&nbsp;&nbsp;&nbsp; 称：<span
                                                    class="bookmark-item uuid-1596004663203 code-00014 editDisable interval-text-box-cls readonly">瑞安市市政工程管理中心</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                地&nbsp;&nbsp;&nbsp; 址：<span
                                                    class="bookmark-item uuid-1596004672274 code-00018 addWord single-line-text-input-box-cls">瑞安市滨江大道新湖大厦北侧</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 传&nbsp;
                                                &nbsp; 真：<span
                                                    class="bookmark-item uuid-1596004680354 code-00017  addWord"></span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                项目联系人（询问）：<span
                                                    class="bookmark-item uuid-1596004688403 code-00015 editDisable single-line-text-input-box-cls readonly">木朝晖</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                项目联系方式（询问）：<span
                                                    class="bookmark-item uuid-1596004695990 code-00016 editDisable single-line-text-input-box-cls readonly">13868386122</span>&nbsp;&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                质疑联系人：<span
                                                    class="bookmark-item uuid-1596004703774 code-AM014cg001 addWord single-line-text-input-box-cls">潘建峰</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                质疑联系方式：<span
                                                    class="bookmark-item uuid-1596004712085 code-AM014cg002 addWord single-line-text-input-box-cls">13587525553</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                <br>&nbsp; &nbsp; 2.采购代理机构信息</span></p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                名&nbsp;&nbsp;&nbsp; 称：<span
                                                    class="bookmark-item uuid-1596004721081 code-00009 addWord interval-text-box-cls">浙江策鼎工程项目管理有限公司</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                地&nbsp;&nbsp;&nbsp; 址：<span
                                                    class="bookmark-item uuid-1596004728442 code-00013 editDisable single-line-text-input-box-cls readonly">瑞安市安阳南路669号三楼</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 传&nbsp;
                                                &nbsp; 真：<span
                                                    class="bookmark-item uuid-1596004736097 code-00012  addWord"></span>&nbsp;</span>&nbsp;
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                项目联系人（询问）：<span
                                                    class="bookmark-item uuid-1596004745033 code-00010 editDisable single-line-text-input-box-cls readonly">戴巍巍</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                项目联系方式（询问）：<span
                                                    class="bookmark-item uuid-1596004753055 code-00011 addWord single-line-text-input-box-cls">13625872310</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                质疑联系人：<span
                                                    class="bookmark-item uuid-1596004761573 code-AM014cg003 addWord single-line-text-input-box-cls">胡丽娜</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                质疑联系方式：<span
                                                    class="bookmark-item uuid-1596004769998 code-AM014cg004 addWord single-line-text-input-box-cls">13587528100</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                <br>&nbsp; &nbsp; 3.同级政府采购监督管理部门</span></p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                名&nbsp;&nbsp;&nbsp; 称：<span
                                                    class="bookmark-item uuid-1596004778916 code-00019 addWord single-line-text-input-box-cls">瑞安市财政局政府采购监管科</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                地&nbsp;&nbsp;&nbsp; 址：<span
                                                    class="bookmark-item uuid-1596004787211 code-00023 addWord single-line-text-input-box-cls">瑞安市财税大楼1505室</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 传&nbsp;
                                                &nbsp; 真：<span
                                                    class="bookmark-item uuid-1596004796586 code-00022 addWord single-line-text-input-box-cls">0577-65827570</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp; 联系人
                                                ：<span
                                                    class="bookmark-item uuid-1596004804824 code-00020 addWord single-line-text-input-box-cls">张先生</span>&nbsp;</span>
                                        </p>
                                        <p style="line-height: normal;"><span style="font-size: 18px;">&nbsp; &nbsp;
                                                监督投诉电话：<span
                                                    class="bookmark-item uuid-1596004812886 code-00021 addWord single-line-text-input-box-cls">0577-65827567</span></span>
                                        </p>
                                    </div>
                                </div><br><br>
                                <div style="font-family:FangSong;">
                                    <p>若对项目采购电子交易系统操作有疑问，可登录政采云（https://www.zcygov.cn/），点击右侧咨询小采，获取采小蜜智能服务管家帮助，或拨打政采云服务热线400-881-7190获取热线服务帮助。&nbsp;
                                        &nbsp; &nbsp; &nbsp;&nbsp;</p>
                                    <p>CA问题联系电话（人工）：汇信CA 400-888-4636；天谷CA 400-087-8198。<br>&nbsp;</p>
                                    <blockquote style="display: none;"><span
                                            class="bookmark-item uuid-1596276900507 code-AM014acquirePurFileDetailUrl addWord single-line-text-input-box-cls">
                                            <a class="purInfoPublishEditAcquireDetailUrl"
                                                id="purInfoPublishEditAcquireDetailUrl"
                                                href="https://www.zcygov.cn/bidding-entrust/#/acquirepurfile/launch/5e430c913c7f7e6e"
                                                style="padding: 2px 15px;margin: 0;font-size: 14px;border-radius: 4px;border: 1px solid transparent;font-weight: 400;white-space: nowrap;text-align: center;background-image: none;color: #fff;background-color: #1890ff;border-color: #1890ff;text-decoration:none;display:none"
                                                target="_blank">潜在供应商</a></span></blockquote>&nbsp;<p><br></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <p><br></p>
            <p><br></p>
            <p><br></p>
            <p style="font-size" class="fjxx">附件信息：</p>
            <ul class="fjxx" style="font-size: 16px;margin-left: 38px;color: #0065ef;list-style-type: none;">
                <li>
                    <p style="display:inline-block"><a
                            href="https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1023FP/331102/10006417326/20214/43f29faf-a0d2-42fc-bb86-d72501f51481">2021年瑞安市桥梁常规检测、护栏升级改造检测及道路塌陷、脱空隐患排查评估定稿(重1)..docx</a>
                    </p>
                    <p style="display:inline-block;margin-left:20px">241.5K</p>
                </li>
            </ul>
        </div>

        <div class="pagebar"></div>

        <table>
            <tbody>
                <tr>
                    <th class="Th-Left">相关链接</th>
                </tr>
                <tr>
                    <td>
                        <div class="BottomNone">
                            <span><a href="/wzcms/zfcgcggg/73544.htm" title="杭州华旗招标代理有限公司关于苍南县质量技术监督检测院多参数监护仪检定装置的竞争性谈判公告"
                                    target="_blank">杭州华旗招标代理有限公司关于苍南县质量技术监督检测院多参数...</a></span>
                            <span><a href="/wzcms/zfcgzbgg/73543.htm"
                                    title="中纬工程管理咨询有限公司关于苍南县应急管理局安全技能提升项目制培训采购项目（标项一）（重2）的中标(成交)结果公告"
                                    target="_blank">中纬工程管理咨询有限公司关于苍南县应急管理局安全技能提升项...</a></span>
                            <span><a href="/wzcms/zfcgdybc/73542.htm"
                                    title="浙江得信工程管理有限公司关于瑞安市云周街道站西社区、周苌村垃圾临时堆放场清运服务（重2）的废标公告"
                                    target="_blank">浙江得信工程管理有限公司关于瑞安市云周街道站西社区、周苌村...</a></span>
                            <span><a href="/wzcms/zfcgdybc/73541.htm" title="温州中源工程造价咨询有限公司关于温州市榕园学校教学用具采购项目的更正公告"
                                    target="_blank">温州中源工程造价咨询有限公司关于温州市榕园学校教学用具采购...</a></span>
                            <span><a href="/wzcms/zfcgcggg/73540.htm"
                                    title="温州元信工程项目管理有限公司关于温州市第十七届运动会（青少年部）田径比赛承办服务的公开招标公告"
                                    target="_blank">温州元信工程项目管理有限公司关于温州市第十七届运动会（青少...</a></span>
                            <span><a href="/wzcms/zfcgcggg/73539.htm"
                                    title="温州元信工程项目管理有限公司关于温州市第十七届运动会（青少年部）游泳比赛承办服务的公开招标公告"
                                    target="_blank">温州元信工程项目管理有限公司关于温州市第十七届运动会（青少...</a></span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

        <table>
            <tbody>
                <tr>
                    <td>
                        <h4></h4><strong>上一篇：</strong><a
                            href="/wzcms/zfcgcggg/70186.htm">浙江嘉德工程项目管理有限公司关于瑞安市城市道路建设规划（2021—2025年）的竞争性磋商公告</a>
                    </td>
                    <td>
                        <h4></h4>下一篇：<a href="/wzcms/zfcgcggg/70180.htm">浙江国际招（投）标公司关于瑞安市高楼镇卫生院胃镜系统项目的公开招标公告</a>
                    </td>
                </tr>
            </tbody>
        </table>

    </div>
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
        # "项目代码",

        # "项目金额",  # budget_amount
        # "预算金额（元）",

        # "中标价格",  # bid_amount
        # "中标价",
        # "中标（成交）金额(元)",

        # "招标方式",
        
        "开标时间",  # tenderopen_time
        "开启时间",
    ], field_name='tenderopen_time')
    # ], field_name='bid_amount', area_id="3320")
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