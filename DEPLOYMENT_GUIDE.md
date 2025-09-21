# Stock Market Data Pipeline - Complete Deployment Guide

This guide provides comprehensive step-by-step instructions for deploying the Stock Market Data Analysis Pipeline to CSC Rahti (OpenShift).

## 📋 Prerequisites Checklist

Before starting, ensure you have:

### **Required Accounts & Access**
- ✅ **GitHub Account** - To fork and clone the repository
- ✅ **CSC Account** - Finnish academic/research account
- ✅ **CSC Rahti Access** - OpenShift container platform access
- ✅ **Finnhub Account** - Free API account for stock market data

### **Required Tools**
- ✅ **Git** - Version control system
- ✅ **OpenShift CLI (oc)** - Command line interface for OpenShift
- ✅ **Web Browser** - For accessing dashboards and registration
- ✅ **Text Editor** - For configuration file editing

### **Knowledge Requirements**
- 🔧 Basic command line usage
- 🔧 Basic understanding of containers and Kubernetes
- 🔧 Basic YAML file editing

---

## 🚀 Complete Deployment Process

### **Phase 1: Environment Setup**

#### **Step 1.1: Get Finnhub API Key**

1. **Visit Finnhub Registration**:
   ```
   https://finnhub.io/register
   ```

2. **Create Account**:
   - Enter your email address
   - Create a secure password
   - Verify your email

3. **Access Dashboard**:
   - Log into your Finnhub account
   - Navigate to **Dashboard**
   - Click on **API Keys**

4. **Copy Your API Key**:
   - Copy the API key (format: `abcd1234efgh5678ijkl`)
   - **Keep it secure** - you'll need it later
   - ⚠️ **Do not share or commit this key to Git**

#### **Step 1.2: Install OpenShift CLI**

**For Windows (PowerShell):**
```powershell
# Download latest oc CLI
Invoke-WebRequest -Uri "https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-windows.zip" -OutFile "oc.zip"

# Extract and add to PATH
Expand-Archive -Path "oc.zip" -DestinationPath "C:\OpenShift"
$env:PATH += ";C:\OpenShift"

# Verify installation
oc version
```

**For macOS:**
```bash
# Using Homebrew
brew install openshift-cli

# Or download directly
curl -LO https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-mac.tar.gz
tar -xzf openshift-client-mac.tar.gz
sudo mv oc /usr/local/bin/
```

**For Linux:**
```bash
# Download and install
curl -LO https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz
tar -xzf openshift-client-linux.tar.gz
sudo mv oc /usr/local/bin/
```

#### **Step 1.3: Access CSC Rahti**

1. **Visit CSC Rahti**:
   ```
   https://rahti.csc.fi/
   ```

2. **Log In with CSC Account**:
   - Click **"Log in with CSC Account"**
   - Use your CSC username and password
   - Complete 2FA if enabled

3. **Login via Command Line**:
   ```bash
   oc login https://rahti.csc.fi:8443
   ```
   - Enter your CSC credentials when prompted
   - Accept any security warnings

4. **Verify Connection**:
   ```bash
   oc whoami
   oc get projects
   ```

---

### **Phase 2: Repository Setup**

#### **Step 2.1: Fork the Repository**

1. **Visit Original Repository**:
   ```
   https://github.com/Vikke82/data-analysis-pipeline-microservices
   ```

2. **Fork the Repository**:
   - Click the **"Fork"** button (top-right)
   - Select your GitHub account as destination
   - Wait for fork creation to complete

3. **Verify Fork Creation**:
   - You should now have: `https://github.com/YOUR-USERNAME/data-analysis-pipeline-microservices`

#### **Step 2.2: Clone Your Fork**

```bash
# Clone your forked repository
git clone https://github.com/YOUR-USERNAME/data-analysis-pipeline-microservices.git

# Navigate to project directory
cd data-analysis-pipeline-microservices

# Verify repository structure
ls -la
```

**Expected Output:**
```
data-analysis-pipeline-microservices/
├── data-ingest/              # Stock data fetching service
├── data-clean/               # Data processing service
├── data-visualization/       # Streamlit dashboard
├── k8s-microservices/       # Kubernetes YAML configurations
├── scripts/                 # Deployment automation scripts
├── docs/                    # Documentation
├── README.md               # Main documentation
└── INFRASTRUCTURE_GUIDE.md # Infrastructure details
```

---

### **Phase 3: OpenShift Project Setup**

#### **Step 3.1: Create OpenShift Project**

```bash
# Create new project (replace YOUR-NAME with your actual name/identifier)
oc new-project stock-pipeline-$(whoami) --display-name="Stock Market Pipeline - $(whoami)"

# Verify project creation
oc project
oc get all
```

