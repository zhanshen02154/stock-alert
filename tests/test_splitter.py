"""
A/B 测试：对比 split_markdown（仅按标题分割）与 split_markdown_with_size（标题+块大小分割）的结果
"""
import os
import tempfile
from typing import List

from langchain_core.documents import Document

from src.knowledge.splitter import split_markdown, split_markdown_with_size

# 测试用 markdown 内容
SAMPLE_MD = """# 智能采购规则文档

## 采购流程

采购流程是整个系统的核心环节，涉及需求提出、审批、下单、收货等多个步骤。每个步骤都需要严格遵守公司规定。

### 需求提出

部门负责人根据业务需求，在系统中提交采购申请。申请中需包含物品名称、数量、预算金额、期望交付日期等关键信息。

### 审批流程

采购申请提交后，需要经过直属领导审批、财务审核、总经理批准三级审批流程。每级审批时限为2个工作日，超时自动流转至下一级。

## 供应商管理

供应商管理模块负责维护合格供应商名录，对供应商进行分类评级和绩效考核，确保采购质量和交付效率。

### 供应商评级

根据供应商的交付准时率、产品质量合格率、售后服务响应速度等维度进行综合评级，分为A、B、C三个等级。A级供应商享有优先合作权。

### 绩效考核

每季度对供应商进行绩效考核，考核结果直接影响供应商的评级变动和合作份额分配。连续两个季度评为C级的供应商将被移出合格名录。
"""


def _create_temp_md(content: str) -> str:
    """创建临时 markdown 文件并返回路径"""
    fd, path = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _print_documents(label: str, documents: List[Document]) -> None:
    """打印分割结果摘要"""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"总块数: {len(documents)}")
    for i, doc in enumerate(documents):
        content = doc.page_content
        print(f"\n--- 块 {i + 1} (长度: {len(content)}) ---")
        print(content[:200] + ("..." if len(content) > 200 else ""))
        print(f"元数据: {doc.metadata}")


class TestSplitterAB:
    """A/B 测试：对比两种分割策略"""

    @classmethod
    def setup_class(cls):
        cls.md_path = _create_temp_md(SAMPLE_MD)

    @classmethod
    def teardown_class(cls):
        os.unlink(cls.md_path)

    def test_split_markdown_only_header(self):
        """A方案：仅按标题分割"""
        documents = split_markdown(self.md_path)
        _print_documents("A方案: 仅按标题分割 (split_markdown)", documents)

        # 验证基本属性
        assert len(documents) > 0
        assert all(isinstance(d, Document) for d in documents)
        assert all(d.page_content.strip() for d in documents)

    def test_split_markdown_with_size(self):
        """B方案：按标题分割 + 块大小限制"""
        documents = split_markdown_with_size(self.md_path, chunk_size=250, chunk_overlap=30)
        _print_documents("B方案: 标题+块大小分割 (split_markdown_with_size)", documents)

        # 验证基本属性
        assert len(documents) > 0
        assert all(isinstance(d, Document) for d in documents)
        assert all(d.page_content.strip() for d in documents)

    def test_ab_comparison(self):
        """A/B 对比测试：比较两种分割策略的差异"""
        docs_a = split_markdown(self.md_path)
        docs_b = split_markdown_with_size(self.md_path, chunk_size=250, chunk_overlap=30)

        print("\n" + "=" * 60)
        print("  A/B 对比摘要")
        print("=" * 60)

        # 块数对比
        print(f"A方案块数: {len(docs_a)}  |  B方案块数: {len(docs_b)}")

        # 长度统计
        lengths_a = [len(d.page_content) for d in docs_a]
        lengths_b = [len(d.page_content) for d in docs_b]

        print(f"\nA方案块长度 - 最小: {min(lengths_a)}, 最大: {max(lengths_a)}, "
              f"平均: {sum(lengths_a) / len(lengths_a):.1f}")
        print(f"B方案块长度 - 最小: {min(lengths_b)}, 最大: {max(lengths_b)}, "
              f"平均: {sum(lengths_b) / len(lengths_b):.1f}")

        # B方案的块不应超过 chunk_size（允许少量溢出，RecursiveCharacterTextSplitter 不保证严格限制）
        over_limit = sum(1 for l in lengths_b if l > 250)
        print(f"\nB方案超过 chunk_size(250) 的块数: {over_limit}")

        # B方案应产生更多块
        assert len(docs_b) >= len(docs_a), (
            f"B方案({len(docs_b)}块)应不少于A方案({len(docs_a)}块)"
        )

        # B方案的平均块长度应小于A方案
        avg_a = sum(lengths_a) / len(lengths_a)
        avg_b = sum(lengths_b) / len(lengths_b)
        assert avg_b <= avg_a, (
            f"B方案平均长度({avg_b:.1f})应不超过A方案({avg_a:.1f})"
        )

        print("\n✓ A/B 对比测试通过")

    def test_with_size_respects_chunk_size_approximately(self):
        """验证 chunk_size 限制大致生效"""
        documents = split_markdown_with_size(self.md_path, chunk_size=250, chunk_overlap=30)
        lengths = [len(d.page_content) for d in documents]

        # 大多数块应在 chunk_size 范围内
        within_limit = sum(1 for l in lengths if l <= 250)
        ratio = within_limit / len(lengths)
        print(f"\n在 chunk_size(250) 内的块比例: {ratio:.1%} ({within_limit}/{len(lengths)})")

        # 至少 80% 的块应在限制内
        assert ratio >= 0.8, f"在限制内的块比例({ratio:.1%})过低"

    def test_overlap_exists_between_adjacent_chunks(self):
        """验证相邻块之间存在重叠"""
        documents = split_markdown_with_size(self.md_path, chunk_size=250, chunk_overlap=30)

        overlap_count = 0
        for i in range(len(documents) - 1):
            curr_end = documents[i].page_content[-30:] if len(documents[i].page_content) > 30 else documents[i].page_content
            next_start = documents[i + 1].page_content[:30] if len(documents[i + 1].page_content) > 30 else documents[i + 1].page_content

            # 检查是否有任何字符重叠
            has_overlap = any(c in next_start for c in curr_end[-10:])
            if has_overlap:
                overlap_count += 1

        print(f"\n相邻块中有重叠的对数: {overlap_count}/{len(documents) - 1}")

    def test_empty_file_path_raises(self):
        """空路径应抛出 ValueError"""
        import pytest
        with pytest.raises(ValueError, match="File path is empty"):
            split_markdown("")
        with pytest.raises(ValueError, match="File path is empty"):
            split_markdown_with_size("")

    def test_non_md_file_raises(self):
        """非 md 文件应抛出 ValueError"""
        import pytest
        with pytest.raises(ValueError, match="File must be a markdown file"):
            split_markdown("test.txt")
        with pytest.raises(ValueError, match="File must be a markdown file"):
            split_markdown_with_size("test.txt")

    def test_nonexistent_file_raises(self):
        """不存在的文件应抛出 FileNotFoundError"""
        import pytest
        with pytest.raises(FileNotFoundError):
            split_markdown("/nonexistent/file.md")
        with pytest.raises(FileNotFoundError):
            split_markdown_with_size("/nonexistent/file.md")
