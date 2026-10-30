/* 线稿零件库：网页版（assets/lesson_template.html，由 scripts/build.py 内联）和 word-family-video 的视频画面（它的 assets/story_frame.html，由它的 scripts/video.py 内联）共用。 */
/* ===================== 线稿零件库 =====================
   坐标系：viewBox 280×122，地面 y=108。新增零件后无需改 build.py（它会自动读取这里的名字）。 */
const INK = "#1e242b", PRE = "#b84a14", ROOT = "#176b4d", BLUE = "#2b5c8f", GREY = "#9aa0a8",
  FILL = "#efe9de", ROPE = "#8a6a4a", PINK = "#f1ddd6";
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pl = pts => pts.map(p => p.join(",")).join(" ");
// 粗估文字宽度（CJK 记 1em，其余 0.58em），用于气泡和标签自适应
function textW(s, fs) { return [...String(s)].reduce((w, ch) => w + (/[　-鿿＀-￯]/.test(ch) ? fs : fs * .58), 0); }

// 姿势：双脚中点为原点、面朝右；h 头心，t 躯干，a 两臂，l 两腿（折线允许肘、膝）；hand 为绳子/物件的手部挂点
const BASE = { h: [0, -64], t: [[0, -54], [0, -28]], a: [[[0, -48], [-10, -34]], [[0, -48], [10, -34]]],
  l: [[[0, -28], [-9, 0]], [[0, -28], [9, 0]]], hand: [10, -34] };
const POSES = {
  stand: {},
  walk: { h: [3, -64], t: [[2, -54], [0, -28]], a: [[[1, -48], [-9, -37]], [[1, -48], [12, -38]]],
    l: [[[0, -28], [-11, 0]], [[0, -28], [5, -14], [12, 0]]], hand: [12, -38] },
  pull: { h: [-11, -60], t: [[-9, -51], [0, -28]], a: [[[-7, -46], [8, -46], [20, -45]], [[-7, -43], [7, -41], [20, -43]]],
    l: [[[0, -28], [-13, 0]], [[0, -28], [10, -13], [15, 0]]], hand: [20, -44] },
  push: { h: [10, -58], t: [[7, -49], [-4, -28]], a: [[[6, -45], [30, -46]], [[5, -41], [30, -38]]],
    l: [[[-4, -28], [-18, 0]], [[-4, -28], [6, 0]]], hand: [30, -42] },
  give: { a: [[[0, -48], [-10, -34]], [[0, -48], [26, -44]]], hand: [26, -44] },
  point: { a: [[[0, -48], [-10, -34]], [[0, -48], [24, -58]]], hand: [24, -58] },
  explain: { a: [[[0, -48], [-10, -34]], [[0, -48], [14, -46], [22, -56]]], hand: [22, -56] },
  withdraw: { a: [[[0, -48], [-10, -34]], [[0, -48], [12, -40], [5, -46]]], hand: [5, -46] },
  think: { a: [[[0, -48], [-10, -34]], [[0, -48], [12, -54], [8, -63]]], hand: [8, -63] },
  stern: { a: [[[0, -48], [-12, -40], [-3, -31]], [[0, -48], [12, -40], [3, -31]]] },
  carry: { a: [[[0, -48], [-12, -64], [-12, -78]], [[0, -48], [12, -64], [12, -78]]], hand: [12, -78] },
  lean: { h: [-14, -59], t: [[-11, -50], [0, -28]], a: [[[-9, -46], [-22, -38]], [[-9, -46], [6, -54]]], hand: [6, -54] },
  sit: { h: [0, -50], t: [[0, -40], [0, -16]], a: [[[0, -34], [12, -24]], [[0, -34], [-8, -22]]],
    l: [[[0, -16], [16, -16], [16, 0]], [[0, -16], [12, -14], [12, 0]]], hand: [12, -24] }
};

