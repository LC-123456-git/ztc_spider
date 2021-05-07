import os
import json
import requests
import datetime
from dateutil.relativedelta import relativedelta


SCRAPYD_URL = "http://114.67.84.76:8060/"
DIR_PATH = os.path.dirname(os.path.abspath(__file__))


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
    today = get_back_date(0)
    yesterday = get_back_date(1)
    suffix = f"{datetime.datetime.now().hour}-{datetime.datetime.now().minute}"

    # 需要运行的spiders
    spider_list = [
        # "province_00_quanguo_spider",
        # "province_02_beijing_spider",
        # "province_03_tianjin_spider",
        # "province_04_hebei_spider",
        # "province_05_shanxi_spider",
        # "province_08_jilin_spider",
        # "province_10_heilongjiang_spider",
        # "province_11_shanghai_spider",
        # "province_13_jiangsu_spider",
        # "province_14_zhejiang_spider",
        # "province_15_zhejiang_spider",
        # "province_16_anhui_spider",
        # "province_18_fujian_spider",
        # "province_19_jiangxi_spider",
        # "province_21_shandong_spider",
        # "province_23_henan_spider",
        # "province_26_hubei_spider",

        # "province_40_sichuan_spider",
        # "ZJ_enterprise_3303_zhenengjituan_spider",
        "ZJ_city_3306_jiaxing_spider",
        # "ZJ_city_3305_ningbo_spider",
        # "ZJ_enterprise_3304_shuiliting_spider",
        # "ZJ_city_3309_wenzhou_spider",
        # "province_49_ningxia_spider",

        # "province_30_guangdong_spider",
        # "province_40_sichuan_spider",
        # "province_44_xizang_spider",
        "province_50_xinjiang_spider",
        # "ZJ_enterprise_3303_zhenengjituan_spider",
        # "ZJ_enterprise_3304_shuiliting_spider",
        # "ZJ_city_3305_ningbo_spider",
        # "ZJ_city_3306_jiaxing_spider",
        # "ZJ_city_3307_huzhou_spider",
        # "ZJ_city_3309_wenzhou_spider",
        # "ZJ_city_3312_shaoxing_spider",
        # "ZJ_city_3313_zhoushan_spider",
]

    # 优先判断运行状态
    r_code, r_text = scrapyd_list_jobs()
    if r_code:
        scrapyd_deploy()  # 打包上传 TODO 如果是定时脚本则不需要上传
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
                if item == "province_00_quanguo_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_02_beijing_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_03_tianjin_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_04_hebei_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_05_shanxi_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_08_jilin_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_10_heilongjiang_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_11_shanghai_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_13_jiangsu_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_14_zhejiang_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_15_zhejiang_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_16_anhui_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_18_fujian_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_19_jiangxi_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_21_shandong_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_23_henan_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_26_hubei_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_40_sichuan_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_44_xizang_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "province_50_xinjiang_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_enterprise_3303_zhenengjituan_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_city_3306_jiaxing_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",  # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=True"]  # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_city_3305_ningbo_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",  # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=True"]  # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_enterprise_3304_shuiliting_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",  # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]  # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_city_3307_huzhou_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",                             # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",                # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",                           # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]                       # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                elif item == "ZJ_city_3309_wenzhou_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            "sdt": f"{get_back_date(10)}",
                            "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",  # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]  # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")
                # elif item == "ZJ_city_3312_shaoxing_spider":
                #     start_day = today
                #     end_day = today
                #     rs, _ = scrapyd_schedule(
                #         spider=item, job=f"{area_id}-{today}-{suffix}",
                #         args={
                #             # "sdt": f"{get_back_date(10)}",
                #             # "edt": f"{end_day}",
                #         },
                #         setting=[
                #             "DOWNLOAD_DELAY=0",  # 下载延迟
                #             "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                #             "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                #             "CONCURRENT_REQUESTS=30",
                #             "CURRENT_HTTP_PROXY_MAX=2",
                #             "ENABLE_PROXY_USE=Flase"]  # 是否启用ip代理
                #     )
                #     if rs:
                #         print(f"运行 {item} 成功!")
                elif item == "ZJ_city_3313_zhoushan_spider":
                    start_day = today
                    end_day = today
                    rs, _ = scrapyd_schedule(
                        spider=item, job=f"{area_id}-{today}-{suffix}",
                        args={
                            # "sdt": f"{get_back_date(10)}",
                            # "edt": f"{end_day}",
                        },
                        setting=[
                            "DOWNLOAD_DELAY=0",  # 下载延迟
                            "CONCURRENT_REQUESTS_PER_IP=30",  # 单个ip并发最大值
                            "MAX_CONNECTIONS=50",  # MYSQL最大连接数
                            "CONCURRENT_REQUESTS=30",
                            "CURRENT_HTTP_PROXY_MAX=2",
                            "ENABLE_PROXY_USE=Flase"]  # 是否启用ip代理
                    )
                    if rs:
                        print(f"运行 {item} 成功!")


    # print(scrapyd_cancel(job=f"23-2021-01-28-11-40"))

    # scrapyd_deploy()  # 打包上传
    # spider_list = [
    #     # "province_00_quanguo_spider",
    #     # "province_02_beijing_spider",
    #     # "province_03_tianjin_spider",
    #     # "province_05_shanxi_spider",
    #     # "province_11_shanghai_spider",
    #     # "province_15_zhejiang_spider",
    #     # "province_19_jiangxi_spider",
    #     # "province_26_hubei_spider",
    #     # "province_49_ningxia_spider",
    # ]
    #
    # for item in spider_list:
    #     area_id = item.split("_")[1]
    #     if item == "province_00_quanguo_spider":  # 因为全量太慢，所以跑增量
    #         print(scrapyd_schedule(spider=item, job=f"{area_id}-{today}", args="day=3"))
    #         continue
    #     print(scrapyd_schedule(spider=item, job=f"{area_id}-{today}"))
    #
    # # for item in spider_list:
    # #     area_id = item.split("_")[1]
    # #     print(scrapyd_cancel(job=f"{area_id}-{today}"))
    #
    # # print(scrapyd_list_projects())  # 列举全部项目
    # # print(scrapyd_list_versions())  # 列举项目全部版本
    # # print(scrapyd_spiders())  # 列举项目全部spiders
    # # print(scrapyd_list_jobs())  # 列举项目全部spiders
    # # print(scrapyd_delete_project())
    pass
