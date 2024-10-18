from openai import OpenAI
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility, Index
from awsome.settings import get_config
from pymilvus import MilvusClient
from pymilvus.milvus_client.milvus_client import IndexParams

# 获取OpenAI配置信息
openai_api_key = get_config("openai.api_key")
openai_base_url = get_config("openai.base_url")

# 创建OpenAI连接
openai_client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_base_url
)

# 获取Milvus配置信息
MILVUS_URI = get_config("milvus.uri")
COLLECTION_NAME = 'test_milvus'
milvus_client = MilvusClient(uri=MILVUS_URI)



# 创建集合
def create_collection():
    if milvus_client.has_collection(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME} already exists. Dropping it.")
        milvus_client.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
        FieldSchema(name="page_number", dtype=DataType.INT32),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="chunk", dtype=DataType.VARCHAR, max_length=1000)
    ]
    schema = CollectionSchema(fields, description="文档向量化测试")

    milvus_client.create_collection(collection_name=COLLECTION_NAME, schema=schema)

def insert_data_milvus(text, page_number, title):
    chunks = text.split("\n")
    for chunk in chunks:
        embedding = get_embedding(chunk)
        res = milvus_client.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "embedding": embedding,
                "page_number": page_number,
                "title": title,
                "chunk": chunk
            }])

        print(res)

# 使用Embedding模型进行向量化
def get_embedding(text, model="text-embedding-ada-002"):
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding



def create_index():
    index_params = IndexParams(
        field_name="embedding",
        index_type="HNSW",  # 指定索引类型
        params={"M": 16, "efConstruction": 200},  # 根据需要设置参数
        metric_type="L2"  # 设置度量类型
    )
    milvus_client.create_index(collection_name=COLLECTION_NAME, index_params=index_params)

def load_collection():
    milvus_client.load_collection(COLLECTION_NAME)

# 根据文本内容检索 Milvus 集合
def search_in_milvus(collection, query_text, top_k=5, model="text-embedding-ada-002"):
    # 将查询文本向量化
    query_embedding = get_embedding(query_text, model=model)

    # 执行搜索
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}
    }
    results = collection.search([query_embedding], "embedding", search_params, limit=top_k)

    # 处理并返回搜索结果
    for result in results:
        print(result)
        for hit in result:
            print(hit)

    return results



def _create_milvus():
    text = "这是一个示例文档，用于测试向量化和插入到Milvus。\n这是第二行。\n这是第三行。\n这是第四行。\n这是第五行"
    page_number = 1
    title = "示例文档标题"

    # 创建collection(相当于数据库的表)
    create_collection()

    # 向milvus插入向量化后的数据
    insert_data_milvus(text, page_number, title)

    # 设置索引
    create_index()

    # 加载collection
    load_collection()



def _search_milvus():
    query_text = "三"  # 要检索的文本
    query_vectors = get_embedding(query_text)

    results = milvus_client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vectors],
        limit=5,
        output_fields = ["id", "page_number", "title", "chunk"]
    )
    for result in results:
        for hit in result:
            print(hit)


# _create_milvus()
_search_milvus()