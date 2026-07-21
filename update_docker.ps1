# Docker Desktop Update Script
Write-Host "========================================"
Write-Host "  Docker Desktop Update Tool"
Write-Host "========================================"
Write-Host ""

Write-Host "Checking current Docker version..."
docker --version 2>$null
Write-Host ""

Write-Host "[1/3] Downloading latest Docker Desktop..."
$outputPath = "$env:TEMP\DockerDesktopInstaller.exe"
$downloaded = $false
$urls = @(
    "https://docker.m.daocloud.io/desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe",
    "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
)

foreach ($url in $urls) {
    try {
        Write-Host "Trying: $url"
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $outputPath -TimeoutSec 300
        if ((Test-Path $outputPath) -and ((Get-Item $outputPath).Length -gt 1000000)) {
            $sizeMB = [math]::Round((Get-Item $outputPath).Length / 1MB, 1)
            Write-Host "[OK] Download complete ($sizeMB MB)"
            $downloaded = $true
            break
        }
    } catch {
        $msg = $_.Exception.Message
        if ($msg.Length -gt 60) { $msg = $msg.Substring(0, 60) }
        Write-Host "[FAIL] $msg"
    }
}

if (-not $downloaded) {
    Write-Host ""
    Write-Host "[!] Download failed!"
    Write-Host "Please try:"
    Write-Host "  1. Enable VPN/proxy and retry"
    Write-Host "  2. Download manually: https://docs.docker.com/desktop/install/windows-install/"
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "[2/3] Stopping Docker Desktop..."
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "com.docker.backend" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "com.docker.service" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "[3/3] Installing..."
Write-Host ""
Start-Process -FilePath $outputPath -ArgumentList "install", "--quiet" -Wait

Write-Host ""
Write-Host "========================================"
Write-Host "  [OK] Docker Desktop updated!"
Write-Host "========================================"
Write-Host ""
Write-Host "Starting Docker Desktop..."
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Write-Host ""
pause
