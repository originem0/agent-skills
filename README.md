# Agent Skills

我的 AI 编码助手技能集合。使用 [SKILL.md 开放标准](https://agents.md/)，跨平台适用。

## 支持的工具

- [Claude Code](https://claude.ai/code) — `~/.claude/skills/`
- [Codex CLI](https://github.com/openai/codex) — `~/.codex/skills/`
- [OpenClaw](https://github.com/openclaw/openclaw) — `~/.openclaw/skills/`

## 安装

### Windows (PowerShell)

```powershell
git clone https://github.com/YOUR_USERNAME/agent-skills.git
cd agent-skills
.\install.ps1
```

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/agent-skills.git
cd agent-skills
chmod +x install.sh
./install.sh
```

安装脚本自动检测已安装的工具，用 symlink/junction 链接。`git pull` 后技能自动更新，不需要重新安装。新增技能后重跑一次 `install.ps1` 即可。

### 手动安装

把 `skills/` 下的目录复制到对应工具的 skills 目录即可。

---

## 技能列表

### PERO 学习系统

用 AI 辅助学习技术知识。不是让 AI 讲课，而是让 AI 当教练，帮你自己构建知识的逻辑链。

| 技能 | 用途 |
|------|------|
| `/PEROlearn` | 教学模式：Priming → Encoding → Reference → Retrieval 四阶段引导学习 |
| `/PEROfeynman` | 检验模式：扮演刁钻学生检验你是否真懂了 |

用法：`cd 到学习项目目录` → 启动工具 → `/PEROlearn`

---

## 添加新技能

在 `skills/` 下创建新目录，放入 `SKILL.md`：

```
skills/
├── PEROlearn/
│   └── SKILL.md
├── PEROfeynman/
│   └── SKILL.md
└── your-new-skill/        ← 新建
    └── SKILL.md
```

SKILL.md 格式：

```markdown
---
name: your-skill-name
description: >
  一段描述，告诉 AI 什么时候该用这个技能。
---

# 技能标题

具体指令...
```

然后重跑 `install.ps1`（或 `install.sh`），新技能自动链接到所有工具。
