"""Configuration for agent service.

Independent configuration loaded from environment variables.
"""

import logging
from typing import Literal

import boto3
from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Agent service settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Model Provider Configuration
    model_provider: Literal["BEDROCK", "OLLAMA", "OPENAI"] = Field(
        default="OLLAMA", description="LLM provider (BEDROCK, OLLAMA, or OPENAI)"
    )

    # AWS Bedrock Configuration
    bedrock_model: str = Field(default="", description="Bedrock model ID")
    aws_region: str | None = Field(default=None, description="AWS region")
    aws_access_key_id: str | None = Field(default=None, description="AWS access key")
    aws_secret_access_key: SecretStr | None = Field(
        default=None, description="AWS secret key"
    )
    aws_session_token: SecretStr | None = Field(
        default=None, description="AWS session token"
    )

    # Ollama Configuration
    ollama_host: str = Field(default="", description="Ollama server URL")
    ollama_model: str = Field(default="", description="Ollama model name")

    # OpenAI Configuration
    openai_api_key: SecretStr = Field(
        default=SecretStr(""), description="OpenAI API key"
    )
    openai_model: str = Field(default="", description="OpenAI model name")

    # MCP Server Configuration
    mcp_server_url: str = Field(
        default="http://localhost:8000/mcp", description="MCP server endpoint URL"
    )

    # Session Configuration
    sessions_dir: str = Field(
        default="strands_sessions", description="Directory for session storage"
    )
    session_ttl_hours: int = Field(
        default=2,
        ge=1,
        description="Session time-to-live in hours (applies to both files and agent cache)",
    )
    session_max_sessions: int = Field(
        default=200, ge=1, description="Maximum number of sessions to keep"
    )
    session_cleanup_interval_minutes: int = Field(
        default=30, ge=5, description="Interval between session cleanup runs"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for task queue and pub/sub",
    )
    redis_task_queue: str = Field(
        default="agent:tasks", description="Redis list key for task queue"
    )
    redis_task_timeout: int = Field(
        default=300, ge=30, description="Task processing timeout in seconds"
    )

    @field_validator("mcp_server_url")
    @classmethod
    def validate_mcp_server_url(cls, v: str) -> str:
        """Validate MCP server URL is not empty."""
        if not v or not v.strip():
            raise ValueError("mcp_server_url is required for agent operation")
        return v

    @field_validator("bedrock_model")
    @classmethod
    def validate_bedrock_model(cls, v: str, info: ValidationInfo) -> str:
        """Validate Bedrock model is set when provider is BEDROCK."""
        if info.data.get("model_provider") == "BEDROCK" and not v:
            raise ValueError("bedrock_model is required when model_provider=BEDROCK")
        return v

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, v: str, info: ValidationInfo) -> str:
        """Validate Ollama model is set when provider is OLLAMA."""
        if info.data.get("model_provider") == "OLLAMA" and not v:
            raise ValueError("ollama_model is required when model_provider=OLLAMA")
        return v

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, v: str, info: ValidationInfo) -> str:
        """Validate OpenAI model is set when provider is OPENAI."""
        if info.data.get("model_provider") == "OPENAI" and not v:
            raise ValueError("openai_model is required when model_provider=OPENAI")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: SecretStr, info: ValidationInfo) -> SecretStr:
        """Validate OpenAI API key is set when provider is OPENAI."""
        if info.data.get("model_provider") == "OPENAI" and not v.get_secret_value():
            raise ValueError("openai_api_key is required when model_provider=OPENAI")
        return v

    def get_bedrock_boto_session(self) -> boto3.Session:
        """Create and return a boto3 Session for AWS Bedrock."""
        if (
            self.aws_access_key_id
            and self.aws_secret_access_key
            and self.aws_session_token
        ):
            return boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key.get_secret_value(),
                aws_session_token=self.aws_session_token.get_secret_value(),
                region_name=self.aws_region,
            )
        return boto3.Session(region_name=self.aws_region)


# Initialize settings singleton
settings = Settings()

# Tool messages for user-friendly display
TOOL_MESSAGES: dict[str, str] = {
    "calculator": "🧮 Calculating",
    "list_all_tables": "📂 Listing all tables",
    "list_tables": "📂 Listing tables",
    "describe_table": "📑 Inspecting table structure",
    "describe_table_with_comments": "🗒️ Reading schema details",
    "get_query_syntax_help": "🔧 Getting query syntax",
    "query": "🔎 Querying database",
    "get_row_count": "🔢 Counting rows",
    "sample_data": "📊 Sampling data",
    "explain_query": "🧭 Analyzing query plan",
    "list_indexes": "🗂️ Listing indexes",
    "list_foreign_keys": "🔗 Checking relationships",
    "get_table_comments": "💬 Reading table comments",
    "database_health": "💚 Checking health",
}
