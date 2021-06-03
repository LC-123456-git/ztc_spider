# @Time : 2021/5/26 9:03 
# @Author : miaokela
# @File : TYC_login.py 
# @Description: 天眼查登录
import os
import random
import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PHONE = '18868271201'
PASSWORD = 'laaimeng2011'
BORDER = 7


class CrackGeetest():
    def __init__(self):
        self.url = 'https://www.tianyancha.com/'
        self.browser = None
        self.account = PHONE
        self.password = PASSWORD
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.tyc_pic = os.path.join(os.path.join(self.path, 'images'), 'Tyc.png')
        self.captcha1 = os.path.join(os.path.join(self.path, 'images'), 'captcha1.png')
        self.captcha2 = os.path.join(os.path.join(self.path, 'images'), 'captcha2.png')

    def __del__(self):
        # self.browser.close()
        pass

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-infobars')
            # options.add_argument('--headless')
            options.add_argument(
                '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"')
            options.add_argument('--dns-prefetch-disable')
            options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
            options.add_argument('disable-infobars')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option('useAutomationExtension', False)
            self.browser = webdriver.Chrome(options=options)
            self.browser.get(self.url)
            self.browser.maximize_window()
            self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperties(navigator,{ webdriver:{ get: () => undefined } })"
            })
            t = random.uniform(0.5, 1)
            time.sleep(t)
            login_button = self.browser.find_element_by_xpath('//a[@onclick="header.loginLink(event)"]')
            login_button.click()
            time.sleep(2)
            pwd_button = self.browser.find_element_by_xpath('//div[@active-tab="1"]')
            pwd_button.click()
            time.sleep(1)
            self.browser.find_element_by_xpath('//input[@name="phone"]').send_keys(self.account)
            time.sleep(1)
            self.browser.find_element_by_xpath('//input[@name="password"]').send_keys(self.password)
            time.sleep(1)
            click_button = self.browser.find_element_by_xpath(
                '//div[@class="modal-dialog -login-box animated"]//div[@onclick="loginObj.loginByPhone(event);"]'
            )
            click_button.click()
            time.sleep(2)
        except Exception as e:
            print(e)

    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        """
        left = 60
        out_break = False
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    out_break = True
                    break
            if out_break: break
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60

        if all([abs(pixel1[0] - pixel2[0]) > threshold, abs(pixel1[1] - pixel2[1]) > threshold,
                abs(pixel1[2] - pixel2[2]) > threshold]):
            return False
        else:
            return True

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 1 / 10
        # 计算间隔
        t = 0.3
        # 初速度
        v = 1

        while current < distance:
            if current < mid:
                a = 10
            else:
                a = -1
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        track.extend([1.2, 2.3, -2.5, -1]) # 滑过去再滑过来，不然有可能被吃
        print('挪动距离边变动：{0}'.format(track))
        return track

    def move_to_gap(self, trace):
        t = random.uniform(0, 0.5)
        # 得到滑块标签
        slider = self.browser.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')
        # 使用click_and_hold()方法悬停在滑块上，perform()方法用于执行
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in trace:
            time.sleep(random.uniform(0, 0.3))
            # 使用move_by_offset()方法拖动滑块，perform()方法用于执行
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        # 模拟人类对准时间
        time.sleep(t)
        # 释放滑块
        ActionChains(self.browser).release().perform()

    def show_element(self, element):  # 让验证码图片迅速还原成完整图片
        self.browser.execute_script("arguments[0].style=arguments[1]", element, "display: block;")

    def hide_element(self, element):  # 暂不知用处
        self.browser.execute_script("arguments[0].style=arguments[1]", element, "display: none;")

    def get_images(self, img, name):
        # 截图整个网页
        self.browser.save_screenshot(self.tyc_pic)
        # 验证码路径
        location = img.location
        # 验证码尺寸
        size = img.size

        top = location['y']
        bottom = location['y'] + size['height'] - 30
        left = location['x']
        right = location['x'] + size['width']

        picture = Image.open(self.tyc_pic)
        picture = picture.crop((left, top, right, bottom))
        picture.save(os.path.join(os.path.join(self.path, 'images'), name))
        time.sleep(0.5)

    def get_image_location(self):
        fullbg = self.browser.find_element_by_xpath('//a[@class="gt_fullbg gt_show"]')
        self.hide_element(fullbg)
        self.show_element(fullbg)
        # 获取完整图片
        self.get_images(fullbg, 'captcha1.png')
        self.browser.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]').click()
        time.sleep(2)
        # 获取带缺口的图片
        bg = self.browser.find_element_by_xpath('//div[@class="gt_cut_fullbg gt_show"]')
        self.show_element(bg)
        self.get_images(bg, 'captcha2.png')

    def slice(self):
        success = True

        try:
            image2 = Image.open(self.captcha1)
            image1 = Image.open(self.captcha2)
            distance = self.get_gap(image1, image2)
            print('DISTANCE: ', distance)
            distance -= BORDER
            track = self.get_track(distance)
            self.move_to_gap(track)

            time.sleep(0.5)
            # time.sleep(200)
            pause_tag = False
            while True:
                for i in [x + 4 for x in range(10, 14)]:
                    mspan = self.browser.find_element_by_xpath('//div[@class="gt_info_text"]/span[2]').text
                    print(mspan)
                    if '拖动滑块' in mspan:
                        time.sleep(1)
                        distance = self.get_gap(image1, image2)
                        print('DISTANCE: ', distance)
                        trace = self.get_track(int(distance) - int(i))
                        # 移动滑块
                        self.move_to_gap(trace)
                        time.sleep(2)

                        # 获取登录后个人信息来判断是否登录
                        if not self.browser.find_element_by_xpath('//div[@id="_modal_container"]'):
                            print('获取的COOKIES: {}'.format(self.cookies))
                            pause_tag = True
                            break
                    else:
                        self.recrack()
                if pause_tag:
                    success = True
                    break
        except Exception as e:
            print(e)
            success = False
            self.recrack()
        return success

    @property
    def cookies(self):
        return self.browser.get_cookies()

    def recrack(self):
        self.browser.close()
        self.crack()

    def crack(self):
        self.open()
        self.get_image_location()
        success = self.slice()
        print(self.cookies)
        print(success)
        # if not success:  # 未完成 重新打开
        #     self.browser.close()
        #     self.crack()
        time.sleep(10)
        # print('本次获得的登录COOKIE: {0}'.format(self.cookies))


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
