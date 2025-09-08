# FalkorDB Setup Guide

## Quick Start

FalkorDB is a high-performance graph database compatible with Redis protocols, offering faster startup times and lower memory usage compared to Neo4j. This guide will help you set up Graphiti with FalkorDB.

## Prerequisites

- Python 3.8+
- Docker (for containerized deployment)
- OpenAI API key (for LLM functionality)

## Installation

### 1. Install FalkorDB Support

```bash
# Install Graphiti with FalkorDB support
pip install graphiti-core[falkordb]

# Or if using uv
uv add "graphiti-core[falkordb]"
```

### 2. Start FalkorDB Server

#### Option A: Docker (Recommended)

```bash
# Start FalkorDB server
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest

# Verify FalkorDB is running
docker logs falkordb
```

#### Option B: Local Installation

```bash
# Install FalkorDB locally (requires Redis)
# Follow instructions at: https://docs.falkordb.com/installation
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database configuration
export GRAPHITI_DB_TYPE=falkordb
export FALKORDB_URL=redis://localhost:6379

# LLM configuration (required)
export OPENAI_API_KEY=your_openai_api_key_here

# Optional: Performance tuning
export SEMAPHORE_LIMIT=20  # Higher concurrency for FalkorDB
export LOG_LEVEL=INFO
```

## Basic Usage

### Python Script Example

```python
import os
from graphiti import Graphiti

# Set database type
os.environ['GRAPHITI_DB_TYPE'] = 'falkordb'
os.environ['FALKORDB_URL'] = 'redis://localhost:6379'
os.environ['OPENAI_API_KEY'] = 'your-api-key'

# Initialize Graphiti with FalkorDB
graphiti = Graphiti()

# Add some data
await graphiti.add_episode(
    name="Setup Test",
    episode_body="Testing FalkorDB setup with Graphiti",
    group_id="test-group"
)

# Search the data
results = await graphiti.search(
    query="setup test",
    group_ids=["test-group"]
)

print(f"Found {len(results)} results")
```

### MCP Server Usage

```bash
# Start Graphiti MCP server with FalkorDB
cd mcp_server
export GRAPHITI_DB_TYPE=falkordb
python graphiti_mcp_server.py
```

## Performance Optimization

### Recommended Settings for FalkorDB

```bash
# Environment variables for optimal FalkorDB performance
export GRAPHITI_DB_TYPE=falkordb
export SEMAPHORE_LIMIT=20          # Higher concurrency than Neo4j
export FALKORDB_URL=redis://localhost:6379
export LOG_LEVEL=INFO              # Monitor performance
```

### Memory Optimization

```bash
# For memory-constrained environments
export SEMAPHORE_LIMIT=15
export MODEL_NAME=gpt-4.1-nano     # Smaller model
export EMBEDDER_MODEL_NAME=text-embedding-3-small
```

## Verification

### Check FalkorDB Connection

```bash
# Test Redis connection
redis-cli -p 6379 ping
# Expected output: PONG

# Test FalkorDB specific commands
redis-cli -p 6379 GRAPH.QUERY test_graph "RETURN 1"
```

### Performance Monitoring

```bash
# Install optional monitoring
pip install psutil

# Check performance metrics (if running MCP server)
curl http://localhost:8000/performance
```

## Connection Strings

FalkorDB supports various connection formats:

```bash
# Basic connection
FALKORDB_URL=redis://localhost:6379

# With password
FALKORDB_URL=redis://:password@localhost:6379

# Custom database number
FALKORDB_URL=redis://localhost:6379/1

# Remote server
FALKORDB_URL=redis://falkordb.example.com:6379
```

## Troubleshooting

### Common Issues

#### FalkorDB Connection Failed

```bash
# Check if FalkorDB is running
docker ps | grep falkordb

# Check port availability
netstat -an | grep 6379

# Restart FalkorDB container
docker restart falkordb
```

#### Slow Performance

```bash
# Check semaphore limits
echo $SEMAPHORE_LIMIT

# Monitor memory usage (requires psutil)
python -c "import psutil; print(f'Memory: {psutil.Process().memory_info().rss/1024/1024:.1f}MB')"

# Check FalkorDB logs
docker logs falkordb
```

#### Module Import Errors

```bash
# Reinstall FalkorDB support
pip install --upgrade "graphiti-core[falkordb]"

# Verify installation
python -c "from graphiti_core.driver.falkordb_driver import FalkorDriver; print('FalkorDB driver available')"
```

## Migration from Neo4j

If you're migrating from Neo4j to FalkorDB, see our [Migration Guide](../guides/neo4j-to-falkordb.md).

## Next Steps

- [Environment Variables Reference](environment-variables.md)
- [Docker Deployment Guide](docker-deployment.md)
- [Performance Tuning](../guides/performance-tuning.md)
- [Basic Examples](../examples/falkordb-basic/)

## Performance Targets

FalkorDB with Graphiti achieves:

- ✅ **Startup Time**: < 5 seconds (vs 15-20s with Neo4j)
- ✅ **Memory Usage**: < 200MB for small datasets (<10k nodes)
- ✅ **Query Latency**: Sub-100ms for basic operations
- ✅ **Concurrent Operations**: 20+ simultaneous operations
