# Data Analysis Pipeline - Microservices Architecture

A comprehensive containerized data analysis pipeline designed for ingesting, processing, and visualizing data from CSC Allas object storage. This version implements a **true microservices architecture** where each service runs in its own separate pod, enabling independent scaling, better resource isolation, and more granular monitoring.

**🎓 Educational Project**: This repository demonstrates the difference between multi-container pods and microservices architecture for students learning cloud services, containerization, and data analysis pipelines.

## 🏗️ Architecture Overview

### **📦 Microservices Architecture**

Unlike the original multi-container pod design, this implementation uses separate pods for each service:

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Redis Pod     │  Data Ingest Pod│    Data Clean Pod       │
│   Port: 6379    │   Service       │      Service            │
│                 │                 │                         │
├─────────────────┴─────────────────┴─────────────────────────┤
│              Data Visualization Pod                         │
│                 (Streamlit Web App)                         │
├─────────────────────────────────────────────────────────────┤
│          Shared PersistentVolume: /shared/data              │
│   • raw_data.csv        • cleaned_data.csv                  │
│   • summary_report.json • quality_metrics.json             │
└─────────────────────────────────────────────────────────────┘
```

### **🔄 Data Flow**

1. **Data Ingest Service** downloads raw data from CSC Allas
2. **Redis Service** coordinates processing status between services
3. **Data Clean Service** processes raw files and creates cleaned datasets
4. **Visualization Service** provides interactive dashboard access
5. **Persistent Volume** enables data sharing between all services

### **🎯 Key Benefits of Microservices Architecture**

#### **✅ Advantages over Multi-Container Pods:**

1. **Independent Scaling**: Scale each service separately based on workload
2. **Service Isolation**: Failures in one service don't affect others
3. **Resource Optimization**: Allocate resources per service needs
4. **Independent Updates**: Deploy service updates without affecting others
5. **Better Monitoring**: Monitor each service independently
6. **Flexibility**: Different restart policies and configuration per service
7. **Technology Diversity**: Each service can use different base images/versions

#### **🔄 Trade-offs:**

- **Network Overhead**: Services communicate over network instead of localhost
- **Complexity**: More configuration files and service discovery setup
- **Storage**: Requires shared persistent volumes for data exchange
- **Debugging**: More complex troubleshooting across distributed services

## 📚 Architecture Comparison

### Multi-Container Pod vs. Microservices

| Aspect | Multi-Container Pod | Microservices |
|--------|-------------------|---------------|
| **Scaling** | All containers scale together | Each service scales independently |
| **Resource Usage** | Shared resources within pod | Dedicated resources per service |
| **Network** | `localhost` communication | Service discovery + DNS |
| **Failures** | Pod failure affects all services | Service isolation |
| **Updates** | All containers updated together | Independent service updates |
| **Complexity** | Lower (single pod) | Higher (multiple services) |
| **Monitoring** | Pod-level monitoring | Service-level monitoring |

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenShift CLI (oc) installed and configured
- CSC Allas account with API credentials
- Access to OpenShift/Kubernetes cluster (CSC Rahti)

### Step 1: Clone and Setup

```powershell
git clone <your-fork-of-this-repo>
cd "Data Analysis pipeline microservice"
```

### Step 2: Configure CSC Allas Credentials

```powershell
# Interactive credential management
.\scripts\manage-allas-credentials-microservices.ps1

# Choose option 1 (Create new credentials) or 5 (Application credentials - recommended)
```

### Step 3: Build and Push Container Images

```powershell
# Build all service images and push to registry
.\scripts\build-and-push-microservices.ps1

# Follow prompts to select registry (CSC Rahti recommended)
```

### Step 4: Deploy to OpenShift

```powershell
# Deploy all microservices
.\scripts\deploy-microservices.ps1

# Monitor deployment progress
oc get pods -w
```

### Step 5: Access Your Dashboard

```powershell
# Get the dashboard URL
oc get routes

