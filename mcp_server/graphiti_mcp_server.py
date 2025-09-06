#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypedDict, cast

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field

from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.embedder.azure_openai import AzureOpenAIEmbedderClient
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client import LLMClient
from graphiti_core.llm_client.azure_openai_client import AzureOpenAILLMClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_NODE_DISTANCE,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.utils.maintenance.graph_data_operations import clear_data

load_dotenv()


DEFAULT_LLM_MODEL = "gpt-4.1-mini"
SMALL_LLM_MODEL = "gpt-4.1-nano"
DEFAULT_EMBEDDER_MODEL = "text-embedding-3-small"

# Semaphore limit for concurrent Graphiti operations.
# Decrease this if you're experiencing 429 rate limit errors from your LLM provider.
# Increase if you have high rate limits.
SEMAPHORE_LIMIT = int(os.getenv("SEMAPHORE_LIMIT", 10))


class Requirement(BaseModel):
    """A Requirement represents a specific need, feature, or functionality that a product or service must fulfill.

    Always ensure an edge is created between the requirement and the project it belongs to, and clearly indicate on the
    edge that the requirement is a requirement.

    Instructions for identifying and extracting requirements:
    1. Look for explicit statements of needs or necessities ("We need X", "X is required", "X must have Y")
    2. Identify functional specifications that describe what the system should do
    3. Pay attention to non-functional requirements like performance, security, or usability criteria
    4. Extract constraints or limitations that must be adhered to
    5. Focus on clear, specific, and measurable requirements rather than vague wishes
    6. Capture the priority or importance if mentioned ("critical", "high priority", etc.)
    7. Include any dependencies between requirements when explicitly stated
    8. Preserve the original intent and scope of the requirement
    9. Categorize requirements appropriately based on their domain or function
    """

    project_name: str = Field(
        ...,
        description="The name of the project to which the requirement belongs.",
    )
    description: str = Field(
        ...,
        description="Description of the requirement. Only use information mentioned in the context to write this description.",
    )


class Preference(BaseModel):
    """A Preference represents a user's expressed like, dislike, or preference for something.

    Instructions for identifying and extracting preferences:
    1. Look for explicit statements of preference such as "I like/love/enjoy/prefer X" or "I don't like/hate/dislike X"
    2. Pay attention to comparative statements ("I prefer X over Y")
    3. Consider the emotional tone when users mention certain topics
    4. Extract only preferences that are clearly expressed, not assumptions
    5. Categorize the preference appropriately based on its domain (food, music, brands, etc.)
    6. Include relevant qualifiers (e.g., "likes spicy food" rather than just "likes food")
    7. Only extract preferences directly stated by the user, not preferences of others they mention
    8. Provide a concise but specific description that captures the nature of the preference
    """

    category: str = Field(
        ...,
        description="The category of the preference. (e.g., 'Brands', 'Food', 'Music')",
    )
    description: str = Field(
        ...,
        description="Brief description of the preference. Only use information mentioned in the context to write this description.",
    )


class Procedure(BaseModel):
    """A Procedure informing the agent what actions to take or how to perform in certain scenarios. Procedures are typically composed of several steps.

    Instructions for identifying and extracting procedures:
    1. Look for sequential instructions or steps ("First do X, then do Y")
    2. Identify explicit directives or commands ("Always do X when Y happens")
    3. Pay attention to conditional statements ("If X occurs, then do Y")
    4. Extract procedures that have clear beginning and end points
    5. Focus on actionable instructions rather than general information
    6. Preserve the original sequence and dependencies between steps
    7. Include any specified conditions or triggers for the procedure
    8. Capture any stated purpose or goal of the procedure
    9. Summarize complex procedures while maintaining critical details
    """

    description: str = Field(
        ...,
        description="Brief description of the procedure. Only use information mentioned in the context to write this description.",
    )


ENTITY_TYPES: dict[str, BaseModel] = {
    "Requirement": Requirement,  # type: ignore
    "Preference": Preference,  # type: ignore
    "Procedure": Procedure,  # type: ignore
}


# Type definitions for API responses
class ErrorResponse(TypedDict):
    error: str


class SuccessResponse(TypedDict):
    message: str


class NodeResult(TypedDict):
    uuid: str
    name: str
    summary: str
    labels: list[str]
    group_id: str
    created_at: str
    attributes: dict[str, Any]


class NodeSearchResponse(TypedDict):
    message: str
    nodes: list[NodeResult]


class FactSearchResponse(TypedDict):
    message: str
    facts: list[dict[str, Any]]


class EpisodeSearchResponse(TypedDict):
    message: str
    episodes: list[dict[str, Any]]


class StatusResponse(TypedDict):
    status: str
    message: str


def create_azure_credential_token_provider() -> Callable[[], str]:
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return token_provider


