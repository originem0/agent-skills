# Agent Skills

我的 AI 编码助手技能集合。使用 [Agent Skills 开放标准](https://agentskills.io/)（SKILL.md 格式）。

## 支持的工具

| 工具 | Skills 目录 | 链接方式 |
|------|------------|---------|
| [Claude Code](https://claude.ai/code) | `~/.claude/skills/` | symlink / junction |
| [Codex CLI](https://github.com/openai/codex) | `~/.codex/skills/` | symlink / junction |
| [OpenClaw](https://github.com/openclaw/openclaw) | `~/.openclaw/skills/` | symlink / junction |

> **注意：** Skills 指令主要针对 Claude Code 测试。其他工具可加载 SKILL.md，但行为可能有差异。

## 安装

### Windows (PowerShell)

```powershell
git clone <your-repo-url>
cd agent-skills
.\install.ps1
```

### macOS / Linux

```bash
git clone <your-repo-url>
cd agent-skills
chmod +x install.sh
./install.sh
```

安装脚本自动检测已安装的工具，用 symlink/junction 链接。`git pull` 后技能自动更新。新增、删除或改名技能后重跑安装脚本即可——指向本仓库但目标已不存在的残留链接会被自动清理（不碰其他来源的链接）。

跨盘符时（如 repo 在 D: 而 .claude 在 C:），PowerShell 版会自动降级为 symlink 或 copy。

### 卸载

```powershell
.\install.ps1 -Uninstall     # Windows
./install.sh --uninstall      # macOS / Linux
```

### 手动安装

把 `skills/` 下的目录复制到对应工具的 skills 目录即可。

---

## 技能列表

### PERO 学习系统

用 AI 辅助深度学习。AI 不是讲师，是认知镜——让你的思维对自己可见，通过探测和挑战帮你构建可迁移的解释模型。

| 技能 | 用途 |
|------|------|
| `/pero-learn` | 教学模式：Priming → Encoding → Reference → Retrieval 四阶段引导学习。掌握以跨会话检索为准（概念检索表），概念性/程序性知识分流起手，含校准循环与抗索答护栏 |
| `/pero-feynman` | 检验模式：扮演较真的学生检验你是否真懂了。基于检索表与薄弱点制定攻击计划，含自信错误陈述攻击与校准差距报告 |

用法：`cd 到学习项目目录` → 启动工具 → `/pero-learn`

### 网页抓取

| 技能 | 用途 |
|------|------|
| `/crawl4ai-scraper` | 本地免费爬虫：Crawl4AI，核心功能无需 API Key，支持单页/深度爬取、CSS/XPath/LLM 结构化提取 |

云端抓取（Firecrawl）用官方 skill，见下方「不在本仓库维护的 skill」。

### 英语词族

| 技能 | 用途 |
|------|------|
| `/word-family` | 给一个单词/词根/日常场景，查实词源（etymology）后生成一页「日常锚点 → 母画面 → 换方向铺开词族」的线稿网页课，含自测模式与迁移题。详见 `skills/word-family/使用说明.md` |

依赖 Python 3.10+、Chrome/Edge（截图自检）；词源优先经 firecrawl 抓 etymonline（需登录），否则退回 Wiktionary。

### 不在本仓库维护的 skill

上游工具自带 skill 时由上游安装，本仓库不保留副本（见 `docs/skill-authoring.md` §4）：

- **widget-viewer**（生成式 UI，WebView2 渲染 HTML widget）：随 [claude-widget-viewer](https://github.com/originem0/claude-widget-viewer) 的 `install.ps1` 安装。
- **Firecrawl**：`firecrawl setup core -g` 安装（只装 skills；裸 `firecrawl setup` 的 defaults 会禁用 Claude Code 原生 WebFetch/WebSearch）。本机只保留 `firecrawl-scrape`、`firecrawl-search`、`firecrawl-map`，其余用 `npx skills remove -g -y <name>` 删除——它们被链接进 ~20 个 agent 目录并记入 `~/.agents/.skill-lock.json`，不要手删。

---

## 添加新技能

在 `skills/` 下创建新目录，放入 `SKILL.md`，然后重跑安装脚本。技能可以携带子资源（模板、示例、脚本），按需加载：

```
skills/
├── pero-learn/          # claude-code only
├── pero-feynman/        # claude-code only
├── crawl4ai-scraper/
│   ├── SKILL.md
│   ├── gotchas.md
│   ├── examples/
│   └── scripts/
├── word-family/         # claude-code only
├── word-family-video/   # claude-code only
└── your-new-skill/
    └── SKILL.md         # 必需，其余可选
```

frontmatter 中可选的 `metadata.platforms` 字段控制技能安装到哪些工具，省略则安装到全部：

```yaml
---
name: my-skill
description: ...
metadata:
  platforms: claude-code   # 空格分隔多个；可选值：claude-code / codex / openclaw
---
```

完整规范见 [docs/skill-authoring.md](docs/skill-authoring.md)。

SKILL.md 格式参考 [Agent Skills 规范](https://agentskills.io/specification)。
