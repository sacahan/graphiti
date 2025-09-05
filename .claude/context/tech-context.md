---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Technical Context

## Language & Runtime

**Primary Language:** Python 3.10+  
**Version Constraint:** >=3.10,<4  
**Package Manager:** UV (with Poetry fallback)  
**Current Version:** 0.20.1

## Core Dependencies

### Essential Libraries

- **pydantic** >=2.11.5 - Data validation and serialization
- **neo4j** >=5.26.0 - Primary graph database driver
- **openai** >=1.91.0 - LLM inference and embeddings
- **tenacity** >=9.0.0 - Retry mechanisms and resilience
- **numpy** >=1.0.0 - Numerical operations
- **python-dotenv** >=1.0.1 - Environment configuration
- **posthog** >=3.0.0 - Analytics and telemetry
- **diskcache** >=5.6.3 - Local caching system

## Optional Provider Dependencies

### LLM Providers

- **anthropic** >=0.49.0 - Anthropic Claude integration
- **groq** >=0.2.0 - Groq inference API
- **google-genai** >=1.8.0 - Google Gemini integration

### Database Backends

- **neo4j** >=5.26.0 - Primary graph database (default)
- **falkordb** >=1.1.2,<2.0.0 - Redis-compatible graph database
- **kuzu** >=0.11.2 - Embedded graph database
- **langchain-aws** >=0.2.29 - Amazon Neptune integration
- **opensearch-py** >=3.0.0 - Full-text search for Neptune
- **boto3** >=1.39.16 - AWS SDK for Neptune

### Embedding Providers

- **voyageai** >=0.2.3 - Voyage AI embeddings
- **sentence-transformers** >=3.2.1 - Local transformer models

## Development Dependencies

### Code Quality Tools

- **pyright** >=1.1.404 - Type checking
- **ruff** >=0.7.1 - Linting and formatting
- **diskcache-stubs** >=5.6.3.6.20240818 - Type stubs

### Testing Framework

- **pytest** >=8.3.3 - Test runner
- **pytest-asyncio** >=0.24.0 - Async test support
- **pytest-xdist** >=3.6.1 - Parallel test execution

### Development Environment

- **ipykernel** >=6.29.5 - Jupyter kernel support
- **jupyterlab** >=4.2.4 - Interactive development

### Integration Libraries

- **langgraph** >=0.2.15 - LangChain graph workflows
- **langchain-anthropic** >=0.2.4 - LangChain Anthropic integration
- **langchain-openai** >=0.2.6 - LangChain OpenAI integration
- **langsmith** >=0.1.108 - LangChain observability
- **transformers** >=4.45.2 - Hugging Face transformers

## Tool Configuration

### Ruff (Linting & Formatting)

- **Line Length:** 100 characters
- **Quote Style:** Single quotes
- **Rules:** E (pycodestyle), F (Pyflakes), UP (pyupgrade), B (flake8-bugbear), SIM (flake8-simplify), I (isort)
- **Ignore:** E501 (line too long, handled by formatter)

### Pyright (Type Checking)

- **Mode:** Basic type checking
- **Python Version:** 3.10
- **Include:** graphiti_core/ directory only

### Pytest Configuration

- **Python Path:** Current directory
- **Parallel Execution:** pytest-xdist
- **Async Support:** pytest-asyncio
- **Integration Test Suffix:** `_int`

## Build System

### Build Backend

- **Backend:** hatchling
- **Build System:** Hatch-based packaging

### Package Management

- **Primary:** UV (modern Python package management)
- **Fallback:** Poetry (legacy support)
- **Lock Files:** uv.lock, poetry.lock

## Database Support Matrix

### Production Databases

| Database       | Version  | Driver        | Use Case                     |
| -------------- | -------- | ------------- | ---------------------------- |
| Neo4j          | >=5.26.0 | neo4j         | Primary production database  |
| FalkorDB       | >=1.1.2  | falkordb      | Redis-compatible alternative |
| Kuzu           | >=0.11.2 | kuzu          | Embedded/local development   |
| Amazon Neptune | Latest   | langchain-aws | Cloud deployment             |

### Full-Text Search

- **Neo4j:** Built-in full-text indexes
- **Amazon Neptune:** OpenSearch Serverless integration
- **Others:** BM25 keyword search implementation

## LLM Provider Support

### Supported Providers

| Provider      | Models                     | Features                            |
| ------------- | -------------------------- | ----------------------------------- |
| OpenAI        | GPT-4, GPT-3.5, Embeddings | Structured output, Function calling |
| Anthropic     | Claude 3.5 Sonnet          | High-quality reasoning              |
| Google Gemini | Gemini 1.5/2.0             | Structured output support           |
| Groq          | Mixtral, Llama             | Fast inference                      |
| Azure OpenAI  | Same as OpenAI             | Enterprise deployment               |
| Ollama        | Local models               | Privacy-focused deployment          |

### Embedding Models

- **OpenAI:** text-embedding-3-small/large
- **Voyage AI:** voyage-2, voyage-law-2
- **Google:** embedding-001
- **Local:** sentence-transformers models

## Performance Configuration

### Concurrency Control

- **SEMAPHORE_LIMIT:** Default 10 concurrent operations
- **Rate Limiting:** Built-in provider-specific handling
- **Parallel Processing:** Optional Neo4j enterprise runtime

### Caching Strategy

- **Disk Cache:** Local result caching
- **Memory Cache:** In-process optimization
- **Vector Cache:** Embedding result storage

## Environment Configuration

### Required Variables

- **OPENAI_API_KEY** - Primary LLM and embeddings
- Database credentials (varies by provider)

### Optional Variables

- **ANTHROPIC_API_KEY** - Claude access
- **GOOGLE_API_KEY** - Gemini integration
- **GROQ_API_KEY** - Groq inference
- **VOYAGE_API_KEY** - Voyage embeddings
- **SEMAPHORE_LIMIT** - Concurrency control
- **GRAPHITI_TELEMETRY_ENABLED** - Analytics opt-out