# Server configuration classes
# The configuration system has a hierarchy:
# - GraphitiConfig is the top-level configuration
#   - LLMConfig handles all OpenAI/LLM related settings
#   - EmbedderConfig manages embedding settings
#   - Neo4jConfig manages database connection details
#   - Various other settings like group_id and feature flags
# Configuration values are loaded from:
# 1. Default values in the class definitions
# 2. Environment variables (loaded via load_dotenv())
# 3. Command line arguments (which override environment variables)
class GraphitiLLMConfig(BaseModel):
    """Configuration for the LLM client.

    Centralizes all LLM-specific configuration parameters including API keys and model selection.
    """

    api_key: str | None = None
    model: str = DEFAULT_LLM_MODEL
    small_model: str = SMALL_LLM_MODEL
    temperature: float = 0.0
    azure_openai_endpoint: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_use_managed_identity: bool = False

    @classmethod
    def from_env(cls) -> "GraphitiLLMConfig":
        """Create LLM configuration from environment variables."""
        # Get model from environment, or use default if not set or empty
        model_env = os.environ.get("MODEL_NAME", "")
        model = model_env if model_env.strip() else DEFAULT_LLM_MODEL

        # Get small_model from environment, or use default if not set or empty
        small_model_env = os.environ.get("SMALL_MODEL_NAME", "")
        small_model = small_model_env if small_model_env.strip() else SMALL_LLM_MODEL

        azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", None)
        azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", None)
        azure_openai_deployment_name = os.environ.get(
            "AZURE_OPENAI_DEPLOYMENT_NAME", None
        )
        azure_openai_use_managed_identity = (
            os.environ.get("AZURE_OPENAI_USE_MANAGED_IDENTITY", "false").lower()
            == "true"
        )

        if azure_openai_endpoint is None:
            # Setup for OpenAI API
            # Log if empty model was provided
            if model_env == "":
                logger.debug(
                    f"MODEL_NAME environment variable not set, using default: {DEFAULT_LLM_MODEL}"
                )
            elif not model_env.strip():
                logger.warning(
                    f"Empty MODEL_NAME environment variable, using default: {DEFAULT_LLM_MODEL}"
                )

            return cls(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model=model,
                small_model=small_model,
                temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")),
            )
        else:
            # Setup for Azure OpenAI API
            # Log if empty deployment name was provided
            if azure_openai_deployment_name is None:
                logger.error(
                    "AZURE_OPENAI_DEPLOYMENT_NAME environment variable not set"
                )

                raise ValueError(
                    "AZURE_OPENAI_DEPLOYMENT_NAME environment variable not set"
                )
            if not azure_openai_use_managed_identity:
                # api key
                api_key = os.environ.get("OPENAI_API_KEY", None)
            else:
                # Managed identity
                api_key = None

            return cls(
                azure_openai_use_managed_identity=azure_openai_use_managed_identity,
                azure_openai_endpoint=azure_openai_endpoint,
                api_key=api_key,
                azure_openai_api_version=azure_openai_api_version,
                azure_openai_deployment_name=azure_openai_deployment_name,
                model=model,
                small_model=small_model,
                temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")),
            )

    @classmethod
    def from_cli_and_env(cls, args: argparse.Namespace) -> "GraphitiLLMConfig":
        """Create LLM configuration from CLI arguments, falling back to environment variables."""
        # Start with environment-based config
        config = cls.from_env()

        # CLI arguments override environment variables when provided
        if hasattr(args, "model") and args.model:
            # Only use CLI model if it's not empty
            if args.model.strip():
                config.model = args.model
            else:
                # Log that empty model was provided and default is used
                logger.warning(
                    f"Empty model name provided, using default: {DEFAULT_LLM_MODEL}"
                )

        if hasattr(args, "small_model") and args.small_model:
            if args.small_model.strip():
                config.small_model = args.small_model
            else:
                logger.warning(
                    f"Empty small_model name provided, using default: {SMALL_LLM_MODEL}"
                )

        if hasattr(args, "temperature") and args.temperature is not None:
            config.temperature = args.temperature

        return config

    def create_client(self) -> LLMClient:
        """Create an LLM client based on this configuration.

        Returns:
            LLMClient instance
        """

        if self.azure_openai_endpoint is not None:
            # Azure OpenAI API setup
            if self.azure_openai_use_managed_identity:
                # Use managed identity for authentication
                token_provider = create_azure_credential_token_provider()
                return AzureOpenAILLMClient(
                    azure_client=AsyncAzureOpenAI(
                        azure_endpoint=self.azure_openai_endpoint,
                        azure_deployment=self.azure_openai_deployment_name,
                        api_version=self.azure_openai_api_version,
                        azure_ad_token_provider=token_provider,
                    ),
                    config=LLMConfig(
                        api_key=self.api_key,
                        model=self.model,
                        small_model=self.small_model,
                        temperature=self.temperature,
                    ),
                )
            elif self.api_key:
                # Use API key for authentication
                return AzureOpenAILLMClient(
                    azure_client=AsyncAzureOpenAI(
                        azure_endpoint=self.azure_openai_endpoint,
                        azure_deployment=self.azure_openai_deployment_name,
                        api_version=self.azure_openai_api_version,
                        api_key=self.api_key,
                    ),
                    config=LLMConfig(
                        api_key=self.api_key,
                        model=self.model,
                        small_model=self.small_model,
                        temperature=self.temperature,
                    ),
                )
            else:
                raise ValueError(
                    "OPENAI_API_KEY must be set when using Azure OpenAI API"
                )

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI API")

        llm_client_config = LLMConfig(
            api_key=self.api_key, model=self.model, small_model=self.small_model
        )

        # Set temperature
        llm_client_config.temperature = self.temperature

        return OpenAIClient(config=llm_client_config)


