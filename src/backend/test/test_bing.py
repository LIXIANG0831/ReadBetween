from langchain_community.utilities import BingSearchAPIWrapper
from awsome.settings import get_config

BING_SEARCH_URL = get_config("api.bing.endpoint")
BING_SUBSCRIPTION_KEY = get_config("api.bing.api_key")
search = BingSearchAPIWrapper(bing_subscription_key=BING_SUBSCRIPTION_KEY,
                              bing_search_url=f"{BING_SEARCH_URL}/v7.0/search",
                              k=5)

results = search.results("西安的天气怎么样？", 5)
snippets = [] # 结果集合
origins = [] # 溯源集合
if len(results) == 0:
    print("No good Bing Search Result was found")
for result in results:
    snippets.append(result["snippet"])
    origin_dict = {
        "title": str(result["title"]).replace("<b>","").replace("</b>",""),
        "link": result["link"],
    }
    origins.append(origin_dict)

print(snippets) # 检索信息
print(origins) # 溯源信息