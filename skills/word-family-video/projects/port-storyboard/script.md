---
lesson: port
status: approved
checked: 2316e28d · 用户授权 AI 审核 · 2026-10-30
spine: 从充电线两端的 port 出发；用身体搬运建立词根，让同一张照片复制、导出再导入，转到跨越、支撑、报告和意义，完整接回动作与入口的两条直接来路
seed: 20261030
---

## 一条线，两种 port [shot: two-ports]
> 已知：充电宝和手机接口
> 推进：提出便携与接口为什么长得相同的疑问
> 来源：https://support.apple.com/en-us/105099
手机快没电，掏出一块 {portable|portable} charger，充电宝。
线那头插进去的口，又叫 USB-C {port|port}。
同样四个字母，一边说便携，一边说接口。
它们讲的是同一件事吗？

```scene
{
  "nodes": [
    {
      "id": "charger",
      "type": "image",
      "file": "media/charger.jpg",
      "credit": "Anker · 产品图",
      "x": 115,
      "y": 310,
      "w": 790,
      "h": 520
    },
    {
      "id": "socket",
      "type": "image",
      "file": "media/usb-c-port.jpg",
      "credit": "Kyu3 · CC BY-SA 4.0 · Wikimedia Commons",
      "x": 1000,
      "y": 360,
      "w": 805,
      "h": 400,
      "crop": [
        0,
        0.32,
        1,
        0.43
      ]
    },
    {
      "id": "portable",
      "type": "text",
      "text": "portable charger",
      "x": 120,
      "y": 155,
      "w": 790,
      "h": 130,
      "size": 82,
      "font": "en",
      "color": "root"
    },
    {
      "id": "port",
      "type": "text",
      "text": "USB-C port",
      "x": 1000,
      "y": 155,
      "w": 800,
      "h": 130,
      "size": 87,
      "font": "en",
      "color": "prefix",
      "opacity": 0
    },
    {
      "id": "left-cn",
      "type": "text",
      "text": "能带走",
      "x": 120,
      "y": 805,
      "w": 790,
      "h": 80,
      "size": 41
    },
    {
      "id": "right-cn",
      "type": "text",
      "text": "一个接口",
      "x": 1000,
      "y": 805,
      "w": 790,
      "h": 80,
      "size": 41,
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "port",
      "at": "port",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "right-cn",
      "at": "port",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ],
  "family": ""
}
```

## 先看搬，再理解能带走 [shot: carry-portable]
> 已知：手提箱子和随身携带设备
> 推进：用完整身体动作建立搬运，再解释 portable
先记住一个动作，把东西从这儿{carry|搬}到那儿。
这一家的词根，来自拉丁语的搬、带。
箱子能搬，手里的小机器也能带出门。
后面的词尾表示能，能被携带，就是 {portable|portable}。
a portable charger，便携充电器。

