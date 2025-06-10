from markdownify import MarkdownConverter, abstract_inline_conversion, chomp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import asyncio
import os
from typing import Optional
from image_utils.async_image_analysis import AsyncImageAnalysis

class CustomMarkdownConverter(MarkdownConverter):
    """
    自定义Markdown转换器，继承自MarkdownConverter。
    提供了更灵活的HTML到Markdown转换选项，例如：
    - 转换链接为绝对路径。
    - 移除所有链接和图片。
    - 特殊处理包含colspan或rowspan的表格。    """
    def __init__(self, current_url: str | None = None,
                 image_analyzer_provider: Optional[str] = None,
                 image_analyzer_api_key: Optional[str] = None,
                 image_analyzer_base_url: Optional[str] = None,
                 image_analyzer_vision_model: Optional[str] = None,
                 **kwargs):
        """
        初始化自定义的Markdown转换器。

        :param current_url: 当前页面的URL，用于将相对链接和图片路径转换为绝对路径。
                            如果提供了此参数，图片和链接的URL将自动转换为绝对路径。
        :param image_analyzer_provider: 图像分析服务提供商（如 'zhipu', 'guiji', 'volces', 'openai'）
        :param image_analyzer_api_key: 图像分析服务的API密钥
        :param image_analyzer_base_url: 图像分析服务的基础URL
        :param image_analyzer_vision_model: 图像分析使用的视觉模型
        :param kwargs: 其他传递给父类MarkdownConverter的参数。
                       例如：strip (需要移除的标签列表), convert (仅转换的标签列表), heading_style等。
        """
       
        super().__init__(**kwargs)
        
        self.current_url = current_url # 存储当前URL，用于路径转换
        
        # 初始化图像分析器
        self.image_analyzer = None
        if image_analyzer_provider:
            # 优先使用传入参数，否则从环境变量读取
            api_key = image_analyzer_api_key or os.getenv(f"{image_analyzer_provider.upper()}_API_KEY")
            base_url = image_analyzer_base_url or os.getenv(f"{image_analyzer_provider.upper()}_BASE_URL")
            vision_model = image_analyzer_vision_model or os.getenv(f"{image_analyzer_provider.upper()}_MODEL")
            try:
                self.image_analyzer = AsyncImageAnalysis(
                    provider=image_analyzer_provider,
                    api_key=api_key,
                    base_url=base_url,
                    vision_model=vision_model
                )
            except Exception as e:
                print(f"警告：无法初始化图像分析器: {e}")
                self.image_analyzer = None

    def convert_img(self, el, text, parent_tags):
        """
        转换<img>标签为Markdown格式的图片。
        如果提供了current_url，则将图片src转换为绝对路径。
        如果配置了图像分析器，将尝试分析图片并生成描述性的标题和描述（仅限远程URL）。

        :param el: BeautifulSoup的Tag对象，代表<img>元素。
        :param text: 图片的替代文本（通常为空，因为alt属性会被单独提取）。
        :param parent_tags: 父标签集合，用于判断上下文。
        :return: Markdown格式的图片字符串，或者在特定情况下返回alt文本或空字符串。
        """
        alt_text = el.attrs.get('alt', '') or ''
        src_url = el.attrs.get('src', '') or ''
        title_text = el.attrs.get('title', '') or ''
        
        if ('_inline' in parent_tags
                and el.parent.name not in self.options['keep_inline_images_in']):
            return alt_text

        if not src_url:
            return alt_text

        # 转换为绝对路径
        if self.current_url:
            src_url = urljoin(self.current_url, src_url)

        # 尝试使用图像分析器 - 仅限远程 URL
        if self.image_analyzer and src_url and src_url.startswith(('http://', 'https://')):
            try:
                analysis_result = asyncio.run(
                    self.image_analyzer.analyze_image(image_url=src_url)
                )
                if analysis_result and not analysis_result.get('error'):
                    analyzed_title = analysis_result.get('title', alt_text or '图片')
                    analyzed_description = analysis_result.get('description', '')
                    markdown_output = f'![{analyzed_title}]({src_url})'
                    if analyzed_description:
                        description_lines = analyzed_description.strip().split('\n')
                        formatted_description = '\n'.join(f'> {line}' for line in description_lines)
                        markdown_output += f'\n{formatted_description}'
                    return markdown_output
            except Exception as e:
                print(f"图像分析失败: {e}")
                # 分析失败，继续使用默认逻辑

        if title_text:
            escaped_title = title_text.replace('"', r'\"')
            title_part = f' "{escaped_title}"'
        else:
            title_part = ''
        return f'![{alt_text}]({src_url}{title_part})'

    def _process_table_element(self, element):
        """
        辅助方法：处理包含colspan或rowspan属性的表格元素（td, th）。
        此方法会解析传入的表格元素字符串，并移除除了'colspan'和'rowspan'之外的所有属性。
        目的是在保留表格结构的同时，简化HTML，以便后续可能由其他工具或手动进行更复杂的Markdown转换。

        :param element: BeautifulSoup的Tag对象，代表一个HTML表格元素（如<table>, <tr>, <td>, <th>）。
        :return: 处理后的HTML元素字符串，仅保留colspan和rowspan属性。
        """
        # 使用BeautifulSoup解析传入的元素字符串，确保操作的是一个独立的DOM结构
        soup = BeautifulSoup(str(element), 'html.parser')
        # 遍历soup中的所有标签
        for tag in soup.find_all(True):
            # 定义需要保留的属性列表
            attrs_to_keep = ['colspan', 'rowspan']
            # 更新标签的属性字典，只保留在attrs_to_keep列表中的属性
            tag.attrs = {key: value for key, value in tag.attrs.items() if key in attrs_to_keep}
        # 返回处理后soup的字符串表示形式
        return str(soup)

    def convert_table(self, el, text, parent_tags):
        """
        转换<table>标签为Markdown格式。
        如果表格中的<td>或<th>标签包含colspan或rowspan属性，
        则调用_process_table_element方法返回处理过的HTML字符串（保留结构但简化属性），
        否则，调用父类的convert_table方法进行标准转换。

        :param el: BeautifulSoup的Tag对象，代表<table>元素。
        :param text: 表格的内部文本内容（通常由子元素的转换结果拼接而成）。
        :param parent_tags: 父标签集合，用于判断上下文。
        :return: Markdown格式的表格字符串，或者在包含合并单元格时返回处理后的HTML字符串。
        """
        # 使用BeautifulSoup解析传入的<table>元素字符串
        soup = BeautifulSoup(str(el), 'html.parser')
        # 检查表格中是否存在任何带有colspan或rowspan属性的<td>或<th>标签
        has_colspan_or_rowspan = any(
            tag.has_attr('colspan') or tag.has_attr('rowspan') for tag in soup.find_all(['td', 'th'])
        )
        if has_colspan_or_rowspan:
            # 如果存在合并单元格，则调用_process_table_element处理整个表格元素
            # 返回的是简化属性后的HTML字符串，而不是Markdown
            return self._process_table_element(el)
        else:
            # 如果没有合并单元格，则调用父类的convert_table方法进行标准Markdown转换
            return super().convert_table(el, text, parent_tags)

    def convert_a(self, el, text, parent_tags):
        """
        转换<a>标签（链接）为Markdown格式。
        如果提供了current_url，则将链接href转换为绝对路径。
        处理自动链接（autolinks）和默认标题（default_title）的选项。

        :param el: BeautifulSoup的Tag对象，代表<a>元素。
        :param text: 链接的显示文本。
        :param convert_as_inline: 布尔值，指示是否应将此链接作为内联元素处理。
        :return: Markdown格式的链接字符串，或者在特定情况下返回空字符串。
        """

        
        # 使用chomp函数处理链接文本，分离前导/尾随空格
        prefix, suffix, text = chomp(text)
        if not text:
            # 如果链接文本为空（例如空的<a></a>标签），则返回空字符串
            return ''
        
        # 获取链接的href和title属性
        href_url = el.get('href')
        title_text = el.get('title')

        if self.current_url and href_url:
            # 如果需要将链接href转换为绝对路径
            # 使用urljoin将href_url（可能是相对路径）与current_url合并为绝对路径
            href_url = urljoin(self.current_url, href_url)


        # 处理Markdownify的autolinks选项：如果链接文本和href相同，且无标题，则使用<href>格式
        if (self.options.get('autolinks', False) # 检查autolinks选项是否存在且为True
                and text.replace(r'\_', '_') == href_url # 文本（处理转义的下划线后）与href相同
                and not title_text # 没有title属性
                and not self.options.get('default_title', False)): # default_title选项未开启
            return f'<{href_url}>' # 返回自动链接格式
        
        # 处理Markdownify的default_title选项：如果没有title属性，但开启了default_title，则使用href作为title
        if self.options.get('default_title', False) and not title_text and href_url:
            title_text = href_url

        # 处理链接标题，如果存在，则进行转义并格式化
        if title_text:
            escaped_title = title_text.replace('"', r'\"') # 转义双引号
            title_part = f' "{escaped_title}"' # 格式化为 "title"
        else:
            title_part = '' # 如果没有标题，则为空

        # 返回标准Markdown格式的链接：[text](href_url "title_text")
        # 如果href_url为空或None，则只返回处理过的文本（prefix + text + suffix）
        return f'{prefix}[{text}]({href_url}{title_part}){suffix}' if href_url else f'{prefix}{text}{suffix}'

    # 加粗标签<b>的转换，使用markdownify库提供的abstract_inline_conversion辅助函数
    # self.options['strong_em_symbol'] 通常是 '*' 或 '_'
    # lambda self: 2 * self.options['strong_em_symbol'] 表示使用两个符号包裹文本，例如 **text**
    convert_b = abstract_inline_conversion(lambda self: 2 * self.options.get('strong_em_symbol', '*'))
    
    # 强调标签<em>或<i>的转换，同样使用abstract_inline_conversion
    # lambda self: self.options['strong_em_symbol'] 表示使用一个符号包裹文本，例如 *text*
    convert_em = abstract_inline_conversion(lambda self: self.options.get('strong_em_symbol', '*'))
    convert_i = convert_em # <i>标签通常与<em>行为一致

    # 删除线标签<del>或<s>的转换
    convert_del = abstract_inline_conversion(lambda self: '~~')
    convert_s = convert_del # <s>标签通常与<del>行为一致
