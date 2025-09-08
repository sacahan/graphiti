# Environment Variables Reference

## Database Configuration

### Database Type Selection

| Variable           | Default | Description                             |
| ------------------ | ------- | --------------------------------------- |
| `GRAPHITI_DB_TYPE` | `neo4j` | Database backend: `neo4j` or `falkordb` |

### FalkorDB Configuration

| Variable            | Default                  | Description                      |
| ------------------- | ------------------------ | -------------------------------- |
| `FALKORDB_URL`      | `redis://localhost:6379` | FalkorDB connection string       |
| `FALKORDB_HOST`     | `localhost`              | FalkorDB server hostname         |
| `FALKORDB_PORT`     | `6379`                   | FalkorDB server port             |
| `FALKORDB_PASSWORD` | _(none)_                 | FalkorDB authentication password |
| `GRAPHITI_DB_NAME`  | `graphiti_db`            | FalkorDB graph database name     |

### Neo4j Configuration

| Variable         | Required | Default  | Description                                          |
| ---------------- | -------- | -------- | ---------------------------------------------------- |
| `NEO4J_URI`      | Yes      | _(none)_ | Neo4j connection URI (e.g., `bolt://localhost:7687`) |
| `NEO4J_USER`     | Yes      | _(none)_ | Neo4j username                                       |
| `NEO4J_PASSWORD` | Yes      | _(none)_ | Neo4j password                                       |
| `NEO4J_DATABASE` | No       | `neo4j`  | Neo4j database name                                  |

## LLM Configuration

### OpenAI

| Variable              | Required | Default                  | Description                        |
| --------------------- | -------- | ------------------------ | ---------------------------------- |
| `OPENAI_API_KEY`      | Yes\*    | _(none)_                 | OpenAI API key                     |
| `MODEL_NAME`          | No       | `gpt-4.1-mini`           | Primary LLM model                  |
| `SMALL_MODEL_NAME`    | No       | `gpt-4.1-nano`           | Lightweight model for simple tasks |
| `EMBEDDER_MODEL_NAME` | No       | `text-embedding-3-small` | Embedding model                    |
| `LLM_TEMPERATURE`     | No       | `0.0`                    | LLM temperature (0.0-1.0)          |

_\*Required when `USE_CUSTOM_ENTITIES=true`_

### Azure OpenAI

| Variable                   | Required | Default              | Description               |
| -------------------------- | -------- | -------------------- | ------------------------- |
| `AZURE_OPENAI_ENDPOINT`    | No       | _(none)_             | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION` | No       | `2023-12-01-preview` | Azure API version         |
| `AZURE_OPENAI_API_KEY`     | No       | _(none)_             | Azure OpenAI API key      |

### Alternative LLM Providers

| Variable            | Required | Default  | Description              |
| ------------------- | -------- | -------- | ------------------------ |
| `ANTHROPIC_API_KEY` | No       | _(none)_ | Anthropic Claude API key |
| `GOOGLE_API_KEY`    | No       | _(none)_ | Google Gemini API key    |
| `GROQ_API_KEY`      | No       | _(none)_ | Groq API key             |

## Performance Configuration

### Concurrency

| Variable          | Default                        | Description                   |
| ----------------- | ------------------------------ | ----------------------------- |
| `SEMAPHORE_LIMIT` | `10` (Neo4j) / `20` (FalkorDB) | Maximum concurrent operations |

### FalkorDB Performance Optimization

```bash
# Recommended FalkorDB settings
GRAPHITI_DB_TYPE=falkordb
SEMAPHORE_LIMIT=20        # Higher concurrency for FalkorDB
FALKORDB_URL=redis://localhost:6379
```

### Neo4j Performance Optimization

```bash
# Recommended Neo4j settings
GRAPHITI_DB_TYPE=neo4j
SEMAPHORE_LIMIT=10        # Conservative for Neo4j
NEO4J_URI=bolt://localhost:7687
USE_PARALLEL_RUNTIME=true  # Enterprise only
```

## Application Configuration

### General Settings

| Variable              | Default  | Description                                        |
| --------------------- | -------- | -------------------------------------------------- |
| `GROUP_ID`            | _(none)_ | Default group ID for episodes                      |
| `USE_CUSTOM_ENTITIES` | `false`  | Enable custom entity extraction                    |
| `LOG_LEVEL`           | `INFO`   | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### MCP Server Specific

| Variable           | Default     | Description                    |
| ------------------ | ----------- | ------------------------------ |
| `MCP_SERVER_HOST`  | `localhost` | MCP server bind address        |
| `MCP_SERVER_PORT`  | `8000`      | MCP server port                |
| `PYTHONUNBUFFERED` | _(none)_    | Force unbuffered Python output |

## Container Configuration

### Docker Environment

```bash
# Production container settings
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://falkordb:6379
MCP_SERVER_HOST=0.0.0.0
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

