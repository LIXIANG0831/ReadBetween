from readbetween.utils.logger_util import logger_util
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from functools import partial


class ThreadPoolExecutorUtil:
    def __init__(self, max_workers=5, async_max_workers=5):
        """
        初始化线程池工具类。

        :param max_workers: 同步线程池中的最大工作线程数，默认为5。
        :param async_max_workers: 异步线程池中的最大工作线程数，默认为5。
        """
        # 同步线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []

        # 异步线程池
        self.async_executor = ThreadPoolExecutor(max_workers=async_max_workers)
        self.async_futures = []
        self.loop = asyncio.get_event_loop()

        logger_util.info(f"线程池初始化完成，同步最大工作线程数：{max_workers}，异步最大工作线程数：{async_max_workers}")

    def submit_task(self, func, *args, **kwargs):
        """
        提交同步任务到线程池。

        :param func: 要执行的函数。
        :param args: 函数位置参数。
        :param kwargs: 函数关键字参数。
        :return: 任务的Future对象。
        """
        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        logger_util.info(f"同步任务提交成功：{func.__name__} 带有参数 {args} 和 {kwargs}")
        return future

    async def submit_async_task(self, func, *args, **kwargs):
        """
        提交异步任务到线程池。

        :param func: 要执行的协程函数或普通函数。
        :param args: 函数位置参数。
        :param kwargs: 函数关键字参数。
        :return: 任务的Future对象。
        """
        # 如果是协程函数，直接加入事件循环
        if asyncio.iscoroutinefunction(func):
            future = asyncio.ensure_future(func(*args, **kwargs))
        else:
            # 普通函数通过run_in_executor执行
            future = self.loop.run_in_executor(self.async_executor, partial(func, *args, **kwargs))

        self.async_futures.append(future)
        logger_util.info(f"异步任务提交成功：{func.__name__} 带有参数 {args} 和 {kwargs}")
        return future

    def wait_for_all(self):
        """
        等待所有同步任务完成。
        """
        logger_util.info("等待所有同步任务完成...")
        for future in as_completed(self.futures):
            try:
                result = future.result()
                logger_util.info(f"同步任务完成:{future} 结果:{result}")
            except Exception as e:
                logger_util.error(f"同步任务执行异常: {e}", exc_info=True)

    async def wait_for_all_async(self):
        """
        等待所有异步任务完成。
        """
        logger_util.info("等待所有异步任务完成...")
        for future in asyncio.as_completed(self.async_futures):
            try:
                result = await future
                logger_util.info(f"异步任务完成:{future} 结果:{result}")
            except Exception as e:
                logger_util.error(f"异步任务执行异常: {e}", exc_info=True)

    def shutdown(self):
        """
        关闭所有线程池。
        """
        logger_util.info("关闭线程池...")
        self.executor.shutdown(wait=True)
        self.async_executor.shutdown(wait=True)
        logger_util.info("所有线程池已关闭")


# 使用示例
if __name__ == "__main__":
    # 定义一个简单的同步任务函数
    def sync_task_example(data):
        print(f"处理同步数据: {data}")
        import time
        time.sleep(1)
        return f"同步数据{data}处理完成"


    # 定义一个简单的异步任务函数
    async def async_task_example(data):
        print(f"处理异步数据: {data}")
        await asyncio.sleep(1)
        return f"异步数据{data}处理完成"


    # 创建线程池工具类实例
    thread_pool_util = ThreadPoolExecutorUtil(max_workers=2, async_max_workers=3)

    # 提交同步任务
    sync_futures = [thread_pool_util.submit_task(sync_task_example, i) for i in range(3)]


    # 提交异步任务
    async def submit_async_tasks():
        tasks = [thread_pool_util.submit_async_task(async_task_example, i) for i in range(10, 13)]
        await thread_pool_util.wait_for_all_async()
        return tasks


    # 运行异步任务
    loop = asyncio.get_event_loop()
    async_futures = loop.run_until_complete(submit_async_tasks())

    # 等待所有同步任务完成
    thread_pool_util.wait_for_all()

    # 关闭线程池
    thread_pool_util.shutdown()