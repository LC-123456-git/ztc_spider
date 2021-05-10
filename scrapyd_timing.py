import os
import json
import requests
import datetime
import copy

SCRAPYD_URL = "http://114.67.84.76:8060/"

default_setting = {
    'DOWNLOAD_DELAY': '1',  # 下载延迟
    'CONCURRENT_REQUESTS_PER_IP': '30',  # 单个ip并发最大值
    'MAX_CONNECTIONS': '50',  # MYSQL最大连接数
    'CONCURRENT_REQUESTS': '2',
    'ENABLE_PROXY_USE': 'Flase',  # 是否启用ip代理
}


def exec_each_schedule(c_item, c_area_id, start_time, end_time, if_incr=False, **kwargs):
    """
    执行站点自定义配置爬虫计划
    Args:
        if_incr: 是否增量
        c_item: 爬虫文件
        c_area_id: 站点id
        start_time: 起始时间
        end_time: 终止时间
        **kwargs: 例如 **{"ENABLE_PROXY_USE":"True"}

    Returns:
        rs: 响应结果
    """
    c_setting = copy.deepcopy(default_setting)
    if kwargs:
        c_setting.update(**kwargs)
    now_time = datetime.datetime.now()
    c_today = '{0:%Y-%m-%d}'.format(now_time)
    c_suffix = '{0}-{1}'.format(now_time.hour, now_time.minute)

    rs, _ = scrapyd_schedule(
        spider=c_item, job='{0}-{1}-{2}'.format(c_area_id, c_today, c_suffix),
        args={
            "sdt": start_time,
            "edt": end_time,
        } if if_incr else {},
        setting=['{k}={v}'.format(k=k, v=v) for k, v in c_setting.items()]
    )
    return rs


def scrapyd_status():
    """
    检查服务的负载状态
    :return:{  “ status” ： “ ok” ， “ running” ： “ 0” ， “ pending” ： “ 0” ， “ finished” ： “ 0” ，
            “ node_name” ： “ node-name”  }
    """
    try:
        r = requests.get(url=f"{SCRAPYD_URL}daemonstatus.json", timeout=10)
        if r.status_code == 200:
            r_dict = json.loads(r.text)
            if r_dict.get("status") == "ok":
                return True, json.loads(r.text)
        return False, ""
    except:
        return False, ""


def scrapyd_schedule(spider, args, setting, project_name="spider_pro", job="49"):
    temp_dict = {
        "project": project_name,
        "spider": spider,
        "jobid": job,
        "setting": setting
        # "_version ": "1.0",
    }
    temp_dict.update(args)
    try:
        r = requests.post(url=f"{SCRAPYD_URL}schedule.json", data=temp_dict)
        if r.status_code == 200:
            return True, ""
    except:
        return False, "运行失败"


def scrapyd_cancel(project="spider_pro", job="49"):
    """
    取消爬虫运行（AKA。工作）。如果作业挂起，则将删除。如果作业正在运行，则会终止
    :param project:项目名称
    :param job:工作ID
    :return:
    """
    r = requests.post(url=f"{SCRAPYD_URL}cancel.json", data={
        "project": project,
        "job": job,
    })
    return r.status_code, r.text


def scrapyd_list_jobs(project_name: str = "spider_pro"):
    """
    获取某个项目的挂起，正在运行和已完成的作业的列表
    :param project_name: -将结果限制为项目名称
    :return:
    """
    try:
        r = requests.get(url=f"{SCRAPYD_URL}listjobs.json", params={
            "project": project_name
        }, timeout=10)
        if r.status_code == 200:
            r_dict = json.loads(r.text)
            if r_dict.get("status") == "ok":
                return True, json.loads(r.text)
        return False, ""
    except:
        return False, ""


def get_back_date(day):
    """
    获取往日时间格式
    :param day:
    :return:
    """
    day = int(day)
    today = datetime.datetime.now()
    if day == 0:
        return today.strftime("%Y-%m-%d")
    else:
        return (today - datetime.timedelta(days=day)).strftime("%Y-%m-%d")


if __name__ == "__main__":
    days_before = get_back_date(10)
    yesterday = get_back_date(1)
    today = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

    # 需要运行的spiders
    spider_list = [  # 57
        "province_00_quanguo_spider",  # error_12
        "province_02_beijing_spider",  # ok
        "province_03_tianjin_spider",  # ok
        "province_04_hebei_spider",  # error_04
        "province_05_shanxi_spider",
        "province_08_jilin_spider",  # ok + error_06
        "province_10_heilongjiang_spider",  # error
        "province_11_shanghai_spider",  # ok
        "province_13_jiangsu_spider",  # error_07 + error_01
        "province_14_zhejiang_spider",  # error
        "province_15_zhejiang_spider",  # ok
        "province_16_anhui_spider",  # ok + error_02
        "province_18_fujian_spider",  # ok + error_05
        "province_19_jiangxi_spider",  # error
        "province_21_shandong_spider",  # error
        "province_23_henan_spider",  # error_11
        "province_26_hubei_spider",  # ok
        "province_30_guangdong_spider",  # error_01
        "province_40_sichuan_spider",  # error
        "province_44_xizang_spider",  # error_01
        "province_49_ningxia_spider",  # error_03
        "province_50_xinjiang_spider",  # ok + 附件没采
        "province_52_pinming_spider",  # ok
        "province_53_bilian_spider",  # ok
        "province_54_Egongxiang_spider",  # ok + error_09
        "province_55_tiangong_spider",  # ok
        "province_57_jingcaizongheng_spider",  # error_01
        "province_71_zhaocaijingbao_spider",  # error_04
        "ZJ_enterprise_3303_zhenengjituan_spider",  # ok
        "ZJ_enterprise_3304_shuiliting_spider",  # ok
        "ZJ_city_3305_ningbo_spider",  # ok  + error_08
        "ZJ_city_3306_jiaxing_spider",  # error_01
        "ZJ_city_3307_huzhou_spider",  # ok + error_01
        "ZJ_city_3309_wenzhou_spider",  # error_02
        "ZJ_city_3312_shaoxing_spider",  # ok + error_01
        "ZJ_city_3313_zhoushan_spider",  # ok
        "ZJ_city_3314_yuhang_spider",  # ok
        "ZJ_city_3315_keqiao_spider",  # ok
        "ZJ_city_3318_jinhua_spider",  # ok + error_01
        "ZJ_city_3319_changxing_spider",  # ok
        "ZJ_city_3320_cangnan_spider",  # error_01
    ]

    # 优先判断运行状态
    r_code, r_text = scrapyd_list_jobs()
    if r_code:
        pending_list = []
        running_list = []
        for item in r_text.get("pending"):
            pending_list.append(item.get("spider"))
        for item in r_text.get("running"):
            running_list.append(item.get("spider"))
        for item in spider_list:
            if item in pending_list or item in running_list:
                print(f"运行 {item} 无效 原因：正在运行或准备当中...")
                continue
            else:
                # 允许运行脚本
                area_id = item.split("_")[1]

                if item == "province_00_quanguo_spider": pass  # 特殊处理,根据需求

                resp = exec_each_schedule(item, area_id, days_before, today, if_incr=True)

                if resp:
                    print('运行{0}成功!'.format(item))
