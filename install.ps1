# Agent Skills installer for Windows
# Supports: Claude Code, Codex CLI, OpenClaw
# Respects `platforms` field in SKILL.md frontmatter for per-skill filtering.
param(
    [switch]$Force,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$SkillsDir = Join-Path $PSScriptRoot "skills"

function Write-OK($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Skip($msg)  { Write-Host "[SKIP] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]  $msg" -ForegroundColor Red }

function Remove-Link {
    # Removes a junction/symlink without touching its target's contents.
    # Windows PowerShell 5.1 on current Win11 builds throws NullReferenceException
    # from `Remove-Item <reparse point> -Force`, so use Directory.Delete instead
    # (non-recursive: deletes only the reparse point itself).
    param([string]$Path)
    # Self-defense: refuse anything that isn't a reparse point, so a caller bug
    # can never turn this into deletion of a real directory.
    if (-not ((Get-Item $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Remove-Link: not a junction/symlink: $Path"
    }
    [System.IO.Directory]::Delete($Path)
}

function Uninstall-Skills {
    # No platform filtering here on purpose: remove any link we own, so links
    # left behind by an older `platforms` config also get cleaned up.
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
            Remove-Link $target
            Write-Host "  Removed: $skillName"
        } elseif (Test-Path $target) {
            Write-Host "  $skillName : not a junction, skipping (remove manually if needed)"
        }
    }
    Write-OK "$ToolName skills uninstalled"
}

function Test-SkillSupportsPlatform {
    # Reads `metadata.platforms` (space-separated string) from SKILL.md frontmatter;
    # per docs/skill-authoring.md §1 the key is an indented `platforms:` line and
    # may only appear under `metadata:`. No field = all platforms.
    # Top-level `platforms:` is the retired format and is deliberately ignored.
    param([string]$SkillDir, [string]$Platform)
    $skillFile = Join-Path $SkillDir "SKILL.md"
    if (-not (Test-Path $skillFile)) { return $true }
    $inFrontmatter = $false
    foreach ($line in Get-Content $skillFile) {
        if ($line -eq '---' -and -not $inFrontmatter) { $inFrontmatter = $true; continue }
        if ($line -eq '---' -and $inFrontmatter) { break }
        if ($inFrontmatter -and $line -match '^\s+platforms:\s*(.+)$') {
            # Exact list compare — substring matching would break with
            # prefix-overlapping platform names (e.g. "code" vs "claude-code")
            $list = ($Matches[1] -replace '"', '') -split '\s+' | Where-Object { $_ }
            return $list -contains $Platform
        }
    }
    return $true  # no platforms field → all platforms
}

function Install-Skills {
    param(
        [string]$TargetDir,
        [string]$ToolName,
        [string]$Platform
    )

    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }

    Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
        $skillName = $_.Name
        $source = $_.FullName
        $target = Join-Path $TargetDir $skillName

        if (-not (Test-SkillSupportsPlatform $source $Platform)) {
            Write-Host "  $skillName : not supported on $ToolName, skipping"
            return
        }

        # Remove existing junction/symlink
        if ((Test-Path $target) -and ((Get-Item $target).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Link $target
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

        # Junctions work across local volumes and need no privilege, so always
        # try one first. (The previous same-drive check was wrong: it routed
        # cross-drive installs to symlinks, which require Developer Mode/admin.)
        # Symlink remains a fallback for non-local sources (e.g. network share),
        # where junctions can't point. The stderr redirect must live inside cmd:
        # a PowerShell-side `2>$null` on a native command under EAP=Stop turns
        # stderr into a terminating NativeCommandError, making this fallback
        # chain unreachable.
        cmd /c "mklink /J ""$target"" ""$source"" 2>nul" | Out-Null
        if (-not (Test-Path $target)) {
            try {
                New-Item -ItemType SymbolicLink -Path $target -Target $source | Out-Null
            } catch {
                Write-Err "$skillName : link creation failed. Enable Developer Mode or run as admin."
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
Write-Host "=== Agent Skills Installer ==="
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
        Install-Skills -TargetDir $ClaudeSkills -ToolName "Claude Code" -Platform "claude-code"

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
        Install-Skills -TargetDir $CodexSkills -ToolName "Codex CLI" -Platform "codex"
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
        Install-Skills -TargetDir $OpenClawSkills -ToolName "OpenClaw" -Platform "openclaw"
    }
} else {
    Write-Skip "OpenClaw not found"
}

Write-Host ""
if ($Uninstall) {
    Write-OK "Uninstall complete"
} else {
    $skillList = (Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object { "/$($_.Name)" }) -join ", "
    Write-OK "Done. Skills in this repo: $skillList"
    Write-Host ""
    Write-Host "Per-tool availability is platform-filtered (see output above)."
    Write-Host "Usage of each skill: see README.md"
    Write-Host ""
    Write-Host "To uninstall: .\install.ps1 -Uninstall"
}
Write-Host ""
