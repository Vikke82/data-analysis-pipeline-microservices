# Data Analysis Pipeline - Microservices Architecture
# Deployment Script
# This script deploys all microservices to OpenShift/Kubernetes

param(
    [string]$Project = "",
    [switch]$Help,
    [switch]$DryRun
)

if ($Help) {
    Write-Host @"
Deployment Script for Data Analysis Pipeline - Microservices

USAGE:
    .\deploy-microservices.ps1 [-Project <project>] [-DryRun] [-Help]

PARAMETERS:
    -Project    OpenShift project name (optional, will use current project)
    -DryRun     Show what would be deployed without actually deploying
    -Help       Show this help message

EXAMPLES:
    .\deploy-microservices.ps1
    .\deploy-microservices.ps1 -Project "my-data-pipeline"
    .\deploy-microservices.ps1 -DryRun

PREREQUISITES:
    - OpenShift CLI (oc) installed and logged in
    - Container images built and pushed to registry
    - Finnhub API credentials configured

"@
    exit 0
}

Write-Host "🚀 Data Analysis Pipeline - Microservices Deployment" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if oc command is available
try {
    oc version --client | Out-Null
}
catch {
    Write-Host "❌ OpenShift CLI (oc) not found. Please install it first." -ForegroundColor Red
    Write-Host "   Download from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/" -ForegroundColor White
    exit 1
}

# Check if logged in to OpenShift
try {
    $currentProject = oc project --short 2>$null
    if (-not $currentProject) {
        Write-Host "❌ Not logged in to OpenShift. Please run: oc login" -ForegroundColor Red
        exit 1
    }
    
    if ($Project -and $Project -ne $currentProject) {
        Write-Host "🔄 Switching to project: $Project" -ForegroundColor Yellow
        oc project $Project
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to switch to project: $Project" -ForegroundColor Red
            exit 1
        }
    }
    
    $currentProject = oc project --short 2>$null
    Write-Host "📍 Current project: $currentProject" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error checking OpenShift login status" -ForegroundColor Red
    exit 1
}

# Check if Finnhub credentials secret exists
Write-Host ""
Write-Host "🔑 Checking Finnhub credentials..." -ForegroundColor Yellow
try {
    oc get secret finnhub-credentials | Out-Null
    Write-Host "   ✅ Finnhub credentials secret found" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Finnhub credentials secret not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 To create Finnhub credentials secret, run:" -ForegroundColor Yellow
    Write-Host @"
oc create secret generic finnhub-credentials \
  --from-literal=FINNHUB_API_KEY=your_finnhub_api_key
"@ -ForegroundColor White
    Write-Host ""
    exit 1
}

# Define deployment order and files
$deploymentSteps = @(
    @{
        Name = "Persistent Volume & ConfigMap"
        Files = @("k8s-microservices\persistent-volume.yaml")
        Description = "Shared storage and configuration"
    },
    @{
        Name = "Redis Cache Service"
        Files = @("k8s-microservices\redis-deployment.yaml")
        Description = "Redis coordination service"
        WaitFor = "deployment/redis"
    },
    @{
        Name = "Data Ingestion Service"
        Files = @("k8s-microservices\data-ingest-deployment.yaml")
        Description = "Stock market data ingestion from Finnhub API"
        WaitFor = "deployment/data-ingest"
    },
    @{
        Name = "Data Cleaning Service"
        Files = @("k8s-microservices\data-clean-deployment.yaml")
        Description = "Data processing and cleaning"
        WaitFor = "deployment/data-clean"
    },
    @{
        Name = "Data Visualization Service"
        Files = @("k8s-microservices\data-visualization-deployment.yaml")
        Description = "Streamlit dashboard and web interface"
        WaitFor = "deployment/data-visualization"
    }
)

# Deploy each step
Write-Host ""
Write-Host "🚀 Starting deployment..." -ForegroundColor Green
Write-Host ""

