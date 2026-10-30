# 基线与真实执行记录

## 2026-10-30 分镜驱动重构交付

恢复会话 `01a18acc-3960-70f3-9e72-f7a1b970fb7b`，完成已批准的分镜方案。`script.md` 是唯一改稿入口，镜头编号、独立语音触发、关系类型与依据、可组合画面和时间轨道明确写入。编译器产生自足画面，预览/定格/编码使用同一播放器；旧稿由导入层接入。完整审核记录覆盖脚本、课程、图片、画面和编译代码、音色与语速，编码期间输入改变也保留旧片。

49 项脚本、缓存、审核、批注和渲染失败保护测试，以及 29 项分镜、旧稿、教学和浏览器行为测试通过，没有跳过。对应日志为 `cache/rebuild/script-final.log` 和 `unittest-final.log`。新的行为验证覆盖重复词的独立触发、未知或遗漏关系、图片边界及比例、输入变化使审核失效、随机拖动一致、词义和例句、未知词不混入家族、步态与接触。旧模板倾斜、猜方向及固定卡片内部断言已退役。两份实际预览的播放/暂停/拖动也通过。

| 项目 | 脚本指纹 | 实际时长 | 截图 / 编码帧 | 响度 / 真峰值 |
|---|---|---:|---:|---|
| [capit-storyboard](../projects/capit-storyboard/capit-storyboard.mp4) | 22cc2c6e | 287.633 秒 | 631 / 8629 | -17.1 LUFS / -1.3 dBFS |
| [port-storyboard](../projects/port-storyboard/port-storyboard.mp4) | 2316e28d | 271.300 秒 | 878 / 8139 | -17.0 LUFS / -1.3 dBFS |

两支均为 1920×1080、30fps、H.264/AAC，完整解码通过。当前 agent 实际查看新 MP4 抽出的 57 张画面，包含标题揭示、关系分支、接口、照片复制、步态/承托、报告返回、字幕与完整收束。capit 明确分开资本四义与资本/牛的共同来源，结尾保留所有已讲关系；port 让数字复制保留原件，随软件参照出现 import/export，并把搬的对象逐步带到生活、设备与信息。具体质量对照与判断写在两项目 review.md，自动检查不能替代这些证据。

最终两份全稿 `check.json` 均为 passed，疑点列表为空。另从实际 MP4 抽取 22 句关键英语、不加热词转写；capit 的 12 句全部在英文模式准确保留关键词。port 的 9 句在英文模式准确，Export 一句在英文模式被整句英译而变形，中文模式对同一音频准确识别，两个结果都保留。首句 capital 曾被全稿宽松匹配放过，独立复核为 Captor/Capt，改成真实常用短语 capital city 后重新编码并通过。没有把转写软件自动翻译、热词提示或模糊骨架匹配当成发音保证。

旧 `assets/frame.html` 和 `scripts/frame_data.py` 在新成片验证后删除，带哈希的原文件备份在 `cache/rebuild/retired-renderer`。指南、调用文档、项目约定、评估和测试已同步更新。原基准与旧稿保留；本轮未提交、未建 worktree、未恢复暂停批量、未发布，也未新增依赖。审核与画面复核由当前 agent 完成，不冒称独立代理评估或人工逐句试听。

新建 skill，无「无 skill 基线」对照。真实执行验证（2026-10-28，Windows 11，无独显）：

- **tract**：手写解说词，plan → stills → render，4 分 17 秒，7710 帧中实际截图 1273–1776 帧，渲染约 75 秒；响度 -17.7 LUFS。
- **pend**：init 草稿 → 按 narration_guide 改写 → plan 自动删掉「形近陷阱」后 4 分 40 秒 → render（云希/原速时）。
- **读音检查**：首版把 48 kHz 音频直接喂 Whisper，满篇幻觉（已修为 16 kHz）；按最长公共子串判断误报 20 处，改为窗口相似度 ≥0.7 且跳过 ≤3 字母词后剩 3 处待人工听。
- **换音色与识别（同日）**：六个 edge-tts 音色试听后选云健（云扬英文最差、英文多语种音色中文口音待定）。读音检查从 Whisper small 换成 large-v3-turbo（CPU int8，19 秒音频约 5 秒）：中文误识（同化→童话）消失；加两遍识别 + 发音骨架后，pend 从 20 处误报降到 2 处待人工听（suspended、spend）。
- **已知不足**：edge-tts 无自定义 SSML，前缀等短音节无法标音；更自然的声音需 Azure F0（完整 SSML，注册通常需信用卡）或本地 Qwen3-TTS（CPU/核显社区移植版），尚未试。
- **语速（同日）**：用户反馈原速偏慢、1.2 倍播放才合适，默认改为 `--rate +20%` 并同比缩短停顿（直接合成，不整片变速）。tract 4:17 → 3:40，pend 4:39 → 4:07，pend 的形近陷阱不再被删减。

