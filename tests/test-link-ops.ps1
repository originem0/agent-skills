# install.ps1 链接操作的单元测试（junction 创建/删除，Windows-only，无 bash 对应）。
# 背景：PS 5.1 在新版 Win11 上 Remove-Item 删 reparse point 会抛 NullReferenceException，
# 且 junction 本就支持跨本地卷、无需特权——install.ps1 据此使用 Remove-Link + 无条件 mklink /J。
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-link-ops.ps1
# 退出码 = 失败用例数。
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$src = Get-Content (Join-Path $RepoRoot "install.ps1") -Raw
if ($src -notmatch '(?s)(function Remove-Link \{.*?\n\})') {
    Write-Host "EXTRACT FAIL: Remove-Link not found in install.ps1"; exit 1
}
Invoke-Expression $Matches[1]

$fixtures = Join-Path ([System.IO.Path]::GetTempPath()) ("linktest-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path "$fixtures\src\sub" | Out-Null
Set-Content (Join-Path $fixtures "src\sub\f.txt") "payload"
$link = Join-Path $fixtures "link"

$failCount = 0
function Assert([string]$name, [bool]$cond) {
    if ($cond) { Write-Host "PASS $name" }
    else { Write-Host "FAIL $name"; $script:failCount++ }
}

# 1. Remove-Link 删除 junction 本身（PS 5.1 下 Remove-Item -Force 会抛 NullReferenceException 的场景）
cmd /c mklink /J "$link" "$fixtures\src" | Out-Null
Remove-Link $link
Assert "Remove-Link 删除 junction" (-not (Test-Path $link))

# 2. 删除链接不伤及目标内容
Assert "目标内容完好" (Test-Path (Join-Path $fixtures "src\sub\f.txt"))

# 3. 跨卷 junction 可创建且可解析（fixtures 在 TEMP，目标指向仓库所在卷；
#    两者同卷时退化为同卷用例，仍然有效）
cmd /c mklink /J "$link" "$RepoRoot\skills\crawl4ai-scraper" | Out-Null
Assert "junction 指向仓库卷可解析" (Test-Path (Join-Path $link "SKILL.md"))

# 4. 刷新循环：Remove-Link 后同名重建（安装器 idempotent 更新路径）
Remove-Link $link
cmd /c mklink /J "$link" "$fixtures\src" | Out-Null
Assert "删除后可重建（幂等刷新）" ((Get-Item $link).LinkType -eq "Junction" -and (Test-Path (Join-Path $link "sub\f.txt")))

Remove-Link $link
Remove-Item $fixtures -Recurse -Force
Write-Host "failures: $failCount"
exit $failCount
