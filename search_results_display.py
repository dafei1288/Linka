import streamlit as st

def display_search_results(search_results):
    """Displays the search results in an expander."""
    if search_results:
        with st.expander("🔎 展开/收起全部搜索结果", expanded=False):
            st.write("### 搜索结果")
            for idx, (title, url, snippet) in enumerate(search_results):
                st.markdown(f"**[{idx+1}] [{title}]({url})**")
                st.markdown(f"**链接：** [{url}]({url})")