const K = {
  fig(o) {
    const P = { ...BASE, ...POSES[o.pose || "stand"] }, s = o.s || 1, gy = o.y ?? 108, dir = o.flip ? -1 : 1;
    let rope = "";
    if (o.rope) {
      const hx = o.x + dir * P.hand[0] * s, hy = gy + P.hand[1] * s;
      rope = `<line x1="${hx}" y1="${hy}" x2="${o.rope[0]}" y2="${o.rope[1]}" stroke="${ROPE}" stroke-width="1.8" stroke-linecap="round"/>`;
    }
    return `${rope}<g transform="translate(${o.x},${gy}) scale(${dir * s},${s})" opacity="${o.op ?? 1}" fill="none" stroke="${o.c || INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="${P.h[0]}" cy="${P.h[1]}" r="9.5" fill="#fff"/><polyline points="${pl(P.t)}"/>
      ${[...P.a, ...P.l].map(x => `<polyline points="${pl(x)}"/>`).join("")}</g>`;
  },
  arrow(o) {
    const c = o.c || PRE, d = o.d ? o.d : o.curve && o.pts.length === 3
      ? `M${o.pts[0]} Q${o.pts[1]} ${o.pts[2]}` : `M${o.pts.map(p => p.join(",")).join(" L")}`;
    return `<path d="${d}" fill="none" stroke="${c}" stroke-width="1.8" ${o.dash ? 'stroke-dasharray="4 3"' : ""} marker-end="url(#ah-${c.slice(1)})" opacity="${o.op ?? 1}"/>`;
  },
  line: o => `<line x1="${o.x1}" y1="${o.y1}" x2="${o.x2}" y2="${o.y2}" stroke="${o.c || "#d6d0c4"}" stroke-width="${o.w || 1.4}" ${o.dash ? 'stroke-dasharray="4 4"' : ""}/>`,
  text: o => `<text x="${o.x}" y="${o.y}" text-anchor="${o.anchor || "middle"}" font-size="${o.size || 11}" font-weight="${o.weight || (o.serif ? 700 : 400)}"
    ${o.serif ? 'font-family="Georgia, serif"' : ""} fill="${o.c || INK}" opacity="${o.op ?? 1}"
    ${o.rot ? `transform="rotate(${o.rot} ${o.x} ${o.y})"` : ""}>${esc(o.text)}</text>`,
  tag(o) {
    const tone = { pre: ["#fdf0e6", PRE], root: ["#e7f3ee", ROOT], muted: ["#eef0f2", "#5e6670"] }[o.tone] || ["#e8eff7", BLUE];
    const w = textW(o.text, 11) + 18;
    return `<g opacity="${o.op ?? 1}"><rect x="${o.x - w / 2}" y="${o.y - 11}" width="${w}" height="20" rx="6" fill="${tone[0]}" stroke="${tone[1]}" stroke-width="1"/>
      <text x="${o.x}" y="${o.y + 3}" text-anchor="middle" font-size="11" font-weight="700" fill="${tone[1]}">${esc(o.text)}</text></g>`;
  },
  bubble(o) {
    const w = textW(o.text, 10.5) + 18;
    const tail = o.tail ? `<path d="M${o.x - 6},${o.y + 9} L${o.tail[0]},${o.tail[1]} L${o.x + 4},${o.y + 9}" fill="#fff" stroke="${INK}" stroke-width="1.3" stroke-linejoin="round"/>` : "";
    return `${tail}<rect x="${o.x - w / 2}" y="${o.y - 10}" width="${w}" height="20" rx="9" fill="#fff" stroke="${INK}" stroke-width="1.3"/>
      <text x="${o.x}" y="${o.y + 4}" text-anchor="middle" font-size="10.5" fill="${INK}">${esc(o.text)}</text>`;
  },
  thought(o) {
    const [fx, fy] = o.from, mx = (fx + o.x) / 2, my = (fy + o.y) / 2;
    return `<circle cx="${fx + (mx - fx) * .4}" cy="${fy + (my - fy) * .4}" r="2" fill="#fff" stroke="${INK}" stroke-width="1.2"/>
      <circle cx="${mx + (o.x - mx) * .3}" cy="${my + (o.y - my) * .3}" r="3.5" fill="#fff" stroke="${INK}" stroke-width="1.2"/>
      <ellipse cx="${o.x}" cy="${o.y}" rx="${Math.max(20, textW(o.text, 12) / 2 + 12)}" ry="13" fill="#fff" stroke="${INK}" stroke-width="1.3"/>
      <text x="${o.x}" y="${o.y + 4}" text-anchor="middle" font-size="12" font-weight="700" fill="${PRE}">${esc(o.text)}</text>`;
  },
  // ---- 基础图形：零件库里没有合适道具时直接拼 ----
  rect: o => `<rect x="${o.x}" y="${o.y}" width="${o.w}" height="${o.h}" rx="${o.r || 0}" fill="${o.fill || FILL}" stroke="${o.c || "#5e6670"}" stroke-width="${o.sw || 1.6}" opacity="${o.op ?? 1}"/>`,
  circle: o => `<circle cx="${o.x}" cy="${o.y}" r="${o.r}" fill="${o.fill || FILL}" stroke="${o.c || "#5e6670"}" stroke-width="${o.sw || 1.6}" opacity="${o.op ?? 1}"/>`,
  path: o => `<path d="${o.d}" fill="${o.fill || "none"}" stroke="${o.c || INK}" stroke-width="${o.sw || 1.6}" stroke-linejoin="round" stroke-linecap="round" opacity="${o.op ?? 1}"/>`,
  // ---- 道具 ----
  spot: o => `<ellipse cx="${o.x}" cy="108" rx="26" ry="5" fill="#e7f3ee" stroke="${ROOT}" stroke-width="1.4"/>
    <text x="${o.x}" y="120" text-anchor="middle" font-size="9" fill="${ROOT}">${esc(o.label || "")}</text>`,
  stairs: o => `<polyline points="${pl(o.pts)}" fill="none" stroke="${GREY}" stroke-width="2"/>`,
  bar: o => `<rect x="${o.x}" y="${o.y}" width="${o.w}" height="${o.h}" rx="4" fill="#e7f3ee" stroke="${ROOT}" stroke-width="1.4"/>
    <rect x="${o.x + 3}" y="${o.y + 3}" width="${(o.w - 6) * (o.fillPct ?? 1)}" height="${o.h - 6}" rx="2" fill="${ROOT}" opacity=".55"/>`,
  table: o => `<g stroke="${GREY}" stroke-width="2" stroke-linecap="round"><line x1="${o.x - o.w / 2}" y1="${o.top}" x2="${o.x + o.w / 2}" y2="${o.top}"/>
    <line x1="${o.x - o.w / 2 + 6}" y1="${o.top}" x2="${o.x - o.w / 2 + 6}" y2="108"/><line x1="${o.x + o.w / 2 - 6}" y1="${o.top}" x2="${o.x + o.w / 2 - 6}" y2="108"/></g>`,
  glass: o => `<g stroke="${INK}" stroke-width="1.6" stroke-linejoin="round">
    <path d="M${o.x - 9},${o.y - 34} L${o.x + 9},${o.y - 34} Q${o.x + 8},${o.y - 20} ${o.x},${o.y - 19} Q${o.x - 8},${o.y - 20} ${o.x - 9},${o.y - 34} Z" fill="${PINK}"/>
    <line x1="${o.x}" y1="${o.y - 19}" x2="${o.x}" y2="${o.y - 2}"/><line x1="${o.x - 7}" y1="${o.y - 1}" x2="${o.x + 7}" y2="${o.y - 1}"/></g>`,
  door: o => `<rect x="${o.x - 17}" y="40" width="34" height="68" fill="${FILL}" stroke="#5e6670" stroke-width="2"/>
    <circle cx="${o.x + 10}" cy="76" r="2" fill="#5e6670"/>`,
  no: o => `<circle cx="${o.x}" cy="${o.y}" r="${o.r || 22}" fill="none" stroke="${PRE}" stroke-width="2.6"/>
    <line x1="${o.x - (o.r || 22) * .7}" y1="${o.y - (o.r || 22) * .7}" x2="${o.x + (o.r || 22) * .7}" y2="${o.y + (o.r || 22) * .7}" stroke="${PRE}" stroke-width="2.6"/>`,
  envelope: o => `<g stroke="#5e6670" stroke-width="1.6" stroke-linejoin="round"><rect x="${o.x - 13}" y="${o.y - 9}" width="26" height="18" fill="${FILL}"/>
    <polyline points="${o.x - 13},${o.y - 9} ${o.x},${o.y + 1} ${o.x + 13},${o.y - 9}" fill="none"/></g>`,
  // 纸片按标签加宽：粗体大写比 textW 估的宽约 1.25 倍（RECEIPT 曾溢出固定 36 宽的框）
  paper: o => { const w = Math.max(36, textW(o.label || "", 10) * 1.25 + 10); return `<g transform="rotate(${o.rot || 0} ${o.x} ${o.y})" opacity="${o.op ?? 1}"><rect x="${o.x - w / 2}" y="${o.y - 14}" width="${w}" height="28" fill="#fff" stroke="#5e6670" stroke-width="1.6"/>
    <text x="${o.x}" y="${o.y + 4}" text-anchor="middle" font-size="10" font-weight="700" fill="${PRE}">${esc(o.label || "")}</text></g>`; },
  crate: o => `<g stroke="#5e6670" stroke-width="1.8"><rect x="${o.x - 20}" y="78" width="40" height="30" fill="${FILL}"/>
    <line x1="${o.x - 20}" y1="78" x2="${o.x + 20}" y2="108"/><line x1="${o.x + 20}" y1="78" x2="${o.x - 20}" y2="108"/></g>`,
  rock: o => `<circle cx="${o.x}" cy="${o.y ?? 108 - (o.r || 30)}" r="${o.r || 30}" fill="#d9d2c5" stroke="#5e6670" stroke-width="2"/>`,
  heart: o => `<path transform="translate(${o.x},${o.y - 12})" d="M0,6 C0,-3 -14,-3 -14,7 C-14,15 -2,21 0,25 C2,21 14,15 14,7 C14,-3 0,-3 0,6 Z"
    fill="${PINK}" stroke="${INK}" stroke-width="1.6" stroke-linejoin="round"/>`,
  carrot: o => `<g stroke="${INK}" stroke-width="1.6" stroke-linejoin="round"><path d="M${o.x - 9},86 L${o.x + 9},86 L${o.x + 1},118 Z" fill="#f3d9c6"/>
    <g stroke="${ROOT}" fill="none" stroke-linecap="round"><path d="M${o.x},86 q-10,-8 -12,-16"/><path d="M${o.x},86 q0,-10 -2,-20"/><path d="M${o.x},86 q9,-7 10,-15"/></g></g>`,
  blocks(o) {
    let out = "";
    for (let r = 0; r < 3; r++) for (let c = 0; c < 2; c++) {
      const moved = r === 0 && c === 1, dx = moved ? o.pulled || 0 : 0;
      out += `<rect x="${o.x - 26 + c * 26 + dx}" y="${96 - r * 12}" width="26" height="12" fill="${moved && o.pulled ? "#f3d9c6" : FILL}" stroke="#5e6670" stroke-width="1.5"/>`;
    }
    return out;
  },
  bag: o => `<g stroke="${INK}" stroke-width="1.6" stroke-linejoin="round">
    <path d="M${o.x - 6},62 C${o.x - 34},70 ${o.x - 34},108 ${o.x},108 C${o.x + 34},108 ${o.x + 34},70 ${o.x + 6},62 Z" fill="${FILL}"/>
    <g stroke="${ROPE}" fill="none" stroke-linecap="round"><path d="M${o.x - 6},62 Q${o.x - 22},52 ${o.x - 36},40"/><path d="M${o.x + 6},62 Q${o.x + 22},52 ${o.x + 36},40"/></g></g>
    <path d="M${o.x - 26},70 L${o.x - 12},66" stroke="${PRE}" stroke-width="1.6" marker-end="url(#ah-${PRE.slice(1)})"/>
    <path d="M${o.x + 26},70 L${o.x + 12},66" stroke="${PRE}" stroke-width="1.6" marker-end="url(#ah-${PRE.slice(1)})"/>`,
  river: o => [70, 80, 90, 100].map(y => `<path d="M${o.x},${y} q${o.w / 4},-5 ${o.w / 2},0 t${o.w / 2},0" fill="none" stroke="${BLUE}" stroke-width="1.6" opacity=".7"/>`).join(""),
  channel: o => `<line x1="${o.x1}" y1="${o.y - 6}" x2="${o.x2}" y2="${o.y - 6}" stroke="${GREY}" stroke-width="1.6"/>
    <line x1="${o.x1}" y1="${o.y + 6}" x2="${o.x2}" y2="${o.y + 6}" stroke="${GREY}" stroke-width="1.6"/>
    <line x1="${o.x1}" y1="${o.y}" x2="${o.x2}" y2="${o.y}" stroke="${BLUE}" stroke-width="1.4" stroke-dasharray="6 5" opacity=".7"/>`,
  sprout: o => `<g stroke="${ROOT}" stroke-width="1.6" fill="none" stroke-linecap="round"><line x1="${o.x}" y1="108" x2="${o.x}" y2="86"/>
    <path d="M${o.x},96 q-9,-2 -10,-10 q8,1 10,10"/><path d="M${o.x},90 q9,-2 10,-10 q-8,1 -10,10"/></g>`,
  apple: o => `<g stroke="${INK}" stroke-width="1.6"><path d="M${o.x},80 c-14,-8 -22,6 -15,18 c4,8 10,10 15,7 c5,3 11,1 15,-7 c7,-12 -1,-26 -15,-18 z" fill="${PINK}"/>
    <path d="M${o.x},80 q1,-7 5,-10" fill="none"/></g>`,
  // 天平：x 为立柱位置；tilt > 0 时右盘下沉；left/right 可在盘子下方写标签
  balance(o) {
    const t = o.tilt || 0, ly = 50 - t, ry = 50 + t, pan = (px, py) =>
      `<line x1="${px}" y1="${py}" x2="${px}" y2="${py + 26}"/><path d="M${px - 16},${py + 26} Q${px},${py + 40} ${px + 16},${py + 26} Z" fill="${FILL}"/>`;
    const lab = (px, py, s) => s ? `<text x="${px}" y="${py - 8}" text-anchor="middle" font-size="10" font-weight="700" fill="${PRE}" stroke="none">${esc(s)}</text>` : "";
    return `<g stroke="${INK}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round">
      <line x1="${o.x}" y1="108" x2="${o.x}" y2="50"/><line x1="${o.x - 22}" y1="108" x2="${o.x + 22}" y2="108"/>
      <line x1="${o.x - 56}" y1="${ly}" x2="${o.x + 56}" y2="${ry}"/><circle cx="${o.x}" cy="50" r="3" fill="#fff"/>
      ${pan(o.x - 56, ly)}${pan(o.x + 56, ry)}${lab(o.x - 56, ly, o.left)}${lab(o.x + 56, ry, o.right)}</g>`;
  },
  flag: o => `<g stroke="${INK}" stroke-width="1.6"><line x1="${o.x - 10}" y1="108" x2="${o.x - 10}" y2="30"/>
    <path d="M${o.x - 10},32 L${o.x + 18},42 L${o.x - 10},52 Z" fill="${PINK}"/></g>`,
  tractor: o => `<g stroke="${INK}" stroke-width="1.8" stroke-linejoin="round">
    <rect x="${o.x - 128}" y="70" width="58" height="26" fill="${FILL}"/><circle cx="${o.x - 99}" cy="99" r="9" fill="#fff"/>
    <line x1="${o.x - 70}" y1="88" x2="${o.x - 30}" y2="88" stroke="${ROPE}"/>
    <rect x="${o.x - 30}" y="72" width="62" height="20" fill="${FILL}"/><path d="M${o.x - 26},72 L${o.x - 26},42 L${o.x + 2},42 L${o.x + 2},72" fill="none"/>
    <line x1="${o.x + 22}" y1="72" x2="${o.x + 22}" y2="56"/><circle cx="${o.x - 14}" cy="92" r="16" fill="#fff"/><circle cx="${o.x - 14}" cy="92" r="5" fill="none"/>
    <circle cx="${o.x + 24}" cy="99" r="9" fill="#fff"/></g>`,
  train(o) {
    let cars = "";
    for (let i = 0; i < 3; i++) {
      const x = o.x + i * 46;
      cars += `<rect x="${x}" y="66" width="40" height="30" fill="${FILL}"/><circle cx="${x + 10}" cy="100" r="6" fill="#fff"/><circle cx="${x + 30}" cy="100" r="6" fill="#fff"/>
        <line x1="${x + 40}" y1="88" x2="${x + 46}" y2="88" stroke="${ROPE}"/>`;
    }
    const L = o.x + 138;
    return `<g stroke="${INK}" stroke-width="1.8" stroke-linejoin="round">${cars}
      <path d="M${L},96 L${L},56 L${L + 22},56 L${L + 22},70 L${L + 52},70 L${L + 58},96 Z" fill="#fff"/>
      <line x1="${L + 42}" y1="70" x2="${L + 42}" y2="56"/><circle cx="${L + 12}" cy="100" r="7" fill="#fff"/><circle cx="${L + 40}" cy="100" r="7" fill="#fff"/></g>`;
  }
};

