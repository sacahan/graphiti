<!-- filepath: /Users/sacahan/Documents/workspace/graphiti/docs/setup/docker-deployment.md -->
# Docker 部署指南

## 快速開始

使用 Docker 在 5 分鐘內部署 Graphiti 搭配 FalkorDB。

```bash
# 下載程式碼庫
git clone https://github.com/your-org/graphiti.git
cd graphiti/mcp_server

# 複製環境變數範本
cp .env.falkordb.example .env

# 編輯並填入您的 OpenAI API 金鑰
nano .env

# 啟動整合服務
docker-compose -f docker-compose.falkordb.yml up -d
```

## Docker Compose 部署

### FalkorDB Stack（推薦）

最佳化的 FalkorDB 部署可提供更快啟動及更低記憶體用量：

```yaml
# docker-compose.falkordb.yml
version: "3.8"

services:
  falkordb:
    image: falkordb/falkordb:edge
    container_name: graphiti-falkordb
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
    environment:
      - FALKOR_QUERY_TIMEOUT=300000
      - FALKOR_MAX_MEMORY=512MB
    healthcheck:
      test: ["CMD", "redis-cli", "-p", "6379", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"

  graphiti-mcp:
    image: graphiti-mcp:falkordb
    container_name: graphiti-mcp-server
    build:
      context: ..
      dockerfile: mcp_server/Dockerfile.falkordb
    env_file:
      - .env
    depends_on:
      falkordb:
        condition: service_healthy
    environment:
      - GRAPHITI_DB_TYPE=falkordb
      - FALKORDB_URL=redis://falkordb:6379
      - SEMAPHORE_LIMIT=20
    ports:
      - "8000:8000"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1024M
          cpus: "2.0"

volumes:
  falkordb_data:
    driver: local
```

### 傳統 Neo4j Stack

作為比較，傳統 Neo4j 部署：

```bash
# 啟動 Neo4j stack
docker-compose up -d
```

## 環境設定

### 必要環境變數

建立 `.env` 檔案：

```bash
# 資料庫設定
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://falkordb:6379

# LLM 設定（必填）
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4.1-mini

# 效能調校
SEMAPHORE_LIMIT=20
LOG_LEVEL=INFO
```

### 生產環境設定

```bash
# 生產用 .env
GRAPHITI_DB_TYPE=falkordb
FALKORDB_URL=redis://falkordb:6379
OPENAI_API_KEY=your_production_api_key
MODEL_NAME=gpt-4.1-mini
SMALL_MODEL_NAME=gpt-4.1-nano
EMBEDDER_MODEL_NAME=text-embedding-3-small
SEMAPHORE_LIMIT=25
LOG_LEVEL=WARNING
GROUP_ID=production
USE_CUSTOM_ENTITIES=true
```

## Dockerfile 最佳化

### FalkorDB 多階段 Dockerfile

最佳化 Dockerfile 可減少容器大小並加快啟動：

```dockerfile
# Dockerfile.falkordb
FROM python:3.12-slim as builder

# 安裝建置相依套件
RUN apt-get update && apt-get install -y \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 相依套件
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir graphiti-core[falkordb]

FROM python:3.12-slim as runtime

# 僅安裝執行時相依套件
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 使用者
RUN useradd --create-home --shell /bin/bash graphiti

# 從 builder 複製已安裝套件
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 複製應用程式
WORKDIR /app
COPY mcp_server/ ./
COPY graphiti_core/ ../graphiti_core/

# 設定擁有權
RUN chown -R graphiti:graphiti /app

# 切換至非 root 使用者
USER graphiti

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
  CMD curl -f http://localhost:8000/status || exit 1

EXPOSE 8000

CMD ["python", "graphiti_mcp_server.py", "--transport", "sse"]
```

## 部署指令

### 本地開發

```bash
# 啟動開發環境
cd mcp_server
docker-compose -f docker-compose.falkordb.yml up --build

# 查看日誌
docker-compose -f docker-compose.falkordb.yml logs -f

# 停止服務
docker-compose -f docker-compose.falkordb.yml down
```

### 生產部署

```bash
# 建置生產映像檔
docker-compose -f docker-compose.falkordb.yml build

# 以生產模式啟動
docker-compose -f docker-compose.falkordb.yml up -d

# 監控服務
docker-compose -f docker-compose.falkordb.yml ps
docker stats
```

### 擴展

```bash
# 擴展 MCP 伺服器（多實例）
docker-compose -f docker-compose.falkordb.yml up -d --scale graphiti-mcp=3

# 多實例需配置負載平衡器
```

## 健康檢查與監控

### 內建健康檢查

兩個容器皆包含完整健康檢查：

```bash
# 檢查服務健康狀態
docker-compose -f docker-compose.falkordb.yml ps

# 手動健康檢查
curl http://localhost:8000/status
curl http://localhost:8000/performance
```

### 監控 Stack

可選：加入 Prometheus 監控：

```yaml
# 加入 docker-compose.falkordb.yml
prometheus:
  image: prom/prometheus:latest
  container_name: graphiti-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
  depends_on:
    - graphiti-mcp

grafana:
  image: grafana/grafana:latest
  container_name: graphiti-grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
  depends_on:
    - prometheus
```

