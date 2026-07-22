<#
.SYNOPSIS
Incremental backup script for embodied intelligence project to J drive
#>

$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$sourceDir = $scriptDir

$backupRoot = "J:\embodied-intelligence-backup"
$hostsBackupDir = Join-Path $backupRoot "hosts"
$systemBackupDir = Join-Path $backupRoot "system"
$sysHosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$projHosts = Join-Path $scriptDir "hosts\hosts"

Write-Host "[J-BACKUP] Starting incremental backup to J drive..."

if (-not (Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot | Out-Null
    Write-Host "[J-BACKUP] Created backup root: $backupRoot"
}

if (-not (Test-Path $hostsBackupDir)) {
    New-Item -ItemType Directory -Path $hostsBackupDir | Out-Null
}

if (-not (Test-Path $systemBackupDir)) {
    New-Item -ItemType Directory -Path $systemBackupDir | Out-Null
}

$excludeDirs = @("env_isaacsim", "env_pybullet", "venv", ".venv", "env", "__pycache__", ".git", "node_modules")
$excludeExtensions = @(".tmp", ".bak", ".log", ".pyc", ".pyo", ".pyd", ".egg-info", ".egg")

Write-Host "[J-BACKUP] === Step 1: Hosts Backup ==="

try {
    Copy-Item -Path $sysHosts -Destination $hostsBackupDir -Force
    Write-Host "[J-BACKUP] Synced system hosts to J drive"
} catch {
    Write-Host "[J-BACKUP] Warning: Failed to sync system hosts: $_"
}

$currentHostsContent = Get-Content $hostsBackupDir\hosts -Raw -ErrorAction SilentlyContinue
if ($currentHostsContent) {
    $hostsBackupFilesDir = Join-Path $hostsBackupDir "backups"
    if (-not (Test-Path $hostsBackupFilesDir)) {
        New-Item -ItemType Directory -Path $hostsBackupFilesDir | Out-Null
    }
    
    $latestHostsBackup = Get-ChildItem -Path $hostsBackupFilesDir -Filter "hosts_*.bak" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    $hasHostsChange = $true
    if ($latestHostsBackup) {
        $backupHostsContent = Get-Content $latestHostsBackup.FullName -Raw -ErrorAction SilentlyContinue
        if ($backupHostsContent -eq $currentHostsContent) {
            $hasHostsChange = $false
        }
    }
    
    if ($hasHostsChange) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $hostsBackupFile = Join-Path $hostsBackupFilesDir "hosts_$timestamp.bak"
        $currentHostsContent | Out-File -FilePath $hostsBackupFile -Encoding UTF8 -NoNewline
        Write-Host "[J-BACKUP] Created hosts backup: hosts_$timestamp.bak"
    } else {
        Write-Host "[J-BACKUP] No hosts changes, skipping hosts backup"
    }
}

Write-Host "[J-BACKUP] === Step 2: System Backup ==="

$allFiles = @()
Get-ChildItem -Path $sourceDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    $file = $_
    $include = $true
    
    foreach ($dir in $excludeDirs) {
        if ($file.FullName -like "*\$dir\*") {
            $include = $false
            break
        }
    }
    
    if ($include) {
        foreach ($ext in $excludeExtensions) {
            if ($file.Extension -eq $ext) {
                $include = $false
                break
            }
        }
    }
    
    if ($include) {
        $allFiles += $file
    }
}

$hashFile = Join-Path $systemBackupDir "file_hashes.json"
$previousHashes = @{}

if (Test-Path $hashFile) {
    $jsonObj = Get-Content $hashFile -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($jsonObj -and $jsonObj -isnot [string]) {
        $jsonObj.PSObject.Properties | ForEach-Object {
            $previousHashes[$_.Name] = $_.Value
        }
    }
}

$currentHashes = @{}
$changedFiles = @()

foreach ($file in $allFiles) {
    $relativePath = $file.FullName.Substring($sourceDir.Length + 1)
    $fileHash = (Get-FileHash $file.FullName -Algorithm MD5).Hash
    $currentHashes[$relativePath] = $fileHash
    
    if (-not $previousHashes.ContainsKey($relativePath) -or $previousHashes[$relativePath] -ne $fileHash) {
        $changedFiles += $file
    }
}

if ($changedFiles.Count -eq 0) {
    Write-Host "[J-BACKUP] No system changes, skipping system backup"
} else {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $currentBackupDir = Join-Path $systemBackupDir "backup_$timestamp"
    New-Item -ItemType Directory -Path $currentBackupDir | Out-Null
    
    $copiedCount = 0
    $totalSize = 0
    foreach ($file in $changedFiles) {
        $relativePath = $file.FullName.Substring($sourceDir.Length + 1)
        $targetPath = Join-Path $currentBackupDir $relativePath
        $targetDir = Split-Path -Parent $targetPath
        
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        $copiedCount++
        $totalSize += $file.Length
    }
    
    $currentHashes | ConvertTo-Json -Depth 100 | Out-File -FilePath $hashFile -Encoding UTF8
    
    $backupInfo = @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        source = $sourceDir
        backup_path = $currentBackupDir
        file_count = $copiedCount
        total_size_bytes = $totalSize
        total_size_human = "{0:N2} MB" -f ($totalSize / 1MB)
        total_files_in_project = $allFiles.Count
    }
    
    $backupInfo | ConvertTo-Json | Out-File -FilePath (Join-Path $currentBackupDir "backup_info.json") -Encoding UTF8
    
    Write-Host "[J-BACKUP] Created system backup: backup_$timestamp"
    Write-Host "[J-BACKUP] Files copied: $copiedCount (total project files: $($allFiles.Count))"
    Write-Host ("[J-BACKUP] Total size: {0:N2} MB" -f ($totalSize / 1MB))
}

Write-Host "[J-BACKUP] === Done ==="
Write-Host "[J-BACKUP] Backup location: $backupRoot"
