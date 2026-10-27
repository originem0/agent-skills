# 开场方式库

开场决定学习者愿不愿意往下看、能不能把这一课挂到自己的生活经验上。**内容第一**：开场要从学习者真实碰到过的东西出发，而不是从词根定义出发。

每课在 `opening.type` 写明用的是哪一种。`scripts/build.py` 会统计已有课程用过的开场类型，并提醒「和上一课相同」。
**选法**：先列出这一课**真正贴合**的 2–3 种，再从中挑已有课程里用得最少的一种。宁可贴合，不要为了轮换硬套。

下面的例子标注了出处：R = B 站「RYAN的英语笔记」的视频口播，本 = 本 skill 已有课程。

---

## 1. `name` 熟词拆名

**做法**：拿一个学习者天天见的英文词，最好它的**中文名正好泄露了词根义**，然后拆开它。
- 本：tractor = 拖「拉」机 → tract 是拖、拉。
- R：airport 是飞机的港口 → port；摆个 pose 吧 → pose 是放。
- 写法：`big` 写「tractor ＝ 拖拉机」；`say` 抛问题「拖拉机为什么叫拖拉机？」。
- 配图：实物照片（拖拉机、港口）。

## 2. `scene` 生活场景 / 标识

**做法**：一个真实场景里的英文标识、包装、界面，学习者见过却没细想。
- R：机场行李提取牌，有的写 Baggage Claim，有的写 Baggage Reclaim——claim 不是「声称」吗？
- 其他可用：药盒上的 Dosage、快递单上的 Recipient、电梯里的 Capacity、App 里的 Subscribe。
- 配图：**最适合配真实照片**（`scripts/photo.py search "baggage claim sign"`）。

## 3. `pair` 双词矛盾

**做法**：两个长得很像的熟词，意思却差得离谱，制造一个「为什么」。
- R：为什么 visit 是拜访，visa 却是签证？为什么 hospital 是医院，hospitality 却是热情招待？为什么 refuse 是拒绝，confuse 却是困惑？
- 写法：`big` 并列两个词；`say` 直接问为什么。谜底在 finale 或最后一张卡揭开。

## 4. `polysemy` 一词多义之谜

**做法**：一个熟词有好几个看似无关的意思，问「怎么串起来」。
- R：course 为什么既是路线，又是课程、赛道，还是一道菜？respect 为什么既是尊重，又是「方面」？press 为什么既是按，又是新闻界？
- 写法：`big` 写这个词和三个意思；第一张卡或 finale 用母画面把几个意思收拢。

## 5. `news` 时事新闻

**做法**：最近新闻标题里出现的同族词（关税 tariff、裁员 layoff、停火 ceasefire、补贴 subsidy……），从新闻场景切入。
- **硬规则**：必须用网页搜索查到真实报道，在 `opening.source` 里写 `{ "title": 标题, "url": 链接, "date": 日期 }`。查不到就换别的开场，**绝不编新闻**。
- 只引用标题和一句事实，不评论、不站队。
- 配图：可用 `scripts/photo.py shot <链接>` 截新闻页的标题区域。
- 时效性强，适合视频；网页版里写清日期。

## 6. `pop` 品牌 / 游戏 / 流行文化

**做法**：学习者熟悉的品牌名、游戏名、电影名、App 名里藏着词根。
- R：CS:GO 全称 Counter-Strike：Global Offensive，counter 是反、对抗；「帽子叔叔」cop 为什么是警察？
- 其他可用：Duolingo（duo 二）、Transformers（trans- + form）、Spectre（spect 看）。
- 注意：品牌名的词源要查证（etym.py 查不到品牌就查它用到的词）；不确定的写成「这个名字里正好有……」，不说成品牌方的本意。

## 7. `story` 想象小剧场

**做法**：用「想象一下」开头，讲一个荒诞又好记的小画面，直接引出母画面。
- R：想象一下，你 sit 的地方多了个 s——可能是一条 snake——你坐不下去，只好站起来：sist 就是站。
- 注意：这类开场往往是**联想**，不是词源。在 caveat 或解说里说一句「这是帮你记的画面」。

## 8. `visual` 视觉谜题

**做法**：一个看起来「写错了」的东西，引出拼写或字母变化的规律。
- R：楼上写着 BVILDING、AVTO——是不是写错了？其实拉丁语里 U 和 V 是同一个字母 → nov = new。
- 配图：招牌、碑刻的真实照片最有说服力。

---

## 写进课程 JSON

```jsonc
"opening": {
  "type": "scene",                                  // 上面 8 种之一
  "big": "Baggage Claim ＝ 行李提取",
  "say": "claim 不是「声称」吗？怎么跑到机场的行李转盘上了？",
  "muted": "……",
  "photo": { "file": "media/claim/opening.jpg", "credit": "照片：Jacky Cheung，CC BY-SA 4.0，Wikimedia Commons",
             "source": "https://commons.wikimedia.org/wiki/File:..." },   // 可选，由 photo.py 自动写入
  "source": { "title": "…", "url": "…", "date": "2026-10-20" },          // 仅 news 类必填
  "scene": [ ... ],                                 // 线稿画面；有 photo 时可省略
  "caption": "……"
}
```

## 好开场的检查清单

1. 学习者读第一句时，脑子里能浮现一个**见过的东西**（一块牌子、一个 App、一则新闻）。
2. 第一句里有一个**问题或矛盾**，而不是一个定义。
3. 开场里的熟词，后面真的会作为主词或 finale 出现，开头的问题在课程结尾被回答。
4. 时事有来源，联想有标注。