### Kubernetes Environment

```bash
# K8s deployment settings
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://falkordb-service:6379
SEMAPHORE_LIMIT=25
GROUP_ID=production-cluster
```

## Configuration Examples

### Local Development

```bash
# .env file for local development
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
LOG_LEVEL=DEBUG
SEMAPHORE_LIMIT=15
```

### Production Deployment

```bash
# Production environment
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://prod-falkordb:6379
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4.1-mini
EMBEDDER_MODEL_NAME=text-embedding-3-small
SEMAPHORE_LIMIT=30
LOG_LEVEL=INFO
USE_CUSTOM_ENTITIES=true
GROUP_ID=production
```

### Memory-Constrained Environment

```bash
# Optimized for low memory usage
GRAPHITI_DB_TYPE=falkordb
SEMAPHORE_LIMIT=10
MODEL_NAME=gpt-4.1-nano
EMBEDDER_MODEL_NAME=text-embedding-3-small
LLM_TEMPERATURE=0.0
USE_CUSTOM_ENTITIES=false
```

### High-Performance Setup

```bash
# Maximum performance configuration
GRAPHITI_DB_TYPE=falkordb
SEMAPHORE_LIMIT=50
FALKORDB_URL=redis://high-perf-falkordb:6379
MODEL_NAME=gpt-4.1-turbo
LOG_LEVEL=WARNING  # Reduce logging overhead
```

## Connection String Formats

### FalkorDB Connection Strings

```bash
# Basic connection
FALKORDB_URL=redis://localhost:6379

# With authentication
FALKORDB_URL=redis://:password@localhost:6379

# Custom database number
FALKORDB_URL=redis://localhost:6379/1

# Remote server with SSL
FALKORDB_URL=rediss://remote-falkordb.com:6380

# Full format
FALKORDB_URL=redis://username:password@hostname:port/database
```

### Neo4j Connection Strings

```bash
# Local Neo4j
NEO4J_URI=bolt://localhost:7687

# Neo4j Aura (cloud)
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io

# Neo4j with routing
NEO4J_URI=neo4j://cluster.neo4j.io:7687

# Secure connection
NEO4J_URI=bolt+s://secure.neo4j.com:7687
```

## Validation

### Required Variables Check

```bash
# Check required variables for FalkorDB
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY is required"
    exit 1
fi

# Optional: Validate FalkorDB connection
redis-cli -u "$FALKORDB_URL" ping
```

### Environment File Template

Create `.env` from template:

```bash
# Copy and customize environment template
cp docs/examples/.env.template .env

# Edit with your values
nano .env
```

## Security Considerations

### Sensitive Variables

Never commit these to version control:

- `OPENAI_API_KEY`
- `NEO4J_PASSWORD`
- `FALKORDB_PASSWORD`
- `AZURE_OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

### Production Security

```bash
# Use secret management systems
export OPENAI_API_KEY=$(vault kv get -field=api_key secret/openai)
export FALKORDB_PASSWORD=$(kubectl get secret falkordb-auth -o jsonpath='{.data.password}' | base64 -d)
```

## Troubleshooting

### Validation Commands

```bash
# Check current configuration
python -c "import os; print('DB Type:', os.getenv('GRAPHITI_DB_TYPE', 'neo4j'))"

# Test database connection
python -c "
import os
os.environ['GRAPHITI_DB_TYPE'] = 'falkordb'
from graphiti_core.driver.factory import DriverFactory
driver = DriverFactory.create_driver()
print('Connection successful')
"
```

### Common Issues

1. **Wrong database type**: Check `GRAPHITI_DB_TYPE` spelling
2. **Connection failures**: Verify URL format and server availability
3. **Performance issues**: Adjust `SEMAPHORE_LIMIT` for your workload
4. **Memory problems**: Use smaller models or reduce concurrency
