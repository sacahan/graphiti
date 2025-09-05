---
created: 2025-09-05T09:44:54Z
last_updated: 2025-09-05T09:44:54Z
version: 1.0
author: Claude Code PM System
---

# Product Context

## Target Users

### Primary Personas

#### AI Agent Developers

**Profile:** Software engineers building AI agents and assistants  
**Needs:** Dynamic knowledge representation, temporal context, real-time updates  
**Pain Points:** Static RAG limitations, batch processing delays, context drift  
**Value Proposition:** Real-time knowledge graphs with temporal awareness

#### Enterprise AI Teams

**Profile:** Large organizations deploying AI at scale  
**Needs:** Scalable knowledge management, compliance, auditability  
**Pain Points:** Data silos, inconsistent context, regulatory requirements  
**Value Proposition:** Enterprise-grade graph infrastructure with full audit trail

#### Research Scientists

**Profile:** AI/ML researchers working on knowledge representation  
**Needs:** Flexible ontologies, experimental frameworks, novel architectures  
**Pain Points:** Rigid systems, limited customization, poor research tooling  
**Value Proposition:** Extensible platform for knowledge graph research

#### Platform Engineers

**Profile:** Infrastructure teams supporting AI applications  
**Needs:** Reliable deployment, monitoring, scalability, multi-tenancy  
**Pain Points:** Complex dependencies, vendor lock-in, operational overhead  
**Value Proposition:** Self-hosted solution with multiple backend options

## Core Functionality

### Knowledge Graph Construction

**Capability:** Automatic graph building from unstructured data  
**Features:**

- Entity extraction and deduplication
- Relationship inference and validation
- Temporal edge management
- Custom ontology support via Pydantic models

### Hybrid Retrieval System

**Capability:** Multi-modal search across graph, semantic, and keyword dimensions  
**Features:**

- Vector similarity search (semantic)
- BM25 keyword search (lexical)
- Graph traversal queries (structural)
- Cross-encoder reranking for precision

### Bi-Temporal Data Model

**Capability:** Time-aware knowledge representation  
**Features:**

- Event occurrence time tracking
- Ingestion time recording
- Point-in-time queries
- Historical context reconstruction

### Incremental Processing

**Capability:** Real-time graph updates without batch recomputation  
**Features:**

- Episode-based ingestion
- Automatic contradiction resolution
- Consistency maintenance
- Scalable concurrent processing

## Use Cases

### AI Agent Memory

**Scenario:** Personal assistant maintaining long-term user context  
**Implementation:** Continuous episode ingestion, temporal query support  
**Benefits:** Consistent personality, context continuity, learning over time

### Dynamic RAG Systems

**Scenario:** Knowledge base that updates with new information  
**Implementation:** Replace static embeddings with live graph queries  
**Benefits:** Always current information, relationship awareness, efficient updates

### Conversational AI

**Scenario:** Chatbots with persistent multi-turn context  
**Implementation:** Graph-based context management across sessions  
**Benefits:** Coherent conversations, relationship tracking, personalization

### Research Analysis

**Scenario:** Scientists tracking evolving research relationships  
**Implementation:** Paper ingestion, citation networks, temporal analysis  
**Benefits:** Trend identification, collaboration discovery, impact analysis

### Enterprise Knowledge Management

**Scenario:** Large organizations with complex, changing knowledge bases  
**Implementation:** Multi-source ingestion, compliance tracking, access control  
**Benefits:** Unified view, audit trails, scalable access patterns

## Product Differentiators

### vs. Traditional RAG

| Aspect                | Traditional RAG        | Graphiti                        |
| --------------------- | ---------------------- | ------------------------------- |
| **Data Updates**      | Batch reprocessing     | Incremental updates             |
| **Temporal Handling** | None/Basic             | Explicit bi-temporal model      |
| **Relationships**     | Implicit in embeddings | Explicit graph edges            |
| **Contradictions**    | Manual resolution      | Automatic temporal invalidation |
| **Query Latency**     | Seconds+               | Sub-second                      |

### vs. GraphRAG

| Aspect            | GraphRAG                      | Graphiti                   |
| ----------------- | ----------------------------- | -------------------------- |
| **Use Case**      | Static document summarization | Dynamic data management    |
| **Processing**    | Batch-oriented                | Real-time incremental      |
| **Structure**     | Community summaries           | Temporal entities/edges    |
| **Retrieval**     | LLM summarization chain       | Direct hybrid search       |
| **Customization** | Limited                       | Full custom entity support |

### vs. Knowledge Graph Databases

| Aspect                 | Traditional KG       | Graphiti                 |
| ---------------------- | -------------------- | ------------------------ |
| **Construction**       | Manual/Expert-driven | Automatic from text      |
| **Temporal Model**     | Basic/None           | Native bi-temporal       |
| **AI Integration**     | External tooling     | Built-in LLM/embedding   |
| **Schema Flexibility** | Rigid ontologies     | Dynamic Pydantic models  |
| **Learning**           | Static               | Continuous from episodes |

## Success Metrics

### Developer Adoption

- GitHub stars, forks, contributors
- Package downloads (PyPI)
- Integration examples and tutorials
- Community discussions and issues

### Performance Benchmarks

- Query latency (target: <1 second)
- Ingestion throughput (episodes/second)
- Memory efficiency (graph size vs. RAM)
- Accuracy metrics (retrieval precision/recall)

### Enterprise Indicators

- Multi-database backend adoption
- Large-scale deployments (>1M nodes)
- Integration with existing systems
- Production uptime and reliability

## Roadmap Priorities

### Current Focus (v0.20+)

- ✅ Custom graph schemas (Pydantic models)
- ✅ Enhanced retrieval configuration
- ✅ MCP server for AI assistants
- 🔄 Expanded test coverage
- 🔄 Performance optimization

### Near-term (Next 3 months)

- Advanced search strategies
- Improved monitoring and observability
- Multi-tenancy support
- Enhanced documentation and examples

### Medium-term (6 months)

- GraphQL query interface
- Real-time subscription support
- Advanced analytics dashboard
- Federated graph deployment

### Long-term Vision

- Distributed graph architecture
- Advanced reasoning capabilities
- Industry-specific templates
- AI-driven schema evolution
