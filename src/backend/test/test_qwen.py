from http import HTTPStatus

from openai import OpenAI
import dashscope


client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-3fbbebdfbdc04d9284621238b6967ba9", # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# completion = client.chat.completions.create(
#     model="qwen-long", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
#     messages=[
#         {'role': 'system', 'content': 'You are a helpful assistant.'},
#         {'role': 'user', 'content': '你是谁？'}
#         ]
# )


# print(completion.choices[0].message.content)

def embed_with_str():
    resp = dashscope.TextEmbedding.call(
        api_key="sk-3fbbebdfbdc04d9284621238b6967ba9",
        model=dashscope.TextEmbedding.Models.text_embedding_v1,
        input='衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买')

    if resp.status_code == HTTPStatus.OK:
        print(resp)
    else:
        print(resp)

if __name__ == '__main__':
    embed_with_str()