# Agent Service

## Overview

The Agent Service is a standalone service that processes AI agent tasks independently from the web server. It consumes tasks from a Redis queue, executes AI agent operations using the Strands Agents framework, and publishes streaming events back through Redis Pub/Sub. This architecture decouples long-running LLM operations from HTTP request handlers, preventing blocking and enabling independent scaling.

## Key Features

- **Independent Process**: Runs separately from the web API for non-blocking LLM calls
- **Queue-based Communication**: Uses Redis for reliable task distribution
- **Session Persistence**: Maintains conversation history via FileSessionManager
- **Multiple LLM Providers**: Supports AWS Bedrock, Ollama, and OpenAI
- **MCP Integration**: Connects to PostgreSQL MCP server for database tools
- **Horizontal Scaling**: Run multiple workers for higher throughput

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                AGENT SERVICE                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐  │
│  │    Worker    │──>│    Agent     │──>│       Strands Agent Framework        │  │
│  │  (Main Loop) │   │   Manager    │   │     (LLM + Tool Orchestration)       │  │
│  └──────────────┘   └──────────────┘   └──────────────────────────────────────┘  │
│         │                  │                           │                         │
│         ▼                  ▼                           ▼                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐  │
│  │    Redis     │   │    File      │   │         Model Providers              │  │
│  │   Client     │   │   Sessions   │   │     (Bedrock / Ollama / OpenAI)      │  │
│  └──────────────┘   └──────────────┘   └──────────────────────────────────────┘  │
│         │                  │                            │                        │
│         │                  ▼                            ▼                        │
│         │        ┌───────────────────┐  ┌──────────────────────────────────────┐ │
│         │        │  Session Cleanup  │  │           MCP Client                 │ │
│         │        │ (Background Task) │  │     (Tool Discovery + RPC)           │ │
│         │        └───────────────────┘  └──────────────────────────────────────┘ │
└─────────┼────────────────────────────────────────────────┼───────────────────────┘
          │                                                │
          ▼                                                ▼ HTTP (MCP Protocol)
    ┌───────────────┐                          ┌──────────────────────────────────┐
    │     Redis     │                          │        MCP PostgreSQL Server     │
    │ (Queue/PubSub)│                          │    (Read-only Database Access)   │
    └───────────────┘                          └──────────────────────────────────┘
