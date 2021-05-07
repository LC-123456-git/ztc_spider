#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2021-01-04
# @Describe: 读取日志重新请求数据并入库
import re


def read_urls_from_log(log_path):
    s = set()
    with open(log_path, "r", encoding="utf-8") as f:
        while True:
            t = f.readline()
            if not t:
                break
            if g := re.search(r"'origin': '.*', 'title_name", t):
                url = g.group(0).split(r"'origin': '")[1].split(r"', 'title_name")[0]
                if url not in s:
                    s.add(url)


if __name__ == "__main__":
    log_path = r"C:\Users\PC\Documents\Tencent Files\376762719\FileRecv\491.log.txt"
    read_urls_from_log(log_path)
    pass