import asyncio
import os
from html2md import convert_url_to_markdown
from web_search.duckduckgo_search import search_duckduckgo

def fetch_and_convert(url, add_frontmatter=True, analyze_images=False):
    return convert_url_to_markdown(
        url,
        provider="guiji",
        api_key=os.getenv("GUIJI_API_KEY"),
        base_url=os.getenv("GUIJI_BASE_URL"),
        analyze_images=analyze_images,
        add_frontmatter=add_frontmatter,
    )


async def fetch_and_convert_async(url, add_frontmatter=True, analyze_images=False, session=None):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None, lambda: fetch_and_convert(url, add_frontmatter=add_frontmatter, analyze_images=analyze_images)
        )
    except Exception:
        return None

def process_search_and_content(query, max_results=10, proxies=None, user_agent=None, analyze_images=False):
    """并发抓取内容，无法获取的直接用搜索body。"""
    results = search_duckduckgo(
        query, max_results=max_results, proxies=proxies, user_agent=user_agent
    )
    search_summaries = []
    urls = []
    bodies = []
    for idx, r in enumerate(results):
        url = r.get("href") or r.get("url")
        title = r.get("title")
        snippet = r.get("body") or r.get("snippet")
        search_summaries.append((title, url, snippet))
        urls.append(url)
        bodies.append(snippet)

    async def batch_fetch():
        tasks = [fetch_and_convert_async(url, add_frontmatter=False, analyze_images=analyze_images) if url else None for url in urls]
        return await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    md_results = loop.run_until_complete(batch_fetch())
    answer_blocks = []
    for idx, md in enumerate(md_results):
        url = urls[idx]
        if md and md.strip():
            answer_blocks.append((md, url))
        else:
            # 用原始body作为兜底内容
            answer_blocks.append((bodies[idx] or "", url))
    return search_summaries, answer_blocks
