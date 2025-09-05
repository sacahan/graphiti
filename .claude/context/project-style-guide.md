---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Code Style Standards

### Python Code Formatting

#### Ruff Configuration (Primary)

- **Line Length:** 100 characters maximum
- **Quote Style:** Single quotes preferred (`'string'` not `"string"`)
- **Indentation:** 4 spaces (no tabs)
- **Trailing Commas:** Required for multi-line structures
- **Import Sorting:** Automatic via ruff's isort integration

#### Enabled Lint Rules

- **E** - pycodestyle errors
- **F** - Pyflakes (unused imports, undefined names)
- **UP** - pyupgrade (modern Python syntax)
- **B** - flake8-bugbear (likely bugs)
- **SIM** - flake8-simplify (code simplification)
- **I** - isort (import organization)

#### Ignored Rules

- **E501** - Line too long (handled by formatter)

### Type Annotations

#### Type Checking with Pyright

- **Mode:** Basic type checking for core library
- **Python Version:** 3.10 baseline
- **Coverage:** All public APIs must be typed
- **Optional Types:** Use `Optional[T]` or `T | None` for nullable values

#### Type Style Guidelines

```python
# Preferred: Use built-in generics (Python 3.9+)
from collections.abc import Sequence
def process_items(items: list[str]) -> dict[str, int]:
    pass

# Avoid: Old-style typing imports when possible
from typing import List, Dict
def process_items(items: List[str]) -> Dict[str, int]:
    pass
```

## Naming Conventions

### Python Identifiers

#### Modules and Packages

- **Style:** `snake_case`
- **Examples:** `llm_client`, `graph_driver`, `search_strategies`

#### Classes

- **Style:** `PascalCase`
- **Examples:** `GraphitiClient`, `Neo4jDriver`, `OpenAIEmbedder`

#### Functions and Methods

- **Style:** `snake_case`
- **Examples:** `add_episode()`, `search_nodes()`, `get_temporal_edges()`

#### Variables and Attributes

- **Style:** `snake_case`
- **Examples:** `episode_count`, `embedding_model`, `query_results`

#### Constants

- **Style:** `UPPER_SNAKE_CASE`
- **Examples:** `DEFAULT_MODEL`, `MAX_RETRIES`, `SEMAPHORE_LIMIT`

#### Private Members

- **Style:** Leading underscore `_private_method()`
- **Usage:** Internal implementation details only

### File and Directory Naming

#### Python Files

- **Style:** `snake_case.py`
- **Examples:** `graphiti.py`, `llm_client.py`, `temporal_operations.py`

#### Test Files

- **Prefix:** `test_` for unit tests
- **Suffix:** `_int.py` for integration tests
- **Examples:** `test_graphiti.py`, `test_neo4j_driver_int.py`

#### Configuration Files

- **Style:** Lowercase with appropriate extensions
- **Examples:** `pyproject.toml`, `docker-compose.yml`, `pytest.ini`

#### Documentation Files

- **Style:** UPPERCASE for root documentation
- **Examples:** `README.md`, `CONTRIBUTING.md`, `LICENSE`

## Project Structure Patterns

### Module Organization

#### Core Library Structure

```python
graphiti_core/
├── __init__.py          # Public API exports
├── graphiti.py          # Main entry point
├── nodes.py            # Core data structures
├── edges.py            # Edge implementations
├── driver/             # Database abstractions
│   ├── __init__.py
│   ├── base.py        # Abstract base class
│   └── neo4j_driver.py # Concrete implementation
└── utils/              # Utility functions
    ├── __init__.py
    └── maintenance/    # Maintenance operations
```

#### Import Patterns

```python
# Public API - expose only what users need
from .graphiti import Graphiti
from .nodes import Node, EntityNode
from .edges import Edge, TemporalEdge

# Internal imports - use relative imports
from .driver.base import BaseGraphDriver
from ..utils.datetime_utils import now_utc
```

### Configuration Management

#### Environment Variables

