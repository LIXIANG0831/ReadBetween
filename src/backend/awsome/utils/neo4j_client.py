from typing import Dict, Any, List

from fastapi import HTTPException
from neo4j import GraphDatabase

# 创建一个全局变量用于存储 Neo4j 驱动
_neo4j_driver = None


class Neo4jClient:
    @staticmethod
    def initialize(uri: str, user: str, password: str):
        """
        初始化 Neo4j 连接
        :param uri: Neo4j 数据库的 URI (例如: bolt://localhost:7687)
        :param user: 数据库用户名
        :param password: 数据库密码
        """
        global _neo4j_driver
        if _neo4j_driver is None:
            _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            print("Neo4j driver initialized successfully.")
        else:
            print("Neo4j driver already initialized.")

    @staticmethod
    def execute_cypher(query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行 Cypher 查询
        """
        global _neo4j_driver
        if _neo4j_driver is None:
            raise HTTPException(status_code=500, detail="Neo4j driver not initialized.")

        with _neo4j_driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    @staticmethod
    def close():
        """
        关闭 Neo4j 驱动连接
        """
        global _neo4j_driver
        if _neo4j_driver:
            _neo4j_driver.close()
            _neo4j_driver = None
            print("Neo4j driver closed successfully.")
