import os
import re
from dataclasses import dataclass
from enum import Enum

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

__headers_to_split_on = [
    ("#", "document_title"),
    ("##", "main_title"),
    ("###", "secondary_heading"),
    ("####", "tertiary_heading"),
]


class ContentType(Enum):
    """
    内容类型枚举，用于识别不同类型的文档内容并采用相应的分割策略

    枚举值说明：
    - CALCULATION: 计算逻辑类，如公式、计算步骤、算法说明等
    - FLOW_DEFINITION: 流程定义类，如状态机、审批流程、操作步骤等
    - TABLE_ENUM: 表格枚举类，如术语表、维度表、状态表等
    - SINGLE_RULE: 单一规则类，如独立条款、规则说明等
    - TABLE_OF_CONTENT: 目录类（预留）
    """

    CALCULATION = "calculation"
    FLOW_DEFINITION = "flow_definition"
    TABLE_ENUM = "table_enum"
    SINGLE_RULE = "single_rule"
    TABLE_OF_CONTENT = "table_of_content"


@dataclass
class ChunkMetadata:
    """
    Chunk 元数据数据类，用于存储分割后块的元信息

    属性说明：
    - content_type: 内容类型
    - chapter_path: 章节路径，如"文档 > 章节 > 子章节"
    - chunk_index: 当前块在章节内的索引
    - total_chunks: 当前章节的总块数
    """

    content_type: ContentType
    chapter_path: str
    chunk_index: int
    total_chunks: int


def _detect_content_type(heading: str, content: str) -> ContentType:
    """
    根据标题和内容自动识别文档内容类型

    识别规则优先级：
    1. 表格枚举类：标题含"表"/"术语"/"维度"，或内容含表格分隔符（优先检测，避免被其他类型误判）
    2. 计算逻辑类：标题含"计算"/"公式"，或内容含计算相关关键词
    3. 流程定义类：标题含"流程"/"状态"/"阶段"/"审批"
    4. 单一规则类：短文本（<500字符）且含句号结尾、列表或加粗格式

    :param heading: 标题文本
    :param content: 内容文本
    :return: ContentType 枚举值，表示识别出的内容类型
    """
    heading_lower = heading.lower()
    content_lower = content.lower()

    if "表" in heading or "| " in content or "术语" in heading or "维度" in heading:
        return ContentType.TABLE_ENUM

    if (
        "计算" in heading
        or "公式" in heading
        or any(
            kw in content_lower
            for kw in ["计算公式", "安全库存 =", "日均销量 =", "建议补货量"]
        )
    ):
        return ContentType.CALCULATION

    if "流程" in heading or "状态" in heading or "阶段" in heading or "审批" in heading:
        return ContentType.FLOW_DEFINITION

    if len(content) < 500 and (
        "。\n" in content or "\n-" in content or "**" in content
    ):
        return ContentType.SINGLE_RULE

    return ContentType.SINGLE_RULE


def _split_by_semantic_boundaries(content: str, content_type: ContentType) -> list[str]:
    """
    根据内容类型选择相应的语义分割策略

    :param content: 待分割的文本内容
    :param content_type: 内容类型枚举值
    :return: 分割后的字符串列表
    """
    if content_type == ContentType.CALCULATION:
        return _split_calculation_chunks(content)
    elif content_type == ContentType.FLOW_DEFINITION:
        return _split_flow_chunks(content)
    elif content_type == ContentType.TABLE_ENUM:
        return _split_table_chunks(content)
    else:
        return _split_single_rule_chunks(content)


def _split_calculation_chunks(content: str) -> list[str]:
    """
    计算逻辑类内容的语义分割策略

    按编号列表（如"1. xxx"）进行分割，同时保持最小块大小（100字符），
    避免产生过细的碎片化内容。

    :param content: 待分割的计算逻辑类文本
    :return: 分割后的字符串列表
    """
    separators = [
        r"(?=\n\d+\. )",
    ]
    chunks = [content]
    min_chunk_size = 100

    for sep in separators:
        new_chunks = []
        for chunk in chunks:
            parts = re.split(sep, chunk)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if len(p) > min_chunk_size:
                    new_chunks.append(p)
                else:
                    if new_chunks and len(new_chunks[-1]) < min_chunk_size:
                        new_chunks[-1] = new_chunks[-1] + "\n" + p
                    else:
                        new_chunks.append(p)
        if len(new_chunks) > len(chunks):
            chunks = new_chunks
    return chunks if len(chunks) > 1 else [content]


