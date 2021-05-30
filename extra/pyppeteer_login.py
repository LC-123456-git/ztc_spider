# @Time : 2021/5/29 23:18 
# @Author : miaokela
# @File : pyppeteer_login.py 
# @Description: 天眼查登录
import asyncio
import random
import tkinter
from PIL import Image
from pyppeteer import launch

BORDER = 0


async def main():
    browser = await launch({
        # 控制是否为无头模式
        "headless": False,
        # chrome启动命令行参数
        "args": [
            # 浏览器代理 配合某些中间人代理使用
            # "--proxy-server=http://127.0.0.1:8008",
            # 最大化窗口
            "--start-maximized",
            # 取消沙盒模式 沙盒模式下权限太小
            "--no-sandbox",
            # 不显示信息栏  比如 chrome正在受到自动测试软件的控制 ...
            "--disable-infobars",
            # log等级设置 在某些不是那么完整的系统里 如果使用默认的日志等级 可能会出现一大堆的warning信息
            "--log-level=3",
            # 设置UA
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        ],
        "dumpio": True,
        # 当界面开多了时会卡住，设置这个参数就不会了
        # 用户数据保存目录 这个最好也自己指定一个目录
        # 如果不指定的话，chrome会自动新建一个临时目录使用，在浏览器退出的时候会自动删除临时目录
        # 在删除的时候可能会删除失败（不知道为什么会出现权限问题，我用的windows） 导致浏览器退出失败
        # 然后chrome进程就会一直没有退出 CPU就会狂飙到99%
        "userDataDir": "",
    })
    page = await browser.newPage()
    await page.evaluate(
        '() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }'
    )
    # await page.evaluate(
    #     '() =>{ window.navigator.chrome = { runtime: {}, }; }'
    # )
    # await page.evaluate(
    #     "() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }"
    # )
    # await page.evaluate(
    #     "() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }"
    # )
    tk = tkinter.Tk()
    width = tk.winfo_screenwidth()
    height = tk.winfo_screenheight()
    tk.quit()
    await page.goto(url='https://www.tianyancha.com/')
    await page.setViewport(viewport={'width': width, 'height': height})

    await asyncio.sleep(2)

    # SELECT CLICK
    right_login = await page.xpath('//a[@onclick="header.loginLink(event)"]')
    await right_login[0].click()

    await asyncio.sleep(1)

    # SELECT LOGIN
    tab_login = await page.xpath('//div[@active-tab="1"]')
    await tab_login[0].click()

    await asyncio.sleep(1)

    # INPUT CREDIT
    username = await page.xpath('//input[@name="phone"]')
    await username[0].type('18868271201')

    username = await page.xpath('//input[@name="password"]')
    await username[0].type('laaimeng2011')

    # SUBMIT
    submit = await page.xpath(
        '//div[@class="modal-dialog -login-box animated"]//div[@onclick="loginObj.loginByPhone(event);"]')
    await submit[0].click()

    await asyncio.sleep(1)

    # SHOW FULL PIC
    full_pic = await page.waitForXPath('//a[@class="gt_fullbg gt_show"]')
    full_pic_box = await full_pic.boundingBox()
    await full_pic.screenshot({
        'path': 'captcha1.png',
        'clip': {
            'x': full_pic_box['x'],
            'y': full_pic_box['y'],
            'width': full_pic_box['width'],
            'height': full_pic_box['height'] - 20,
        }
    })

    # SHOW MISSING BLOCK
    missing_block = await page.xpath('//div[@class="gt_slider_knob gt_show"]')
    await missing_block[0].click()

    missing_block_pic = await page.waitForXPath('//div[@class="gt_cut_fullbg gt_show"]')
    missing_block_pic_box = await missing_block_pic.boundingBox()

    await missing_block_pic.screenshot({
        'path': 'captcha2.png',
        'clip': {
            'x': missing_block_pic_box['x'],
            'y': missing_block_pic_box['y'],
            'width': missing_block_pic_box['width'],
            'height': missing_block_pic_box['height'] - 20,
        }
    })

    await asyncio.sleep(2)
    # GET DISTANCE
    image1 = Image.open('./captcha1.png')
    image2 = Image.open('./captcha2.png')

    distance = get_gap(image2, image1)
    # distance += 15
    print(distance)
    # GET TRACK
    track = get_track(distance)
    # MOVE TO GAP
    t = random.uniform(0, 0.5)

    slider = await page.waitForXPath('//div[@class="gt_slider_knob gt_show"]')
    slider_info = await slider.boundingBox()
    mouse = page.mouse

    await mouse.down()
    c_x, c_y = slider_info['x'], slider_info['y']
    for x in track:
        if x:
            await asyncio.sleep(random.uniform(0, 0.2))
            c_x += x
            await mouse.move(c_x, c_y)

    await asyncio.sleep(t)

    await page.mouse.up()
    await asyncio.sleep(2)
    await page.screenshot({'path': 'tyc.png'})

    await browser.close()


def get_gap(image1, image2):
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
            if not is_pixel_equal(image1, image2, i, j):
                left = i
                out_break = True
                break
        if out_break: break
    return left


def is_pixel_equal(image1, image2, x, y):
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


def get_track(distance):
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
    mid = distance * 2 / 5
    # 计算间隔
    t = 0.3
    # 初速度
    v = 1

    while current < distance:
        if current < mid:
            a = 5
        else:
            a = -2
        v0 = v
        v = v0 + a * t
        move = v0 * t + 1 / 2 * a * t * t
        current += move
        track.append(round(move))
    track.extend([1.2, 2.3, -2.5, -1])  # 滑过去再滑过来，不然有可能被吃
    print('挪动距离边变动：{0}'.format(track))
    return track


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
