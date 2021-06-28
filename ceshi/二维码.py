import qrcode

data = 'C:/Users/PC12/Documents/WeChat%20Files/wxid_m6dl632p6n522/FileStorage/File/2021-05/%E8%89%BE%E9%A3%9E%E8%99%8E.pdf'
img_file = r'保存路径.jpg'

# 实例化QRCode生成qr对象
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4
)
# 传入数据
qr.add_data(data)

qr.make(fit=True)

# 生成二维码
img = qr.make_image()

# 保存二维码
img.save(img_file)













