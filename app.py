import streamlit as st
from duckduckgo_search import DDGS
from html2md import convert_url_to_markdown
import os
import openai
import requests
import asyncio
import concurrent.futures


st.set_page_config(page_title="联网搜索对话系统", layout="wide")
st.title("🔎 联网搜索对话系统 ")

# Sidebar options
st.sidebar.title("配置选项")
analyze_images_enabled = st.sidebar.checkbox("开启图片分析", value=False)
if st.sidebar.button("清空对话记录", use_container_width=True):
    st.session_state["history"] = []
    st.session_state["search_results"] = []


def search_duckduckgo(query, max_results=3, proxies=None, user_agent=None):
    ddgs = DDGS()
    # 通过requests自定义user-agent和代理
    headers = {
        "User-Agent": user_agent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    results = []
    for r in ddgs.text(query, max_results=max_results):
        # 这里可以用requests.head测试代理和user-agent
        try:
            requests.head(
                r.get("href") or r.get("url"),
                headers=headers,
                proxies=proxies,
                timeout=3,
            )
        except Exception:
            pass
        results.append(r)
    return results


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


def call_guiji_rag_model(query, answer_blocks):
    guiji_api_key = os.getenv("GUIJI_API_KEY")
    guiji_base_url = os.getenv("GUIJI_BASE_URL")
    guiji_model = os.getenv("GUIJI_TEXT_MODEL")
    prompt = f"用户问题：{query}\n\n参考内容（可包含图片）：\n" + "\n\n".join(
        answer_blocks
    )
    openai.api_key = guiji_api_key
    openai.base_url = guiji_base_url
    response = openai.chat.completions.create(
        model=guiji_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的中文智能助手。你可以参考下方提供的内容（包括文本和图片），结合自己的知识，回答用户问题。你可以引用参考内容中的图片（以Markdown格式输出）来增强你的回答效果。回答时请尽量引用有用的内容和图片，提升交互体验。",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096
    )
    return response.choices[0].message.content


def call_guiji_rag_model_stream(query, answer_blocks, _, chat_history=None):
    client = openai.OpenAI(
        api_key=os.getenv("GUIJI_API_KEY"), base_url=os.getenv("GUIJI_BASE_URL")
    )
    guiji_model = os.getenv("GUIJI_TEXT_MODEL")
    # 拼接参考内容，每篇用【第n篇参考文章开始】和【第n篇参考文章结束】包围，前缀加[编号]
    ref_content = ""
    for idx, md in enumerate(answer_blocks):
        ref_content += (
            f"【第{idx+1}篇参考文章开始】\n[${idx+1}]\n"
            + md
            + f"\n【第{idx+1}篇参考文章结束】\n"
        )
    prompt = f"用户问题：{query}\n\n参考内容如下（可包含图片）：\n{ref_content}"
    sys_prompt = (
        "你是一个专业的中文智能助手。你只能参考下方提供的内容（包括文本和图片），结合自己的知识，回答用户问题。"
        "回答正文中如有引用内容，请用[1][2]等角标标注。"
        "回答最后请以'参考文章：'的形式，列出你用到的文章编号和对应链接，格式如：\n参考文章：\n[1] 链接1\n[2] 链接2。"
        "如果没有参考任何文章，可以省略该部分。"
        "请严格不要将【第n篇参考文章开始】和【第n篇参考文章结束】外的内容当作参考资料。"
        "如果参考内容里面没有正确答案，那么就回答用户我不知道即可。"
        "不要输出任何参考内容以外的内容。"
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt},
    ]
    if chat_history:
        # 将历史记录拼接到消息中
        for chat in chat_history:
            messages.insert(-1, chat)  # 在倒数第二个位置插入，保持用户问题在最后

    response = client.chat.completions.create(
        model=guiji_model, messages=messages, stream=True, max_tokens=4096
    )
    return response


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
        tasks = [fetch_and_convert_async(url, add_frontmatter=True, analyze_images=analyze_images) if url else None for url in urls]
        return await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    md_results = loop.run_until_complete(batch_fetch())
    answer_blocks = []
    for idx, md in enumerate(md_results):
        if md and md.strip():
            answer_blocks.append(md)
        else:
            # 用原始body作为兜底内容
            answer_blocks.append(bodies[idx] or "")
    return search_summaries, answer_blocks


# 搜索输入框
query = st.text_input("请输入你的问题或关键词：", "OpenAI GPT-4o 有哪些新特性？")

# 聊天历史与输入框（使用st.chat_message和st.chat_input实现原生ChatGPT体验）
if "history" not in st.session_state:
    st.session_state["history"] = []
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

for msg in st.session_state["history"]:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

user_input = st.chat_input("请输入你的问题...")

if user_input and user_input.strip():
    st.session_state["history"].append({"role": "user", "content": user_input.strip()})
    proxies = None  # 例如{"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    with st.status("正在联网搜索和处理内容，请稍候...", expanded=True) as status:
        try:
            status.write("🔍 正在进行 DuckDuckGo 搜索...")
            search_summaries, answer_blocks = process_search_and_content(
                user_input, proxies=proxies, user_agent=user_agent, analyze_images=analyze_images_enabled
            )
            st.session_state["search_results"] = search_summaries           
            status.write(f"✅ 搜索完成，共{len(search_summaries)}条结果。")
            if answer_blocks:
                status.write("🤖 正在调用大模型流式生成回答...")
                chat_history = st.session_state["history"][-5:]
                response = call_guiji_rag_model_stream(
                    user_input, answer_blocks, None, chat_history
                )
                full_answer = ""
                with st.chat_message("assistant"):
                    stream_placeholder = st.empty()
                    for chunk in response:
                        delta = (
                            chunk.choices[0].delta.content
                            if chunk.choices[0].delta
                            else ""
                        )
                        if delta:
                            full_answer += delta
                            stream_placeholder.markdown(full_answer)
                st.session_state["history"].append(
                    {"role": "assistant", "content": full_answer}
                )
                status.write("✅ 回答生成完毕！")
        except Exception as e:
            st.error(f"搜索或内容抓取失败: {e}")
            status.write("❌ 搜索或内容抓取失败")    # 在status容器外部显示搜索结果
if st.session_state.get("search_results"):
    with st.expander("🔎 展开/收起全部搜索结果", expanded=False):
        st.write("### 搜索结果")
        for idx, (title, url, snippet) in enumerate(st.session_state["search_results"]):
            st.markdown(f"**[{idx+1}] [{title}]({url})**")
            st.markdown(f"**链接：** [{url}]({url})")
            # if snippet:
            #     st.markdown(f"**摘要：** {snippet}")
