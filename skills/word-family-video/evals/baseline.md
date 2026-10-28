# 基线与真实执行记录

新建 skill，无「无 skill 基线」对照。真实执行验证（2026-10-28，Windows 11，无独显）：

- **tract**：手写解说词，plan → stills → render，4 分 17 秒，7710 帧中实际截图 1273–1776 帧，渲染约 75 秒；响度 -17.7 LUFS。
- **pend**：init 草稿 → 按 narration_guide 改写 → plan 自动删掉「形近陷阱」后 4 分 40 秒 → render。
- **读音检查**：首版把 48 kHz 音频直接喂 Whisper，满篇幻觉（已修为 16 kHz）；按最长公共子串判断误报 20 处，改为窗口相似度 ≥0.7 且跳过 ≤3 字母词后剩 3 处待人工听。
- **换音色与识别（同日）**：六个 edge-tts 音色试听后选云健（云扬英文最差、英文多语种音色中文口音待定）。读音检查从 Whisper small 换成 large-v3-turbo（CPU int8，19 秒音频约 5 秒）：中文误识（同化→童话）消失；加两遍识别 + 发音骨架后，pend 从 20 处误报降到 2 处待人工听（suspended、spend）。
- **已知不足**：edge-tts 无自定义 SSML，前缀等短音节无法标音；更自然的声音需 Azure F0（完整 SSML，注册通常需信用卡）或本地 Qwen3-TTS（CPU/核显社区移植版），尚未试。
