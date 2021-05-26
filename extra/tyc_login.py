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
BORDER = 6

class CrackGeetest():
    def __init__(self):
        self.url = 'https://www.tianyancha.com/'
        self.browser = None
        self.wait = None
        self.account = PHONE
        self.password = PASSWORD
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.tyc_pic = os.path.join(os.path.join(self.path, 'images'), 'Tyc.png')

    def __del__(self):
        self.browser.close()

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_img')))
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return (top, bottom, left, right)

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
            self.browser = webdriver.Chrome()
            self.wait = WebDriverWait(self.browser, 20)
            self.browser.get(self.url)
            self.browser.maximize_window()
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
        left = 53
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    return i
        return left + 47

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

        if abs(pixel1[0] - pixel2[0]) > threshold and abs(pixel1[1] - pixel2[1]) > threshold and abs(
                pixel1[2] - pixel2[2]) > threshold:
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
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        track += [2, -2]
        return track

    def move_to_gap(self, trace):
        t = random.uniform(0, 0.5)
        # 得到滑块标签
        slider = self.browser.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')
        # 使用click_and_hold()方法悬停在滑块上，perform()方法用于执行
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in trace:
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

        # top, bottom, left, right = location['y']+3, location['y'] + size['height'], location['x']-325, location['x'] + size['width']-328
        # 加入代码self.driver.maximize_window()使浏览器全屏后就不需要修改位置参数了,mac上不知道什么原因需要修改位置
        top, bottom, left, right = location['y'], location['y'] + size['height'] - 20, location['x'], location['x'] + \
                                   size['width']
        picture = Image.open(self.tyc_pic)
        picture = picture.crop((left, top, right, bottom))
        picture.save(os.path.join(os.path.join(self.path, 'images'), name))
        time.sleep(0.5)

    def get_image_location(self):
        # 获取验证码图片路径--->调用get_images截取图片
        fullbg = self.browser.find_element_by_xpath('//a[@class="gt_fullbg gt_show"]')
        self.hide_element(fullbg)
        self.show_element(fullbg)
        # 获取完整图片
        self.get_images(fullbg, 'captcha1.png')
        # 点击一下滑动按钮触发出来带缺口的图片
        self.browser.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]').click()
        time.sleep(2)
        # 获取带缺口的图片
        bg = self.browser.find_element_by_xpath('//div[@class="gt_cut_fullbg gt_show"]')
        self.show_element(bg)
        self.get_images(bg, 'captcha2.png')

    def slice(self):
        success = True

        try:
            image2 = Image.open(os.path.join(os.path.join(self.path, 'images'), 'captcha2.png'))
            image1 = Image.open(os.path.join(os.path.join(self.path, 'images'), 'captcha1.png'))
            # 获取缺口位置
            gap = self.get_gap(image1, image2)
            print('缺口位置', gap)
            # 减去缺口位移
            gap -= BORDER
            # 获取移动轨迹
            track = self.get_track(gap)
            # print('滑动轨迹', track)
            # 拖动滑块
            self.move_to_gap(track)
            time.sleep(0.5)
            while True:
                for i in [x+2 for x in range(8, 9)]:  # 再次滑动2次,距离缩短
                    try:
                        mspan = self.browser.find_element_by_xpath('//div[@class="gt_info_text"]/span[2]').text
                        print(mspan)
                        if '拖动滑块' in mspan:
                            time.sleep(1)
                            distance = self.get_gap(image1, image2)
                            print('计算偏移量为：%s Px' % distance)
                            trace = self.get_track(int(distance) - int(i))
                            print('减值%s' % i)
                            print(trace)
                            # 移动滑块
                            self.move_to_gap(trace)
                            time.sleep(0.5)
                        else:  # 请关闭验证重试
                            if '怪物' in mspan:
                                time.sleep(5)
                                self.get_image_location()
                                self.slice()
                            else:
                                break
                    except Exception as e:
                        if '//div[@class="gt_info_text"]/span[2]' in str(e):
                            pass
                        else:
                            print(e)
                success = False
                break
        except Exception as e:
            success = False
            if '//span[@class="gt_info_content"]' in str(e):
                pass
            else:
                print(e)
        return success

    @property
    def cookies(self):
        return self.browser.get_cookies()

    def crack(self):
        self.open()
        self.get_image_location()
        success = self.slice()
        if not success:  # 未完成 重新打开
            self.browser.close()
            self.crack()
        print('本次获得的登录COOKIE: {0}'.format(self.cookies))

if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
