# PERO Skills installer for Windows
# Supports: Claude Code, Codex CLI, OpenClaw
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SkillsDir = Join-Path $PSScriptRoot "skills"

function Write-OK($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Skip($msg)  { Write-Host "[SKIP] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]  $msg" -ForegroundColor Red }

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

        # Remove existing symlink
        if ((Test-Path $target) -and ((Get-Item $target).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Item $target -Force
        }

        # Skip if real directory exists
        if (Test-Path $target) {
            if ($Force) {
                Remove-Item $target -Recurse -Force
            } else {
                Write-Host "  $skillName : already exists, use -Force to overwrite"
                return
            }
        }

        # Create directory junction (works without admin on Windows)
        cmd /c mklink /J "$target" "$source" | Out-Null
        Write-Host "  $skillName -> $target"
    }
    Write-OK "$ToolName skills installed"
}

Write-Host ""
Write-Host "=== PERO Skills Installer ==="
Write-Host ""

# Claude Code
$ClaudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if ((Get-Command claude -ErrorAction SilentlyContinue) -or (Test-Path $ClaudeDir)) {
    Write-Host "Claude Code detected"
    Install-Skills -TargetDir $ClaudeSkills -ToolName "Claude Code"

    # Clean up old commands format
    @("PEROlearn.md", "PEROfeynman.md") | ForEach-Object {
        $old = Join-Path $ClaudeDir "commands\$_"
        if (Test-Path $old) {
            Remove-Item $old -Force
            Write-Host "  Removed old command: $_"
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
    Install-Skills -TargetDir $CodexSkills -ToolName "Codex CLI"
} else {
    Write-Skip "Codex CLI not found"
}

Write-Host ""

# OpenClaw
$OpenClawSkills = Join-Path $env:USERPROFILE ".openclaw\skills"
$OpenClawDir = Join-Path $env:USERPROFILE ".openclaw"
if ((Get-Command openclaw -ErrorAction SilentlyContinue) -or (Test-Path $OpenClawDir)) {
    Write-Host "OpenClaw detected"
    Install-Skills -TargetDir $OpenClawSkills -ToolName "OpenClaw"
} else {
    Write-Skip "OpenClaw not found"
}

Write-Host ""
Write-OK "Done. Skills available: /PEROlearn, /PEROfeynman"
Write-Host ""
Write-Host "Usage:"
Write-Host "  1. cd to your learning project directory"
Write-Host "  2. Run /PEROlearn to start or continue learning"
Write-Host "  3. Run /PEROfeynman to test your understanding"
Write-Host ""
