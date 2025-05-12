import sys
from loguru import logger
from readbetween.config import settings

class LoggerUtil:
    def __init__(self, log_file_path):
        self.logger = logger
        # 清空所有默认的日志设置
        self.logger.remove()

        # 添加控制台输出的格式
        self.logger.add(sys.stdout,
                        format="<green>{time:YYYYMMDD HH:mm:ss}</green> | "  # 颜色>时间
                               "{process.name} | "  # 进程名
                               "{thread.name} | "  # 线程名
                               "<cyan>{module}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | "  # 模块名.方法名:行号
                               "<level>{level}</level>: "  # 日志等级
                               "<level>{message}</level>",  # 日志内容
                        )

        # 输出不同级别的日志到不同的文件
        self.logger.add(log_file_path + '/info.log', level='INFO',
                        format='{time:YYYYMMDD HH:mm:ss} - '  # 时间
                               "{process.name} | "  # 进程名
                               "{thread.name} | "  # 线程名
                               '{module}.{function}:{line} - {level} - {message}',  # 模块名.方法名:行号
                        rotation="10 MB")  # 文件大小达到 10 MB 时轮转

        self.logger.add(log_file_path + '/debug.log', level='DEBUG',
                        format='{time:YYYYMMDD HH:mm:ss} - '
                               "{process.name} | "
                               "{thread.name} | "
                               '{module}.{function}:{line} - {level} - {message}',
                        rotation="10 MB")

        self.logger.add(log_file_path + '/warning.log', level='WARNING',
                        format='{time:YYYYMMDD HH:mm:ss} - '
                               "{process.name} | "
                               "{thread.name} | "
                               '{module}.{function}:{line} - {level} - {message}',
                        rotation="10 MB")

        self.logger.add(log_file_path + '/error.log', level='ERROR',
                        format='{time:YYYYMMDD HH:mm:ss} - '
                               "{process.name} | "
                               "{thread.name} | "
                               '{module}.{function}:{line} - {level} - {message}',
                        rotation="10 MB")

        self.logger.add(log_file_path + '/critical.log', level='CRITICAL',
                        format='{time:YYYYMMDD HH:mm:ss} - '
                               "{process.name} | "
                               "{thread.name} | "
                               '{module}.{function}:{line} - {level} - {message}',
                        rotation="10 MB")

    def get_logger(self):
        # 返回 logger 实例
        return self.logger


# 获取日志文件路径配置
base_log_path = settings.logger.base_log_path
# 创建 MyLogger 的实例并获取 logger
logger_util = LoggerUtil(log_file_path=base_log_path).get_logger()


def ss():
    # 记录不同级别的日志
    logger_util.info("这是一个信息日志。")
    logger_util.debug("这是一个调试日志。")
    logger_util.warning("这是一个警告日志。")
    logger_util.error("这是一个错误日志。")
    logger_util.critical("这是一个严重错误日志。")


if __name__ == '__main__':
    ss()
