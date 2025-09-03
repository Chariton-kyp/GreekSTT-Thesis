# PowerShell script to start all GreekSTT services

Write-Host "🚀 Starting GreekSTT Comparison Platform - All Services" -ForegroundColor Cyan

# Start infrastructure first
Write-Host "📦 Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d db redis pgadmin mailhog

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start infrastructure services" -ForegroundColor Red
    exit 1
}

# Wait a bit for services to initialize
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start backend service
Write-Host "🔧 Starting backend service..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start backend service" -ForegroundColor Red
    exit 1
}

# Check if GPU is available and start appropriate AI service
Write-Host "🔍 Checking for GPU availability..." -ForegroundColor Yellow
try {
    nvidia-smi 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🚀 GPU detected - starting AI service with GPU support..." -ForegroundColor Green
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d ai-gpu
    } else {
        throw "No GPU"
    }
} catch {
    Write-Host "💻 No GPU detected - starting AI service with CPU only..." -ForegroundColor Yellow
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d ai-cpu
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start AI service" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "   Frontend (Angular): http://localhost:4200 (start manually with: npm run dev:frontend)" -ForegroundColor White
Write-Host "   Backend API: http://localhost:5001" -ForegroundColor White
Write-Host "   AI Service: http://localhost:8000" -ForegroundColor White
Write-Host "   PgAdmin: http://localhost:5050 (admin@greekstt.research/admin)" -ForegroundColor White
Write-Host "   MailHog: http://localhost:8025" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Debug Ports:" -ForegroundColor Cyan
Write-Host "   Backend Debugpy: localhost:5678" -ForegroundColor White
Write-Host "   AI Service Debugpy: localhost:5679" -ForegroundColor White
Write-Host ""
Write-Host "📊 Check status with: docker-compose ps" -ForegroundColor Yellow
Write-Host "📋 View logs with: docker-compose logs -f [service_name]" -ForegroundColor Yellow