// scene 可以是零件数组，也可以是 { items: [...], ground: false }
// 这些零件自己处理 op；其余零件统一包一层 <g opacity> 支持透明度。
// 每个零件外包 <g data-k data-i>，供 build.py 的自动版面检查定位（重叠、出界）。
const OWN_OP = new Set(["fig", "arrow", "text", "tag", "paper", "rect", "circle", "path"]);
function scene(sc, caption) {
  const items = Array.isArray(sc) ? sc : sc.items, ground = Array.isArray(sc) || sc.ground !== false;
  const marks = [PRE, GREY, BLUE, ROOT].map(c => `<marker id="ah-${c.slice(1)}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="${c}" stroke-width="1.6"/></marker>`).join("");
  const body = items.map((o, i) => {
    if (!K[o.k]) return `<text x="140" y="60" text-anchor="middle" fill="#c0392b">未知零件 ${esc(o.k)}</text>`;
    const out = K[o.k](o);
    const op = o.op != null && !OWN_OP.has(o.k) ? ` opacity="${o.op}"` : "";
    return `<g data-k="${o.k}" data-i="${i}"${op}>${out}</g>`;
  }).join("");
  return `<figure class="stage"><svg viewBox="0 0 280 122" xmlns="http://www.w3.org/2000/svg"><defs>${marks}</defs>
    ${ground ? `<line x1="16" y1="108" x2="264" y2="108" stroke="#d6d0c4" stroke-width="2" stroke-linecap="round"/>` : ""}
    ${body}</svg>${caption ? `<figcaption>${esc(caption)}</figcaption>` : ""}</figure>`;
}

