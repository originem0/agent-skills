---
lesson: capit
status: approved
checked: 22cc2c6e · 用户授权 AI 审核 · 2026-10-30
spine: 从 capital 四义追到头；让形状、带头者、章节、尽头、财产和生命各有画面，最后收全已讲分支和形近边界
seed: 20261030
say_as: captain → cap-tain
---

## 一个词，四个意思 [shot: four-meanings]
> 已知：首都这个熟悉译法
> 推进：先留下 capital 四义为什么相连的问题
课本里的 capital city，意思是首都。
单看第一个词，它还能表示{money|资本}。
还是{letter|大写字母}。
还有 capital punishment，{life|死刑}。
这四个意思，为什么共用一个词？

```scene
{
  "nodes": [
    {
      "id": "capital",
      "type": "text",
      "text": "capital",
      "x": 120,
      "y": 160,
      "w": 1650,
      "h": 215,
      "size": 170,
      "font": "en",
      "color": "root"
    },
    {
      "id": "city",
      "type": "text",
      "text": "首都",
      "x": 130,
      "y": 445,
      "w": 730,
      "h": 130,
      "size": 70
    },
    {
      "id": "money",
      "type": "text",
      "text": "资本",
      "x": 1040,
      "y": 445,
      "w": 730,
      "h": 130,
      "size": 70,
      "opacity": 0
    },
    {
      "id": "letter",
      "type": "text",
      "text": "大写字母",
      "x": 130,
      "y": 665,
      "w": 730,
      "h": 130,
      "size": 70,
      "opacity": 0
    },
    {
      "id": "life",
      "type": "text",
      "text": "capital punishment\n死刑",
      "x": 1040,
      "y": 665,
      "w": 740,
      "h": 150,
      "size": 48,
      "opacity": 0
    },
    {
      "id": "hline",
      "type": "shape",
      "shape": "rect",
      "x": 120,
      "y": 610,
      "w": 1680,
      "h": 3,
      "fill": "rule"
    }
  ],
  "events": [
    {
      "target": "money",
      "at": "money",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "letter",
      "at": "letter",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "life",
      "at": "life",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ],
  "family": ""
}
```

## 先看最像头的一颗 [shot: head-cabbage]
> 已知：头的形状与菜市场的卷心菜
> 推进：建立 caput 与 cabbage 的真实词源关系
> 来源：https://www.etymonline.com/word/cabbage
答案先从一颗{head|头}找起。
拉丁语管头叫 caput，进了别的词，常写成 capit。
货架上的卷心菜，是最像头的一颗。
古代法国北部，表示头的词，也用来叫卷心菜。
英语借过来，就是 {cabbage|cabbage}。
一颗卷心菜，至今还说 a head of cabbage。

```scene
{
  "learn": [
    {
      "id": "head",
      "label": "caput → capit",
      "detail": "头：形状、位置与作用",
      "source": "lesson:captain",
      "words": [],
      "kind": "etymology"
    },
    {
      "id": "cabbage",
      "label": "cabbage",
      "detail": "圆圆的一颗头 → 卷心菜",
      "source": "https://www.etymonline.com/word/cabbage",
      "words": [
        "cabbage"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "cabbage-photo",
      "type": "image",
      "file": "media/cabbage.jpg",
      "credit": "Acabashi · CC BY-SA 4.0 · Wikimedia Commons",
      "x": 830,
      "y": 225,
      "w": 970,
      "h": 600,
      "relation": "cabbage"
    },
    {
      "id": "head-shape",
      "type": "shape",
      "shape": "path",
      "x": 190,
      "y": 230,
      "w": 235,
      "h": 280,
      "fill": "green",
      "stroke": "root",
      "strokeWidth": 4,
      "d": "M120 8 C55 4 18 52 23 105 C23 158 45 182 61 197 L61 257 H139 L140 200 C180 191 192 165 191 142 L213 142 L201 113 L201 99 C196 40 161 8 120 8 Z"
    },
    {
      "id": "head-word",
      "type": "text",
      "relation": "head",
      "x": 120,
      "y": 610,
      "w": 650,
      "h": 100,
      "size": 64,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "name",
      "type": "text",
      "relation": "cabbage",
      "x": 885,
      "y": 160,
      "w": 850,
      "h": 100,
      "size": 72,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "phrase",
      "type": "text",
      "text": "a head of cabbage",
      "x": 865,
      "y": 820,
      "w": 900,
      "h": 80,
      "size": 43,
      "font": "en",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "head-word",
      "at": "head",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "name",
      "at": "cabbage",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "phrase",
      "at": "cabbage",
      "to": {
        "opacity": 1
      },
      "duration": 0.5,
      "offset": 0.7
    }
  ]
}
```