def _split_flow_chunks(content: str) -> list[str]:
    """
    流程定义类内容的语义分割策略

    按编号列表（如"1. xxx"）进行分割，同时保持最小块大小（120字符），
    确保每个块包含完整的流程步骤描述。

    :param content: 待分割的流程定义类文本
    :return: 分割后的字符串列表
    """
    separators = [
        r"(?=\n\d+\. )",
    ]
    chunks = [content]
    for sep in separators:
        new_chunks = []
        for chunk in chunks:
            parts = re.split(sep, chunk)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if len(p) > 120:
                    new_chunks.append(p)
                else:
                    if new_chunks and len(new_chunks[-1]) < 120:
                        new_chunks[-1] = new_chunks[-1] + "\n" + p
                    else:
                        new_chunks.append(p)
        if len(new_chunks) > len(chunks):
            chunks = new_chunks
    return chunks if len(chunks) > 1 else [content]


def _split_table_chunks(content: str) -> list[str]:
    """
    表格枚举类内容的语义分割策略

    使用正则表达式匹配 Markdown 表格格式，保持表格结构的完整性。
    如果内容中包含多个表格，则分别返回；否则返回原始内容。

    :param content: 待分割的表格枚举类文本
    :return: 分割后的字符串列表（每个表格为一个元素）
    """
    table_pattern = r"(\|[^\n]+\|\n?)+"
    tables = re.findall(table_pattern, content)
    if len(tables) <= 1:
        return [content]
    return [t.strip() for t in tables if t.strip()]


def _split_single_rule_chunks(content: str) -> list[str]:
    """
    单一规则类内容的语义分割策略

    保持内容原样不分割，确保规则条款的完整性和独立性。

    :param content: 待分割的单一规则类文本
    :return: 包含原始内容的单元素列表
    """
    return [content]


def _build_chapter_path(metadata: dict) -> str:
    """
    根据元数据构建章节路径字符串

    将文档标题、一级标题、二级标题、三级标题组合成"文档 > 章节 > 子章节"的格式，
    用于标识每个Chunk在文档中的层级位置。

    :param metadata: 包含标题信息的元数据字典
    :return: 章节路径字符串
    """
    parts = []
    if metadata.get("document_title"):
        parts.append(metadata["document_title"].replace("#", "").strip())
    if metadata.get("main_title"):
        parts.append(metadata["main_title"].replace("##", "").strip())
    if metadata.get("secondary_heading"):
        parts.append(metadata["secondary_heading"].replace("###", "").strip())
    if metadata.get("tertiary_heading"):
        parts.append(metadata["tertiary_heading"].replace("####", "").strip())
    return " > ".join(parts) if parts else "未知章节"


def _estimate_chinese_chars(text: str) -> int:
    """
    估算文本中的中文字符数量

    使用正则表达式替换法：中文字符替换为"好"（1字符），英文字符替换为空，
    通过计算替换后的字符串长度来估算中文字符数量。

    :param text: 待估算的文本
    :return: 估算的中文字符数量
    """
    return len(
        re.sub(
            r"[\u0000-\u007F\u4e00-\u9fff]",
            lambda m: "好" if "\u4e00" <= m.group() <= "\u9fff" else "",
            text,
        )
    )


def _should_split_by_size(content: str, chunk_size: int) -> bool:
    """
    判断内容是否需要按大小进行二次分割

    :param content: 待判断的文本内容
    :param chunk_size: 允许的最大字符数
    :return: True表示需要分割，False表示不需要
    """
    char_count = _estimate_chinese_chars(content)
    return char_count > chunk_size