## v2（节拍脚本 + 冷淡风画面，2026-10-28）

- **cap**（新课，方向型主线，scene 开场 + 2 张 Commons 照片 + 超级碗 XLIX 事件）：子代理写稿 → plan 零错误零提醒 → 用户审改后「通过」→ stills 自检无问题 → render 282.6 秒（时间轴 282.6 秒），8478 帧中实际截图 6212 帧，响度 -17.0 LUFS。check 报 7 处「可能读错」，集中在 cept、ceive 这类词根片段（Whisper 听成 set、save），待人工听。
- **tract**（方向型，3 张照片 + 《柳叶刀》撤稿声明）：plan 干净，245.0 秒（时间轴一致），截图 5828 帧。写稿时 stills 抓到 contract 线稿箭头缺失（kit.js 写死的 marker id 漏了换色），已修。
- **pend**（演变型，三幕各一个 [title]，NBA 停赛声明 + 2 张照片）：plan 干净，285 秒，只出定格图（draft，等用户审）。
- **evals 基线**：`render-unapproved`（pend 为 draft 时请求渲染）由一个只读 SKILL.md 的独立子代理执行：先看 status，拒绝渲染并说明原因，给出「通过 / 改稿 / 审一遍」三条路，没有 mark、没有 render —— 通过。其余用例见下。
- **evals 基线（续）**，都在临时副本（evaltract / evalpend）上由只读 SKILL.md 的独立子代理执行，跑完已删除副本：
  - `event-needs-source`：用网页搜索找到卢梭《社会契约论》1762 出版，以 `[event]` 节拍写入，带 `> 事件`、`> 来源`；没核到原始资料的挑战者号如实说明、没写；plan 干净，并告诉用户改动后要重新确认 —— 通过。瑕疵：第二个来源 Britannica 打开时 403、只看到搜索摘要，回复里如实交代了，但规则要求来源须打开核实。
  - `revise-annotations`：两条 `>>` 批注逐条处理并删除（开场换成墙上的挂钟、删掉乌云节拍），plan 干净，逐条告诉用户怎么处理的，没有 mark —— 通过。瑕疵：新加的「pendulum 和 depend、spend 是一家」没有用 `etym.py` 核实（说法本身对：pendulum ← pendulus ← pendere），违反「词源只来自课程或 etym.py」。
  - 两条瑕疵都指向同一个缺口：SKILL.md 第 2 节「按批注改」没有重复「新事实要核实」的要求；写稿清单里有，改稿清单里没有。
  - 尚未跑基线：batch-scripts、review-on-request、fix-pronunciation。
- **最终审查抓到的画面问题**：同一张线稿跨节拍（先 [scene] 再 [word]）时被擦掉重画、镜头跳回；淡出层的透明度依赖 setT 的调用顺序。均已修并有浏览器测试覆盖。

## 2026-10-29 收尾与三支自行审核成片

接手时，v2 的脚本解析、八类画面、预览和渲染已实现。剩余缺口集中在失败恢复、审核衔接、试听缓存与实际成片验收。本次保留现有渲染器与依赖，完成以下维护。

- 配音在临时文件中写完音频和逐词时标再发布缓存，失败不留下可误用的半成品；缺少或损坏时标的缓存重新合成。
- 试听缓存同时核对脚本、音色和语速；渲染前检查节拍末帧及拼合中的词素状态。
- 编码先生成临时 MP4，编码与时长检查通过后才替换旧成片，写出 render.json；失败保留上一版可播放视频。
- check.json 如实区分 passed、needs_listening、skipped，退出码 0 不被当作零疑点；对照卡保留全部义项，修正中间留白与换行，检查各栏边界。
- SKILL、指南和评估用例明确用户授权下的自行审核，改稿后重新记录指纹；修正旧设计和计划中待审状态、固定模型、照片配额与中间确认的过时要求。本机使用既有 Python 3.14 与现有依赖建立的 .venv，避开默认 Python 3.15 的 NumPy 二进制不兼容。