## 带头的人 [shot: captain]
> 已知：美国队长、飞机上的机长广播
> 推进：从身体的头走到团队的头，并保留历史变形边界
从一颗菜，换成一队人。
美国队长，英文叫 {captain|Captain} America。
走在一船人、一队人最前头的，就是 captain。
坐飞机听到 This is your captain speaking，是机长在说话。
这个词经过法语进入英语，旧拼法里还看得到中间的 i。
后来字形变短，头的这条来路没有变。

```scene
{
  "requires": [
    "head"
  ],
  "learn": [
    {
      "id": "captain",
      "label": "captain",
      "detail": "带头的人 → 队长、船长、机长",
      "source": "lesson:captain",
      "words": [
        "captain"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "poster",
      "type": "image",
      "file": "media/captain-america.jpg",
      "credit": "Marvel / IMP Awards · Captain America",
      "x": 120,
      "y": 145,
      "w": 480,
      "h": 750
    },
    {
      "id": "word",
      "type": "text",
      "relation": "captain",
      "x": 725,
      "y": 210,
      "w": 1060,
      "h": 145,
      "size": 118,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "roles",
      "type": "text",
      "text": "队长 · 船长 · 机长",
      "x": 730,
      "y": 385,
      "w": 1080,
      "h": 95,
      "size": 46
    },
    {
      "id": "example",
      "type": "text",
      "text": "This is your captain speaking",
      "x": 730,
      "y": 535,
      "w": 1080,
      "h": 110,
      "size": 48,
      "font": "en"
    },
    {
      "id": "history",
      "type": "text",
      "text": "capitayn  →  captain",
      "x": 730,
      "y": 720,
      "w": 1080,
      "h": 90,
      "size": 55,
      "font": "en",
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "word",
      "at": "captain",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 相同的 capt，两个来源 [shot: head-or-catch]
> 已知：captain 中的 capt
> 推进：把抓与头区分开，避免只凭相同字母认亲
> 来源：https://www.etymonline.com/word/capture
可相同字母，会把你带错门。
We {capture|capture} the moment，捕捉这一刻。
这个开头，来自拉丁语的抓。
{captain|captain} 来自头，旧拼法少了一个 i。
要分清亲戚，得看来路。

```scene
{
  "requires": [
    "captain"
  ],
  "learn": [
    {
      "id": "capture-contrast",
      "label": "captain ≠ capture",
      "detail": "头 ≠ 抓；相同拼写不保证同源",
      "source": "https://www.etymonline.com/word/capture",
      "words": [
        "capture"
      ],
      "kind": "contrast"
    }
  ],
  "nodes": [
    {
      "id": "left",
      "type": "text",
      "text": "captain",
      "x": 120,
      "y": 280,
      "w": 750,
      "h": 150,
      "size": 118,
      "font": "en",
      "color": "root",
      "relation": "capture-contrast"
    },
    {
      "id": "right",
      "type": "text",
      "text": "capture",
      "x": 1060,
      "y": 280,
      "w": 750,
      "h": 150,
      "size": 118,
      "font": "en",
      "color": "accent",
      "opacity": 0
    },
    {
      "id": "head-origin",
      "type": "text",
      "text": "caput\n头",
      "x": 120,
      "y": 520,
      "w": 750,
      "h": 180,
      "size": 66,
      "font": "en",
      "color": "root"
    },
    {
      "id": "catch-origin",
      "type": "text",
      "text": "capere\n抓",
      "x": 1060,
      "y": 520,
      "w": 750,
      "h": 180,
      "size": 66,
      "font": "en",
      "color": "accent",
      "opacity": 0
    },
    {
      "id": "not-equal",
      "type": "text",
      "text": "≠",
      "x": 895,
      "y": 380,
      "w": 130,
      "h": 130,
      "size": 100,
      "color": "muted"
    },
    {
      "id": "example",
      "type": "text",
      "text": "We capture the moment",
      "x": 1060,
      "y": 790,
      "w": 750,
      "h": 75,
      "size": 37,
      "font": "en",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "right",
      "at": "capture",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "catch-origin",
      "at": "capture",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "example",
      "at": "capture",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 头儿，也可以是头等的事 [shot: chief-chef]
> 已知：CEO 与做饭的主厨
> 推进：chief 的人和事两层用法，以及 chef 的法语联系
公司的头，又换了一张面孔。
CEO 的全称，chief executive officer。
打头的 C，就是 {chief|chief}。
它同样经过法语，接回头和首领。
说 {reason|chief reason}，就是主要原因。
从排在最前的人，走到了排在最前的事。
现代法语写成 {chef|chef}，厨房的头，就是主厨。

```scene
{
  "requires": [
    "head",
    "captain"
  ],
  "learn": [
    {
      "id": "chief",
      "label": "chief / chef",
      "detail": "首领 → 主要；厨房的头是主厨",
      "source": "lesson:chief",
      "words": [
        "chief",
        "chef"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "ceo",
      "type": "text",
      "text": "CEO",
      "x": 120,
      "y": 185,
      "w": 750,
      "h": 215,
      "size": 168,
      "font": "en",
      "color": "root"
    },
    {
      "id": "full-name",
      "type": "text",
      "text": "Chief Executive Officer",
      "x": 120,
      "y": 440,
      "w": 1550,
      "h": 90,
      "size": 56,
      "font": "en"
    },
    {
      "id": "chief",
      "type": "text",
      "relation": "chief",
      "x": 1040,
      "y": 190,
      "w": 760,
      "h": 150,
      "size": 83,
      "font": "en",
      "color": "root",
      "opacity": 0,
      "text": "chief"
    },
    {
      "id": "reason",
      "type": "text",
      "text": "chief reason\n主要原因",
      "x": 120,
      "y": 660,
      "w": 770,
      "h": 155,
      "size": 49,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "chef",
      "type": "text",
      "text": "chef\n主厨",
      "x": 1070,
      "y": 640,
      "w": 520,
      "h": 175,
      "size": 62,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "hat",
      "type": "shape",
      "shape": "path",
      "x": 1580,
      "y": 585,
      "w": 195,
      "h": 170,
      "fill": "white",
      "d": "M25 135 L25 80 C-8 85 -8 20 34 26 C45 -10 112 -10 125 26 C170 5 198 60 162 82 L162 135 Z",
      "stroke": "root",
      "strokeWidth": 4,
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "chief",
      "at": "chief",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "reason",
      "at": "reason",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "chef",
      "at": "chef",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "hat",
      "at": "chef",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 书也分成一颗颗小头 [shot: chapter]
> 已知：英文小说的 Chapter 1
> 推进：把书的分章和“小头”相接，避免把 ter 当指小后缀
翻开英文小说，正文顶上常印着 {chapter|Chapter} 1。
一本书分成几块，每块顶着一个标题。
拉丁语把这样的部分叫小头。
这个词经过古法语，整体变成了 chapter，章。
小，属于拉丁语原词。
英语末尾的 ter，不是表示小的后缀。

```scene
{
  "requires": [
    "head"
  ],
  "learn": [
    {
      "id": "chapter",
      "label": "chapter",
      "detail": "拉丁语“小头” → 书的一章",
      "source": "lesson:chapter",
      "words": [
        "chapter"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "page",
      "type": "shape",
      "shape": "rect",
      "x": 160,
      "y": 160,
      "w": 745,
      "h": 740,
      "fill": "white",
      "stroke": "rule",
      "strokeWidth": 3
    },
    {
      "id": "chapter-title",
      "type": "text",
      "text": "Chapter 1",
      "x": 225,
      "y": 230,
      "w": 620,
      "h": 130,
      "size": 76,
      "font": "en",
      "color": "root",
      "relation": "chapter"
    },
    {
      "id": "body1",
      "type": "shape",
      "shape": "rect",
      "x": 225,
      "y": 430,
      "w": 590,
      "h": 4,
      "fill": "rule"
    },
    {
      "id": "body2",
      "type": "shape",
      "shape": "rect",
      "x": 225,
      "y": 490,
      "w": 540,
      "h": 4,
      "fill": "rule"
    },
    {
      "id": "body3",
      "type": "shape",
      "shape": "rect",
      "x": 225,
      "y": 550,
      "w": 590,
      "h": 4,
      "fill": "rule"
    },
    {
      "id": "body4",
      "type": "shape",
      "shape": "rect",
      "x": 225,
      "y": 610,
      "w": 480,
      "h": 4,
      "fill": "rule"
    },
    {
      "id": "little-head",
      "type": "text",
      "text": "capitulum\n小头",
      "x": 1060,
      "y": 230,
      "w": 690,
      "h": 200,
      "size": 69,
      "font": "en",
      "color": "root"
    },
    {
      "id": "borrow",
      "type": "line",
      "x": 1120,
      "y": 495,
      "w": 410,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "word",
      "type": "text",
      "relation": "chapter",
      "x": 1060,
      "y": 585,
      "w": 720,
      "h": 135,
      "size": 100,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "whole",
      "type": "text",
      "text": "整个词的历史变形",
      "x": 1060,
      "y": 780,
      "w": 720,
      "h": 80,
      "size": 36,
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "word",
      "at": "chapter",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 头，也可以是一条路的尽头 [shot: achieve]
> 已知：刚才头的位置、带头与标题
> 推进：在转折处整合母题，再引出达到终点
刚才的头，有形状，有主次，也有开端。
换到一条路上，还能指{end|尽头}。
拉丁语曾用头来表示末端，到头，就是完成。
这条关系经过法语，进入了 {achieve|achieve} a goal，达成目标。
重点在于事情做成了，不是在说一个首领。

```scene
{
  "requires": [
    "head",
    "chief",
    "chapter"
  ],
  "learn": [
    {
      "id": "achieve",
      "label": "achieve",
      "detail": "走到尽头 → 完成、达成",
      "source": "lesson:achieve",
      "words": [
        "achieve"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "known",
      "type": "text",
      "text": "形状 · 主次 · 开端",
      "x": 120,
      "y": 155,
      "w": 1680,
      "h": 95,
      "size": 47,
      "color": "muted"
    },
    {
      "id": "route",
      "type": "line",
      "x": 200,
      "y": 555,
      "w": 1460,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "traveler",
      "type": "shape",
      "shape": "ellipse",
      "x": 235,
      "y": 516,
      "w": 74,
      "h": 74,
      "fill": "root"
    },
    {
      "id": "start",
      "type": "text",
      "text": "开始",
      "x": 160,
      "y": 650,
      "w": 400,
      "h": 95,
      "size": 52
    },
    {
      "id": "end",
      "type": "text",
      "text": "尽头",
      "x": 1360,
      "y": 650,
      "w": 410,
      "h": 95,
      "size": 52,
      "opacity": 0
    },
    {
      "id": "word",
      "type": "text",
      "relation": "achieve",
      "x": 120,
      "y": 285,
      "w": 1550,
      "h": 145,
      "size": 120,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "example",
      "type": "text",
      "text": "achieve a goal",
      "x": 700,
      "y": 775,
      "w": 1090,
      "h": 95,
      "size": 57,
      "font": "en",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "end",
      "at": "end",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "traveler",
      "at": "end",
      "to": {
        "x": 1570
      },
      "duration": 2.4
    },
    {
      "target": "word",
      "at": "achieve",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "example",
      "at": "achieve",
      "to": {
        "opacity": 1
      },
      "duration": 0.5,
      "offset": 1
    }
  ]
}
```

## 从坏结局，到小淘气 [shot: mischief]
> 已知：achieve 的到头关系
> 推进：说明 mischief 的历史变化，不把现代词义机械拆成坏首领
同一条路，也可能走到坏结局。
{mischief|mischief} 的前面表示坏，后面接的是到头。
古时候，它可以说灾祸、不幸。
后来语气逐渐变轻。
今天的 {today|mischief}，多半是小孩的淘气、捣蛋。
词源告诉你来路，今天多重的语气，还得看语境。

```scene
{
  "requires": [
    "achieve"
  ],
  "learn": [
    {
      "id": "mischief",
      "label": "mischief",
      "detail": "坏结局 → 不幸；现代常指淘气",
      "source": "lesson:mischief",
      "words": [
        "mischief"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "mischief",
      "x": 120,
      "y": 160,
      "w": 1670,
      "h": 180,
      "size": 137,
      "font": "en",
      "color": "root"
    },
    {
      "id": "old",
      "type": "text",
      "text": "坏结局\n灾祸 · 不幸",
      "x": 130,
      "y": 445,
      "w": 710,
      "h": 230,
      "size": 65
    },
    {
      "id": "soften",
      "type": "line",
      "x": 855,
      "y": 560,
      "w": 180,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "today",
      "type": "text",
      "text": "淘气 · 捣蛋",
      "x": 1150,
      "y": 490,
      "w": 650,
      "h": 160,
      "size": 64,
      "opacity": 0
    },
    {
      "id": "example",
      "type": "text",
      "text": "full of mischief",
      "x": 1150,
      "y": 720,
      "w": 660,
      "h": 105,
      "size": 54,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "time",
      "type": "text",
      "text": "语气随历史变化",
      "x": 130,
      "y": 780,
      "w": 740,
      "h": 90,
      "size": 37,
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "today",
      "at": "today",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "example",
      "at": "today",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 回到 capital，先看位置 [shot: capital-position]
> 已知：国家的中心、句子的开头
> 推进：逐个解开 capital 的首都与大写义
现在回到开头的 capital。
表示头的词干，接上词尾，就成了头的、主要的。
{city|首都}，是一个国家的头。
中文的首，也已经把关系说出来了。
{letter|大写字母}，站在句子或单词的头上。
先把这两个意思接回头的位置。

```scene
{
  "requires": [
    "head",
    "chief"
  ],
  "learn": [
    {
      "id": "capital-city",
      "label": "capital city",
      "detail": "国家的头 → 首都",
      "source": "lesson:capital",
      "words": [
        "capital"
      ],
      "kind": "etymology"
    },
    {
      "id": "capital-letter",
      "label": "capital letter",
      "detail": "句子或单词开头 → 大写字母",
      "source": "lesson:capital",
      "words": [],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "capital",
      "type": "text",
      "text": "capital",
      "x": 120,
      "y": 140,
      "w": 1680,
      "h": 180,
      "size": 133,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "capit",
          "color": "root"
        },
        {
          "text": "al",
          "color": "suffix"
        }
      ]
    },
    {
      "id": "city",
      "type": "shape",
      "shape": "path",
      "x": 205,
      "y": 400,
      "w": 470,
      "h": 260,
      "fill": "green",
      "d": "M10 75 L235 5 L460 75 Z M45 95 H425 V245 H45 Z M100 105 V230 M185 105 V230 M285 105 V230 M370 105 V230",
      "stroke": "root",
      "strokeWidth": 7
    },
    {
      "id": "city-label",
      "type": "text",
      "relation": "capital-city",
      "x": 140,
      "y": 735,
      "w": 700,
      "h": 100,
      "size": 61,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "capital-a",
      "type": "text",
      "text": "A",
      "x": 1060,
      "y": 330,
      "w": 190,
      "h": 310,
      "size": 244,
      "font": "en",
      "color": "root"
    },
    {
      "id": "sentence",
      "type": "text",
      "text": "new chapter.",
      "x": 1270,
      "y": 510,
      "w": 500,
      "h": 100,
      "size": 53,
      "font": "en"
    },
    {
      "id": "letter-label",
      "type": "text",
      "relation": "capital-letter",
      "x": 1040,
      "y": 735,
      "w": 750,
      "h": 100,
      "size": 61,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "morpheme",
      "type": "text",
      "text": "capit + -al  头的",
      "x": 1030,
      "y": 175,
      "w": 765,
      "h": 105,
      "size": 43,
      "font": "en",
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "city-label",
      "at": "city",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "letter-label",
      "at": "letter",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 钱里的头，是哪一份 [shot: capital-money]
> 已知：本金与利息的区别
> 推进：给资本义补出 principal sum 的中间桥梁
钱里的头，又是什么？
一笔借款里，{principal|本金}是主要的那份。
利息，是另外付出的部分。
capital 的这条意思，从主要财产、本金走到了{capital|资本}。

```scene
{
  "requires": [
    "head",
    "chief"
  ],
  "learn": [
    {
      "id": "capital-money",
      "label": "capital",
      "detail": "主要财产、本金 → 资本",
      "source": "lesson:capital",
      "words": [
        "capital"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "heading",
      "type": "text",
      "text": "一笔借款",
      "x": 120,
      "y": 160,
      "w": 1680,
      "h": 100,
      "size": 63
    },
    {
      "id": "principal-box",
      "type": "shape",
      "shape": "rect",
      "x": 150,
      "y": 350,
      "w": 980,
      "h": 330,
      "fill": "green"
    },
    {
      "id": "principal",
      "type": "text",
      "text": "principal\n本金",
      "x": 200,
      "y": 405,
      "w": 850,
      "h": 220,
      "size": 76,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "interest-box",
      "type": "shape",
      "shape": "rect",
      "x": 1250,
      "y": 440,
      "w": 520,
      "h": 210,
      "fill": "blue"
    },
    {
      "id": "interest",
      "type": "text",
      "text": "interest\n利息",
      "x": 1300,
      "y": 465,
      "w": 400,
      "h": 160,
      "size": 58,
      "font": "en"
    },
    {
      "id": "capital",
      "type": "text",
      "relation": "capital-money",
      "x": 150,
      "y": 760,
      "w": 1550,
      "h": 120,
      "size": 100,
      "font": "en",
      "color": "root",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "principal",
      "at": "principal",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "capital",
      "at": "capital",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 有时，头指的是生命 [shot: capital-life]
> 已知：capital 的形状与主次两条线
> 推进：解释死刑义而不误说成某一种行刑方式
还有 capital punishment，死刑。
这里碰到的是{life|生命}。
头，可以用来代表一个人的性命。
所以它说的是死亡的惩罚，不限定哪种执行方式。

```scene
{
  "requires": [
    "head"
  ],
  "learn": [
    {
      "id": "capital-life",
      "label": "capital punishment",
      "detail": "牵连头、性命 → 死刑",
      "source": "lesson:capital",
      "words": [
        "capital"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "phrase",
      "type": "text",
      "relation": "capital-life",
      "x": 120,
      "y": 210,
      "w": 1680,
      "h": 170,
      "size": 110,
      "font": "en",
      "color": "root"
    },
    {
      "id": "head",
      "type": "shape",
      "shape": "path",
      "x": 245,
      "y": 450,
      "w": 235,
      "h": 280,
      "fill": "green",
      "stroke": "root",
      "strokeWidth": 4,
      "d": "M120 8 C55 4 18 52 23 105 C23 158 45 182 61 197 L61 257 H139 L140 200 C180 191 192 165 191 142 L213 142 L201 113 L201 99 C196 40 161 8 120 8 Z"
    },
    {
      "id": "link",
      "type": "line",
      "x": 570,
      "y": 605,
      "w": 350,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "life",
      "type": "text",
      "text": "life\n生命",
      "x": 1050,
      "y": 465,
      "w": 700,
      "h": 250,
      "size": 95,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "meaning",
      "type": "text",
      "text": "头 → 性命",
      "x": 120,
      "y": 775,
      "w": 780,
      "h": 90,
      "size": 48,
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "life",
      "at": "life",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 资本的亲戚，在牧场上 [shot: capital-cattle]
> 已知：capital 的财产支线
> 推进：用共同来源的分叉解释 cattle，明确不是资本直接变牛
财产这条支线，还藏着一个意外的亲戚。
牧场上的牛，a herd of {cattle|cattle}。
中世纪拉丁语里，表示主要财产的词，分出了两条路。
一条进入资本这个意思。
另一条经过法语，早先各种{property|财产}都能指。
后来多指牲畜，再收窄到{cows|牛}。
capital 和 cattle，是共同来源的两支。

```scene
{
  "requires": [
    "capital-money"
  ],
  "learn": [
    {
      "id": "cattle",
      "label": "capital / cattle",
      "detail": "同一财产词源的两支；牲畜 → 牛",
      "source": "lesson:cattle",
      "words": [
        "cattle"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "origin",
      "type": "text",
      "text": "capitale · 财产",
      "x": 550,
      "y": 145,
      "w": 1100,
      "h": 120,
      "size": 77,
      "font": "en",
      "color": "root",
      "relation": "cattle"
    },
    {
      "id": "left-branch",
      "type": "line",
      "x": 470,
      "y": 310,
      "w": 430,
      "h": 110,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4,
      "points": [
        [
          430,
          0
        ],
        [
          0,
          110
        ]
      ]
    },
    {
      "id": "right-branch",
      "type": "line",
      "x": 1030,
      "y": 310,
      "w": 380,
      "h": 110,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4,
      "points": [
        [
          0,
          0
        ],
        [
          380,
          110
        ]
      ]
    },
    {
      "id": "capital",
      "type": "text",
      "text": "capital\n资本",
      "x": 145,
      "y": 455,
      "w": 640,
      "h": 230,
      "size": 88,
      "font": "en",
      "color": "root"
    },
    {
      "id": "cows",
      "type": "image",
      "file": "media/cattle.jpg",
      "credit": "Quintin Soloviev · CC BY 4.0 · Wikimedia Commons",
      "x": 1040,
      "y": 550,
      "w": 760,
      "h": 310,
      "opacity": 0,
      "crop": [
        0,
        0.28,
        1,
        0.57
      ]
    },
    {
      "id": "stages",
      "type": "text",
      "text": "财产 → 牲畜 → 牛",
      "x": 1040,
      "y": 872,
      "w": 680,
      "h": 48,
      "size": 33,
      "opacity": 0
    },
    {
      "id": "cattle",
      "type": "text",
      "text": "cattle",
      "x": 1090,
      "y": 435,
      "w": 700,
      "h": 95,
      "size": 75,
      "font": "en",
      "color": "root",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "cattle",
      "at": "cattle",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "cows",
      "at": "cattle",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "stages",
      "at": "property",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 最后两颗头，在你的胳膊上 [shot: biceps]
> 已知：身体的头和一个部位的起点
> 推进：通过双起点的结构理解二头肌
> 来源：https://www.etymonline.com/word/biceps
再低头看看胳膊。
二头肌的两颗头，指的是{two|两个起点}。
The {biceps|biceps} has two heads，二头肌有两个头。
前面表示二，后面仍是头的变形。

```scene
{
  "requires": [
    "head"
  ],
  "learn": [
    {
      "id": "biceps",
      "label": "biceps",
      "detail": "两个头 = 肌肉的两处起点",
      "source": "https://www.etymonline.com/word/biceps",
      "words": [
        "biceps"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "biceps",
      "x": 120,
      "y": 175,
      "w": 770,
      "h": 175,
      "size": 142,
      "font": "en",
      "color": "root"
    },
    {
      "id": "parts",
      "type": "text",
      "text": "bi- 二   +   -ceps 头",
      "x": 125,
      "y": 420,
      "w": 760,
      "h": 120,
      "size": 44,
      "font": "en"
    },
    {
      "id": "phrase",
      "type": "text",
      "text": "two distinct origins",
      "x": 120,
      "y": 700,
      "w": 800,
      "h": 100,
      "size": 50,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "tendon-left",
      "type": "shape",
      "shape": "path",
      "x": 1090,
      "y": 280,
      "w": 170,
      "h": 370,
      "fill": "none",
      "d": "M0 0 C0 120 80 190 160 360",
      "stroke": "prefix",
      "strokeWidth": 12
    },
    {
      "id": "tendon-right",
      "type": "shape",
      "shape": "path",
      "x": 1300,
      "y": 280,
      "w": 190,
      "h": 370,
      "fill": "none",
      "d": "M180 0 C170 100 100 220 0 360",
      "stroke": "root",
      "strokeWidth": 12
    },
    {
      "id": "muscle",
      "type": "shape",
      "shape": "ellipse",
      "x": 1185,
      "y": 565,
      "w": 225,
      "h": 265,
      "fill": "green",
      "stroke": "root",
      "strokeWidth": 5
    },
    {
      "id": "origin1",
      "type": "shape",
      "shape": "ellipse",
      "x": 1066,
      "y": 250,
      "w": 40,
      "h": 40,
      "fill": "prefix"
    },
    {
      "id": "origin2",
      "type": "shape",
      "shape": "ellipse",
      "x": 1460,
      "y": 250,
      "w": 40,
      "h": 40,
      "fill": "root"
    },
    {
      "id": "origin-label",
      "type": "text",
      "text": "起点          起点",
      "x": 1000,
      "y": 155,
      "w": 660,
      "h": 90,
      "size": 41
    },
    {
      "id": "diagram",
      "type": "text",
      "text": "结构示意",
      "x": 1490,
      "y": 815,
      "w": 300,
      "h": 75,
      "size": 30,
      "color": "muted"
    },
    {
      "id": "muscle-label",
      "type": "text",
      "text": "同一块肌肉",
      "x": 1460,
      "y": 690,
      "w": 350,
      "h": 80,
      "size": 36,
      "color": "muted"
    }
  ],
  "events": [
    {
      "target": "phrase",
      "at": "two",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 把头的形状和作用接起来 [shot: close-shape-role]
> 已知：刚讲过的菜、领头者、章节与二头肌
> 推进：收拢形状、位置、作用和起点，不引入未讲的新亲戚
把刚才的关系连起来。
卷心菜像头，captain、chief 是带头的，chef 是厨房的头。
chapter 把书分成小头，二头肌有两处起点。

```scene
{
  "closing": true,
  "recall": [
    "head",
    "cabbage",
    "captain",
    "chief",
    "chapter",
    "biceps"
  ],
  "nodes": [
    {
      "id": "summary",
      "type": "summary",
      "refs": [
        "head",
        "cabbage",
        "captain",
        "chief",
        "chapter",
        "biceps"
      ],
      "heading": "形状 · 位置 · 作用",
      "x": 120,
      "y": 180,
      "w": 1680,
      "h": 690,
      "layout": "branches"
    }
  ],
  "events": []
}
```

## 认亲，也要保留边界 [shot: close-boundaries]
> 已知：完成、淘气，以及 captain 和 capture
> 推进：把语义变化和同形异源一起收束
走到尽头，接到的是完成、达成。
mischief 从坏结局，走到了今天常说的淘气。
那个表示抓的词，要留在这家之外。

```scene
{
  "closing": true,
  "recall": [
    "achieve",
    "mischief",
    "capture-contrast"
  ],
  "nodes": [
    {
      "id": "summary",
      "type": "summary",
      "refs": [
        "achieve",
        "mischief",
        "capture-contrast"
      ],
      "heading": "来路相连，今天的意思仍看语境",
      "x": 120,
      "y": 180,
      "w": 1680,
      "h": 690,
      "layout": "branches"
    }
  ],
  "events": []
}
```

## 四个意思，都有来路 [shot: close-capital]
> 已知：开头留下的 capital 四义疑问
> 推进：完整回答开场，并让 cattle 财产分支留下
回到 capital，国家的头、句子的头、钱的主要部分、人的性命。
四个意思，都接回同一个头。
财产那条路，还分出了牧场上的牛。

```scene
{
  "closing": true,
  "recall": [
    "capital-city",
    "capital-letter",
    "capital-money",
    "capital-life",
    "cattle"
  ],
  "nodes": [
    {
      "id": "summary",
      "type": "summary",
      "refs": [
        "capital-city",
        "capital-letter",
        "capital-money",
        "capital-life",
        "cattle"
      ],
      "heading": "capital 的四义与财产分支",
      "x": 120,
      "y": 180,
      "w": 1680,
      "h": 690,
      "layout": "branches"
    }
  ],
  "events": []
}
```
