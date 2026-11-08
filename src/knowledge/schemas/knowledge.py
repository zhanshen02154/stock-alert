from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """知识库检索片段"""

    chunk_id: str = Field(default="", description="片段ID")
    source: str = Field(default="", description="文档名称")
    version: str = Field(default="unknown", description="文档版本")
    chapter_path: str = Field(default="", description="章节路径")
    content: str = Field(default="", description="片段内容")
    score: float = Field(default=0.0, description="检索得分")


class KnowledgeSearchOutput(BaseModel):
    """知识库检索结果"""

    query: str = Field(default="", description="检索问题")
    chunks: list[KnowledgeChunk] = Field(default_factory=list, description="检索片段")
    total: int = Field(default=0, description="片段总数")
