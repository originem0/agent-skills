# widget-viewer 基线记录

## 重构前基线

裸答条件：未读取 skill 目录内任何文件，仅凭模型自身知识 + 系统提示中的 skill 一句话描述作答。

### 场景 1: "画一个这个项目最近提交数量的柱状图"

裸答：我会用 `git log` 统计最近提交数量，然后生成图表。默认做法大概率是以下之一：
- 直接在回复里输出一个完整 HTML 代码块（含 Chart.js CDN），让用户自己存文件打开；
- 或写一个独立 HTML 文件到项目根目录/临时目录，然后尝试用 `start` 命令在浏览器打开。

差距（诚实记录）：
- 不知道应写入 `.claude/widgets/` 目录、文件名用 snake_case——这是 hook 触发渲染的关键路径约定，裸答完全不会命中。
- 不知道 skill 内有现成模板文件，更不知道具体文件名（如 chartjs 模板叫什么、放在哪个目录），只能从零手写 HTML。
- 不知道颜色要走 CSS 变量 + `getComputedStyle` 的约定，默认会硬编码 hex 色值。
- 容器 `width:100%` 的响应式要求也不会主动满足。

### 场景 2: "给我画个安装脚本工作流程的示意图"

裸答：默认会输出 Mermaid 代码块（flowchart TD）或 ASCII 流程图直接放在回复文本里，因为这是零依赖的做法。

差距：
- 不知道存在 SVG 示意图模板（具体文件名不知道），不会想到用原生 SVG + viewBox 做可缩放示意图。
- 不知道 `viewBox + width=100%`、不设固定像素宽的规范。
- 不知道要写入 `.claude/widgets/` 触发 hook 弹窗渲染——Mermaid 代码块在 CLI 里根本渲染不出图。

### 场景 3: "让你画的图窗口没弹出来"

裸答：从系统提示的 skill 描述里我知道渲染靠 `claude-widget-viewer.exe`（WebView2），所以会猜测性地检查：exe 是否存在/在 PATH、WebView2 runtime 是否安装。但具体排障路径是编不出来的：
- 不知道渲染由 settings.json 里的 PostToolUse Write hook 触发，因此不会去查 hook 配置是否存在——这是最可能的根因，裸答会漏掉。
- 不知道安装来源是 github.com/originem0/claude-widget-viewer，无法指路安装。
- 很可能会犯的错：盲目重写同一个 HTML 文件"再试一次"，而不理解 hook 触发机制。

### 基线结论

三个场景的核心差距一致：不知道 `.claude/widgets/` 路径约定 + hook 触发机制 + 模板文件清单。这些是纯项目私有约定，模型知识不可能覆盖，skill 文档必须显式携带。

## 重构后复验

用同一组 3 个场景对照重构后的 SKILL.md（57 行）逐条核对 expected_behavior：

### 场景 1: chart-request

- 写入 `.claude/widgets/<snake_case_name>.html`：SKILL.md 首段明确给出路径约定 → 命中。
- 基于 `assets/chartjs.html` 改造：模板表首行给出路径 + bar 改法（`type:'bar'`、去 fill/tension、`borderRadius:4`），并要求"Read the template file, copy it, then modify" → 命中。
- CSS 变量 `getComputedStyle` 不硬编码 hex、容器 `width:100%`：Mandatory Rules 前两条逐字覆盖 → 命中。

### 场景 2: diagram-request

- `assets/svg-diagram.html` 模板路径：模板表第二行 → 命中。
- `viewBox + width="100%"` 不设固定像素宽：Mandatory Rules SVG 条目逐字覆盖 → 命中。
- 写入 `.claude/widgets/` 触发 hook：首段 + Requirements 节 → 命中。

### 场景 3: window-not-opening

- 依赖 = claude-widget-viewer 在 PATH + settings.json 的 PostToolUse Write hook：Requirements 节 1、2 两条逐字覆盖 → 命中。
- 指向 github.com/originem0/claude-widget-viewer：Requirements 节首句链接 → 命中。
- 不盲目重写重试：Requirements 末句 "tell the user to install claude-widget-viewer instead of retrying" → 命中。

### 真实渲染验证

写入 `.claude/widgets/refactor_smoke_test.html`（raw fragment，`width:100%` 容器 + "子项目 2 验证"标题）后，`tasklist | grep -i claude-widget-viewer` 检出进程（PID 13040），RENDER OK。目录改名后 hook 链路（junction → 安装的 skill → PostToolUse hook → WebView2 窗口）工作正常。验证后已删除该文件。

### 复验结论

基线记录的三类核心差距（路径约定、hook 机制、模板清单）全部被重构后的 SKILL.md 显式覆盖，9/9 expected_behavior 断言在文档层面命中，渲染链路真实执行通过。

