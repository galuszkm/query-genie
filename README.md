<div align="center">

# 🧞 QueryGenie

### Agentic AI Platform for Intelligent Database Interaction

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-19.2+-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.9+-3178c6.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ed.svg)](https://www.docker.com/)

**Transform natural language into actionable insights with production-ready agentic AI**

[Getting Started](#quick-start) • [Architecture](#system-architecture) • [Features](#key-features) • [Configuration](#configuration-guide) • [Usage](#usage-examples)

</div>

## 🌟 Overview

**QueryGenie** is a complete, production-ready agentic AI platform that demonstrates how to build **enterprise-grade intelligent systems** from the ground up. Unlike typical side projects, QueryGenie is built for **real-world deployment, research, and experimentation**.

### What You Get

**🤖 Complete AI Agent Stack** — Agentic RAG with autonomous reasoning loops, multi-step query execution, schema exploration, and intelligent result synthesis

**🎨 Professional Dashboard** — React + TypeScript frontend with real-time SSE streaming, reasoning visualization, and complete tool execution tracking

**🔐 Enterprise Security** — Multi-layer input protection (prompt injection, XSS, SQL injection via AST parsing), CORS controls, rate limiting, and read-only database enforcement

**⚡ Built to Scale** — Horizontally scalable workers, event-driven architecture, connection pooling, and independent service deployment

**🔧 Highly Extensible** — Swap LLM providers (Bedrock, Ollama, OpenAI), connect any database (PostgreSQL, MySQL, MongoDB), add custom tools and expert agents in minutes

**🏗️ Production Patterns** — Implements CQRS, pub/sub messaging, adapter pattern (MCP), async-first design, and distributed event-driven architecture

**🔬 Research-Ready** — Transparent agent reasoning, experiment with prompts and tools, well-documented codebase, easy integration via REST API

**🚀 Deploy Anywhere** — Docker Compose for local, Kubernetes for scale, or cloud platforms (AWS, Azure, GCP)

<div align="center">

<a href=".resources/demo.mp4">
  <img src=".resources/demo.jpg" alt="QueryGenie Demo" style="max-width: 1000px;">
</a>

*Click to watch the full demo video*

</div>

### Core Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **Frontend Dashboard** | Real-time visualization of agent reasoning with streaming SSE updates | React 19 + TypeScript + Vite |
| **Backend API Service** | Secure gateway with input sanitization, rate limiting, and event streaming | FastAPI + Pydantic + SlowAPI |
| **Agent Service** | Autonomous AI agent with tool orchestration and reasoning loops | Strands Framework + MCP Client |
| **MCP PostgreSQL Server** | Read-only database access layer implementing Model Context Protocol | FastMCP + asyncpg |
| **Message Broker** | Event queue and pub/sub for distributed task processing | Redis 7 |

---

## 🚀 Key Features

- **🎨 Interactive Dashboard** — Real-time visualization of agent reasoning, tool execution, and workflow with SSE streaming
- **🤖 Agentic RAG** — Multi-step reasoning with autonomous data retrieval, schema exploration, and intelligent synthesis
- **🔐 Enterprise Security** — Input sanitization, prompt injection detection, XSS/SQL injection prevention via AST parsing, CORS controls, rate limiting, and read-only enforcement
- **📊 Natural Language Queries** — Plain English to SQL with multi-database support and AI-generated insights
- **⚡ Horizontally Scalable** — Multiple agent workers, custom tools, expert agents, and flexible LLM providers
- **🏗️ Event-Driven Architecture** — Decoupled services, async I/O, Redis pub/sub, and graceful error handling


## 🏛️ System Architecture

QueryGenie implements a distributed, event-driven architecture following industry best practices:

**Architecture Patterns**:
- 🔄 **Producer-Consumer Pattern**: Backend produces tasks, agent workers consume
- 📢 **Publish-Subscribe**: Real-time event streaming via Redis pub/sub
- 🎯 **CQRS (Command Query Responsibility Segregation)**: Separate read/write concerns
- 🔌 **Adapter Pattern**: MCP protocol abstracts database access
- 🧱 **Layered Architecture**: Clear separation between API, business logic, and data layers

```
         ┌──────────────────────────────────────────────────────────────────────────────────┐
         │                          FRONTEND DASHBOARD (React + TS)                         │
         │           Real-time SSE streaming • Reasoning visualization • Tool tracking      │
         └──────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼ HTTP/SSE (Port 8080)
         ┌──────────────────────────────────────────────────────────────────────────────────┐
         │                              BACKEND API SERVICE                                 │
         │                                                                                  │
         │  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐    │
         │  │   FastAPI Gateway   │───>│  Input Sanitizer │───>│   Rate Limiter        │    │
         │  │   (REST + SSE)      │    │  (Prompt Inj.)   │    │   (SlowAPI)           │    │
         │  └─────────────────────┘    └──────────────────┘    └───────────────────────┘    │
         │            │                                                                     │
         │            ▼                                                                     │
         │  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐    │
         │  │   CORS Controls     │───>│  Redis Client    │───>│  Task Queue (LPUSH)   │    │
         │  │  (Origin Whitelist) │    │  (Enqueue)       │    │  Pub/Sub (Subscribe)  │    │
         │  └─────────────────────┘    └──────────────────┘    └───────────────────────┘    │
         └──────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼ Redis Queue (agent:tasks)
         ┌──────────────────────────────────────────────────────────────────────────────────┐
         │                       REDIS MESSAGE BROKER (Port 6379)                           │
         │              Task Queue (LPUSH/BRPOP) • Pub/Sub (Channels: task:{id})            │
         └──────────────────────────────────────────────────────────────────────────────────┘
             ▲  Pub/Sub Events                  │
             │                                  ▼ BRPOP (Blocking Pop)
         ┌───│──────────────────────────────────────────────────────────────────────────────┐
         │   │                         AGENT SERVICE (Scalable Workers)                     │
         │   │                                                                              │
         │   │ ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  │
         │   │ │ Worker Pool  │───>│  Agent Manager   │───>│  Strands Framework          │  │
         │   │ │ (BRPOP Loop) │    │  (Per Session)   │    │  (Agentic RAG + Tools)      │  │
         │   │ └──────────────┘    └──────────────────┘    └─────────────────────────────┘  │
         │   │                              │                            │                  │
         │   │                              ▼                            ▼                  │
         │  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  │
         │  │  Redis Publish  │    │  Session Files   │    │      LLM Providers          │  │
         │  │  (SSE Events)   │    │  (Persistence)   │    │ (Bedrock / Ollama / OpenAI) │  │
         │  └─────────────────┘    └──────────────────┘    └─────────────────────────────┘  │
         │                                  │                            │                  │
         │                                  ▼                            ▼                  │
         │                         ┌───────────────────┐   ┌─────────────────────────────┐  │
         │                         │  Session Cleanup  │   │      MCP Client             │  │
         │                         │ (TTL Management)  │   │  (Tool Discovery + RPC)     │  │
         │                         └───────────────────┘   └─────────────────────────────┘  │
         └──────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼ HTTP + MCP Protocol (Port 8000)
         ┌──────────────────────────────────────────────────────────────────────────────────┐
         │                      MCP POSTGRESQL SERVER (Read-Only Layer)                     │
         │       Schema Discovery • Query Execution • Result Caching • Safety Validation    │
         └──────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼ asyncpg Connection Pool
         ┌──────────────────────────────────────────────────────────────────────────────────┐
         │                          POSTGRESQL DATABASES (Port 5432)                        │
         │              Multiple Databases • Connection Pooling • Query Optimization        │
         └──────────────────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **User submits natural language question** via the React dashboard
2. **Backend API** sanitizes input (prompt injection detection), validates, and enqueues task to Redis
3. **Agent worker** picks up task, creates/retrieves session-specific agent
4. **AI Agent** reasons about the question, breaks it into steps, selects tools
5. **MCP Server** validates queries using SQL AST parser (read-only enforcement, SQL injection prevention)
6. **Agent synthesizes** results from multiple queries into a coherent answer
7. **Real-time updates** stream back to frontend via SSE as agent progresses
8. **User sees** complete reasoning chain, tool calls, queries, and final answer


## 📦 Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 19, TypeScript 5.9+, Vite |
| **Backend** | Python 3.13, FastAPI, Pydantic, SlowAPI, Uvicorn |
| **AI & Agents** | Strands Framework, MCP Client, AWS Bedrock (Claude), Ollama, OpenAI |
| **Database** | PostgreSQL 17, asyncpg, FastMCP |
| **Message Broker** | Redis 7 (Queue + Pub/Sub) |
| **DevOps** | Docker, Docker Compose, uv |
| **Quality & Testing** | Ruff, MyPy, pytest, pre-commit |


## 🚀 Quick Start

Get QueryGenie running in under 5 minutes!

### Prerequisites

- **Docker & Docker Compose** — For containerized deployment ([Install Docker](https://docs.docker.com/get-docker/))
- **Python 3.13+** — For local development ([Install Python](https://www.python.org/downloads/))
- **uv** — Fast Python package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 22+** — For frontend development ([Install Node](https://nodejs.org/))
- **LLM Access** — Choose one:
  - **OpenAI API Key** (easiest) — Get from [OpenAI Platform](https://platform.openai.com/api-keys)
  - **Ollama** (free, local) — Install from [ollama.ai](https://ollama.ai/)
  - **AWS Bedrock** (enterprise) — Requires AWS account with Bedrock access

### Option 1: Docker Compose (Recommended for First Run)

The fastest way to experience QueryGenie with all services and a sample database:

```bash
# 1. Clone the repository
git clone <repository-url>
cd querygenie

# 2. Configure environment
cp example.env .env
# Edit .env if you want to customize (optional for first run)

# 3. Start all services
docker compose up --build

# 4. Open your browser
# Frontend: http://localhost:8080
# Backend API: http://localhost:8080/api
# MCP Server: http://localhost:8000
```

**What's included:**
- ✅ PostgreSQL 17 with sample data (products, orders, customers)
- ✅ Redis 7 for task queue and pub/sub
- ✅ MCP PostgreSQL Server (port 8000)
- ✅ Agent Service (worker)
- ✅ Backend API + Frontend (port 8080)

**Try it out:**
- Ask: *"Show me the top 5 products by revenue"*
- Ask: *"What are the categories in the database?"*
- Ask: *"Find customers who made purchases in the last month"*

### Option 2: Local Development (Full Control)

For active development with hot reload:

```bash
# 1. Clone and install dependencies
git clone <repository-url>
cd querygenie
uv sync --all-groups

# 2. Install git hooks (recommended)
uv run just install

# 3. Start infrastructure (PostgreSQL + Redis)
docker compose up postgres redis

# 4. Configure environment
cp example.env .env
# Edit .env with your database credentials and LLM provider

# 5. Start services in separate terminals

# Terminal 1: MCP Server
uv run python -m mcp_postgres.src.server

# Terminal 2: Agent Service
uv run python -m agent_service.src.main

# Terminal 3: Backend API
uv run uvicorn backend.src.app:create_app --factory --reload --port 8080

# Terminal 4: Frontend (optional)
cd frontend
npm install
npm run dev
```

## 📚 Project Structure

QueryGenie follows a modular architecture with clear separation of concerns:

```
querygenie/
├── 🎨 frontend/                   # React + TypeScript Dashboard
│   ├── src/
│   │   ├── components/            # Reusable UI components
│   │   │   ├── ChatMessage        # Message display with tool tracking
│   │   │   ├── ThinkingBox        # Real-time reasoning visualization
│   │   │   ├── ToolBadge          # Tool execution indicators
│   │   │   └── WorkflowDialog     # Complete reasoning timeline
│   │   ├── hooks/                 # Custom React hooks (useChat, useSSE)
│   │   ├── services/              # API client and event handling
│   │   └── types/                 # TypeScript type definitions
│   └── README.md                  # Frontend documentation
│
├── 🔐 backend/                    # API Gateway Service
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes.py          # HTTP endpoints + SSE streaming
│   │   │   ├── middleware.py      # Request logging, error tracking, CORS
│   │   │   ├── rate_limit.py      # Per-IP request throttling
│   │   │   └── models.py          # Pydantic request/response models
│   │   ├── utils/
│   │   │   ├── input_sanitizer.py # XSS, SQLi protection
│   │   │   ├── redis_client.py    # Queue enqueue, pub/sub subscribe
│   │   │   └── session.py         # Session management
│   │   └── config.py              # Environment configuration
│   ├── tests/                     # Unit and integration tests
│   └── README.md                  # 📖 Backend documentation
│
├── 🤖 agent_service/              # AI Agent Worker
│   ├── src/
│   │   ├── core/
│   │   │   ├── agent_manager.py   # Agent creation and caching
│   │   │   ├── config.py          # LLM provider configuration
│   │   │   └── prompts.py         # System prompts and instructions
│   │   ├── events/
│   │   │   ├── redis_client.py    # Task consumption (BRPOP)
│   │   │   ├── stream.py          # SSE event publishing
│   │   │   └── workflow.py        # Reasoning and tool tracking
│   │   ├── tools/                 # 🔧 Custom tool plugins (extend here!)
│   │   └── utils/
│   │       ├── session_cleanup.py # TTL-based session management
│   │       └── metrics.py         # Performance monitoring
│   ├── tests/                     # Agent behavior tests
│   └── README.md                  # 📖 Agent service documentation
│
├── 🗄️ mcp_postgres/               # MCP PostgreSQL Server
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py          # Multi-database configuration
│   │   │   ├── connection.py      # Connection pooling
│   │   │   └── cache.py           # Schema caching
│   │   ├── tools/
│   │   │   ├── discovery.py       # List databases and schemas
│   │   │   ├── schema.py          # Table structure exploration
│   │   │   └── query.py           # Safe query execution
│   │   └── utils/
│   │       ├── validator.py       # Read-only enforcement
│   │       └── monitor.py         # Query performance tracking
│   ├── tests/                     # Database tool tests
│   └── README.md                  # 📖 MCP server documentation
│
├── 📋 tasks/                      # Just task definitions
│   ├── check.just                 # Code quality checks
│   ├── format.just                # Code formatting
│   ├── test.just                  # Testing tasks
│   └── install.just               # Installation tasks
│
├── 🐳 docker-compose.yml          # Service orchestration
├── ⚙️ pyproject.toml              # Python dependencies (uv)
├── 🚀 justfile                    # Task runner entry point
├── 📝 example.env                 # Environment template
├── 🗃️ init.sql                    # Sample database schema
└── 📖 README.md                   # This file

```

### 📖 Module Documentation

Each component has detailed documentation:

- **[Backend README](backend/README.md)** — API endpoints, authentication, rate limiting, SSE streaming
- **[Agent Service README](agent_service/README.md)** — Agent architecture, tool development, session management, LLM configuration
- **[MCP Server README](mcp_postgres/README.md)** — Database tools, safety features, multi-database setup, caching strategies

## ⚙️ Configuration Guide

QueryGenie is highly configurable through environment variables. Create a `.env` file from the template:

```bash
cp example.env .env
```

### 🗄️ Database Configuration

Connect to one or multiple PostgreSQL databases:

```env
# Pattern: DATABASE{N}_URL where N = 1, 2, 3...
DATABASE1_URL=postgresql://user:password@localhost:5432/production_db
DATABASE2_URL=postgresql://user:password@localhost:5432/analytics_db
DATABASE3_URL=postgresql://user:password@localhost:5432/staging_db

# For Docker PostgreSQL initialization
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=querygenie
```

### 🤖 LLM Provider Configuration

**Option A: AWS Bedrock** (Production-grade Claude models)

```env
MODEL_PROVIDER=BEDROCK
BEDROCK_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=optional_session_token
```

**Option B: Ollama** (Local deployment, privacy-first)

```env
MODEL_PROVIDER=OLLAMA
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
```

**Option C: OpenAI** (Easiest setup, pay-per-use)

```env
MODEL_PROVIDER=OPENAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

**💡 Choosing an LLM Provider:**
- **OpenAI** — Easiest to get started (just API key), excellent performance, but costs per token (~$0.01-0.03 per 1K tokens)
- **Ollama** — Free and private, runs on your hardware, best for on-premises deployment or cost control
- **Bedrock** — Enterprise AWS integration, managed service with SLA, requires AWS account setup

> **⚠️ WARNING: Token Usage with Pay-Per-Use Providers**
>
> Agentic workflows can consume **significantly more tokens** than simple chat applications. A single question may trigger **multiple tool calls, reasoning loops, and context retrievals**, easily consuming **50K-100K+ tokens per query**.
>
> **Cost Example (OpenAI GPT-4.1):**
> - Single query: 100K tokens ≈ $0.20
> - 100 queries/day ≈ $20/day ≈ $600/month
>
> **Best Practices:**
> - ✅ **Monitor usage** via provider dashboard (OpenAI Usage, AWS Cost Explorer)
> - ✅ **Set spending limits** in your provider account
> - ✅ **Start with Ollama** for development/testing (free)
> - ✅ **Use cheaper models** for non-critical tasks (gpt-5-nano, gpt-4o-mini)
> - ✅ **Implement caching** for repeated queries
> - ⚠️ **Never use production API keys in development**

### 🔐 Security Configuration

```env
# CORS Configuration (comma-separated origins, empty in production)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080

# Input Validation (strict mode enables prompt injection detection)
INPUT_SANITIZER_STRICT=true

# Rate Limiting (per-tool rate limiting to prevent abuse)
# Configured in mcp_postgres/src/core/config.py
```

### 📡 Redis & MCP Configuration

```env
# Redis Message Broker
REDIS_URL=redis://localhost:6379/0
REDIS_TASK_QUEUE=agent:tasks

# MCP PostgreSQL Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_URL=http://localhost:8000/mcp
```

### 💾 Session Management

```env
# Session storage and cleanup
SESSIONS_DIR=strands_sessions
SESSION_TTL_HOURS=2                      # Max session age
SESSION_MAX_SESSIONS=200                 # Max sessions on disk
SESSION_CLEANUP_INTERVAL_MINUTES=30      # Cleanup frequency
```

## 🎯 Usage Examples

### Example 1: Database Exploration

**User:** *"What tables are in the database?"*

**Agent reasoning:**
1. 🔍 Discover available databases
2. 📋 List all tables in each schema
3. 📊 Summarize table names and purposes

**Result:** Complete list of tables with descriptions

### Example 2: Complex Analysis

**User:** *"Show me the top 5 customers by total revenue and their most purchased product category"*

**Agent reasoning:**
1. 🗂️ Explore schema (orders, customers, products, categories)
2. 📝 Sample data to understand relationships
3. 🔗 Plan multi-table JOIN query
4. 📊 Execute query with aggregations
5. 💡 Synthesize insights from results

**Result:** Formatted table with customer names, revenue, and top categories

### Example 3: Time-based Queries

**User:** *"What was the sales trend over the last quarter?"*

**Agent reasoning:**
1. 🗓️ Identify date columns in orders table
2. 📅 Calculate last quarter date range
3. 📈 Aggregate sales by week/month
4. 📊 Present trend with insights

**Result:** Time-series data with trend analysis


## 🔧 Customization & Extension

QueryGenie is designed for easy customization:

### Adding Custom Tools

Create new tools for the agent to use:

```python
# agent_service/src/tools/calculator.py

from strands import tool

@tool
def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage of value relative to total."""
    if total == 0:
        return 0.0
    return (value / total) * 100

# Register in agent_service/src/core/agent_manager.py
```

### Adding Expert Agents

Implement specialized agents for specific domains:

```python
# agent_service/src/agents/sql_optimizer.py

class SQLOptimizerAgent:
    """Expert agent for query optimization"""

    async def optimize_query(self, query: str) -> str:
        # Analyze and optimize SQL
        # Add indexes suggestions
        # Rewrite inefficient queries
        pass
```

### Connecting Different Databases

Extend beyond PostgreSQL:

```python
# mcp_<database>/src/server.py

# Example: Add MongoDB support
from fastmcp import FastMCP
from pymongo import MongoClient

mcp = FastMCP("MongoDB MCP Server")

@mcp.tool()
async def query_collection(db: str, collection: str, filter: dict):
    """Query MongoDB collection"""
    client = MongoClient(MONGO_URL)
    return list(client[db][collection].find(filter))
```

### Integrating External APIs

Add REST API tools for enriched data:

```python
# agent_service/src/tools/weather_api.py

@tool
async def get_weather(location: str) -> dict:
    """Fetch current weather for location"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{location}")
        return response.json()
```


## 🚀 Deployment Options

QueryGenie supports multiple deployment strategies:

### 🏠 On-Premises Deployment

Perfect for enterprises with data sovereignty requirements:

```bash
# Deploy on internal servers
docker compose up -d

# Configure firewall rules
# Set up reverse proxy (nginx/traefik)
# Configure SSL certificates
# Set up monitoring (Prometheus, Grafana)
```

### ☁️ AWS Deployment

Production-ready cloud deployment:

**Architecture:**
- **ECS Fargate** — Container orchestration
- **RDS PostgreSQL** — Managed database
- **ElastiCache Redis** — Managed Redis
- **ALB** — Load balancer with SSL
- **CloudWatch** — Monitoring and logs
- **Secrets Manager** — Secure credential storage

```bash
# Example Terraform/CloudFormation deployment
# Deploy to ECS with auto-scaling
# Configure RDS multi-AZ for HA
# Set up ElastiCache cluster
```

### 🌐 Other Cloud Providers

- **Azure**: Azure Container Instances, Azure Database for PostgreSQL, Azure Cache for Redis
- **GCP**: Cloud Run, Cloud SQL, Memorystore
- **DigitalOcean**: App Platform, Managed PostgreSQL, Managed Redis

### 🎯 Kubernetes Deployment

For large-scale production:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: querygenie-agent
spec:
  replicas: 5  # Horizontal scaling
  selector:
    matchLabels:
      app: querygenie-agent
  template:
    spec:
      containers:
      - name: agent
        image: querygenie/agent:latest
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
```


## 🛠️ Development Guide

### Project Commands

QueryGenie uses **just** as a task runner. All commands are prefixed with `uv run`:

#### Installation & Setup

```bash
uv run just install          # Install project + git hooks
uv run just install-project  # Install dependencies only
uv run just install-hooks    # Install git hooks only
```

#### Code Quality

```bash
uv run just check            # Run all checks (format, lint, type, security)
uv run just check-code       # Ruff linting
uv run just check-format     # Check code formatting
uv run just check-type       # MyPy type checking
uv run just check-security   # Bandit security scan
uv run just check-audit      # Dependency vulnerability audit
```

#### Testing

```bash
uv run just test                              # Run tests with coverage
uv run just test-test                         # Run tests without coverage
uv run just test-coverage                     # Custom coverage settings
```

#### Formatting

```bash
uv run just format           # Format all code
uv run just format-import    # Sort imports (Ruff)
uv run just format-source    # Format source code (Ruff)
```

#### Cleanup

```bash
uv run just clean            # Clean all artifacts
uv run just clean-build      # Remove build files
uv run just clean-cache      # Remove cache files
uv run just clean-coverage   # Remove coverage reports
```

### Git Workflow

QueryGenie uses **Commitizen** for conventional commits:

```bash
# Make changes
git add .

# Create conventional commit (interactive)
uv run just commit-files

# Push (pre-push hooks run checks)
git push

# Bump version based on commits
uv run just commit-bump
```

**Commit Types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `style:` — Code style (formatting, etc.)
- `refactor:` — Code restructuring
- `test:` — Adding tests
- `chore:` — Maintenance tasks

### Testing Strategy

```bash
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest agent_service/tests/
uv run pytest backend/tests/test_routes.py

# Run with coverage report
uv run pytest --cov=backend --cov=agent_service --cov=mcp_postgres

# Run in parallel
uv run pytest -n auto
```

## 📊 Monitoring & Observability

QueryGenie includes built-in monitoring capabilities:

### Metrics Collection

- **Request latency**: Track API response times
- **Agent execution time**: Monitor reasoning loop performance
- **Query execution time**: Database query performance
- **Tool usage**: Track which tools are used most frequently
- **Error rates**: Monitor failures and exceptions

### Logging

Structured JSON logging throughout:

```python
# Example log output
{
  "timestamp": "2025-12-23T10:30:45.123Z",
  "level": "INFO",
  "service": "agent_service",
  "session_id": "abc123",
  "message": "Query executed successfully",
  "duration_ms": 245,
  "tool": "query_database"
}
```

### Health Checks

```bash
# Backend health
curl http://localhost:8080/health

# MCP Server health
curl http://localhost:8000/health

# Redis connection
redis-cli PING
```


## 🔬 Research & Experimentation

QueryGenie is an excellent platform for AI research:

### Use Cases

1. **Prompt Engineering**: Experiment with different system prompts and instructions
2. **Tool Design**: Test various tool interfaces and parameter schemas
3. **Reasoning Patterns**: Study how agents break down complex problems
4. **Multi-Agent Systems**: Implement agent collaboration and delegation
5. **RAG Optimization**: Tune retrieval strategies and context selection
6. **LLM Comparison**: Benchmark different models on the same tasks

### Experiment Ideas

```python
# A/B test different prompts
prompts = {
    "concise": "Answer briefly with data",
    "detailed": "Provide comprehensive analysis with reasoning",
    "chain_of_thought": "Think step by step before answering"
}

# Compare reasoning strategies
strategies = ["depth_first", "breadth_first", "beam_search"]

# Test tool combinations
tool_sets = [
    ["query", "schema"],
    ["query", "schema", "sample"],
    ["query", "schema", "sample", "aggregate"]
]
```


## 🤝 Contributing

We welcome contributions! QueryGenie is designed to be extended and improved:

### Areas for Contribution

- 🔧 **New tools**: Add support for more data sources (APIs, files, etc.)
- 🤖 **Expert agents**: Implement specialized agents for domains
- 🎨 **UI enhancements**: Improve dashboard visualizations
- 📚 **Documentation**: Expand guides and tutorials
- 🧪 **Tests**: Increase test coverage
- 🐛 **Bug fixes**: Report and fix issues

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/querygenie.git
cd querygenie

# Install with dev dependencies
uv sync --all-groups

# Install git hooks
uv run just install-hooks

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
uv run just check
uv run just test

# Commit with conventional commits
uv run just commit-files

# Push and create PR
git push origin feature/your-feature-name
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Agent not responding
```bash
# Check Redis connection
redis-cli PING

# Check agent service logs
docker compose logs agent-service

# Verify task queue
redis-cli LLEN agent:tasks
```

**Issue**: Database connection failed
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d querygenie

# Check MCP server logs
docker compose logs mcp-postgres

# Verify DATABASE URLs in .env
```

**Issue**: Frontend not connecting
```bash
# Check backend is running
curl http://localhost:8080/ai/api/health

# Check browser console for CORS errors
# Verify ALLOWED_ORIGINS in .env
```

**Issue**: LLM errors
```bash
# For Bedrock: Verify AWS credentials
aws sts get-caller-identity

# For Ollama: Check Ollama is running
curl http://localhost:11434/api/tags

# Check MODEL_PROVIDER in .env
```

## 📄 License

MIT


## 🙏 Acknowledgments

QueryGenie is built on top of excellent open-source projects:

- **[Strands](https://strandsagents.com/latest/)** — Agentic workflow framework
- **[FastMCP](https://gofastmcp.com/)** — Model Context Protocol server
- **[FastAPI](https://fastapi.tiangolo.com/)** — Modern Python web framework
- **[React](https://react.dev/)** — UI library
- **[Redis](https://redis.io/)** — In-memory data store
- **[PostgreSQL](https://www.postgresql.org/)** — Advanced database system


## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/galuszkm/querygenie/issues)
- **Discussions**: [GitHub Discussions](https://github.com/galuszkm/querygenie/discussions)
- **Documentation**: [Full Docs](https://docs.yoursite.com)


<div align="center">

**Built with ❤️ for the AI community**

⭐ Star this repo if you find it useful!

[Report Bug](https://github.com/galuszkm/querygenie/issues) · [Request Feature](https://github.com/galuszkm/querygenie/issues)

</div>
