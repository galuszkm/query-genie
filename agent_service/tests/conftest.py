"""Test configuration for agent_service tests."""

import os
import sys
from pathlib import Path

# Set test environment variables
os.environ.setdefault("MODEL_PROVIDER", "BEDROCK")
os.environ.setdefault("BEDROCK_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("OLLAMA_MODEL", "llama3")
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:8000/mcp")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SESSIONS_DIR", "/tmp/test_sessions")

# Add agent_service directory to path so 'src' module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