**Expected Output:**
```
Using project "stock-pipeline-yourname" on server "https://rahti.csc.fi:8443".
No resources found in stock-pipeline-yourname namespace.
```

#### **Step 3.2: Configure Resource Quotas (If Needed)**

```bash
# Check current quotas
oc describe quota

# If you need to request more resources, contact CSC support
# Typical requirements:
# - CPU: 2 cores
# - Memory: 4Gi
# - Storage: 10Gi
```

---

### **Phase 4: Configuration Setup**

#### **Step 4.1: Configure Finnhub API Key**

```bash
# Navigate to Kubernetes configurations
cd k8s-microservices

# Edit Finnhub configuration
nano finnhub-config.yaml
# or use your preferred editor:
# vim finnhub-config.yaml
# code finnhub-config.yaml
```

**Update the following in `finnhub-config.yaml`:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: finnhub-credentials
  namespace: stock-pipeline-yourname  # Update with your project name
type: Opaque
stringData:
  FINNHUB_API_KEY: "your-actual-finnhub-api-key-here"  # Replace with your API key
```

**⚠️ Important Security Notes:**
- Replace `your-actual-finnhub-api-key-here` with your real API key
- Replace `stock-pipeline-yourname` with your actual project name
- Never commit the API key to version control

#### **Step 4.2: Update Project Namespace References**

If your project name is different, update namespace references in all YAML files:

```bash
# Find all namespace references
grep -r "namespace:" *.yaml

# Update each file to match your project name
sed -i 's/data-pipeline-microservices/stock-pipeline-yourname/g' *.yaml
```

---

### **Phase 5: Infrastructure Deployment**

#### **Step 5.1: Deploy Storage Infrastructure**

```bash
# Deploy persistent volume claim for shared data storage
oc apply -f persistent-volume.yaml

# Verify PVC creation
oc get pvc
```

**Expected Output:**
```
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
shared-data-pvc   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   10Gi       RWO            standard       10s
```

#### **Step 5.2: Deploy Redis Message Queue**

```bash
# Deploy Redis service
oc apply -f redis-deployment.yaml

# Wait for Redis to start
oc get pods -w
# Press Ctrl+C when Redis pod shows "Running"

# Verify Redis deployment
oc get all -l app=redis
```

**Expected Output:**
```
NAME                         READY   STATUS    RESTARTS   AGE
pod/redis-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

NAME                    TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/redis-service   ClusterIP   172.30.xx.xx   <none>        6379/TCP   30s
```

#### **Step 5.3: Deploy API Credentials**

```bash
# Deploy Finnhub API credentials
oc apply -f finnhub-config.yaml

# Verify secret creation
oc get secrets finnhub-credentials
```

**Expected Output:**
```
NAME                  TYPE     DATA   AGE
finnhub-credentials   Opaque   1      5s
```

---

### **Phase 6: Application Services Deployment**

#### **Step 6.1: Deploy Data Ingestion Service**

```bash
# Deploy stock data ingestion service
oc apply -f data-ingest-deployment.yaml

# Monitor deployment
oc get pods -l app=data-ingest -w
# Wait until pod shows "Running" status
```

**Verify Data Ingestion:**
```bash
# Check pod logs
oc logs -l app=data-ingest --tail=20

# Look for successful API connections:
# "Successfully connected to Redis"
# "Finnhub API: Live API key configured"
# "Starting stock data fetch from Finnhub API"
```

#### **Step 6.2: Deploy Data Visualization Service**

**⚠️ Important: Volume Limitation**

Due to ReadWriteOnce volume limitation, only one service can access the shared volume at a time.

```bash
# Scale down data-ingest temporarily
oc scale deployment data-ingest --replicas=0

# Deploy visualization service
oc apply -f data-visualization-deployment.yaml

# Wait for deployment
oc get pods -l app=data-visualization -w
```

#### **Step 6.3: Create External Access Route**

```bash
# Create external route for dashboard access
oc expose service data-visualization-service --name=stock-dashboard

# Get the external URL
oc get routes stock-dashboard
```

**Expected Output:**
```
NAME              HOST/PORT                                                PATH   SERVICES                     PORT        TERMINATION     WILDCARD
stock-dashboard   stock-dashboard-stock-pipeline-yourname.rahtiapp.fi            data-visualization-service   streamlit   edge/Redirect   None
```

#### **Step 6.4: Enable HTTPS (Recommended)**

```bash
# Create secure route with TLS
oc create route edge stock-dashboard-secure \
  --service=data-visualization-service \
  --port=8501

# Get secure URL
oc get routes stock-dashboard-secure
```

---

### **Phase 7: Optional Data Processing Service**

```bash
# Scale down visualization to deploy data cleaning
oc scale deployment data-visualization --replicas=0

