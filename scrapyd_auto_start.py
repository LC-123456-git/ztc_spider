import os
import json
import requests
import datetime
from dateutil.relativedelta import relativedelta
import copy

SCRAPYD_URL = "http://114.67.84.76:8060/"
DIR_PATH = os.path.dirname(os.path.abspath(__file__))

default_setting = {
    'DOWNLOAD_DELAY': '1',  # 下载延迟
    'CONCURRENT_REQUESTS_PER_IP': '30',  # 单个ip并发最大值
    'MAX_CONNECTIONS': '50',  # MYSQL最大连接数
    'CONCURRENT_REQUESTS': '2',
    'ENABLE_PROXY_USE': 'False',  # 是否启用ip代理
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


def scrapyd_deploy(target="data-server", project="spider_pro"):
    cmd_str = f"scrapyd-deploy {target} -p {project}"
    cmd_path = os.path.join(DIR_PATH, project)
    os.chdir(cmd_path)
    os.system(cmd_str)


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


def scrapyd_list_projects():
    """
    获取上传到此Scrapy服务器的项目列表。
    :return:{ “ status” ： “ ok” ， “ projects” ： [ “ myproject” ， “ otherproject” ]}
    """
    r = requests.get(url=f"{SCRAPYD_URL}listprojects.json")
    return r.status_code, r.text


def scrapyd_list_versions(project="spider_pro"):
    """
    获取可用于某些项目的版本列表。按顺序返回版本，最后一个是当前使用的版本
    :param project:项目名称
    :return: { “ status” ： “ ok” ， “ versions” ： [ “ r99” ， “ r156” ]}
    """
    r = requests.get(url=f"{SCRAPYD_URL}listversions.json", params={
        "project": project
    })
    return r.status_code, r.text


def scrapyd_spiders(project="spider_pro", _version="1.0"):
    """
    获取某个项目的最新（除非被覆盖）版本中可用的蜘蛛列表
    :param project:项目名称
    :param _version:要检查的项目的版本
    :return:{ “ status” ： “ ok” ， “ spiders” ： [ “ spider1” ， “ spider2” ， “ spider3” ]}
    """
    r = requests.get(url=f"{SCRAPYD_URL}listspiders.json", params={
        "project": project,
        "_version": _version,
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


def scrapyd_delete_version(project_name="spider_pro", version="1.0"):
    """
    删除项目版本。如果给定项目没有更多版本可用，则该项目也将被删除。
    :param project_name: 项目名称
    :param version: 项目版本
    :return: { “ status” ： “ ok” }
    """
    r = requests.post(url=f"{SCRAPYD_URL}delversion.json", params={
        "project": project_name,
        "version": version,
    })
    return r.status_code, r.text


def scrapyd_delete_project(project="spider_pro"):
    """
    删除项目及其所有上载的版本
    :param project: 项目名称
    :return: { “ status” ： “ ok” }
    """
    r = requests.post(url=f"{SCRAPYD_URL}delproject.json", params={
        "project": project,
    })
    return r.status_code, r.text


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


def get_back_date_by_month(month):
    """
    获取往日时间格式，按月
    :param month: 月数
    :param day:
    :return:
    """
    month = int(month)
    today = datetime.datetime.now()
    if month == 0:
        return today.strftime("%Y-%m-%d")
    else:
        return (today - relativedelta(months=month)).strftime("%Y-%m-%d")


if __name__ == "__main__":
    # scrapyd_deploy()

    # scrapyd_cancel(job='city-2021-05-10-13-38')
    days_before = get_back_date(15)
    yesterday = get_back_date(1)
    today = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

    # miaokela
    # ZJ_city_3320_cangnan_spider 
    # ZJ_city_3319_changxing_spider 
    # ZJ_city_3314_yuhang_spider 
    # province_55_tiangong_spider 
    # province_53_bilian_spider 
    # province_52_pinming_spider

    # error_01: twisted.internet.error.TimeoutError: User timeout caused connection failure  # 通过DOWNLOAD_DELAY解决
    # error_02: TypeError: expected string or bytes-like object
    # error_03: KeyError: 'NoticesItem does not support field: web_name'
    # error_04: AttributeError: 'NoneType' object has no attribute 'replace'
    # error_05: twisted.web._newclient.ResponseFailed: [<twisted.python.failure.Failure builtins.ValueError: Too many Content-Length headers; response is invalid>]
    # error_06: (1366, "Incorrect integer value: '宸ヤ綔鍔ㄦ€�' for column 'notice_type' at row 1")
    # error_07: ERROR: Gave up retrying <POST https://www.shggzy.com/queryContent_31-jyxx.jspx> (failed 4 times): 403 Forbidden
    # error_08: TypeError: argument of type 'NoneType' is not iterable
    # error_09: IndexError: string index out of range
    # error_10: 404
    # error_11:  Crawled 1218 pages (at 0 pages/min), scraped 0 items (at 0 items/min)
    # error_12: TypeError: to_bytes must receive a str or bytes object, got NoneType
    # 需要运行的spiders
    spider_list = [
        # "province_00_quanguo_spider",  # error_12
        # "province_02_beijing_spider",  # ok
        # "province_03_tianjin_spider",  # ok
        # "province_04_hebei_spider",  # error_04
        # "province_05_shanxi_spider",
        # "province_08_jilin_spider",  # ok + error_06
        "province_10_heilongjiang_spider",  # error
        # "province_11_shanghai_spider",  # ok
        # "province_13_jiangsu_spider",  # error_07 + error_01
        # "province_14_zhejiang_spider",  # error
        # "province_15_zhejiang_spider",  # ok
        # "province_16_anhui_spider",  # ok + error_02
        # "province_18_fujian_spider",  # ok + error_05
        # "province_19_jiangxi_spider",  # error
        # "province_21_shandong_spider",  # error
        # "province_23_henan_spider",  # error_11
        # "province_26_hubei_spider",  # ok
        # "province_30_guangdong_spider",  # error_01
        # "province_40_sichuan_spider",  # error
        # "province_44_xizang_spider",  # error_01
        # "province_49_ningxia_spider",  # error_03
        # "province_50_xinjiang_spider",  # ok + 附件没采
        # "province_52_pinming_spider",  # ok
        # "province_53_bilian_spider",  # ok
        # "province_54_Egongxiang_spider",  # ok + error_09
        # "province_55_tiangong_spider",  # ok
        # "province_57_jingcaizongheng_spider",  # error_01
        # "province_71_zhaocaijingbao_spider",  # error_04
        # "ZJ_enterprise_3303_zhenengjituan_spider",  # ok
        # "ZJ_enterprise_3304_shuiliting_spider",  # ok
        # "ZJ_city_3305_ningbo_spider",  # ok  + error_08
        # "ZJ_city_3306_jiaxing_spider",  # error_01
        # "ZJ_city_3307_huzhou_spider",  # ok + error_01
        # "ZJ_city_3309_wenzhou_spider",  # error_02
        # "ZJ_city_3312_shaoxing_spider",  # ok + error_01
        # "ZJ_city_3313_zhoushan_spider",  # ok
        # "ZJ_city_3314_yuhang_spider",  # ok
        # "ZJ_city_3315_keqiao_spider",  # ok
        # "ZJ_city_3318_jinhua_spider",  # ok + error_01
        # "ZJ_city_3319_changxing_spider",  # ok
        # "ZJ_city_3320_cangnan_spider",  # error_01
        # "ZJ_city_3321_linhai_spider",
        # "ZJ_city_3322_anji_spider",
        "ZJ_city_3323_xiaoshan_spider",
    ]

    # 优先判断运行状态
    r_code, r_text = scrapyd_list_jobs()
    if r_code:
        scrapyd_deploy()  # 打包上传 TODO 如果是定时脚本则不需要上传
        pending_list = []
        running_list = []
        # print(scrapyd_cancel(project="spider_pro", job="10-2021-05-14-16-25"))
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
                    'sdt': days_before,
                    'edt': today,
                    # 'day': 30
                }

                if_incr = False
                # if item == "ZJ_city_3319_changxing_spider":  # 特殊处理,根据需求
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_DELAY": 5}
                # if item == "province_57_jingcaizongheng_spider":
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_TIMEOUT": 15, 'ROBOTSTXT_OBEY': False}
                if item == "province_21_shandong_spider":
                    if_incr = True
                    # CONCURRENT_REQUESTS_PER_IP
                    info = {
                        # "ENABLE_PROXY_USE": False,
                        # 'CONCURRENT_REQUESTS_PER_IP': 20,
                        "DOWNLOAD_TIMEOUT": 0.5,
                        'CONCURRENT_REQUESTS': 10,
                        'RANDOMIZE_DOWNLOAD_DELAY': True,
                    }

                    arg_choices = {
                        'day': 30
                    }
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
                # # if item == "province_11_shanghai_spider":
                # #     info = {
                # #         "DOWNLOAD_TIMEOUT": 0,
                # #         'RANDOMIZE_DOWNLOAD_DELAY': True,
                # #         'DOWNLOAD_DELAY': 1,
                # #         'RETRY_ENABLED': False,
                # #     }
                # if item == "ZJ_city_3323_xiaoshan_spider":
                #     if_incr = True
                #     info = {"ENABLE_PROXY_USE": False, "DOWNLOAD_TIMEOUT": 40}
                resp = exec_each_schedule(item, area_id, arg_choices=arg_choices, if_incr=if_incr, **info)

                if resp:
                    print('运行{0}成功!'.format(item))