/* ---------- 词素标签与单词着色（网页版、视频版共用） ----------
   parts 每项可以是数组 [形式, 中文义, 类型?] 或对象 {m, cn, kind?, of?}。
   类型：以 - 结尾是前缀 p，以 - 开头是后缀 s，其余是词根 r。of = 这是谁的变体/同化形式（如 "ad-"）。 */
function normPart(pt) {
  const o = Array.isArray(pt) ? { m: pt[0], cn: pt[1], kind: pt[2] } : { ...pt };
  o.kind = o.kind || (o.m.endsWith("-") ? "p" : o.m.startsWith("-") ? "s" : "r");
  return o;
}
const chips = parts => `<div class="morph">${parts.map(normPart).map(p =>
  `<span class="chip ${p.kind}"><b>${esc(p.m)}</b><small>${esc(p.cn)}${p.of ? `<em class="of">${esc(p.of)} 的${p.how || (p.kind === "p" ? "同化形式" : "变体")}</em>` : ""}</small></span>`
).join('<span class="plus">+</span>')}</div>`;
const colorWord = ([p = "", r = "", s = ""]) => `<span class="p">${esc(p)}</span><span class="r">${esc(r)}</span><span class="s">${esc(s)}</span>`;
// 变体一行：「il-（l 前）illegal · im-（b/m/p 前）impossible」
const variantLine = v => (v || []).map(x => `${x.m}${x.note ? `（${x.note}）` : ""}${x.ex ? " " + x.ex : ""}`).join(" · ");

