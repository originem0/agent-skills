# install.ps1 平台过滤函数的单元测试（metadata.platforms 格式）。
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1
# 退出码 = 失败用例数。
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$src = Get-Content (Join-Path $RepoRoot "install.ps1") -Raw
if ($src -notmatch '(?s)(function Test-SkillSupportsPlatform \{.*?\n\})') {
    Write-Host "EXTRACT FAIL: function not found in install.ps1"; exit 1
}
Invoke-Expression $Matches[1]

$fixtures = Join-Path ([System.IO.Path]::GetTempPath()) ("skilltest-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixtures | Out-Null

function New-Fixture([string]$name, [string[]]$fm) {
    $dir = Join-Path $fixtures $name
    New-Item -ItemType Directory -Path $dir | Out-Null
    @('---') + $fm + @('---', '# body') | Set-Content (Join-Path $dir "SKILL.md")
    return $dir
}

$single  = New-Fixture "single"  @('name: a', 'metadata:', '  platforms: claude-code')
$multi   = New-Fixture "multi"   @('name: b', 'metadata:', '  platforms: claude-code codex')
$quoted  = New-Fixture "quoted"  @('name: c', 'metadata:', '  platforms: "codex"')
$nofield = New-Fixture "nofield" @('name: d')
$legacy  = New-Fixture "legacy"  @('name: e', 'platforms: [claude-code]')

$cases = @(
    @("单平台命中",                 $single,  "claude-code", $true),
    @("单平台拒绝其他",             $single,  "codex",       $false),
    @("前缀重叠不误匹配",           $single,  "code",        $false),
    @("多平台命中第二项",           $multi,   "codex",       $true),
    @("带引号的值命中",             $quoted,  "codex",       $true),
    @("无字段=全平台",              $nofield, "openclaw",    $true),
    @("废弃的顶层格式被忽略=全平台", $legacy,  "codex",       $true),
    @("PEROlearn 装 claude-code",   (Join-Path $RepoRoot "skills/PEROlearn"),        "claude-code", $true),
    @("PEROlearn 不装 codex",       (Join-Path $RepoRoot "skills/PEROlearn"),        "codex",       $false),
    @("crawl4ai 全平台",            (Join-Path $RepoRoot "skills/crawl4ai-scraper"), "codex",       $true)
)
$failCount = 0
foreach ($c in $cases) {
    $got = Test-SkillSupportsPlatform $c[1] $c[2]
    if ($got -eq $c[3]) { Write-Host "PASS $($c[0])" }
    else { Write-Host "FAIL $($c[0]) (got $got want $($c[3]))"; $failCount++ }
}
Remove-Item $fixtures -Recurse -Force
Write-Host "failures: $failCount"
exit $failCount
