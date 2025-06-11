import streamlit as st
from search_results_display import display_search_results
from search_processing import process_search_and_content 
from prompt_utils import format_query_with_references, get_system_prompt # 导入 get_system_prompt
import os
import openai



st.set_page_config(page_title="联网搜索对话系统", layout="wide")
st.title("🔎 联网搜索对话系统 ")

st.sidebar.title("配置选项")
analyze_images_enabled = st.sidebar.checkbox("开启图片分析", value=False)
if st.sidebar.button("清空对话记录", use_container_width=True):
    st.session_state["history"] = []
    st.session_state["search_results"] = []



def call_guiji_rag_model_stream(query, answer_blocks, _, chat_history=None):
    client = openai.OpenAI(
        api_key=os.getenv("GUIJI_API_KEY"), base_url=os.getenv("GUIJI_BASE_URL")
    )
    guiji_model = os.getenv("GUIJI_TEXT_MODEL")
    # 拼接参考内容
    prompt = format_query_with_references(query, answer_blocks)
    sys_prompt = get_system_prompt() # 调用函数获取系统提示词
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
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    with st.status("正在联网搜索和处理内容，请稍候...", expanded=True) as status:
        try:
            status.write("🔍 正在进行 DuckDuckGo 搜索...")
            search_summaries, answer_blocks = process_search_and_content(
                user_input, user_agent=user_agent, analyze_images=analyze_images_enabled
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
display_search_results(st.session_state.get("search_results"))

