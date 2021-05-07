#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/29
# @Author : wwj
# @Describe: 附件下载
from spider_pro.items import FileItem
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request


FILE_DOWNLOAD_TIMEOUT = 40


class FilePipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        if isinstance(item, FileItem):
            meta = {
                'spider': info.spider.name,
                'file_name': item['file_name'],
                'file_type': item['file_type'],
                'file_path': item['file_path'],
                'download_timeout': FILE_DOWNLOAD_TIMEOUT,
            }
            yield Request(item['file_url'], meta=meta)

    def file_path(self, request, response=None, info=None, item=None):
        file_path = request.meta['file_path']
        return file_path