class GraphitiEmbedderConfig(BaseModel):
    """Configuration for the embedder client.

    Centralizes all embedding-related configuration parameters.
    """

    model: str = DEFAULT_EMBEDDER_MODEL
    api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_use_managed_identity: bool = False

    @classmethod
    def from_env(cls) -> "GraphitiEmbedderConfig":
        """Create embedder configuration from environment variables."""

        # Get model from environment, or use default if not set or empty
        model_env = os.environ.get("EMBEDDER_MODEL_NAME", "")
        model = model_env if model_env.strip() else DEFAULT_EMBEDDER_MODEL

        azure_openai_endpoint = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT", None)
        azure_openai_api_version = os.environ.get(
            "AZURE_OPENAI_EMBEDDING_API_VERSION", None
        )
        azure_openai_deployment_name = os.environ.get(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", None
        )
        azure_openai_use_managed_identity = (
            os.environ.get("AZURE_OPENAI_USE_MANAGED_IDENTITY", "false").lower()
            == "true"
        )
        if azure_openai_endpoint is not None:
            # Setup for Azure OpenAI API
            # Log if empty deployment name was provided
            azure_openai_deployment_name = os.environ.get(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", None
            )
            if azure_openai_deployment_name is None:
                logger.error(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME environment variable not set"
                )

                raise ValueError(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME environment variable not set"
                )

            if not azure_openai_use_managed_identity:
                # api key
                api_key = os.environ.get(
                    "AZURE_OPENAI_EMBEDDING_API_KEY", None
                ) or os.environ.get("OPENAI_API_KEY", None)
            else:
                # Managed identity
                api_key = None

            return cls(
                azure_openai_use_managed_identity=azure_openai_use_managed_identity,
                azure_openai_endpoint=azure_openai_endpoint,
                api_key=api_key,
                azure_openai_api_version=azure_openai_api_version,
                azure_openai_deployment_name=azure_openai_deployment_name,
            )
        else:
            return cls(
                model=model,
                api_key=os.environ.get("OPENAI_API_KEY"),
            )

    def create_client(self) -> EmbedderClient | None:
        if self.azure_openai_endpoint is not None:
            # Azure OpenAI API setup
            if self.azure_openai_use_managed_identity:
                # Use managed identity for authentication
                token_provider = create_azure_credential_token_provider()
                return AzureOpenAIEmbedderClient(
                    azure_client=AsyncAzureOpenAI(
                        azure_endpoint=self.azure_openai_endpoint,
                        azure_deployment=self.azure_openai_deployment_name,
                        api_version=self.azure_openai_api_version,
                        azure_ad_token_provider=token_provider,
                    ),
                    model=self.model,
                )
            elif self.api_key:
                # Use API key for authentication
                return AzureOpenAIEmbedderClient(
                    azure_client=AsyncAzureOpenAI(
                        azure_endpoint=self.azure_openai_endpoint,
                        azure_deployment=self.azure_openai_deployment_name,
                        api_version=self.azure_openai_api_version,
                        api_key=self.api_key,
                    ),
                    model=self.model,
                )
            else:
                logger.error("OPENAI_API_KEY must be set when using Azure OpenAI API")
                return None
        else:
            # OpenAI API setup
            if not self.api_key:
                return None

            embedder_config = OpenAIEmbedderConfig(
                api_key=self.api_key, embedding_model=self.model
            )

            return OpenAIEmbedder(config=embedder_config)


class DatabaseConfig(BaseModel):
    """Configuration for database connection (Neo4j or FalkorDB)."""

    # Neo4j-specific settings (only used if GRAPHITI_DB_TYPE=neo4j)
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"

    # Database name (used by both Neo4j and FalkorDB)
    database: str | None = None

    # Database type from environment
    db_type: str = "neo4j"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database configuration from environment variables."""
        db_type = os.getenv("GRAPHITI_DB_TYPE", "neo4j").lower()

        # For FalkorDB, we don't need URI/user/password as it uses environment-based config
        # But we still collect them for backward compatibility and potential override
        return cls(
            db_type=db_type,
            uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD", "password"),
            database=os.environ.get("GRAPHITI_DB_NAME"),
        )


class GraphitiConfig(BaseModel):
    """Configuration for Graphiti client.

    Centralizes all configuration parameters for the Graphiti client.
    """

    llm: GraphitiLLMConfig = Field(default_factory=GraphitiLLMConfig)
    embedder: GraphitiEmbedderConfig = Field(default_factory=GraphitiEmbedderConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    group_id: str | None = None
    use_custom_entities: bool = False
    destroy_graph: bool = False

    @classmethod
    def from_env(cls) -> "GraphitiConfig":
        """Create a configuration instance from environment variables."""
        return cls(
            llm=GraphitiLLMConfig.from_env(),
            embedder=GraphitiEmbedderConfig.from_env(),
            database=DatabaseConfig.from_env(),
        )

    @classmethod
    def from_cli_and_env(cls, args: argparse.Namespace) -> "GraphitiConfig":
        """Create configuration from CLI arguments, falling back to environment variables."""
        # Start with environment configuration
        config = cls.from_env()

        # Apply CLI overrides
        if args.group_id:
            config.group_id = args.group_id
        else:
            config.group_id = "default"

        config.use_custom_entities = args.use_custom_entities
        config.destroy_graph = args.destroy_graph

        # Update LLM config using CLI args
        config.llm = GraphitiLLMConfig.from_cli_and_env(args)

        return config


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    transport: str = "sse"  # Default to SSE transport

    @classmethod
    def from_cli(cls, args: argparse.Namespace) -> "MCPConfig":
        """Create MCP configuration from CLI arguments."""
        return cls(transport=args.transport)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create global config instance - will be properly initialized later
config = GraphitiConfig.from_env()

# MCP server instructions
GRAPHITI_MCP_INSTRUCTIONS = """
Graphiti is a memory service for AI agents built on a knowledge graph. Graphiti performs well
with dynamic data such as user interactions, changing enterprise data, and external information.

