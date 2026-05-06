# CLAUDE.md

# splitter.py
文本分割器，主要用于将Markdown文档分割为语义完整的文档，支持按结构和语义分割，以及按字符数分割文档，同时考虑了文档的标题层级和内容类型， 以确保分割后的文档保持语义的连贯性， 并且每个文档的字符数在指定范围内， 以适应不同的应用需求，如文本检索、 文本分类、 文本摘要等。
- split_markdown_hierarchical：按结构和语义分割文档
┌─────────────────────────────────────────────────────────────┐
│  split_markdown_hierarchical()                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. MarkdownHeaderTextSplitter 解析标题层级                  │
│     ↓ 生成 header_docs (按 # / ## / ### 分段)               │
│                                                             │
│  2. 遍历每个 header_doc                                     │
│     ↓                                                       │
│     ├─ _detect_content_type() 识别内容类型                   │
│     │                                                        │
│     ├─ _split_by_semantic_boundaries() 按语义分割           │
│     │   ├─ CALCULATION → _split_calculation_chunks()       │
│     │   ├─ FLOW_DEFINITION → _split_flow_chunks()         │
│     │   ├─ TABLE_ENUM → _split_table_chunks()              │
│     │   └─ SINGLE_RULE → _split_single_rule_chunks()        │
│     │                                                        │
│     └─ 对每个语义 chunk：                                     │
│         ├─ 未超限 → 直接加入结果                             │
│         └─ 超限(>800字符) → _safe_split_large_chunk()       │
│                                                             │
│  3. 编号 chunk_seq 和 total_in_chapter                      │
│                                                             │
│  输出: result_chunks (16个语义完整的 Document)               │
└─────────────────────────────────────────────────────────────┘
- split_markdown：按结构和语义分割文档
- split_text：按字符数分割文本
- split_by_semantic_boundaries：按语义边界分割文本

# vector.py
向量数据库，主要用于存储和检索向量表示的文档，支持向量相似度搜索， 以实现基于向量的文档检索和推荐。
- MilvusManager：向量数据库管理类，用于初始化、 连接、 创建集合、 插入向量、 搜索向量等操作

# retriever.py
文档检索器，主要用于根据用户查询， 从向量数据库中检索最相关的文档， 并返回检索结果。
- BaseKnowledgeRetriever：基础文档检索器类，用于初始化
