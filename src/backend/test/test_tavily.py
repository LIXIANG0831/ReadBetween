from awsome.settings import get_config
tavily_api_key = get_config("api.tavily.api_key")
def _tavily_search():
    from tavily import TavilyClient
    tavily_client = TavilyClient(api_key=tavily_api_key)
    # 1. Executing a simple search query
    response_1 = tavily_client.search("今天西安天气怎么样？")
    # 2. Executing a context search query
    response_2 = tavily_client.get_search_context("今天西安天气怎么样？")
    # 3. Executing a Q&A search query
    response_3 = tavily_client.qna_search("今天西安天气怎么样？")

    print(response_1)
    print(response_2)
    print(response_3)

_tavily_search()