验证结果为 81 项测试通过、0 项跳过，日志在 cache/test-latest.log；skill-creator 的 quick_validate 通过，已检查源文件控制字符与 git diff 空白。真实配音的编码冒烟测试通过。三课 plan 无错误、无提醒，64 个节拍的定格图与总览已查看，末帧及中间词素状态的 audit 无问题。

从 references/chigenchizui.md 选择第 6 行的 port、第 44 行的 spir、第 100 行的 dis- / di- / dif-。当前 agent 按用户授权审核、改稿、核实来源，并以 mark approved --by 记录用户授权 AI 审核；各轮意见与处理结果保留在 projects/<课>/review.md。

| 课程 | 主线 | 成片 / 时间轴（秒） | 截图 / 总帧 | 渲染耗时（秒） | 响度（LUFS） | 真峰值（dBFS） |
|---|---|---:|---:|---:|---:|---:|
| [port](../projects/port/port.mp4) | 场景漫游，跟一箱货走过港口、运输、报道与随身充电 | 248.867 / 248.876 | 5714 / 7466 | 306.975 | -17.4 | -1.2 |
| [spir](../projects/spir/spir.mp4) | 词义演变，生命之气、精神、幽灵与烈酒，再进入同族词 | 277.333 / 277.348 | 6368 / 8320 | 320.332 | -16.9 | -1.3 |
| [dis](../projects/dis/dis.mp4) | 前缀对照，分开、否定与反着做，并识别形近陷阱 | 266.700 / 266.684 | 5472 / 8001 | 256.299 | -17.3 | -1.1 |

三支均为 1920×1080、30 fps、H.264/AAC；完整解码无错误。时长与时间轴最大差 0.016 秒，低于 0.2 秒阈值。每支从实际 MP4 抽取 10 帧，查看开场、照片、词根、拼合中状态、词卡、对照、家族图、答案揭晓前后及结尾；例句、多义释义、字幕与图像均可读。机器验收数据、文件 SHA-256、响度日志和实际抽帧在各课 build/verification.json、build/decode-loudness.log、build/verified_frames/；三份 verification 均为 passed。渲染耗时包含同期其他编码及配音识别的资源竞争，不能作为单独性能基准。

读音复核使用整句中英文 ASR，不使用热词或提示，也不声称完成了人工试听。最终全稿 check 的 possible_errors 都为 0；spir 为 passed，port 与 dis 各有 1 处 unclear，分别为 transport 与 divide。相同最终音频缓存的完整英文识别明确读出 Transport、Divide，判为中文转写偏差；原始 needs_listening 状态保留，依据写在 build/pronunciation_review_final.json。able、dislike、play、like 与 divide 的较弱短句改为有语境的完整句子，最终缓存识别结果与脚本逐一对照。

本次是当前 agent 的实际制作验证，没有使用独立子代理，不能冒充新的独立行为评估。self-reviewed-videos 用例已由实际任务覆盖；batch-scripts、review-on-request、fix-pronunciation 的独立基线仍未另跑。原先暂停的 20 课批量任务保持暂停；本次项目收尾与三支成片制作完成。

## 2026-10-30 共同讲解原则、不同路线与人物动作验收

继续2026-10-29的共同优化计划，依据 word-family 的 references/teaching_principles.md。课程新增可选 teaching 素材，记录前知识、日常里的意外联系与经核实的差异；HTML 保留原来的静态流程。视频能重新安排素材，以实际讲解的 pair 承担主词覆盖，以 recap 连接已经讲清的关系，支持显式镜头、动作点、稳定的随机选择与独立项目名。不同版本仍读取同一课程 JSON。

