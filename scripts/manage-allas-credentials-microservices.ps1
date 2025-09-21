# CSC Allas Credentials Management for Microservices
# This script helps manage CSC Allas credentials for the microservices deployment

param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"
CSC Allas Credentials Management for Microservices

This script helps you manage CSC Allas credentials for the data analysis pipeline microservices.

USAGE:
    .\manage-allas-credentials-microservices.ps1 [-Help]

FEATURES:
    1. Create new Allas credentials secret
    2. Update existing credentials
    3. View current credentials (masked)
    4. Test connection to Allas
    5. Delete credentials
    6. Setup application credentials (recommended)

"@
    exit 0
}

Write-Host "🔑 CSC Allas Credentials Management - Microservices" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if oc command is available
try {
    oc version --client | Out-Null
}
catch {
    Write-Host "❌ OpenShift CLI (oc) not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Check if logged in to OpenShift
try {
    $currentProject = oc project --short 2>$null
    if (-not $currentProject) {
        Write-Host "❌ Not logged in to OpenShift. Please run: oc login" -ForegroundColor Red
        exit 1
    }
    Write-Host "📍 Current project: $currentProject" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error checking OpenShift login status" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Available options:" -ForegroundColor Yellow
Write-Host "   1. Create new credentials" -ForegroundColor White
Write-Host "   2. Update existing credentials" -ForegroundColor White
Write-Host "   3. View current credentials" -ForegroundColor White
Write-Host "   4. Test Allas connection" -ForegroundColor White
Write-Host "   5. Setup application credentials (recommended)" -ForegroundColor White
Write-Host "   6. Delete credentials" -ForegroundColor White
Write-Host "   7. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-7)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🆕 Creating new Allas credentials..." -ForegroundColor Yellow
        
        # Check if secret already exists
        try {
            oc get secret allas-credentials | Out-Null
            Write-Host "⚠️  Credentials secret already exists!" -ForegroundColor Yellow
            $overwrite = Read-Host "Overwrite existing secret? (y/n)"
            if ($overwrite -ne "y" -and $overwrite -ne "Y") {
                Write-Host "❌ Cancelled." -ForegroundColor Red
                exit 0
            }
            oc delete secret allas-credentials
        }
        catch {
            # Secret doesn't exist, which is fine
        }
        
        Write-Host "Please enter your CSC Allas credentials:" -ForegroundColor White
        $osUsername = Read-Host "OS_USERNAME (your CSC username)"
        $osPassword = Read-Host "OS_PASSWORD (your CSC password)" -AsSecureString
        $osPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($osPassword))
        $osProjectName = Read-Host "OS_PROJECT_NAME (e.g., project_2015319)"
        $dataBucket = Read-Host "DATA_BUCKET (container name, default: cloudservices)"
        
        if (-not $dataBucket) { $dataBucket = "cloudservices" }
        
        try {
            oc create secret generic allas-credentials `
                --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 `
                --from-literal=OS_USERNAME=$osUsername `
                --from-literal=OS_PASSWORD=$osPasswordPlain `
                --from-literal=OS_PROJECT_NAME=$osProjectName `
                --from-literal=OS_PROJECT_DOMAIN_NAME=Default `
                --from-literal=OS_USER_DOMAIN_NAME=Default `
                --from-literal=DATA_BUCKET=$dataBucket
            
            Write-Host "✅ Credentials created successfully!" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to create credentials: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "🔄 Updating existing credentials..." -ForegroundColor Yellow
        
        try {
            oc get secret allas-credentials | Out-Null
        }
        catch {
            Write-Host "❌ No existing credentials found. Use option 1 to create new credentials." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Enter new values (press Enter to keep current value):" -ForegroundColor White
        
        $osUsername = Read-Host "OS_USERNAME"
        $osPassword = Read-Host "OS_PASSWORD" -AsSecureString
        $osPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($osPassword))
        $osProjectName = Read-Host "OS_PROJECT_NAME"
        $dataBucket = Read-Host "DATA_BUCKET"
        
        # Build the update command
        $updateCmd = "oc create secret generic allas-credentials --dry-run=client -o yaml"
        
        if ($osUsername) { $updateCmd += " --from-literal=OS_USERNAME=$osUsername" }
        if ($osPasswordPlain) { $updateCmd += " --from-literal=OS_PASSWORD=$osPasswordPlain" }
        if ($osProjectName) { $updateCmd += " --from-literal=OS_PROJECT_NAME=$osProjectName" }
        if ($dataBucket) { $updateCmd += " --from-literal=DATA_BUCKET=$dataBucket" }
        
        $updateCmd += " --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3"
        $updateCmd += " --from-literal=OS_PROJECT_DOMAIN_NAME=Default"
        $updateCmd += " --from-literal=OS_USER_DOMAIN_NAME=Default"
        $updateCmd += " | oc apply -f -"
        
        try {
            Invoke-Expression $updateCmd
            Write-Host "✅ Credentials updated successfully!" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to update credentials: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "👁️  Viewing current credentials..." -ForegroundColor Yellow
        
        try {
            $secretData = oc get secret allas-credentials -o json | ConvertFrom-Json
            Write-Host "Current credentials (masked):" -ForegroundColor White
            
            foreach ($key in $secretData.data.Keys) {
                $value = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secretData.data.$key))
                if ($key -eq "OS_PASSWORD") {
                    Write-Host "   $key`: ********" -ForegroundColor Gray
                }
                else {
                    Write-Host "   $key`: $value" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Host "❌ Failed to view credentials. Make sure they exist." -ForegroundColor Red
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "🧪 Testing Allas connection..." -ForegroundColor Yellow
        
        try {
            oc get secret allas-credentials | Out-Null
        }
        catch {
            Write-Host "❌ No credentials found. Create credentials first." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Creating test pod to verify connection..." -ForegroundColor White
        
        $testPodYaml = @"
apiVersion: v1
kind: Pod
metadata:
  name: allas-test-microservices
spec:
  containers:
  - name: test
    image: python:3.11-slim
    command: ["/bin/bash"]
    args: ["-c", "pip install python-swiftclient python-keystoneclient && python -c 'from swiftclient.service import SwiftService; import os; print(f\"Testing connection to {os.environ.get(\"OS_PROJECT_NAME\", \"unknown project\")}\"); swift = SwiftService(); list(swift.list(container=os.environ.get(\"DATA_BUCKET\", \"cloudservices\"))); print(\"✅ Connection successful!\")'"]
    envFrom:
    - secretRef:
        name: allas-credentials
  restartPolicy: Never
"@
        
        try {
            # Clean up any existing test pod
            oc delete pod allas-test-microservices --ignore-not-found | Out-Null
            
            # Create test pod
            $testPodYaml | oc apply -f -
            
            Write-Host "Waiting for test to complete..." -ForegroundColor Cyan
            
            # Wait for pod to complete
            $timeout = 120
            $elapsed = 0
            while ($elapsed -lt $timeout) {
                $podStatus = oc get pod allas-test-microservices -o jsonpath='{.status.phase}' 2>$null
                if ($podStatus -eq "Succeeded") {
                    $logs = oc logs allas-test-microservices
                    Write-Host $logs -ForegroundColor Green
                    break
                }
                elseif ($podStatus -eq "Failed") {
                    Write-Host "❌ Connection test failed!" -ForegroundColor Red
                    $logs = oc logs allas-test-microservices
                    Write-Host $logs -ForegroundColor Red
                    break
                }
                
                Start-Sleep 5
                $elapsed += 5
                Write-Host "." -NoNewline -ForegroundColor Cyan
            }
            
            # Clean up test pod
            oc delete pod allas-test-microservices --ignore-not-found | Out-Null
        }
        catch {
            Write-Host "❌ Test failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "🔐 Setting up Application Credentials (Recommended)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Application credentials are more secure than using your main password." -ForegroundColor White
        Write-Host "To create application credentials:" -ForegroundColor White
        Write-Host "1. Go to: https://pouta.csc.fi" -ForegroundColor Gray
        Write-Host "2. Navigate to Identity > Application Credentials" -ForegroundColor Gray
        Write-Host "3. Click 'Create Application Credential'" -ForegroundColor Gray
        Write-Host "4. Give it a name (e.g., 'data-pipeline-microservices')" -ForegroundColor Gray
        Write-Host "5. Copy the ID and Secret" -ForegroundColor Gray
        Write-Host ""
        
        $hasAppCreds = Read-Host "Do you have application credentials ready? (y/n)"
        
        if ($hasAppCreds -eq "y" -or $hasAppCreds -eq "Y") {
            $appCredId = Read-Host "Application Credential ID"
            $appCredSecret = Read-Host "Application Credential Secret" -AsSecureString
            $appCredSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($appCredSecret))
            $osProjectName = Read-Host "OS_PROJECT_NAME (e.g., project_2015319)"
            $dataBucket = Read-Host "DATA_BUCKET (container name, default: cloudservices)"
            
            if (-not $dataBucket) { $dataBucket = "cloudservices" }
            
            # Delete existing secret if it exists
            oc delete secret allas-credentials --ignore-not-found | Out-Null
            
            try {
                oc create secret generic allas-credentials `
                    --from-literal=OS_AUTH_URL=https://pouta.csc.fi:5001/v3 `
                    --from-literal=OS_APPLICATION_CREDENTIAL_ID=$appCredId `
                    --from-literal=OS_APPLICATION_CREDENTIAL_SECRET=$appCredSecretPlain `
                    --from-literal=OS_PROJECT_NAME=$osProjectName `
                    --from-literal=DATA_BUCKET=$dataBucket
                
                Write-Host "✅ Application credentials created successfully!" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Failed to create application credentials: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "Please create application credentials first, then run this script again." -ForegroundColor Yellow
        }
    }
    
    "6" {
        Write-Host ""
        Write-Host "🗑️  Deleting credentials..." -ForegroundColor Red
        
        $confirm = Read-Host "Are you sure you want to delete the credentials? (y/n)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            try {
                oc delete secret allas-credentials
                Write-Host "✅ Credentials deleted successfully!" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Failed to delete credentials: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "❌ Cancelled." -ForegroundColor Red
        }
    }
    
    "7" {
        Write-Host "👋 Goodbye!" -ForegroundColor Green
        exit 0
    }
    
    default {
        Write-Host "❌ Invalid option. Please select 1-7." -ForegroundColor Red
    }
}