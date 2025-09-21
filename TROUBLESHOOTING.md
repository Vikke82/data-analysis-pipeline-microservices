# Troubleshooting Guide - Stock Market Data Pipeline

This guide helps resolve common issues when deploying and running the Stock Market Data Analysis Pipeline on CSC Rahti (OpenShift).

## 🚨 Common Deployment Issues

### **Issue 1: Pod Stuck in "ContainerCreating"**

**Symptoms:**
```bash
NAME                                  READY   STATUS              RESTARTS   AGE
data-ingest-xxxxxxxxxx-xxxxx          0/1     ContainerCreating   0          5m
```

**Diagnosis:**
```bash
# Check pod details
oc describe pod POD-NAME

# Look for error messages in Events section
```

**Common Causes & Solutions:**

#### **A. Multi-Attach Volume Error**
```
Multi-Attach error for volume "pvc-xxxxx" Volume is already used by pod(s)
```

**Solution:**
```bash
# Scale down conflicting service
oc scale deployment data-visualization --replicas=0

# Wait for pod termination
oc get pods -w

# Scale up desired service
oc scale deployment data-ingest --replicas=1
```

#### **B. Image Pull Issues**
```
Failed to pull image: ErrImagePull
```

**Solution:**
```bash
# Check image exists and is accessible
oc describe deployment data-ingest

# If using custom images, verify registry access
docker pull docker.io/vikke82/data-ingest:stock-v1.0

# For image pull secrets (if needed):
oc create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password
```

#### **C. Resource Constraints**
```
Insufficient cpu/memory
```

**Solution:**
```bash
# Check quota and usage
oc describe quota
oc top pods
oc top nodes

# Reduce resource requests in deployment YAML:
resources:
  requests:
    memory: "64Mi"    # Reduced from 128Mi
    cpu: "25m"        # Reduced from 50m
```

### **Issue 2: Pod CrashLoopBackOff**

**Symptoms:**
```bash
NAME                                  READY   STATUS             RESTARTS   AGE
data-ingest-xxxxxxxxxx-xxxxx          0/1     CrashLoopBackOff   5          10m
```

**Diagnosis:**
```bash
# Check pod logs
oc logs POD-NAME --previous

# Check current logs
oc logs -f POD-NAME
```

**Common Causes & Solutions:**

#### **A. Missing Environment Variables**
```
KeyError: 'FINNHUB_API_KEY'
```

**Solution:**
```bash
# Verify secret exists
oc get secrets finnhub-credentials

# Check secret content (masked)
oc describe secret finnhub-credentials

# Recreate secret if needed
oc delete secret finnhub-credentials
oc create secret generic finnhub-credentials \
  --from-literal=FINNHUB_API_KEY='your-api-key'
```

#### **B. Redis Connection Failed**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check Redis pod status
oc get pods -l app=redis

# Verify Redis service
oc get services redis-service

# Test Redis connectivity
oc exec deployment/redis -- redis-cli ping

# If Redis is down, redeploy
oc delete -f redis-deployment.yaml
oc apply -f redis-deployment.yaml
```

#### **C. Invalid API Key**
```
HTTP 401: Unauthorized - Invalid API key
```

**Solution:**
```bash
# Verify API key is correct
# Login to Finnhub dashboard: https://finnhub.io/dashboard
# Copy the correct API key

# Update secret
oc patch secret finnhub-credentials -p='{"stringData":{"FINNHUB_API_KEY":"your-correct-api-key"}}'

# Restart pods to pick up new secret
oc rollout restart deployment/data-ingest
```

### **Issue 3: Route/Dashboard Not Accessible**

**Symptoms:**
- Dashboard URL returns 404 or connection timeout
- Route shows but webpage won't load

**Diagnosis:**
```bash
# Check route configuration
oc get routes
oc describe route stock-dashboard

# Check service endpoints
oc get endpoints data-visualization-service

# Check pod readiness
oc get pods -l app=data-visualization
```

**Solutions:**

#### **A. Service Not Running**
```bash
# Check if visualization pod is running
oc get pods -l app=data-visualization

# If not running, check for volume conflicts
oc describe pod POD-NAME

