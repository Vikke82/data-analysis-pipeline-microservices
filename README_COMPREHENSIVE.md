# Data Analysis Pipeline - Microservices Architecture

**A comprehensive educational project demonstrating the transformation from multi-container pods to microservices architecture using Kubernetes/OpenShift.**

## 📚 **For Students: Learning Objectives**

This project teaches you:
- **Microservices Architecture** - Understanding service decomposition and communication
- **Kubernetes/OpenShift** - Container orchestration and service management
- **Docker** - Containerization and image management
- **Service Discovery** - How services find and communicate with each other
- **Cloud Deployment** - Deploying to CSC Rahti (OpenShift)
- **Resource Management** - CPU, memory, and storage optimization

---

## 🏗️ **Application Structure & Components**

### **Architecture Overview**
This application transforms a data analysis pipeline from a **single pod with multiple containers** into a **microservices architecture** where each service runs in its own pod.

```
Original Architecture (Multi-Container Pod):
┌─────────────────────────────────────────────┐
│                Single Pod                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐ │
│  │  Redis  │ │Data-Ingest│ │Data-Clean    │ │
│  └─────────┘ └──────────┘ └──────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │        Data-Visualization              │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘

Microservices Architecture (Separate Pods):
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Redis Pod    │  │Data-Ingest  │  │Data-Clean   │  │Visualization│
│┌───────────┐│  │Pod          │  │Pod          │  │Pod          │
││  Redis    ││  │┌───────────┐│  │┌───────────┐│  │┌───────────┐│
││  Service  ││  ││Data-Ingest││  ││Data-Clean ││  ││Streamlit  ││
│└───────────┘│  │└───────────┘│  │└───────────┘│  ││Dashboard  ││
└─────────────┘  └─────────────┘  └─────────────┘  │└───────────┘│
                                                    └─────────────┘
        ↕                ↕                ↕                ↕
   Kubernetes Services (Internal Communication)
```

### **Service Descriptions**

#### **1. Redis Service** (`redis/`)
- **Purpose**: Message queue and coordination between services
- **Technology**: Redis 7-alpine
- **Role**: Pub/Sub messaging, data coordination, service communication
- **Port**: 6379
- **Dependencies**: None (base service)

#### **2. Data Ingest Service** (`data-ingest/`)
- **Purpose**: Downloads data files from CSC Allas object storage
- **Technology**: Python 3.11, SwiftService (OpenStack Swift client)
- **Key Features**:
  - Connects to CSC Allas using OpenStack Swift API
  - Downloads files based on scheduling or triggers
  - Publishes notifications via Redis when data is ready
- **Port**: 8080 (health checks)
- **Dependencies**: Redis service, CSC Allas credentials

#### **3. Data Clean Service** (`data-clean/`)
- **Purpose**: Processes and cleans raw data files
- **Technology**: Python 3.11, pandas, numpy
- **Key Features**:
  - Listens for data-ready events from Redis
  - Performs data cleaning, validation, and quality scoring
  - Processes CSV files and creates cleaned datasets
  - Publishes processed-data events via Redis
- **Port**: 8080 (health checks)
- **Dependencies**: Redis service, shared storage access

#### **4. Data Visualization Service** (`data-visualization/`)
- **Purpose**: Interactive web dashboard for data analysis
- **Technology**: Python 3.11, Streamlit, Plotly, pandas
- **Key Features**:
  - Web-based dashboard accessible via browser
  - Real-time data visualization and analytics
  - Service status monitoring and health checks
  - Interactive charts and data exploration
- **Port**: 8501 (Streamlit web interface)
- **Dependencies**: Redis service, processed data access
- **External Access**: Available via OpenShift Route

---

## 🌐 **Service Interfaces & Communication**

### **Internal Service Communication**
Services communicate using **Kubernetes Service Discovery** and **Redis Pub/Sub**:

```python
# Example: Services connect to Redis using Kubernetes DNS
REDIS_HOST = "redis-service"  # Kubernetes service name
REDIS_PORT = "6379"

# Redis connection in Python
import redis
r = redis.Redis(host='redis-service', port=6379, decode_responses=True)
```

