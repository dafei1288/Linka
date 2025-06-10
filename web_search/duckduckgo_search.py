# filepath: c:\Users\k\Documents\project\programming_project\python_project\importance\Linka\web_search\duckduckgo_search.py
from duckduckgo_search import DDGS
from typing import List, Dict, Optional


def search_duckduckgo(query: str, max_results: int = 10, proxies: Optional[Dict] = None, user_agent: Optional[str] = None) -> List[Dict]:
    """
    使用 DuckDuckGo 进行网络搜索
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数量
        proxies: 代理设置，格式如 {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        user_agent: 自定义 User-Agent
        
    Returns:
        搜索结果列表，每个结果包含 title, href/url, body/snippet 等字段
    """
    ddgs = DDGS()
    
    # 设置默认 User-Agent
    default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    headers = {
        "User-Agent": user_agent or default_user_agent
    }
    
    results = []
    try:
        for r in ddgs.text(query, max_results=max_results):
            # 只收集结果，不做可访问性验证
            results.append(r)
    except Exception as e:
        print(f"DuckDuckGo 搜索出错: {e}")
        raise
        
    return results


if __name__ == "__main__":
    # 测试代码
    test_query = "OpenAI GPT-4o"
    results = search_duckduckgo(test_query, max_results=10)
    for i, result in enumerate(results, 1):
        print(f"结果 {i}:")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"链接: {result.get('href') or result.get('url', 'N/A')}")
        print(f"摘要: {result.get('body') or result.get('snippet', 'N/A')}")
        print("-" * 50)
