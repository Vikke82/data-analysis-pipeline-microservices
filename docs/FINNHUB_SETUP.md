# Stock Market Data Pipeline Configuration

This guide explains how to configure the stock market data pipeline with Finnhub API integration.

## Prerequisites

1. **Finnhub API Key**: Sign up at [Finnhub.io](https://finnhub.io/docs/api) to get your free API key
2. **Kubernetes/OpenShift cluster** access

## Configuration Steps

### 1. Set up Finnhub API Key

Replace the placeholder API key in `finnhub-config.yaml`:

```bash
# Create base64 encoded API key
echo -n "your_actual_finnhub_api_key" | base64

# Update the secret in finnhub-config.yaml with the base64 encoded key
```

### 2. Deploy Configuration

Apply the configuration files:

```bash
# Apply the Finnhub configuration
kubectl apply -f k8s-microservices/finnhub-config.yaml

# Verify the secret and configmap
kubectl get secrets finnhub-credentials
kubectl get configmap pipeline-config
```

### 3. Customize Stock Symbols

Edit the `STOCK_SYMBOLS` in `finnhub-config.yaml` to change which stocks are tracked:

```yaml
data:
  STOCK_SYMBOLS: "AAPL,GOOGL,MSFT,TSLA,AMZN,NVDA,META,NFLX,AMD,CRM"
```

### 4. Deploy Services

Deploy all services in order:

```bash
# Deploy persistent storage
kubectl apply -f k8s-microservices/persistent-volume.yaml

# Deploy Redis
kubectl apply -f k8s-microservices/redis-deployment.yaml

# Deploy microservices
kubectl apply -f k8s-microservices/data-ingest-deployment.yaml
kubectl apply -f k8s-microservices/data-clean-deployment.yaml
kubectl apply -f k8s-microservices/data-visualization-deployment.yaml
```

## Environment Variables

### Data Ingest Service
- `FINNHUB_API_KEY`: Your Finnhub API key (from secret)
- `STOCK_SYMBOLS`: Comma-separated list of stock symbols (from configmap)
- `REDIS_HOST`: Redis service hostname
- `REDIS_PORT`: Redis service port
- `SHARED_DATA_PATH`: Path to shared storage
- `LOG_LEVEL`: Logging level

### Data Clean Service
- `REDIS_HOST`: Redis service hostname
- `REDIS_PORT`: Redis service port
- `SHARED_DATA_PATH`: Path to shared storage
- `LOG_LEVEL`: Logging level

### Data Visualization Service
- `REDIS_HOST`: Redis service hostname
- `REDIS_PORT`: Redis service port
- `SHARED_DATA_PATH`: Path to shared storage

## API Rate Limits

Finnhub free tier provides:
- 60 API calls/minute
- Real-time data for US stocks
- Historical data (30 days)

For production usage, consider upgrading to a paid plan for higher rate limits.

## Monitoring

Check service status:

```bash
# Check pods
kubectl get pods

# Check service logs
kubectl logs -f deployment/data-ingest
kubectl logs -f deployment/data-clean
kubectl logs -f deployment/data-visualization

# Check Redis status
kubectl exec -it deployment/redis -- redis-cli ping
```

## Troubleshooting

1. **API Key Issues**: Ensure the base64 encoding is correct
2. **Rate Limiting**: Monitor logs for rate limit errors
3. **Stock Symbol Errors**: Verify symbol format (uppercase, valid symbols)
4. **Redis Connection**: Check Redis service is running and accessible