from pymilvus import FieldSchema, DataType
from readbetween.config import settings
from enum import Enum

# 系统内置嵌入模型
MODEL_SAVE_PATH = './static/models'
BUILT_IN_EMBEDDING_NAME = "iic/nlp_gte_sentence-embedding_chinese-large"  # 1024维
BUILT_IN_TTS_NAME = "AI-ModelScope/Kokoro-82M-v1.1-zh"
BUILT_IN_STT_NAME = "Systran/faster-whisper-base"


# SourceMsgType 引用来源类型
class SourceMsgType(Enum):
    WEB = "web"
    KB = "kb"


# 系统内置供应商
SYSTEM_MODEL_PROVIDER = [{"OpenAI-Compatible": "openai-compatible"}, {"Qwen": "qwen"}, {"OpenAI": "openai"},
                         {"vLLM": "hosted_vllm"}]

# 盐
SALT = "readbetween"

# 模型类型
ModelType_LLM = "llm"
ModelType_Embedding = "embedding"

# 系统内置嵌入模型显示名称
System_Embedding_Name = "系统内置嵌入模型"

# Redis前缀
PrefixRedisConversation = "conv_cfg_info:"
Ex_PrefixRedisConversation = 30 * 60

PrefixRedisKnowledge = "know_cfg_info:"

RedisMCPServerKey = "mcp_server_info"
RedisMCPServerDetailKey = "mcp_server_detail_info"

"""
Milvus 默认配置项
"""
milvus_default_fields_1024 = [
    FieldSchema(name="bbox", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="start_page", dtype=DataType.INT64),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="extra", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="knowledge_id", dtype=DataType.VARCHAR, max_length=65535, is_partition_key=True),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024)
]

milvus_default_fields_768 = [
    FieldSchema(name="bbox", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="start_page", dtype=DataType.INT64),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="extra", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="knowledge_id", dtype=DataType.VARCHAR, max_length=65535, is_partition_key=True),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768)
]

"""
Milvus 索引参数
"""
milvus_default_index_params = {
    "index_type": "HNSW",
    "metric_type": "L2",
    "params": {
        "M": 8,
        "efConstruction": 64
    }
}

"""
常量
"""
# 系统默认启用模型
# Deprecated
redis_default_model_key = "awsome_default_system_model"

"""
记忆默认配置
"""
memory_config = {
    "llm": {  # LLM配置
        "provider": "openai",
        "config": {
            "model": settings.memory.llm.llm_name,
            "temperature": 0.1,
            "max_tokens": 2000,
            "top_p": 0.3,
            "api_key": settings.memory.llm.api_key,
            "openai_base_url": settings.memory.llm.base_url
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": settings.memory.embedding.embedding_name,
            "embedding_dims": settings.memory.embedding.dimension,
            "api_key": settings.memory.embedding.api_key,
            "openai_base_url": settings.memory.embedding.base_url
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            # "url": "neo4j+s://localhost:7687",
            "url": settings.memory.neo4j.url,
            "username": settings.memory.neo4j.username,
            "password": settings.memory.neo4j.password,
        }
    },
    "vector_store": {
        "provider": "milvus",
        "config": {
            "collection_name": settings.memory.milvus_memory_name,
            "embedding_model_dims": settings.memory.embedding.dimension,
            "url": settings.storage.milvus.uri
        }
    },
    "version": "v1.1"  # v1.1配置支持Graph
}
