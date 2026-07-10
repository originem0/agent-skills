# PERO v3 机制研究依据索引

本文件是 PERO v3 各机制的研究依据，供人工查证，**运行时不加载**。调研日期：2026-07-09。链接与效应量来自当日检索的公开文献，未做二次核实的推断均已标注。

## Contents

- 总依据：交球护栏与外部状态
- 跨会话检索至标准（successive relearning）
- 首次接触分流（PS-I vs example-first）
- 8 轮指令刷新
- 对抗场景应对（抗谄媚/抗索答）
- 校准循环（防流畅性错觉）
- 支架渐撤与无辅助标准
- 交错练习
- 内容特定 priming
- 情绪负荷
- 已知证据缺口

## 总依据：交球护栏与外部状态

PERO 的两个地基被 2024-26 实证直接背书。其一，"引导不给答案"护栏：无约束 ChatGPT 使学生练习成绩 +48% 但独立考试 **-17%**（比从未用过更差），教师设计的"只给提示、推动自己推理"护栏消除了危害——Generative AI Without Guardrails Can Harm Learning (Bastani et al., PNAS 2025, 预注册 RCT), https://www.pnas.org/doi/10.1073/pnas.2422633122。护栏化 tutor 的正面上限：0.73-1.3 SD——AI Tutoring Outperforms Active Learning (Kestin et al., Scientific Reports 2025), https://erctpapers.com/papers/47-kestin-et-al-2025-ai-tutoring-active-learning.html。其二，CLAUDE.md 外部状态：LLM 内隐追踪学习者掌握度不可靠，误概念识别显著弱于答案解释，微调后仍不及经典知识追踪模型——Problems With LLMs for Learner Modelling (2025), https://arxiv.org/abs/2512.23036；结构化学习者信号注入使 Khanmigo 下一题正确率 +6.1%（无独立 RCT），https://www.growthbook.io/blog/how-khan-academy-optimizes-ai-tutoring-with-experimentation。先诊断后回应的显式决策链（错误类型→策略→意图）使专家偏好 +76%，随机决策 -97%——Bridge (Wang, Demszky et al., NAACL 2024), https://arxiv.org/abs/2310.10648。

## 跨会话检索至标准（successive relearning）

掌握标准从"本会话表现"改为"≥3 个不同日期成功检索"。依据：successive relearning（跨天重复检索至标准）是检索练习最强形式，课堂实证提升超过一个字母等级——Rawson & Dunlosky (2022) Successive Relearning, Current Directions in Psychological Science, https://journals.sagepub.com/doi/full/10.1177/09637214221100484。单会话内一次成功即停：单会话 3 次 vs 1 次的优势在跨天 relearning 后消失（overlearning 被 relearning 覆盖，Rawson & Dunlosky 2011 系列）。议程综述：Pan, Dunlosky et al. (2024) Emerging and Future Directions in Test-Enhanced Learning, Educ Psychol Rev, https://link.springer.com/article/10.1007/s10648-024-09857-2。边界：高元素交互性材料的检索收益减弱，先分解再检索——van Gog & Sweller (2015), https://link.springer.com/article/10.1007/s10648-015-9310-x（Karpicke & Aue 反驳 https://link.springer.com/article/10.1007/s10648-015-9309-3；Rawson 回应 https://link.springer.com/article/10.1007/s10648-015-9308-4）。调度权归协议：学习者自主决定练习去留时检索收益归零（Rawson 系列）。

## 首次接触分流（PS-I vs example-first）

概念性新知识（目标迁移）先给设计好会失败的探索问题再讲授：PS-I 优于 I-PS，g=0.36（高保真实施 0.37-0.58），利概念理解与迁移、不损程序性知识——Sinha & Kapur (2021) When Problem Solving Followed by Instruction Works, Review of Educational Research, https://journals.sagepub.com/doi/10.3102/00346543211019105。程序性技能保持 worked example 先行 + 渐撤（CLT 传统结论；渐撤见"支架渐撤"节）。v2 的一律"先 worked example"缺此分流，是本次修正点。

## 8 轮指令刷新

v2 的 15 轮重载收紧到 8 轮 + 事件触发。依据：GPT-3.5/LLaMA2 在 8 轮内出现显著指令漂移（注意力对早期 token 衰减），system prompt 重复注入是实测最优的实用缓解——Measuring and Controlling Instruction (In)Stability (Li et al., COLM 2024), https://arxiv.org/abs/2402.10962。通用模型长对话中教学能力衰退快于专门化模型——MathTutorBench (Macina et al., 2025), https://arxiv.org/abs/2502.18940。

