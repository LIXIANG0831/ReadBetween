import numpy as np
import os
import cv2
from paddleocr import PPStructure, save_structure_res
from paddle.utils import try_import
from PIL import Image
"""
# 安装PaddlePaddle
## https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/install

# 安装PaddleOCR
## 安装 PaddleOCR
pip3 install "paddleocr>=2.6.0.3"
## 安装 PaddleOCR-图像方向分类
pip3 install paddleclas>=2.4.3

"""

# 初始化OCR引擎，设置为不检测表格，仅进行文本识别，并显示日志
ocr_engine = PPStructure(table=False, ocr=True, show_log=True)

# 设置输出结果保存的文件夹
save_folder = '/Users/lixiang/Desktop/output'
# 指定要处理的PDF文件路径
img_path = '/Users/lixiang/Documents/Test_Material/普通.pdf'

# 尝试导入fitz模块用于PDF处理
fitz = try_import("fitz")
imgs = []  # 用于存储处理后的图像列表

# 打开PDF文件
with fitz.open(img_path) as pdf:
    # 遍历PDF中的每一页
    for pg in range(0, pdf.page_count):
        page = pdf[pg]
        # 创建一个变换矩阵，将图像放大2倍
        mat = fitz.Matrix(2, 2)
        pm = page.get_pixmap(matrix=mat, alpha=False)

        # 如果图像的宽度或高度超过2000像素，则不放大图像
        if pm.width > 2000 or pm.height > 2000:
            pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

        # 将pixmap转换为PIL图像
        img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
        # 将PIL图像转换为OpenCV格式
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        imgs.append(img)  # 将处理后的图像添加到列表中

# 使用OCR引擎处理每张图像
for index, img in enumerate(imgs):
    result = ocr_engine(img)  # 对图像进行OCR识别
    # 将结构化结果保存到指定文件夹
    save_structure_res(result, save_folder, os.path.basename(img_path).split('.')[0], index)

    # 打印OCR结果，去除每行中的图像数据
    for line in result:
        line.pop('img')  # 从结果中移除图像数据
        print(line)  # 打印处理后的行
