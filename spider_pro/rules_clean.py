import re
import pandas
import math
import copy
from lxml import etree


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
                        content_list = doc.xpath("//div[@class='WordSection1']//text()")

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
                            content_list.remove("工程概况")
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
                                # print(value.strip())
                            tag = item.split(":")[-1].split("：")[-1].split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}[:|：].*?</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    return value.strip()
                                    # print(value.strip())

                    # 匹配带冒号开始的文本内容后面有标签且换行的
                    if key in str(re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)):
                        all_results_value = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[1::2]
                        all_results_key = re.findall(re.compile(r'<td style=".*?">(.*?)</td>', re.S), content)[::2]
                        for value, key_keys in zip(all_results_value, all_results_key):
                            if key in key_keys:
                                value = value.replace('\xa0', '')
                                if value.strip():
                                    # print(value.strip())
                                    return value.strip()

                    # 匹配带空格开始的文本内容
                    all_results = re.findall(fr"{key}\s+?<", content)
                    if all_results:
                        for item in all_results:
                            value_list = item.split(" ")
                            for v_item in value_list:
                                if v_item.strip():
                                    # print(v_item.strip())
                                    return v_item.strip()

                    # 匹配不带任何开始标记的文本内容
                    all_results = re.findall(fr"{key}</.*?>", content)
                    if all_results:
                        for item in all_results:
                            tag = item.split("</")[-1].split(">")[0]
                            if value_str := re.search(fr"{key}</{tag}>.*?<{tag}.*?>.*?</{tag}>", content):
                                value = value_str.group().split(">")[-2].split("</")[0]
                                if value.strip():
                                    # print(value.strip())
                                    return value.strip()

                # return ""
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

    @staticmethod
    def is_horizon(table_content):
        """
        判断tr下td数是否相同
        """
        status = 1
        try:
            doc = etree.HTML(table_content)
            tr_els = doc.xpath('//tr')
            tds = []
            for tr_el in tr_els:
                td_els = tr_el.xpath('./td')
                if not td_els:
                    td_els = tr_el.xpath('./th')
                tds.append(len(td_els))
            if len(set(tds)) == 1:
                status = 0
        except Exception as e:
            print('is_horizon error: ', e)
        return status

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
                            if KeywordsExtract.is_horizon(table_txt):
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
                                        assert int(t_key), 'TH NODE.'
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
                    ]
                if self.field_name == 'tenderee':
                    regular_list = [
                        r'招标人为([\u4e00-\u9fa5 （ ）]+?)[, ， 。]',
                    ]
                if self.field_name == 'bidding_agency':
                    regular_list = [
                        r'招标代理机构：(.*?)地',
                        r'委托([^，,、]*?)[进行 , ，]',
                    ]
                if self.field_name == 'project_number':  # 项目代码：2020-330327-48-01-167360）批准建  目（编号：A3303270480001353001001）招标文件（以
                    regular_list = [
                        r'[项目代码|编号][\： \:]([0-9 A-Z a-z \-]+)\）',
                    ]
                if self.field_name == 'budget_amount':  # 本工程预算金额约为479万元。
                    regular_list = [
                        r'预算金额.*?为(\d+)万元'
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
        去除符号
        """
        symbols = ['？', '?']

        try:
            for symbol in symbols:
                self._value = ''.join(self._value.split(symbol))
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
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 18pt"
                                                        align="center"><b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">浙江天诚工程咨询有限公司关于<span>2021</span>年温州市生态环境局苍南分局空气检测设备采购项目的中标<span>(</span>成交<span>)</span>结果公告</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 18pt"
                                                        align="left"><b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">一、项目编号：</span></b><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black"> </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">CNDL2021177</span>
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 18pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">二、项目名称：</span></b><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black"> </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">2021</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">年温州市生态环境局苍南分局空气检测设备采购项目</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 18pt"
                                                        align="left"><b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">三、中标（成交）信息</span></b><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'Arial','sans-serif'; COLOR: black"> </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             1.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">中标结果：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">  </span>
                                                    </p>
                                                    <table style="WIDTH: 728.1pt; BORDER-COLLAPSE: collapse" cellspacing="0"
                                                        cellpadding="0" width="971" border="0">
                                                        <thead>
                                                            <tr style="HEIGHT: 20.65pt">
                                                                <td
                                                                    style="BORDER-TOP: #bbbbbb 1.5pt solid; HEIGHT: 20.65pt; BORDER-RIGHT: #dddddd 1pt solid; BACKGROUND: white; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><b><span
                                                                                style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">序号</span></b>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: #bbbbbb 1.5pt solid; HEIGHT: 20.65pt; BORDER-RIGHT: #dddddd 1pt solid; BACKGROUND: white; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><b><span
                                                                                style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">中标（成交）金额<span>(</span>元<span>)</span></span></b>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: #bbbbbb 1.5pt solid; HEIGHT: 20.65pt; BORDER-RIGHT: #dddddd 1pt solid; BACKGROUND: white; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><b><span
                                                                                style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">中标供应商名称</span></b>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: #bbbbbb 1.5pt solid; HEIGHT: 20.65pt; BORDER-RIGHT: #dddddd 1pt solid; BACKGROUND: white; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><b><span
                                                                                style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">中标供应商地址</span></b>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            <tr style="HEIGHT: 21.4pt">
                                                                <td
                                                                    style="BORDER-TOP: medium none; HEIGHT: 21.4pt; BORDER-RIGHT: #dddddd 1pt solid; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">1</span>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: medium none; HEIGHT: 21.4pt; BORDER-RIGHT: #dddddd 1pt solid; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">最终报价<span>:425800(</span>元<span>)</span></span>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: medium none; HEIGHT: 21.4pt; BORDER-RIGHT: #dddddd 1pt solid; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">杭州千宁科技有限公司</span>
                                                                    </p>
                                                                </td>
                                                                <td
                                                                    style="BORDER-TOP: medium none; HEIGHT: 21.4pt; BORDER-RIGHT: #dddddd 1pt solid; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">里商乡向阳村<span>118</span>号</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             2.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">废标结果</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">:  </span>
                                                    </p>
                                                    <table style="WIDTH: 100%; BORDER-COLLAPSE: collapse" cellspacing="0"
                                                        cellpadding="0" width="100%" border="0">
                                                        <tbody>
                                                            <tr>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">序号</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">标项名称</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">废标理由</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">其他事项</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                            <tr>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">/</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">/</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">/</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 25%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="25%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">/</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 22.5pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">四、主要标的信息</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             1.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">货物类主要标的信息：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">  
                                                             </span></p>
                                                    <table style="WIDTH: 100%; BORDER-COLLAPSE: collapse" cellspacing="0"
                                                        cellpadding="0" width="100%" border="0">
                                                        <tbody>
                                                            <tr>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">序号</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">标项名称</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">标的名称</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">品牌</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">数量</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">单价（元）</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: #dddddd 1pt solid; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">规格型号</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                            <tr>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">1</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">2021</span><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">年温州市生态环境局苍南分局空气检测设备采购项目</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">便携式挥发性有机物气体分析仪</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">谱育科技</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">1</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">198600</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">EXPEC
                                                                            3100</span></p>
                                                                </td>
                                                            </tr>
                                                            <tr>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">2</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">2021</span><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">年温州市生态环境局苍南分局空气检测设备采购项目</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">风速风向仪</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">上海风云</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">8</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">2300</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">FYF-1</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                            <tr>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: #dddddd 1pt solid; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">3</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">2021</span><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">年温州市生态环境局苍南分局空气检测设备采购项目</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">手持式颗粒物检测仪</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">青岛明华</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">6</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">34800</span>
                                                                    </p>
                                                                </td>
                                                                <td style="BORDER-TOP: medium none; BORDER-RIGHT: #dddddd 1pt solid; WIDTH: 14%; BORDER-BOTTOM: #dddddd 1pt solid; PADDING-BOTTOM: 3.75pt; PADDING-TOP: 3.75pt; PADDING-LEFT: 7.5pt; BORDER-LEFT: medium none; PADDING-RIGHT: 7.5pt"
                                                                    width="14%">
                                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; WORD-BREAK: break-all; TEXT-ALIGN: center; TEXT-JUSTIFY: inter-ideograph; MARGIN: 0cm 0cm 7.5pt"
                                                                        align="center"><span
                                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 宋体">MH1020</span>
                                                                    </p>
                                                                </td>
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             2.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">工程类主要标的信息：</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             3.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">服务类主要标的信息：</span>
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 22.5pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">五、评审专家（单一来源采购人员）名单：</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">吴克飞</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">,</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">宋国光</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">,</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">林丙钱</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">,</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">徐登晓</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">,</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">袁超前</span>
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 22.5pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">六、代理服务收费标准及金额：</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             1.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">代理服务收费标准：按招标文件约定</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             2.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">代理服务收费金额（元）：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">8000 </span><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'Arial','sans-serif'; COLOR: black"> </span>
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 22.5pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">七、公告期限</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                             </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">自本公告发布之日起</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">1</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">个工作日。</span>
                                                    </p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 22.5pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">八、其他补充事宜</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 18pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              1.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">各参加政府采购活动的供应商认为该中标</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">/</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">成交结果和采购过程等使自己的权益受到损害的，可以自本公告期限届满之日（本公告发布之日后第</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">2</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">个工作日）起</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">7</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">个工作日内，以书面形式向采购人或受其委托的采购代理机构提出质疑。质疑供应商对采购人、采购代理机构的答复不满意或者采购人、采购代理机构未在规定的时间内作出答复的，可以在答复期满后十五个工作日内向同级政府采购监督管理部门投诉。质疑函范本、投诉书范本请到浙江政府采购网下载专区下载。</span><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'Arial','sans-serif'; COLOR: black"> 
                                                                      </span></p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 18pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              2.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">其他事项：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">无</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> </span><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'Arial','sans-serif'; COLOR: black">  
                                                                             </span></p>
                                                    <p
                                                        style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: justify; TEXT-JUSTIFY: inter-ideograph; MARGIN: 7.5pt 0cm; LINE-HEIGHT: 24pt">
                                                        <b><span
                                                                style="FONT-SIZE: 13.5pt; FONT-FAMILY: 黑体; COLOR: black">九、对本次公告内容提出询问、质疑、投诉，请按以下方式联系</span></b>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              1.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">采购人信息</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">名</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">称：温州市生态环境局苍南分局</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">地</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">址：苍南县灵溪镇江湾路环保大厦</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">3</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">楼</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">传</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">真：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">/ </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">项目联系人（询问）：陈先生</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">项目联系方式（询问）：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-59972971</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">质疑联系人：陈先生</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">质疑联系方式：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-59972971</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              2.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">采购代理机构信息</span><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">名</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">称：浙江天诚工程咨询有限公司</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">地</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">址：苍南县灵溪镇上江小区</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">1-17</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">栋</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">3</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">单元</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">302</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">室</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">传</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">真：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-68807257</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">项目联系人（询问）：郑先生</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">项目联系方式（询问）：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-68807257</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">、</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">17395770925</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">质疑联系人：袁楠楠</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">质疑联系方式：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-68807257 </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              3.</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">同级政府采购监督管理部门</span><span
                                                            style="FONT-SIZE: 12pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">  </span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">名</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">称：苍南县政府采购监督管理办公室</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">地</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">   
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">址：苍南县灵溪镇春晖路</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">555</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">号（苍南县行政审批中心对面）</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">传</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">真：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-59867927</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">联系人</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">
                                                        </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">：陈先生</span>
                                                    </p>
                                                    <p style="FONT-SIZE: 10.5pt; FONT-FAMILY: 'Calibri','sans-serif'; TEXT-ALIGN: left; TEXT-JUSTIFY: inter-ideograph; MARGIN: 3.75pt 0cm; LINE-HEIGHT: 22.5pt"
                                                        align="left"><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black"> 
                                                              </span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 宋体; COLOR: black">监督投诉电话：</span><span
                                                            style="FONT-SIZE: 13.5pt; FONT-FAMILY: 'FangSong','serif'; COLOR: black">0577-59867927 </span>
                                                    </p>
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
                                                    src="http://file.zhaotx.cn/view?systemUrl=webfile/20210512/jpg/CFE15D0415F7479AB4920FFF65517516.jpg"
                                                    width="17" height="16" /></td>
                                            <td />
                                            <td width="25" align="center"><img
                                                    src="http://file.zhaotx.cn/view?systemUrl=webfile/20210512/jpg/CB532CA698DE4DAFAC7748B18C3C9351.jpg"
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
        "项目名称",  # project_name
        "招标项目",
        "工程名称",
        "招标工程项目",

        # "中标单位",  # successful_bidder

        # "联系电话",  # contact_information
        # "联系方式",
        # "电\s*话",

        # "联系人",  # liaison
        # "联\s*系\s*人",
        # "项目经理",

        # "采购人信息[ψ \s]*?名[\s]+称",

        # "招标人",  # tenderee
        # "招&nbsp;标&nbsp;人",
        # "招标单位",
        # "采购人信息[ψ \s]*?名[\s]+称",
        # "招标代理机构",

        # "招标代理",  # bidding_agency
        # "采购代理机构信息[ψ \s]*?名[\s]+称",

        # "开启时间",

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
    ], field_name='project_name', area_id="3320")
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
