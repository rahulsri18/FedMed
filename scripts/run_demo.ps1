# scripts/run_demo.ps1 - PowerShell Local Orchestration Runner for FedMed (Windows)
# Owner: M1 (Server & Orchestration Lead)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "           FedMed Cross-Silo FL Demo Runner (Windows)            " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$processes = @()

try {
    # 1. Start Server
    Write-Host "[1/6] Launching Central Flower Orchestrator (port 8080)..." -ForegroundColor Yellow
    $server = Start-Process python -ArgumentList "-m server.server --port 8080 --rounds 5 --encrypted" -PassThru
    $processes += $server
    Start-Sleep -Seconds 2

    # 2. Start FastAPI
    Write-Host "[2/6] Launching FastAPI Telemetry Service (port 8000)..." -ForegroundColor Yellow
    $api = Start-Process uvicorn -ArgumentList "api.main:app --host 0.0.0.0 --port 8000" -PassThru
    $processes += $api
    Start-Sleep -Seconds 1

    # 3. Start Hospital Node 1
    Write-Host "[3/6] Launching Hospital Node 1 (Aux Port 8081)..." -ForegroundColor Yellow
    $hosp1 = Start-Process python -ArgumentList "-m client.client --node-id 1 --port 8081" -PassThru
    $processes += $hosp1
    Start-Sleep -Seconds 1

    # 4. Start Hospital Node 2
    Write-Host "[4/6] Launching Hospital Node 2 (Aux Port 8082)..." -ForegroundColor Yellow
    $hosp2 = Start-Process python -ArgumentList "-m client.client --node-id 2 --port 8082" -PassThru
    $processes += $hosp2
    Start-Sleep -Seconds 1

    # 5. Start Hospital Node 3
    Write-Host "[5/6] Launching Hospital Node 3 (Aux Port 8083)..." -ForegroundColor Yellow
    $hosp3 = Start-Process python -ArgumentList "-m client.client --node-id 3 --port 8083" -PassThru
    $processes += $hosp3
    Start-Sleep -Seconds 1

    # 6. Start Dashboard
    Write-Host "[6/6] Launching Frontend Dashboard (port 3000)..." -ForegroundColor Yellow
    $dashboard = Start-Process npm -ArgumentList "run dev" -WorkingDirectory "dashboard" -PassThru
    $processes += $dashboard

    Write-Host "`n=================================================================" -ForegroundColor Green
    Write-Host "   All FedMed Services Running Successfully!" -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "   - Dashboard UI:       http://localhost:3000"
    Write-Host "   - API Documentation:  http://localhost:8000/docs"
    Write-Host "   - WebSocket Stream:   ws://localhost:8000/ws/telemetry"
    Write-Host "   - Flower Server:      localhost:8080"
    Write-Host "================================================================="
    Write-Host "Press Enter to stop all services..."

    Read-Host
}
finally {
    Write-Host "`n[FedMed Runner] Terminating background processes..." -ForegroundColor Yellow
    foreach ($p in $processes) {
        if ($p -and -not $p.HasExited) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[FedMed Runner] All processes terminated." -ForegroundColor Green
}
