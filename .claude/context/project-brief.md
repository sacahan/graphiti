---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Project Brief

## What It Does

**Graphiti** is a Python framework for building and querying temporally-aware knowledge graphs specifically designed for AI agents operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) systems that rely on static embeddings and batch processing, Graphiti continuously integrates user interactions, structured/unstructured data, and external information into a coherent, queryable graph that updates in real-time.

## Why It Exists

### Core Problem

Traditional RAG approaches face significant limitations when dealing with frequently changing data:

- **Batch Processing Bottleneck:** Require complete recomputation for updates
- **Static Context:** Unable to handle evolving relationships and contradictions
- **Temporal Blindness:** No awareness of when events occurred vs. when they were learned
- **Relationship Loss:** Connections between entities exist only implicitly in embeddings

### Solution Approach

Graphiti addresses these challenges through:

- **Real-time Incremental Updates:** Immediate integration without batch recomputation
- **Bi-temporal Data Model:** Explicit tracking of event occurrence and ingestion times
- **Hybrid Retrieval:** Combines semantic, keyword, and graph traversal methods
- **Temporal Edge Management:** Automatic handling of contradictions through time-aware invalidation

## Project Scope

### Primary Objectives

1. **Enable Real-Time Knowledge Graphs** - Continuous updates without performance degradation
2. **Support Multiple AI Providers** - OpenAI, Anthropic, Gemini, Groq with extensible architecture
3. **Provide Database Flexibility** - Neo4j, FalkorDB, Kuzu, Amazon Neptune support
4. **Deliver Sub-Second Query Performance** - Optimized hybrid search with reranking
5. **Ensure Production Readiness** - Enterprise deployment, monitoring, scalability

### Key Boundaries

**In Scope:**

- Knowledge graph construction from text/JSON episodes
- Temporal relationship management and querying
- Multiple LLM and database backend support
- MCP server for AI assistant integration
- REST API for external system integration

**Out of Scope:**

- Visual graph editing interfaces
- Real-time collaborative editing
- Complex reasoning engines (inference beyond basic graph traversal)
- Distributed graph federation (current version)

## Success Criteria

### Technical Success

- **Performance:** <1 second query latency for typical workloads
- **Scalability:** Handle >1M nodes with reasonable resource usage
- **Reliability:** >99% uptime in production deployments
- **Accuracy:** Maintain >90% precision in retrieval tasks

### Adoption Success

- **Developer Community:** Growing GitHub engagement (stars, forks, contributors)
- **Production Usage:** Enterprise deployments at scale
- **Integration Ecosystem:** Multiple client libraries and integrations
- **Documentation Quality:** Comprehensive guides enabling self-service adoption

### Business Success

- **Market Position:** Recognized alternative to traditional RAG systems
- **Research Impact:** Academic citations and research collaborations
- **Commercial Viability:** Sustainable development through Zep platform synergy
- **Open Source Health:** Active contributor community and maintenance

## Key Stakeholders

### Internal Teams

- **Core Development Team:** Framework architecture and feature development
- **Zep Platform Team:** Integration with commercial offering
- **Research Team:** Algorithm development and academic collaboration
- **DevOps Team:** Infrastructure, deployment, and monitoring

### External Communities

- **AI Agent Developers:** Primary users building intelligent systems
- **Enterprise AI Teams:** Large-scale deployment and integration
- **Academic Researchers:** Knowledge representation and graph AI research
- **Open Source Contributors:** Community development and extensions

## Constraints & Dependencies

### Technical Constraints

- **Python Ecosystem:** Committed to Python 3.10+ for development simplicity
- **LLM Provider Dependency:** Quality depends on underlying model capabilities
- **Database Performance:** Query performance limited by chosen backend
- **Memory Usage:** In-memory operations constrain maximum graph size

### Resource Constraints

- **Development Bandwidth:** Limited core team requires careful prioritization
- **Infrastructure Costs:** Testing across multiple providers and databases
- **Documentation Effort:** Comprehensive guides require significant investment
- **Support Capacity:** Community support scales with adoption

### External Dependencies

- **LLM Provider APIs:** OpenAI, Anthropic, Google availability and pricing
- **Database Vendors:** Neo4j, FalkorDB, Kuzu compatibility and support
- **Python Ecosystem:** Upstream dependency updates and security patches
- **Cloud Platforms:** Deployment and infrastructure provider stability

## Risk Mitigation

### Technical Risks

- **Provider Lock-in:** Mitigated by multi-provider architecture
- **Performance Degradation:** Addressed through optimization and benchmarking
- **Data Consistency:** Managed via temporal validation and testing
- **Scale Limitations:** Handled through modular architecture design

### Market Risks

- **Competition:** Differentiated through temporal features and real-time updates
- **Technology Shifts:** Architecture designed for extensibility and adaptation
- **Adoption Barriers:** Reduced through comprehensive documentation and examples
- **Integration Complexity:** Simplified via standardized APIs and MCP protocol

## Long-term Vision

Graphiti aims to become the standard framework for temporal knowledge graphs in AI systems, enabling:

- **Ubiquitous Agent Memory:** Every AI assistant has persistent, evolving knowledge
- **Enterprise Knowledge Unification:** Organization-wide intelligent data integration
- **Research Acceleration:** Advanced knowledge representation capabilities for scientists
- **Ecosystem Foundation:** Platform for building next-generation AI applications

The project's success will be measured not just by technical capabilities, but by its ability to enable new classes of AI applications that were previously impractical or impossible with static knowledge systems.
