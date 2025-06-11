\
"""
提示词处理工具函数
"""

def format_query_with_references(query: str, answer_blocks: list) -> str:
    """
    将用户问题和参考内容块格式化为最终的提示词。

    参数:
        query (str): 用户提出的问题。
        answer_blocks (list): 包含(正文, url)元组的列表。

    返回:
        str: 格式化后的完整提示词。
    """
    ref_content = ""
    for idx, (md, url) in enumerate(answer_blocks):
        ref_content += (
            f"【第{idx+1}篇参考文章开始】\n[{idx+1}] 原文链接: {url}\n"
            + md
            + f"\n【第{idx+1}篇参考文章结束】\n"
        )
    prompt = f"用户问题：{query}\n\n参考内容如下（可以从里面选择合适的图片输出，增强与用户的交互效果）：\n{ref_content}"
    # with open("prompt.md", "w", encoding="utf-8") as f:
    #     f.write(prompt)
    return prompt

def get_system_prompt() -> str:
    """
    获取用于RAG模型的系统提示词。

    返回:
        str: 系统提示词字符串。
    """
    return (
        "你是一个专业的中文智能助手。你只能参考下方提供的内容（包括文本和图片），结合自己的知识，回答用户问题。"
        "回答正文中如有引用内容，请用[1][2]等角标标注。"
        "回答最后请以'参考文章：'的形式，列出你用到的文章编号和对应链接，格式如：\\n参考文章：\\n[1] 链接1\\n[2] 链接2。"  
        "如果没有参考任何文章，可以省略该部分。"
        "如果参考内容里面没有正确答案，那么就回答用户我不知道即可。"
        "不要输出任何参考内容以外的内容。"
    )