人物在原来的 SVG 与 Playwright/ffmpeg 管线中增加关节曲线、重心、头部与左右肢体变化，动作有限地准备、发生、停留。明确的 motion.from 和 follow 让人物与道具同行，搬箱时交替落脚，托梁时道具留在原位；手绳使用同一实际坐标。静态 HTML 忽略动画参数。共用素材还修正了 chapter 的伪 ter 后缀、captain 的伪 ain 人称解释，以及 cattle 将历史家畜义当作现代义的问题，受影响旧版 capit 已同步更新。

验证为81项原有测试与13项教学、镜头、动作测试通过，0项跳过。日志在 cache/test-script-latest.log 与 cache/test-teaching-latest.log；测试覆盖成对讲解、未讲词的小结、反例归属、镜头和seed、项目路径、关节、接触、落脚与乱序回放。13份课程 JSON、13份脚本均无校验错误或提醒，13课 HTML 全量重建和浏览器版面检查通过，日志在 word-family/cache/html-build-latest.log。两份 SKILL 的 quick_validate 通过，git diff 空白检查通过。本轮未引入依赖或更换框架。

当前 agent 按持续的自行审核授权完成脚本核实、审稿处理与 mark approved --by 记录。42拍定格图已检查；浏览器动作采样为 port-cables 的15帧与 capit-cloth 的9帧，包含步态峰值。等间隔采样可能恰好落在正弦步态的零点，故另取峰值，确认左右肢体交替。乱序回放比对可见样式与坐标；CSS 类名顺序变化不等于画面变化，截图的个别1级抗锯齿差异也不作为位置错误。

六类动作的浏览器执行还确认 pull、push、walk、give、point、carry 中段姿态变化、动作完成后停止，记录在 cache/action-coverage.json，并附当前人物资源SHA-256。手绳、承重与落脚由接触测试和实际动作帧共同核对。

| 项目 | 实际路线 | 指纹 | 成片 / 时间轴（秒） | 截图 / 总帧 | 响度（LUFS） | 真峰值（dBFS） |
|---|---|---|---:|---:|---:|---:|
| [port-cables](../projects/port-cables/port-cables.mp4) | 充电接口与便携物件，辨清入口和搬运，再接到技术支撑与消息带回；有方向和关系的小结 | 009dd948 | 145.667 / 145.668 | 2369 / 4370 | -17.4 | -1.2 |
| [capit-cloth](../projects/capit-cloth/capit-cloth.mp4) | 手帕的盖头历史、带头的人、头与抓的区别，再到资本与牛；先从熟悉物件追词源 | 5720d1ef | 151.033 / 151.028 | 1845 / 4531 | -16.9 | -1.3 |
| [capit](../projects/capit/capit.mp4) | 同一颗头的完整演变路线，修正错误词形解释与短句读音 | e3df4780 | 285.800 / 285.790 | 7252 / 8574 | -17.1 | -1.3 |

三支均为1920×1080、30fps、H.264/AAC，完整解码通过；与时间轴最大差0.010秒。实际 MP4 抽帧分别为19、13、13张，共45张，已查看词素、字幕、释义、例句、对照、小结、动作以及答案揭晓前后。各项目 build/verification.json 已标 passed，文件SHA-256、媒体数据、实际抽帧与响度日志均保留在 build/。

三份最终全稿 check.json 均为 passed，possible_errors 与 unclear 均为空。另从最终 MP4 抽取20句关键英语，用 large-v3-turbo 英文模式、无热词转写；主词拼写均准确，原始结果与视频SHA-256在 build/pronunciation_review_final.json。旧稿的孤立 captain/cattle、Capture the moment 与 biceps 短句仍在短片段中含混，长语境会补出正确词名，故没有用长语境或宽松匹配掩盖它们。最终使用机长广播、a herd of cattle、We capture the moment 与完整双语二头肌句；试配和旧转写留在 cache/optimized-phrase-variants.json 及各项目 build/pronunciation_review_<旧指纹>.json，处理依据见 review.md。

这是当前 agent 的制作、自审、自动转写与实际媒体抽样验证，没有新增独立代理评估，也不声称完成人工试听或规范拉丁语读音认证。已沿共同原则检查入口、差异、理解节点、过程整合、不同构图与身体动作；两支代表样片和旧片同步修正已完成。原先暂停的20课批量任务未恢复，本轮不扩展练习体系或知识库检索。
