FROM python:3.13.9-slim AS builder

ENV UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
ENV UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

# 安装pip（Python镜像已包含）并使用pip安装uv
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple  \
    && pip install --no-cache-dir uv

# 设置工作目录
WORKDIR /app

# 复制依赖定义文件
COPY pyproject.toml uv.lock ./

# 使用uv安装依赖到虚拟环境
RUN uv venv
RUN uv sync --frozen

FROM python:3.13.9-slim

# 设置工作目录
WORKDIR /app

# 创建非root用户
RUN groupadd -g 1002 appuser && useradd -r -u 1002 -g appuser appuser

# 从builder阶段复制虚拟环境
COPY --from=builder /app/.venv ./.venv

# 将虚拟环境添加到PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# 复制Python源代码
COPY --chown=app:app src/ ./src/
COPY --chown=app:app config/ ./config/

# 确保所有.py文件存在（验证）
RUN find ./src ./config -name "*.py" | head -5

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 7860

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# 设置入口点
CMD ["python", "-m", "src.main"]