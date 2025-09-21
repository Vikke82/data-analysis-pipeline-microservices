# Stock Market Data Pipeline - Infrastructure Guide

## 📋 Overview

This document provides a comprehensive explanation of the microservices infrastructure, YAML configurations, OpenShift deployment, and shared volume architecture for the Stock Market Data Analysis Pipeline.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenShift Cluster                        │
│                                                             │
│  ┌─────────────────┐   ┌─────────────────┐                │
│  │   data-ingest   │   │ data-visualization │             │
│  │   Service       │   │     Service      │                │
│  │                 │   │                 │                │
│  │ - Fetches stock │   │ - Streamlit UI  │                │
│  │   data from     │   │ - Interactive   │                │
│  │   Finnhub API   │   │   dashboards    │                │
│  │ - Processes     │   │ - Stock charts  │                │
│  │   financial     │   │ - Market        │                │
│  │   indicators    │   │   analysis      │                │
│  └─────────┬───────┘   └─────────┬───────┘                │
│            │                     │                        │
│            │    ┌─────────────────────────────┐           │
│            │    │     Shared Volume           │           │
│            │    │   (PersistentVolume)        │           │
│            └────┤                             ├───────────┘
│                 │  - CSV data files           │
│                 │  - Stock quotes             │
│                 │  - Historical data          │
│                 │  - Company profiles         │
│                 │  - News & earnings          │
│                 │  - Technical indicators     │
│                 └─────────────────────────────┘
│                              │
│            ┌─────────────────┴─────────────────┐
│            │             Redis                 │
│            │         (Message Queue)           │
│            │                                   │
│            │  - Inter-service communication    │
│            │  - Status updates                 │
│            │  - Event notifications            │
│            └───────────────────────────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘

External APIs:
┌─────────────────┐
│   Finnhub API   │  ←── Data ingestion from stock market
│  (Stock Market  │      - Real-time quotes
│      Data)      │      - Historical data
└─────────────────┘      - Company profiles
                         - News & earnings
```

## 🔧 Core Components

### 1. **Data Ingest Service** (`data-ingest`)
- **Purpose**: Fetches comprehensive stock market data from Finnhub API
- **Data Sources**: 
  - Real-time stock quotes
  - Historical price data
  - Company profiles & news
  - Earnings & financial statements
  - Insider transactions
  - Analyst recommendations
  - Social sentiment analysis
  - Dividend history
  - IPO calendar
- **Output**: Multiple CSV files stored in shared volume
- **Scheduling**: Runs every 15 minutes

### 2. **Data Visualization Service** (`data-visualization`)
- **Purpose**: Interactive web dashboard for stock market analysis
- **Technology**: Streamlit-based web application
- **Features**:
  - Real-time stock price charts
  - Candlestick charts with technical indicators
  - Market overview dashboards
  - Performance metrics and trends
- **Port**: 8501 (Streamlit default)

### 3. **Redis Service** (`redis`)
- **Purpose**: Message queue and inter-service communication
- **Functions**:
  - Event publishing/subscribing
  - Service status tracking
  - Real-time notifications between services

### 4. **Shared Storage** (`shared-data-pvc`)
- **Purpose**: Persistent storage for CSV data files
- **Type**: PersistentVolumeClaim (PVC)
- **Access Mode**: ReadWriteOnce (RWO) - **Important limitation**
- **Mount Path**: `/shared/data` in all services

## 📁 YAML Configuration Files

### Required OpenShift YAML Files

#### 1. **Namespace Configuration**
```yaml
# k8s-microservices/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: data-pipeline-microservices
  labels:
    name: data-pipeline-microservices
```

#### 2. **Persistent Volume Claim (Shared Storage)**
```yaml
# k8s-microservices/shared-data-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
  namespace: data-pipeline-microservices
spec:
  accessModes:
    - ReadWriteOnce  # ⚠️ Only one pod can mount at a time
  resources:
    requests:
      storage: 10Gi  # 10GB storage allocation
  storageClassName: standard  # OpenShift default storage class
```

#### 3. **Configuration Map (Environment Variables)**
```yaml
# k8s-microservices/pipeline-config.yaml
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

#### 4. **Finnhub API Credentials (Secret)**
```yaml
# k8s-microservices/finnhub-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: finnhub-credentials
  namespace: data-pipeline-microservices
type: Opaque
stringData:
  FINNHUB_API_KEY: "your-actual-api-key-here"
```

#### 5. **Redis Deployment**
```yaml
# k8s-microservices/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: data-pipeline-microservices
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
        tier: backend
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: data-pipeline-microservices
spec:
  selector:
    app: redis
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
```