Graphiti transforms information into a richly connected knowledge network, allowing you to 
capture relationships between concepts, entities, and information. The system organizes data as episodes 
(content snippets), nodes (entities), and facts (relationships between entities), creating a dynamic, 
queryable memory store that evolves with new information. Graphiti supports multiple data formats, including 
structured JSON data, enabling seamless integration with existing data pipelines and systems.

Facts contain temporal metadata, allowing you to track the time of creation and whether a fact is invalid 
(superseded by new information).

Key capabilities:
1. Add episodes (text, messages, or JSON) to the knowledge graph with the add_memory tool
2. Search for nodes (entities) in the graph using natural language queries with search_nodes
3. Find relevant facts (relationships between entities) with search_facts
4. Retrieve specific entity edges or episodes by UUID
5. Manage the knowledge graph with tools like delete_episode, delete_entity_edge, and clear_graph

The server connects to a database for persistent storage and uses language models for certain operations. 
Each piece of information is organized by group_id, allowing you to maintain separate knowledge domains.

When adding information, provide descriptive names and detailed content to improve search quality. 
When searching, use specific queries and consider filtering by group_id for more relevant results.

For optimal performance, ensure the database is properly configured and accessible, and valid 
API keys are provided for any language model operations.
"""

# MCP server instance
mcp = FastMCP(
    "Graphiti Agent Memory",
    instructions=GRAPHITI_MCP_INSTRUCTIONS,
)

# Initialize Graphiti client
graphiti_client: Graphiti | None = None


async def initialize_graphiti():
    """Initialize the Graphiti client with optimized settings for the configured database."""
    global graphiti_client, config

    init_start_time = time.time()
    logger.info(
        f"Starting Graphiti initialization with {config.database.db_type} database..."
    )

    try:
        # Parallelize client creation where possible
        async def create_llm_client():
            if config.llm.api_key or config.llm.azure_openai_endpoint:
                return config.llm.create_client()
            return None

        async def create_embedder_client():
            return config.embedder.create_client()

        # Run client creation in parallel
        llm_client_task = asyncio.create_task(create_llm_client())
        embedder_client_task = asyncio.create_task(create_embedder_client())

        llm_client = await llm_client_task
        embedder_client = await embedder_client_task

        # Validate requirements
        if not llm_client and config.use_custom_entities:
            raise ValueError(
                "OPENAI_API_KEY must be set when custom entities are enabled"
            )

        # Database validation based on type
        if config.database.db_type == "neo4j":
            if (
                not config.database.uri
                or not config.database.user
                or not config.database.password
            ):
                raise ValueError(
                    "NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set for Neo4j"
                )
        elif config.database.db_type == "falkordb":
            # FalkorDB-specific validation
            falkor_url = os.getenv("FALKORDB_URL")
            if not falkor_url:
                logger.warning(
                    "FALKORDB_URL not set, using default: redis://localhost:6379. "
                    "Set FALKORDB_URL for custom FalkorDB connection."
                )
            else:
                logger.info(f"Using FalkorDB URL: {falkor_url}")

            # Check if FalkorDB module is available
            try:
                from graphiti_core.driver.falkordb_driver import FalkorDriver

                logger.debug("FalkorDB driver module available")
            except ImportError as e:
                raise ImportError(
                    "FalkorDB driver not available. Install with: pip install graphiti-core[falkordb]"
                ) from e

        # Initialize Graphiti client using DriverFactory
        driver_start_time = time.time()

        # For Neo4j, pass the URI, user, password
        # For FalkorDB, these will be ignored and environment config will be used
        graphiti_kwargs = {
            "llm_client": llm_client,
            "embedder": embedder_client,
            "max_coroutines": SEMAPHORE_LIMIT,
        }

        if config.database.db_type == "neo4j":
            graphiti_kwargs.update(
                {
                    "uri": config.database.uri,
                    "user": config.database.user,
                    "password": config.database.password,
                }
            )
        elif config.database.db_type == "falkordb":
            # For FalkorDB, use the FalkorDB URL directly
            falkor_url = os.getenv("FALKORDB_URL")
            if falkor_url:
                graphiti_kwargs.update(
                    {
                        "uri": falkor_url,
                        "user": None,  # FalkorDB uses Redis protocol, typically no auth
                        "password": None,
                    }
                )
            else:
                logger.error("FALKORDB_URL not configured for FalkorDB database type")
                raise ValueError("FALKORDB_URL must be provided when using FalkorDB")

        if config.database.database:
            graphiti_kwargs["database"] = config.database.database

        try:
            graphiti_client = Graphiti(**graphiti_kwargs)
        except TypeError as e:
            if "database" in str(e) and "database" in graphiti_kwargs:
                # Remove database parameter and try again (fallback for older versions)
                logger.warning(
                    f"Graphiti constructor doesn't accept 'database' parameter, retrying without it: {e}"
                )
                del graphiti_kwargs["database"]
                graphiti_client = Graphiti(**graphiti_kwargs)
            else:
                raise

        driver_init_time = time.time() - driver_start_time
        logger.info(f"Database driver initialization took {driver_init_time:.2f}s")

        # Clear graph if requested (before building indices for better performance)
        if config.destroy_graph:
            clear_start_time = time.time()
            logger.info("Destroying graph...")
            await clear_data(graphiti_client.driver)
            clear_time = time.time() - clear_start_time
            logger.info(f"Graph clearing took {clear_time:.2f}s")

        # Build indices and constraints
        indices_start_time = time.time()
        await graphiti_client.build_indices_and_constraints()
        indices_time = time.time() - indices_start_time
        logger.info(f"Index and constraint building took {indices_time:.2f}s")

        total_init_time = time.time() - init_start_time
        logger.info(
            f"Graphiti client initialized successfully in {total_init_time:.2f}s"
        )

        # Log configuration details for transparency
        logger.info(f"Database type: {config.database.db_type}")
        if config.database.db_type == "neo4j":
            logger.info(f"Neo4j URI: {config.database.uri}")

        if llm_client:
            logger.info(f"LLM model: {config.llm.model}")
            logger.info(f"Temperature: {config.llm.temperature}")
        else:
            logger.info("No LLM client configured - entity extraction will be limited")

        if embedder_client:
            logger.info(f"Embedder model: {config.embedder.model}")
        else:
            logger.info(
                "No embedder client configured - semantic search will be limited"
            )

        logger.info(f"Group ID: {config.group_id}")
        logger.info(
            f"Custom entity extraction: {'enabled' if config.use_custom_entities else 'disabled'}"
        )
        logger.info(f"Concurrency limit: {SEMAPHORE_LIMIT}")

        # Performance target check for FalkorDB
        if config.database.db_type == "falkordb" and total_init_time > 5.0:
            logger.warning(
                f"FalkorDB initialization took {total_init_time:.2f}s (target: <5s)"
            )
        elif config.database.db_type == "falkordb":
            logger.info(
                f"FalkorDB initialization target achieved: {total_init_time:.2f}s < 5s"
            )

    except ImportError as e:
        init_time = time.time() - init_start_time
        if "falkordb" in str(e).lower():
            logger.error(
                f"FalkorDB driver not available after {init_time:.2f}s. "
                f"Install with: pip install graphiti-core[falkordb]. Error: {str(e)}"
            )
        else:
            logger.error(f"Missing dependency after {init_time:.2f}s: {str(e)}")
        raise
    except ConnectionRefusedError as e:
        init_time = time.time() - init_start_time
        db_type = config.database.db_type
        if db_type == "falkordb":
            logger.error(
                f"Cannot connect to FalkorDB after {init_time:.2f}s. "
                f"Ensure FalkorDB is running at {os.getenv('FALKORDB_URL', 'redis://localhost:6379')}. "
                f"Start with: docker run -p 6379:6379 falkordb/falkordb:latest"
            )
        elif db_type == "neo4j":
            logger.error(
                f"Cannot connect to Neo4j after {init_time:.2f}s. "
                f"Ensure Neo4j is running at {config.database.uri}. "
                f"Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables."
            )
        else:
            logger.error(
                f"Database connection refused after {init_time:.2f}s: {str(e)}"
            )
        raise
    except ValueError as e:
        init_time = time.time() - init_start_time
        error_msg = str(e).lower()
        if "openai_api_key" in error_msg:
            logger.error(
                f"OpenAI API configuration error after {init_time:.2f}s: {str(e)}. "
                f"Set OPENAI_API_KEY environment variable or disable custom entities with --no-custom-entities"
            )
        elif "neo4j" in error_msg or "uri" in error_msg:
            logger.error(
                f"Neo4j configuration error after {init_time:.2f}s: {str(e)}. "
                f"Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables."
            )
        else:
            logger.error(f"Configuration error after {init_time:.2f}s: {str(e)}")
        raise
    except Exception as e:
        init_time = time.time() - init_start_time
        db_type = (
            getattr(config.database, "db_type", "unknown")
            if hasattr(config, "database")
            else "unknown"
        )
        logger.error(
            f"Failed to initialize Graphiti with {db_type} after {init_time:.2f}s: {str(e)}"
        )

        # Add helpful hints for common issues
        if "timeout" in str(e).lower():
            if db_type == "falkordb":
                logger.error(
                    "Hint: FalkorDB connection timeout. Check if FalkorDB server is responsive."
                )
            elif db_type == "neo4j":
                logger.error(
                    "Hint: Neo4j connection timeout. Check if Neo4j server is responsive."
                )
        elif "authentication" in str(e).lower():
            if db_type == "neo4j":
                logger.error(
                    "Hint: Neo4j authentication failed. Check NEO4J_USER and NEO4J_PASSWORD."
                )
        elif "permission" in str(e).lower() or "denied" in str(e).lower():
            logger.error(
                "Hint: Database permission denied. Check user credentials and database access rights."
            )

        raise


def format_fact_result(edge: EntityEdge) -> dict[str, Any]:
    """Format an entity edge into a readable result.

    Since EntityEdge is a Pydantic BaseModel, we can use its built-in serialization capabilities.

    Args:
        edge: The EntityEdge to format

    Returns:
        A dictionary representation of the edge with serialized dates and excluded embeddings
    """
    result = edge.model_dump(
        mode="json",
        exclude={
            "fact_embedding",
        },
    )
    result.get("attributes", {}).pop("fact_embedding", None)
    return result


# Dictionary to store queues for each group_id
# Each queue is a list of tasks to be processed sequentially
episode_queues: dict[str, asyncio.Queue] = {}
# Dictionary to track if a worker is running for each group_id
queue_workers: dict[str, bool] = {}


async def process_episode_queue(group_id: str):
    """Process episodes for a specific group_id sequentially.

    This function runs as a long-lived task that processes episodes
    from the queue one at a time.
    """
    global queue_workers

    logger.info(f"Starting episode queue worker for group_id: {group_id}")
    queue_workers[group_id] = True

    try:
        while True:
            # Get the next episode processing function from the queue
            # This will wait if the queue is empty
            process_func = await episode_queues[group_id].get()

            try:
                # Process the episode
                await process_func()
            except Exception as e:
                logger.error(
                    f"Error processing queued episode for group_id {group_id}: {str(e)}"
                )
            finally:
                # Mark the task as done regardless of success/failure
                episode_queues[group_id].task_done()
    except asyncio.CancelledError:
        logger.info(f"Episode queue worker for group_id {group_id} was cancelled")
    except Exception as e:
        logger.error(
            f"Unexpected error in queue worker for group_id {group_id}: {str(e)}"
        )
    finally:
        queue_workers[group_id] = False
        logger.info(f"Stopped episode queue worker for group_id: {group_id}")


@mcp.tool()
async def add_memory(
    name: str,
    episode_body: str,
    group_id: str | None = None,
    source: str = "text",
    source_description: str = "",
    uuid: str | None = None,
) -> SuccessResponse | ErrorResponse:
    """Add an episode to memory. This is the primary way to add information to the graph.

    This function returns immediately and processes the episode addition in the background.
    Episodes for the same group_id are processed sequentially to avoid race conditions.

    Args:
        name (str): Name of the episode
        episode_body (str): The content of the episode to persist to memory. When source='json', this must be a
                           properly escaped JSON string, not a raw Python dictionary. The JSON data will be
                           automatically processed to extract entities and relationships.
        group_id (str, optional): A unique ID for this graph. If not provided, uses the default group_id from CLI
                                 or a generated one.
        source (str, optional): Source type, must be one of:
                               - 'text': For plain text content (default)
                               - 'json': For structured data
                               - 'message': For conversation-style content
        source_description (str, optional): Description of the source
        uuid (str, optional): Optional UUID for the episode

    Examples:
        # Adding plain text content
        add_memory(
            name="Company News",
            episode_body="Acme Corp announced a new product line today.",
            source="text",
            source_description="news article",
            group_id="some_arbitrary_string"
        )

        # Adding structured JSON data
        # NOTE: episode_body must be a properly escaped JSON string. Note the triple backslashes
        add_memory(
            name="Customer Profile",
            episode_body="{\\\"company\\\": {\\\"name\\\": \\\"Acme Technologies\\\"}, \\\"products\\\": [{\\\"id\\\": \\\"P001\\\", \\\"name\\\": \\\"CloudSync\\\"}, {\\\"id\\\": \\\"P002\\\", \\\"name\\\": \\\"DataMiner\\\"}]}",
            source="json",
            source_description="CRM data"
        )

        # Adding message-style content
        add_memory(
            name="Customer Conversation",
            episode_body="user: What's your return policy?\nassistant: You can return items within 30 days.",
            source="message",
            source_description="chat transcript",
            group_id="some_arbitrary_string"
        )

    Notes:
        When using source='json':
        - The JSON must be a properly escaped string, not a raw Python dictionary
        - The JSON will be automatically processed to extract entities and relationships
        - Complex nested structures are supported (arrays, nested objects, mixed data types), but keep nesting to a minimum
        - Entities will be created from appropriate JSON properties
        - Relationships between entities will be established based on the JSON structure
    """
    global graphiti_client, episode_queues, queue_workers

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # Map string source to EpisodeType enum
        source_type = EpisodeType.text
        if source.lower() == "message":
            source_type = EpisodeType.message
        elif source.lower() == "json":
            source_type = EpisodeType.json

        # Use the provided group_id or fall back to the default from config
        effective_group_id = group_id if group_id is not None else config.group_id

        # Cast group_id to str to satisfy type checker
        # The Graphiti client expects a str for group_id, not Optional[str]
        group_id_str = str(effective_group_id) if effective_group_id is not None else ""

        # We've already checked that graphiti_client is not None above
        # This assert statement helps type checkers understand that graphiti_client is defined
        assert graphiti_client is not None, "graphiti_client should not be None here"

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Define the episode processing function
        async def process_episode():
            try:
                logger.info(
                    f"Processing queued episode '{name}' for group_id: {group_id_str}"
                )
                # Use all entity types if use_custom_entities is enabled, otherwise use empty dict
                entity_types = ENTITY_TYPES if config.use_custom_entities else {}

                await client.add_episode(
                    name=name,
                    episode_body=episode_body,
                    source=source_type,
                    source_description=source_description,
                    group_id=group_id_str,  # Using the string version of group_id
                    uuid=uuid,
                    reference_time=datetime.now(timezone.utc),
                    entity_types=entity_types,
                )
                logger.info(f"Episode '{name}' added successfully")

                logger.info(f"Episode '{name}' processed successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Error processing episode '{name}' for group_id {group_id_str}: {error_msg}"
                )

        # Initialize queue for this group_id if it doesn't exist
        if group_id_str not in episode_queues:
            episode_queues[group_id_str] = asyncio.Queue()

        # Add the episode processing function to the queue
        await episode_queues[group_id_str].put(process_episode)

        # Start a worker for this queue if one isn't already running
        if not queue_workers.get(group_id_str, False):
            asyncio.create_task(process_episode_queue(group_id_str))

        # Return immediately with a success message
        return SuccessResponse(
            message=f"Episode '{name}' queued for processing (position: {episode_queues[group_id_str].qsize()})"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error queuing episode task: {error_msg}")
        return ErrorResponse(error=f"Error queuing episode task: {error_msg}")


@mcp.tool()
async def search_memory_nodes(
    query: str,
    group_ids: list[str] | None = None,
    max_nodes: int = 10,
    center_node_uuid: str | None = None,
    entity: str = "",  # cursor seems to break with None
) -> NodeSearchResponse | ErrorResponse:
    """Search the graph memory for relevant node summaries.
    These contain a summary of all of a node's relationships with other nodes.

    Note: entity is a single entity type to filter results (permitted: "Preference", "Procedure").

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_nodes: Maximum number of nodes to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
        entity: Optional single entity type to filter results (permitted: "Preference", "Procedure")
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # Use the provided group_ids or fall back to the default from config if none provided
        effective_group_ids = (
            group_ids
            if group_ids is not None
            else [config.group_id] if config.group_id else []
        )

        # Configure the search
        if center_node_uuid is not None:
            search_config = NODE_HYBRID_SEARCH_NODE_DISTANCE.model_copy(deep=True)
        else:
            search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = max_nodes

        filters = SearchFilters()
        if entity != "":
            filters.node_labels = [entity]

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Perform the search using the _search method
        search_results = await client._search(
            query=query,
            config=search_config,
            group_ids=effective_group_ids,
            center_node_uuid=center_node_uuid,
            search_filter=filters,
        )

        if not search_results.nodes:
            return NodeSearchResponse(message="No relevant nodes found", nodes=[])

        # Format the node results
        formatted_nodes: list[NodeResult] = [
            {
                "uuid": node.uuid,
                "name": node.name,
                "summary": node.summary if hasattr(node, "summary") else "",
                "labels": node.labels if hasattr(node, "labels") else [],
                "group_id": node.group_id,
                "created_at": node.created_at.isoformat(),
                "attributes": node.attributes if hasattr(node, "attributes") else {},
            }
            for node in search_results.nodes
        ]

        return NodeSearchResponse(
            message="Nodes retrieved successfully", nodes=formatted_nodes
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching nodes: {error_msg}")
        return ErrorResponse(error=f"Error searching nodes: {error_msg}")


@mcp.tool()
async def search_memory_facts(
    query: str,
    group_ids: list[str] | None = None,
    max_facts: int = 10,
    center_node_uuid: str | None = None,
) -> FactSearchResponse | ErrorResponse:
    """Search the graph memory for relevant facts.

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_facts: Maximum number of facts to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # Validate max_facts parameter
        if max_facts <= 0:
            return ErrorResponse(error="max_facts must be a positive integer")

        # Use the provided group_ids or fall back to the default from config if none provided
        effective_group_ids = (
            group_ids
            if group_ids is not None
            else [config.group_id] if config.group_id else []
        )

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        relevant_edges = await client.search(
            group_ids=effective_group_ids,
            query=query,
            num_results=max_facts,
            center_node_uuid=center_node_uuid,
        )

        if not relevant_edges:
            return FactSearchResponse(message="No relevant facts found", facts=[])

        facts = [format_fact_result(edge) for edge in relevant_edges]
        return FactSearchResponse(message="Facts retrieved successfully", facts=facts)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching facts: {error_msg}")
        return ErrorResponse(error=f"Error searching facts: {error_msg}")


@mcp.tool()
async def delete_entity_edge(uuid: str) -> SuccessResponse | ErrorResponse:
    """Delete an entity edge from the graph memory.

    Args:
        uuid: UUID of the entity edge to delete
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the entity edge by UUID
        entity_edge = await EntityEdge.get_by_uuid(client.driver, uuid)
        # Delete the edge using its delete method
        await entity_edge.delete(client.driver)
        return SuccessResponse(
            message=f"Entity edge with UUID {uuid} deleted successfully"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error deleting entity edge: {error_msg}")
        return ErrorResponse(error=f"Error deleting entity edge: {error_msg}")


@mcp.tool()
async def delete_episode(uuid: str) -> SuccessResponse | ErrorResponse:
    """Delete an episode from the graph memory.

    Args:
        uuid: UUID of the episode to delete
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the episodic node by UUID - EpisodicNode is already imported at the top
        episodic_node = await EpisodicNode.get_by_uuid(client.driver, uuid)
        # Delete the node using its delete method
        await episodic_node.delete(client.driver)
        return SuccessResponse(message=f"Episode with UUID {uuid} deleted successfully")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error deleting episode: {error_msg}")
        return ErrorResponse(error=f"Error deleting episode: {error_msg}")


@mcp.tool()
async def get_entity_edge(uuid: str) -> dict[str, Any] | ErrorResponse:
    """Get an entity edge from the graph memory by its UUID.

    Args:
        uuid: UUID of the entity edge to retrieve
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the entity edge directly using the EntityEdge class method
        entity_edge = await EntityEdge.get_by_uuid(client.driver, uuid)

        # Use the format_fact_result function to serialize the edge
        # Return the Python dict directly - MCP will handle serialization
        return format_fact_result(entity_edge)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting entity edge: {error_msg}")
        return ErrorResponse(error=f"Error getting entity edge: {error_msg}")


@mcp.tool()
async def get_episodes(
    group_id: str | None = None, last_n: int = 10
) -> list[dict[str, Any]] | EpisodeSearchResponse | ErrorResponse:
    """Get the most recent memory episodes for a specific group.

    Args:
        group_id: ID of the group to retrieve episodes from. If not provided, uses the default group_id.
        last_n: Number of most recent episodes to retrieve (default: 10)
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # Use the provided group_id or fall back to the default from config
        effective_group_id = group_id if group_id is not None else config.group_id

        if not isinstance(effective_group_id, str):
            return ErrorResponse(error="Group ID must be a string")

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        episodes = await client.retrieve_episodes(
            group_ids=[effective_group_id],
            last_n=last_n,
            reference_time=datetime.now(timezone.utc),
        )

        if not episodes:
            return EpisodeSearchResponse(
                message=f"No episodes found for group {effective_group_id}", episodes=[]
            )

        # Use Pydantic's model_dump method for EpisodicNode serialization
        formatted_episodes = [
            # Use mode='json' to handle datetime serialization
            episode.model_dump(mode="json")
            for episode in episodes
        ]

        # Return the Python list directly - MCP will handle serialization
        return formatted_episodes
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting episodes: {error_msg}")
        return ErrorResponse(error=f"Error getting episodes: {error_msg}")


@mcp.tool()
async def clear_graph() -> SuccessResponse | ErrorResponse:
    """Clear all data from the graph memory and rebuild indices."""
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error="Graphiti client not initialized")

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # clear_data is already imported at the top
        await clear_data(client.driver)
        await client.build_indices_and_constraints()
        return SuccessResponse(message="Graph cleared successfully and indices rebuilt")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error clearing graph: {error_msg}")
        return ErrorResponse(error=f"Error clearing graph: {error_msg}")


@mcp.resource("http://graphiti/status")
async def get_status() -> StatusResponse:
    """Get the status of the Graphiti MCP server and database connection."""
    global graphiti_client

    if graphiti_client is None:
        return StatusResponse(status="error", message="Graphiti client not initialized")

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Test database connection with timing
        connection_start_time = time.time()

        # Database-specific connection verification
        if config.database.db_type == "neo4j":
            await client.driver.client.verify_connectivity()  # type: ignore
        elif config.database.db_type == "falkordb":
            # FalkorDB doesn't have verify_connectivity, so test with a simple query
            try:
                await client.driver.execute_query("RETURN 1")
            except Exception as e:
                raise ConnectionError(
                    f"FalkorDB connection test failed: {str(e)}"
                ) from e

        connection_time = time.time() - connection_start_time

        db_type = config.database.db_type
        message = f"Graphiti MCP server is running and connected to {db_type} (connection check: {connection_time:.3f}s)"

        return StatusResponse(status="ok", message=message)
    except Exception as e:
        error_msg = str(e)
        db_type = config.database.db_type
        logger.error(f"Error checking {db_type} connection: {error_msg}")
        return StatusResponse(
            status="error",
            message=f"Graphiti MCP server is running but {db_type} connection failed: {error_msg}",
        )


async def initialize_server() -> MCPConfig:
    """Parse CLI arguments and initialize the Graphiti server configuration."""
    global config

    parser = argparse.ArgumentParser(
        description="Run the Graphiti MCP server with optional LLM client"
    )
    parser.add_argument(
        "--group-id",
        help="Namespace for the graph. This is an arbitrary string used to organize related data. "
        "If not provided, a random UUID will be generated.",
    )
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport to use for communication with the client. (default: sse)",
    )
    parser.add_argument(
        "--model",
        help=f"Model name to use with the LLM client. (default: {DEFAULT_LLM_MODEL})",
    )
    parser.add_argument(
        "--small-model",
        help=f"Small model name to use with the LLM client. (default: {SMALL_LLM_MODEL})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature setting for the LLM (0.0-2.0). Lower values make output more deterministic. (default: 0.7)",
    )
    parser.add_argument(
        "--destroy-graph", action="store_true", help="Destroy all Graphiti graphs"
    )
    parser.add_argument(
        "--use-custom-entities",
        action="store_true",
        help="Enable entity extraction using the predefined ENTITY_TYPES",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_SERVER_HOST"),
        help="Host to bind the MCP server to (default: MCP_SERVER_HOST environment variable)",
    )

    args = parser.parse_args()

    # Build configuration from CLI arguments and environment variables
    config = GraphitiConfig.from_cli_and_env(args)

    # Log the group ID configuration
    if args.group_id:
        logger.info(f"Using provided group_id: {config.group_id}")
    else:
        logger.info(f"Generated random group_id: {config.group_id}")

    # Log entity extraction configuration
    if config.use_custom_entities:
        logger.info("Entity extraction enabled using predefined ENTITY_TYPES")
    else:
        logger.info("Entity extraction disabled (no custom entities will be used)")

    # Initialize Graphiti
    await initialize_graphiti()

    if args.host:
        logger.info(f"Setting MCP server host to: {args.host}")
        # Set MCP server host from CLI or env
        mcp.settings.host = args.host

    # Return MCP configuration
    return MCPConfig.from_cli(args)


async def run_mcp_server():
    """Run the MCP server in the current event loop."""
    # Initialize the server
    mcp_config = await initialize_server()

    # Run the server with stdio transport for MCP in the same event loop
    logger.info(f"Starting MCP server with transport: {mcp_config.transport}")
    if mcp_config.transport == "stdio":
        await mcp.run_stdio_async()
    elif mcp_config.transport == "sse":
        logger.info(
            f"Running MCP server with SSE transport on {mcp.settings.host}:{mcp.settings.port}"
        )
        await mcp.run_sse_async()


def main():
    """Main function to run the Graphiti MCP server."""
    try:
        # Run everything in a single event loop
        asyncio.run(run_mcp_server())
    except Exception as e:
        logger.error(f"Error initializing Graphiti MCP server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
