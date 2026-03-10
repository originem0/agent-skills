# PERO Skills installer for Windows
# Supports: Claude Code, Codex CLI, OpenClaw
param(
    [switch]$Force,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$SkillsDir = Join-Path $PSScriptRoot "skills"

function Write-OK($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Skip($msg)  { Write-Host "[SKIP] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]  $msg" -ForegroundColor Red }

function Test-SameDrive {
    param([string]$Path1, [string]$Path2)
    $root1 = [System.IO.Path]::GetPathRoot($Path1)
    $root2 = [System.IO.Path]::GetPathRoot($Path2)
    return $root1 -eq $root2
}

function Uninstall-Skills {
    param(
        [string]$TargetDir,
        [string]$ToolName
    )

    if (-not (Test-Path $TargetDir)) {
        Write-Skip "$ToolName skills directory not found"
        return
    }

    Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
        $skillName = $_.Name
        $target = Join-Path $TargetDir $skillName

        if ((Test-Path $target) -and ((Get-Item $target).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Item $target -Force
            Write-Host "  Removed: $skillName"
        } elseif (Test-Path $target) {
            Write-Host "  $skillName : not a junction, skipping (remove manually if needed)"
        }
    }
    Write-OK "$ToolName skills uninstalled"
}

function Install-Skills {
    param(
        [string]$TargetDir,
        [string]$ToolName
    )

    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }

    Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
        $skillName = $_.Name
        $source = $_.FullName
        $target = Join-Path $TargetDir $skillName

        # Remove existing junction/symlink
        if ((Test-Path $target) -and ((Get-Item $target).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Item $target -Force
            Write-Host "  $skillName : updating link"
        }

        # Handle existing real directory
        if (Test-Path $target) {
            if ($Force) {
                Write-Host "  $skillName : overwriting existing directory (-Force)"
                Remove-Item $target -Recurse -Force
            } else {
                Write-Host "  $skillName : real directory exists, skipping (use -Force to overwrite)"
                return
            }
        }

        # Choose link type: junction for same drive, symlink for cross-drive
        if (Test-SameDrive $source $TargetDir) {
            cmd /c mklink /J "$target" "$source" | Out-Null
        } else {
            # Junction doesn't work across drives; use directory symlink
            # Requires Developer Mode or elevated privileges
            try {
                New-Item -ItemType SymbolicLink -Path $target -Target $source | Out-Null
            } catch {
                Write-Err "$skillName : cross-drive symlink failed. Enable Developer Mode or run as admin."
                Write-Host "  Falling back to copy (won't auto-update with git pull)..."
                Copy-Item -Path $source -Destination $target -Recurse
                return
            }
        }
        Write-Host "  $skillName -> $target"
    }
    Write-OK "$ToolName skills installed"
}

Write-Host ""
Write-Host "=== PERO Skills Installer ==="
Write-Host ""

if ($Uninstall) {
    Write-Host "Mode: uninstall"
    Write-Host ""
}

# Claude Code
$ClaudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if ((Get-Command claude -ErrorAction SilentlyContinue) -or (Test-Path $ClaudeDir)) {
    Write-Host "Claude Code detected"
    if ($Uninstall) {
        Uninstall-Skills -TargetDir $ClaudeSkills -ToolName "Claude Code"
    } else {
        Install-Skills -TargetDir $ClaudeSkills -ToolName "Claude Code"

        # Clean up old commands format (with confirmation)
        @("PEROlearn.md", "PEROfeynman.md") | ForEach-Object {
            $old = Join-Path $ClaudeDir "commands\$_"
            if (Test-Path $old) {
                $reply = Read-Host "  Found old command format: $_. Remove? [y/N]"
                if ($reply -eq 'y' -or $reply -eq 'Y') {
                    Remove-Item $old -Force
                    Write-Host "  Removed: $_"
                }
            }
        }
    }
} else {
    Write-Skip "Claude Code not found"
}

Write-Host ""

# Codex CLI
$CodexSkills = Join-Path $env:USERPROFILE ".codex\skills"
$CodexDir = Join-Path $env:USERPROFILE ".codex"
if ((Get-Command codex -ErrorAction SilentlyContinue) -or (Test-Path $CodexDir)) {
    Write-Host "Codex CLI detected"
    if ($Uninstall) {
        Uninstall-Skills -TargetDir $CodexSkills -ToolName "Codex CLI"
    } else {
        Install-Skills -TargetDir $CodexSkills -ToolName "Codex CLI"
    }
} else {
    Write-Skip "Codex CLI not found"
}

Write-Host ""

# OpenClaw
$OpenClawSkills = Join-Path $env:USERPROFILE ".openclaw\skills"
$OpenClawDir = Join-Path $env:USERPROFILE ".openclaw"
if ((Get-Command openclaw -ErrorAction SilentlyContinue) -or (Test-Path $OpenClawDir)) {
    Write-Host "OpenClaw detected"
    if ($Uninstall) {
        Uninstall-Skills -TargetDir $OpenClawSkills -ToolName "OpenClaw"
    } else {
        Install-Skills -TargetDir $OpenClawSkills -ToolName "OpenClaw"
    }
} else {
    Write-Skip "OpenClaw not found"
}

Write-Host ""
if ($Uninstall) {
    Write-OK "Uninstall complete"
} else {
    Write-OK "Done. Skills available: /PEROlearn, /PEROfeynman"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  1. cd to your learning project directory"
    Write-Host "  2. Run /PEROlearn to start or continue learning"
    Write-Host "  3. Run /PEROfeynman to test your understanding"
    Write-Host ""
    Write-Host "To uninstall: .\install.ps1 -Uninstall"
}
Write-Host ""
