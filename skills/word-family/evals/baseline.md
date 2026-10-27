# 基线与真实执行记录

两个 skill（word-family、word-family-video）都是新建的，不是重构，所以没有「无 skill 基线」对照；下面记录真实执行验证。

## word-family（2026-10-28）

- **独立子代理端到端**：只给 skill 目录、不给设计对话，输入「/word-family 我今天读到 depend 这个词」。产出 pend 一课（锚点 pendant 吊坠，6 个主词 + spend 回扣，形近陷阱 pen/penalty/pound），20 次词源抓取。
  暴露的问题已修：家族图连线压字（渲染器布局）、--links 混入站点热门词条（解析未截断）、词根多义（挂/称）无规则、caveat 过长、literal 长度说明不准。
- **版面检查**：故意构造「文字被人物遮住 / 两个标签重叠 / 标签出界」三种问题，`build.py` 全部报出并定位到零件编号；tract、pend 两课零提醒。
- **变体检查**：tract（at- 未标）、pend（sus-/ap-/im- 未标）均被同化表提醒，补 `of` 后清零。
- **evals/ 场景**：mixed-roots、existing-lesson、opaque-word、prefix-variants、news-opening —— 未跑自动评分，仅作为人工/子代理验收清单。