// 家族图：词根居中，派生词按椭圆均匀排布，日常词放四角——收成「一个面」。
// 左右两侧的标签向外对齐（文字往外长），连线停在文字内侧，避免连线压字。有变体时写在中心椭圆里。
function familyMap(L) {
  const W = 680, H = 356, cx = 340, cy = 174, n = L.words.length;
  const vs = (L.root.variants || []).map(v => v.m).join(" · ");
  // 变体行在椭圆下部（低于中心约 28）：椭圆在那个高度的半宽要容得下整行，所以按字宽反推 rx
  const ry = vs ? 50 : 36, rx = vs ? Math.max(78, (textW(vs, 12) / 2 + 6) / Math.sqrt(1 - (28 / ry) ** 2)) : 62;
  const rootFs = Math.min(24, 150 / Math.max(L.root.m.length, 1));
  const nodes = L.words.map((w, i) => {
    const a = (-90 + i * 360 / n) * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    const side = Math.abs(c) < 0.3 ? 0 : Math.sign(c);           // 0 = 上下居中；±1 = 右/左两侧
    const x = cx + 175 * c, y = cy + 122 * s;
    const anchor = side === 0 ? "middle" : side > 0 ? "start" : "end";
    const [ex, ey] = side ? [x - 10 * side, y - 6] : s < 0 ? [x, y + 28] : [x, y - 22];
    const [p = "", r = "", sf = ""] = w.split;
    return `<g data-node="${i}"><line x1="${cx + (rx + 2) * c}" y1="${cy + (ry + 2) * s}" x2="${ex}" y2="${ey}" stroke="#d6d0c4" stroke-width="1.6"/>
      <text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Georgia, serif" font-size="19" font-weight="700"><tspan fill="${PRE}">${esc(p)}</tspan><tspan fill="${ROOT}">${esc(r)}</tspan><tspan fill="#5e6670">${esc(sf)}</tspan></text>
      <text x="${x}" y="${y + 18}" text-anchor="${anchor}" font-size="11.5" fill="#6b717a">${esc(w.literal)}</text></g>`;
  }).join("");
  const corners = [[18, 24, "start"], [W - 18, 24, "end"], [18, H - 12, "start"], [W - 18, H - 12, "end"]];
  const daily = (L.daily || []).slice(0, 4).map((d, i) => `<text x="${corners[i][0]}" y="${corners[i][1]}" text-anchor="${corners[i][2]}" font-size="12" fill="#8a9099">${esc(d)}</text>`).join("");
  const dy = vs ? -8 : 0;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#e7f3ee" stroke="${ROOT}" stroke-width="1.4"/>
    <text x="${cx}" y="${cy - 2 + dy}" text-anchor="middle" font-family="Georgia, serif" font-size="${rootFs}" font-weight="700" fill="${ROOT}">${esc(L.root.m)}</text>
    <text x="${cx}" y="${cy + 16 + dy}" text-anchor="middle" font-size="12" fill="${ROOT}">${esc(L.root.cn)}</text>
    ${vs ? `<text x="${cx}" y="${cy + 32}" text-anchor="middle" font-family="Georgia, serif" font-size="12" font-weight="700" fill="${PRE}">${esc(vs)}</text>` : ""}
    ${nodes}${daily}</svg>`;
}