```scene
{
  "learn": [
    {
      "id": "carry",
      "label": "portare",
      "detail": "搬、带：这一家的共同动作",
      "source": "lesson:portable",
      "words": [],
      "kind": "etymology"
    },
    {
      "id": "portable",
      "label": "portable",
      "detail": "能被携带 → 便携的",
      "source": "lesson:portable",
      "words": [
        "portable"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "portable",
      "x": 120,
      "y": 150,
      "w": 1660,
      "h": 175,
      "size": 133,
      "font": "en",
      "color": "root",
      "opacity": 0,
      "runs": [
        {
          "text": "port",
          "color": "root"
        },
        {
          "text": "able",
          "color": "suffix"
        }
      ]
    },
    {
      "id": "root",
      "type": "text",
      "relation": "carry",
      "x": 120,
      "y": 150,
      "w": 1660,
      "h": 150,
      "size": 113,
      "font": "en",
      "color": "root"
    },
    {
      "id": "carrier",
      "type": "illustration",
      "items": [
        {
          "k": "fig",
          "x": 80,
          "pose": "carry",
          "id": "carrier",
          "motion": {
            "from": [
              204,
              108
            ],
            "duration": 3.2
          },
          "flip": 1
        },
        {
          "k": "rect",
          "x": 62,
          "y": 12,
          "w": 36,
          "h": 18,
          "follow": "carrier"
        }
      ],
      "x": 140,
      "y": 335,
      "w": 1635,
      "h": 455,
      "actionAt": "carry",
      "actLevel": "明显",
      "relation": "carry"
    },
    {
      "id": "parts",
      "type": "text",
      "text": "port 搬、带  +  -able 能……的",
      "x": 150,
      "y": 810,
      "w": 1570,
      "h": 95,
      "size": 49,
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "root",
      "at": "portable",
      "to": {
        "opacity": 0
      },
      "duration": 0.22
    },
    {
      "target": "word",
      "at": "portable",
      "to": {
        "opacity": 1
      },
      "duration": 0.35,
      "offset": 0.22
    },
    {
      "target": "parts",
      "at": "portable",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 接口讲的是入口 [shot: socket-gateway]
> 已知：刚刚建立的搬运动作
> 推进：把 portare 的搬与 porta 的入口分清，避免声称远源毫无关系
> 来源：https://www.etymonline.com/word/portable
> 来源：https://www.etymonline.com/word/port
> 来源：https://support.apple.com/en-us/105099
再看线插进去的这个口。
它是设备的出入口，电和数据可以从这里进出。
接口这个 {port|port}，接的是门、通道这条来路。
portable 里的部分，说的是搬运。
这里分清的是直接来路，一个讲动作，一个讲入口。

```scene
{
  "requires": [
    "carry",
    "portable"
  ],
  "learn": [
    {
      "id": "port-contrast",
      "label": "portable / port",
      "detail": "搬运的词干；接口接到入口义",
      "source": "https://www.etymonline.com/word/port",
      "words": [
        "port"
      ],
      "kind": "contrast"
    }
  ],
  "nodes": [
    {
      "id": "socket",
      "type": "image",
      "file": "media/usb-c-port.jpg",
      "credit": "Kyu3 · CC BY-SA 4.0 · Wikimedia Commons",
      "x": 120,
      "y": 150,
      "w": 1680,
      "h": 475,
      "crop": [
        0.06,
        0.3,
        0.91,
        0.46
      ],
      "relation": "port-contrast"
    },
    {
      "id": "left",
      "type": "text",
      "text": "portare\n搬、带",
      "x": 140,
      "y": 715,
      "w": 760,
      "h": 145,
      "size": 59,
      "font": "en",
      "color": "root"
    },
    {
      "id": "right",
      "type": "text",
      "text": "porta / portal\n门、入口",
      "x": 1060,
      "y": 715,
      "w": 740,
      "h": 145,
      "size": 59,
      "font": "en",
      "color": "prefix",
      "opacity": 0
    },
    {
      "id": "point",
      "type": "line",
      "x": 948,
      "y": 328,
      "w": 4,
      "h": 100,
      "stroke": "prefix",
      "arrow": true,
      "strokeWidth": 4,
      "points": [
        [
          2,
          100
        ],
        [
          2,
          0
        ]
      ]
    }
  ],
  "events": [
    {
      "target": "right",
      "at": "port",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 这次搬进来的是照片 [shot: import-photo]
> 已知：手机里的照片和电脑相册
> 推进：把 import 的向内关系接到导入与进口
> 来源：https://support.microsoft.com/en-us/windows/import-photos-and-videos-from-phone-to-pc-aed09800-f826-4d40-a243-7640de229d9d
线接上电脑，照片就能从手机进入相册。
Windows 照片应用里，这一步写着 {import|Import}。
前面的部分表示往里，后面仍是搬。
Import photos，就是导入照片。
搬进国境的换成货物，就是进口。
这里的词头讲方向，不是否定。

```scene
{
  "requires": [
    "carry"
  ],
  "learn": [
    {
      "id": "import",
      "label": "import",
      "detail": "往参照里面搬 → 导入、进口",
      "source": "lesson:import",
      "words": [
        "import"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "import",
      "x": 120,
      "y": 140,
      "w": 1680,
      "h": 175,
      "size": 131,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "im",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        }
      ]
    },
    {
      "id": "phone",
      "type": "shape",
      "shape": "rect",
      "x": 185,
      "y": 360,
      "w": 390,
      "h": 505,
      "fill": "white",
      "stroke": "ink",
      "strokeWidth": 5,
      "radius": 28
    },
    {
      "id": "phone-label",
      "type": "text",
      "text": "手机",
      "x": 220,
      "y": 365,
      "w": 320,
      "h": 75,
      "size": 39
    },
    {
      "id": "source",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 225,
      "y": 450,
      "w": 310,
      "h": 370
    },
    {
      "id": "album",
      "type": "shape",
      "shape": "rect",
      "x": 1050,
      "y": 355,
      "w": 740,
      "h": 520,
      "fill": "green",
      "stroke": "rule",
      "strokeWidth": 3
    },
    {
      "id": "app-name",
      "type": "text",
      "text": "照片应用",
      "x": 1100,
      "y": 365,
      "w": 630,
      "h": 80,
      "size": 40
    },
    {
      "id": "inward",
      "type": "line",
      "x": 640,
      "y": 600,
      "w": 345,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "copy",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 225,
      "y": 450,
      "w": 310,
      "h": 370,
      "opacity": 0
    },
    {
      "id": "example",
      "type": "text",
      "text": "Import photos",
      "x": 1090,
      "y": 735,
      "w": 670,
      "h": 110,
      "size": 53,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "demo",
      "type": "text",
      "text": "操作示意",
      "x": 1470,
      "y": 300,
      "w": 310,
      "h": 55,
      "size": 27,
      "color": "muted"
    },
    {
      "id": "morpheme",
      "type": "text",
      "text": "in- → im-  往里",
      "x": 1030,
      "y": 175,
      "w": 765,
      "h": 105,
      "size": 43,
      "font": "en",
      "color": "prefix"
    }
  ],
  "events": [
    {
      "target": "copy",
      "at": "import",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "copy",
      "at": "import",
      "to": {
        "x": 1300,
        "y": 450,
        "w": 230,
        "h": 280
      },
      "duration": 2.4
    },
    {
      "target": "example",
      "at": "import",
      "to": {
        "opacity": 1
      },
      "duration": 0.5,
      "offset": 2.5
    }
  ]
}
```

## 修好的照片，还要送出去 [shot: export-photo]
> 已知：照片已经进入软件
> 推进：把 export 与软件边界及货物出口相接
> 来源：https://support.apple.com/guide/photos/export-photos-videos-and-slideshows-pht6e157c5f/mac
照片整理好了，要另存一份发给朋友。
在 Mac 的照片应用里，文件菜单有 {export|Export}。
前面表示往外，后面还是搬。
把照片往软件外送，就是导出。
送到别国的货物，就叫出口，也不一定经过港口。

```scene
{
  "requires": [
    "import"
  ],
  "learn": [
    {
      "id": "export",
      "label": "export",
      "detail": "往参照外面搬 → 导出、出口",
      "source": "lesson:export",
      "words": [
        "export"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "export",
      "x": 120,
      "y": 140,
      "w": 1680,
      "h": 175,
      "size": 131,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "ex",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        }
      ]
    },
    {
      "id": "app",
      "type": "shape",
      "shape": "rect",
      "x": 140,
      "y": 350,
      "w": 690,
      "h": 535,
      "fill": "green",
      "stroke": "rule",
      "strokeWidth": 3
    },
    {
      "id": "menu",
      "type": "text",
      "text": "File  ›  Export",
      "x": 175,
      "y": 355,
      "w": 610,
      "h": 80,
      "size": 42,
      "font": "en"
    },
    {
      "id": "original",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 350,
      "y": 465,
      "w": 255,
      "h": 310
    },
    {
      "id": "exported",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 350,
      "y": 465,
      "w": 255,
      "h": 310,
      "opacity": 0
    },
    {
      "id": "arrow",
      "type": "line",
      "x": 845,
      "y": 615,
      "w": 350,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "file-name",
      "type": "text",
      "text": "Photo.jpg",
      "x": 1250,
      "y": 790,
      "w": 520,
      "h": 80,
      "size": 51,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "outside",
      "type": "text",
      "text": "软件外的图片文件",
      "x": 1130,
      "y": 355,
      "w": 680,
      "h": 85,
      "size": 40
    },
    {
      "id": "demo",
      "type": "text",
      "text": "操作示意",
      "x": 1400,
      "y": 285,
      "w": 390,
      "h": 55,
      "size": 27,
      "color": "muted"
    },
    {
      "id": "morpheme",
      "type": "text",
      "text": "ex-  往外",
      "x": 1030,
      "y": 175,
      "w": 765,
      "h": 105,
      "size": 43,
      "font": "en",
      "color": "prefix"
    }
  ],
  "events": [
    {
      "target": "exported",
      "at": "export",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "exported",
      "at": "export",
      "to": {
        "x": 1360
      },
      "duration": 2.4
    },
    {
      "target": "file-name",
      "at": "export",
      "to": {
        "opacity": 1
      },
      "duration": 0.4,
      "offset": 2.4
    }
  ]
}
```

## 同一张照片，方向为什么变了 [shot: reference]
> 已知：刚讲过的导入与导出
> 推进：在同一个镜头里改变参照，保留数字搬运的原件
> 来源：https://support.apple.com/guide/photos/export-photos-videos-and-slideshows-pht6e157c5f/mac
让同一张照片，接着进入另一个软件。
对发出它的软件，这一步叫 {export|export}。
对接收它的软件，这一步又叫 {import|import}。
进和出，先要认清是谁的里面。
数字的搬运，可以把原件留下。

```scene
{
  "requires": [
    "import",
    "export"
  ],
  "learn": [
    {
      "id": "reference",
      "label": "export → import",
      "detail": "同一次传递，参照不同；原件可保留",
      "source": "https://support.apple.com/guide/photos/export-photos-videos-and-slideshows-pht6e157c5f/mac",
      "words": [],
      "kind": "usage"
    }
  ],
  "nodes": [
    {
      "id": "app-a",
      "type": "shape",
      "shape": "rect",
      "x": 120,
      "y": 335,
      "w": 680,
      "h": 550,
      "fill": "white",
      "stroke": "rule",
      "strokeWidth": 3,
      "radius": 12
    },
    {
      "id": "app-b",
      "type": "shape",
      "shape": "rect",
      "x": 1090,
      "y": 335,
      "w": 710,
      "h": 550,
      "fill": "white",
      "stroke": "rule",
      "strokeWidth": 3,
      "radius": 12
    },
    {
      "id": "a-name",
      "type": "text",
      "text": "软件 A",
      "x": 155,
      "y": 345,
      "w": 610,
      "h": 80,
      "size": 36,
      "color": "muted"
    },
    {
      "id": "b-name",
      "type": "text",
      "text": "软件 B",
      "x": 1130,
      "y": 345,
      "w": 630,
      "h": 80,
      "size": 36,
      "color": "muted"
    },
    {
      "id": "source",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 290,
      "y": 455,
      "w": 270,
      "h": 328
    },
    {
      "id": "copy",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 290,
      "y": 455,
      "w": 270,
      "h": 328,
      "opacity": 0
    },
    {
      "id": "direction",
      "type": "line",
      "x": 800,
      "y": 615,
      "w": 260,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "demo",
      "type": "text",
      "text": "操作示意",
      "x": 1420,
      "y": 830,
      "w": 330,
      "h": 55,
      "size": 26,
      "color": "muted"
    },
    {
      "id": "relation",
      "type": "text",
      "relation": "reference",
      "x": 120,
      "y": 145,
      "w": 1680,
      "h": 125,
      "size": 83,
      "font": "en",
      "color": "root"
    },
    {
      "id": "out-label",
      "type": "text",
      "text": "export · 导出",
      "x": 145,
      "y": 795,
      "w": 530,
      "h": 76,
      "size": 43,
      "font": "en",
      "opacity": 0
    },
    {
      "id": "in-label",
      "type": "text",
      "text": "import · 导入",
      "x": 1120,
      "y": 795,
      "w": 570,
      "h": 76,
      "size": 43,
      "font": "en",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "out-label",
      "at": "export",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "copy",
      "at": "export",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "copy",
      "at": "export",
      "to": {
        "x": 1310
      },
      "duration": 2.6
    },
    {
      "target": "in-label",
      "at": "import",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 一车人，也能被搬过去 [shot: transport]
> 已知：照片跨过软件边界
> 推进：从可见交通解释 trans 的跨越与 transport
照片能搬，人也能搬。
从城这头坐到那头，你用的是 public {transport|transport}，公共交通。
前面的部分表示跨过去，到另一边。
把人或东西跨地运过去，就是运输。
对象换了，跨过去的关系还在。

```scene
{
  "requires": [
    "carry",
    "reference"
  ],
  "learn": [
    {
      "id": "transport",
      "label": "transport",
      "detail": "跨到另一边 → 运输、交通",
      "source": "lesson:transport",
      "words": [
        "transport"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "transport",
      "x": 120,
      "y": 150,
      "w": 1680,
      "h": 175,
      "size": 124,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "trans",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        }
      ]
    },
    {
      "id": "example",
      "type": "text",
      "text": "public transport",
      "x": 120,
      "y": 315,
      "w": 1580,
      "h": 95,
      "size": 55,
      "font": "en"
    },
    {
      "id": "road",
      "type": "shape",
      "shape": "rect",
      "x": 150,
      "y": 725,
      "w": 1620,
      "h": 5,
      "fill": "rule"
    },
    {
      "id": "from",
      "type": "text",
      "text": "这头",
      "x": 150,
      "y": 795,
      "w": 490,
      "h": 80,
      "size": 44
    },
    {
      "id": "to",
      "type": "text",
      "text": "那头",
      "x": 1410,
      "y": 795,
      "w": 390,
      "h": 80,
      "size": 44
    },
    {
      "id": "bus",
      "type": "shape",
      "shape": "rect",
      "x": 210,
      "y": 475,
      "w": 450,
      "h": 200,
      "fill": "green",
      "stroke": "root",
      "strokeWidth": 4,
      "radius": 18
    },
    {
      "id": "windows",
      "type": "shape",
      "shape": "rect",
      "x": 250,
      "y": 505,
      "w": 365,
      "h": 75,
      "fill": "white",
      "stroke": "rule",
      "strokeWidth": 3
    },
    {
      "id": "wheel1",
      "type": "shape",
      "shape": "ellipse",
      "x": 265,
      "y": 655,
      "w": 70,
      "h": 70,
      "fill": "ink"
    },
    {
      "id": "wheel2",
      "type": "shape",
      "shape": "ellipse",
      "x": 535,
      "y": 655,
      "w": 70,
      "h": 70,
      "fill": "ink"
    },
    {
      "id": "cross",
      "type": "line",
      "x": 810,
      "y": 590,
      "w": 860,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4
    },
    {
      "id": "morpheme",
      "type": "text",
      "text": "trans-  跨过",
      "x": 1030,
      "y": 175,
      "w": 765,
      "h": 105,
      "size": 43,
      "font": "en",
      "color": "prefix"
    }
  ],
  "events": [
    {
      "target": "bus",
      "at": "transport",
      "to": {
        "x": 1150
      },
      "duration": 3
    },
    {
      "target": "windows",
      "at": "transport",
      "to": {
        "x": 1190
      },
      "duration": 3
    },
    {
      "target": "wheel1",
      "at": "transport",
      "to": {
        "x": 1205
      },
      "duration": 3
    },
    {
      "target": "wheel2",
      "at": "transport",
      "to": {
        "x": 1475
      },
      "duration": 3
    }
  ]
}
```

## 这次，从下面托住 [shot: support-body]
> 已知：搬的动作和重物会下落
> 推进：用接触动作呈现 support 的向上承托与词头同化
横梁要往下掉，从底下把它{lift|托}住。
这回，力量从下面往上。
这个动作叫 {support|support}，支撑。
词头表示从下面，碰到后面的声音，变成了现在的拼法。
托住一块木板，是最看得见的支撑。

```scene
{
  "requires": [
    "carry"
  ],
  "learn": [
    {
      "id": "support-body",
      "label": "support",
      "detail": "从下面承托 → 支撑",
      "source": "lesson:support",
      "words": [
        "support"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "support-body",
      "x": 120,
      "y": 145,
      "w": 1680,
      "h": 175,
      "size": 125,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "sup",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        }
      ]
    },
    {
      "id": "lift",
      "type": "illustration",
      "ref": "support",
      "x": 150,
      "y": 320,
      "w": 1600,
      "h": 455,
      "actionAt": "lift",
      "actLevel": "明显",
      "relation": "support-body"
    },
    {
      "id": "parts",
      "type": "text",
      "text": "sub- 从下面  →  sup-",
      "x": 160,
      "y": 815,
      "w": 1570,
      "h": 95,
      "size": 50,
      "font": "en",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "parts",
      "at": "support",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 撑住的也可以是生活 [shot: support-family]
> 已知：横梁需要下面的支撑
> 推进：从承托连接供养，不把所有 support 都限于物理动作
> 来源：https://www.etymonline.com/word/support
如果被撑住的，是一家人的生活呢？
提供食物、住处和日常所需，叫 support a {family|family}。
供养一家人。
支撑的对象，已经从木板换成了生活。

```scene
{
  "requires": [
    "support-body"
  ],
  "learn": [
    {
      "id": "support-family",
      "label": "support a family",
      "detail": "提供生活所需 → 供养",
      "source": "lesson:support",
      "words": [
        "support"
      ],
      "kind": "usage"
    }
  ],
  "nodes": [
    {
      "id": "phrase",
      "type": "text",
      "relation": "support-family",
      "x": 120,
      "y": 145,
      "w": 1680,
      "h": 150,
      "size": 101,
      "font": "en",
      "color": "root"
    },
    {
      "id": "house",
      "type": "shape",
      "shape": "path",
      "x": 270,
      "y": 350,
      "w": 535,
      "h": 385,
      "fill": "white",
      "d": "M10 155 L268 5 L525 155 M65 132 V375 H470 V132 M205 375 V230 H330 V375",
      "stroke": "root",
      "strokeWidth": 7
    },
    {
      "id": "needs",
      "type": "text",
      "text": "食物\n住处\n生活所需",
      "x": 1110,
      "y": 370,
      "w": 650,
      "h": 295,
      "size": 62
    },
    {
      "id": "base",
      "type": "shape",
      "shape": "rect",
      "x": 160,
      "y": 760,
      "w": 1600,
      "h": 20,
      "fill": "root",
      "opacity": 0
    },
    {
      "id": "meaning",
      "type": "text",
      "text": "供养",
      "x": 120,
      "y": 820,
      "w": 1680,
      "h": 80,
      "size": 54,
      "align": "center",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "base",
      "at": "family",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "meaning",
      "at": "family",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 设备正常运转，也需要支撑 [shot: support-tech]
> 已知：手机和电脑连接不上的经验
> 推进：用真实帮助页解释技术支持
> 来源：https://support.apple.com/en-us/105099
> 来源：https://www.etymonline.com/word/support
如果手机和电脑连不上，去网站的 {support|Support} 找帮助。
眼前就是苹果讲解充电和连接的页面。
让设备恢复工作，这种服务叫 tech support。
被撑住的，换成了设备的正常运转。

```scene
{
  "requires": [
    "support-body",
    "support-family"
  ],
  "learn": [
    {
      "id": "support-tech",
      "label": "tech support",
      "detail": "帮助设备履行功能、保持运作",
      "source": "https://www.etymonline.com/word/support",
      "words": [
        "support"
      ],
      "kind": "usage"
    }
  ],
  "nodes": [
    {
      "id": "phrase",
      "type": "text",
      "relation": "support-tech",
      "x": 120,
      "y": 210,
      "w": 760,
      "h": 180,
      "size": 99,
      "font": "en",
      "color": "root"
    },
    {
      "id": "meaning",
      "type": "text",
      "text": "技术支持",
      "x": 120,
      "y": 480,
      "w": 760,
      "h": 110,
      "size": 61
    },
    {
      "id": "function",
      "type": "text",
      "text": "维持正常运作",
      "x": 120,
      "y": 710,
      "w": 780,
      "h": 90,
      "size": 42,
      "color": "muted"
    },
    {
      "id": "page",
      "type": "image",
      "file": "media/apple-support.png",
      "credit": "Apple Support · 原页面截图",
      "x": 960,
      "y": 215,
      "w": 835,
      "h": 630,
      "crop": [
        0.03,
        0.23,
        0.94,
        0.68
      ],
      "relation": "support-tech"
    }
  ],
  "events": []
}
```

## 带回来的，是检查结果 [shot: report]
> 已知：设备检查和电池使用记录
> 推进：让 re 的回来承载可见的信息流，而不只放一条例句
> 来源：https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options
再让电脑检查电池的使用情况。
它可以生成一份 battery {report|report}，电池报告。
前面表示回来，后面表示带。
带到你面前的，这次是检查结果。
report，报告、报道。记者也是把见闻带回来的人。
从箱子、照片到消息，搬的东西越来越看不见了。

```scene
{
  "requires": [
    "carry",
    "support-tech"
  ],
  "learn": [
    {
      "id": "report",
      "label": "report",
      "detail": "把结果、消息带回来 → 报告、报道",
      "source": "lesson:report",
      "words": [
        "report"
      ],
      "kind": "etymology"
    }
  ],
  "nodes": [
    {
      "id": "word",
      "type": "text",
      "relation": "report",
      "x": 120,
      "y": 145,
      "w": 1680,
      "h": 175,
      "size": 128,
      "font": "en",
      "color": "root",
      "runs": [
        {
          "text": "re",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        }
      ]
    },
    {
      "id": "computer",
      "type": "shape",
      "shape": "rect",
      "x": 1150,
      "y": 420,
      "w": 525,
      "h": 345,
      "fill": "blue",
      "stroke": "ink",
      "strokeWidth": 4,
      "radius": 12
    },
    {
      "id": "check",
      "type": "text",
      "text": "检查电池",
      "x": 1190,
      "y": 435,
      "w": 440,
      "h": 90,
      "size": 43
    },
    {
      "id": "battery",
      "type": "shape",
      "shape": "rect",
      "x": 1310,
      "y": 575,
      "w": 210,
      "h": 98,
      "fill": "green",
      "stroke": "root",
      "strokeWidth": 5
    },
    {
      "id": "return",
      "type": "line",
      "x": 695,
      "y": 620,
      "w": 390,
      "h": 4,
      "stroke": "root",
      "arrow": true,
      "strokeWidth": 4,
      "points": [
        [
          390,
          2
        ],
        [
          0,
          2
        ]
      ]
    },
    {
      "id": "paper",
      "type": "shape",
      "shape": "rect",
      "x": 1150,
      "y": 445,
      "w": 525,
      "h": 335,
      "fill": "white",
      "stroke": "rule",
      "strokeWidth": 3,
      "opacity": 0
    },
    {
      "id": "heading",
      "type": "text",
      "text": "Battery report",
      "x": 1175,
      "y": 485,
      "w": 475,
      "h": 100,
      "size": 51,
      "font": "en",
      "color": "root",
      "opacity": 0
    },
    {
      "id": "results",
      "type": "text",
      "text": "使用记录\n检查结果",
      "x": 1175,
      "y": 620,
      "w": 475,
      "h": 125,
      "size": 41,
      "opacity": 0
    },
    {
      "id": "demo",
      "type": "text",
      "text": "报告示意",
      "x": 120,
      "y": 815,
      "w": 700,
      "h": 70,
      "size": 28,
      "color": "muted"
    },
    {
      "id": "morpheme",
      "type": "text",
      "text": "re-  回来",
      "x": 1030,
      "y": 175,
      "w": 765,
      "h": 105,
      "size": 43,
      "font": "en",
      "color": "prefix"
    }
  ],
  "events": [
    {
      "target": "paper",
      "at": "report",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "heading",
      "at": "report",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "results",
      "at": "report",
      "to": {
        "opacity": 1
      },
      "duration": 0.2
    },
    {
      "target": "paper",
      "at": "report",
      "to": {
        "x": 140
      },
      "duration": 2.2
    },
    {
      "target": "heading",
      "at": "report",
      "to": {
        "x": 165
      },
      "duration": 2.2
    },
    {
      "target": "results",
      "at": "report",
      "to": {
        "x": 165
      },
      "duration": 2.2
    }
  ]
}
```

## 文件很小，意义可以很重 [shot: important]
> 已知：一路传递过来的同一张照片
> 推进：把 important 接到有意义的历史支线，并分开记忆联想
> 来源：https://www.etymonline.com/word/important
再看刚才那张照片。
对别人可能普通，对主人却很重要。
an {important|important} photo，一张重要的照片。
同一个拉丁动词，到中世纪还有有分量、有意义的用法。
important 带着这层意思进入英语。
我们说在心里有分量，可以帮你{memory|记住}它。
这层联想，不等于实物的重量。

```scene
{
  "requires": [
    "carry",
    "import"
  ],
  "learn": [
    {
      "id": "important",
      "label": "important",
      "detail": "历史上的有分量、有意义 → 重要",
      "source": "lesson:important",
      "words": [
        "important"
      ],
      "kind": "etymology"
    },
    {
      "id": "weight-memory",
      "label": "有分量",
      "detail": "记忆联想；不等于实际重量",
      "source": "lesson:important",
      "words": [],
      "kind": "analogy"
    }
  ],
  "nodes": [
    {
      "id": "photo",
      "type": "image",
      "file": "media/important-photo.png",
      "credit": "©Hello · Adobe",
      "x": 130,
      "y": 190,
      "w": 520,
      "h": 650
    },
    {
      "id": "word",
      "type": "text",
      "relation": "important",
      "x": 785,
      "y": 185,
      "w": 1020,
      "h": 175,
      "size": 119,
      "font": "en",
      "color": "root",
      "opacity": 0,
      "runs": [
        {
          "text": "im",
          "color": "prefix"
        },
        {
          "text": "port",
          "color": "root"
        },
        {
          "text": "ant",
          "color": "suffix"
        }
      ]
    },
    {
      "id": "small",
      "type": "text",
      "text": "文件大小",
      "x": 795,
      "y": 430,
      "w": 1000,
      "h": 90,
      "size": 43,
      "color": "muted"
    },
    {
      "id": "meaning",
      "type": "text",
      "text": "对人的意义",
      "x": 795,
      "y": 540,
      "w": 1000,
      "h": 120,
      "size": 69
    },
    {
      "id": "memory",
      "type": "text",
      "relation": "weight-memory",
      "x": 800,
      "y": 745,
      "w": 670,
      "h": 105,
      "size": 68,
      "color": "root",
      "opacity": 0
    },
    {
      "id": "note",
      "type": "text",
      "text": "记忆联想",
      "x": 1480,
      "y": 775,
      "w": 330,
      "h": 75,
      "size": 29,
      "color": "muted",
      "opacity": 0
    }
  ],
  "events": [
    {
      "target": "word",
      "at": "important",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "memory",
      "at": "memory",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    },
    {
      "target": "note",
      "at": "memory",
      "to": {
        "opacity": 1
      },
      "duration": 0.5
    }
  ]
}
```

## 先把方向接回搬 [shot: close-directions]
> 已知：能带走、进出、跨越与软件参照
> 推进：收拢实际搬运动作和数字复制的边界
先把方向接回搬。
portable 能带走，import 往里，export 往外，transport 跨过去。
进和出要有参照，数字搬运还可以保留原件。

```scene
{
  "closing": true,
  "recall": [
    "carry",
    "portable",
    "import",
    "export",
    "reference",
    "transport"
  ],
  "nodes": [
    {
      "id": "summary",
      "type": "summary",
      "refs": [
        "carry",
        "portable",
        "import",
        "export",
        "reference",
        "transport"
      ],
      "heading": "方向与参照",
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

## 对象变了，关系还在 [shot: close-objects]
> 已知：生活、设备、结果与重要性的支线
> 推进：把 support 各用法及 report、important 完整带回
再看搬的对象和语境。
support 能托住木板，供养生活，也能维持设备运转。
report 带回消息，important 接到有分量、有意义。
词源是线索，联想帮助记忆，今天的用法还要分清。

```scene
{
  "closing": true,
  "recall": [
    "support-body",
    "support-family",
    "support-tech",
    "report",
    "important",
    "weight-memory"
  ],
  "nodes": [
    {
      "id": "summary",
      "type": "summary",
      "refs": [
        "support-body",
        "support-family",
        "support-tech",
        "report",
        "important",
        "weight-memory"
      ],
      "heading": "从可见的东西，到生活、信息与意义",
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

## 回到手里这条线 [shot: close-two-ports]
> 已知：开头同形的两个 port
> 推进：回答开场，保留动作与入口的直接词源区别
回到这条充电线。
portable charger 的名字，讲能带走。
USB-C port 这个接口，讲入口和通道。
下次见到 port，先认它在说什么，再沿关系往回找。

```scene
{
  "closing": true,
  "recall": [
    "port-contrast",
    "portable"
  ],
  "nodes": [
    {
      "id": "charger",
      "type": "image",
      "file": "media/charger.jpg",
      "credit": "Anker · 产品图",
      "x": 120,
      "y": 325,
      "w": 770,
      "h": 525
    },
    {
      "id": "socket",
      "type": "image",
      "file": "media/usb-c-port.jpg",
      "credit": "Kyu3 · CC BY-SA 4.0 · Wikimedia Commons",
      "x": 1010,
      "y": 390,
      "w": 790,
      "h": 380,
      "crop": [
        0,
        0.32,
        1,
        0.43
      ]
    },
    {
      "id": "portable",
      "type": "text",
      "relation": "portable",
      "x": 120,
      "y": 155,
      "w": 760,
      "h": 130,
      "size": 100,
      "font": "en",
      "color": "root"
    },
    {
      "id": "port",
      "type": "text",
      "text": "port",
      "x": 1020,
      "y": 155,
      "w": 740,
      "h": 130,
      "size": 100,
      "font": "en",
      "color": "prefix",
      "relation": "port-contrast"
    },
    {
      "id": "carry",
      "type": "text",
      "text": "能被携带",
      "x": 120,
      "y": 815,
      "w": 760,
      "h": 85,
      "size": 47
    },
    {
      "id": "gateway",
      "type": "text",
      "text": "设备出入口",
      "x": 1020,
      "y": 815,
      "w": 750,
      "h": 85,
      "size": 47
    }
  ],
  "events": []
}
```
