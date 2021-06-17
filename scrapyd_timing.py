import os
import json
import requests
import datetime
import copy

SCRAPYD_URL = "http://114.67.84.76:8060/"

default_setting = {
    # 'DOWNLOAD_DELAY': '1',  # 下载延迟
    # 'CONCURRENT_REQUESTS_PER_IP': '30',  # 单个ip并发最大值
    # 'MAX_CONNECTIONS': '50',  # MYSQL最大连接数
    # 'CONCURRENT_REQUESTS': '2',
    'ENABLE_PROXY_USE': 'True',  # 是否启用ip代理
}


def exec_each_schedule(c_item, c_area_id, arg_choices=None, if_incr=False, **kwargs):
    """
    执行站点自定义配置爬虫计划
    Args:
        arg_choices: 时间参数
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
        args=arg_choices if if_incr else {},
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
    days_before = get_back_date(2)
    yesterday = get_back_date(1)
    today = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

    # 需要运行的spiders
    spider_list = [
        "province_00_quanguo_spider",
        "province_02_beijing_spider",
        "province_03_tianjin_spider",
        "province_04_hebei_spider",
        "province_05_shanxi_spider",
        "province_08_jilin_spider",
        "province_10_heilongjiang_spider",
        "province_11_shanghai_spider",
        "province_13_jiangsu_spider",
        "province_14_zhejiang_spider",
        "province_15_zhejiang_spider",
        "province_16_anhui_spider", 
        "province_18_fujian_spider",
        "province_19_jiangxi_spider",
        "province_21_shandong_spider",
        "province_23_henan_spider",
        "province_26_hubei_spider",
        "province_28_hunan_spider",
        "province_30_guangdong_spider",
        # "province_40_sichuan_spider",
        "province_41_guizhou_spider",
        "province_44_xizang_spider",
        "province_45_shanxi_spider",
        # "province_49_ningxia_spider",
        "province_50_xinjiang_spider",
        "province_52_pinming_spider",
        "province_53_bilian_spider",
        "province_54_Egongxiang_spider",
        "province_55_tiangong_spider",
        "province_56_hebeijiantou_spider",
        "province_57_jingcaizongheng_spider",
        "province_59_xinzhi_spider",
        "province_65_guoepingtai_spider",
        "province_67_yangguangyizhao_spider",
        "province_68_qilu_spider",
        "province_62_xindian_spider", 
        "province_71_zhaocaijingbao_spider",
        "province_78_zhuzhaixiushan_spider",
        "province_79_xinEcai_spider",
        "province_83_wangcai_spider",
        "province_85_anzhuangxinxi_spider",
        "ZJ_city_3302_zjcaigou_spider",
        "ZJ_enterprise_3303_zhenengjituan_spider",
        "ZJ_enterprise_3304_shuiliting_spider",
        "ZJ_city_3305_ningbo_spider",
        "ZJ_city_3306_jiaxing_spider",
        "ZJ_city_3307_huzhou_spider",
        "ZJ_city_3309_wenzhou_spider",
        "ZJ_city_3312_shaoxing_spider",
        "ZJ_city_3313_zhoushan_spider",
        "ZJ_city_3314_yuhang_spider",
        "ZJ_city_3315_keqiao_spider",
        "ZJ_city_3318_jinhua_spider",
        "ZJ_city_3319_changxing_spider",
        "ZJ_city_3320_cangnan_spider",
        "ZJ_city_3321_linhai_spider",
        "ZJ_city_3322_anji_spider",
        "ZJ_city_3323_xiaoshan_spider",
        "ZJ_city_3324_nanxun_spider",
        "ZJ_city_3326_longyou_spider",
        "ZJ_city_3327_pingyang_spider",
        "ZJ_city_3328_changshan_spider",
        "qcc_crawler",
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
                info = {}

                arg_choices = {
                    'sdt': yesterday,
                    'edt': today,
                    # 'day': 30
                }

                if_incr = True
                if item == "province_02_beijing_spider":
                    if_incr = True
                    # CONCURRENT_REQUESTS_PER_IP
                    info = {
                        'RANDOMIZE_DOWNLOAD_DELAY': True,
                        'ENABLE_PROXY_USE': 'True',
                    }

                    arg_choices = {
                        'day': 1
                    }
                if item == "province_21_shandong_spider":
                    if_incr = True
                    # CONCURRENT_REQUESTS_PER_IP
                    info = {
                        'RANDOMIZE_DOWNLOAD_DELAY': True,
                        'ENABLE_PROXY_USE': 'True',
                    }

                    arg_choices = {
                        'day': 1
                    }
                # if item == "ZJ_city_3319_changxing_spider":  # 特殊处理,根据需求
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_DELAY": 5}
                # if item == "province_57_jingcaizongheng_spider":
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_TIMEOUT": 15, 'ROBOTSTXT_OBEY': False}
                # if item == "province_21_shandong_spider":
                #     if_incr = True
                #     # CONCURRENT_REQUESTS_PER_IP
                #     info = {
                #         # "ENABLE_PROXY_USE": False,
                #         # 'CONCURRENT_REQUESTS_PER_IP': 20,
                #         "DOWNLOAD_TIMEOUT": 0.5,
                #         'CONCURRENT_REQUESTS': 10,
                #         'RANDOMIZE_DOWNLOAD_DELAY': True,
                #     }
                #
                #     arg_choices = {
                #         'day': 30
                #     }
                # if item == "province_00_quanguo_spider":  # 特殊处理,根据需求
                #     if_incr = True
                #
                #     info = {
                #         "ENABLE_PROXY_USE": False,
                #         "DOWNLOAD_DELAY": 0,
                #         "DOWNLOAD_TIMEOUT": 20,
                #         "CONCURRENT_REQUESTS_PER_IP": 20,
                #         "CONCURRENT_REQUESTS": 5,
                #     }  # province_00_quanguo_spider
                # if item == "ZJ_city_3314_yuhang_spider":  # 特殊处理,根据需求
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_DELAY": 5}
                #
                # if item == "ZJ_city_3309_wenzhou_spider":
                #     info = {"ENABLE_PROXY_USE": False}
                #     # info = {"DOWNLOAD_TIMEOUT": 60}
                #     # info = {"DOWNLOAD_DELAY": 0.5, "DOWNLOAD_TIMEOUT": 20, 'RANDOMIZE_DOWNLOAD_DELAY': True}
                # if item == "province_44_xizang_spider":
                #     info = {"ENABLE_PROXY_USE": False, "CONCURRENT_REQUESTS": 5, "DOWNLOAD_TIMEOUT": 60}
                # if item == "province_11_shanghai_spider":
                #     info = {
                #         "DOWNLOAD_TIMEOUT": 0,
                #         'RANDOMIZE_DOWNLOAD_DELAY': True,
                #         'DOWNLOAD_DELAY': 1,
                #         'RETRY_ENABLED': False,
                #     }
                resp = exec_each_schedule(item, area_id, arg_choices=arg_choices, if_incr=if_incr, **info)

                if resp:
                    print('运行{0}成功!'.format(item))
