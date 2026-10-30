# 本项目的交付约定

用户在 2026-10-29 明确要求，中间内容脚本由 agent 自行审核，此后只看最终成果。本项目的视频制作和改稿沿用这项授权，除非用户改变要求。完成来源核实、内容审稿、画面和读音检查后直接交付成片，不重复要求用户审核脚本。每次修改仍须重新检查，并用 `mark approved --by "用户授权 AI 审核"` 记录新指纹。

具体脚本规则见 `SKILL.md` 和 `references/script_guide.md`。词源、新闻与数字必须有已核实的依据；推测与记忆联想不能讲成定论。最终检查要看实际成片，不能只依赖自动检查的退出码。

本机默认 Python 3.15 与已装的 NumPy 二进制扩展不兼容。当前可用环境是本目录的 `.venv\Scripts\python.exe`，由现有 Python 3.14 建立并复用现有依赖。运行示例为 `.venv\Scripts\python.exe -I scripts/video.py plan port`。

本次收尾和三支视频直接在当前目录完成，不提交 git、不建 worktree。保留已有修改和其他课的草稿。此前暂停的 20 课批量任务没有因此自动恢复；这项审核授权也不包含对外发布。

2026-10-29 用户确认两项目一起优化，先将共同讲解原则写入文档，再写计划并实现。共同依据见 word-family 的 `references/teaching_principles.md`。HTML 允许固定流程；视频要按材料选择路线、句式和构图，允许合适方案之间随机变化，并在过程中小结整合。重点是日常里的意外联系、易混词根词缀的差异、前知识和认知负荷，本轮不扩展练习体系。人物改善要体现在关节、重心与接触动作，不只换入场动效。

2026-10-30 用户指定 `projects/capit/capit.mp4` 为目前最满意的标准示例，后续视频以超过它为交付要求。标准包括内容丰富且连贯，举例、图片和例句真正帮助理解并带来启发，画面按内容选择、不强塞会动的火柴人，最后完整收拢已讲关系和开场问题。以本版成片和脚本为参照，不能把时长、照片数量、分镜顺序或小结数量变成配额。写稿、审稿与成片检查均按 [capit 标准示例](references/capit_benchmark.md) 对照；检查通过不等于达到质量标准。

2026-10-30 已接续会话 `01a18acc-3960-70f3-9e72-f7a1b970fb7b` 完成分镜驱动重构。新稿用稳定编号的 `[shot]`、明确的讲解关系和节点/时间轨道，格式见 `references/storyboard_guide.md`；旧稿通过 `scripts/legacy_import.py` 进入同一个播放器。旧 `assets/frame.html` 和 `scripts/frame_data.py` 已退役，原文件备份在 `cache/rebuild/retired-renderer`。独立样片为 `projects/capit-storyboard` 与 `projects/port-storyboard`，原基准及其他草稿保留。

`build/approval.json` 现覆盖脚本、课程、实际图片、编译和画面代码、音色与语速。相关输入变化后沿用既有授权重新检查并 mark，不只改状态。实际 MP4 的检查记录在各项目 `build/verification.json` 与 `pronunciation_review_final.json`。本机音频复核继续用 FFmpeg 解码为 16 kHz 浮点数组后交给 Whisper，直接给文件路径会触发现有 PyAV 的 `metadata_errors` 不兼容；无需升级依赖。

2026-10-30 用户追加要求恢复顶部单词导航，提交推送，再覆盖重生成已经存在的成片，排除词根 port 和 capit 的全部版本。此次明确授权覆盖此前不提交 git 的约定；视频覆盖范围为 cap、dis、lect、pend、rupt、spir、tract、voc，不把未出片草稿纳入批量。导航可跟随回讲而回到旧词，不用单词出现次数冒充学习完成度。
