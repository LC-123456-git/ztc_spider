import os
import json
import requests
import datetime
from dateutil.relativedelta import relativedelta
import copy

SCRAPYD_URL = "http://114.67.84.76:8060/"
DIR_PATH = os.path.dirname(os.path.abspath(__file__))

default_setting = {
    # 'DOWNLOAD_DELAY': '1',  # 下载延迟
    # 'CONCURRENT_REQUESTS_PER_IP': '30',  # 单个ip并发最大值
    # 'MAX_CONNECTIONS': '50',  # MYSQL最大连接数
    # 'CONCURRENT_REQUESTS': '2',
    # 'ENABLE_PROXY_USE': 'True',  # 是否启用ip代理
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

    days_before = get_back_date(10)
    yesterday = get_back_date(1)
    today = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

    spider_list = [
        # "province_00_quanguo_spider",  # error_12
        # "province_02_beijing_spider",  # ok
        # "province_03_tianjin_spider",  # ok
        # "province_04_hebei_spider",  # error_04
        # "province_05_shanxi_spider",
        # "province_08_jilin_spider",  # ok + error_06
        # "province_10_heilongjiang_spider",  # error
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
        # "province_39_chongqing_spider",  # error_01
        # "province_40_sichuan_spider",  # error
        # "province_41_guizhou_spider",
        # "province_44_xizang_spider",  # error_01
        # "province_45_shanxi_spider",  # error_01
        # "province_49_ningxia_spider",  # error_03
        # "province_50_xinjiang_spider",  # ok + 附件没采
        # "province_52_pinming_spider",  # ok
        # "province_53_bilian_spider",  # ok
        # "province_54_Egongxiang_spider",  # ok + error_09
        # "province_55_tiangong_spider",  # ok
        # "province_56_hebeijiantou_spider",  # ok
        # "province_57_jingcaizongheng_spider",  # error_01
        # "province_59_xinzhi_spider",
        # "province_62_xindian_spider",  # error_01
        # "province_68_qilu_spider",
        # "province_71_zhaocaijingbao_spider",  # error_04
        # "province_79_xinEcai_spider",
        # 'province_65_guoepingtai_spider',
        # "province_71_zhaocaijingbao_spider",  # error_04
        # "province_78_zhuzhaixiushan_spider",  # error_04
        # "province_83_wangcai_spider",
        # "province_85_anzhuangxinxi_spider"
        # "ZJ_city_3302_zjcaigou_spider"
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
        # "ZJ_city_3323_xiaoshan_spider",
        # "ZJ_city_3324_nanxun_spider",
        # "ZJ_city_3326_longyou_spider",
        # "qcc_crawler",
        # "ZJ_city_3327_pingyang_spider",
        # "ZJ_city_3331_fuyang_spider",
        # "ZJ_city_3332_chunan_spider",
        # "ZJ_city_3334_jiande_spider",
        # "ZJ_city_3335_wzlucheng_spider",
        # "ZJ_city_3336_yueqing_spider",
        # "ZJ_city_3337_ruian_spider",
        # "ZJ_city_3338_yongjia_spider",
        # "ZJ_city_3339_dongtou_spider",
        # "ZJ_city_3340_wencheng_spider",
        # "ZJ_city_3341_taishun_spider",
        "ZJ_city_3342_shangyu_spider",
        # "ZJ_city_3343_xinchang_spider",
        # "ZJ_city_3344_shengzhou_spider",
        # "ZJ_city_3345_yuecheng_spider",
    ]

    # 优先判断运行状态
    r_code, r_text = scrapyd_list_jobs()
    if r_code:
        scrapyd_deploy()  # 打包上传 TODO 如果是定时脚本则不需要上传
        pending_list = []
        running_list = []

    # print(scrapyd_cancel(project="spider_pro", job="62-2021-06-09-16-44"))
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
                    # 'day': 10
                }

                # if_incr = True            # 增量
                if_incr = False         # 全量
                resp = exec_each_schedule(item, area_id, arg_choices=arg_choices, if_incr=if_incr, **info)

                if resp:
                    print('运行{0}成功!'.format(item))

