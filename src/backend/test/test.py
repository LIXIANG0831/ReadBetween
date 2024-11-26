# import os
# # from langchain_community.embeddings
# from langchain_community.embeddings.openai import Embeddings
# os.environ["OPENAI_API_KEY"] = "sk-2HQfMSP2ixV91oQb0788C26b667446FbAd8341Dd3b61F97f"
# os.environ["OPENAI_API_BASE"] = "https://chat-proxy.xaa.ycpc.com/v1/"
# embedding_model = Embeddings(model="text-embedding-ada-002",chunk_size=1000)
# result1 = embedding_model.embed_query(text[0])
# print(result1[:5])
# print(result1[-5:])
# result2 = embedding_model.embed_query(text[1])
# print(result2[:5])
# print(result2[-5:])


import openai
from openai.types import CreateEmbeddingResponse

text = ['你好啊','你好']
client = openai.Client(
    api_key='sk-2HQfMSP2ixV91oQb0788C26b667446FbAd8341Dd3b61F97f',
    base_url='https://chat-proxy.xaa.ycpc.com/v1'
)
response:CreateEmbeddingResponse = client.embeddings.create(input=text,model='text-embedding-ada-002')
for emb in response.data:
    print(emb.embedding)