# Your dashboard will be available at: https://data-visualization-route-PROJECT.2.rahtiapp.fi
```

## 📋 Detailed Setup

### Service Architecture Details

#### 1. Redis Service (`redis-deployment.yaml`)
- **Purpose**: Coordinates processing between services
- **Image**: `redis:7-alpine`
- **Resources**: 50m CPU, 128Mi memory
- **Storage**: Ephemeral (EmptyDir)
- **Service**: `redis-service:6379`

#### 2. Data Ingest Service (`data-ingest-deployment.yaml`)
- **Purpose**: Downloads data from CSC Allas
- **Resources**: 100m-500m CPU, 256Mi-512Mi memory
- **Environment**: CSC Allas credentials
- **Storage**: Shared PersistentVolume
- **Schedule**: Downloads every 30 minutes

#### 3. Data Clean Service (`data-clean-deployment.yaml`)
- **Purpose**: Processes and cleans raw data
- **Resources**: 150m-600m CPU, 384Mi-768Mi memory
- **Processing**: Event-driven (listens to Redis pub/sub)
- **Storage**: Shared PersistentVolume
- **Features**: Quality scoring, outlier removal

#### 4. Data Visualization Service (`data-visualization-deployment.yaml`)
- **Purpose**: Interactive Streamlit dashboard
- **Resources**: 150m-600m CPU, 384Mi-768Mi memory
- **Port**: 8501 (Streamlit)
- **Access**: External Route with TLS termination
- **Storage**: Shared PersistentVolume (read-only)

### Network Architecture

```yaml
# Service Discovery Configuration
Redis Service: redis-service.default.svc.cluster.local:6379
Data Ingest: data-ingest-service.default.svc.cluster.local:8080
Data Clean: data-clean-service.default.svc.cluster.local:8080
Visualization: data-visualization-service.default.svc.cluster.local:8501
```

### Storage Architecture

```yaml
# Shared Persistent Volume
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods can read/write
  resources:
    requests:
      storage: 10Gi
```

## 🔧 Service Configuration

### Environment Variables

Each service uses these common environment variables:

```yaml
env:
- name: REDIS_HOST
  value: "redis-service"
- name: REDIS_PORT
  value: "6379"
- name: SHARED_DATA_PATH
  value: "/shared/data"
- name: LOG_LEVEL
  value: "INFO"
```

### Health Checks

All services implement health checks:

```yaml
livenessProbe:
  exec:
    command:
    - python
    - -c
    - "import redis; r = redis.Redis(host='redis-service'); r.ping()"
  initialDelaySeconds: 60
  periodSeconds: 30
```

## 🚀 Deployment Options

### Option 1: Automated Deployment (Recommended)

```powershell
# One-command deployment
.\scripts\deploy-microservices.ps1
```

### Option 2: Manual Deployment

```powershell
# Step-by-step deployment
oc apply -f k8s-microservices\persistent-volume.yaml
oc apply -f k8s-microservices\redis-deployment.yaml
oc apply -f k8s-microservices\data-ingest-deployment.yaml
oc apply -f k8s-microservices\data-clean-deployment.yaml
oc apply -f k8s-microservices\data-visualization-deployment.yaml

# Wait for deployments
oc rollout status deployment/redis
oc rollout status deployment/data-ingest
oc rollout status deployment/data-clean
oc rollout status deployment/data-visualization
```

### Option 3: Development Mode

```powershell
# Deploy with dry-run first
.\scripts\deploy-microservices.ps1 -DryRun

# Then deploy normally
.\scripts\deploy-microservices.ps1
```

## 📊 Monitoring and Scaling

### Service Monitoring

```powershell
# Check all pods
oc get pods -l tier=backend,frontend

# Monitor specific services
oc logs -f deployment/data-ingest
oc logs -f deployment/data-clean
oc logs -f deployment/data-visualization
oc logs -f deployment/redis

# Check service endpoints
oc get endpoints
```

### Resource Monitoring

```powershell
# Check resource usage
oc top pods

# Check resource limits
oc describe pod <pod-name>

# Monitor events
oc get events --sort-by=.metadata.creationTimestamp
```

### Scaling Services

```powershell
# Scale individual services
oc scale deployment/data-ingest --replicas=2
oc scale deployment/data-clean --replicas=3
oc scale deployment/data-visualization --replicas=2

# Auto-scaling (if HPA is configured)
oc autoscale deployment/data-clean --min=1 --max=5 --cpu-percent=70
```

## 🔒 Security Considerations

### Network Security
- Services communicate within cluster network
- External access only through Routes with TLS termination
- Service-to-service communication encrypted

### Credential Management
- CSC Allas credentials stored as Kubernetes Secrets
- Application credentials recommended over passwords
- Secrets mounted as environment variables

### Access Control
```powershell
# Check current permissions
oc auth can-i create pods
oc auth can-i get secrets