```

## Project Structure

```
agent_service/src/
├── main.py                  # Entry point, task processor orchestration
├── core/                    # Core agent functionality
│   ├── agent_manager.py     # Agent lifecycle and caching
│   ├── config.py            # Configuration and settings
│   └── prompts.py           # System prompts
├── events/                  # Event streaming and Redis operations
│   ├── redis_client.py      # Queue consumption, event publishing
│   ├── stream.py            # SSE event transformation
│   └── workflow.py          # Workflow extraction and reasoning
├── utils/                   # Utility functions
│   ├── formatting.py        # Response extraction
│   ├── logging_config.py    # Structured logging
│   ├── metrics.py           # Session metrics persistence
│   └── session_cleanup.py   # Background session cleanup
└── tools/                   # Custom tools
```

## Module Reference

### Main (`main.py`)

The entry point that orchestrates task processing. Creates a single `TaskProcessor` instance that:
- Connects to Redis
- Initializes the agent manager
- Runs an infinite loop consuming tasks from Redis queue
- Starts background session cleanup task
- Handles graceful shutdown

```python
# Start the service
python -m agent_service.src.main
```

### Core Module

**Agent Manager (`core/agent_manager.py`)**

Manages AI agent lifecycle and caching:
- Initializes LLM model (Bedrock or Ollama)
- Connects to MCP server for database tools
- Caches agents by session_id for conversation continuity
- Uses `FileSessionManager` for conversation persistence
- `SlidingWindowConversationManager` keeps last 40 messages
- **Cache Eviction**: Agents inactive for longer than `SESSION_TTL_HOURS` are automatically removed from memory
- Cleanup runs periodically alongside session file cleanup

**Configuration (`core/config.py`)**

Environment-based configuration with validation:
- Model provider settings (Bedrock/Ollama)
- Redis connection parameters
- Session management settings (TTL, max sessions, cleanup interval)
- MCP server URL

**Prompts (`core/prompts.py`)**

System prompt for AI agent behavior and tool usage guidelines.

### Events Module

**Redis Client (`events/redis_client.py`)**

Handles Redis operations:
- Task consumption using BRPOP (blocking pop)
- Event publishing to Pub/Sub channels
- Task cancellation tracking

**Stream Processing (`events/stream.py`)**

Transforms Strands agent events into frontend SSE events:

```
Agent Event Types          →    Frontend Event Types
─────────────────────           ────────────────────
event["data"]              →    {"type": "token", "content": ...}
event["current_tool_use"]  →    Track in pending_tools dict
event["message"]           →    Process for workflow steps
event["result"]            →    {"type": "complete", ...}
```

**Workflow Processing (`events/workflow.py`)**

Extracts structured workflow steps from agent message content blocks:
- **Reasoning blocks** → `{"type": "reasoning", "content": ...}`
- **Tool use blocks** → Track pending tool with input
- **Tool result blocks** → `{"type": "tool", "name": ..., "input": ..., "output": ...}`

Output truncation at 5KB prevents large SSE payloads while preserving LLM context.

### Utils Module

**Formatting (`utils/formatting.py`)**

Response extraction and error formatting utilities.

**Logging (`utils/logging_config.py`)**

Structured logging configuration with context.

**Metrics (`utils/metrics.py`)**

Session metrics persistence to timestamped JSON files.

**Session Cleanup (`utils/session_cleanup.py`)**

Background session cleanup with two-pass strategy:
1. **TTL-based removal**: Deletes sessions older than configured TTL (default: 2 hours)
2. **Max count enforcement**: Removes oldest sessions if total exceeds limit (default: 200)

Runs periodically in background (default: every 30 minutes) without blocking task processing.

**Note**: The same TTL applies to both session files on disk and agent cache in memory. Agents inactive for longer than `SESSION_TTL_HOURS` are evicted from the cache to prevent unbounded memory growth.

## Configuration

Configure the worker via environment variables or `.env` file:

### Model Provider

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_PROVIDER` | LLM provider: `BEDROCK`, `OLLAMA`, or `OPENAI` | `OLLAMA` |

**AWS Bedrock** (when `MODEL_PROVIDER=BEDROCK`):

| Variable | Description |
|----------|-------------|
| `BEDROCK_MODEL` | Model ID (e.g., `anthropic.claude-sonnet-4-5-20250929-v1:0`) |
| `AWS_REGION` | AWS region |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_SESSION_TOKEN` | AWS session token (if using temporary credentials) |

**Ollama** (when `MODEL_PROVIDER=OLLAMA`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | Required |
| `OLLAMA_MODEL` | Model name (e.g., `qwen2.5:14b`) | Required |

**OpenAI** (when `MODEL_PROVIDER=OPENAI`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys) | Required |
| `OPENAI_MODEL` | Model name (e.g., `gpt-5`, `gpt-5-mini`, `gpt-4.1`) | Required |

**Model Configuration:**
- **Temperature**: `0.4` (consistent across providers for predictable responses)
- **Top P**: `0.9` (nucleus sampling for quality)
- **Context**: `16384` tokens (Ollama)

### Redis Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_TASK_QUEUE` | Redis list key for task queue | `agent:tasks` |
| `REDIS_TASK_TIMEOUT` | Task processing timeout (seconds) | `300` |

### MCP Server

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_URL` | MCP PostgreSQL server endpoint | `http://localhost:8000/mcp` |

### Session Management

| Variable | Description | Default |
|----------|-------------|---------|
| `SESSIONS_DIR` | Directory for session files | `strands_sessions` |
| `SESSION_TTL_HOURS` | Session time-to-live (hours) - applies to both files and agent cache | `2` |
| `SESSION_MAX_SESSIONS` | Maximum sessions to keep | `200` |
| `SESSION_CLEANUP_INTERVAL_MINUTES` | Cleanup interval (minutes) | `30` |

