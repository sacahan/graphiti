---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Project Structure

## Root Directory Layout

```
graphiti/
├── .claude/                    # Claude Code PM system
├── .env.example               # Environment configuration template
├── .git/                      # Git repository metadata
├── .github/                   # GitHub workflows and templates
├── .gitignore                 # Git ignore patterns
├── AGENTS.md                  # Agent configuration documentation
├── CLAUDE.md                  # Claude Code project instructions
├── CODE_OF_CONDUCT.md         # Community guidelines
├── COMMANDS.md                # PM system commands documentation
├── conftest.py               # pytest configuration
├── CONTRIBUTING.md           # Contribution guidelines
├── depot.json                # Depot configuration
├── docker-compose.test.yml   # Testing Docker configuration
├── docker-compose.yml        # Production Docker configuration
├── Dockerfile                # Container build instructions
├── ellipsis.yaml            # Ellipsis configuration
├── examples/                 # Example implementations
├── graphiti_core/           # Core library implementation
├── images/                  # Documentation assets
├── LICENSE                  # Apache 2.0 license
├── Makefile                 # Build and development commands
├── mcp_server/             # MCP server implementation
├── poetry.lock             # Poetry dependency lock file
├── py.typed                # PEP 561 typing marker
├── pyproject.toml          # Project configuration
├── pytest.ini             # pytest configuration
├── README.md               # Project documentation
├── SECURITY.md             # Security policy
├── server/                 # FastAPI REST service
├── signatures/             # Type signatures
├── tests/                  # Test suite
├── uv.lock                 # UV dependency lock file
└── Zep-CLA.md             # Contributor License Agreement
```

## Core Library Structure (`graphiti_core/`)

### Primary Modules

- **`graphiti.py`** - Main orchestration class
- **`nodes.py`** - Graph node data structures
- **`edges.py`** - Graph edge data structures

### Key Subsystems

- **`driver/`** - Database drivers (Neo4j, FalkorDB, Kuzu, Neptune)
- **`llm_client/`** - LLM integrations (OpenAI, Anthropic, Gemini, Groq)
- **`embedder/`** - Embedding providers
- **`search/`** - Hybrid search implementation
- **`prompts/`** - LLM prompt templates
- **`utils/`** - Utilities and maintenance operations
- **`cross_encoder/`** - Reranking implementations
- **`telemetry/`** - Usage analytics

## Service Architecture

### Server (`server/`)

- **FastAPI-based REST API**
- **`graph_service/main.py`** - Application entry point
- **`routers/`** - API endpoint definitions
- **`dto/`** - Data transfer objects

### MCP Server (`mcp_server/`)

- **Model Context Protocol implementation**
- **`graphiti_mcp_server.py`** - MCP server main
- **Docker deployment support**

## Configuration Files

### Python Project Configuration

- **`pyproject.toml`** - Main project configuration
  - Dependencies and optional extras
  - Build system configuration
  - Tool settings (ruff, pyright, pytest)
- **`uv.lock`** - UV dependency resolution
- **`poetry.lock`** - Poetry dependency resolution

### Development Tools

- **`Makefile`** - Common development commands
- **`pytest.ini`** - Test configuration
- **`conftest.py`** - Test fixtures and setup

### Deployment

- **`Dockerfile`** - Container image definition
- **`docker-compose.yml`** - Production deployment
- **`docker-compose.test.yml`** - Test environment

## Testing Structure (`tests/`)

### Test Organization

- **Unit tests** - Direct module testing
- **Integration tests** - Database-dependent tests (suffix `_int`)
- **Evaluation tests** - End-to-end validation (`evals/`)

### Test Categories

- **`llm_client/`** - LLM provider testing
- **`driver/`** - Database driver testing
- **`embedder/`** - Embedding provider testing
- **`utils/`** - Utility function testing
- **`evals/`** - Performance and accuracy evaluation

## File Naming Conventions

### Python Modules

- Snake case for module names
- Class names in PascalCase
- Function names in snake_case
- Constants in UPPER_SNAKE_CASE

### Test Files

- Mirror source structure in `tests/`
- Integration tests suffixed with `_int`
- Evaluation tests prefixed with `eval_`

### Configuration Files

- Lowercase with extensions (.toml, .yml, .ini)
- Docker files capitalized (Dockerfile)
- Markdown files in UPPERCASE.md for root docs

## Module Dependencies

### External Dependencies

- **Core:** pydantic, neo4j, openai, tenacity, numpy
- **Optional:** anthropic, groq, google-genai, falkordb, kuzu
- **Dev:** pyright, ruff, pytest, pytest-asyncio, pytest-xdist

### Internal Architecture

- Clean separation between drivers and core logic
- Pluggable LLM and embedding providers
- Modular search strategies
- Configurable telemetry system
