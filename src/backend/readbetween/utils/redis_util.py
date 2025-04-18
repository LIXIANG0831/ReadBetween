import redis
from redis import ConnectionPool
from typing import Optional, Any
from readbetween.settings import get_config

class RedisUtil:
    """封装 Redis 操作的工具类"""

    def __init__(self, url: str = None, max_connections: int = 10):
        """初始化 Redis 客户端

        Args:
            url (str): Redis 服务器的连接 URL
            max_connections (int): 最大连接数
        """
        url = url or get_config("storage.redis.uri")
        self.pool = ConnectionPool.from_url(url, max_connections=max_connections)
        self.client = redis.StrictRedis(connection_pool=self.pool)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置键值对

        Args:
            key (str): 键
            value (Any): 值
            ex (Optional[int]): 过期时间（秒）

        Returns:
            bool: 操作是否成功
        """
        return self.client.set(key, value, ex=ex)

    def setNX(self, key: str, value: Any) -> bool:
        """设置键值对，仅在键不存在时

        Args:
            key (str): 键
            value (Any): 值

        Returns:
            bool: 如果键设置成功返回 True，否则返回 False
        """
        return self.client.setnx(key, value)

    def get(self, key: str) -> Optional[str]:
        """获取键对应的值

        Args:
            key (str): 键

        Returns:
            Optional[str]: 值，如果键不存在则返回 None
        """
        return self.client.get(key)

    def delete(self, key: str) -> int:
        """删除指定的键

        Args:
            key (str): 键

        Returns:
            int: 被删除的键的数量
        """
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key (str): 键

        Returns:
            bool: 如果键存在则返回 True，否则返回 False
        """
        return self.client.exists(key) == 1

    def expire(self, key: str, timeout: int) -> bool:
        """设置键的过期时间

        Args:
            key (str): 键
            timeout (int): 过期时间（秒）

        Returns:
            bool: 操作是否成功
        """
        return self.client.expire(key, timeout)

    def keys(self, pattern: str = '*') -> list:
        """获取匹配指定模式的所有键

        Args:
            pattern (str): 匹配模式（默认为 '*'）

        Returns:
            list: 匹配的键列表
        """
        return self.client.keys(pattern)

    def flushdb(self) -> bool:
        """清空当前数据库

        Returns:
            bool: 操作是否成功
        """
        return self.client.flushdb()

    # 你可以根据需要添加更多的 Redis 操作方法
