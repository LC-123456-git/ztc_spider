#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-18
# @Describe: Items

import scrapy


class NoticesItem(scrapy.Item):
    table_name = "notices"
    table_desc = "公告"

    # 采集字段
    origin = scrapy.Field({"idx": 1, "comment": "来源链接"})
    title_name = scrapy.Field({"idx": 2, "comment": "公告标题"})
    pub_time = scrapy.Field({"idx": 3, "comment": "公告发布时间", "default": "1970-01-01"})
    info_source = scrapy.Field({"idx": 4, "comment": "信息来源"})
    content = scrapy.Field({"idx": 5, "comment": "内容"})
    create_time = scrapy.Field({"idx": 6, "comment": "创建时间"})
    update_time = scrapy.Field({"idx": 7, "comment": "更新时间"})
    is_have_file = scrapy.Field({"idx": 8, "comment": "是否包含文件"})
    files_path = scrapy.Field({"idx": 9, "comment": "文件相对路径，按英文逗号隔开"})
    notice_type = scrapy.Field(
        {"idx": 10, "comment": "公告类型"})  # 0#招标公告 1#招标预告 2#招标变更 3#招标异常 4#中标预告 5#中标公告 6#资格预审结果公告 7#其他公告
    area_id = scrapy.Field({"idx": 11, "comment": "地区ID"})

    # 采集新增字段
    category = scrapy.Field({"idx": 53, "comment": "种类"})
    business_category = scrapy.Field({"idx": 54, "comment": "业务种类"})

    # 清洗字段
    title = scrapy.Field({"idx": 13, "comment": "公告标题"})
    project_number = scrapy.Field({"idx": 14, "comment": "项目编号"})
    project_name = scrapy.Field({"idx": 15, "comment": "项目名称"})
    tenderee = scrapy.Field({"idx": 16, "comment": "招标人"})
    bidding_agency = scrapy.Field({"idx": 17, "comment": "招标代理"})

    area_code = scrapy.Field({"idx": 18, "comment": "区县编号"})
    area = scrapy.Field({"idx": 19, "comment": "地区"})
    address = scrapy.Field({"idx": 20, "comment": "详细地址"})
    email = scrapy.Field({"idx": 21, "comment": "电子邮箱"})
    description = scrapy.Field({"idx": 22, "comment": "招标方案说明"})

    bid_type = scrapy.Field({"idx": 23, "comment": "招标方式"})
    bid_modus = scrapy.Field({"idx": 24, "comment": "招标组织形式"})
    inspect_dept = scrapy.Field({"idx": 25, "comment": "监督部门"})
    review_dept = scrapy.Field({"idx": 26, "comment": "审核部门"})
    notice_nature = scrapy.Field({"idx": 27, "comment": "公告性质"})

    bid_file = scrapy.Field({"idx": 28, "comment": "招标文件"})
    bid_file_start_time = scrapy.Field({"idx": 29, "comment": "招标文件获取开始时间"})
    bid_file_end_time = scrapy.Field({"idx": 30, "comment": "招标文件获取截止时间"})
    apply_end_time = scrapy.Field({"idx": 31, "comment": "报名截止时间"})
    notice_start_time = scrapy.Field({"idx": 32, "comment": "公告开始时间"})

    notice_end_time = scrapy.Field({"idx": 33, "comment": "公告结束时间"})
    aberrant_type = scrapy.Field({"idx": 34, "comment": "异常类型"})
    budget_amount = scrapy.Field({"idx": 35, "comment": "预算金额"})
    tenderopen_time = scrapy.Field({"idx": 36, "comment": "开标时间"})

    publish_time = scrapy.Field({"idx": 37, "comment": "发布时间"})
    liaison = scrapy.Field({"idx": 38, "comment": "联系人"})
    contact_information = scrapy.Field({"idx": 39, "comment": "联系方式"})
    classify_id = scrapy.Field({"idx": 41, "comment": "公告分类id"})

    classify_name = scrapy.Field({"idx": 42, "comment": "公告分类名称"})
    project_type = scrapy.Field({"idx": 43, "comment": "项目类型"})
    state = scrapy.Field({"idx": 44, "comment": "状态0-待发布1-已发布2-已下架3-待审核4-审核拒绝", "default": "0"})
    file_ids = scrapy.Field({"idx": 45, "comment": "附件ids"})
    company_type = scrapy.Field({"idx": 46, "comment": "单位类型"})

    successful_bidder = scrapy.Field({"idx": 47, "comment": "中标方"})
    bid_amount = scrapy.Field({"idx": 48, "comment": "中标金额"})
    sign_type = scrapy.Field({"idx": 49, "comment": "标讯类型 0-平台发布1-用户发布2-采集发布", "default": "2"})
    source = scrapy.Field({"idx": 50, "comment": "来源(采集的公告就填写采集网站、用户和平台发布就用用户名)"})
    source_url = scrapy.Field({"idx": 51, "comment": "采集发布来源网站URL"})

    # 标记字段
    is_clean = scrapy.Field({"idx": 52, "comment": "是否清洗 0 未清洗 1清洗", "default": "0"})


class FileItem(scrapy.Item):
    file_url = scrapy.Field()  # 附件下载链接
    file_name = scrapy.Field()  # 附件名称
    file_type = scrapy.Field()  # 附件类型
    file_path = scrapy.Field()  # 附件存储位置


class AreaItem(scrapy.Item):
    table_name = "area"
    table_desc = "地区"
    area = scrapy.Field({"idx": 1, "comment": "地区"})
    address = scrapy.Field({"idx": 2, "comment": "地址"})
    name = scrapy.Field({"idx": 3, "comment": "名称"})
    url = scrapy.Field({"idx": 4, "comment": "网址"})


if __name__ == "__main__":
    pass
