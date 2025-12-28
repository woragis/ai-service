# PowerShell script to test AI Service locally in Docker

Write-Host "🚀 Testing AI Service locally in Docker..." -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  No .env file found. Creating from env.sample..." -ForegroundColor Yellow
    if (Test-Path env.sample) {
        Copy-Item env.sample .env
        Write-Host "📝 Please edit .env file with your API keys" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "❌ No env.sample file found. Cannot proceed." -ForegroundColor Red
        exit 1
    }
}

# Build Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
docker build -t ai-service:local .

# Remove existing container if it exists
if (docker ps -a --format "{{.Names}}" | Select-String -Pattern "ai-service-test") {
    Write-Host "🧹 Removing existing container..." -ForegroundColor Yellow
    docker rm -f ai-service-test
}

# Run container
Write-Host "🏃 Starting container..." -ForegroundColor Cyan
docker run -d `
    --name ai-service-test `
    -p 8000:8000 `
    --env-file .env `
    -e ENV=development `
    -e LOG_LEVEL=info `
    -e CORS_ENABLED=true `
    -e CORS_ALLOWED_ORIGINS=* `
    ai-service:local

# Wait for service to be ready
Write-Host "⏳ Waiting for service to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Health check
Write-Host "🏥 Checking health..." -ForegroundColor Cyan
$maxRetries = 10
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Service is healthy!" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        $retryCount++
        if ($retryCount -eq $maxRetries) {
            Write-Host "❌ Service failed to start" -ForegroundColor Red
            docker logs ai-service-test
            docker rm -f ai-service-test
            exit 1
        }
        Start-Sleep -Seconds 2
    }
}

# Test endpoints
Write-Host "🧪 Testing endpoints..." -ForegroundColor Cyan

# Test health endpoint
Write-Host "  - Testing /healthz..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/healthz"
    $health | ConvertTo-Json -Depth 3
} catch {
    Write-Host "  ⚠️  Health check failed: $_" -ForegroundColor Yellow
}

# Test agents endpoint
Write-Host "  - Testing /v1/agents..." -ForegroundColor Yellow
try {
    $agents = Invoke-RestMethod -Uri "http://localhost:8000/v1/agents"
    $agents | ConvertTo-Json
} catch {
    Write-Host "  ⚠️  Agents endpoint failed: $_" -ForegroundColor Yellow
}

# Test metrics endpoint
Write-Host "  - Testing /metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    $metrics.Content.Split("`n")[0..19] | ForEach-Object { Write-Host $_ }
} catch {
    Write-Host "  ⚠️  Metrics endpoint failed: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Service is running!" -ForegroundColor Green
Write-Host "📍 Access at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Metrics at: http://localhost:8000/metrics" -ForegroundColor Cyan
Write-Host "🏥 Health at: http://localhost:8000/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop: docker rm -f ai-service-test" -ForegroundColor Yellow
Write-Host "To view logs: docker logs -f ai-service-test" -ForegroundColor Yellow

