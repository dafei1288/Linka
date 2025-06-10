import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def sogou_search(query: str, num: int = 5) -> List[Dict]:
    """
    搜狗搜索，返回前num条结果。默认只搜索公众号内容。
    :param query: 搜索关键词
    :param num: 返回结果数
    :return: [{"title":..., "url":..., "snippet":...}, ...]
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # 使用 site:weixin.sogou.com 限制只搜索公众号内容
    query = f"公众号 {query}"
    params = {
        "query": query,
        "ie": "utf8"
    }
    url = "https://www.sogou.com/web"
    resp = requests.get(url, params=params, headers=headers, timeout=8)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select(".vrwrap, .rb, .pt"):
        a = item.select_one("a")
        if not a or not a.get("href"): continue
        title = a.get_text(strip=True)
        link = a["href"]
        snippet = item.get_text(" ", strip=True)
        results.append({"title": title, "url": link, "snippet": snippet})
        if len(results) >= num:
            break
    return results

if __name__ == "__main__":
    for r in sogou_search("OpenAI GPT-4o", 3):
        print(r)
