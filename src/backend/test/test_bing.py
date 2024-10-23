from langchain_community.utilities import BingSearchAPIWrapper
from awsome.settings import get_config

BING_SEARCH_URL = get_config("api.bing.endpoint")
BING_SUBSCRIPTION_KEY = get_config("api.bing.api_key")
search = BingSearchAPIWrapper(bing_subscription_key=BING_SUBSCRIPTION_KEY,
                              bing_search_url=f"{BING_SEARCH_URL}/v7.0/search",
                              k=4)

result = search.run("西安的天气怎么样？")
origin = search.results("西安的天气怎么样？")
print(result) # 结果信息
print(origin) # 溯源信息