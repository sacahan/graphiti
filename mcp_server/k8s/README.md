# Kubernetes Deployment for Graphiti MCP with FalkorDB

This directory contains Kubernetes manifests for deploying Graphiti MCP Server with FalkorDB in a Kubernetes cluster.

## Quick Start

1. **Create the namespace and apply configurations:**

   ```bash
   kubectl apply -f namespace.yaml
   kubectl apply -f configmap.yaml
   kubectl apply -f falkordb-deployment.yaml
   kubectl apply -f graphiti-deployment.yaml
   ```

2. **Update the secret with your API keys:**

   ```bash
   kubectl edit secret graphiti-secrets -n graphiti
   # Update OPENAI_API_KEY with your actual API key
   ```

3. **Verify deployment:**
   ```bash
   kubectl get pods -n graphiti
   kubectl logs -f deployment/graphiti-mcp -n graphiti
   ```

## Files Overview

- **namespace.yaml**: Creates the `graphiti` namespace
- **configmap.yaml**: Contains configuration and secrets for the application
- **falkordb-deployment.yaml**: FalkorDB database deployment, service, and persistent volume
- **graphiti-deployment.yaml**: Graphiti MCP Server deployment and service

## Configuration

### Required Configuration

Update `configmap.yaml` to configure your deployment:

```yaml
# In the Secret section, update with your actual API keys:
stringData:
  OPENAI_API_KEY: "your_actual_openai_api_key"
```

### Optional Configuration

- **Scaling**: Modify `replicas` in `graphiti-deployment.yaml`
- **Resources**: Adjust CPU/memory limits based on your cluster capacity
- **Storage**: Modify PVC size in `falkordb-deployment.yaml`
- **Ingress**: Uncomment and configure ingress in `graphiti-deployment.yaml`

## Accessing the Service

### Internal Access (within cluster)

The service is available at: `http://graphiti-mcp-service.graphiti.svc.cluster.local:8000`

### External Access

#### Option 1: Port Forward (Development)

```bash
kubectl port-forward service/graphiti-mcp-service 8000:8000 -n graphiti
```

Access at: `http://localhost:8000`

#### Option 2: NodePort (Simple external access)

Edit `graphiti-deployment.yaml`:

```yaml
spec:
  type: NodePort
```

#### Option 3: LoadBalancer (Cloud environments)

Edit `graphiti-deployment.yaml`:

```yaml
spec:
  type: LoadBalancer
```

#### Option 4: Ingress (Production)

Uncomment and configure the Ingress section in `graphiti-deployment.yaml`

## Monitoring

The deployment includes annotations for Prometheus scraping:

- Metrics endpoint: `/metrics`
- Port: `8000`

To enable monitoring, ensure your Prometheus is configured to scrape pods with the appropriate annotations.

## Security

- Containers run as non-root user (UID 1000)
- Security contexts applied with minimal privileges
- Secrets stored in Kubernetes Secret objects

## Troubleshooting

### Check pod status:

```bash
kubectl get pods -n graphiti
kubectl describe pod <pod-name> -n graphiti
```

### Check logs:

```bash
kubectl logs -f deployment/graphiti-mcp -n graphiti
kubectl logs -f deployment/falkordb -n graphiti
```

### Check services:

```bash
kubectl get svc -n graphiti
kubectl describe svc graphiti-mcp-service -n graphiti
```

### Test connectivity:

```bash
# Port forward and test
kubectl port-forward service/graphiti-mcp-service 8000:8000 -n graphiti &
curl http://localhost:8000/status
```

## Production Considerations

1. **Resource Limits**: Adjust CPU/memory limits based on actual usage
2. **Persistence**: Configure appropriate storage class for PVC
3. **High Availability**: Increase FalkorDB replicas with clustering configuration
4. **Backup**: Implement backup strategy for FalkorDB data
5. **TLS**: Configure TLS termination at ingress or load balancer
6. **Network Policies**: Implement network policies for security
7. **Monitoring**: Set up comprehensive monitoring and alerting

## Cleanup

To remove the deployment:

```bash
kubectl delete -f graphiti-deployment.yaml
kubectl delete -f falkordb-deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete -f namespace.yaml
```
