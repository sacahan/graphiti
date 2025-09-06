---
name: apply-falkor
status: backlog
created: 2025-09-05T10:38:27Z
progress: 0%
prd: .claude/prds/apply-falkor.md
github: https://github.com/sacahan/graphiti/issues/1
updated: 2025-09-06T01:31:13Z
---

# Epic: apply-falkor

## Overview

Implement database backend flexibility in Graphiti to enable seamless switching between Neo4j and FalkorDB via environment variables. This epic focuses on refactoring the hardcoded Neo4j dependencies to create a configurable database abstraction, with particular optimization for lightweight MCP Server deployments using FalkorDB.

The implementation leverages Graphiti's existing driver abstraction pattern (Strategy Pattern) to extend database backend selection while maintaining full API compatibility and achieving significant performance improvements for resource-constrained environments.

## Architecture Decisions

### Core Technical Decisions

1. **Environment Variable-Based Backend Selection**
   - **Decision**: Use `GRAPHITI_DB_TYPE` environment variable for runtime database selection
   - **Rationale**: Maintains backward compatibility while enabling zero-code-change deployment flexibility
   - **Alternative Considered**: Constructor parameters (rejected for deployment complexity)

2. **Leverage Existing Driver Pattern**
   - **Decision**: Extend the existing `BaseGraphDriver` abstraction rather than creating new interfaces
   - **Rationale**: Minimizes code changes and maintains architectural consistency
   - **Pattern**: Strategy Pattern already implemented in `graphiti_core/driver/`

3. **Configuration Hierarchy**
   - **Decision**: Environment Variables → Connection String → Defaults
   - **Rationale**: Provides flexibility for different deployment scenarios (containers, local dev, CI)

4. **Backward Compatibility First**
   - **Decision**: Default to Neo4j behavior if no `GRAPHITI_DB_TYPE` specified
   - **Rationale**: Ensures existing deployments continue working without changes

### Technology Choices

- **Configuration Management**: Extend existing Pydantic models in driver configurations
- **Connection Handling**: Leverage existing FalkorDB driver (`falkordb>=1.1.2,<2.0.0`)
- **Error Handling**: Extend existing `GraphitiError` hierarchy for database-specific errors
- **Testing Strategy**: Extend existing integration test patterns with database switching

## Technical Approach

### Backend Services

#### Database Driver Factory Enhancement

- **Location**: `graphiti_core/driver/`
- **Changes**:
  - Create `DriverFactory` class to handle backend selection
  - Extend `BaseGraphDriver` interface if needed for common operations
  - Add database-specific configuration validation

#### Configuration System Updates

- **Location**: `graphiti_core/` (main Graphiti class)
- **Changes**:
  - Add environment variable parsing for `GRAPHITI_DB_TYPE`
  - Implement FalkorDB-specific environment variables (`FALKORDB_HOST`, `FALKORDB_PORT`, etc.)
  - Add runtime configuration validation with clear error messages

#### MCP Server Optimization

- **Location**: `mcp_server/`
- **Changes**:
  - Optimize initialization sequence for FalkorDB (faster startup)
  - Add FalkorDB-specific error handling and logging
  - Container-friendly configuration defaults

### Infrastructure

#### Environment Variable Schema

