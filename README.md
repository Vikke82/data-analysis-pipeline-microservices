# Stock Market Data Analysis Pipeline - Microservices Architecture

**A comprehensive real-time stock market data pipeline demonstrating microservices architecture using Kubernetes/OpenShift and Finnhub API integration.**

## 📚 **For Students: Learning Objectives**

This project teaches you:
- **Microservices Architecture** - Service decomposition and inter-service communication
- **Real-time Financial Data Processing** - API integration and market data handling
- **Kubernetes/OpenShift** - Container orchestration and service management
- **Docker** - Containerization and image management
- **Technical Analysis** - Stock market indicators and financial metrics
- **Cloud Deployment** - Deploying to CSC Rahti (OpenShift)
- **Resource Management** - CPU, memory, and storage optimization

---

## 🎓 **Student Instructions: Fork, Clone & Deploy**

### **📋 Prerequisites**
Before starting, ensure you have:
- GitHub account
- CSC Rahti (OpenShift) access with project namespace
- Finnhub API key (free from https://finnhub.io/)
- Basic knowledge of Git, Docker, and Kubernetes concepts

### **🍴 Step 1: Fork This Repository**

1. **Visit the repository**: https://github.com/Vikke82/data-analysis-pipeline-microservices
2. **Click "Fork"** in the top-right corner
3. **Select your GitHub account** as the destination
4. **Wait for fork creation** - GitHub will create your personal copy

### **📥 Step 2: Clone Your Fork**

```bash
# Clone your forked repository
git clone https://github.com/YOUR-USERNAME/data-analysis-pipeline-microservices.git

# Navigate to the project directory
cd data-analysis-pipeline-microservices

# Verify the repository structure
ls -la
```

**Expected directory structure:**
```
data-analysis-pipeline-microservices/
├── data-ingest/              # Stock data fetching service
├── data-clean/               # Data processing service  
├── data-visualization/       # Streamlit dashboard
├── k8s-microservices/       # Kubernetes YAML files
├── docs/                    # Documentation
├── scripts/                 # Deployment scripts
├── INFRASTRUCTURE_GUIDE.md  # Complete infrastructure guide
└── README.md               # This file
```

### **🔑 Step 3: Get Finnhub API Key**

1. **Visit Finnhub**: https://finnhub.io/register
2. **Create free account** with your email
3. **Go to Dashboard** → **API Keys**
4. **Copy your API key** (format: `abcd1234efgh5678`)
5. **Keep it secure** - you'll need it for deployment

### **🚀 Step 4: Deploy to CSC Rahti (OpenShift)**

#### **4.1 Access CSC Rahti**
```bash
# Login to CSC Rahti OpenShift cluster
oc login https://rahti.csc.fi:8443

# Create your project namespace (replace YOUR-NAME with your name)
oc new-project stock-pipeline-YOUR-NAME --display-name="Stock Market Pipeline - YOUR-NAME"

# Verify you're in the right project
oc project
```

#### **4.2 Configure Finnhub API Key**
```bash
# Navigate to Kubernetes configurations
cd k8s-microservices

# Edit the Finnhub configuration file
# Replace 'your-api-key-here' with your actual API key
nano finnhub-config.yaml
```

**Update this section in `finnhub-config.yaml`:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: finnhub-credentials
  namespace: stock-pipeline-YOUR-NAME  # Update namespace
type: Opaque
stringData:
  FINNHUB_API_KEY: "your-actual-finnhub-api-key-here"  # Replace this
```

#### **4.3 Deploy Infrastructure Components**
```bash
# Deploy in the correct order:

# 1. Create persistent storage
oc apply -f persistent-volume.yaml

# 2. Deploy Redis message queue
oc apply -f redis-deployment.yaml

# 3. Configure API credentials
oc apply -f finnhub-config.yaml

# 4. Deploy data ingestion service
oc apply -f data-ingest-deployment.yaml

# 5. Deploy data visualization dashboard
oc apply -f data-visualization-deployment.yaml

# Optional: Deploy data cleaning service
oc apply -f data-clean-deployment.yaml
```

#### **4.4 Verify Deployment**
```bash
# Check all pods are running
oc get pods

# Expected output (may take 2-3 minutes):
# NAME                                  READY   STATUS    RESTARTS   AGE
# data-ingest-xxxxxxxxx-xxxxx          1/1     Running   0          2m
# data-visualization-xxxxxxxxx-xxxxx   1/1     Running   0          1m
# redis-xxxxxxxxx-xxxxx                1/1     Running   0          3m

# Check services
oc get services

# Check persistent volume claims
oc get pvc
```

#### **4.5 Create External Access Route**
```bash
# Create route for web dashboard access
oc expose service data-visualization-service --name=stock-dashboard-route

# Get the external URL
oc get routes

# Example output:
# NAME                   HOST/PORT                                    PATH   SERVICES
# stock-dashboard-route  stock-dashboard-route-stock-pipeline-YOUR-NAME.rahtiapp.fi...
```

### **🌐 Step 5: Access Your Application**

1. **Copy the route URL** from the previous step
2. **Open in browser**: `https://stock-dashboard-route-stock-pipeline-YOUR-NAME.rahtiapp.fi`
3. **Wait for data ingestion** (first run takes 1-2 minutes)
4. **Explore the dashboard**:
   - Real-time stock prices
   - Interactive candlestick charts  
   - Technical indicators (SMA, EMA, RSI, MACD)
   - Market overview and analysis

### **🐛 Troubleshooting Common Issues**

#### **Problem: Pods stuck in "ContainerCreating"**
```bash
# Check pod details
oc describe pod POD-NAME

# Common causes:
# - Image pull issues
# - Volume mounting problems
# - Resource constraints
```

#### **Problem: "Multi-Attach error for volume"**
```bash
# Only one pod can mount the shared volume at a time
# Scale down conflicting services:
oc scale deployment data-ingest --replicas=0
oc scale deployment data-visualization --replicas=1

# Or vice versa for data collection:
oc scale deployment data-visualization --replicas=0  
oc scale deployment data-ingest --replicas=1
```

#### **Problem: API key not working**
```bash
# Verify secret was created correctly
oc get secrets finnhub-credentials -o yaml

# Check pod logs for API errors
oc logs deployment/data-ingest
```

#### **Problem: Dashboard not loading**
```bash
# Check visualization pod logs
oc logs deployment/data-visualization

# Verify route is accessible
oc get routes

# Check service endpoints
oc get endpoints
```

### **📊 Understanding the Data Pipeline**

#### **Data Flow:**
```
1. Data-Ingest Pod → Fetches stock data from Finnhub API every 15 minutes
2. Saves data to shared persistent volume as CSV files
3. Data-Visualization Pod → Reads CSV files and displays interactive dashboard
4. Redis → Coordinates communication between services
```

#### **Generated Data Files:**
Your application creates these files in the shared storage:
- `stock_quotes_YYYYMMDD_HHMMSS.csv` - Real-time stock prices
- `stock_historical_YYYYMMDD_HHMMSS.csv` - Historical price data
- Technical analysis data with indicators

#### **Monitoring Your Application:**
```bash
# Check resource usage
oc top pods

# Monitor logs in real-time  
oc logs -f deployment/data-ingest
oc logs -f deployment/data-visualization

# Check service status
oc get all
```

### **💡 Learning Exercises**

1. **Modify Stock Symbols**: Edit the deployment YAML to track different stocks
2. **Adjust Resource Limits**: Experiment with CPU/memory limits in deployments  
3. **Add New Technical Indicators**: Extend the data processing logic
4. **Implement Alerts**: Add email/Slack notifications for significant price changes
5. **Scale Services**: Try horizontal pod autoscaling
6. **Add Monitoring**: Implement Prometheus metrics collection

### **📚 Additional Resources**

- **OpenShift Documentation**: https://docs.openshift.com/
- **CSC Rahti User Guide**: https://docs.csc.fi/cloud/rahti/
- **Finnhub API Documentation**: https://finnhub.io/docs/api
- **Kubernetes Concepts**: https://kubernetes.io/docs/concepts/
- **Streamlit Documentation**: https://docs.streamlit.io/

---

## 🏗️ **Application Structure & Components**

### **Architecture Overview**
This application implements a **real-time stock market data pipeline** using **microservices architecture** where each service runs in its own pod, processing financial data from the Finnhub API.

```
Stock Market Data Pipeline Architecture:

┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│Redis Pod    │  │Stock Data       │  │Stock Data       │  │Stock Market     │
│┌───────────┐│  │Ingest Pod       │  │Processing Pod   │  │Dashboard Pod    │
││  Redis    ││  │┌───────────────┐│  │┌───────────────┐│  │┌───────────────┐│
││  Service  ││◄─┤│Finnhub API    ││◄─┤│Technical      ││◄─┤│Real-time      ││
││(Coord.)   ││  ││Integration    ││  ││Indicators     ││  ││Stock Charts   ││
│└───────────┘│  │└───────────────┘│  │└───────────────┘│  ││& Analysis     ││
└─────────────┘  └─────────────────┘  └─────────────────┘  │└───────────────┘│
                          │                       │         └─────────────────┘
                          ▼                       ▼
                 ┌─────────────────┐    ┌─────────────────┐
                 │Real-time Quotes │    │Historical Data  │
                 │+ Market Sentiment│    │+ Tech Indicators│
                 └─────────────────┘    └─────────────────┘
```

### **Service Descriptions**

#### **1. Redis Service** (`redis/`)
- **Purpose**: Message queue and coordination between stock data services
- **Technology**: Redis 7-alpine
- **Role**: Pub/Sub messaging, data coordination, service communication
- **Port**: 6379
- **Dependencies**: None (base service)

#### **2. Stock Data Ingest Service** (`data-ingest/`)
- **Purpose**: Fetches real-time stock data from Finnhub API
- **Technology**: Python 3.11, Finnhub API, requests
- **Key Features**:
  - Real-time stock quotes and market data
  - Historical stock data (30-day lookback)
  - Configurable stock symbols (AAPL, GOOGL, MSFT, etc.)
  - Rate-limited API calls with error handling
  - Publishes data-ready notifications via Redis
- **Port**: 8080 (health checks)
- **Dependencies**: Redis service, Finnhub API key

#### **3. Stock Data Processing Service** (`data-clean/`)
- **Purpose**: Processes stock data and calculates technical indicators
- **Technology**: Python 3.11, pandas, numpy, TA-Lib
- **Key Features**:
  - Technical indicators: SMA, EMA, MACD, RSI, Bollinger Bands
  - Market sentiment analysis and volatility calculations
  - Data quality scoring and validation
  - Stock performance metrics and daily returns
  - Publishes processed-data events via Redis
- **Port**: 8080 (health checks)
- **Dependencies**: Redis service, shared storage access

#### **4. Stock Market Dashboard Service** (`data-visualization/`)
- **Purpose**: Interactive stock market dashboard and analytics
- **Technology**: Python 3.11, Streamlit, Plotly, pandas
- **Key Features**:
  - Real-time stock price charts with candlestick plots
  - Technical indicator overlays (moving averages, Bollinger Bands)
  - Market overview with sentiment analysis
  - Individual stock analysis and performance metrics
  - RSI, MACD, and volatility indicators
  - Service status monitoring and health checks
- **Port**: 8501 (Streamlit web interface)
- **Dependencies**: Redis service, processed stock data access
- **External Access**: Available via OpenShift Route

---

## 🌐 **Service Interfaces & Communication**

### **Internal Service Communication**
Services communicate using **Kubernetes Service Discovery** and **Redis Pub/Sub**:

```python
# Example: Services connect to Redis using Kubernetes DNS
REDIS_HOST = "redis-service"  # Kubernetes service name
REDIS_PORT = "6379"

# Redis connection for stock data coordination
import redis
r = redis.Redis(host='redis-service', port=6379, decode_responses=True)

# Stock data pipeline events
r.publish('stock_data_pipeline', {
    'event': 'data_ingested',
    'symbols': ['AAPL', 'GOOGL', 'MSFT'],
    'timestamp': datetime.now().isoformat()
})
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

## 🎓 **For Instructors: Classroom Use**

### **Course Integration**
This project is designed for **Cloud Computing**, **Software Architecture**, and **DevOps** courses. It covers:

**Week-by-Week Learning Path:**
- **Week 1-2**: Docker containerization and microservices concepts
- **Week 3-4**: Kubernetes/OpenShift deployment and service management
- **Week 5-6**: API integration and real-time data processing
- **Week 7-8**: Monitoring, scaling, and troubleshooting

**Assessment Opportunities:**
- **Lab Assignment**: Deploy and customize the pipeline
- **Project Extension**: Add new data sources or technical indicators
- **Architecture Analysis**: Compare monolithic vs. microservices approaches
- **Performance Tuning**: Optimize resource usage and scaling

### **Student Assignment Ideas**
1. **Extend Data Sources**: Add cryptocurrency or forex data APIs
2. **Implement Alerting**: Email/Slack notifications for price thresholds
3. **Add Machine Learning**: Stock price prediction models
4. **Performance Monitoring**: Prometheus + Grafana integration
5. **Security Enhancement**: Add authentication and HTTPS
6. **Multi-Region Deployment**: Deploy across multiple CSC Rahti regions

### **Grading Rubric Suggestions**
- **Deployment (25%)**: Successfully deploy all services
- **Customization (25%)**: Modify configurations and add features  
- **Documentation (20%)**: Document changes and architecture decisions
- **Troubleshooting (15%)**: Demonstrate problem-solving skills
- **Presentation (15%)**: Explain architecture and design choices

## 🤝 **Contributing**

We welcome contributions from students and instructors! Here's how to contribute:

### **For Students**
1. **Fork the repository** to your GitHub account
2. **Create a feature branch**: `git checkout -b feature/your-enhancement`
3. **Make your changes** and commit with clear messages
4. **Test thoroughly** in your CSC Rahti environment
5. **Submit a Pull Request** with detailed description

**Contribution Ideas:**
- Fix bugs or improve error handling
- Add new technical indicators
- Improve dashboard UI/UX
- Add unit tests
- Enhance documentation
- Optimize Docker images
- Add new data visualization types

### **For Instructors**
- Submit course material suggestions
- Share assignment ideas and rubrics
- Report issues or propose improvements
- Contribute learning exercises
- Add deployment guides for other cloud platforms

### **Development Setup**
```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/data-analysis-pipeline-microservices.git
cd data-analysis-pipeline-microservices

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r data-ingest/requirements.txt
pip install -r data-visualization/requirements.txt

# Run services locally for development
cd data-ingest && python app.py
cd data-visualization && streamlit run app.py
```

### **Pull Request Guidelines**
- Provide clear description of changes
- Include screenshots for UI changes
- Test deployment on CSC Rahti
- Update documentation as needed
- Follow Python PEP 8 style guidelines
- Add comments for complex logic

## 📖 **Educational Resources**

### **Recommended Reading**
- **"Microservices Patterns"** by Chris Richardson
- **"Kubernetes in Action"** by Marko Lukša  
- **"Docker Deep Dive"** by Nigel Poulton
- **CSC Rahti Documentation**: https://docs.csc.fi/cloud/rahti/

### **Online Courses**
- **Kubernetes Basics** (Kubernetes Academy)
- **Docker Essentials** (Docker Hub)
- **OpenShift for Developers** (Red Hat Learning)
- **Python for Finance** (Coursera)

### **Hands-On Labs**
- **Katacoda OpenShift Scenarios**: https://learn.openshift.com/
- **Kubernetes by Example**: https://kubernetesbyexample.com/
- **Docker Labs**: https://labs.play-with-docker.com/

## 🏆 **Success Stories**

Students have successfully:
- **Extended the pipeline** with cryptocurrency data
- **Implemented machine learning** price prediction models
- **Added monitoring** with Prometheus and Grafana
- **Created mobile dashboards** using React Native
- **Built CI/CD pipelines** with GitHub Actions
- **Deployed to multiple clouds** (AWS, Azure, GCP)

## 📞 **Support Channels**

### **For Students**
1. **GitHub Issues**: Report bugs and ask technical questions
2. **Course Forum**: Discuss with classmates and instructors
3. **Office Hours**: Meet with instructors for personalized help
4. **Study Groups**: Form teams for collaborative learning

### **For Instructors**  
1. **Instructor Portal**: Access teaching materials and guides
2. **Community Forum**: Connect with other educators
3. **Email Support**: Direct contact for course integration
4. **Webinars**: Monthly sessions on microservices education

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