#### 6. **Data Ingest Deployment**
```yaml
# k8s-microservices/data-ingest-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-ingest
  namespace: data-pipeline-microservices
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-ingest
  template:
    metadata:
      labels:
        app: data-ingest
        tier: backend
    spec:
      containers:
      - name: data-ingest
        image: docker.io/vikke82/data-ingest:stock-v1.0
        env:
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: REDIS_HOST
        - name: REDIS_PORT
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: REDIS_PORT
        - name: SHARED_DATA_PATH
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: SHARED_DATA_PATH
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: LOG_LEVEL
        - name: FINNHUB_API_KEY
          valueFrom:
            secretKeyRef:
              name: finnhub-credentials
              key: FINNHUB_API_KEY
        - name: STOCK_SYMBOLS
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: STOCK_SYMBOLS
        volumeMounts:
        - name: shared-data
          mountPath: /shared/data
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "100m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import redis; r = redis.Redis(host='redis-service'); r.ping(); print('OK')"
          initialDelaySeconds: 30
          periodSeconds: 15
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data-pvc
```

#### 7. **Data Visualization Deployment**
```yaml
# k8s-microservices/data-visualization-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-visualization
  namespace: data-pipeline-microservices
spec:
  replicas: 1
  selector:
    matchLabels:
      app: data-visualization
  template:
    metadata:
      labels:
        app: data-visualization
        tier: frontend
    spec:
      containers:
      - name: data-visualization
        image: docker.io/vikke82/data-visualization:stock-v1.0
        ports:
        - containerPort: 8501  # Streamlit default port
        env:
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: REDIS_HOST
        - name: REDIS_PORT
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: REDIS_PORT
        - name: SHARED_DATA_PATH
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: SHARED_DATA_PATH
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: LOG_LEVEL
        volumeMounts:
        - name: shared-data
          mountPath: /shared/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: data-visualization-service
  namespace: data-pipeline-microservices
spec:
  selector:
    app: data-visualization
  ports:
    - protocol: TCP
      port: 8501
      targetPort: 8501
      name: streamlit
```

#### 8. **Route Configuration (External Access)**
```yaml
# k8s-microservices/data-visualization-route.yaml
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
    targetPort: streamlit
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

## 💾 Shared Volume Deep Dive

### **How Shared Volume Works**

The shared volume is implemented using a **PersistentVolumeClaim (PVC)** with the following characteristics:

#### **Volume Configuration**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
spec:
  accessModes:
    - ReadWriteOnce  # ⚠️ Critical limitation
  resources:
    requests:
      storage: 10Gi
```

#### **Key Properties**
- **Storage Class**: `standard` (OpenShift default)
- **Access Mode**: `ReadWriteOnce` (RWO)
- **Capacity**: 10GB
- **Mount Path**: `/shared/data` in containers
- **File System**: Standard Linux file system

#### **🚨 ReadWriteOnce Limitation**
The `ReadWriteOnce` access mode means:
- ✅ **Can be mounted**: By only ONE pod at a time
- ❌ **Cannot be shared**: Between multiple running pods simultaneously
- ⚠️ **Multi-Attach Error**: Occurs when multiple pods try to mount the same volume

### **Why This Limitation Exists**

1. **Storage Backend**: Many storage systems don't support concurrent access
2. **Data Consistency**: Prevents file corruption from simultaneous writes
3. **OpenShift Default**: Standard storage class uses RWO for reliability

### **Current Impact**
- **Data Ingest** and **Data Visualization** services cannot run simultaneously
- Must scale one service to 0 replicas before starting the other
- Manual orchestration required for service switching

### **Production Solutions**

#### **Option 1: ReadWriteMany (RWX) Storage**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc-rwx
spec:
  accessModes:
    - ReadWriteMany  # ✅ Multiple pods can mount
  resources:
    requests:
      storage: 10Gi
  storageClassName: "nfs-storage"  # Requires NFS or similar
```

#### **Option 2: Separate Volumes**
```yaml
# Separate PVC for each service
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-ingest-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-visualization-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

#### **Option 3: Object Storage (S3/MinIO)**
Replace shared volumes with object storage:
- AWS S3, Google Cloud Storage, or MinIO
- Services read/write directly to object storage
- No volume mounting limitations
- Better for cloud-native architectures

## 🚀 Deployment Process

### **Step 1: Deploy Infrastructure**
```bash
# Create namespace
oc apply -f k8s-microservices/namespace.yaml

# Create shared storage
oc apply -f k8s-microservices/shared-data-pvc.yaml

# Deploy configuration
oc apply -f k8s-microservices/pipeline-config.yaml
oc apply -f k8s-microservices/finnhub-config.yaml
```

