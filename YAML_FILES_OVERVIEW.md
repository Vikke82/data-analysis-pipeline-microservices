# Current YAML Configuration Files Overview

This document shows the actual YAML files present in your `k8s-microservices/` directory and their purposes.

## 📁 Existing YAML Files

### **Core Infrastructure Files**

1. **`persistent-volume.yaml`** - Shared storage configuration
   - Creates PersistentVolumeClaim for data sharing
   - 10GB storage allocation
   - ReadWriteOnce access mode (limitation causing Multi-Attach errors)

2. **`redis-deployment.yaml`** - Message queue service
   - Redis container for inter-service communication
   - Internal service for pub/sub messaging
   - Used for event notifications between services

3. **`finnhub-config.yaml`** - API credentials secret
   - Stores Finnhub API key securely
   - Referenced by data-ingest service
   - Contains sensitive authentication data

### **Service Deployment Files**

4. **`data-ingest-deployment.yaml`** - Stock data fetching service
   - Fetches data from Finnhub API every 15 minutes
   - Mounts shared volume at `/shared/data`
   - Processes comprehensive financial data
   - **Current limitation**: Cannot run simultaneously with visualization

5. **`data-visualization-deployment.yaml`** - Dashboard service
   - Streamlit web application
   - Reads CSV files from shared volume
   - Exposes port 8501 for web access
   - **Current limitation**: Cannot run simultaneously with data-ingest

6. **`data-clean-deployment.yaml`** - Data processing service
   - Currently not actively used in stock pipeline
   - Originally for CSC Allas data cleaning
   - Could be repurposed for additional data processing

### **Build Configuration**

7. **`build-config.yaml`** - OpenShift Source-to-Image
   - Defines how to build Docker images from source code
   - Alternative to local Docker builds
   - Useful when Docker Desktop has permission issues

## 🔍 Key Configuration Analysis

### **Shared Volume Configuration**
```yaml
# From persistent-volume.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
  namespace: data-pipeline-microservices
spec:
  accessModes:
    - ReadWriteOnce  # ⚠️ This causes the Multi-Attach limitation
  resources:
    requests:
      storage: 10Gi
```

### **Service Communication Pattern**
```yaml
# Services reference shared volume
volumeMounts:
- name: shared-data
  mountPath: /shared/data  # Common mount point

volumes:
- name: shared-data
  persistentVolumeClaim:
    claimName: shared-data-pvc  # Same PVC shared
```

### **Environment Variable Management**
```yaml
# Services get configuration from ConfigMap and Secrets
env:
- name: FINNHUB_API_KEY
  valueFrom:
    secretKeyRef:
      name: finnhub-credentials
      key: FINNHUB_API_KEY
- name: REDIS_HOST
  value: "redis-service"
- name: SHARED_DATA_PATH
  value: "/shared/data"
```

## 🚨 Current Architecture Limitations

### **1. Volume Access Conflict**
- **Problem**: ReadWriteOnce means only one pod can mount the shared volume
- **Symptom**: "Multi-Attach error" when both services try to start
- **Current Workaround**: Manual scaling (one service at a time)
- **Production Fix Needed**: ReadWriteMany storage or separate volumes

### **2. Manual Service Orchestration**
```bash
# Current process to switch services:
oc scale deployment data-ingest --replicas=0
oc scale deployment data-visualization --replicas=1

# Or vice versa:
oc scale deployment data-visualization --replicas=0  
oc scale deployment data-ingest --replicas=1
```

### **3. Missing Configuration Files**
Your project could benefit from these additional YAML files:

#### **Missing: Namespace Configuration**
```yaml
# Should create: namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: data-pipeline-microservices
```

#### **Missing: ConfigMap for Environment Variables**
```yaml
# Should create: pipeline-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-config
  namespace: data-pipeline-microservices
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  SHARED_DATA_PATH: "/shared/data"
  LOG_LEVEL: "INFO"
  STOCK_SYMBOLS: "AAPL,GOOGL,MSFT,TSLA,AMZN,NVDA,META"
```

#### **Missing: External Access Route**
```yaml
# Should create: data-visualization-route.yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: data-visualization-route
  namespace: data-pipeline-microservices
spec:
  to:
    kind: Service
    name: data-visualization-service
  port:
    targetPort: 8501
  tls:
    termination: edge
```

## 📊 Data Flow Through YAML Configurations

```
1. persistent-volume.yaml
   ↓ Creates shared storage
   
2. redis-deployment.yaml  
   ↓ Provides message queue
   
3. finnhub-config.yaml
   ↓ Stores API credentials
   
4. data-ingest-deployment.yaml
   ↓ Fetches data → saves to shared volume
   
5. data-visualization-deployment.yaml
   ↓ Reads from shared volume → displays dashboard
```

## 🎯 Recommended Next Steps

1. **Add missing YAML files** for complete configuration
2. **Implement ReadWriteMany storage** to fix Multi-Attach errors
3. **Add Route configuration** for external dashboard access
4. **Create proper ConfigMap** for centralized environment management
5. **Consider data-clean service integration** for enhanced data processing

## 📝 File Deployment Order

For proper deployment, apply YAML files in this order:

```bash
# 1. Infrastructure
oc apply -f k8s-microservices/namespace.yaml           # (missing - should create)
oc apply -f k8s-microservices/persistent-volume.yaml   # ✅ exists

# 2. Configuration  
oc apply -f k8s-microservices/pipeline-config.yaml     # (missing - should create)
oc apply -f k8s-microservices/finnhub-config.yaml      # ✅ exists

# 3. Services
oc apply -f k8s-microservices/redis-deployment.yaml    # ✅ exists
oc apply -f k8s-microservices/data-ingest-deployment.yaml        # ✅ exists
oc apply -f k8s-microservices/data-visualization-deployment.yaml # ✅ exists

# 4. External Access
oc apply -f k8s-microservices/data-visualization-route.yaml      # (missing - should create)
```

This overview shows your current YAML structure and identifies gaps that should be filled for a complete OpenShift deployment configuration.