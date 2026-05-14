# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the application
uv run python -m src.main

# Run tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_setup.py -v

# Build Docker image
docker build -t stock-alert:local .
```

## Architecture

This is a **multi-agent inventory management system** built with LangGraph. A supervisor agent routes user requests to specialized sub-agents, which call tools that wrap a Go microservice backend via HTTP.

### Request Flow

```
FastAPI (/api/v1) → ChatService → InventoryManagerGraph (LangGraph)
                                        ↓
                               SupervisorAgent (routes)
                              ↙        ↓         ↘
                    DataQuery  KnowledgeSearch  InventoryOperator
                       ↓             ↓               ↓
                    Tools        Milvus RAG        Tools
                       ↓                            ↓
                  Go Microservice              Go Microservice
```

### Key Layers

- **`src/api/`** — FastAPI routers: chat, sessions, users, health. All routes under `/api/v1`.
- **`src/agents/`** — Agent implementations. `supervisor_agent.py` routes; `data_query_agent.py`, `knowledge_search_agent.py`, `inventory_operate.py` are the workers.
- **`src/graph/`** — LangGraph workflow. `setup.py` compiles the graph with node-level retry/cache policies; `inventory_manager.py` is the main orchestrator class.
- **`src/tools/`** — Tool wrappers around the Go microservice HTTP API. `registry.py` groups tools by agent type and registers them at startup.
- **`src/knowledge/`** — RAG pipeline: Milvus vector store, semantic document splitter, retriever. See `src/knowledge/CLAUDE.md` for details.
- **`src/core/`** — LLM factory (`llm/`), shared `AgentState` (LangGraph state schema), and Pydantic schemas.
- **`src/storage/`** — MySQL (session persistence) and Redis (LangGraph checkpointing, 180s cache TTL on knowledge search node).
- **`src/events/`** — Kafka consumer for inventory events (protobuf schemas in `src/events/proto/`).
- **`config/`** — All runtime config is loaded from **Consul KV** at the `agent/stock-alert` prefix via `config/settings.py`. The app will fail to start if Consul is unreachable. Prompt templates live in `config/prompts/` as YAML files.

### Configuration

All runtime config comes from Consul, not `.env` files. Required environment variables to bootstrap the Consul connection:

```
CONSUL_HOST=127.0.0.1
CONSUL_PORT=8500
MICROSERVICE_URL=http://localhost:9080
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=<key>
JWT_SECRET_KEY=<secret>
```

For local dev, copy `docker-compose-dev.yml` to `docker-compose.yml` and fill in the values.

### LLM Provider

Uses DashScope (Alibaba Qwen/QwQ) via `langchain-qwq` and `langchain-openai`. The LLM factory in `src/core/llm/` supports swapping providers. Model config is read from Consul.

### Memory & State

- **Session history**: stored in MySQL via `src/repository/session.py`
- **LangGraph checkpoints**: stored in Redis via `langgraph-checkpoint-redis`
- **Context bounding**: `langmem` summarizes message history to keep context within limits