### **Step 2: Deploy Services**
```bash
# Deploy Redis (message queue)
oc apply -f k8s-microservices/redis-deployment.yaml

# Deploy data ingestion
oc apply -f k8s-microservices/data-ingest-deployment.yaml

# Deploy visualization (scale ingest to 0 first)
oc scale deployment data-ingest --replicas=0 -n data-pipeline-microservices
oc apply -f k8s-microservices/data-visualization-deployment.yaml

# Create external access route
oc apply -f k8s-microservices/data-visualization-route.yaml
```

### **Step 3: Verify Deployment**
```bash
# Check all resources
oc get all -n data-pipeline-microservices

# Check persistent volumes
oc get pvc -n data-pipeline-microservices

# Check pod logs
oc logs -l app=data-visualization -n data-pipeline-microservices

# Get external URL
oc get route data-visualization-route -n data-pipeline-microservices
```

## 🔄 Service Communication Flow

```
1. Data Ingest Service starts
   ↓
2. Fetches stock data from Finnhub API
   ↓
3. Processes and saves CSV files to shared volume
   ↓
4. Publishes event to Redis: "data_ingested"
   ↓
5. Data Visualization Service (if running) receives event
   ↓
6. Reads new CSV files from shared volume
   ↓
7. Updates dashboard with fresh data
   ↓
8. Users access dashboard via OpenShift Route
```

## 📊 Data Flow Architecture

### **CSV File Types Generated**
The data-ingest service creates these files in `/shared/data/`:

1. **`stock_quotes_YYYYMMDD_HHMMSS.csv`** - Real-time prices
2. **`stock_historical_YYYYMMDD_HHMMSS.csv`** - Historical price data
3. **`company_profiles_YYYYMMDD_HHMMSS.csv`** - Company information
4. **`company_news_YYYYMMDD_HHMMSS.csv`** - Recent news articles
5. **`earnings_YYYYMMDD_HHMMSS.csv`** - Quarterly earnings
6. **`financials_YYYYMMDD_HHMMSS.csv`** - Financial statements
7. **`insider_transactions_YYYYMMDD_HHMMSS.csv`** - Insider trading
8. **`analyst_recommendations_YYYYMMDD_HHMMSS.csv`** - Buy/sell ratings
9. **`social_sentiment_YYYYMMDD_HHMMSS.csv`** - Social media sentiment
10. **`dividends_YYYYMMDD_HHMMSS.csv`** - Dividend history
11. **`market_news_YYYYMMDD_HHMMSS.csv`** - General market news
12. **`ipo_calendar_YYYYMMDD_HHMMSS.csv`** - Upcoming IPOs

### **File Access Pattern**
```
┌─────────────────┐    Write CSV files    ┌─────────────────┐
│  Data Ingest    ├────────────────────► │  Shared Volume  │
│    Service      │                       │   /shared/data  │
└─────────────────┘                       └─────────────────┘
                                                    │
                                           Read CSV files
                                                    ▼
                                          ┌─────────────────┐
                                          │ Data Visualiza- │
                                          │  tion Service   │
                                          └─────────────────┘
```

## 🔐 Security Considerations

### **Secrets Management**
- **Finnhub API Key**: Stored in Kubernetes Secret
- **Redis**: No authentication (internal network only)
- **TLS**: Enabled on external route with edge termination

### **Network Security**
- **Internal Services**: Cluster-internal communication only
- **External Access**: Only visualization dashboard exposed via Route
- **Port Isolation**: Services only expose necessary ports

### **Resource Limits**
- **Memory**: Defined limits prevent resource exhaustion
- **CPU**: Throttling prevents single service monopolization
- **Storage**: PVC limits prevent unbounded growth

## 🐛 Common Issues & Troubleshooting

### **1. Multi-Attach Volume Error**
```
Warning  FailedAttachVolume  Multi-Attach error for volume
```
**Solution**: Scale down conflicting pods before starting new ones

### **2. Pod Stuck in ContainerCreating**
**Check**: Volume attachment issues, storage availability

### **3. API Rate Limiting**
**Symptom**: 403 Forbidden errors from Finnhub API
**Solution**: Increase delay between API calls, check API key limits

### **4. Dashboard Not Loading**
**Check**: Route configuration, service ports, pod readiness

## 💡 Future Improvements

### **Infrastructure**
- Implement ReadWriteMany storage for concurrent access
- Add horizontal pod autoscaling
- Implement proper service mesh (Istio)
- Add monitoring with Prometheus/Grafana

### **Application**
- Add data cleaning service back
- Implement real-time streaming with Kafka
- Add machine learning predictions
- Implement proper error handling and retries

This comprehensive guide covers all aspects of the stock market data pipeline infrastructure, from YAML configurations to shared volume mechanics and deployment processes.