# Scale down conflicting services
oc scale deployment data-ingest --replicas=0
oc scale deployment data-clean --replicas=0
oc scale deployment data-visualization --replicas=1
```

#### **B. Port Configuration Issues**
```bash
# Verify service port mapping
oc get service data-visualization-service -o yaml

# Should show:
# ports:
# - name: streamlit
#   port: 8501
#   targetPort: 8501

# Recreate service if needed
oc delete service data-visualization-service
oc apply -f data-visualization-deployment.yaml
```

#### **C. Route Configuration**
```bash
# Create route manually if missing
oc expose service data-visualization-service --name=stock-dashboard

# For HTTPS:
oc create route edge stock-dashboard-secure \
  --service=data-visualization-service \
  --port=8501
```

### **Issue 4: No Data in Dashboard**

**Symptoms:**
- Dashboard loads but shows empty charts
- "No data available" messages

**Diagnosis:**
```bash
# Check if data files exist
oc exec deployment/data-ingest -- ls -la /shared/data/

# Check data-ingest logs
oc logs deployment/data-ingest --tail=50

# Check shared volume mounting
oc describe pod data-ingest-POD-NAME
```

**Solutions:**

#### **A. Data Ingestion Not Running**
```bash
# Switch to data ingestion mode
oc scale deployment data-visualization --replicas=0
oc scale deployment data-ingest --replicas=1

# Wait for data collection (15 minutes for first run)
oc logs -f deployment/data-ingest

# Look for: "Stock data ingestion completed"
```

#### **B. API Rate Limiting**
```
HTTP 429: Too Many Requests
```

**Solution:**
```bash
# Wait for rate limit reset (usually 1 minute)
# Increase delay in data-ingest service

# Check API usage in Finnhub dashboard
```

#### **C. File Permission Issues**
```bash
# Check file permissions in shared volume
oc exec deployment/data-ingest -- ls -la /shared/data/

# Fix permissions if needed
oc exec deployment/data-ingest -- chmod -R 755 /shared/data/
```

## 🔧 Performance Issues

### **Issue 5: Slow Dashboard Loading**

**Symptoms:**
- Dashboard takes long time to load
- Charts render slowly

**Solutions:**

#### **A. Increase Pod Resources**
```yaml
# Edit data-visualization-deployment.yaml
resources:
  requests:
    memory: "256Mi"  # Increased from 128Mi
    cpu: "100m"      # Increased from 50m
  limits:
    memory: "512Mi"  # Increased from 256Mi
    cpu: "200m"      # Increased from 100m
```

#### **B. Optimize Data Processing**
```bash
# Reduce data retention period
oc exec deployment/data-ingest -- find /shared/data -name "*.csv" -mtime +3 -delete

# Restart services
oc rollout restart deployment/data-visualization
```

### **Issue 6: High Memory Usage**

**Diagnosis:**
```bash
# Check resource usage
oc top pods

# Check memory limits
oc describe pod POD-NAME | grep -A 5 -B 5 memory
```

**Solutions:**
```bash
# Increase memory limits
oc patch deployment data-visualization -p='{"spec":{"template":{"spec":{"containers":[{"name":"data-visualization","resources":{"limits":{"memory":"1Gi"}}}]}}}}'

# Or reduce data processing load
# Edit app.py to process fewer symbols or shorter time periods
```

## 🛠️ Advanced Troubleshooting

### **Debug Mode Activation**

```bash
# Enable debug logging
oc set env deployment/data-ingest LOG_LEVEL=DEBUG
oc set env deployment/data-visualization LOG_LEVEL=DEBUG

# View detailed logs
oc logs -f deployment/data-ingest
```

### **Interactive Pod Debugging**

```bash
# Access pod shell for debugging
oc exec -it deployment/data-ingest -- /bin/bash

# Inside pod, check:
# - File system: ls -la /shared/data/
# - Network: ping redis-service
# - Environment: env | grep -E "(REDIS|FINNHUB)"
# - Python packages: pip list
```

### **Network Connectivity Tests**

```bash
# Test Redis connectivity
oc exec deployment/data-ingest -- nc -zv redis-service 6379

# Test external API access
oc exec deployment/data-ingest -- curl -I "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR-API-KEY"

