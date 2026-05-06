# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python -m src.main

# Run tests
uv run pytest                          # All tests
uv run pytest tests/test_specific.py   # Single test file
uv run pytest -v                       # Verbose output

# Start via script
./scripts/start_agent.sh

# Docker
docker build -t stock-alert:latest .
docker-compose up -d
```

## Environment Variables

- `CONSUL_HOST` — Consul server host (default: `127.0.0.1`)
- `CONSUL_PORT` — Consul server port (default: `8500`)

Configuration is loaded from Consul KV at prefix `agent/stock-alert` in production, or from `config/settings.yaml` in local development.

## Architecture

This is an AI-powered inventory management system that combines Kafka event processing, FastAPI REST endpoints, LangGraph agents, and RAG knowledge retrieval.

### System Components

1. **Event Processing Layer** — Kafka consumer that decodes Protobuf messages and routes to handlers
2. **API Layer** — FastAPI application with chat, user, and health endpoints (port 8000, root path `/api/v1`)
3. **Agent Layer** — LangGraph-based `InventoryAgent` with LLM decision-making (Qwen via DashScope)
4. **Knowledge Layer** — Milvus vector store with hybrid search (BM25 + HNSW) for RAG
5. **Storage Layer** — MySQL (sessions), Redis (caching/checkpointing), Milvus (vectors)
6. **Service Layer** — ChatService, SessionService, UserService
   - **ChatService**: Manages chat sessions, handles user messages, and coordinates with `InventoryAgent`
   - **SessionService**: Manages chat session state, including user input, system response, and history
   - **UserService**: Manages user accounts, authentication, and authorization

### Message Processing Pipeline

```
Kafka Message (JSON wrapper)
  → EventDecoder: Base64 decode body → deserialize BaseEvent proto → extract payload
  → decode payload as specific event type (e.g. OnInventoryDeductSuccess)
  → convert to Pydantic model
  → HandlerRegistry.get_handler(event_type) → Handler.handle()
```

**Key files:**
- `src/events/consumer.py` — async Kafka consumer with batch processing (batch_size=100, timeout=5000ms)
- `src/events/decoder.py` — decodes JSON-wrapped, Base64-encoded, nested Protobuf messages
- `src/events/schemas.py` — Pydantic event models; `EVENT_TYPE_TO_MODEL` maps type strings to models
- `src/events/protos/` — generated `*_pb2.py` files; `__init__.py` holds `EVENT_TYPE_TO_PROTOBUF` mapping
- `src/events/handlers/handler_registry.py` — global `registry` instance; maps event type strings to handlers
- `src/events/handlers/base_handler.py` — abstract `BaseHandler` with `event_type` property and async `handle()`

### Adding a New Event Type

1. Define `.proto` and compile with `protoc` → place generated `*_pb2.py` in `src/events/protos/`
2. Add entry to `EVENT_TYPE_TO_PROTOBUF` in `src/events/protos/__init__.py`
3. Add Pydantic model in `src/events/schemas.py` and add to `EVENT_TYPE_TO_MODEL`
4. Create handler in `src/events/handlers/` inheriting `BaseHandler`
5. Register handler via `registry.register()` in `src/main.py`

### API Layer (FastAPI)

- **Base path**: `/api/v1`
- **Port**: 8000
- **Middleware**: Auth (JWT), CORS
- **Routers**:
  - `/chats/*` — chat sessions, messages, streaming (SSE)
  - `/health` — health check
  - `/users/*` — user management
- **Lifecycle**: Startup loads Consul config, initializes MySQL/Redis/Milvus, starts InventoryAgent; shutdown gracefully closes all resources

### RAG Knowledge System

- **Vector Store**: Milvus with hybrid search (dense + sparse vectors)
- **Embeddings**: Qwen embeddings via DashScope
- **Indexing**: HNSW (M=16, efConstruction=256) for dense vectors, BM25 for sparse vectors
- **Metric**: COSINE similarity for semantic search
- **Documents**: Knowledge docs in `src/knowledge/docs/`
- **Manager**: `MilvusManager` in `src/knowledge/vector_store.py` caches collection instances

### Agent System

- **Main Agent**: `InventoryAgent` (LangGraph-based) in `src/agents/inventory_agent.py`
- **LLM**: Qwen (QWQ-Plus model) via DashScope `ChatQwQ`
- **Checkpointing**: Redis-backed (`AsyncRedisSaver`) or in-memory (`InMemorySaver`)
- **State**: Defined in `src/core/agent_state.py`
- **Prompts**: YAML templates in `config/prompts/` (system.yaml, monitor.yaml, decision.yaml, emergency.yaml)

### Storage Layer

- **MySQL**: Session storage via `create_mysql_session_store()` in `src/storage/mysql.py`
- **Redis**: Caching and LangGraph checkpointing via `create_redis_client()` in `src/storage/redis.py`
- **Milvus**: Vector storage for RAG, managed by `MilvusManager` in `src/knowledge/vector_store.py`
- **Retriever**: `BaseKnowledgeRetriever` in `src/knowledge/retriever.py` defines the interface for document retrieval

### Configuration

- **Local dev**: `config/settings.yaml` (Kafka, Consul, agent settings)
- **Production**: Consul KV at prefix `agent/stock-alert` (loaded by `config/settings.py`)
- **LLM**: DashScope `ChatQwQ` (QWQ-Plus model), configured in `src/main.py`
- **Agent prompts**: `config/prompts/` (monitor, decision, emergency, system YAML files)
- **Checkpointer**: Configurable via `checkpointer.type` in config (redis or memory)

## Development Notes

- **Tools layer** (`src/tools/`) is awaiting implementation
- The handler `src/events/handlers/inventory_duduct_success.py` has a TODO for main business logic
- Python 3.13+ required
- Uses `uv` for dependency management (faster than pip)
- `uv sync` to install dependencies
- `uv run src/main.py` to start the system
- `uv test` to run unit tests
- `uv test --coverage` to run tests with coverage report
- `uv test --coverage --html` to generate HTML coverage report
- `uv test --coverage --xml` to generate XML coverage report
- `uv test --coverage --json` to generate JSON coverage report
- `uv test --coverage --term` to generate terminal coverage report