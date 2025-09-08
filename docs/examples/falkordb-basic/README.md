# FalkorDB Basic Examples

This directory contains comprehensive examples for using Graphiti with FalkorDB, demonstrating improved performance over Neo4j.

## Quick Start

```bash
# Install dependencies
pip install "graphiti-core[falkordb]" python-dotenv psutil

# Start FalkorDB
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest

# Configure environment
cp .env.template .env
# Edit .env with your OPENAI_API_KEY

# Run examples
python basic_usage.py
python mcp_server_example.py
python performance_demo.py
```

## Examples Overview

### Core Examples

- **`basic_usage.py`** - Essential FalkorDB operations with Graphiti
  - Connection setup and configuration
  - Basic graph operations (add/search episodes)
  - Performance monitoring and metrics
  - Memory usage tracking

- **`mcp_server_example.py`** - MCP server integration with FalkorDB
  - MCP server configuration simulation
  - Performance endpoint testing
  - Container deployment patterns
  - Real-time monitoring integration

- **`performance_demo.py`** - Comprehensive performance benchmarking
  - Side-by-side Neo4j vs FalkorDB comparison
  - Startup time, memory usage, and operation speed analysis
  - Performance target validation
  - Automated benchmark reporting

### Configuration Files

- **`.env.template`** - Complete environment configuration template
  - FalkorDB connection settings
  - Performance optimization parameters
  - Development vs production presets
  - Alternative LLM provider configurations

## Configuration Guide

### Basic Setup

```bash
# Copy and customize environment template
cp .env.template .env
nano .env
```

### Required Environment Variables

```bash
# Essential settings
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://localhost:6379
OPENAI_API_KEY=your-api-key-here
```

### Performance Optimization

```bash
# FalkorDB optimized settings
SEMAPHORE_LIMIT=20          # Higher concurrency than Neo4j (10)
LOG_LEVEL=INFO              # Appropriate logging level
MODEL_NAME=gpt-4.1-mini     # Balanced performance/cost
```

## Performance Targets

These examples demonstrate FalkorDB achieving significant improvements:

| Metric             | Target  | Neo4j Baseline | FalkorDB Result |
| ------------------ | ------- | -------------- | --------------- |
| **Startup time**   | < 5s    | 15-20s         | < 5s ✅         |
| **Memory usage**   | < 200MB | 500MB+         | < 200MB ✅      |
| **Concurrency**    | 20+ ops | 10 ops         | 20+ ops ✅      |
| **Query response** | < 100ms | ~200ms         | < 100ms ✅      |

## Usage Examples

### Basic Operations

```bash
# Test basic functionality
python basic_usage.py

# Expected output:
# 🚀 FalkorDB Basic Usage Example
# ✅ Startup completed in 3.2s
# 🎉 Startup target achieved (<5s)
# 📊 Memory usage: 180MB
# 🎉 Memory target achieved (<200MB)
```

### MCP Server Integration

```bash
# Simulate MCP server operations
python mcp_server_example.py

# Test actual MCP server (requires mcp_server setup)
cd ../../../mcp_server
python graphiti_mcp_server.py
```

### Performance Benchmarking

```bash
# Run comprehensive performance comparison
python performance_demo.py

# Expected benchmarks:
# 🏁 FalkorDB vs Neo4j Performance Demo
# 📊 PERFORMANCE COMPARISON
# 🚀 STARTUP TIME: 77% improvement
# 💾 MEMORY USAGE: 65% reduction
# ⚡ OPERATION SPEED: 60% faster
```

## Troubleshooting

### FalkorDB Connection Issues

```bash
# Verify FalkorDB is running
docker ps | grep falkordb
redis-cli -p 6379 ping
# Expected: PONG

# Check connection in examples
python -c "
import redis
r = redis.from_url('redis://localhost:6379')
print('FalkorDB connected:', r.ping())
"
```

### Performance Issues

```bash
# Monitor resource usage
docker stats falkordb

# Check example configuration
python -c "
import os
print('DB Type:', os.getenv('GRAPHITI_DB_TYPE'))
print('Semaphore Limit:', os.getenv('SEMAPHORE_LIMIT'))
"
```

### Dependencies

```bash
# Install optional dependencies for full functionality
pip install psutil  # For memory monitoring
pip install redis   # For FalkorDB connection testing
```

## Next Steps

After running these examples:

1. **Production Setup**: See `../../../docs/setup/docker-deployment.md`
2. **Migration Guide**: See `../../../docs/guides/neo4j-to-falkordb.md`
3. **Performance Tuning**: See `../../../docs/guides/performance-tuning.md`
4. **MCP Server**: See `../../../mcp_server/README.md`

## Example Output

### Successful Run

```
🚀 FalkorDB Basic Usage Example
==================================================
1. Initializing Graphiti with FalkorDB...
   ✅ Startup completed in 4.2s
   🎉 Startup target achieved (<5s)
   📊 Memory usage: 185.3MB
   🎉 Memory target achieved (<200MB)

2. Adding test episodes...
   Episode 1: FalkorDB Setup (0.234s)
   Episode 2: Performance Testing (0.198s)
   Episode 3: Development Progress (0.201s)
   ✅ All episodes added successfully

3. Testing search functionality...
   Query: 'FalkorDB performance' -> 2 results (0.089s)
     - FalkorDB Setup: Successfully set up FalkorDB as graph database...
     - Performance Testing: FalkorDB demonstrates faster startup times...
   ✅ Search operations completed

🎉 FalkorDB basic usage example completed successfully!
```
