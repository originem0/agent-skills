# 分镜格式

口播和画面只改 `projects/<项目>/script.md`。新稿用稳定编号的 shot；旧画面块只作为已有稿的导入格式，不另设第二套播放器。共同讲解原则、素材核实和口播写法见 [script_guide.md](script_guide.md)，质量参照见 [capit_benchmark.md](capit_benchmark.md)。

## 一个可以执行的片段

以下示例只讲 import，其余主词明确跳过。实际成片根据材料决定展开量，不把示例的两拍当成模板。

````markdown
---
lesson: port
spine: 从软件的里面看导入，再接回搬运
skip: portable（本段不讲）；export（本段不讲）；transport（本段不讲）；support（本段不讲）；report（本段不讲）
---

## 进入软件 [shot: photo-inside]
> 已知：手机照片进入电脑相册
> 推进：把导入的里面和搬运动作相接
Import photos，就是把照片{enter|import}，导入相册。

```scene
{
  "learn": [{
    "id": "carry-in", "kind": "etymology", "label": "import",
    "detail": "往里面搬 → 导入、进口", "words": ["import"],
    "source": "lesson:import"
  }],
  "nodes": [{
    "id": "word", "type": "text", "relation": "carry-in",
    "x": 120, "y": 230, "w": 1500, "h": 170,
    "font": "en", "size": 110, "color": "root", "opacity": 0
  }],
  "events": [{"target": "word", "at": "enter", "duration": 0.5, "to": {"opacity": 1}}]
}
```

## 这一步往哪儿 [shot: close-inside]
> 已知：刚才已经讲过导入
> 推进：把软件边界与搬运动作重新连接
往谁的里面搬，要先认清参照。

```scene
{
  "recall": ["carry-in"], "closing": true,
  "nodes": [{"id": "summary", "type": "summary", "refs": ["carry-in"],
             "x": 120, "y": 230, "w": 1500, "h": 560}]
}
```
````

## 镜头与语音

- `## 标题 [shot: 编号]` 的编号整片唯一。字母开头，后接字母、数字、短横线、下划线或点，最多 80 字符。改一段口播不改无关镜头编号。
- 每拍写 `> 已知`、`> 推进`、口播和一个 `scene` JSON 块。元数据、代码块都不念。`>>` 仍是待处理批注。
- `{enter|import}` 的 enter 是触发编号，实际只念和显示 import。同一拍两次 import 用不同编号，不能共用触发点。
- `at` 写触发编号或镜头内秒数；`offset` 加减秒数，`duration` 为非负秒数。编译成绝对时间，同一属性的动作不能重叠，也不能越过镜头边界。
- `label` 可覆盖屏幕上的镜头标题。`family` 可覆盖左上角词根提示，写 `""` 可在开场提问时暂不揭示答案。省略时显示课程词根。
- 顶部单词导航只显示已经进入讲解的词，当前词突出，其他词淡显。默认跟随本段 learn 的 words 或 recall；`focus: ["word"]` 可明确回到已讲词，多个词可同时定位，`focus: []` 表示本段不突出单词。未知词和仅作形近对比的词不能进入词族导航。第一次出现只代表引入，不显示完成计数。长列表按可用宽度保留当前附近的词。
- 镜头选择落实在稿中。播放器不随机选词、换图或从中文释义猜动作。

## 关系及依据

`learn` 声明本段新讲的关系，包含唯一 `id`、`kind`、`label`、`detail`、`source` 和可选 `words`。

| kind | 用途 |
|---|---|
| etymology | 已核实的词源演变 |
| usage | 现代语境与用法 |
| analogy | 明确说成联想的记忆画面 |
| contrast | 对比与家族边界 |

`source` 用 `lesson:词` 引用课程中已有词源，或写已打开核实的网页 URL。一个来源字段不自动证明整段所有事实，其他依据仍写 `> 来源`。词源缓存可由 word-family 的 `etym.py` 复核。数字同样要有所在段依据；检查只能检出缺项，不能替代查证。

