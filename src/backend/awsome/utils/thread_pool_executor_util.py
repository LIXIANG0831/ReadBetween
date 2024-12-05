from awsome.utils.logger_util import logger_util
from concurrent.futures import ThreadPoolExecutor, as_completed


class ThreadPoolExecutorUtil:
    def __init__(self, max_workers=5):
        """
        初始化线程池工具类。

        :param max_workers: 线程池中的最大工作线程数，默认为5。
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []
        logger_util.info(f"线程池初始化完成，最大工作线程数：{max_workers}")

    def submit_task(self, func, *args, **kwargs):
        """
        提交任务到线程池。

        :param func: 要执行的函数。
        :param args: 函数位置参数。
        :param kwargs: 函数关键字参数。
        :return: 任务的Future对象。
        """
        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        logger_util.info(f"任务提交成功：{func.__name__} 带有参数 {args} 和 {kwargs}")
        return future

    def wait_for_all(self):
        """
        等待所有任务完成。
        """
        logger_util.info("等待所有任务完成...")
        for future in as_completed(self.futures):
            try:
                # 获取任务结果
                result = future.result()
                logger_util.info(f"任务完成:{future} 结果:{result}")
            except Exception as e:
                # 处理异常
                logger_util.error(f"任务执行异常: {e}", exc_info=True)

    def shutdown(self):
        """
        关闭线程池。
        """
        logger_util.info("关闭线程池...")
        self.executor.shutdown(wait=True)
        logger_util.info("线程池已关闭")


# 使用示例
if __name__ == "__main__":
    # 定义一个简单的任务函数
    def task_example(data):
        print(f"处理数据: {data}")
        # 模拟耗时操作
        import time
        time.sleep(1)
        return f"数据{data}处理完成"


    # 创建线程池工具类实例
    thread_pool_util = ThreadPoolExecutorUtil(max_workers=2)

    # 提交任务
    futures = [thread_pool_util.submit_task(task_example, i) for i in range(100)]

    # 等待所有任务完成
    thread_pool_util.wait_for_all()

    # 关闭线程池
    thread_pool_util.shutdown()