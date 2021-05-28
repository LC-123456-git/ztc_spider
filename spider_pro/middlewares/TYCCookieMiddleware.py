"""
@file          :TYCCookieMiddleware.py
@description   :天眼查cookie设置
@date          :2021/05/28 08:54:45
@author        :miaokela
@version       :1.0
"""


class TYCCookieMiddleware(object):

    def __init__(self, logger, **kwargs):
        super(TYCCookieMiddleware, self).__init__()
        self.logger = logger
        self.need_add_cookie = {
            'tyc_crawler',
        }
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        logger = crawler.spider.logger
        return cls(logger, **settings)

    @staticmethod
    def cookie_to_dic(cookie):
        return {i.split('=')[0].strip():i.split('=')[1].strip() for i in cookie.split('; ')}

    def process_request(self, request, spider):
        if spider.name in self.need_add_cookie :
            default_cookie = """
            ssuid=5810947917; TYCID=c8bb9b30afbd11eb8beb8fabe54a0d9c; undefined=c8bb9b30afbd11eb8beb8fabe54a0d9c; _ga=GA1.2.1041886134.1620451522; creditGuide=1; tyc-user-phone=%255B%252218868271201%2522%255D; bad_id658cce70-d9dc-11e9-96c6-833900356dc6=fedcd011-baf5-11eb-ad34-11b84dc1127f; jsid=https%3A%2F%2Fwww.tianyancha.com%2F%3Fjsid%3DSEM-BAIDU-PZ-SY-2021112-BIAOTI; _gid=GA1.2.1184650736.1621903665; bdHomeCount=17; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218868271201%22%2C%22first_id%22%3A%221794a6ff4c14db-02ebe045497c34-5771031-2073600-1794a6ff4c2d78%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%221794a6ff4c14db-02ebe045497c34-5771031-2073600-1794a6ff4c2d78%22%7D; aliyungf_tc=690bb05f928467412403ff4114f27a56643a1a9a010b20bbe84b7c44dfb4fab6; csrfToken=9dGIUFChzbU40SRh7Im9vBr1; bannerFlag=true; Hm_lvt_e92c8d65d92d534b0fc290df538b4758=1622017316,1622095354,1622096870,1622163676; CT_TYCID=94d01eed41e947cbba7b082a52c470b5; RTYCID=cfece106922b40069a0f56fd10b49c9a; acw_tc=781bad3e16221654946256849e2369617f344290c8b8211fc544b07b75ec98; searchSessionId=1622165507.53122274; relatedHumanSearchGraphId=23537076; relatedHumanSearchGraphId.sig=L3thJnpAakH_ZNreufxHTL5v-cvUlzGmcMgYBpYEOj4; auth_token=eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxODg2ODI3MTIwMSIsImlhdCI6MTYyMjE2Njg2NCwiZXhwIjoxNjUzNzAyODY0fQ.ZOD1e2BdP1Hps8SGnf3JKgUf_6CW4z3HSr3hQ0tIZIaEG6X_rYyF5cAzQaq0YXWmEzPPPVwWw0PiwQQj5e0FQg; tyc-user-info={%22state%22:%220%22%2C%22vipManager%22:%220%22%2C%22mobile%22:%2218868271201%22}; tyc-user-info-save-time=1622166864621; Hm_lpvt_e92c8d65d92d534b0fc290df538b4758=1622166916; _gat_gtag_UA_123487620_1=1; cloud_token=e4e86c6afca6498dbe56ac2ff23db4d6; cloud_utm=61c90296d77b4071a2e1bbf4e68630f8
            """
            cookie = TYCCookieMiddleware.cookie_to_dic(default_cookie)

            # self.logger.info('CURRENT COOKIE: {0}'.format(cookie))
            request.cookies = cookie


if __name__ == "__main__":
    pass