foreach ($step in $deploymentSteps) {
    Write-Host "📦 Deploying: $($step.Name)" -ForegroundColor Yellow
    Write-Host "   Description: $($step.Description)" -ForegroundColor White
    
    foreach ($file in $step.Files) {
        if (-not (Test-Path $file)) {
            Write-Host "   ❌ File not found: $file" -ForegroundColor Red
            continue
        }
        
        Write-Host "   📄 Applying: $file" -ForegroundColor White
        
        if ($DryRun) {
            Write-Host "   🔍 DRY RUN - Would apply: $file" -ForegroundColor Cyan
            oc apply -f $file --dry-run=client
        }
        else {
            try {
                oc apply -f $file
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "   ❌ Failed to apply: $file" -ForegroundColor Red
                    continue
                }
                Write-Host "   ✅ Successfully applied: $file" -ForegroundColor Green
            }
            catch {
                Write-Host "   ❌ Error applying $file`: $($_.Exception.Message)" -ForegroundColor Red
                continue
            }
        }
    }
    
    # Wait for deployment if specified
    if ($step.WaitFor -and -not $DryRun) {
        Write-Host "   ⏳ Waiting for $($step.WaitFor) to be ready..." -ForegroundColor Cyan
        try {
            oc rollout status $($step.WaitFor) --timeout=300s
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ $($step.WaitFor) is ready" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️  $($step.WaitFor) deployment may have issues" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "   ⚠️  Error waiting for $($step.WaitFor): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

if (-not $DryRun) {
    # Get route URL
    Write-Host "🌐 Getting application URL..." -ForegroundColor Yellow
    try {
        $routeUrl = oc get route data-visualization-route -o jsonpath='{.spec.host}' 2>$null
        if ($routeUrl) {
            Write-Host "✅ Application deployed successfully!" -ForegroundColor Green
            Write-Host "🔗 Dashboard URL: https://$routeUrl" -ForegroundColor Cyan
        }
        else {
            Write-Host "⚠️  Route not found. Check with: oc get routes" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Could not get route URL. Check with: oc get routes" -ForegroundColor Yellow
    }
    
    # Show deployment status
    Write-Host ""
    Write-Host "📋 Deployment Status:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "🗄️  Redis Service:" -ForegroundColor White
    oc get pods -l app=redis
    Write-Host ""
    
    Write-Host "📥 Data Ingest Service:" -ForegroundColor White
    oc get pods -l app=data-ingest
    Write-Host ""
    
    Write-Host "🧹 Data Clean Service:" -ForegroundColor White
    oc get pods -l app=data-clean
    Write-Host ""
    
    Write-Host "📊 Data Visualization Service:" -ForegroundColor White
    oc get pods -l app=data-visualization
    Write-Host ""
    
    Write-Host "🌐 Routes:" -ForegroundColor White
    oc get routes
    Write-Host ""
}

Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Yellow
Write-Host "   Check pods:              oc get pods" -ForegroundColor White
Write-Host "   View service logs:       oc logs -f deployment/SERVICE_NAME" -ForegroundColor White
Write-Host "   Get routes:              oc get routes" -ForegroundColor White
Write-Host "   Scale service:           oc scale deployment/SERVICE_NAME --replicas=2" -ForegroundColor White
Write-Host "   Delete deployment:       oc delete -f k8s-microservices/" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitoring commands:" -ForegroundColor Yellow
Write-Host "   Watch pods:              oc get pods -w" -ForegroundColor White
Write-Host "   Check service status:    oc get svc" -ForegroundColor White
Write-Host "   View events:             oc get events --sort-by=.metadata.creationTimestamp" -ForegroundColor White
Write-Host ""

if (-not $DryRun) {
    Write-Host "🏁 Your microservices data analysis pipeline is now running!" -ForegroundColor Green
    if ($routeUrl) {
        Write-Host "   Access your dashboard at: https://$routeUrl" -ForegroundColor Cyan
    }
}