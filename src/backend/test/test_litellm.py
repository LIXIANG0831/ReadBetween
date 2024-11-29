# pip install litellm
import litellm
litellm.set_verbose = True  # 打印litellm调用日志

messages = [{ "content": "介绍一下你自己。","role": "user"}]
# vllm call
vllm_response = litellm.completion(
    model="hosted_vllm/ycpc-gpt",
    base_url="http://10.193.22.13:8080/v1",
    api_key="sk-2HQfMSP2ixV91oQb0788C26b667446FbAd8341Dd3b61F97f",
    messages=messages
)

# openai-compatible call
openai_compatible_response = litellm.completion(
    model="openai/ycpc-gpt",
    base_url="https://chat-proxy.xaa.ycpc.com/v1",
    api_key="sk-2HQfMSP2ixV91oQb0788C26b667446FbAd8341Dd3b61F97f",
    messages=messages
)

print(openai_compatible_response.choices[0].message.content)
