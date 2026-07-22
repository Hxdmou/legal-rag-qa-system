<#
.SYNOPSIS
Incremental backup script for hosts file
#>

$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$sysHosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$projHosts = Join-Path $scriptDir "hosts"
$backupDir = Join-Path $scriptDir "backups"

Write-Host "[BACKUP] Starting incremental backup..."

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "[BACKUP] Created backup directory: $backupDir"
}

try {
    Write-Host "[BACKUP] Syncing system hosts to project..."
    Copy-Item -Path $sysHosts -Destination $projHosts -Force
} catch {
    Write-Host "[BACKUP] Warning: Failed to sync system hosts: $_"
}

$currentContent = Get-Content $projHosts -Raw -ErrorAction SilentlyContinue
if (-not $currentContent) {
    Write-Host "[BACKUP] Error: Cannot read project hosts file"
    exit 1
}

$hasDifference = $true
$latestBackup = Get-ChildItem -Path $backupDir -Filter "hosts_*.bak" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestBackup) {
    $backupContent = Get-Content $latestBackup.FullName -Raw -ErrorAction SilentlyContinue
    if ($backupContent -eq $currentContent) {
        $hasDifference = $false
    }
}

if ($hasDifference) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $backupDir "hosts_$timestamp.bak"
    $currentContent | Out-File -FilePath $backupFile -Encoding UTF8 -NoNewline
    Write-Host "[BACKUP] Created backup: $backupFile"
} else {
    Write-Host "[BACKUP] No changes detected, skipping backup"
}

$backupCount = (Get-ChildItem -Path $backupDir -Filter "hosts_*.bak" -ErrorAction SilentlyContinue).Count
Write-Host "[BACKUP] Done! Total backups: $backupCount"
