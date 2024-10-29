import psycopg2
import os
import signal
import sys
import json
from bs4 import BeautifulSoup
from awsome.settings import get_config

# 数据库 URI
db_uri = get_config("storage.postgres.uri")

# 确保保存文件的目录存在
output_dir = '/Users/lixiang/Desktop/wbcontent_files'
os.makedirs(output_dir, exist_ok=True)

# 进度文件
progress_file = 'progress.json'

# 记录当前进度
current_index = 0

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def save_progress(index):
    """保存当前进度到文件"""
    with open(progress_file, 'w') as f:
        json.dump({'current_index': index}, f)


def load_progress():
    """从文件中加载进度"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f).get('current_index', 0)
    return 0


def signal_handler(sig, frame):
    """处理信号，优雅退出并保存进度"""
    print("\nReceived interrupt signal. Saving progress...")
    save_progress(current_index)
    sys.exit(0)


def fetch_wbcontent(cursor):
    """生成器函数，逐行获取 """
    query = ("SELECT wbtitle,wbsummary,wbcontent,wbpicurl,wbkeyword,wbdate,wbupdatedate "
             "FROM wbnews "
             "ORDER BY wbupdatedate desc;")
    cursor.execute(query)
    for row in cursor:
        yield row


# 捕获中断信号
signal.signal(signal.SIGINT, signal_handler)

try:
    # 连接到 PostgreSQL 数据库
    connection = psycopg2.connect(db_uri)

    # 创建一个游标对象
    cursor = connection.cursor()

    # 加载进度
    current_index = load_progress()

    # 使用生成器逐行处理 wbcontent
    for idx, (wbtitle, wbsummary, wbcontent, wbpicurl, wbkeyword, wbdate, wbupdatedate) in enumerate(fetch_wbcontent(cursor)):
        if idx < current_index:
            continue  # 跳过已处理的记录
        if os.path.exists(os.path.join(output_dir, f'{wbtitle}-{wbdate}.txt'.replace('/', '-'))):
            continue # 跳过已存在文件

        # 使用 id 作为文件名，确保文件名唯一
        filename = os.path.join(output_dir, f'{wbtitle}-{wbdate}.txt'.replace('/', '-'))

        # 移除html标签
        if wbcontent: wbcontent = remove_html_tags(wbcontent)

        # 写入文件
        if wbcontent and wbcontent.strip():
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(wbcontent)  # 写入文件

        # 更新当前进度
        current_index = idx + 1
        save_progress(current_index)

        # 可选：每处理一定数量的记录后，可以打印进度
        if (idx + 1) % 100 == 0:
            print(f"已处理 {idx + 1} 条记录...")

    print(f"所有文件已经保存至 '{output_dir}'")

except Exception as e:
    print("Error occurred:", e)

finally:
    # 关闭游标和连接
    if cursor:
        cursor.close()
    if connection:
        connection.close()