## 效能最佳化

### 容器資源限制

FalkorDB 最佳化資源分配：

```yaml
# FalkorDB 容器
deploy:
  resources:
    limits:
      memory: 512M      # 足夠 FalkorDB 使用
      cpus: "1.0"
    reservations:
      memory: 256M
      cpus: "0.5"

# Graphiti MCP 容器
deploy:
  resources:
    limits:
      memory: 1024M     # 支援嵌入模型
      cpus: "2.0"
    reservations:
      memory: 512M
      cpus: "0.5"
```

### Volume 最佳化

```yaml
volumes:
  falkordb_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/graphiti/data # 建議使用高速 SSD
```

## 備份與持久化

### 資料持久化

FalkorDB 資料會儲存於 Docker volume：

```bash
# 建立備份
docker run --rm -v mcp_server_falkordb_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar czf /backup/falkordb-backup-$(date +%Y%m%d).tar.gz -C /data .

# 還原備份
docker run --rm -v mcp_server_falkordb_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar xzf /backup/falkordb-backup-20241201.tar.gz -C /data
```

### 自動化備份

```yaml
# 加入備份服務至 docker-compose
backup:
  image: alpine
  container_name: graphiti-backup
  volumes:
    - falkordb_data:/data:ro
    - ./backups:/backups
  command: >
    sh -c "
      while true; do
        tar czf /backups/falkordb-backup-$$(date +%Y%m%d-%H%M).tar.gz -C /data .
        sleep 86400  # 每日備份
      done
    "
  depends_on:
    - falkordb
  restart: unless-stopped
```

## 疑難排解

### 常見問題

#### 容器啟動失敗

```bash
# 檢查容器日誌
docker-compose -f docker-compose.falkordb.yml logs falkordb
docker-compose -f docker-compose.falkordb.yml logs graphiti-mcp

# 檢查容器狀態
docker-compose -f docker-compose.falkordb.yml ps

# 重新啟動失敗容器
docker-compose -f docker-compose.falkordb.yml restart
```

#### 效能問題

```bash
# 監控資源使用
docker stats

# 檢查效能指標
curl http://localhost:8000/performance

# 調整 docker-compose.falkordb.yml 資源限制
```

#### 連線問題

```bash
# 測試 FalkorDB 連線
docker exec graphiti-falkordb redis-cli ping

# 測試 MCP 伺服器
curl http://localhost:8000/status

# 檢查網路連線
docker-compose -f docker-compose.falkordb.yml exec graphiti-mcp \
  ping falkordb
```

### 除錯模式

```bash
# 啟用除錯日誌
echo "LOG_LEVEL=DEBUG" >> .env

# 以除錯模式重啟
docker-compose -f docker-compose.falkordb.yml up -d

# 追蹤除錯日誌
docker-compose -f docker-compose.falkordb.yml logs -f graphiti-mcp
```

### 容器 Shell 存取

```bash
# 進入 FalkorDB 容器
docker exec -it graphiti-falkordb redis-cli

# 進入 MCP 伺服器容器
docker exec -it graphiti-mcp-server bash

# 檢查 Python 環境
docker exec -it graphiti-mcp-server python -c "
from graphiti_core.driver.factory import DriverFactory
print('Driver factory working')
"
```

## 安全性考量

### 生產環境安全

```yaml
# docker-compose.yml 安全性強化
services:
  falkordb:
    environment:
      - REDIS_PASSWORD=${FALKORDB_PASSWORD}
    command: redis-server --requirepass ${FALKORDB_PASSWORD}

  graphiti-mcp:
    environment:
      - FALKORDB_PASSWORD=${FALKORDB_PASSWORD}
    read_only: true
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
```

### 網路安全

```yaml
# 建立隔離網路
networks:
  graphiti-network:
    driver: bridge
    internal: false

services:
  falkordb:
    networks:
      - graphiti-network
    ports: [] # 移除外部端口暴露

  graphiti-mcp:
    networks:
      - graphiti-network
    ports:
      - "8000:8000"
```

## 容器大小最佳化

目標容器大小：

- **FalkorDB**：~50MB（基於 Redis）
- **Graphiti MCP**：<400MB（Python + 相依套件）
- **整合 Stack**：<500MB

最佳化技巧：

1. 多階段 Docker 建置
2. 精簡基礎映像檔（`slim`）
3. 有效層快取
4. 移除不必要套件

## 從 Neo4j 遷移

從 Neo4j Docker 部署遷移：

```bash
# 停止 Neo4j stack
docker-compose down

# 備份 Neo4j 資料（如有需要）
# ... 備份流程 ...

# 切換至 FalkorDB
docker-compose -f docker-compose.falkordb.yml up -d

# 匯入資料（如有需要）
# ... 資料遷移流程 ...
```

## 下一步

- [Kubernetes 部署](../../examples/k8s/)
- [效能調校](../guides/performance-tuning.md)
- [監控設定](../guides/monitoring.md)
- [備份策略](../guides/backup-recovery.md)
