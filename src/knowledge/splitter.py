import os

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

__headers_to_split_on = [
    ("#", "document_title"),
    ("##", "main_title"),
    ("###", "secondary_heading"),
]


def split_markdown(file_path: str) -> list[Document]:
    """
    文档路径
    :param file_path: markdown文件路径
    :return: 分割后的Document列表
    """
    try:
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
    except Exception as e:
        raise e


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
    # 先按标题分割
    header_documents = split_markdown(file_path)

    # 再按chunk_size限制块大小进行二次分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    documents = text_splitter.split_documents(header_documents)
    return documents
