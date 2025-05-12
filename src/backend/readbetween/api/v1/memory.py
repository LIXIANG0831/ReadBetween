import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from readbetween.config import Settings
from readbetween.core.dependencies import get_settings
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.models.v1.memory import MemoryQuery
from readbetween.utils.logger_util import logger_util
from readbetween.utils.neo4j_client import Neo4jClient, _neo4j_driver
from readbetween.settings import get_config
from readbetween.utils.redis_util import RedisUtil

router = APIRouter(tags=["记忆管理"])

redis_util = RedisUtil()


@router.post("/memory/query")
async def query_memory(memory_query: MemoryQuery, settings: Settings = Depends(get_settings)):
    try:
        if _neo4j_driver is None:  # 未初始化Neo4j连接
            neo4j_uri = settings.memory.neo4j.url
            neo4j_user = settings.memory.neo4j.username
            neo4j_password = settings.memory.neo4j.password
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