# Check DNS resolution
oc exec deployment/data-ingest -- nslookup redis-service
```

### **Storage Issues**

```bash
# Check persistent volume status
oc get pv,pvc

# Check storage usage
oc exec deployment/data-ingest -- df -h

# Check volume mounting
oc describe pod POD-NAME | grep -A 10 -B 5 "Mounts:"
```

## 📊 Monitoring Commands

### **Health Check Scripts**

```bash
#!/bin/bash
# health-check.sh - Quick system health verification

echo "=== Pod Status ==="
oc get pods

echo "=== Service Status ==="
oc get services

echo "=== Route Status ==="
oc get routes

echo "=== Resource Usage ==="
oc top pods 2>/dev/null || echo "Metrics not available"

echo "=== Redis Health ==="
oc exec deployment/redis -- redis-cli ping 2>/dev/null || echo "Redis not accessible"

echo "=== Data Files ==="
oc exec deployment/data-ingest -- ls -la /shared/data/ 2>/dev/null || echo "Data volume not accessible"

echo "=== Recent Logs ==="
oc logs deployment/data-visualization --tail=5 2>/dev/null || echo "Visualization logs not available"
```

### **Log Aggregation**

```bash
# Save logs for analysis
oc logs deployment/data-ingest > data-ingest.log
oc logs deployment/data-visualization > data-visualization.log
oc logs deployment/redis > redis.log

# Search for errors
grep -i error *.log
grep -i failed *.log
```

## 🔄 Recovery Procedures

### **Complete Service Reset**

```bash
# Scale down all services
oc scale deployment data-ingest --replicas=0
oc scale deployment data-visualization --replicas=0
oc scale deployment data-clean --replicas=0

# Wait for pods to terminate
oc get pods -w

# Restart Redis
oc rollout restart deployment/redis
oc wait --for=condition=available --timeout=300s deployment/redis

# Scale up desired service
oc scale deployment data-visualization --replicas=1
```

### **Storage Reset**

```bash
# WARNING: This will delete all data
oc scale deployment data-ingest --replicas=0
oc scale deployment data-visualization --replicas=0

# Clean shared volume
oc exec deployment/redis -- rm -rf /shared/data/*

# Restart data collection
oc scale deployment data-ingest --replicas=1
```

### **Complete Redeployment**

```bash
# Delete all application resources
oc delete -f data-ingest-deployment.yaml
oc delete -f data-visualization-deployment.yaml  
oc delete -f data-clean-deployment.yaml
oc delete -f redis-deployment.yaml

# Wait for cleanup
sleep 30

# Redeploy in order
oc apply -f redis-deployment.yaml
oc apply -f data-ingest-deployment.yaml
oc apply -f data-visualization-deployment.yaml
```

## 📞 Getting Help

### **Log Collection for Support**

```bash
# Create comprehensive diagnostic report
mkdir diagnostic-$(date +%Y%m%d-%H%M%S)
cd diagnostic-*/

# Collect system information
oc get all -o yaml > all-resources.yaml
oc describe quota > quota.txt
oc top pods > resource-usage.txt

# Collect logs
oc logs deployment/data-ingest > data-ingest.log
oc logs deployment/data-visualization > data-visualization.log
oc logs deployment/redis > redis.log

# Create archive
cd ..
tar -czf diagnostic-$(date +%Y%m%d-%H%M%S).tar.gz diagnostic-*/
```

### **Support Channels**

1. **GitHub Issues**: Create issue with diagnostic information
2. **CSC Service Desk**: For Rahti platform issues
3. **Course Forum**: For educational assistance
4. **Documentation**: Check README.md and INFRASTRUCTURE_GUIDE.md

### **Common Solutions Summary**

| Problem | Quick Solution |
|---------|----------------|
| Pod stuck creating | Check `oc describe pod` for volume conflicts |
| Dashboard not loading | Scale down data-ingest, scale up visualization |
| No data in charts | Run data-ingest for 15 minutes first |
| API errors | Verify Finnhub API key in secret |
| Memory issues | Increase pod resource limits |
| Route not working | Recreate with `oc expose service` |

This troubleshooting guide covers the most common issues. For persistent problems, collect diagnostic information and seek support through appropriate channels.