# 顶部单词导航恢复后的八支成片

2026-10-31 完成。接续会话 01a18cbc-c194-7392-9424-d16f4b0816e1，覆盖更新已存在的八支视频；导航实现此前已在 4a3acea 提交推送。以下链接指向本机成片，视频和构建缓存按仓库约定保留在本地。

| 词根 | 时长 | 成片 | 审稿及验收 | MP4 SHA-256 前 12 位 |
|---|---|---|---|---|
| cap | 4 分 42.7 秒 | [cap.mp4](../projects/cap/cap.mp4) | [审稿](../projects/cap/review.md) · [画面](../projects/cap/build/verification.json) · [读音](../projects/cap/build/pronunciation_review_final.json) | `24b8c4d970fe` |
| dis | 4 分 28.7 秒 | [dis.mp4](../projects/dis/dis.mp4) | [审稿](../projects/dis/review.md) · [画面](../projects/dis/build/verification.json) · [读音](../projects/dis/build/pronunciation_review_final.json) | `7e314002bc2d` |
| lect | 4 分 38.4 秒 | [lect.mp4](../projects/lect/lect.mp4) | [审稿](../projects/lect/review.md) · [画面](../projects/lect/build/verification.json) · [读音](../projects/lect/build/pronunciation_review_final.json) | `2717c33d5c40` |
| pend | 4 分 44.8 秒 | [pend.mp4](../projects/pend/pend.mp4) | [审稿](../projects/pend/review.md) · [画面](../projects/pend/build/verification.json) · [读音](../projects/pend/build/pronunciation_review_final.json) | `c8fad3a689e1` |
| rupt | 4 分 42.6 秒 | [rupt.mp4](../projects/rupt/rupt.mp4) | [审稿](../projects/rupt/review.md) · [画面](../projects/rupt/build/verification.json) · [读音](../projects/rupt/build/pronunciation_review_final.json) | `ff92ccb6286d` |
| spir | 4 分 46.0 秒 | [spir.mp4](../projects/spir/spir.mp4) | [审稿](../projects/spir/review.md) · [画面](../projects/spir/build/verification.json) · [读音](../projects/spir/build/pronunciation_review_final.json) | `c31727e516f5` |
| tract | 4 分 5.9 秒 | [tract.mp4](../projects/tract/tract.mp4) | [审稿](../projects/tract/review.md) · [画面](../projects/tract/build/verification.json) · [读音](../projects/tract/build/pronunciation_review_final.json) | `f8b2e71ed2ff` |
| voc | 4 分 47.2 秒 | [voc.mp4](../projects/voc/voc.mp4) | [审稿](../projects/voc/review.md) · [画面](../projects/voc/build/verification.json) · [读音](../projects/voc/build/pronunciation_review_final.json) | `13a0d6268270` |

八支均重新记录了脚本、课程、图片、编译及画面代码、音色和语速的完整审核输入。实际 MP4 共检查 269 个画面时间点，复核 73 句关键英语；完整解码、音轨、时长和响度均通过。画面检查包含每个分镜末帧、选定动作和文字出现的前中后，并另看重点完整尺寸画面。

读音复核从实际成片提取音频，使用 large-v3-turbo，无热词提示。原始 check.json 的 needs_listening 如实保留，逐项处理结果见各课 review.md；没有把相似度匹配或重复转写当作读音正确的依据。irrupt 与 erupt 的同音关系已对照 Cambridge 原页。

本轮修正了收据图文错配、收据确认收到款项的表述、若干历史词形被误当作通用后缀的讲法，以及中英混读含混。家族图保留口播已经讲到的旁支，顶部导航随当前讲解与回讲定位。各课对照 capit 基准的具体证据记录在审稿文件中。

代码验证为 49 项脚本检查、34 项单元和浏览器检查全部通过；13 份课程数据验证无错误。

未重生成 port、port-cables、port-storyboard、capit、capit-storyboard，五支原片 SHA-256 与任务开始前一致。capit-cloth 由用户在工作期间主动删除，并于 2026-10-31 明确确认保留删除；未恢复或重生成它。其余未出片草稿不属于本次批量。

执行前后清单、原片备份与分阶段日志位于 cache/navigation-refresh。各课 build/approval.json、render.json、verification.json 和 pronunciation_review_final.json 保存完整指纹及检查证据。
