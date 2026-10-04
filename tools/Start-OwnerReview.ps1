$ErrorActionPreference = 'Stop'
$reviewRoot = Split-Path -Parent $PSScriptRoot
$reviewPython = Join-Path $reviewRoot '.venv\Scripts\python.exe'
$reviewScript = Join-Path $PSScriptRoot 'owner_review.py'
if (-not (Test-Path -LiteralPath (Join-Path $reviewRoot '.owner-review\configuration.json'))) {
    & $reviewPython -B $reviewScript init
    if ($LASTEXITCODE -ne 0) { throw 'Owner review initialization failed.' }
}
& $reviewPython -B $reviewScript verify
if ($LASTEXITCODE -ne 0) { throw 'Owner review identity verification failed.' }
foreach ($reviewPort in @(8140, 3140)) {
    $reviewListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $reviewPort)
    try { $reviewListener.Start() } catch { throw "Port $reviewPort is occupied. Existing processes were left untouched." } finally { $reviewListener.Stop() }
}
if (-not (Test-Path -LiteralPath (Join-Path $reviewRoot 'frontend\.next\BUILD_ID'))) { throw 'Run npm.cmd run build from frontend first.' }
$reviewOldBackend = $env:AXYREL_BACKEND_URL
$reviewOldOrigin = $env:AXYREL_FRONTEND_ORIGIN
$reviewBackend = $null
$reviewServer = $null
Push-Location (Join-Path $reviewRoot 'frontend')
try {
    $reviewBackend = Start-Process -FilePath $reviewPython -ArgumentList @('-B', "`"$reviewScript`"", 'serve') -WorkingDirectory $reviewRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $reviewRoot '.owner-review\backend.stdout.log') -RedirectStandardError (Join-Path $reviewRoot '.owner-review\backend.stderr.log')
    $reviewReady = $false
    for ($reviewAttempt = 0; $reviewAttempt -lt 30; $reviewAttempt++) {
        if ($reviewBackend.HasExited) { throw 'Review backend failed to start. Check .owner-review/backend.stderr.log.' }
        try { $reviewHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8140/health' -TimeoutSec 1; $reviewReady = $true; break } catch { Start-Sleep -Milliseconds 300 }
    }
    if (-not $reviewReady) { throw 'Review backend did not become ready.' }
    $reviewPortOwner = Get-NetTCPConnection -LocalPort 8140 -State Listen -ErrorAction Stop
    $reviewProcessId = [int]$reviewPortOwner.OwningProcess
    $reviewOriginalId = $reviewProcessId
    for ($reviewDepth = 0; $reviewDepth -lt 8 -and $reviewProcessId -ne $reviewBackend.Id; $reviewDepth++) {
        $reviewProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $reviewProcessId" -ErrorAction Stop
        if (-not $reviewProcess) { break }
        $reviewProcessId = [int]$reviewProcess.ParentProcessId
    }
    if ($reviewBackend.HasExited -or $reviewProcessId -ne $reviewBackend.Id) { throw 'Review port identity is ambiguous. Refusing to start the frontend.' }
    $reviewServer = Get-Process -Id $reviewOriginalId -ErrorAction Stop
    $env:AXYREL_BACKEND_URL = 'http://127.0.0.1:8140'
    $env:AXYREL_FRONTEND_ORIGIN = 'http://127.0.0.1:3140'
    Write-Host 'Owner review: http://127.0.0.1:3140/login'
    Write-Host 'Credentials: .owner-review/credentials.txt. Ctrl+C stops servers; records/images are retained.'
    & npm.cmd run start -- --port 3140
} finally {
    if ($reviewServer -and -not $reviewServer.HasExited) { Stop-Process -Id $reviewServer.Id }
    if ($reviewBackend -and -not $reviewBackend.HasExited) { Stop-Process -Id $reviewBackend.Id }
    $env:AXYREL_BACKEND_URL = $reviewOldBackend
    $env:AXYREL_FRONTEND_ORIGIN = $reviewOldOrigin
    Pop-Location
}
