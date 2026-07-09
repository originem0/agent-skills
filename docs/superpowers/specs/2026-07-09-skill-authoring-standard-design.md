# Skill 编写规范（子项目 1）设计文档

日期：2026-07-09
状态：待审阅

## 背景与总体规划

本仓库启动全部 skill 的现代化重构，动因有三：底层工具/生态过时、skill 编写方法论过时、PERO 理论待升级。无实际观察到的故障驱动，无历史兼容包袱（PERO 状态文件格式可破坏性重设计）。

重构分解为三个顺序子项目，各自独立走 spec → plan → 实施 → 验证：

1. **子项目 1（本文档）**：skill 编写规范 —— 后续重构的度量衡。
2. **子项目 2**：工具类 skill 更新（crawl4ai-scraper、firecrawl-scraper、widget-viewer）—— 联网核对最新 CLI/依赖，按新规范重构，真实执行验证。同时作为新规范的第一次实战检验。
3. **子项目 3**：PERO 理论升级（PEROlearn、PEROfeynman）—— 调研学习科学与 LLM tutoring 实证研究后重设计，用子代理模拟学习者对话验证。

顺序不可调换：规范是 2/3 的前置；工具类小而快，先暴露规范自身的问题，再进 PERO 深水区。

## 子项目 1 产出物

`docs/skill-authoring.md` —— 本仓库 skill 编写与验收规范。三个来源：

- [agentskills.io 规范](https://agentskills.io/specification)：结构合法性（frontmatter 字段、目录约定、progressive disclosure 分层）。
- [Anthropic skill 写作最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：有效性（description 触发设计、自由度分级、评估驱动开发）。
- 本仓库自有约定：多平台安装过滤、中英双语触发场景。

## 现存违规（规范必须裁决的问题）

调研对照发现四处与官方规范冲突，规范文档需给出裁决，子项目 2/3 重构时执行：

| # | 问题 | 裁决 |
|---|------|------|
| 1 | `platforms` 是自造顶层字段，官方扩展点是 `metadata` | 迁移为 `metadata.platforms`，同步修改 install.ps1 / install.sh 的 frontmatter 解析（已确认，接受破坏性变更） |
| 2 | 爬虫 skill 的 `allowed-tools` 写成 YAML 列表，官方规范为空格分隔字符串 | 改为空格分隔字符串格式 |
| 3 | 目录命名不统一：widget-viewer 用 `reference/`（官方推荐 `references/`）、`templates/` 语义上应为 `assets/` | 统一采用官方目录名：`references/`、`scripts/`、`assets/`；`examples/` 作为本仓库允许的补充目录保留 |
| 4 | description 写法未固化 | 规范中固化为模板：第三人称 + 做什么 + 何时用 + 中英双语触发词 |

## skill-authoring.md 内容框架

### 1. Frontmatter 规则
- 必填：`name`（≤64 字符，小写字母/数字/连字符，与目录名一致）、`description`（≤1024 字符）。
- description 模板：第三人称陈述"做什么"，随后"Use when / 触发场景"，包含中英双语关键词。禁止第一/第二人称。
- 可选：`compatibility`（环境要求，如 widget-viewer 的 Windows + WebView2）、`allowed-tools`（空格分隔字符串）。
- 本仓库扩展：`metadata.platforms`，值为空格分隔的平台列表字符串（如 `"claude-code codex"`，可选值 claude-code / codex / openclaw），省略 = 全平台。

### 2. 结构与 progressive disclosure
- SKILL.md 正文 < 500 行；建议 < 5000 tokens。
- 文件引用只允许一层深（所有 reference 文件直接从 SKILL.md 链接）。
- 超过 100 行的 reference 文件顶部加目录。
- 目录定名：`references/`（文档）、`scripts/`（可执行，写明是"执行"还是"阅读参考"）、`assets/`（模板/静态资源）、`examples/`（可运行示例代码）。
- 时效性内容（版本号、日期相关行为）放"旧模式"折叠区或 gotchas，不写进主流程。

### 3. 指令有效性
- 自由度分级：脆弱操作给精确命令（低自由度），启发式任务给方向（高自由度）；默认给一个方案 + 逃生舱，不并列多选项。
- 复杂流程用 checklist 模式（让模型复制清单逐项勾选）。
- 质量关键路径用 feedback loop 模式（校验 → 修复 → 重校验，通过才继续）。
- 全文术语一致；示例具体不抽象。
- 假设模型已聪明：不解释模型已知的概念，每段内容对得起它的 token 成本。

### 4. 验收标准（评估驱动）
- 每个 skill 至少 3 个评估场景，存放于该 skill 的 `evals/` 目录，JSON 格式：`{query, files?, expected_behavior[]}`。
- 重构流程：先跑基线（无 skill 时模型对评估场景的表现）→ 重构 → 用评估场景验证改进。不做无基线的重构。
- 真实执行验证：工具类 skill 实际执行核心命令（抓真实网页、渲染真实 widget）；PERO 类用子代理模拟学习者对话检验指令保真度。
- 注：`evals/` 是本仓库约定（官方规范无此目录，属"任意附加目录"），安装时随 skill 一起链接，不影响运行。

## 范围外

- 各 skill 的具体重构（子项目 2/3 执行）。
- install 脚本除 `metadata.platforms` 解析外的改动。
- 不引入 skills-ref CLI 等新工具链依赖；结构合法性靠规范清单人工核对，有效性靠 evals。

## 验收标准（子项目 1 自身）

1. `docs/skill-authoring.md` 覆盖上述四个章节，含现存违规的四项裁决。
2. install.ps1 / install.sh 解析 `metadata.platforms`，且现有 3 个带 `platforms` 字段的 skill（PEROlearn、PEROfeynman、widget-viewer）的 frontmatter 同步迁移——这是机械改动，在本子项目内完成，保证规范落地即生效、仓库不存在新旧两种格式并存的窗口期。
3. 规范可直接当验收清单用：子项目 2/3 的 PR 逐项核对。
