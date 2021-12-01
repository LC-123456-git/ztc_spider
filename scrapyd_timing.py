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
    yesterday = get_back_date(3)
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
        "province_39_chongqing_spider",
        # "province_40_sichuan_spider",
        "province_41_guizhou_spider",
        "province_42_yunnan_spider",
        "province_44_xizang_spider",
        "province_45_shanxi_spider",
        # "province_49_ningxia_spider",
        "province_50_xinjiang_spider",
        "province_51_bingtuan_spider",
        "province_52_pinming_spider",
        "province_53_bilian_spider",
        "province_54_Egongxiang_spider",
        "province_55_tiangong_spider",
        "province_56_hebeijiantou_spider",
        "province_57_jingcaizongheng_spider",
        "province_59_xinzhi_spider",
        "province_62_xindian_spider",
        "province_65_guoepingtai_spider",
        "province_67_yangguangyizhao_spider",
        "province_68_qilu_spider",
        "province_71_zhaocaijingbao_spider",
        "province_77_zhaobide_spider",
        "province_78_zhuzhaixiushan_spider",
        "province_79_xinEcai_spider",
        "province_80_yankuangzhaocai_spider",
        "province_82_bide_spider",
        "province_83_wangcai_spider",
        "province_85_anzhuangxinxi_spider",
        "province_3101_shanghaigov_spider",
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
        "ZJ_city_3316_zhuji_spider",
        "ZJ_city_3318_jinhua_spider",
        "ZJ_city_3319_changxing_spider",
        "ZJ_city_3320_cangnan_spider",
        "ZJ_city_3321_linhai_spider",
        "ZJ_city_3322_anji_spider",
        "ZJ_city_3323_xiaoshan_spider",
        "ZJ_city_3324_nanxun_spider",
        "ZJ_city_3325_deqing_spider",
        "ZJ_city_3326_longyou_spider",
        "ZJ_city_3328_changshan_spider",
        "ZJ_city_3331_fuyang_spider",
        "ZJ_city_3332_chunan_spider",
        "ZJ_city_3334_jiande_spider",
        "ZJ_city_3335_wzlucheng_spider",
        "ZJ_city_3336_yueqing_spider",
        "ZJ_city_3337_ruian_spider",
        "ZJ_city_3338_yongjia_spider",
        "ZJ_city_3339_dongtou_spider",
        "ZJ_city_3340_wencheng_spider",
        "ZJ_city_3341_taishun_spider",
        "ZJ_city_3342_shangyu_spider",
        "ZJ_city_3343_xinchang_spider",
        "ZJ_city_3344_yuecheng_spider",
        "ZJ_city_3345_shengzhou_spider",
        "ZJ_city_3346_huzhouwuxing_spider",
        "ZJ_city_3347_wenling_spider",
        "ZJ_city_3348_sanmenxian_spider",
        "ZJ_city_3351_wucheng_spider",
        "ZJ_city_3353_lanxi_spider",
        "ZJ_city_3355_yongkang_spider",
        "ZJ_city_3356_jinhuayiwu_spider",
        "ZJ_city_3360_wuyi_spider",
        "ZJ_city_3361_jinhuapujiang_spider",
        "ZJ_city_3362_jinhuapanan_spider",
        "qcc_crawler",
        # "province_117_hebei_spider",
        "province_118_henan_spider",
        "province_119_hubei_spider",
        "province_120_hunan_spider",
        "province_121_shanxi_spider",
        "province_122_shandong_spider",
        "province_123_heilongjiang_spider",
        "province_124_jilin_spider",
        # "province_125_liaoning_spider",
        "province_126_hainan_spider",
        "province_127_neimenggu_spider",
        "province_128_guangdong_spider",
        "province_129_shanxi_spider",
        # "province_130_gansu_spider",
        "province_131_qinghai_spider",
        "province_132_nianxia_spider",
        "province_133_jiangxi_spider",
        "province_141_anhui_spider",
        "province_143_dalian_spider",
        "province_145_qingdao_spider",
        "province_146_bingtuan_spider",
        "province_148_zhongguoty_spider",
        "province_149_zhongzhaolian_spider",
        "province_150_jizhaobiao_spider",
        "province_151_zhonggangzb_spider",
        "province_152_zhongmeiyg_spider",
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
                area_id = item.split("_")[2] if item.split("_")[1] == 'city' else item.split("_")[1]
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
                resp = exec_each_schedule(item, area_id, arg_choices=arg_choices, if_incr=if_incr, **info)

                if resp:
                    print('运行{0}成功!'.format(item))
