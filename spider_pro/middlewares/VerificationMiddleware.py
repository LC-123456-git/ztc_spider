"""
@file          :VerificationMiddleware.py
@description   :验证码cookie设置
@date          :2021/05/28 08:54:45
@author        :miaokela
@version       :1.0
"""
import os
import requests
from PIL import Image
from pytesseract import *
from scrapy.downloadermiddlewares.retry import RetryMiddleware

class VerificationMiddleware(RetryMiddleware):

    def __init__(self, logger, **kwargs):
        super(VerificationMiddleware, self).__init__(kwargs)
        self.logger = logger
        self.url = 'http://www.ccgp-ningxia.gov.cn/public/NXGPPNEW/dynamic/contents/CGGG/index.jsp?cid=312&sid=1'
        self.URL = 'http://www.ccgp-ningxia.gov.cn/admin/AuthCode_too.do'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        self.retry_dict = kwargs.get("LOCAL_PROXY_RETRY_TIMES_DICT")
        self.need_add_dict = {
            'new_dict',
        }
        self.settings = kwargs

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        logger = crawler.spider.logger
        return cls(logger, **settings)

    def get_auth_code(self):
        img_content = requests.get(url=self.URL, headers=self.headers)
        img_path = os.path.join(self.settings.get('IMAGES_PATH'), 'images.jpeg')
        with open(img_path, 'wb') as fp:
            fp.write(img_content.content)
        img_code = image_to_string(Image.open(img_path), lang='eng', config='-psm 10').strip()
        return img_code

    def cookie_to_dic(self, response):
        new_dict = response.meta['new_dict'] | {'authCode': self.get_auth_code()}
        resp = requests.post(url=self.url, data=new_dict, headers=self.headers)
        cookie_dict = requests.utils.dict_from_cookiejar(resp.cookies)
        _cookies = 'JSESSIONID' + '=' + cookie_dict['JSESSIONID']
        return _cookies

    def process_response(self, request, response, spider):
        try:
            new_dict = response.meta['new_dict']
            respon = requests.post(url=response.url, data=new_dict, headers=response.headers)
            if respon.text == 'reload':
                request.headers = response.headers | {'cookie': self.cookie_to_dic(response)}
                # respon = self.process_response(request, response, spider)
            return self._retry(request, 'nima', spider) or response
        except Exception as e:
            return response

if __name__ == "__main__":
    pass
