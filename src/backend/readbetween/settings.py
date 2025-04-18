import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 获取 APP_ENV 环境变量
APP_ENV = os.getenv('APP_ENV', 'dev')

# 设置项目的基础目录
BASE_DIR = Path(__file__).resolve().parent


# 不同环境对应的配置文件
CONFIG_FILE = BASE_DIR / 'core' / f'config_{APP_ENV}.yaml'


# 读取 YAML 配置文件
with open(CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)

def get_config(key, default=None):
    """
    获取配置项的值

    :param key: 配置项的键，支持嵌套键，如 'database.host'
    :param default: 如果键不存在，返回的默认值
    :return: 配置项的值
    """
    keys = key.split('.')
    value = config
    for k in keys:
        value = value.get(k, default)
        if value is default:
            break
    return value