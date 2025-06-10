# Linka - 联网搜索对话系统

Linka 是一个基于 Streamlit 构建的联网搜索对话系统。它能够接收用户输入的问题，通过搜索引擎获取相关信息，对网页内容进行处理（包括可选的图片内容分析），并利用大型语言模型（LLM）生成综合性的回答。

## 主要功能

* **联网搜索**：支持通过 DuckDuckGo（默认）或搜狗搜索引擎（代码中包含实现）进行实时网络搜索。
* **内容提取与转换**：能够从搜索到的网页链接中提取主要内容，并将其转换为 Markdown 格式。
* **图片分析（可选）**：集成了图片分析功能，可以识别网页中的图片内容，并生成描述，丰富回答的信息维度。支持多种图片分析服务商（如智谱、硅基等）。
* **RAG 对话模型**：利用检索增强生成（RAG）技术，结合搜索到的上下文信息，通过大型语言模型（本项目中配置为调用类似 OpenAI API 规范的“硅基”模型）生成更准确、更相关的回答。
* **Streamlit Web 界面**：提供一个用户友好的 Web 界面，方便用户输入问题、查看搜索结果和模型的回答，并支持清空对话历史。
* **异步处理**：在内容获取和图片分析等环节采用异步处理，提升应用性能和响应速度。

## 技术栈

* **Python**: 主要编程语言。
* **Streamlit**: 用于构建交互式 Web 应用界面。
* **DuckDuckGo Search (`duckduckgo-search`)**: 用于执行网络搜索。
* **Requests**: 用于发起 HTTP 请求获取网页内容。
* **Trafilatura**: 用于提取网页正文内容。
* **Markdownify**: 用于将 HTML 内容转换为 Markdown 格式。
* **OpenAI Python Library (接口规范)**: 用于与符合 OpenAI API 规范的大型语言模型（如本项目配置的硅基模型）进行交互，包括文本生成和图片理解。
* **Beautiful Soup (`bs4`)**: 用于解析 HTML 内容（在搜狗搜索和部分 Markdown 转换逻辑中使用）。
* **Python-dotenv**: 用于管理环境变量（如 API 密钥）。
* **Asyncio**: 用于实现异步编程，提高 I/O 密集型操作的效率。

## 项目结构

```text
Linka/
├── app.py                      # Streamlit 应用主程序
├── html2md.py                  # HTML 到 Markdown 转换及图片分析核心逻辑
├── requirements.txt            # Python 依赖包列表
├── README.md                   # 项目说明文件
├── image_utils/
│   └── async_image_analysis.py # 异步图片分析模块
├── web_search/
│   ├── __init__.py
│   ├── duckduckgo_search.py    # DuckDuckGo 搜索模块
│   └── sogou_search.py         # 搜狗搜索模块 (代码中提供，app.py 未直接使用)
├── tests/
│   └── custom_convert.py       # 自定义 Markdown 转换器的测试或早期版本
└── __pycache__/                # Python 编译的缓存文件
```

## 安装与运行

1. **克隆项目** (如果项目在版本控制中)

   ```bash
   git clone https://github.com/li-xiu-qi/Linka.git
   cd Linka
   ```

2. **创建并激活虚拟环境** (推荐)

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   项目需要配置 API 密钥等敏感信息。创建一个 `.env` 文件在项目根目录，并填入必要的环境变量，例如：

   ```env
   GUIJI_API_KEY="YOUR_GUIJI_API_KEY"
   GUIJI_BASE_URL="YOUR_GUIJI_API_BASE_URL"
   GUIJI_TEXT_MODEL="YOUR_GUIJI_TEXT_MODEL_NAME"
   GUIJI_VISION_MODEL="YOUR_GUIJI_VISION_MODEL_NAME"

   # 如果使用其他图片分析服务商，也需要配置相应的 KEY 和 URL
   # ZHIPU_API_KEY="YOUR_ZHIPU_API_KEY"
   # ZHIPU_BASE_URL="YOUR_ZHIPU_BASE_URL"
   # ZHIPU_VISION_MODEL="YOUR_ZHIPU_VISION_MODEL_NAME"
   ```

   请根据 `image_utils/async_image_analysis.py` 和 `app.py` 中的配置，填写实际使用的服务商和模型信息。

5. **运行 Streamlit 应用**

   ```bash
   streamlit run app.py
   ```

   应用将在本地启动，并在浏览器中打开。

## 使用说明

1. 打开应用后，在侧边栏可以选择是否“开启图片分析”。
2. 在主界面的输入框中输入你的问题或关键词。
3. 点击下方的聊天输入框发送问题。
4. 系统会进行联网搜索，处理内容，并调用大模型生成回答。
5. 回答和搜索结果会显示在界面上。
6. 可以通过侧边栏的“清空对话记录”按钮清除当前的对话历史和搜索结果。

## 注意事项

* 确保已正确配置所需的 API 密钥和模型名称等环境变量。
* 网络连接是必需的，因为系统需要实时搜索信息。
* 图片分析功能依赖于所选服务商的 API 能力和可用性。
* 如果遇到 `ProxyError` 或网络访问问题，可能需要在代码中（例如 `app.py` 的 `process_search_and_content` 函数内）配置代理服务器。

## 未来可改进方向

* 支持更多的搜索引擎。
* 优化内容提取和 Markdown 转换的准确性。
* 提供更多的模型配置选项。
* 增强错误处理和用户反馈机制。
* 添加更详细的日志记录。