def _safe_split_large_chunk(
    chunk: Document, chunk_size: int, overlap: int, min_chunk_size: int = 50
) -> list[Document]:
    """
    安全分割超大Chunk，确保不超过指定的最大字符数

    采用多级分隔符策略，按优先级尝试不同的分隔符：
    1. 优先按段落分隔（换行符）
    2. 其次按句子分隔（句号、感叹号、问号）
    3. 最后按逗号、空格分隔

    同时支持：
    - 相邻Chunk之间保留重叠内容（overlap）
    - 末尾过小的Chunk会合并到前一个Chunk

    :param chunk: 待分割的Document对象
    :param chunk_size: 单个Chunk的最大字符数
    :param overlap: 相邻Chunk之间的重叠字符数
    :param min_chunk_size: 最小Chunk大小，小于此值会合并到前一个Chunk（默认50）
    :return: 分割后的Document列表
    """
    text = chunk.page_content
    separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

    all_splits = []
    for sep in separators:
        splits = text.split(sep)
        if len(splits) > 1:
            all_splits = splits
            break

    if not all_splits:
        return [chunk]

    chunks = []
    current = ""
    current_size = 0

    for i, part in enumerate(all_splits):
        part_size = _estimate_chinese_chars(part)
        if current_size + part_size > chunk_size and current:
            chunks.append(
                Document(page_content=current.strip(), metadata=chunk.metadata.copy())
            )
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current = overlap_text + part
            current_size = part_size
        else:
            current += part
            current_size += part_size

    if current.strip():
        if chunks and _estimate_chinese_chars(current.strip()) < min_chunk_size:
            chunks[-1] = Document(
                page_content=(chunks[-1].page_content + "\n" + current.strip()).strip(),
                metadata=chunks[-1].metadata.copy(),
            )
        else:
            chunks.append(
                Document(page_content=current.strip(), metadata=chunk.metadata.copy())
            )

    return chunks if chunks else [chunk]


def split_markdown_hierarchical(
    file_path: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[Document]:
    """
    层次化语义分割策略：
    1. 按 Markdown 标题结构解析，保留层级元数据
    2. 根据内容类型（计算逻辑、流程定义、表格枚举、单一规则）选择不同的语义边界分割
    3. 对过大的 Chunk 进行二次分割

    :param file_path: Markdown 文件路径
    :param chunk_size: 每个 Chunk 的最大字符数（默认 800）
    :param overlap: 相邻 Chunk 之间的重叠字符数（默认 100）
    :return: 分割后的 Document 列表
    """
    if file_path == "":
        raise ValueError("File path is empty")
    if not file_path.endswith(".md"):
        raise ValueError("File must be a markdown file")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file=file_path, encoding="utf8", mode="r") as file:
        content = file.read()

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=__headers_to_split_on
    )
    header_docs = markdown_splitter.split_text(content)

    result_chunks: list[Document] = []
    chapter_counter: dict[str, int] = {}

    for doc in header_docs:
        heading = doc.metadata.get("secondary_heading") or doc.metadata.get(
            "main_title", ""
        )
        content_type = _detect_content_type(heading, doc.page_content)

        semantic_chunks = _split_by_semantic_boundaries(doc.page_content, content_type)

        chapter_path = _build_chapter_path(doc.metadata)

        for i, chunk_text in enumerate(semantic_chunks):
            if not chunk_text.strip():
                continue

            metadata = doc.metadata.copy()
            metadata["content_type"] = content_type.value
            metadata["chapter_path"] = chapter_path
            metadata["content_idx"] = i

            if _should_split_by_size(chunk_text, chunk_size):
                sub_chunk = Document(page_content=chunk_text, metadata=metadata)
                sub_chunks = _safe_split_large_chunk(sub_chunk, chunk_size, overlap)
                result_chunks.extend(sub_chunks)
            else:
                result_chunks.append(
                    Document(page_content=chunk_text, metadata=metadata)
                )

    for chunk in result_chunks:
        path = chunk.metadata.get("chapter_path", "")
        if path not in chapter_counter:
            chapter_counter[path] = 0
        chapter_counter[path] += 1
        chunk.metadata["chunk_seq"] = chapter_counter[path]

    for chunk in result_chunks:
        path = chunk.metadata.get("chapter_path", "")
        chunk.metadata["total_in_chapter"] = chapter_counter.get(path, 1)

    return result_chunks


def split_markdown(file_path: str) -> list[Document]:
    """
    按 Markdown 标题分割文档（保留层级元数据）

    :param file_path: markdown文件路径
    :return: 分割后的Document列表
    """
    if file_path == "":
        raise ValueError("File path is empty")
    if not file_path.endswith(".md"):
        raise ValueError("File must be a markdown file")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file=file_path, encoding="utf8", mode="r") as file:
        content = file.read()
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=__headers_to_split_on
        )
        return markdown_splitter.split_text(content)


def split_markdown_with_size(
    file_path: str, chunk_size: int = 250, chunk_overlap: int = 30
) -> list[Document]:
    """
    按标题分割markdown文件后，再按chunk_size限制块大小进行二次分割

    :param file_path: markdown文件路径
    :param chunk_size: 每个块的最大字符数，默认250
    :param chunk_overlap: 块之间的重叠字符数，默认30
    :return: 分割后的Document列表
    """
    header_documents = split_markdown(file_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    documents = text_splitter.split_documents(header_documents)
    return documents
