# Skill 编写规范

本仓库所有 skill 的编写与验收标准。依据：[agentskills.io 规范](https://agentskills.io/specification)、[Anthropic skill 写作最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)。新增或重构 skill 时逐项核对，PR 以本文件为验收清单。

## 1. Frontmatter

**必填字段：**

- `name`：≤64 字符，仅小写字母、数字、连字符；不以连字符开头或结尾，无连续连字符；必须与目录名一致。
- `description`：≤1024 字符，第三人称。模板：

  ```yaml
  description: >
    <做什么：第三人称动词开头，一到两句。>
    Use when <何时用：具体触发场景>。
    触发词：<中文关键词>, <english keywords>。
  ```

  禁止第一/第二人称（"我可以帮你""你可以用这个"）。中英双语触发词都要有——两种语言的请求都必须能命中。

**可选字段（只在需要时写）：**

- `compatibility`：≤500 字符，环境硬性要求（OS、外部依赖、网络）。多数 skill 不需要。
- `allowed-tools`：**空格分隔字符串**，如 `allowed-tools: Read Write Bash`。不是 YAML 列表。
- `metadata.platforms`（本仓库扩展）：安装平台过滤，空格分隔字符串，缺省 = 全平台安装。

  ```yaml
  metadata:
    platforms: claude-code            # 多平台写 "claude-code codex"
  ```

  可选值：`claude-code` / `codex` / `openclaw`。
  格式约束（安装脚本是逐行解析器，不是完整 YAML 解析器）：
  - 必须写在 `metadata:` 下，两空格缩进，单独一行；
  - 值为纯字符串或双引号字符串，**不用 `[]` 列表**；
  - `platforms:` 键不得出现在 frontmatter 的其他位置（顶层 `platforms:` 是废弃格式，安装脚本不识别）。

## 2. 结构与 progressive disclosure

- SKILL.md 正文 < 500 行。接近上限就拆文件。
- 子目录定名（官方约定 + 本仓库补充）：
  - `references/` — 文档资料（不是 `reference/`）
  - `scripts/` — 可执行脚本
  - `assets/` — 模板与静态资源（不是 `templates/`）
  - `examples/` — 可运行示例代码（本仓库补充）
  - `evals/` — 评估场景（本仓库补充，见 §4）
- 文件引用只允许一层深：所有子文件直接从 SKILL.md 链接，子文件不再链接其他子文件。
- 超过 100 行的 references 文件顶部加内容目录（Contents 列表），保证部分读取时可见全貌。
- 引用 scripts 时写明意图："运行 `scripts/x.sh`"（执行，产物进上下文）或"参考 `scripts/x.py` 的算法"（阅读，代码进上下文）。
- 路径一律正斜杠，包括面向 Windows 的 skill。
- 时效性内容（版本号、日期相关行为差异）不进主流程，放 gotchas 或折叠的"旧模式"区。

## 3. 指令有效性

- **假设模型已聪明**：不解释模型已知的概念（什么是 PDF、库怎么装）。每段内容自问："这段对得起它的 token 成本吗？"
- **自由度分级**：
  - 脆弱、必须精确的操作 → 给确切命令，注明"不要修改参数"（低自由度）。
  - 有判断空间的任务 → 给方向和启发式，信任模型选路（高自由度）。
  - 默认给一个方案 + 逃生舱（"X 场景改用 Y"），不并列多个等价选项让模型自己挑。
- **复杂流程用 checklist**：给出可复制的清单，让模型逐项勾选推进。
- **质量关键路径用 feedback loop**：校验 → 修复 → 重校验，通过才继续；写明"校验失败时回到第 N 步"。
- 术语一致：同一事物全文只用一个名字。
- 示例具体不抽象：给真实的输入/输出对，不给"诸如此类"。

## 4. 验收（评估驱动）

- 每个 skill 至少 3 个评估场景，放在该 skill 的 `evals/` 目录，每个场景一个 JSON 文件：

  ```json
  {
    "query": "用户会说的原话",
    "files": ["可选：测试用的输入文件路径"],
    "expected_behavior": [
      "可观察的行为断言 1",
      "可观察的行为断言 2",
      "可观察的行为断言 3"
    ]
  }
  ```

- 重构流程：先跑基线（无 skill 时模型对同一组场景的表现）→ 重构 → 用同一组场景验证改进。**无基线不重构。**
- 真实执行验证：
  - 工具类 skill：实际执行核心命令（抓真实网页、渲染真实 widget），不以"命令看起来对"为准。
  - 对话类 skill（PERO 系列）：子代理模拟用户对话，检验指令保真度（该问时问、该停时停）。

## 附：新增/重构 skill 检查单

- [ ] name 合法（小写/数字/连字符）且与目录名一致
- [ ] description 第三人称，含"做什么 + 何时用 + 中英双语触发词"
- [ ] allowed-tools（如有）为空格分隔字符串
- [ ] 平台受限时使用 metadata.platforms（新格式）
- [ ] SKILL.md < 500 行，文件引用一层深
- [ ] 子目录命名符合 §2
- [ ] 无时效性内容混入主流程
- [ ] evals/ 有 ≥3 个场景，且有基线记录
- [ ] 真实执行验证通过
