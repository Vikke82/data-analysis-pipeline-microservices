# Deployment Guide - Microservices Architecture

This guide provides step-by-step instructions for deploying the data analysis pipeline using microservices architecture on CSC Rahti (OpenShift).

## 🎯 Prerequisites

### Required Tools
- **OpenShift CLI (oc)** - [Download here](https://mirror.openshift.com/pub/openshift-v4/clients/ocp/)
- **Docker** - For building container images
- **PowerShell** - For running deployment scripts
- **Git** - For repository management

### Required Access
- **CSC Account** with Allas storage access
- **CSC Rahti Project** - Request at [CSC Customer Portal](https://my.csc.fi)
- **Container Registry** - CSC Rahti registry or Docker Hub

### Resource Requirements
| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|------------|-----------|---------------|--------------|
| Redis | 50m | 200m | 128Mi | 256Mi |
| Data Ingest | 100m | 500m | 256Mi | 512Mi |
| Data Clean | 150m | 600m | 384Mi | 768Mi |
| Visualization | 150m | 600m | 384Mi | 768Mi |
| **Total** | **450m** | **1.9 cores** | **1.15GB** | **2.3GB** |

## 📋 Step-by-Step Deployment

### Step 1: Environment Setup

1. **Clone Repository**
   ```powershell
   git clone <your-repository-url>
   cd "Data Analysis pipeline microservice"
   ```

2. **Login to CSC Rahti**
   ```powershell
   oc login https://api.2.rahti.csc.fi:6443
   ```

3. **Create or Select Project**
   ```powershell
   # Create new project
   oc new-project my-data-pipeline --description="csc_project: YOUR_PROJECT_NUMBER"
   
   # Or switch to existing project
   oc project my-data-pipeline
   ```

### Step 2: Configure CSC Allas Credentials

**Option A: Interactive Script (Recommended)**
```powershell
.\scripts\manage-allas-credentials-microservices.ps1
# Choose option 5 for Application Credentials (most secure)
```

**Option B: Manual Setup**
```powershell
oc create secret generic allas-credentials \
  --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 \
  --from-literal=OS_USERNAME=your_csc_username \
  --from-literal=OS_PASSWORD=your_csc_password \
  --from-literal=OS_PROJECT_NAME=project_XXXXXXX \
  --from-literal=OS_PROJECT_DOMAIN_NAME=Default \
  --from-literal=OS_USER_DOMAIN_NAME=Default \
  --from-literal=DATA_BUCKET=your_container_name
```

### Step 3: Build and Push Container Images

**Option A: Automated Script (Recommended)**
```powershell
.\scripts\build-and-push-microservices.ps1
# Follow prompts to select registry and project
```

**Option B: Manual Build and Push**
```powershell
# Set your registry
$REGISTRY = "image-registry.rahti.csc.fi/your-project"

# Build images
docker build -t $REGISTRY/data-ingest:latest data-ingest/
docker build -t $REGISTRY/data-clean:latest data-clean/
docker build -t $REGISTRY/data-visualization:latest data-visualization/

# Push images
docker push $REGISTRY/data-ingest:latest
docker push $REGISTRY/data-clean:latest
docker push $REGISTRY/data-visualization:latest
```

### Step 4: Deploy Microservices

**Option A: Automated Deployment (Recommended)**
```powershell
.\scripts\deploy-microservices.ps1
```

**Option B: Manual Deployment**
```powershell
# Deploy in order
oc apply -f k8s-microservices\persistent-volume.yaml
oc apply -f k8s-microservices\redis-deployment.yaml
oc apply -f k8s-microservices\data-ingest-deployment.yaml
oc apply -f k8s-microservices\data-clean-deployment.yaml
oc apply -f k8s-microservices\data-visualization-deployment.yaml

# Wait for deployments
oc rollout status deployment/redis --timeout=300s
oc rollout status deployment/data-ingest --timeout=300s
oc rollout status deployment/data-clean --timeout=300s
oc rollout status deployment/data-visualization --timeout=300s
```

### Step 5: Verify Deployment

```powershell
# Check pod status
oc get pods

# Expected output:
# NAME                                 READY   STATUS    RESTARTS   AGE
# redis-7b8c4f4d6d-xyz12              1/1     Running   0          2m
# data-ingest-6f9d8b7c5a-abc34        1/1     Running   0          2m
# data-clean-8a5e7f2d1b-def56         1/1     Running   0          2m
# data-visualization-9c4d6e8a7b-ghi78 1/1     Running   0          2m

# Check services
oc get svc

# Check routes
oc get routes

# Get dashboard URL
oc get route data-visualization-route -o jsonpath='{.spec.host}'
```

## 🔧 Configuration Details

### Persistent Volume Configuration

```yaml
# k8s-microservices/persistent-volume.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-pvc
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods can access
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard-rwo  # CSC Rahti storage class
```

### Service Discovery Configuration

```yaml
# ConfigMap for service discovery
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-config
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  SHARED_DATA_PATH: "/shared/data"
```

### Health Check Configuration

```yaml
# Example health check for data services
livenessProbe:
  exec:
    command:
    - python
    - -c
    - "import redis; r = redis.Redis(host='redis-service'); r.ping()"
  initialDelaySeconds: 60
  periodSeconds: 30
```

## 📊 Monitoring and Troubleshooting

### Monitoring Commands

```powershell
# Watch pod status
oc get pods -w

# Check resource usage
oc top pods

# View service logs
oc logs -f deployment/data-ingest
oc logs -f deployment/data-clean
oc logs -f deployment/data-visualization

# Check service endpoints
oc get endpoints

# View recent events
oc get events --sort-by=.metadata.creationTimestamp
```

### Common Issues and Solutions

#### 1. Pod Not Starting
```powershell
# Check pod details
oc describe pod <pod-name>

# Common causes:
# - Image pull errors -> Check registry access
# - Resource constraints -> Check cluster quotas
# - Volume mount issues -> Check PVC status
```

#### 2. Service Communication Issues
```powershell
# Test service connectivity
oc exec -it deployment/data-ingest -- nc -zv redis-service 6379

# Check DNS resolution
oc exec -it deployment/data-ingest -- nslookup redis-service

# Verify service configuration
oc describe service redis-service
```

#### 3. Storage Issues
```powershell
# Check PVC status
oc get pvc shared-data-pvc

# Check volume mounts
oc describe pod <pod-name>

# Test file access
oc exec -it deployment/data-clean -- ls -la /shared/data
```

#### 4. Performance Issues
```powershell
# Check resource utilization
oc top pods --containers

# Check resource limits
oc describe pod <pod-name>

# Scale up if needed
oc scale deployment/data-clean --replicas=3
```

## 🚀 Scaling and Optimization

### Horizontal Scaling

```powershell
# Scale individual services based on load
oc scale deployment/data-ingest --replicas=1      # Limited by external API
oc scale deployment/data-clean --replicas=5       # CPU-intensive processing
oc scale deployment/data-visualization --replicas=2  # Handle more users
oc scale deployment/redis --replicas=1            # Single instance sufficient
```

### Vertical Scaling

```powershell
# Update resource limits
oc patch deployment data-clean -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "data-clean",
          "resources": {
            "requests": {"cpu": "300m", "memory": "512Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
          }
        }]
      }
    }
  }
}'
```

### Auto-Scaling (HPA)

```powershell
# Enable horizontal pod autoscaler
oc autoscale deployment/data-clean --min=1 --max=10 --cpu-percent=70
oc autoscale deployment/data-visualization --min=1 --max=5 --cpu-percent=80

# Check HPA status
oc get hpa
```

## 🔐 Security Best Practices

### Network Security
```yaml
# Network policies (if supported)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: data-pipeline-netpol
spec:
  podSelector:
    matchLabels:
      app: data-pipeline-microservices
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: data-pipeline-microservices
```

### Secret Management
```powershell
# Use application credentials instead of passwords
# Rotate secrets regularly
# Monitor secret access logs
```

### RBAC Configuration
```powershell
# Create service account
oc create serviceaccount pipeline-sa

# Bind minimal required permissions
oc create rolebinding pipeline-rb --clusterrole=edit --serviceaccount=default:pipeline-sa
```

## 🔄 CI/CD Integration

### GitLab CI Example
```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

variables:
  REGISTRY: "image-registry.rahti.csc.fi/your-project"

build:
  stage: build
  script:
    - docker build -t $REGISTRY/data-ingest:$CI_COMMIT_SHA data-ingest/
    - docker build -t $REGISTRY/data-clean:$CI_COMMIT_SHA data-clean/
    - docker build -t $REGISTRY/data-visualization:$CI_COMMIT_SHA data-visualization/
    - docker push $REGISTRY/data-ingest:$CI_COMMIT_SHA
    - docker push $REGISTRY/data-clean:$CI_COMMIT_SHA
    - docker push $REGISTRY/data-visualization:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - oc login --token=$OPENSHIFT_TOKEN --server=$OPENSHIFT_SERVER
    - oc project $OPENSHIFT_PROJECT
    - oc set image deployment/data-ingest data-ingest=$REGISTRY/data-ingest:$CI_COMMIT_SHA
    - oc set image deployment/data-clean data-clean=$REGISTRY/data-clean:$CI_COMMIT_SHA
    - oc set image deployment/data-visualization data-visualization=$REGISTRY/data-visualization:$CI_COMMIT_SHA
    - oc rollout status deployment/data-ingest
    - oc rollout status deployment/data-clean
    - oc rollout status deployment/data-visualization
```

## 🧹 Cleanup

### Remove Deployment
```powershell
# Remove all resources
oc delete -f k8s-microservices/

# Or remove individual components
oc delete deployment redis data-ingest data-clean data-visualization
oc delete service redis-service data-ingest-service data-clean-service data-visualization-service
oc delete route data-visualization-route
oc delete pvc shared-data-pvc
oc delete configmap pipeline-config
oc delete secret allas-credentials
```

### Complete Project Cleanup
```powershell
# Delete entire project (use with caution!)
oc delete project my-data-pipeline
```

## 📚 Next Steps

1. **Customize Services** - Modify the Python code for your specific data processing needs
2. **Add Monitoring** - Integrate Prometheus/Grafana for detailed metrics  
3. **Implement Logging** - Set up centralized logging with ELK stack
4. **Security Hardening** - Implement network policies and pod security policies
5. **Performance Tuning** - Optimize based on your workload characteristics

## 🆘 Support

- **CSC Documentation**: [docs.csc.fi](https://docs.csc.fi/)
- **OpenShift Documentation**: [docs.openshift.com](https://docs.openshift.com/)
- **Course Support**: Contact your instructor or TA

---

**🎉 Congratulations!** You've successfully deployed a microservices-based data analysis pipeline on CSC Rahti! 🚀