**Important**: `SESSION_TTL_HOURS` controls both session file retention and agent cache eviction. Sessions and their cached agents are removed after this period of inactivity to manage disk space and memory usage.

## Usage

### Running Standalone

```bash
# From project root
python -m agent_service.src.main

# With custom environment
MODEL_PROVIDER=BEDROCK python -m agent_service.src.main
```

### Docker

```bash
# Build image
docker build -f agent_service/Dockerfile -t agent-service .

# Run container
docker run -e REDIS_URL=redis://host.docker.internal:6379 \
           -e MCP_SERVER_URL=http://host.docker.internal:8000/mcp \
           -e MODEL_PROVIDER=OLLAMA \
           -e OLLAMA_HOST=http://host.docker.internal:11434 \
           -e OLLAMA_MODEL=qwen2.5:14b \
           agent-service
```

### Docker Compose

The worker is configured in `docker-compose.yml`:

```yaml
agent-service:
  build:
    context: .
    dockerfile: agent_service/Dockerfile
  environment:
    - MCP_SERVER_URL=http://mcp-postgres:8000/mcp
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    redis:
      condition: service_healthy
    mcp-postgres:
      condition: service_healthy
  volumes:
    - ./strands_sessions:/app/strands_sessions
```

## SSE Event Format

Events maintain frontend compatibility:

```json
{"type": "session", "session_id": "uuid"}
{"type": "token", "content": "Hello"}
{"type": "tool", "name": "query", "message": "🔎 Querying..."}
{"type": "complete", "response": "...", "workflow": [...], "session_id": "uuid"}
{"type": "error", "message": "...", "session_id": "uuid"}
```

## Session Management

- **Session ID**: UUID identifying a conversation
- **Agent Cache**: Workers cache agents by session_id for conversation continuity
- **Persistence**: `FileSessionManager` stores conversations to disk in `strands_sessions/`
- **Metrics**: Saved per-session in `strands_sessions/session_{id}/metrics/`
- **Context Window**: Last 40 messages kept via `SlidingWindowConversationManager`

## Extending the Worker

### Adding Custom Tools

Create a new tool function decorated with `@tool` and register it in the agent manager:

```python
# agent_service/src/tools/my_tool.py
from strands import tool

@tool
async def my_custom_tool(param: str) -> dict:
    """
    Description shown to the LLM for tool selection.

    Args:
        param: Parameter description for the LLM.

    Returns:
        Dictionary with status and content.
    """
    result = do_something(param)
    return {"status": "success", "content": [{"text": result}]}
```

```python
# agent_service/src/agent_manager.py - in get_or_create_agent()
from .tools import my_custom_tool

tools = self._mcp_tools + [calculator, my_custom_tool]
```

Update the system prompt to document the new tool:

```python
# agent_service/src/prompts.py
SYSTEM_PROMPT = """
...
CUSTOM TOOLS:
• my_custom_tool - Description of what it does
...
"""
```

### Adding New Model Providers

Extend the `_init_model()` method in `AgentManager`:

```python
# agent_service/src/agent_manager.py
def _init_model(self) -> None:
    if settings.model_provider == "BEDROCK":
        self._model = BedrockModel(...)
    elif settings.model_provider == "OLLAMA":
        self._model = OllamaModel(...)
    elif settings.model_provider == "OPENAI":
        # Add new provider
        from strands.models.openai import OpenAIModel
        self._model = OpenAIModel(
            api_key=settings.openai_api_key,
            model_id=settings.openai_model,
        )
```

### Horizontal Scaling

Run multiple worker instances for higher throughput:

```yaml
# docker-compose.yml
agent-service:
  deploy:
    replicas: 3
```

Workers are stateless - Redis BRPOP automatically distributes tasks across workers.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Strands Agents 1.20 |
| LLM Providers | AWS Bedrock, Ollama |
| Tool Protocol | MCP (Model Context Protocol) 1.24 |
| Message Broker | Redis (Queue + Pub/Sub) |
| Sessions | File-based with JSON persistence |
| Async Runtime | Python asyncio |