### **API Endpoints**

#### **Data Ingest Service**
```
GET  /health          - Health check endpoint
POST /trigger-ingest  - Manually trigger data ingestion
GET  /status          - Service status and last run info
```

#### **Data Clean Service**  
```
GET  /health          - Health check endpoint
POST /trigger-clean   - Manually trigger data cleaning
GET  /stats           - Processing statistics and metrics
```

#### **Data Visualization Service**
```
GET  /                - Main Streamlit dashboard
GET  /healthz         - Health check for Kubernetes
```

### **Message Flow**
```
Data-Ingest → Redis → Data-Clean → Redis → Data-Visualization
     ↓           ↓         ↓           ↓            ↓
   "data-      "data-   "cleaning-  "data-    "update-
   available"  ready"   started"    processed" dashboard"
```

---

## 🍴 **How to Fork This Repository**

### **Step 1: Fork the Repository**
1. Go to the original repository: `https://github.com/your-username/data-analysis-pipeline-microservice`
2. Click the **"Fork"** button in the top-right corner
3. Select your GitHub account as the destination
4. Wait for the fork to be created

### **Step 2: Clone Your Fork**
```bash
# Clone your forked repository
git clone https://github.com/YOUR-USERNAME/data-analysis-pipeline-microservice.git

# Navigate to the project directory
cd data-analysis-pipeline-microservice

# Add the original repository as upstream (optional, for updates)
git remote add upstream https://github.com/original-username/data-analysis-pipeline-microservice.git
```

### **Step 3: Customize for Your Project**
```bash
# Create a new branch for your changes
git checkout -b my-implementation

# Make your changes...
# Then commit and push
git add .
git commit -m "Add my implementation"
git push origin my-implementation
```

---

## 🐳 **Manual Deployment Steps (Using Docker Hub)**

### **Prerequisites**
Before starting, ensure you have:
- Docker Desktop installed and running
- Docker Hub account created
- OpenShift CLI (`oc`) installed
- Access to CSC Rahti
- CSC Allas credentials

### **Step 1: Prepare Your Environment**

#### **1.1 Login to Docker Hub**
```powershell
docker login
# Enter your Docker Hub username and password
```

#### **1.2 Login to CSC Rahti**
```powershell
# Login via web browser (recommended)
oc login --web

# OR login with token
oc login https://api.2.rahti.csc.fi:6443 --token=YOUR_TOKEN
```

#### **1.3 Create OpenShift Project**
```powershell
# Create a new project (replace with your project details)
oc new-project my-data-pipeline --description="csc_project: 2012345"

# Verify you're in the correct project
oc project
```

### **Step 2: Build and Push Docker Images**

#### **2.1 Build All Images**
```powershell
# Build data-ingest service
docker build -t YOUR-DOCKERHUB-USERNAME/data-ingest:latest data-ingest/

# Build data-clean service  
docker build -t YOUR-DOCKERHUB-USERNAME/data-clean:latest data-clean/

# Build data-visualization service
docker build -t YOUR-DOCKERHUB-USERNAME/data-visualization:latest data-visualization/
```

#### **2.2 Push Images to Docker Hub**
```powershell
# Push all images
docker push YOUR-DOCKERHUB-USERNAME/data-ingest:latest
docker push YOUR-DOCKERHUB-USERNAME/data-clean:latest
docker push YOUR-DOCKERHUB-USERNAME/data-visualization:latest

# Verify images are available
docker images | findstr YOUR-DOCKERHUB-USERNAME
```

### **Step 3: Update Kubernetes Manifests**

#### **3.1 Update Image References**
Edit each deployment file in `k8s-microservices/` and replace:
```yaml
# Change this:
image: image-registry.rahti.csc.fi/your-project/service-name:latest

# To this:
image: docker.io/YOUR-DOCKERHUB-USERNAME/service-name:latest
```

**Files to update:**
- `k8s-microservices/data-ingest-deployment.yaml`
- `k8s-microservices/data-clean-deployment.yaml`  
- `k8s-microservices/data-visualization-deployment.yaml`

