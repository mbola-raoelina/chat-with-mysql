# Ollama Model Setup Script for Windows
# This script downloads the recommended models for the Secure AI SQL Chat application

Write-Host "Secure AI SQL Chat - Model Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if Ollama is installed
Write-Host "`nChecking if Ollama is installed..." -ForegroundColor Yellow
if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Ollama not found!" -ForegroundColor Red
    Write-Host "`nPlease install Ollama first:" -ForegroundColor Cyan
    Write-Host "   Visit: https://ollama.ai/download" -ForegroundColor Cyan
    Write-Host "   Or run: winget install Ollama.Ollama" -ForegroundColor Cyan
    Write-Host "`nAfter installation, restart your terminal and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "SUCCESS: Ollama found!" -ForegroundColor Green

# Check if Ollama service is running
Write-Host "`nChecking if Ollama service is running..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5
    Write-Host "SUCCESS: Ollama service is running!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Ollama service not running. Starting Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 10
    
    # Check again
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5
        Write-Host "SUCCESS: Ollama service started successfully!" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to start Ollama service!" -ForegroundColor Red
        Write-Host "Please start Ollama manually: ollama serve" -ForegroundColor Yellow
        exit 1
    }
}

# Define recommended models
$recommendedModels = @(
    @{name="sqlcoder:15b"; description="SQL-optimized model (~9GB)"},
    @{name="deepseek-coder:33b"; description="Code generation model (~18GB)"},
    @{name="codellama:13b-instruct"; description="General coding model (~7.4GB)"},
    @{name="llama3:latest"; description="General purpose model (~4.7GB)"}
)

# Check existing models
Write-Host "`nChecking existing models..." -ForegroundColor Yellow
try {
    $existingModels = (Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET).models | ForEach-Object { $_.name }
    Write-Host "SUCCESS: Found existing models: $($existingModels -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "INFO: No existing models found." -ForegroundColor Cyan
    $existingModels = @()
}

# Download missing models
Write-Host "`nDownloading recommended models..." -ForegroundColor Yellow
$totalModels = $recommendedModels.Count
$downloadedCount = 0

foreach ($model in $recommendedModels) {
    $modelName = $model.name
    $description = $model.description
    
    if ($existingModels -contains $modelName) {
        Write-Host "SUCCESS: $modelName already installed" -ForegroundColor Green
        $downloadedCount++
    } else {
        Write-Host "`nDownloading $modelName ($description)..." -ForegroundColor Cyan
        Write-Host "This may take 5-30 minutes depending on your internet speed..." -ForegroundColor Yellow
        
        try {
            $process = Start-Process -FilePath "ollama" -ArgumentList "pull", $modelName -Wait -PassThru -NoNewWindow
            
            if ($process.ExitCode -eq 0) {
                Write-Host "SUCCESS: $modelName downloaded successfully!" -ForegroundColor Green
                $downloadedCount++
            } else {
                Write-Host "ERROR: Failed to download $modelName" -ForegroundColor Red
            }
        } catch {
            Write-Host "ERROR: Error downloading $modelName`: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Summary
Write-Host "`nDownload Summary:" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host "Total recommended models: $totalModels" -ForegroundColor Cyan
Write-Host "Successfully downloaded: $downloadedCount" -ForegroundColor Green
Write-Host "Already installed: $($totalModels - $downloadedCount)" -ForegroundColor Cyan

if ($downloadedCount -eq $totalModels) {
    Write-Host "`nSUCCESS: All models are ready!" -ForegroundColor Green
    Write-Host "You can now run the Secure AI SQL Chat application:" -ForegroundColor Cyan
    Write-Host "   streamlit run secure_app_with_model_selection.py" -ForegroundColor White
} else {
    Write-Host "`nWARNING: Some models failed to download." -ForegroundColor Yellow
    Write-Host "You can still run the app with available models." -ForegroundColor Cyan
    Write-Host "To retry downloading, run: ollama pull model_name" -ForegroundColor Cyan
}

Write-Host "`nFor more information, see the documentation in the project folder." -ForegroundColor Cyan
Write-Host "Happy secure SQL chatting!" -ForegroundColor Green 