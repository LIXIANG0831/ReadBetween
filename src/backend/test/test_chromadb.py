# pip install chromadb
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_base="https://gpt.cosmoplat.com/v1",
                api_key="sk-j6rj6sglXDAWPJHr6fC4D63fDbEd42E99b1cC7479384E2B6",
                model_name="text-embedding-ada-002"
            )

print(openai_ef(["你好"]))


client = chromadb.PersistentClient(path="chromadb")

# switch `create_collection` to `get_or_create_collection` to avoid creating a new collection every time
collection = client.get_or_create_collection(
    name="my_collection",
    embedding_function=openai_ef,
)

# switch `add` to `upsert` to avoid adding the same documents every time
collection.upsert(
    documents=[
        "在春暖花开的季节，微风轻拂，阳光洒在湖面上，波光粼粼。远处的山峦在云雾中若隐若现，仿佛一幅天然的水墨画。人们在湖边漫步，享受着大自然的宁静与美好。",
        "春天来临，湖边的景色格外迷人。阳光洒在湖面上，波光闪烁，微风拂过，带来阵阵花香。远处的山峦在云雾中时隐时现，宛如一幅水墨画。人们漫步在湖边，沉浸在大自然的宁静之中。",
        "夏天的海边，烈日炎炎，海浪拍打着沙滩，发出阵阵轰鸣。孩子们在沙滩上玩耍，欢声笑语回荡在空中。远处的海面上，帆船点点，海鸥在天空中翱翔，构成了一幅生动的画面。",
        "在寒冷的冬天，雪花纷纷扬扬地飘落，大地被覆盖上一层洁白的雪毯。树枝上挂满了冰凌，晶莹剔透。远处的山峦被白雪覆盖，宛如银装素裹的世界。人们裹着厚厚的棉衣，在雪地里行走，留下一串串深深的脚印。",
        "秋天的森林，树叶逐渐变黄，微风一吹，落叶纷飞。阳光透过树叶的缝隙洒在地上，形成斑驳的光影。远处的山峦在秋日的阳光下显得格外壮美。人们漫步在林间小道上，感受着秋天的宁静与丰收的气息。"
    ],
    ids=["id1", "id2", "id3", "id4", "id5"]
)

# results = collection.query(
#     query_texts=["春天的湖边"],  # Chroma 会自动向量化文本进行查询
#     # query_texts=["冬天好冷"],
#     n_results=2  # how many results to return
# )

results = collection.query(
    query_embeddings=openai_ef(["春天的湖边"]),  # 直接通过向量查询
    n_results=2  # how many results to return
)

print(results)

documents = results.get("documents", [])
distances = results.get("distances", [])

document_distance_pairs = zip(documents, distances)

# 遍历并打印结果
for document, distance in document_distance_pairs:
    print(f"Document: {document}\nDistance: {distance}")