#### **3.2 Update Route Hostname (Optional)**
In `data-visualization-deployment.yaml`, you can customize the route:
```yaml
spec:
  host: my-pipeline-YOUR-PROJECT-NAME.2.rahtiapp.fi
```

### **Step 4: Create CSC Allas Secret**

#### **4.1 Choose Authentication Method**

**Option A: Username/Password**
```powershell
oc create secret generic allas-credentials \
  --from-literal=OS_USERNAME='your-csc-username' \
  --from-literal=OS_PASSWORD='your-csc-password' \
  --from-literal=OS_PROJECT_NAME='your-csc-project-name' \
  --from-literal=OS_USER_DOMAIN_NAME='Default' \
  --from-literal=OS_PROJECT_DOMAIN_ID='default' \
  --from-literal=OS_REGION_NAME='regionOne' \
  --from-literal=OS_INTERFACE='public' \
  --from-literal=OS_IDENTITY_API_VERSION='3' \
  --from-literal=OS_AUTH_URL='https://pouta.csc.fi:5001/v3'
```

**Option B: Application Credentials (Recommended)**
1. Visit https://pouta.csc.fi
2. Go to **Identity → Application Credentials**
3. Create new application credential
4. Use the generated ID and secret:

```powershell
oc create secret generic allas-credentials \
  --from-literal=OS_APPLICATION_CREDENTIAL_ID='your-app-credential-id' \
  --from-literal=OS_APPLICATION_CREDENTIAL_SECRET='your-app-credential-secret' \
  --from-literal=OS_AUTH_URL='https://pouta.csc.fi:5001/v3' \
  --from-literal=OS_AUTH_TYPE='v3applicationcredential'
```

### **Step 5: Deploy Services**

#### **5.1 Deploy in Correct Order**
```powershell
# 1. Deploy storage and configuration
oc apply -f k8s-microservices/persistent-volume.yaml

# 2. Deploy Redis (base dependency)
oc apply -f k8s-microservices/redis-deployment.yaml

# 3. Deploy application services
oc apply -f k8s-microservices/data-ingest-deployment.yaml
oc apply -f k8s-microservices/data-clean-deployment.yaml
oc apply -f k8s-microservices/data-visualization-deployment.yaml
```

#### **5.2 Verify Deployment**
```powershell
# Check all pods are running
oc get pods

# Check services are created
oc get services

# Check external route
oc get routes

# View logs if needed
oc logs deployment/data-visualization
```

### **Step 6: Access Your Application**

#### **6.1 Get Application URL**
```powershell
# Get the route URL
oc get routes
```

#### **6.2 Test Application**
1. Open the route URL in your browser
2. You should see the Streamlit dashboard
3. Check service status in the application
4. Verify data pipeline functionality

---

## 🛠️ **Troubleshooting Guide**

### **Common Issues**

#### **Pods Stuck in Pending**
```powershell
# Check resource quotas
oc describe quota

# Check resource limits in deployments
oc describe deployment/service-name
```

#### **Image Pull Errors**
```powershell
# Verify image exists on Docker Hub
docker pull YOUR-DOCKERHUB-USERNAME/service-name:latest

# Check if image name is correct in deployment
oc describe deployment/service-name
```

#### **Services Can't Communicate**
```powershell
# Check if services are running
oc get pods

# Test internal connectivity
oc exec -it pod-name -- nslookup redis-service

# Check Redis connectivity
oc exec -it pod-name -- ping redis-service
```

#### **Application Not Accessible**
```powershell
# Check route configuration
oc get routes

# Verify service is listening
oc port-forward deployment/data-visualization 8501:8501
# Then test: http://localhost:8501
```

### **Resource Optimization**

#### **Adjust CPU/Memory Limits**
If hitting resource quotas:
```yaml
resources:
  requests:
    cpu: 50m        # Minimum required by CSC Rahti
    memory: 128Mi   # Reduce if needed
  limits:
    cpu: 100m       # Reduce to fit quota
    memory: 256Mi   # Reduce if needed
```

#### **Scale Services**
```powershell
# Scale individual services
oc scale deployment/data-clean --replicas=2

# Set up auto-scaling
oc autoscale deployment/data-clean --min=1 --max=3 --cpu-percent=70
```

