# 课程数据格式（lessons/*.json）

完整样例见 `lessons/tract.json`。写新课时先复制它再改，比从零写更不容易出错。`scripts/build.py` 会做格式校验，不通过就不生成页面。

## 顶层

```jsonc
{
  "title": "从拖拉机开始：tract「拖、拉」一家",   // 页面标题：日常锚点 + 词根 + 核心义
  "root": { "m": "tract", "cn": "拖、拉",          // 词根或前缀（基本形）
            "variants": [ { "m": "trait", "note": "经法语变形", "ex": "portrait" } ] },  // 可选：变体，见下
  "seqTitle": "同一个人在拉，换个方向就是一个新词", // 可选，主线小节标题
  "opening": { ... },   // 日常锚点
  "anchor":  { ... },   // 母画面
  "words":   [ ... ],   // 主词 5–7 个（校验允许 3–8）
  "finale":  { ... },   // 可选：结尾回扣词，字段同 words 里的一项
  "daily":   [ "tractor 拖拉机", "train 火车" ],  // 可选：家族图四角的日常词，最多 4 个
  "traps":   [ "<b class='serif'>track</b>……" ],  // 可选：形近陷阱，允许少量 HTML（<b>）
  "transfer": [ ["protract = pro-（向前）+ tract", "答案……"] ],  // 迁移题 [题目, 答案]
  "source":  "词源核对：etymonline（经 firecrawl 抓取），2026-10-28"
}
```

## root.variants（变体，可选但常常必需）

```jsonc
"root": { "m": "in-", "cn": "不",
  "variants": [
    { "m": "il-", "note": "l 前", "ex": "illegal" },
    { "m": "im-", "note": "b、m、p 前", "ex": "impossible" },
    { "m": "ir-", "note": "r 前", "ex": "irregular" } ] }
```

- `m` 必填；`note` 写出现条件；`ex` 写一个例词，最好是主词之一。
- 不要再把变体塞进 `m`（旧写法 `"pend / pens"` 已废弃，改成 `m: "pend"` + variants）。
- 主词至少覆盖一个变体，否则 build.py 会提醒。规则详见 `style_guide.md`「变体与同化」。

## opening（日常锚点）

```jsonc
{
  "type": "name",                             // 开场方式：name/scene/pair/polysemy/news/pop/story/visual，见 openings.md
  "big": "tractor ＝ 拖拉机",                 // 一行大字：锚点本身
  "say": "拖拉机为什么叫「拖拉」机？……",       // 钩子：问题或矛盾
  "muted": "就这一个 tract，拖出了一整个家族……", // 可选：预告家族规模，留一个悬念给 finale
  "scene": [ ... ],                           // 线稿画面，见 scene_kit.md；有 photo 时可省略
  "caption": "拖拉机：拖着车斗走的机器",
  "photo": { "file": "media/tract/opening.jpg", "credit": "照片：…，Public domain，Wikimedia Commons", "source": "…" },
                                              // 可选，由 scripts/photo.py pick/shot 自动写入，不要手写
  "source": { "title": "…", "url": "…", "date": "…" }   // 仅 type=news 必填：真实检索到的报道
}
```

## anchor（母画面）

```jsonc
{
  "text": "记住这个画面：一个人，拉着一根绳子。",
  "more": "接下来每个词，都是这个人在拉，只是换了方向——……",  // 可选：预告所有方向
  "scene": [ ... ],
  "caption": "tract 的母画面：拉"
}
```

## words[i]（主词卡片）

| 字段 | 必填 | 说明 |
|---|---|---|
| `w` | ✔ | 单词 |
| `split` | ✔ | `[前缀, 词根, 后缀]`，拼起来必须等于 `w`。没有前缀写 `""`，没有后缀可省略。例：`["at","tract"]`、`["","tract","ion"]` |
| `node` | | 时间线节点上显示的短标签，通常是前缀，如 `"at-"`；finale 可用 `"↩"` |
| `parts` | ✔ | 词素标签。每项写成数组 `["de-", "从……往下"]`，或者对象 `{"m": "at-", "cn": "朝向", "of": "ad-"}`。以 `-` 结尾自动识别为前缀，以 `-` 开头为后缀，其余为词根（可用 `kind: "p"/"r"/"s"` 强制指定）。**这个词素是别的形式的同化/变体时必须用对象写法加 `of`**；不是同化而是缩略的，再加 `"how": "缩略"` |
| `link` | | 过渡句，承接上一张卡的方向变化 |
| `literal` | ✔ | 字面画面，也会出现在家族图上，**控制在 12 个字以内** |
| `caption` | | 画面说明 |
| `bridge` | ✔ | 画面 → 词义的桥接，结尾用反问 |
| `meaning` | ✔ | 词性 + 词义 |
| `senses` | | 派生词、一词多义、搭配，数组 |
| `ex` | | `[英文例句, 中文]` |
| `caveat` | | 变体为什么变、联想标注、辨析。**最多两句话** |
| `fact` | ✔ | 词源事实，一行 |
| `scene` | ✔ | 画面 |

自测模式下，`meaning`、`bridge`、`senses` 会被模糊，所以 `literal` 和画面里**不要直接写出词义**，要留给读者推。
