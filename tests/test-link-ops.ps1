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

# 提取安装器真实的 mklink 调用行（而非在测试里复制一份），
# 保证用例 5-7 验证的就是 install.ps1 实际发货的写法。
if ($src -notmatch '(?m)^\s*(cmd /c "mklink /J ""\$target"" ""\$source"" 2>nul" \| Out-Null)\s*$') {
    Write-Host "EXTRACT FAIL: mklink invocation not found in install.ps1"; exit 1
}
$mklinkLine = $Matches[1]

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

# 3. 跨卷 junction 可创建且可解析（fixtures 在 TEMP 即系统盘，目标指向仓库所在卷；
#    两者同卷时退化为同卷用例，仍然有效。借用 skills/crawl4ai-scraper 作为真实
#    仓库卷目标——它是全平台 skill，预期长期存在）
cmd /c mklink /J "$link" "$RepoRoot\skills\crawl4ai-scraper" | Out-Null
Assert "junction 指向仓库卷可解析" (Test-Path (Join-Path $link "SKILL.md"))

# 4. 刷新循环：Remove-Link 后同名重建（安装器 idempotent 更新路径）
Remove-Link $link
cmd /c mklink /J "$link" "$fixtures\src" | Out-Null
Assert "删除后可重建（幂等刷新）" ((Get-Item $link).LinkType -eq "Junction" -and (Test-Path (Join-Path $link "sub\f.txt")))

# 5. mklink 失败（目标已被普通文件占据）在 EAP=Stop 下不得抛 terminating error——
#    否则 install.ps1 的 symlink/copy 降级链永远不可达。
#    回归背景：PowerShell 侧 `2>$null` 会把原生命令 stderr 变成 NativeCommandError，
#    EAP=Stop 使其直接终止脚本；重定向必须写在 cmd 内部（2>nul）。
$target = Join-Path $fixtures "blocked"
$source = "$fixtures\src"
Set-Content $target "occupied"
$reachedFallbackCheck = $false
try {
    Invoke-Expression $mklinkLine
    $reachedFallbackCheck = $true
} catch { }
Assert "mklink 失败不终止脚本（降级链可达）" $reachedFallbackCheck
Assert "失败后占位文件未被破坏" ((Get-Content $target) -eq "occupied")

# 6. 提取的真实调用行在正常路径下能建链（含空格路径，验证 cmd 内层引号写法）
$spacedSrc = Join-Path $fixtures "sp ace src"
New-Item -ItemType Directory -Path $spacedSrc | Out-Null
Set-Content (Join-Path $spacedSrc "g.txt") "y"
$target = Join-Path $fixtures "sp ace link"
$source = $spacedSrc
Invoke-Expression $mklinkLine
Assert "真实调用行可建链（含空格路径）" (Test-Path (Join-Path $target "g.txt"))
Remove-Link $target

# 7. Remove-Link 拒绝非 reparse point（自防御：不误删真实目录）
$realDir = Join-Path $fixtures "realdir"
New-Item -ItemType Directory -Path $realDir | Out-Null
$refused = $false
try { Remove-Link $realDir } catch { $refused = $true }
Assert "Remove-Link 拒绝真实目录" ($refused -and (Test-Path $realDir))

Remove-Link $link
Remove-Item $fixtures -Recurse -Force
Write-Host "failures: $failCount"
exit $failCount