```bash
# Database Selection
GRAPHITI_DB_TYPE=falkordb|neo4j  # Default: neo4j

# FalkorDB Configuration
FALKORDB_HOST=localhost          # Default: localhost
FALKORDB_PORT=6379              # Default: 6379
FALKORDB_DATABASE=0             # Default: 0
FALKORDB_PASSWORD=              # Optional

# Maintain existing Neo4j variables
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

#### Docker Integration

- Update MCP server Docker configuration for FalkorDB support
- Add docker-compose examples with FalkorDB
- Optimize container startup sequence

## Implementation Strategy

### Development Phases

#### Phase 1: Core Infrastructure (Week 1)

- Analyze existing hardcoded Neo4j dependencies
- Design and implement `DriverFactory` pattern
- Add environment variable configuration system
- Create basic FalkorDB backend switching

#### Phase 2: MCP Server Integration (Week 2)

- Integrate database selection into MCP server initialization
- Optimize FalkorDB startup sequence
- Add comprehensive error handling and logging
- Implement configuration validation

#### Phase 3: Testing & Optimization (Week 3)

- Extend integration tests for dual-database support
- Performance benchmarking and optimization
- Memory usage optimization for FalkorDB deployments
- Container deployment testing

#### Phase 4: Documentation (Week 4)

- Update setup guides with FalkorDB instructions
- Create migration documentation
- Docker deployment examples
- Troubleshooting guides

### Risk Mitigation

1. **API Compatibility**: Extensive testing against existing SDK usage patterns
2. **Performance Regression**: Benchmarking before/after for Neo4j deployments
3. **Configuration Complexity**: Default values and clear error messages
4. **Database Feature Parity**: Focus on core MCP Server functionality first

## Task Breakdown Preview

High-level task categories that will be created:

- [ ] **Database Factory Implementation**: Create configurable driver selection mechanism
- [ ] **Environment Configuration**: Implement GRAPHITI_DB_TYPE and FalkorDB variables
- [ ] **MCP Server Integration**: Integrate database selection into MCP server startup
- [ ] **Configuration Validation**: Add runtime validation with clear error messages
- [ ] **Performance Optimization**: Optimize FalkorDB startup and memory usage
- [ ] **Integration Testing**: Extend test suite for dual-database scenarios
- [ ] **Documentation Updates**: Create setup guides and examples
- [ ] **Container Support**: Update Docker configurations and examples

## Dependencies

### External Dependencies

- **FalkorDB Server**: Version 1.1.2+ running and accessible
- **Redis Infrastructure**: For teams leveraging existing Redis deployments
- **Container Runtime**: Docker/Podman for testing containerized deployments

### Internal Dependencies

- **Graphiti Core**: Stable during development (avoid breaking changes)
- **Driver Abstraction**: May need minor enhancements to support switching
- **MCP Server**: Require modifications for initialization optimization
- **CI Pipeline**: Updates needed for dual-database testing

### Prerequisite Work

- Code audit to identify all hardcoded Neo4j dependencies
- Analysis of existing `BaseGraphDriver` interface sufficiency
- Performance baseline establishment for current FalkorDB implementation

## Success Criteria (Technical)

### Performance Benchmarks

- **MCP Server Startup**: <5 seconds with FalkorDB (vs ~15-20s Neo4j)
- **Memory Usage**: <200MB peak for small datasets (<10k nodes)
- **Query Latency**: Maintain <500ms 95th percentile for hybrid search
- **Zero Performance Regression**: Neo4j performance unchanged

### Quality Gates

- **Test Coverage**: >90% for new database selection code paths
- **API Compatibility**: 100% backward compatibility with existing SDK
- **Integration Tests**: Pass for both Neo4j and FalkorDB backends
- **Container Support**: Successful Docker deployment with both databases

### Acceptance Criteria

- Environment variable `GRAPHITI_DB_TYPE=falkordb` switches to FalkorDB
- All core MCP Server features work identically with both databases
- Setup time <30 minutes for new FalkorDB users following documentation
- Clear error messages for configuration issues

## Estimated Effort

### Overall Timeline

- **Total Duration**: 4-5 weeks (part-time development)
- **Critical Path**: Database factory implementation → MCP integration → Testing

### Resource Requirements

- **Primary Developer**: 1 person, part-time (15-20 hours/week)
- **Code Review**: Core Graphiti maintainer involvement
- **Testing**: CI pipeline updates and integration testing setup

### Effort Breakdown

- **Week 1**: Analysis & Core Implementation (20 hours)
- **Week 2**: MCP Server Integration (15 hours)
- **Week 3**: Testing & Optimization (18 hours)
- **Week 4**: Documentation & Examples (12 hours)
- **Buffer**: 1 week for review feedback and refinements

### Critical Path Items

1. Identifying and refactoring hardcoded Neo4j dependencies
2. Ensuring FalkorDB driver interface compatibility
3. MCP Server initialization sequence optimization
4. Comprehensive integration testing setup

## Tasks Created

- [ ] 001.md - Audit Neo4j hardcoded dependencies (parallel: true)
- [ ] 002.md - Implement database factory pattern (parallel: false)
- [ ] 003.md - Add FalkorDB environment configuration (parallel: true)
- [ ] 004.md - Integrate factory into main Graphiti class (parallel: false)
- [ ] 005.md - Optimize MCP server for FalkorDB (parallel: false)
- [ ] 006.md - Extend integration tests for dual-database support (parallel: true)
- [ ] 007.md - Create FalkorDB setup documentation (parallel: true)
- [ ] 008.md - Update container deployment examples (parallel: true)

Total tasks: 8
Parallel tasks: 5
Sequential tasks: 3
Estimated total effort: 58-71 hours