- **Naming:** `GRAPHITI_*` prefix for project-specific variables
- **Examples:** `GRAPHITI_TELEMETRY_ENABLED`, `GRAPHITI_LOG_LEVEL`
- **Provider Keys:** Use standard names (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

#### Pydantic Models for Config

```python
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    model: str = Field(default='gpt-4', description='Model name')
    api_key: str = Field(..., description='API key for provider')
    base_url: str | None = Field(default=None, description='Custom base URL')

    class Config:
        env_prefix = 'GRAPHITI_LLM_'
```

## Documentation Standards

### Docstring Style (Google Format)

```python
def search_nodes(
    self,
    query: str,
    limit: int = 10,
    filters: dict[str, Any] | None = None
) -> list[Node]:
    """Search for nodes matching the given query.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.
        filters: Optional filters to apply to results.

    Returns:
        List of matching nodes sorted by relevance.

    Raises:
        SearchError: If the search backend is unavailable.
        ValueError: If query is empty or limit is negative.

    Example:
        >>> client = GraphitiClient()
        >>> nodes = client.search_nodes("machine learning", limit=5)
        >>> len(nodes)
        5
    """
```

### Comment Guidelines

```python
# Good: Explain why, not what
# Use exponential backoff to avoid overwhelming the API
await asyncio.sleep(2 ** attempt)

# Avoid: Explaining obvious code
# Increment the counter
counter += 1
```

## Error Handling Patterns

### Exception Hierarchy

```python
class GraphitiError(Exception):
    """Base exception for all Graphiti errors."""
    pass

class ConfigurationError(GraphitiError):
    """Raised when configuration is invalid."""
    pass

class ProviderError(GraphitiError):
    """Raised when external provider fails."""
    pass
```

### Error Messages

- **Be Specific:** Include relevant context and values
- **Be Actionable:** Suggest what the user should do
- **Be Consistent:** Use similar phrasing across the codebase

```python
# Good
raise ConfigurationError(
    f"OpenAI API key not found. Set OPENAI_API_KEY environment variable "
    f"or pass api_key parameter to LLMConfig."
)

# Avoid
raise Exception("API key missing")
```

## Testing Conventions

### Test Organization

```python
tests/
├── unit/              # Fast tests, no external dependencies
│   ├── test_nodes.py
│   └── test_edges.py
├── integration/       # Tests requiring databases/APIs
│   ├── test_neo4j_driver_int.py
│   └── test_openai_client_int.py
└── evals/            # End-to-end evaluation tests
    └── eval_search_accuracy.py
```

### Test Naming

```python
class TestGraphitiClient:
    def test_add_episode_creates_nodes(self):
        """Test that adding an episode creates appropriate nodes."""
        pass

    def test_add_episode_with_invalid_data_raises_error(self):
        """Test that invalid episode data raises ValidationError."""
        pass
```

### Test Fixtures

- **Use pytest fixtures** for common setup
- **Name fixtures descriptively** (`neo4j_client`, `sample_episode`)
- **Minimize fixture scope** to avoid unnecessary overhead

## Performance Guidelines

### Async/Await Usage

- **Use async throughout** for I/O operations
- **Don't mix sync and async** without proper handling
- **Use asyncio.gather()** for concurrent operations

```python
# Good: Concurrent API calls
results = await asyncio.gather(
    client.embed_text(text1),
    client.embed_text(text2),
    client.embed_text(text3)
)

# Avoid: Sequential API calls
results = []
for text in texts:
    result = await client.embed_text(text)
    results.append(result)
```

### Resource Management

- **Use context managers** for database connections
- **Implement proper cleanup** in `__aexit__` methods
- **Set reasonable timeouts** for external calls

## Security Practices

### Secret Management

- **Never hardcode secrets** in source code
- **Use environment variables** for API keys
- **Validate inputs** using Pydantic models
- **Sanitize outputs** before logging

### Input Validation

```python
from pydantic import BaseModel, validator

class EpisodeData(BaseModel):
    content: str
    timestamp: datetime | None = None

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v
```

This style guide ensures consistency across the Graphiti codebase while maintaining readability, maintainability, and professional quality standards.
