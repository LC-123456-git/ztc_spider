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
import re

class VerificationMiddleware(RetryMiddleware):

    def __init__(self, kwargs, logger):
        super(VerificationMiddleware, self).__init__(kwargs)
        self.logger = logger
        self.url = 'http://www.ccgp-ningxia.gov.cn/public/NXGPPNEW/dynamic/contents/CGGG/index.jsp?cid=312&sid=1'
        self.URL = 'http://www.ccgp-ningxia.gov.cn/admin/AuthCode_too.do'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        self.settings = kwargs
        self.tag = 0

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        logger = crawler.spider.logger
        return cls(settings, logger)

    def get_auth_code(self):
        img_content = requests.get(url=self.URL, headers=self.headers)
        img_path = os.path.join(self.settings.get('IMAGES_PATH'), 'images.jpeg')
        with open(img_path, 'wb') as fp:
            fp.write(img_content.content)
        img = Image.open(img_path)
        txt = pytesseract.image_to_string(img)
        txt = ''.join(txt.split(' '))
        com = re.compile(r'(\d+)')
        img_code = com.findall(txt)
        return img_code

    def cookie_to_dic(self, request):
        new_dict = request.meta['new_dict'] | {'authCode': self.get_auth_code()}
        resp = requests.post(url=self.url, data=new_dict, headers=self.headers)
        # cookie_dict = requests.utils.dict_from_cookiejar(resp.cookies)
        cookie_dict = resp.cookies.get_dict()
        return cookie_dict

    def process_response(self, request, response, spider):
        try:
            if response.text == 'reload':
                self.tag += 1
                if self.tag < 2:
                    request.cookies = self.cookie_to_dic(request)
                return self._retry(request, request.meta['new_dict'], spider)
            return response
        except Exception as e:
            return response

if __name__ == "__main__":
    pass
