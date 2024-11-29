from pymilvus import FieldSchema, DataType
"""
Milvus 默认配置项
"""
milvus_default_fields = [
    FieldSchema(name="bbox", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="page", dtype=DataType.INT64),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="extra", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="file_id", dtype=DataType.INT64),
    FieldSchema(name="knowledge_id", dtype=DataType.VARCHAR, max_length=65535, is_partition_key=True),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024)
]

milvus_default_index_params = {
    "index_type": "HNSW",
    "metric_type": "L2",
    "params": {
        "M": 8,
        "efConstruction": 64
    }
}


"""
ElasticSearch默认配置项
"""
es_index_settings = {
    "number_of_shards": 1,
    "number_of_replicas": 1
}