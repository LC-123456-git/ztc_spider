"""
@file           :maintain_proxy_pool.py
@description    :维护代理池
@date           :2021/06/15 21:30:53
@author         :miaokela
@version        :1.0
"""
from redis.exceptions import WatchError
import redis
import requests
import json
import datetime
import time
import re


NAME_HTTP_PROXY = "http_proxy"  # redis http代理池
NAME_HTTPS_PROXY = "https_proxy"  # redis https代理池
NAME_HTTP_USED_PROXY = "used:http_proxy"  # 已使用的代理池
NAME_HTTPS_USED_PROXY = "used:https_proxy"  # 已使用的代理池
NAME_RETRY_TIMES = "retry_times"  # 代理重试池
CURRENT_HTTP_PROXY_MAX = 10  # redis http 最大数量
CURRENT_HTTPS_PROXY_MAX = 10  # redis https 最大数量


class ProxyPool:

    def __init__(self, **kwargs):
        self.redis_pool = redis.ConnectionPool(
            host=kwargs.get("REDIS_HOST"), 
            port=8090,
            decode_responses=True, 
            max_connections=int(kwargs.get("MAX_CONNECTIONS")),
            password=kwargs.get("REDIS_PASSWORD"), 
            retry_on_timeout=True
        )
        self.redis_client = redis.StrictRedis(connection_pool=self.redis_pool, port=8090)

    @staticmethod
    def get_local_network_ip():
        ret = requests.get('https://ip.cn/api/index?ip=&type=0').content.decode('utf-8')
        ip = ''
        try:
            ip_info = json.loads(ret)
            ip = ip_info.get('ip', '')
        except Exception as e:
            pass
        return ip

    @staticmethod
    def add_while_list(ip):
        """
        :param ip: 本机外网ip
        :return:
        """
        requests.get(
            f'http://wapi.http.linkudp.com/index/index/save_white?neek=271627&appkey=1128c20479f5c3ce9d81a034693b03b4&white={ip}')


    def get_proxy_ip(self, _type: int, retry_times: int, /, num: int = 1, yys: int = 100017, port: int = 1,
                     _time: int = 1,
                     data_type: int = 2, mr: int = 1, ts: int = 1):
        """
        :param _type: 类型 1 直连、2 独享 3、隧道
        :param retry_times: 当前请求次数
        :param num: 提取IP数量
        :param yys: 0:不限 100026:联通 100017:电信
        :param port: IP协议 1:HTTP 2:SOCK5 11:HTTPS
        :param _time: 稳定时长 1:5-25min 2:25min-3h 3:3-6h 4:6-12h 7:48-72h
        :param data_type: 数据格式：1:TXT 2:JSON 3:html
        :param mr: 去重选择（1:360天去重 2:单日去重 3:不去重）
        :param ts: 1 显示过期时间 0 不显示
        :return:
        """
        self.logger.info('正在获取新的IP...')
        if retry_times >= 3:
            self.logger.error(f"获取代理失败 重试次数超出: {_type=} {port=} {num=} {yys=} {_time=} {data_type=} {mr=}")
            return False
        else:
            retry_times += 1
        if _type == 1:
            # 套餐
            r = requests.get(url=f"http://webapi.http.zhimacangku.com/getip?num={num}&type={data_type}&pro=&city=0&yys={yys}&port={port}&pack=143415&ts={ts}&ys=0&cs=0&lb=1&sb=0&pb=4&mr={mr}&regions="
                             )
            # 单次
            # r = requests.get(
            #     url=f"http://webapi.http.zhimacangku.com/getip?num={num}&type={data_type}&pro=&city=0&yys={yys}&port={port}&time={_time}&ts={ts}&ys=0&cs=0&lb=1&sb=0&pb=4&mr={mr}&regions="
            # )
        elif _type == 2:
            r = requests.get(
                url=f"http://http.tiqu.letecs.com/getip3?num={num}&type={data_type}&pro=&city=0&yys={yys}&port={port}&time={_time}&ts={ts}&ys=0&cs=0&lb=1&sb=0&pb=4&mr={mr}&regions="
            )
        elif _type == 3:
            r = requests.get(
                url=f"http://http.tiqu.letecs.com/getip3?num={num}&type={data_type}&pro=&city=0&yys={yys}&port={port}&time={_time}&ts={ts}&ys=0&cs=0&lb=1&sb=0&pb=4&mr={mr}&regions="
            )
        else:
            self.logger.error(f"获取http代理失败： 参数异常 {_type=}")
            return False
        if r.status_code == 200:
            r_dict = json.loads(r.text)
            if r_dict.get("code") in [0, "0"]:
                if port == 1:
                    self.logger.info(f"获取http代理成功: {num=} {r_dict.get('data')=} {port=}")
                    t_list = []
                    for item in r_dict.get("data"):
                        t_list.append({
                            "proxy": f'http://{item.get("ip")}:{item.get("port")}',
                            "time": int((datetime.datetime.fromisoformat(
                                item.get("expire_time")) - datetime.datetime.now()).total_seconds())
                        })
                    return t_list
                else:
                    self.logger.info(f"获取https代理成功: {num=} {r_dict.get('data')=} {port=}")
                    t_list = []
                    for item in r_dict.get("data"):
                        t_list.append({
                            "proxy": f'https://{item.get("ip")}:{item.get("port")}',
                            "time": int((datetime.datetime.fromisoformat(
                                item.get("expire_time")) - datetime.datetime.now()).total_seconds())
                        })
                    return t_list
            elif r_dict.get("code") in [113, "113"]:
                if ip_group := re.search(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", r_dict.get("msg")):
                    ip = ip_group.group(0)
                else:
                    ip = ProxyPool.get_local_network_ip()
                ProxyPool.add_while_list(ip)
                time.sleep(1)
                return self.get_proxy_ip(1, retry_times)
            elif r_dict.get("code") in [111, "111"]:
                time.sleep(1)
                return self.get_proxy_ip(1, retry_times)
            elif r_dict.get("code") in [114, "114"]:
                self.logger.error(f"获取代理失败： code={r_dict.get('code')} {r_dict.get('msg')}")
            else:
                self.logger.error(
                    f"获取代理失败 : code={r_dict.get('code')} {_type=} {port=} {num=} {yys=} {_time=} {data_type=} {mr=}")
                return False
        self.logger.error(f"获取代理失败 : {r.status_code=} {_type=} {port=} {num=} {yys=} {_time=} {data_type=} {mr=}")
        return False


    def maintain_proxy_pool(self):
        while True:
            for name_proxy in [NAME_HTTP_PROXY, NAME_HTTPS_PROXY]:
                
                max_num = CURRENT_HTTP_PROXY_MAX if name_proxy == NAME_HTTP_PROXY else CURRENT_HTTPS_PROXY_MAX
                port = 1 if name_proxy == NAME_HTTP_PROXY else 11
                num_redis = self.redis_client.scard(name_proxy)
                if num_redis < max_num:
                    temp_data = self.get_proxy_ip(1, 1, num=max_num - num_redis, port=port)
                    if not temp_data:
                        self.logger.error(f"尝试更新{name_proxy} ip池失败: 未获取到新的ip")
                        continue
                    else:
                        self.logger.info(f"开始尝试更新{name_proxy} ip池: {temp_data}")
                    proxy_list = [item.get("proxy") for item in temp_data]
                    with self.redis_client.pipeline() as pipe:
                        while True:
                            try:
                                pipe.watch(name_proxy)
                                num_redis = self.redis_client.scard(name_proxy)
                                if num_redis < max_num:
                                    pipe.multi()
                                    pipe.sadd(name_proxy, *proxy_list[:(max_num - num_redis)])
                                    for item in temp_data[:(max_num - num_redis)]:
                                        pipe.setex(item.get("proxy"), item.get("time"), item.get("time"))
                                    r_exec = pipe.execute()
                                    self.logger.info(
                                        f"更新{name_proxy} ip池成功: 数量{max_num - num_redis} {temp_data[:(max_num - num_redis)]} {r_exec=}")
                                    break
                                else:
                                    break
                            except WatchError as e:
                                pipe.unwatch()
                            except Exception as e:
                                pipe.unwatch()
                            finally:
                                pass

            proxy_list = self.redis_client.smembers(self.name_http_proxy)
            for item in proxy_list:
                if not self.redis_client.exists(item) or not item.startswith("http://"):
                    self.redis_client.srem(self.name_http_proxy, item)
                    self.redis_client.sadd(self.name_http_used_proxy, item)

            proxy_list = self.redis_client.smembers(self.name_https_proxy)
            for item in proxy_list:
                if not self.redis_client.exists(item) or not item.startswith("https://"):
                    self.redis_client.srem(self.name_https_proxy, item)
                    self.redis_client.sadd(self.name_https_used_proxy, item)









