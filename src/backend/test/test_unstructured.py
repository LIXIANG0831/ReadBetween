from unstructured.partition.auto import partition

"""

pip install "unstructured[all-docs]"

:系统额外依赖

::MAC
brew install libmagic poppler tesseract libreoffice pandoc
brew install tesseract-ocr-chi-sim

::Ubuntu
sudo apt update && sudo apt install -y libmagic-dev poppler-utils tesseract-ocr libreoffice pandoc
sudo apt install -y tesseract-ocr-chi-sim  # 安装简体中文支持
"""

elements = partition(filename="/Users/lixiang/Documents/Test_Material/普通.pdf")

for element in elements:
    print(element)
