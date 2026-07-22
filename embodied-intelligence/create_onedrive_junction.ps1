# Create directory junction C:\Users\523\OneDrive -> E:\onedrive
# This fixes Windows Backup error: path not found for cached old OneDrive location
# Junction is transparent to apps and lets backup access the old cached path

$junctionPath = "C:\Users\523\OneDrive"
$targetPath = "E:\onedrive"

Write-Output "=== Creating OneDrive junction to fix backup path cache ==="

# Verify target exists
if (-not (Test-Path $targetPath)) {
    Write-Output "ERROR: Target path $targetPath does not exist!"
    exit 1
}
Write-Output "Target verified: $targetPath exists"

# Check if junction already exists
if (Test-Path $junctionPath) {
    $item = Get-Item $junctionPath -Force
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        Write-Output "Junction already exists at $junctionPath"
        $currentTarget = (Get-Item $junctionPath).Target
        Write-Output "Current target: $currentTarget"
        if ($currentTarget -eq $targetPath) {
            Write-Output "Junction is correct, no action needed"
            exit 0
        } else {
            Write-Output "Junction points to wrong target, removing..."
            Remove-Item $junctionPath -Force
        }
    } else {
        Write-Output "ERROR: $junctionPath exists as a real directory, not a junction!"
        Write-Output "Cannot create junction over existing directory"
        exit 1
    }
}

# Create the junction
try {
    New-Item -ItemType Junction -Path $junctionPath -Target $targetPath -ErrorAction Stop | Out-Null
    Write-Output "SUCCESS: Junction created"
    Write-Output "  $junctionPath -> $targetPath"
} catch {
    Write-Output "Failed to create junction via PowerShell: $_"
    Write-Output "Trying via cmd mklink..."
    $result = cmd /c "mklink /J `"$junctionPath`" `"$targetPath`"" 2>&1
    Write-Output "mklink result: $result"
}

# Verify junction
if (Test-Path $junctionPath) {
    $item = Get-Item $junctionPath -Force
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        Write-Output ""
        Write-Output "=== Verification ==="
        Write-Output "Junction path: $junctionPath"
        Write-Output "Attributes: $($item.Attributes)"
        $subItems = Get-ChildItem $junctionPath -ErrorAction SilentlyContinue | Select-Object -First 10 Name
        Write-Output "Contents accessible:"
        foreach ($s in $subItems) {
            Write-Output "  - $($s.Name)"
        }
        Write-Output ""
        Write-Output "=== Junction created successfully ==="
    } else {
        Write-Output "ERROR: Path exists but is not a junction"
    }
} else {
    Write-Output "ERROR: Junction was not created"
}
