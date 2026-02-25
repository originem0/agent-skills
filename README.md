# PERO Skills

PERO (Priming → Encoding → Reference → Retrieval) 学习系统的 AI 技能包。

用 AI 辅助学习技术知识，但不是让 AI 讲课——而是让 AI 当教练，帮你自己构建知识的逻辑链。

## 包含的技能

| 技能 | 用途 |
|------|------|
| `/PEROlearn` | 教学模式：引导你通过四个阶段学习新知识 |
| `/PEROfeynman` | 检验模式：扮演刁钻学生检验你是否真懂了 |

## 支持的工具

- [Claude Code](https://claude.ai/code) — `~/.claude/skills/`
- [Codex CLI](https://github.com/openai/codex) — `~/.codex/skills/`
- [OpenClaw](https://github.com/openclaw/openclaw) — `~/.openclaw/skills/`

SKILL.md 是跨平台开放标准，一份文件适用于所有支持该标准的工具。

## 安装

### Windows (PowerShell)

```powershell
git clone https://github.com/YOUR_USERNAME/pero-skills.git
cd pero-skills
.\install.ps1
```

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/pero-skills.git
cd pero-skills
chmod +x install.sh
./install.sh
```

安装脚本会自动检测你装了哪些工具，用 symlink（Linux/macOS）或 junction（Windows）链接技能目录。这意味着 `git pull` 之后技能自动更新，不需要重新安装。

### 手动安装

如果不想跑脚本，把 `skills/PEROlearn` 和 `skills/PEROfeynman` 目录复制到对应工具的 skills 目录即可。

## 使用方法

### 开始学新主题

```
cd ~/learning        # 你存放学习项目的目录
claude               # 或 codex / openclaw
/PEROlearn
```

AI 会问你学什么、目的、水平，然后在当前目录创建项目子目录并开始教学。

### 继续学习

```
cd ~/learning/linux-server   # cd 到已有的学习项目目录
claude
/PEROlearn
```

AI 读取 CLAUDE.md 恢复进度，从上次断点继续。

### 费曼检验

在学习对话中任何时候：

```
/PEROfeynman
```

AI 切换为"刁钻学生"模式，基于你的薄弱点记录和逻辑链发起检验。

## PERO 是什么

四个阶段：

1. **Priming**（引发认知渴望）：扫描全貌，建立充满缺口的框架，让大脑主动想去填补
2. **Encoding**（构建逻辑链）：AI 提供素材，你自己组织概念之间的关系，AI 挑战你的组织
3. **Reference**（认知卸载）：区分核心逻辑链和查文档就行的细节，释放工作记忆
4. **Retrieval**（检验重建）：不看资料，从核心锚点推出完整逻辑链

核心理念：**学习者是主角**。AI 不讲课，AI 提供素材和挑战。

## 进度文件

每个学习项目有一个 `CLAUDE.md` 文件，存储：
- 知识地图（模块和完成状态）
- 逻辑链（已构建的因果链）
- 薄弱点记录（犯过的错和修正）
- 停车场（暂缓的问题）
- Session 记录和费曼检验记录

这个文件由 AI 在教学过程中维护，是跨 Session 恢复上下文的关键。