`words` 里的单词必须出现在本段口播中。本课主词要有对应讲解，或列入 `skip`；仅在开头问句里点名不算讲完。不要为凑覆盖把尚未解释的词塞进关系记录。

`requires` 指向前面已建立的前提，`recall` 指向本段回扣的关系。两者不能提前引用。每个新关系和回扣都要有带 `relation` 的画面节点，或明确列入 summary 的 `refs`。标记 `closing: true` 的结尾镜头合起来收全本片关系，可以分段呈现，不把所有词挤在一屏。

程序不判断一句话是否真正讲透，也不证明标了 relation 的图片就合适。来源、讲解推进、视觉对应与总结完整性仍由审稿和实际成片检查负责。

## 画面节点

画布为 1920×1080。内容区在 y=105 到 933 之间，底部留给署名和字幕。通常从 x=120 到 1800 布置。字号与留白按内容选择，不自动用缩字掩盖拥挤。

每个节点写唯一 `id`、`type`、`x/y/w/h`。可写 `opacity`、`scale`、`rotation`；默认不倾斜、不缩放。字号、尺寸、缩放为正数，透明度为 0 到 1。

| type | 内容字段 |
|---|---|
| text | `text` 或 `runs: [{text,color}]`；`font: en/zh`、`size`、`weight`、`color`、`align: left/center/right` |
| image | 项目内相对路径 `file`，必填 `credit`；`fit: contain/cover`；可选 `crop: [x,y,w,h]` 为原图内 0–1 归一化裁切，保持原图比例 |
| illustration | 课程线稿 `ref` 或明确的共享图形 `items`，二选一；`actionAt`、`actLevel: 静止/轻/正常/明显` |
| shape | `shape: rect/ellipse/path`、`fill`、`stroke`、`strokeWidth`；矩形可写 `radius`，路径写 `d` |
| line | 局部坐标 `points: [[x,y],…]`、`stroke`、`strokeWidth`、`arrow`、`dash` |
| summary | 已讲关系的 `refs`、可选 `heading`、`layout: branches/columns`；只展开明确点名的关系 |

text 可以用 `relation: 编号` 和 `field: label/detail` 读取同一份关系记录。图片和图形上的 relation 表示它承担该解释，不能拿任意配图顶替。图片嵌入编译结果，浏览器不临时访问外部网站。图片出处和许可放进稿件，屏幕署名保持简短。

`photo` 命令仍提供兼容旧稿的简写输出。新稿取其中的文件路径与署名，写进 image 节点；不要把旧 `[photo]` 节拍混入 shot 脚本。

颜色可以用十六进制，也可以用 `ink/muted/faint/rule/root/prefix/suffix/paper/green/blue/accent/white`。这些是视觉语义色，不是固定讲法类别。

`events` 用 `target` 指向本拍节点，`to` 只改 `x/y/w/h/opacity/scale/rotation`。`ease` 为 smooth、linear 或 hold。动作负责解释时才使用；演员的位置、关节、脚步与道具接触仍须看实际过程。

## 检查与审核

`plan` 校验稿件、合成配音并写 `timeline.json`、`film.json`、`frame.html` 和试听音频。编译结果固定了每个节点、图片字节及动作时间。`preview`、`stills`、`render` 使用同一个编译器与播放器。

`stills` 的末帧总览帮助检查布局；编码前还自动检查轨道变化前、中、后。必须另外看重点动作和实际 MP4，检查字幕、箭头是否穿字、图片关键部位以及是否真的解开关系。

`mark approved` 记录脚本、课程、图片、编译和画面代码、音色与语速的完整输入指纹。任何一项变化后，按已有授权重新检查并记录，不能只改状态行。编码失败、时长不符或编码期间输入变化，都保留原成片。

`check` 的英文转写只用于找疑点。只有热词提示后才认出的词仍列为含混，不算通过。优先用真实短语修正孤立英语词的读音；在实际 MP4 中再次抽取关键句复核，保留原始转写和媒体哈希。
