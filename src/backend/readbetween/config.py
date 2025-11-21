from typing import List, Optional

from pydantic import BaseModel  # 确保导入 BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


# BaseConfig 保持不变
class BaseConfig(BaseSettings):
    """基础配置类"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


# AppConfig
class AppConfig(BaseModel):
    """应用配置"""
    author: str = "LIXIANG"
    version: str = "v1.0"
    port: int = 8080
    env: str = "prod"


# StorageConfig
class StorageConfig(BaseModel):
    """存储配置"""

    class MySQLConfig(BaseModel): uri: str = ""

    class RedisConfig(BaseModel): uri: str = ""

    class MinioConfig(BaseModel):
        secure: bool = False
        cert_check: bool = False
        endpoint: str = ""
        access_key: str = ""
        secret_key: str = ""
        default_bucket: str = "readbetween"

    class MilvusConfig(BaseModel): uri: str = ""

    class ESConfig(BaseModel):
        hosts: List[str] = []
        timeout: int = 200
        http_auth: Optional[str] = None

    mysql: MySQLConfig = MySQLConfig()
    redis: RedisConfig = RedisConfig()
    minio: MinioConfig = MinioConfig()
    milvus: MilvusConfig = MilvusConfig()
    es: ESConfig = ESConfig()


# MemoryConfig
class MemoryConfig(BaseModel):
    """记忆模块配置"""

    class Neo4jConfig(BaseModel):
        url: str = ""
        username: str = ""
        password: str = ""

    class LlmConfig(BaseModel):
        base_url: str = ""
        api_key: str = ""
        llm_name: str = ""

    class EmbeddingConfig(BaseModel):
        base_url: str = ""
        api_key: str = ""
        embedding_name: str = ""
        dimension: int = 768

    milvus_memory_name: str = ""
    neo4j: Neo4jConfig = Neo4jConfig()
    llm: LlmConfig = LlmConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()


class LoggerConfig(BaseModel):
    base_log_path: str = "./readbetween_log"


class LiveKitConfig(BaseModel):
    url: str = "ws://localhost:7880"
    api_key: str = "devkey"
    api_secret: str = "secret"


# Deprecated
class SystemConfig(BaseModel):
    class ModelsConfig(BaseModel):
        class EmbeddingConfig(BaseModel):
            name: str = "iic/nlp_gte_sentence-embedding_chinese-large"

        base_dir: str = "./static/models"
        embedding: EmbeddingConfig = EmbeddingConfig()

    default_model_provider: List[dict] = []
    models: ModelsConfig = ModelsConfig()


# Settings 类是唯一的顶层 BaseSettings
class Settings(BaseConfig):
    """全局配置"""
    app: AppConfig = AppConfig()
    storage: StorageConfig = StorageConfig()
    memory: MemoryConfig = MemoryConfig()
    logger: LoggerConfig = LoggerConfig()
    livekit: LiveKitConfig = LiveKitConfig()
    # system: SystemConfig = SystemConfig()

    model_config = SettingsConfigDict(
        env_file='.env',  # 从 BaseConfig 继承（或重新声明）
        env_file_encoding='utf-8',  # 从 BaseConfig 继承（或重新声明）
        extra='ignore',  # 从 BaseConfig 继承（或重新声明）
        env_nested_delimiter='__'  # 应用于所有嵌套 BaseModel
    )


settings = Settings()