# Service account configuration
oc create serviceaccount pipeline-sa
oc adm policy add-scc-to-user restricted system:serviceaccount:PROJECT:pipeline-sa
```

## 📈 Performance Tuning

### Resource Optimization

```yaml
# Optimized resource configuration
resources:
  requests:
    cpu: 100m      # Guaranteed CPU
    memory: 256Mi  # Guaranteed memory
  limits:
    cpu: 500m      # Maximum CPU
    memory: 512Mi  # Maximum memory
```

### Storage Optimization

```yaml
# Fast storage for better performance
storageClassName: standard-rwo  # SSD storage
accessModes:
  - ReadWriteMany  # Shared across pods
```

### Network Optimization

```yaml
# Service mesh for advanced traffic management (optional)
annotations:
  sidecar.istio.io/inject: "true"
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Pod Startup Issues
```powershell
# Check pod status
oc describe pod <pod-name>

# Check logs
oc logs <pod-name>

# Common fixes:
# - Check image pull secrets
# - Verify resource limits
# - Check persistent volume claims
```

#### 2. Service Communication Issues
```powershell
# Test service DNS resolution
oc exec -it <pod-name> -- nslookup redis-service

# Test service connectivity
oc exec -it <pod-name> -- nc -zv redis-service 6379

# Check service endpoints
oc get endpoints redis-service
```

#### 3. Storage Issues
```powershell
# Check PVC status
oc get pvc shared-data-pvc

# Check volume mounts
oc describe pod <pod-name>

# Test file system access
oc exec -it <pod-name> -- ls -la /shared/data
```

#### 4. Performance Issues
```powershell
# Check resource usage
oc top pods

# Check resource requests vs limits
oc describe pod <pod-name>

# Monitor CPU/Memory over time
oc adm top pod --containers=true
```

### Debug Commands

```powershell
# Interactive debugging
oc exec -it deployment/data-ingest -- /bin/bash

# Port forwarding for local testing
oc port-forward service/data-visualization-service 8501:8501

# View all resources
oc get all -l app=data-pipeline-microservices

# Export configuration for backup
oc get all,secrets,pvc -o yaml > pipeline-backup.yaml
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Deploy Microservices Pipeline
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and Push Images
      run: |
        docker build -t ${{ secrets.REGISTRY }}/data-ingest:${{ github.sha }} data-ingest/
        docker build -t ${{ secrets.REGISTRY }}/data-clean:${{ github.sha }} data-clean/
        docker build -t ${{ secrets.REGISTRY }}/data-visualization:${{ github.sha }} data-visualization/
        
    - name: Deploy to OpenShift
      run: |
        oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}
        oc apply -f k8s-microservices/
        oc rollout status deployment/data-ingest
        oc rollout status deployment/data-clean
        oc rollout status deployment/data-visualization
```

## 📚 Learning Resources

### Microservices Concepts
- [Microservices Pattern](https://microservices.io/)
- [Kubernetes Microservices Best Practices](https://kubernetes.io/docs/concepts/)
- [OpenShift Container Platform Documentation](https://docs.openshift.com/)

### CSC Services
- [CSC Allas Documentation](https://docs.csc.fi/data/Allas/)
- [CSC Rahti Documentation](https://docs.csc.fi/cloud/rahti/)

## 🎓 Educational Value

This project demonstrates:

1. **Microservices Architecture Patterns**
   - Service discovery and communication
   - Data consistency in distributed systems
   - Event-driven architecture with pub/sub

2. **Kubernetes/OpenShift Concepts**
   - Pod vs. Service separation
   - ConfigMaps and Secrets management
   - Persistent volume sharing
   - Service mesh communication

3. **Cloud-Native Development**
   - Container orchestration
   - Horizontal scaling
   - Health checks and observability
   - Infrastructure as Code

## 🤝 Contributing

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CSC - IT Center for Science for providing Allas storage and Rahti platform
- OpenShift and Kubernetes communities
- University of Oulu for educational support

---

**📊 Ready to deploy your microservices data pipeline?**

Run: `.\scripts\deploy-microservices.ps1` and start analyzing data! 🚀