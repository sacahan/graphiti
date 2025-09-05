---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# System Patterns

## Architectural Style

**Primary Pattern:** Layered Architecture with Plugin System  
**Design Philosophy:** Modular components with clean interfaces  
**Core Principle:** Separation of concerns with configurable providers

## Key Design Patterns

### 1. Strategy Pattern

**Used For:** LLM Providers, Database Drivers, Embedding Services  
**Implementation:** Abstract base classes with concrete implementations  
**Benefits:** Swappable providers, testability, extensibility

```python
# Example: LLM Client Strategy
class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Message]) -> Response:
        pass

class OpenAIClient(BaseLLMClient):
    # OpenAI-specific implementation

class AnthropicClient(BaseLLMClient):
    # Anthropic-specific implementation
```

### 2. Factory Pattern

**Used For:** Client instantiation, Driver creation  
**Implementation:** Configuration-driven object creation  
**Benefits:** Centralized creation logic, dependency injection

### 3. Adapter Pattern

**Used For:** Database driver abstraction  
**Implementation:** Common interface for different graph databases  
**Benefits:** Uniform API across Neo4j, FalkorDB, Kuzu, Neptune

### 4. Observer Pattern

**Used For:** Telemetry and event tracking  
**Implementation:** Event-driven analytics collection  
**Benefits:** Loosely coupled monitoring, opt-out capability

## Data Flow Architecture

### 1. Bi-Temporal Data Model

**Pattern:** Temporal versioning with explicit time tracking  
**Implementation:**

- Event occurrence time (when it happened)
- Ingestion time (when we learned about it)
- Validity periods for relationships

### 2. Episode-Based Ingestion

**Pattern:** Incremental data processing  
**Flow:**

1. Episode ingestion → Entity extraction
2. Entity deduplication → Graph updates
3. Relationship validation → Temporal edge management

### 3. Hybrid Retrieval Strategy

**Pattern:** Multi-modal search combination  
**Components:**

- Semantic search (vector embeddings)
- Keyword search (BM25)
- Graph traversal (relationship following)
- Cross-encoder reranking

## Error Handling Patterns

### 1. Resilience Layer

**Pattern:** Fail-fast for critical, graceful degradation for optional  
**Implementation:**

- Critical: Missing text model → immediate failure
- Optional: Extraction model failure → log and continue
- External services: Retry with exponential backoff

### 2. Tenacity Integration

**Pattern:** Configurable retry strategies  
**Usage:** LLM API calls, database connections, embedding generation  
**Benefits:** Automatic recovery from transient failures

## Configuration Patterns

### 1. Environment-Driven Configuration

**Pattern:** 12-Factor App methodology  
**Implementation:** Environment variables for all external dependencies  
**Benefits:** Deployment flexibility, secret management

### 2. Hierarchical Configuration

**Pattern:** Default → Environment → Explicit override  
**Implementation:** Pydantic models with validation  
**Benefits:** Type safety, clear precedence rules

## Concurrency Patterns

### 1. Semaphore-Based Rate Limiting

**Pattern:** Configurable concurrency control  
**Implementation:** SEMAPHORE_LIMIT environment variable  
**Benefits:** Provider rate limit compliance, resource management

### 2. Async/Await Throughout

**Pattern:** Fully asynchronous I/O  
**Implementation:** AsyncIO for all external calls  
**Benefits:** High throughput, non-blocking operations

## Testing Patterns

### 1. Test Categorization

**Pattern:** Unit vs Integration test separation  
**Implementation:**

- Unit tests: No external dependencies
- Integration tests: Suffix `_int`, require database
- Evaluation tests: End-to-end validation

### 2. Mock Strategy

**Pattern:** No mocks for integration testing  
**Philosophy:** Test against real services for reliability  
**Benefits:** Catches provider API changes, real-world validation

## Caching Patterns

### 1. Multi-Level Caching

**Pattern:** Memory + Disk + Provider caching  
**Implementation:**

- In-memory: Recent results
- Disk cache: Persistent storage
- Provider cache: LLM result caching

### 2. Cache Key Strategy

**Pattern:** Content-based keys with version control  
**Benefits:** Cache invalidation, reproducible results

## Plugin Architecture

### 1. Provider Registration

**Pattern:** Dynamic provider loading  
**Implementation:** Configuration-based provider selection  
**Benefits:** Runtime provider switching, A/B testing

### 2. Extension Points

**Pattern:** Well-defined integration interfaces  
**Available Extensions:**

- Custom entity types (Pydantic models)
- Search strategies
- Embedding providers
- Cross-encoders/rerankers

## Data Consistency Patterns

### 1. Temporal Edge Validation

**Pattern:** Time-aware relationship management  
**Implementation:** Automatic invalidation of contradicting edges  
**Benefits:** Maintains graph consistency over time

### 2. Incremental Updates

**Pattern:** Append-only with temporal versioning  
**Implementation:** No destructive updates, all changes tracked  
**Benefits:** Full audit trail, point-in-time queries

## Performance Patterns

### 1. Lazy Loading

**Pattern:** On-demand resource initialization  
**Implementation:** Database connections, model loading  
**Benefits:** Faster startup, reduced memory usage

### 2. Batch Processing

**Pattern:** Bulk operations for efficiency  
**Implementation:** Batch embeddings, bulk graph updates  
**Benefits:** Higher throughput, reduced API calls

## Security Patterns

### 1. Secret Management

**Pattern:** Environment-based credentials  
**Implementation:** No hardcoded secrets, .env support  
**Benefits:** Secure deployment, audit compliance

### 2. Input Validation

**Pattern:** Pydantic model validation  
**Implementation:** Type checking, constraint validation  
**Benefits:** Runtime safety, clear error messages
