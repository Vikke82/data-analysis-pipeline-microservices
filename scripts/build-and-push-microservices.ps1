# Data Analysis Pipeline - Microservices Architecture
# Build and Push Script
# This script builds and pushes Docker images for all microservices

param(
    [string]$Registry = "",
    [string]$Project = "",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Build and Push Script for Data Analysis Pipeline - Microservices

USAGE:
    .\build-and-push-microservices.ps1 [-Registry <registry>] [-Project <project>]

PARAMETERS:
    -Registry   Docker registry URL (optional, will prompt if not provided)
    -Project    Project name (optional, will prompt if not provided)
    -Help       Show this help message

EXAMPLES:
    .\build-and-push-microservices.ps1
    .\build-and-push-microservices.ps1 -Registry "image-registry.rahti.csc.fi/myproject" -Project "myproject"

"@
    exit 0
}

Write-Host "🐳 Data Analysis Pipeline - Microservices Build & Push" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Get registry and project information
if (-not $Registry) {
    Write-Host "📋 Available registry options:" -ForegroundColor Yellow
    Write-Host "   1. CSC Rahti Registry (image-registry.rahti.csc.fi)" -ForegroundColor White
    Write-Host "   2. Docker Hub (docker.io)" -ForegroundColor White
    Write-Host "   3. Custom registry" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Select registry option (1-3)"
    
    switch ($choice) {
        "1" {
            if (-not $Project) {
                $Project = Read-Host "Enter your CSC Rahti project name"
            }
            $Registry = "image-registry.rahti.csc.fi/$Project"
        }
        "2" {
            if (-not $Project) {
                $Project = Read-Host "Enter your Docker Hub username"
            }
            $Registry = "docker.io/$Project"
        }
        "3" {
            $Registry = Read-Host "Enter custom registry URL (e.g., myregistry.com/myproject)"
        }
        default {
            Write-Host "❌ Invalid choice. Exiting." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""
Write-Host "🎯 Using registry: $Registry" -ForegroundColor Green
Write-Host ""

# Check authentication for CSC Rahti registry
if ($Registry -like "*rahti.csc.fi*") {
    Write-Host "🔐 Checking CSC Rahti authentication..." -ForegroundColor Yellow
    
    # Check if oc is available
    try {
        $ocVersion = oc version --client 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ OpenShift CLI (oc) not found!" -ForegroundColor Red
            Write-Host "   Please install oc CLI: https://docs.openshift.com/container-platform/4.14/cli_reference/openshift_cli/getting-started-cli.html" -ForegroundColor Yellow
            exit 1
        }
    }
    catch {
        Write-Host "❌ OpenShift CLI (oc) not found!" -ForegroundColor Red
        Write-Host "   Please install oc CLI: https://docs.openshift.com/container-platform/4.14/cli_reference/openshift_cli/getting-started-cli.html" -ForegroundColor Yellow
        exit 1
    }
    
    # Check if logged in
    try {
        $currentProject = oc project -q 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Not logged into OpenShift!" -ForegroundColor Red
            Write-Host "   Please login first:" -ForegroundColor Yellow
            Write-Host "   oc login https://api.2.rahti.csc.fi:6443" -ForegroundColor White
            Write-Host "   oc new-project $Project --description='csc_project: YOUR_PROJECT_NUMBER'" -ForegroundColor White
            exit 1
        }
        Write-Host "   ✅ Logged in to project: $currentProject" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Not logged into OpenShift!" -ForegroundColor Red
        Write-Host "   Please login first:" -ForegroundColor Yellow
        Write-Host "   oc login https://api.2.rahti.csc.fi:6443" -ForegroundColor White
        exit 1
    }
    
    # Login to Docker registry
    Write-Host "   🔑 Logging into Docker registry..." -ForegroundColor White
    try {
        # Test network connectivity first
        Write-Host "      Testing network connectivity..." -ForegroundColor Gray
        try {
            $testConnection = Test-NetConnection -ComputerName "image-registry.rahti.csc.fi" -Port 443 -WarningAction SilentlyContinue -ErrorAction Stop
            if (-not $testConnection.TcpTestSucceeded) {
                Write-Host "❌ Cannot reach CSC Rahti registry!" -ForegroundColor Red
                Write-Host "   Network troubleshooting steps:" -ForegroundColor Yellow
                Write-Host "   1. Check your internet connection" -ForegroundColor White
                Write-Host "   2. Try: nslookup image-registry.rahti.csc.fi" -ForegroundColor White
                Write-Host "   3. Check if you're behind a corporate firewall/proxy" -ForegroundColor White
                Write-Host "   4. Try connecting from a different network" -ForegroundColor White
                Write-Host ""
                $continueAnyway = Read-Host "Continue anyway and try Docker login? (y/n)"
                if ($continueAnyway -ne "y" -and $continueAnyway -ne "Y") {
                    exit 1
                }
            }
        }
        catch {
            Write-Host "      Network test inconclusive, proceeding with login attempt..." -ForegroundColor Gray
        }
        
        $token = oc whoami -t
        $loginResult = echo $token | docker login image-registry.rahti.csc.fi -u unused --password-stdin 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker registry login failed!" -ForegroundColor Red
            Write-Host $loginResult -ForegroundColor Red
            Write-Host ""
            Write-Host "🔧 Troubleshooting options:" -ForegroundColor Yellow
            Write-Host "   1. Check your network connection and DNS settings" -ForegroundColor White
            Write-Host "   2. Try alternative registry: Docker Hub" -ForegroundColor White
            Write-Host "   3. Use VPN if behind restrictive network" -ForegroundColor White
            Write-Host "   4. Contact your network administrator about firewall rules" -ForegroundColor White
            Write-Host ""
            $useAlternative = Read-Host "Would you like to use Docker Hub instead? (y/n)"
            if ($useAlternative -eq "y" -or $useAlternative -eq "Y") {
                $dockerHubUser = Read-Host "Enter your Docker Hub username"
                $Registry = "docker.io/$dockerHubUser"
                Write-Host "   ✅ Switched to Docker Hub: $Registry" -ForegroundColor Green
                Write-Host "   📝 Make sure you're logged into Docker Hub: docker login" -ForegroundColor Yellow
            }
            else {
                exit 1
            }
        }
        else {
            Write-Host "   ✅ Docker registry login successful" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ Failed to login to Docker registry: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Alternative solutions:" -ForegroundColor Yellow
        Write-Host "   1. Use Docker Hub: docker login" -ForegroundColor White
        Write-Host "   2. Check network connectivity" -ForegroundColor White
        Write-Host "   3. Try from different network/location" -ForegroundColor White
        exit 1
    }
}

Write-Host ""

# Define services
$services = @(
    @{
        Name = "data-ingest"
        Path = "data-ingest"
        Description = "Data ingestion from CSC Allas"
    },
    @{
        Name = "data-clean"
        Path = "data-clean"
        Description = "Data cleaning and processing"
    },
    @{
        Name = "data-visualization"
        Path = "data-visualization"
        Description = "Streamlit dashboard"
    }
)

# Build and push each service
foreach ($service in $services) {
    Write-Host "🔨 Building $($service.Name): $($service.Description)" -ForegroundColor Yellow
    
    $imageName = "$Registry/$($service.Name):latest"
    $buildPath = $service.Path
    
    if (-not (Test-Path $buildPath)) {
        Write-Host "❌ Directory $buildPath not found!" -ForegroundColor Red
        continue
    }
    
    # Build the image
    Write-Host "   📦 Building image: $imageName" -ForegroundColor White
    try {
        $buildResult = docker build -t $imageName $buildPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Build failed for $($service.Name)" -ForegroundColor Red
            Write-Host $buildResult -ForegroundColor Red
            continue
        }
        Write-Host "   ✅ Build successful" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Build failed for $($service.Name): $($_.Exception.Message)" -ForegroundColor Red
        continue
    }
    
    # Push the image
    Write-Host "   🚀 Pushing image: $imageName" -ForegroundColor White
    Write-Host "      (This may take several minutes for first push...)" -ForegroundColor Gray
    try {
        $pushJob = Start-Job -ScriptBlock {
            param($imageName)
            docker push $imageName 2>&1
        } -ArgumentList $imageName
        
        # Wait for push with timeout (10 minutes)
        $timeout = 600 # seconds
        $completed = Wait-Job $pushJob -Timeout $timeout
        
        if ($completed) {
            $pushResult = Receive-Job $pushJob
            Remove-Job $pushJob
            
            if ($pushResult -like "*error*" -or $pushResult -like "*failed*") {
                Write-Host "❌ Push failed for $($service.Name)" -ForegroundColor Red
                Write-Host $pushResult -ForegroundColor Red
                continue
            }
            Write-Host "   ✅ Push successful" -ForegroundColor Green
        }
        else {
            Write-Host "   ⏱️  Push is taking longer than expected..." -ForegroundColor Yellow
            Write-Host "      You can check progress manually: docker push $imageName" -ForegroundColor Gray
            
            # Kill the job and continue
            Stop-Job $pushJob -ErrorAction SilentlyContinue
            Remove-Job $pushJob -ErrorAction SilentlyContinue
            
            $continueChoice = Read-Host "      Continue with next service? (y/n)"
            if ($continueChoice -ne "y" -and $continueChoice -ne "Y") {
                Write-Host "   Stopping script. You can resume pushes manually." -ForegroundColor Yellow
                exit 0
            }
        }
    }
    catch {
        Write-Host "❌ Push failed for $($service.Name): $($_.Exception.Message)" -ForegroundColor Red
        continue
    }
    
    Write-Host ""
}

Write-Host "🎉 Build and push completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Update k8s-microservices/*.yaml files with your registry URL" -ForegroundColor White
Write-Host "   2. Run: .\deploy-microservices.ps1" -ForegroundColor White
Write-Host "   3. Check deployment: oc get pods" -ForegroundColor White
Write-Host ""

# Offer to update deployment files
$updateFiles = Read-Host "Update deployment files with new registry? (y/n)"
if ($updateFiles -eq "y" -or $updateFiles -eq "Y") {
    Write-Host "📝 Updating deployment files..." -ForegroundColor Yellow
    
    $deploymentFiles = @(
        "k8s-microservices\data-ingest-deployment.yaml",
        "k8s-microservices\data-clean-deployment.yaml",
        "k8s-microservices\data-visualization-deployment.yaml"
    )
    
    foreach ($file in $deploymentFiles) {
        if (Test-Path $file) {
            try {
                (Get-Content $file) -replace 'image-registry\.rahti\.csc\.fi/your-project', $Registry | Set-Content $file
                Write-Host "   ✅ Updated $file" -ForegroundColor Green
            }
            catch {
                Write-Host "   ❌ Failed to update ${file}: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "   🎯 Deployment files updated with registry: $Registry" -ForegroundColor Green
}