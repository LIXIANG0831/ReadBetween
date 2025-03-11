import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from awsome.models.schemas.response import resp_200, resp_500
from awsome.models.v1.memory import MemoryQuery
from awsome.utils.logger_util import logger_util
from awsome.utils.neo4j_client import Neo4jClient, _neo4j_driver
from awsome.settings import get_config
from awsome.utils.redis_util import RedisUtil

router = APIRouter(tags=["记忆管理"])

redis_util = RedisUtil()


@router.post("/memory/query")
async def query_memory(memory_query: MemoryQuery):
    try:
        if _neo4j_driver is None:  # 未初始化Neo4j连接
            neo4j_uri = get_config("memory_only.neo4j.url")
            neo4j_user = get_config("memory_only.neo4j.username")
            neo4j_password = get_config("memory_only.neo4j.password")
            Neo4jClient.initialize(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)

        query = f"MATCH (n)-[r]->(m) {memory_query.condition} " \
                f"RETURN n.name AS source, n.created AS source_created, type(r) AS relationship, m.name AS target, m.created AS target_created"

        results = Neo4jClient.execute_cypher(query, memory_query.condition_parameters)
        structured_results = []
        for record in results:
            structured_results.append(record)

        return resp_200(data=structured_results)
    except Exception as e:
        logger_util.error(f"查询Neo4J数据失败: {str(e)}")
        return resp_500(message=str(e))


@router.get("/memory/get_info")
async def get_memory_setting_info():
    try:
        memory_setting = get_config("memory_only")
        if redis_util.exists("memory_setting"):
            return resp_200(data=json.loads(redis_util.get("memory_setting")))
        else:
            redis_util.set("memory_setting", json.dumps(memory_setting))
            return resp_200(data=memory_setting)
    except Exception as e:
        logger_util.error(f"查询Neo4J数据失败: {str(e)}")
        return resp_500(message=str(e))
