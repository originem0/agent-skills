/* 视频人物沿用课程的姿势与坐标，但用关节曲线绘制，并在同一 DOM 上动作。
   不替换整张 SVG，避免丢掉描边进度；所有姿态只由参数和时间决定。 */
const VIDEO_ACTORS = (() => {
  const limit = x => Math.max(0, Math.min(1, x));
  const smooth = x => { x = limit(x); return x * x * (3 - 2 * x); };
  const num = x => +x.toFixed(3);
  const mix = (a, b, t) => a.map((x, i) => x + (b[i] - x) * t);
  const levels = { "静止": 0, "轻": 0.45, "正常": 1, "明显": 1.3 };
  function hash(s) {
    let h = 2166136261;
    for (const c of String(s)) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
    return h >>> 0;
  }
  function bend(a, b, amount) {
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [(a[0] + b[0]) / 2 - (b[1] - a[1]) / d * amount,
            (a[1] + b[1]) / 2 + (b[0] - a[0]) / d * amount];
  }
  function base(o) {
    const p = JSON.parse(JSON.stringify({ ...BASE, ...POSES[o.pose || "stand"] }));
    p.a = p.a.map((a, i) => [a[0], a.length > 2 ? a[1] : bend(a[0], a[1], i ? -5 : 4), a[a.length - 1]]);
    p.l = p.l.map((a, i) => [a[0], a.length > 2 ? a[1] : bend(a[0], a[1], i ? -2 : 2), a[a.length - 1]]);
    return p;
  }
  function knee(a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], actual = Math.hypot(dx, dy) || .01;
    const d = Math.min(34.1, Math.max(.1, actual)), upper = 17, lower = 17.2;
    const along = (upper * upper - lower * lower + d * d) / (2 * d);
    const height = Math.sqrt(Math.max(0, upper * upper - along * along));
    return [a[0] + dx / actual * along + dy / actual * height,
            a[1] + dy / actual * along - dx / actual * height];
  }
  function walking(p, o, q, origin, s, dir) {
    const from = o.motion.from, distance = o.x - from[0];
    const cycles = Math.max(1, Math.min(8, Math.round(Math.abs(distance) / (52 * s))));
    const stride = distance / cycles, phase = smooth(q) * cycles;
    const oldFeet = base(o).l.map(l => l[2]);
    p.l.forEach((leg, i) => {
      const offset = i ? 0 : .5, n = Math.floor(phase + offset), f = phase + offset - n;
      const swing = f <= .55 ? 0 : (f - .55) / .45;
      let world = [from[0] + (n - offset + .28) * stride + stride * smooth(swing),
                   origin[1] - 6 * s * Math.sin(Math.PI * swing)];
      // 起步与停步接回原有脚姿；中段支撑脚的世界位置固定，身体经过它，不在地面滑行。
      if (q < .13) world = mix([from[0] + dir * oldFeet[i][0] * s, from[1] + oldFeet[i][1] * s], world, smooth(q / .13));
      if (q > .85) world = mix(world, [o.x + dir * oldFeet[i][0] * s, (o.y ?? 108) + oldFeet[i][1] * s], smooth((q - .85) / .15));
      leg[2] = [(world[0] - origin[0]) / (dir * s), (world[1] - origin[1]) / s];
      leg[1] = knee(leg[0], leg[2]);
    });
  }
  function frame(o, progress, strength = 1) {
    const p = base(o), q = limit(progress), pose = o.pose || "stand";
    // 灰色残影是原位，不参与动作；站立的背景人物不自动晃动。
    const amp = (o.op != null && o.op < 0.55) || (pose === "stand" && !o.motion) ? 0 : strength;
    const moving = o.motion && Array.isArray(o.motion.from) && amp > 0;
    const u = Math.sin(Math.PI * q) * amp, sway = (hash(o.seed || 0) % 101 / 100 - 0.5) * 0.4;
    let dx = 0, headAngle = 0;
    const torso = (x, y) => {
      p.h[0] += x; p.h[1] += y;
      p.t[0][0] += x * 0.8; p.t[0][1] += y;
      p.t[p.t.length - 1][0] += x * 0.25; p.t[p.t.length - 1][1] += y * 0.7;
      p.a.forEach(a => { a[0][0] += x * 0.8; a[0][1] += y; });
      p.l.forEach(a => { a[0][0] += x * 0.25; a[0][1] += y * 0.7; });
    };
    switch (pose) {
      case "pull":
        torso(-5.5 * u, 2.5 * u); headAngle = -5 * u;
        p.a.forEach((a, i) => { a[1][0] -= (4 + i) * u; a[1][1] += 2 * u; });
        p.l.forEach((a, i) => { a[1][0] += (i ? 4 : -3) * u; a[1][1] += 3 * u; });
        break;
      case "push":
        torso(5 * u, 2.5 * u); headAngle = 4 * u;
        p.a.forEach(a => { a[1][0] -= 4 * u; a[1][1] += 4 * u; });
        p.l.forEach((a, i) => { a[1][0] += (i ? 3 : -3) * u; });
        break;
      case "walk": {
        const gait = Math.sin(4 * Math.PI * q) * amp;
        torso(1.5 * u, -Math.abs(gait) * 1.5);
        dx = moving ? 0 : -8 * Math.pow(1 - q, 3) * amp;
        p.l.forEach((a, i) => {
          const step = i ? gait : -gait;
          a[1][0] += step * 4; a[1][1] -= Math.max(step, 0) * 6;
          a[2][0] += step * 3; a[2][1] -= Math.max(step, 0) * 4;
        });
        p.a.forEach((a, i) => { a[1][0] += (i ? -gait : gait) * 3; a[2][0] += (i ? -gait : gait) * 4; });
        headAngle = gait * 2;
        break;
      }
      case "carry":
        torso(moving ? .5 * u : 1.5 * u, moving ? -Math.abs(Math.sin(4 * Math.PI * q)) * .8 : 4 * u); headAngle = -3 * u;
        p.a.forEach((a, i) => { a[1][0] += (i ? 3 : -3) * u; });
        p.l.forEach((a, i) => { a[1][0] += (i ? 4 : -4) * u; });
        break;
      case "give": case "explain":
        torso(1.8 * u, 0); p.a[1][1][1] -= 5 * u; p.a[1][2][0] += 3 * u;
        headAngle = -4 * u; break;
      case "withdraw":
        torso(-1.5 * u, 0); p.a[1][1][0] -= 4 * u; p.a[1][2][0] -= 3 * u;
        headAngle = 4 * u; break;
      case "point":
        p.a[1][1][1] -= 3 * u; p.a[1][2][1] -= 4 * u; headAngle = -7 * u; break;
      case "think":
        torso(-2 * u, u); p.a[1][1][0] -= 4 * u;
        p.a[1][2] = [p.h[0] + 8, p.h[1] + 1]; headAngle = 6 * u; break;
      case "stern":
        p.a.forEach((a, i) => { a[1][0] += (i ? 2 : -2) * u; }); headAngle = 2 * u; break;
      case "lean":
        torso(-4 * u, u); headAngle = -5 * u; break;
      case "sit":
        torso(-u, 0); p.a[1][1][1] -= 2 * u; headAngle = 3 * u; break;
    }
    // 握持由实际手部决定。两手拉绳时共用接触点；镜像、缩放和行走位移同样作用到绳头。
    if (o.rope) {
      p.a[1][2] = [...p.hand];
      if (pose === "pull") p.a[0][2] = [...p.hand];
    } else p.hand = [...p.a[1][2]];
    const s = o.s || 1, dir = o.flip ? -1 : 1, gy = o.y ?? 108;
    const origin = moving ? mix(o.motion.from, [o.x, gy], smooth(q)) : [o.x + dir * dx * s, gy];
    if (moving && pose !== "sit") walking(p, o, q, origin, s, dir);
    const hand = [origin[0] + dir * p.hand[0] * s, origin[1] + p.hand[1] * s];
    return { ...p, origin, handWorld: hand, headAngle: headAngle + sway, s, dir };
  }
  function limb(a) {
    const before = mix(a[1], a[0], 0.12), after = mix(a[1], a[2], 0.12);
    return `M${a[0].map(num)} L${before.map(num)} Q${a[1].map(num)} ${after.map(num)} L${a[2].map(num)}`;
  }
  function geometry(o, p) {
    const neck = [p.h[0], p.h[1] + 8.4], shoulder = p.t[0], hip = p.t[p.t.length - 1];
    return {
      body: `M${neck.map(num)} Q${[shoulder[0] + 1, shoulder[1]].map(num)} ${shoulder.map(num)} Q${[hip[0] - 1.5, (shoulder[1] + hip[1]) / 2].map(num)} ${hip.map(num)}`,
      arms: p.a.map(limb), legs: p.l.map(limb),
      palms: p.a.map(a => `M${[a[2][0] - 1.4, a[2][1] + 0.3].map(num)} q1.8,1.2 3.5,-0.3`),
      feet: p.l.map(a => `M${[a[2][0] - 1.8, a[2][1]].map(num)} q2.7,1.3 5.8,0.4`),
      head: `translate(${p.h.map(num)}) rotate(${num(p.headAngle)})`,
      transform: `translate(${p.origin.map(num)}) scale(${p.dir * p.s},${p.s})`
    };
  }
  function render(o) {
    const p = frame(o, 0, 0), g = geometry(o, p), cfg = esc(JSON.stringify(o));
    const face = o.pose === "think" || o.pose === "stern" ? "M1,-3 Q3,-4 5,-2" : "M1,-3 Q3,-3.5 5,-2.5";
    const path = (part, d, sw = 2.35) => `<path data-part="${part}" d="${d}" stroke-width="${sw}"/>`;
    return `<g data-actor="${cfg}" opacity="${o.op ?? 1}">
      ${o.rope ? `<line data-rope="1" x1="${p.handWorld[0]}" y1="${p.handWorld[1]}" x2="${o.rope[0]}" y2="${o.rope[1]}" stroke="${ROPE}" stroke-width="1.8" stroke-linecap="round"/>` : ""}
      <g data-body="1" transform="${g.transform}" fill="none" stroke="${o.c || INK}" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="0" cy="1" rx="18" ry="1.1" fill="${GREY}" stroke="none" opacity=".16"/>
        ${path("body", g.body, 2.6)}
        ${g.legs.map((d, i) => path("leg" + i, d)).join("")}${g.arms.map((d, i) => path("arm" + i, d)).join("")}
        ${g.feet.map((d, i) => path("foot" + i, d, 2.5)).join("")}${g.palms.map((d, i) => path("palm" + i, d, 1.7)).join("")}
        <g data-head="1" transform="${g.head}"><circle cx="0" cy="0" r="8.4" fill="#f7f9fa" stroke-width="1.9"/>
          <path d="${face}" stroke-width=".9"/><circle cx="3.7" cy="-.3" r=".65" fill="${INK}" stroke="none"/>
          <path d="M2,3.8 Q4,4.6 5.2,3.4" stroke-width=".8"/></g>
      </g></g>`;
  }
  function paint(group, q, level) {
    const o = group.__actor || (group.__actor = JSON.parse(group.dataset.actor));
    const p = frame(o, q, levels[level] ?? 1), g = geometry(o, p);
    let changed = false;
    const set = (el, key, value) => {
      if (!el) return;
      value = String(value);
      if (el.getAttribute(key) !== value) { el.setAttribute(key, value); changed = true; }
    };
    set(group.querySelector("[data-body]"), "transform", g.transform);
    set(group.querySelector("[data-head]"), "transform", g.head);
    set(group.querySelector('[data-part="body"]'), "d", g.body);
    for (const [name, list] of [["arm", g.arms], ["leg", g.legs], ["foot", g.feet], ["palm", g.palms]])
      list.forEach((d, i) => set(group.querySelector(`[data-part="${name}${i}"]`), "d", d));
    const rope = group.querySelector("[data-rope]");
    set(rope, "x1", num(p.handWorld[0])); set(rope, "y1", num(p.handWorld[1]));
    set(group, "data-hand", p.handWorld.map(num).join(","));
    return { changed, delta: [p.origin[0] - o.x, p.origin[1] - (o.y ?? 108)] };
  }
  const duration = o => o.motion?.duration || 2.4 + (hash(o.seed || 0) % 9) / 20;
  function update(cam, t) {
    const start = +cam.dataset.actAt, level = cam.dataset.actLevel || "正常";
    let changed = false;
    const roles = new Map();
    cam.querySelectorAll("[data-actor]").forEach(group => {
      const o = group.__actor || (group.__actor = JSON.parse(group.dataset.actor));
      const result = paint(group, limit((t - start) / duration(o)), level);
      changed = result.changed || changed;
      if (o.id) roles.set(o.id, result.delta);
    });
    cam.querySelectorAll("[data-follow]").forEach(el => {
      const delta = roles.get(el.dataset.follow) || [0, 0], value = `translate(${delta.map(num)})`;
      if (el.getAttribute("transform") !== value) { el.setAttribute("transform", value); changed = true; }
    });
    return changed;
  }
  // 只在视频页面替换人物；HTML 继续使用共享 kit.js 的静态线稿。
  K.fig = render;
  return { frame, update, hash, duration };
})();
