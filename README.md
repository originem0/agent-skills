# Agent Skills

我的 AI 编码助手技能集合。使用 [SKILL.md 开放标准](https://agents.md/)。

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

安装脚本自动检测已安装的工具，用 symlink/junction 链接。`git pull` 后技能自动更新。新增技能后重跑安装脚本即可。

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
| `/PEROlearn` | 教学模式：Priming → Encoding → Reference → Retrieval 四阶段引导学习。支持陈述性/程序性知识自动判定，程序性知识含实践验证和内隐知识显性化 |
| `/PEROfeynman` | 检验模式：扮演较真的学生检验你是否真懂了。程序性知识含实践挑战 |

用法：`cd 到学习项目目录` → 启动工具 → `/PEROlearn`

### 网页抓取

用 AI 助手直接抓取网页、提取数据。两个技能覆盖免费和云端两种场景。

| 技能 | 用途 |
|------|------|
| `/crawl4ai-scraper` | 本地免费爬虫：Crawl4AI，无需 API Key，支持单页/深度爬取、CSS/LLM 结构化提取 |
| `/firecrawl-scraper` | 云端爬虫：Firecrawl CLI，开箱即用，内置代理和反爬，支持搜索/浏览器自动化 |

选择指南：
- 免费、本地、隐私优先 → `crawl4ai-scraper`
- 快速、云端、不折腾 → `firecrawl-scraper`（免费 500 credits/月）

---

## 添加新技能

在 `skills/` 下创建新目录，放入 `SKILL.md`，然后重跑安装脚本。

```
skills/
├── PEROlearn/
│   └── SKILL.md
├── PEROfeynman/
│   └── SKILL.md
├── crawl4ai-scraper/
│   └── SKILL.md
├── firecrawl-scraper/
│   └── SKILL.md
└── your-new-skill/
    └── SKILL.md
```

SKILL.md 格式参考 [agents.md 标准](https://agents.md/)。