# Deploy data cleaning service
oc apply -f data-clean-deployment.yaml

# Wait for deployment
oc get pods -l app=data-clean -w
```

---

## ✅ Verification & Testing

### **Step 7.1: Verify All Components**

```bash
# Check all pods are running
oc get pods

# Expected output (note: only one data service due to volume limitation):
# NAME                                  READY   STATUS    RESTARTS   AGE
# data-visualization-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
# redis-xxxxxxxxxx-xxxxx                1/1     Running   0          10m
```

### **Step 7.2: Test Service Communication**

```bash
# Test Redis connectivity
oc exec deployment/redis -- redis-cli ping
# Expected: PONG

# Check service endpoints
oc get endpoints
```

### **Step 7.3: Verify Data Generation**

```bash
# Scale up data-ingest temporarily to generate data
oc scale deployment data-visualization --replicas=0
oc scale deployment data-ingest --replicas=1

# Wait for data ingestion
sleep 60

# Check generated data files
oc exec deployment/data-ingest -- ls -la /shared/data/

# Look for files like:
# stock_quotes_YYYYMMDD_HHMMSS.csv
# company_profiles_YYYYMMDD_HHMMSS.csv
```

### **Step 7.4: Access Web Dashboard**

1. **Get Dashboard URL**:
   ```bash
   oc get routes stock-dashboard
   ```

2. **Open in Browser**:
   - Copy the HOST/PORT URL
   - Open in web browser
   - Add `https://` prefix if using secure route

3. **Verify Dashboard Features**:
   - ✅ Stock quotes display
   - ✅ Interactive charts load
   - ✅ Technical indicators show
   - ✅ Market overview works
   - ✅ No error messages

### **Step 7.5: Service Switching Process**

Due to volume limitations, use this process to switch between services:

**To Switch to Data Ingestion (Data Collection)**:
```bash
# Scale down visualization
oc scale deployment data-visualization --replicas=0

# Scale up data ingestion
oc scale deployment data-ingest --replicas=1

# Monitor data collection
oc logs -f deployment/data-ingest
```

**To Switch to Visualization (Dashboard Access)**:
```bash
# Scale down data ingestion
oc scale deployment data-ingest --replicas=0

# Scale up visualization
oc scale deployment data-visualization --replicas=1

# Access dashboard via route URL
```

---

## 🔧 Monitoring & Maintenance

### **Daily Operations**

```bash
# Check resource usage
oc top pods

# Monitor logs
oc logs -f deployment/data-visualization
oc logs -f deployment/data-ingest

# Check storage usage
oc exec deployment/data-ingest -- df -h /shared/data
```

### **Weekly Maintenance**

```bash
# Clean old data files (optional)
oc exec deployment/data-ingest -- find /shared/data -name "*.csv" -mtime +7 -delete

# Restart services for fresh data
oc rollout restart deployment/data-ingest
oc rollout restart deployment/data-visualization
```

### **Resource Monitoring**

```bash
# Check quota usage
oc describe quota

# Monitor pod health
oc get pods --watch

# Check persistent volume status
oc get pv,pvc
```

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ All pods show "Running" status
- ✅ Redis responds to ping commands
- ✅ Finnhub API key authentication works
- ✅ Data files are generated in shared storage
- ✅ Web dashboard loads without errors
- ✅ Stock charts display real data
- ✅ External route provides HTTPS access
- ✅ Services can be scaled up/down successfully

---

## 📱 Quick Reference Commands

### **Essential Commands**
```bash
# Login and project selection
oc login https://rahti.csc.fi:8443
oc project stock-pipeline-$(whoami)

# Check status
oc get all
oc get pods
oc get routes

# Service scaling
oc scale deployment data-ingest --replicas=1
oc scale deployment data-visualization --replicas=1

# Logs and debugging
oc logs -f deployment/SERVICE-NAME
oc describe pod POD-NAME
oc exec -it POD-NAME -- /bin/bash

# Clean restart
oc rollout restart deployment/SERVICE-NAME
```

### **Emergency Recovery**
```bash
# Delete and redeploy if something goes wrong
oc delete -f data-ingest-deployment.yaml
oc delete -f data-visualization-deployment.yaml
oc apply -f data-ingest-deployment.yaml
oc apply -f data-visualization-deployment.yaml
```

### **Complete Cleanup (if needed)**
```bash
# Remove all resources
oc delete all --all
oc delete pvc --all
oc delete secrets --all

# Delete project entirely
oc delete project stock-pipeline-$(whoami)
```

---

This comprehensive guide provides everything needed for successful deployment of the Stock Market Data Pipeline to CSC Rahti OpenShift platform.