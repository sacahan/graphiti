---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Project Overview

## High-Level Summary

Graphiti is an open-source Python framework that revolutionizes how AI agents handle knowledge by building temporally-aware knowledge graphs from dynamic data. Instead of static document embeddings, Graphiti creates living knowledge representations that evolve in real-time, maintaining historical context while enabling sub-second query performance through hybrid retrieval strategies.

## Core Features

### 🎯 Real-Time Knowledge Graph Construction

- **Automatic Entity Extraction:** Identifies entities and relationships from unstructured text and structured JSON
- **Temporal Edge Management:** Tracks when relationships form, change, or become invalid over time
- **Contradiction Resolution:** Automatically handles conflicting information through temporal invalidation
- **Custom Ontologies:** Support for developer-defined entity types via Pydantic models

### ⚡ Hybrid Retrieval System

- **Multi-Modal Search:** Combines semantic embeddings, BM25 keyword search, and graph traversal
- **Cross-Encoder Reranking:** Precision optimization using neural reranking models
- **Search Strategies:** Configurable approaches for different use cases and performance requirements
- **Sub-Second Performance:** Optimized for interactive applications requiring immediate responses

### 🕰️ Bi-Temporal Data Model

- **Event Time Tracking:** When events actually occurred in the real world
- **Ingestion Time Recording:** When information was learned by the system
- **Point-in-Time Queries:** Reconstruct knowledge state at any historical moment
- **Audit Trail:** Complete history of all knowledge changes and sources

### 🔧 Multi-Provider Architecture

- **Database Flexibility:** Neo4j, FalkorDB, Kuzu, Amazon Neptune support
- **LLM Provider Choice:** OpenAI, Anthropic, Gemini, Groq, Azure OpenAI, local Ollama
- **Embedding Options:** OpenAI, Voyage AI, Google, local sentence-transformers
- **Production Ready:** Enterprise deployment with Docker, monitoring, and scalability

## Current Capabilities

### Knowledge Ingestion

- **Episode Processing:** Text and structured data ingestion with entity extraction
- **Incremental Updates:** Real-time graph updates without batch recomputation
- **Bulk Operations:** Efficient processing of large datasets with parallel execution
- **Data Validation:** Pydantic-based validation ensuring data quality and consistency

### Query & Retrieval

- **Semantic Search:** Vector similarity using configurable embedding models
- **Keyword Search:** BM25-based lexical search for precise term matching
- **Graph Queries:** Relationship traversal and pattern matching across the knowledge graph
- **Hybrid Fusion:** Intelligent combination of multiple search modalities with reranking

### Integration Points

- **MCP Server:** Model Context Protocol integration for AI assistants (Claude, Cursor)
- **REST API:** FastAPI-based service for external system integration
- **Python SDK:** Direct library integration for Python applications
- **LangChain Support:** Compatible with LangChain workflows and agents

### Developer Experience

- **Rich Configuration:** Environment-based setup with sensible defaults
- **Comprehensive Testing:** Unit, integration, and evaluation test suites
- **Example Projects:** Quickstart guides and real-world implementation examples
- **Type Safety:** Full type annotations with Pyright validation

## System Architecture

### Core Components

```
graphiti_core/
├── graphiti.py          # Main orchestration class
├── nodes.py            # Graph node implementations
├── edges.py            # Graph edge implementations
├── driver/             # Database abstraction layer
├── llm_client/         # LLM provider integrations
├── embedder/          # Embedding service clients
├── search/            # Hybrid search strategies
├── prompts/           # LLM prompt management
└── utils/             # Maintenance and utilities
```

### Service Architecture

```
├── server/            # FastAPI REST service
├── mcp_server/       # Model Context Protocol server
├── examples/         # Implementation examples
└── tests/           # Comprehensive test suite
```

## Integration Ecosystem

### Deployment Options

- **Local Development:** SQLite-based Kuzu for rapid prototyping
- **Production Scale:** Neo4j cluster with high availability
- **Cloud Native:** Amazon Neptune with OpenSearch integration
- **Redis Compatible:** FalkorDB for existing Redis infrastructure

### AI Platform Integrations

- **Claude Code:** Native MCP integration for seamless assistant memory
- **Cursor IDE:** Knowledge graph-powered code understanding
- **LangChain Agents:** Graph-enhanced reasoning and memory
- **Custom Applications:** Direct SDK integration for specialized use cases

### Monitoring & Observability

- **Performance Metrics:** Query latency, ingestion throughput, memory usage
- **Health Checks:** Database connectivity, LLM provider status, system resources
- **Analytics:** Optional telemetry for usage patterns and optimization
- **Error Tracking:** Comprehensive logging with structured error reporting

## Performance Characteristics

### Scale Capabilities

- **Graph Size:** Tested with >1M nodes and relationships
- **Query Performance:** Sub-second response times for typical workloads
- **Concurrent Users:** Supports multiple simultaneous queries and ingestion
- **Memory Efficiency:** Optimized data structures for large graph storage

### Optimization Features

- **Caching Strategy:** Multi-level caching (memory, disk, provider)
- **Parallel Processing:** Configurable concurrency for ingestion pipelines
- **Index Management:** Automatic database index creation and maintenance
- **Resource Control:** Semaphore-based rate limiting for provider APIs

## Development Status

### Stable Features (v0.20+)

- ✅ Core knowledge graph construction and querying
- ✅ Multi-provider LLM and database support
- ✅ Temporal relationship management
- ✅ Hybrid retrieval with reranking
- ✅ MCP server implementation
- ✅ Custom entity type support via Pydantic

### Active Development

- 🔄 Enhanced test coverage for reliability assurance
- 🔄 Performance optimization for larger datasets
- 🔄 Advanced search strategy configuration
- 🔄 Improved monitoring and observability tools

### Future Roadmap

- 📅 GraphQL query interface for flexible data access
- 📅 Multi-tenancy support for shared deployments
- 📅 Advanced analytics dashboard for graph insights
- 📅 Federated graph deployment across multiple instances

The project represents a significant advancement in knowledge representation for AI systems, moving beyond static embeddings to dynamic, temporal knowledge graphs that can grow and evolve with real-world information changes.
