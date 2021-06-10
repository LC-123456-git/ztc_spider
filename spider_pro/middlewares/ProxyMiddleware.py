#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwj
# @Date: 2020-12-21
# @Describe: ip代理中间件
import datetime
import re
import redis
import threading
import json
import time
import requests
from redis.exceptions import WatchError
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest
from spider_pro import constans as const
from lxml import etree


class ProxyMiddleware(RetryMiddleware):

    def __init__(self, kwargs, logger):
        super(ProxyMiddleware, self).__init__(kwargs)
        self.logger = logger
        self.redis_pool = redis.ConnectionPool(
            host=kwargs.get("REDIS_HOST"), port=8090,decode_responses=True, max_connections=int(kwargs.get("MAX_CONNECTIONS")),
            password=kwargs.get("REDIS_PASSWORD"), retry_on_timeout=True)
        self.redis_client = redis.StrictRedis(connection_pool=self.redis_pool, port=8090)
        self.max_http = int(kwargs.get("CURRENT_HTTP_PROXY_MAX"))
        self.max_https = int(kwargs.get("CURRENT_HTTPS_PROXY_MAX"))
        self.time_wait = kwargs.get("TIME_WAIT_PROXY_SLEEP")
        self.time_thread = kwargs.get("TIME_MAINTAIN_PROXY_POOL_AGAIN")
        self.time_exit = kwargs.get("TIME_EXIT_WHEN_LOCAL_PROXY_SET_EMPTY")
        self.retry_dict = kwargs.get("LOCAL_PROXY_RETRY_TIMES_DICT")
        self.retry_times = kwargs.get("LOCAL_PROXY_RETRY_MAX_TIMES")
        self.name_http_proxy = kwargs.get("NAME_HTTP_PROXY")
        self.name_https_proxy = kwargs.get("NAME_HTTPS_PROXY")
        self.name_http_abandon_proxy = kwargs.get("NAME_HTTP_ABANDON_PROXY")
        self.name_https_abandon_proxy = kwargs.get("NAME_HTTPS_ABANDON_PROXY")
        self.name_http_used_proxy = kwargs.get("NAME_HTTP_USED_PROXY")
        self.name_https_used_proxy = kwargs.get("NAME_HTTPS_USED_PROXY")
        self.name_retry_times = kwargs.get("NAME_RETRY_TIMES")

        self.name_delay_request = kwargs.get("NAME_DELAY_REQUEST")

        self.enable_proxy_infinite = True if kwargs.get("ENABLE_PROXY_INFINITE") in const.TRUE_LIST else False
        self.enable_proxy_use = True if kwargs.get("ENABLE_PROXY_USE") in const.TRUE_LIST else False

        if self.enable_proxy_use:
            self.maintain_proxy_thread = threading.Thread(target=self.maintain_proxy_pool)
            self.maintain_proxy_thread.setDaemon(True)
            self.maintain_proxy_thread.start()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        logger = crawler.spider.logger
        return cls(settings, logger)

    def process_request(self, request, spider):
        if self.enable_proxy_use:
            if request.url.startswith("http://"):
                request.meta['proxy'] = self.get_redis_proxy_ip(self.name_http_proxy, spider)
            else:
                request.meta['proxy'] = self.get_redis_proxy_ip(self.name_https_proxy, spider)

            request.meta['download_slot'] = request.meta['proxy']
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(f"{request.meta.get('channelId')} time={time.time()} r_times={request.meta.get('retry_times', 0)} {request.meta.get(self.name_delay_request, None)}")

    def process_response(self, request, response, spider):
        """
        :param request:  request
        :param response: response
        :param spider: spider
        :return: response
        """
        retry_times = request.meta.get('retry_times', 0)
        if response.status == 200:
            if spider.name == 'qcc_crawler':
                if '<script>window.location.href=' in response.text:
                    self.logger.info('请求响应异常, retry:{0}'.format(retry_times))
                    if retry_times >= self.max_retry_times:
                        self.process_exception(request, Exception('超过重试次数.'), spider)

                    reason = Exception('请求响应异常.')
                    
                    return self._retry(request, reason, spider) or response
            return response
        else:
            reason = response_status_message(response.status)
            if retry_times >= self.max_retry_times:
                self.logger.error(
                    f"抓取失败 重试次数用完: {request.url=} {spider.area_id=} {reason=}")
                return response
            elif response.status == 404:
                return self._retry(request, reason, spider) or response
                # self.logger.error(f"被重定向到404页面了 {request.url=} {spider.area_id=} {reason=}")
            else:
                request.meta[self.name_delay_request] = True
                return self._retry(request, reason, spider) or response

    def process_exception(self, request, exception, spider):
        """
        :param request: request
        :param exception: exception
        :param spider: spider
        :return: response
        """
        if isinstance(exception, IgnoreRequest):
            return
        if request.meta.get('retry_times', 0) >= self.max_retry_times:
            if not self.enable_proxy_infinite and self.enable_proxy_use:
                self.logger.info('移除代理:{0}'.format(request.meta.get("proxy")))
                self.delete_redis_ip_from(request.meta.get("proxy"))
            self.logger.error(
                f"捕获失败 重试次数用完: {request.url=} {spider.area_id=} {exception=}")
        elif isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            # current_retry_times = request.meta.get('retry_times', 0) + 2
            # request.meta["download_timeout"] = current_retry_times * 15
            return self._retry(request, exception, spider)
        else:
            self.logger.error(
                f"捕获失败 非重试异常: {request.url=} {spider.area_id=} {exception=}")

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
                    ip = ProxyMiddleware.get_local_network_ip()
                ProxyMiddleware.add_while_list(ip)
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

    def get_redis_proxy_ip(self, name_proxy, spider):
        # return "http://220.165.42.99:4260"
        # return "http://182.38.125.145:4213"  # 测试用无效代理 勿删
        start_time = time.time()
        while True:
            r_set = self.redis_client.srandmember(name_proxy, 1)
            if not r_set:
                time.sleep(self.time_wait)
                if time.time() - start_time > self.time_exit:
                    self.logger.error(f"退出脚本 :超时未获得新的{name_proxy=}")
                    spider.crawler.engine.close_spider(spider, "超时等待ip池")
                    return False
                continue
            if name_proxy == self.name_http_proxy and r_set[0].startswith("http://"):
                return r_set[0]  # TODO 需要策略
            elif name_proxy == self.name_https_proxy and r_set[0].startswith("https://"):
                return r_set[0]  # TODO 需要策略

    def delete_redis_ip_from(self, item):
        if item:
            if item.startswith("http://"):
                self.redis_client.srem(self.name_http_proxy, item)
                self.redis_client.sadd(self.name_http_used_proxy, item)
            else:
                self.redis_client.srem(self.name_https_proxy, item)
                self.redis_client.sadd(self.name_https_used_proxy, item)

    def maintain_proxy_pool(self):
        while True:
            # 更新redis ip池
            for name_proxy in [self.name_http_proxy, self.name_https_proxy]:
                max_num = self.max_http if name_proxy == self.name_http_proxy else self.max_https
                port = 1 if name_proxy == self.name_http_proxy else 11
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

            # for name_proxy in [self.name_http_proxy, self.name_https_proxy]:
            #     proxy_list = self.redis_client.smembers(name_proxy)
            #     for item in proxy_list:
            #         if not self.redis_client.exists(item):
            #             if item.startswith("http://"):
            #                 self.redis_client.srem(self.name_http_proxy, item)
            #                 self.redis_client.sadd(self.name_http_used_proxy, item)
            #             else:
            #                 self.redis_client.srem(self.name_https_proxy, item)
            #                 self.redis_client.sadd(self.name_https_used_proxy, item)

            time.sleep(10)


if __name__ == "__main__":
    # REDIS_HOST = "114.67.84.76"
    # MAX_CONNECTIONS = 1
    # REDIS_PASSWORD = "Ly3sa%@D0$pJt0y6."
    # redis_pool = redis.ConnectionPool(
    #     host=REDIS_HOST, password=REDIS_PASSWORD, decode_responses=True, max_connections=MAX_CONNECTIONS)
    # redis_client = redis.StrictRedis(connection_pool=redis_pool)
    # # print(redis_client.keys(fr"dwd"))
    # print(redis_client.scard("used:http_proxy"))
    #
    # # redis_client.flushall()  # !!!!

    # ip = ProxyMiddleware.get_local_network_ip()
    # ProxyMiddleware.add_while_list(ip)

    pass
