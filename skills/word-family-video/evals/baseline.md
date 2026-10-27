# 基线与真实执行记录

新建 skill，无「无 skill 基线」对照。真实执行验证（2026-10-28，Windows 11，无独显）：

- **tract**：手写解说词，plan → stills → render，4 分 17 秒，7710 帧中实际截图 1273–1776 帧，渲染约 75 秒；响度 -17.7 LUFS。
- **pend**：init 草稿 → 按 narration_guide 改写 → plan 自动删掉「形近陷阱」后 4 分 40 秒 → render。
- **读音检查**：首版把 48 kHz 音频直接喂 Whisper，满篇幻觉（已修为 16 kHz）；按最长公共子串判断误报 20 处，改为窗口相似度 ≥0.7 且跳过 ≤3 字母词后剩 3 处待人工听。
- **已知不足**：edge-tts 云希语调偏平；Whisper small 在中英混读里对短英文词识别不稳（见本目录 evals 与后续 TTS/ASR 调研）。