---

## 📊 **Monitoring & Observability**

### **Health Checks**
Each service includes health check endpoints:
```powershell
# Check pod health
oc get pods

# View detailed pod status
oc describe pod pod-name

# Check application logs
oc logs deployment/service-name

# Follow logs in real-time
oc logs -f deployment/service-name
```

### **Service Metrics**
```powershell
# Check resource usage
oc top pods

# Monitor events
oc get events --sort-by=.metadata.creationTimestamp

# Check service endpoints
oc get endpoints
```

---

## 🎓 **Learning Outcomes**

After completing this project, you will understand:

### **Microservices Concepts**
- **Service Decomposition**: How to break monoliths into services
- **Communication Patterns**: Sync vs async, pub/sub messaging
- **Data Management**: Shared vs service-owned data
- **Fault Tolerance**: Service isolation and failure handling

### **Kubernetes/OpenShift**
- **Pod Management**: Single vs multi-container pods
- **Service Discovery**: DNS-based service communication
- **Resource Management**: CPU, memory, storage quotas
- **Networking**: ClusterIP, NodePort, Routes
- **Configuration**: ConfigMaps, Secrets, Environment Variables

### **Cloud-Native Development**
- **Container Orchestration**: Deployment strategies
- **Scaling Patterns**: Horizontal and vertical scaling
- **Health Checks**: Liveness and readiness probes
- **Rolling Updates**: Zero-downtime deployments

### **DevOps Practices**
- **Infrastructure as Code**: YAML manifests
- **Container Registry**: Docker Hub integration
- **Monitoring**: Logs, metrics, health checks
- **Troubleshooting**: Debugging distributed systems

---

## 📁 **Project Structure**

```
data-analysis-pipeline-microservice/
├── data-ingest/                 # Data ingestion service
│   ├── Dockerfile              # Container definition
│   ├── requirements.txt        # Python dependencies
│   └── app.py                  # Main application code
├── data-clean/                  # Data cleaning service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── data-visualization/          # Streamlit dashboard
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── k8s-microservices/          # Kubernetes manifests
│   ├── redis-deployment.yaml          # Redis service deployment
│   ├── data-ingest-deployment.yaml    # Data ingest service
│   ├── data-clean-deployment.yaml     # Data cleaning service
│   ├── data-visualization-deployment.yaml  # Web dashboard
│   └── persistent-volume.yaml         # Shared storage
├── scripts/                    # Automation scripts
│   ├── build-and-push-microservices.ps1  # Build & push images
│   └── deploy-microservices.ps1           # Deploy all services
├── docs/                       # Documentation
│   ├── ARCHITECTURE_COMPARISON.md     # Architecture analysis
│   ├── DEPLOYMENT_GUIDE.md            # Detailed deployment guide
│   └── CREATE_ALLAS_SECRET.md         # Allas credentials setup
└── README.md                   # This file
```

---

## 🚀 **Quick Start (Automated)**

If you prefer automated deployment, use the provided scripts:

```powershell
# 1. Build and push Docker images
.\scripts\build-and-push-microservices.ps1

# 2. Deploy all services
.\scripts\deploy-microservices.ps1
```

---

## 📚 **Additional Resources**

### **Documentation**
- [CSC Rahti Documentation](https://docs.csc.fi/cloud/rahti/)
- [CSC Allas Documentation](https://docs.csc.fi/data/Allas/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OpenShift Documentation](https://docs.openshift.com/)

### **Tools**
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [OpenShift CLI](https://docs.openshift.com/container-platform/4.14/cli_reference/openshift_cli/getting-started-cli.html)
- [VS Code](https://code.visualstudio.com/) with Kubernetes extension

### **Learning Materials**
- [Microservices Patterns](https://microservices.io/patterns/)
- [Kubernetes Tutorials](https://kubernetes.io/docs/tutorials/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

If you encounter issues:
1. Check the [Troubleshooting Guide](#-troubleshooting-guide)
2. Review the application logs: `oc logs deployment/service-name`
3. Check the [Issues](https://github.com/your-username/repo/issues) page
4. Contact your course instructor

---

**Happy Learning! 🚀**