## 对抗场景应对（抗谄媚/抗索答）

SOTA 模型的默认行为不可信：GPT-4 错误识别 94% 但约 47% 回合泄露答案——Unifying AI Tutor Evaluation / MRBench (Maurya et al., NAACL 2025), https://arxiv.org/abs/2412.09416。对抗性学生（哀求、假装推理、变相索答）能击穿纯指令——Answer Leakage Robustness against Adversarial Students (2026), https://arxiv.org/abs/2604.18660。谄媚的三类教育危害（术语框架攻击、权威声称、面子压力）——Sycophancy is an Educational Safety Risk (2026), https://arxiv.org/abs/2605.14604；谄媚强化新手误概念且难被察觉——Invisible Saboteurs (2025), https://arxiv.org/abs/2510.03667。模型系统性"过度否定次优但正确的解、过度肯定错误解"——Confirming Correct, Missing the Rest (2026), https://arxiv.org/abs/2605.16207——对应 v3 的"先确认正确性再谈优化"与"不因自信软化判定"两条。attempt-before-hint 的架构级依从证据见 Tutor CoPilot (2024), https://arxiv.org/abs/2410.03017。

## 校准循环（防流畅性错觉）

元认知监测系统性过度自信，处理流畅度是主因；预测-表现差距反馈与检索失败经历可改善校准——判断训练研究 https://www.sciencedirect.com/science/article/abs/pii/S0959475218308788；检索失败降低过度自信 https://www.sciencedirect.com/science/article/abs/pii/S1053810014001469。AI 顺滑解释制造掌握错觉：短期产出更好但 6 周保持测验落后约 11pp（2025 RCT，见 LLM tutoring 调研工件）；元认知行为被 AI 交互挤出——Beware of Metacognitive Laziness (Fan et al., BJET 2025), https://arxiv.org/abs/2412.09315。设计落点：检索前预测置信、检索后对照差距入表；"懂了"不作为决策输入。

## 支架渐撤与无辅助标准

所有危害证据的共同形态是"有 AI 好、没 AI 垮"（Bastani -17%），故模块完成必须含无提示综合任务 + 下一 session 延迟复验。支架按水平自适应：novice 给 worked examples、advanced 撤支架（AIED 2026 field experiment，见调研工件）；低先验知识者从低变异性问题学得更好，高先验者相反（disordinal ATI, CLT 个体差异研究 2024）。

## 交错练习

同族可混淆概念 ≥2 个时练习交错排列（相邻不同策略）：预注册 cluster RCT d=0.83，机制是迫使按题选策略；收益仅现于延迟测试，且需可混淆的同族问题——Rohrer, Dedrick, Hartwig & Cheung (2020), J Educ Psychol, https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf。

## 内容特定 priming

预问收益是内容特定的：被预问内容 g=0.66，未预问内容 g=0.01，"泛化激活先验知识"不成立——Pan & Carpenter (2023), Educ Psychol Rev, https://link.springer.com/article/10.1007/s10648-023-09814-5；multilevel meta (2025), https://link.springer.com/article/10.1007/s10648-025-10075-7。附带：priming 制造的信息缺口是短时厌恶性状态，须同会话闭合否则动机收益流失（Monosov 2024 神经证据，见调研工件）。

## 情绪负荷

CLT 近年扩展将情绪/自我调节纳入负荷框架——Sweller (2023) The Development of Cognitive Load Theory, Educ Psychol Rev, https://link.springer.com/article/10.1007/s10648-023-09817-2；Education Sciences 特刊 (2025), https://www.mdpi.com/2227-7102/15/4/458。设计落点：挫败感进入根因诊断分支，与第二序卡点（信念层）衔接。

## 已知证据缺口

Khanmigo 无已发表独立 RCT；verbosity 作为单一变量的研究缺失；护栏化 tutor 的大效应（Kestin）尚无长期保持数据；本索引部分二手来源（AIED 2026 field experiment、2025 保持测验 RCT、disordinal ATI 研究）在调研工件中未留直接链接，引用时以调研工件 `.git/sdd/research-*.md` 的记录为准。
