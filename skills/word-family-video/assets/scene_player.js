/* 只执行编译好的元素和轨道。选词、释义、构图与总结的决策均在编译前完成。 */
(() => {
  const clamp = x => Math.max(0, Math.min(1, x));
  const ease = (x, mode) => mode === "hold" ? +(x >= 1) : mode === "linear" ? clamp(x) : (x=clamp(x), x*x*(3-2*x));
  const el = (tag, className, parent) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (parent) parent.appendChild(node);
    return node;
  };
  const film = document.getElementById("film"), sections = [], caches = [];
  const ns = (svg, prefix) => svg.replace(/\bid="([^"]+)"/g, (_, id) => `id="${prefix}-${id}"`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${prefix}-${id})`)
    .replace(/href="#([^"]+)"/g, (_, id) => `href="#${prefix}-${id}"`);

  function mount(n, parent, shotId, entries) {
    const node = el("div", "node " + n.type, parent);
    node.dataset.nodeId = n.id;
    node.id = shotId + "--" + n.id;
    const entry = {el:node, n, previous:"", children:[]};
    entries.push(entry);
    if (n.type === "group") {
      for (const child of n.children) mount(child, node, node.id, entry.children);
    } else if (n.type === "text") {
      node.style.fontFamily = n.font === "en" ? "var(--en)" : "var(--zh)";
      node.style.fontSize = (n.size || 52) + "px";
      node.style.fontWeight = n.weight || (n.font === "en" ? 500 : 400);
      node.style.color = n.color || "var(--ink)";
      node.style.textAlign = n.align || "left";
      node.style.justifyContent = n.align === "center" ? "center" : n.align === "right" ? "flex-end" : "flex-start";
      const ink = el("span", "ink", node);
      if (n.runs) for (const run of n.runs) {
        const span = el("span", "", ink);
        span.textContent = run.text;
        if (run.color) span.style.color = run.color;
      } else ink.textContent = n.text || "";
    } else if (n.type === "image") {
      node.classList.add("photo");
      const img = el("img", "", node);
      img.src = DATA.assets[n.asset];
      img.alt = "";
      img.style.objectFit = n.fit || "contain";
      if (n.crop) {
        const cropWindow = el("div", "crop-window", node);
        cropWindow.style.cssText = "position:absolute;overflow:hidden";
        cropWindow.appendChild(img);
        // 裁切选的是原图的一部分，不能把接口、人物或文字拉伸到镜头宽高比。
        entry.crop = values => {
          if (!img.naturalWidth) return;
          const [x,y,w,h] = n.crop, cw=img.naturalWidth*w, ch=img.naturalHeight*h;
          const scale = (n.fit === "cover" ? Math.max : Math.min)(values.w/cw,values.h/ch);
          cropWindow.style.left = (values.w-cw*scale)/2+"px";
          cropWindow.style.top = (values.h-ch*scale)/2+"px";
          cropWindow.style.width = cw*scale+"px";
          cropWindow.style.height = ch*scale+"px";
          img.style.cssText = `position:absolute;width:${img.naturalWidth*scale}px;height:${img.naturalHeight*scale}px;left:${-x*img.naturalWidth*scale}px;top:${-y*img.naturalHeight*scale}px`;
        };
        img.addEventListener("load", () => entry.crop(entry.values || n));
      }
    } else if (n.type === "illustration") {
      const cam = el("div", "cam", node);
      cam.dataset.actAt = n.actionAt;
      cam.dataset.actLevel = n.actLevel;
      const items = Array.isArray(n.items) ? n.items : n.items.items;
      const seeded = items.map((item,i) => item.k === "fig" ? {...item, seed:VIDEO_ACTORS.hash(shotId+":"+n.id+":"+(item.id||i))} : item);
      cam.innerHTML = ns(scene(Array.isArray(n.items) ? seeded : {...n.items, items:seeded}, ""), node.id);
      cam.querySelectorAll("g[data-i]").forEach(g => {
        const item = seeded[+g.dataset.i];
        if (item.follow) g.dataset.follow = item.follow;
      });
      entry.cam = cam;
    } else if (n.type === "shape" || n.type === "line") {
      let inside = "", defs = "";
      const stroke = n.stroke || "#cbd5d5", sw = n.strokeWidth ?? 3;
      if (n.type === "line") {
        if (n.arrow) defs = `<defs><marker id="${node.id}-arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L11 6 L1 11" fill="none" stroke="${esc(stroke)}" stroke-width="1.5"/></marker></defs>`;
        const points = (n.points || [[0,n.h/2],[n.w,n.h/2]]).map(p=>p.join(",")).join(" ");
        inside = `<polyline points="${esc(points)}" fill="none" stroke="${esc(stroke)}" stroke-width="${sw}" ${n.dash?'stroke-dasharray="10 9"':''} ${n.arrow?`marker-end="url(#${node.id}-arrow)"`:''}/>`;
      } else {
        const fill = n.fill || "none", attrs = `fill="${esc(fill)}" stroke="${n.stroke?esc(stroke):'none'}" stroke-width="${sw}"`;
        if (n.shape === "ellipse") inside = `<ellipse cx="${n.w/2}" cy="${n.h/2}" rx="${n.w/2-sw}" ry="${n.h/2-sw}" ${attrs}/>`;
        else if (n.shape === "path") inside = `<path d="${esc(n.d || '')}" ${attrs} stroke-linecap="round" stroke-linejoin="round"/>`;
        else inside = `<rect x="${sw/2}" y="${sw/2}" width="${Math.max(0,n.w-sw)}" height="${Math.max(0,n.h-sw)}" rx="${n.radius||0}" ${attrs}/>`;
      }
      node.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n.w} ${n.h}">${defs}${inside}</svg>`;
    }
    return entry;
  }
  DATA.shots.forEach(s => {
    const sec = el("section", "shot", film), entries = [];
    sec.dataset.shot = s.id;
    for (const n of s.nodes) mount(n, sec, s.id, entries);
    sections.push(sec);
    caches.push(entries);
  });
  document.getElementById("family").textContent = DATA.root;
  let active = -1, lastSubtitle = null, lastCredits = null;
  let lastNavigation = "";
  function paintNavigation(navigation) {
    const host = document.getElementById("words"), data = navigation || {words:[],active:[]};
    host.hidden = !data.words.length;
    const width = host.clientWidth, key = JSON.stringify([data,width]);
    if (key === lastNavigation) return;
    lastNavigation = key;
    host.replaceChildren();
    if (!data.words.length) return;
    const current = new Set(data.active), labels = data.words.map(word => {
      const span = el("span", "word" + (current.has(word) ? " now" : ""), host);
      span.textContent = word;
      span.dataset.word = word;
      if (current.has(word)) span.setAttribute("aria-current", "true");
      return span;
    });
    // 按实际排版宽度取窗口。这里只决定怎样摆放，词语归属和当前词已经由编译器给定。
    const widths = labels.map(span => span.offsetWidth), last = labels.length-1;
    const focused = data.words.map((word,i) => current.has(word) ? i : -1).filter(i => i >= 0);
    let lo = focused[0] ?? last, hi = focused.at(-1) ?? last;
    const used = (a,b) => widths.slice(a,b+1).reduce((sum,w) => sum+w,0) + 20*(b-a) + (a>0?40:0) + (b<last?40:0);
    if (used(lo,hi)>width) lo=hi;
    while (true) {
      const left=lo>0 && used(lo-1,hi)<=width, right=hi<last && used(lo,hi+1)<=width;
      if (!left && !right) break;
      if (left) lo--;
      if (right && used(lo,hi+1)<=width) hi++;
    }
    const more = () => {const span=el("span","more");span.textContent="…";span.setAttribute("aria-hidden","true");return span;};
    host.replaceChildren(...(lo>0?[more()]:[]),...labels.slice(lo,hi+1),...(hi<last?[more()]:[]));
  }
  document.fonts.ready.then(() => {
    if (active>=0) {lastNavigation="";paintNavigation(DATA.shots[active].navigation);}
  });
  function paint(entry, state, t) {
    const n = entry.n, values = {x:n.x,y:n.y,w:n.w,h:n.h,opacity:n.opacity??1,scale:n.scale??1,rotation:n.rotation??0,...state};
    const key = JSON.stringify(values);
    let changed = key !== entry.previous;
    if (changed) {
      const style = entry.el.style;
      for (const [prop,field] of [["left","x"],["top","y"],["width","w"],["height","h"]]) style[prop] = values[field]+"px";
      style.opacity = values.opacity;
      style.transform = `scale(${values.scale}) rotate(${values.rotation}deg)`;
      entry.previous = key;
    }
    entry.values = values;
    if (entry.crop && changed) entry.crop(values);
    for (const child of entry.children) changed = paint(child, {}, t) || changed;
    if (entry.cam) changed = VIDEO_ACTORS.update(entry.cam, t) || changed;
    return changed;
  }
  function setT(t) {
    t = Math.max(0, Math.min(DATA.total, t));
    let index = DATA.shots.findIndex(s => t < s.t1);
    if (index < 0) index = DATA.shots.length - 1;
    let changed = active !== index;
    if (changed) {
      if (active >= 0) sections[active].classList.remove("on");
      sections[index].classList.add("on");
      document.getElementById("chapter").textContent = DATA.shots[index].title;
      document.getElementById("family").textContent = DATA.shots[index].family;
      paintNavigation(DATA.shots[index].navigation);
      active = index;
    }
    const shot = DATA.shots[index], states = {};
    // 每次从初始状态计算。拖动进度条和顺序编码具有相同结果，不依赖上一帧。
    for (const tr of shot.tracks) {
      if (t < tr.at) continue;
      const q = tr.end === tr.at ? 1 : ease((t-tr.at)/(tr.end-tr.at), tr.ease);
      (states[tr.target] ||= {})[tr.prop] = +(tr.start+(tr.to-tr.start)*q).toFixed(5);
    }
    for (const entry of caches[index]) changed = paint(entry, states[entry.n.id]||{}, t) || changed;
    const sub = DATA.subs.find(s => t >= s.s && t < s.e)?.t || "";
    if (sub !== lastSubtitle) { document.getElementById("sub").textContent = sub; lastSubtitle = sub; changed = true; }
    const credits = [...new Set(caches[index].filter(e => e.n.credit && +(states[e.n.id]?.opacity ?? e.n.opacity ?? 1) > .01)
      .map(e=>e.n.credit.replace(/\s*[（(]https?:\/\/.*$/, "")))].join(" · ");
    if (credits !== lastCredits) { document.getElementById("credits").textContent = credits; lastCredits = credits; changed = true; }
    return changed;
  }
  function audit() {
    const issues = [], sec = sections[active];
    if (!sec) return ["没有当前镜头"];
    const visible = e => {
      for (let n=e; n && n!==sec; n=n.parentElement) if (+getComputedStyle(n).opacity < .01) return false;
      return true;
    };
    const textRects = [];
    for (const node of sec.querySelectorAll(".node")) {
      if (!visible(node)) continue;
      const r = node.getBoundingClientRect(), id = node.dataset.nodeId;
      if (r.left < -1 || r.top < 105 || r.right > 1921 || r.bottom > 933)
        issues.push(`${id} 超出内容区域 (${Math.round(r.left)},${Math.round(r.top)},${Math.round(r.right)},${Math.round(r.bottom)})`);
      const ink = node.classList.contains("text") && node.querySelector(":scope > .ink");
      if (ink) {
        const ir = ink.getBoundingClientRect();
        if (ir.width > r.width+2 || ir.height > r.height+2 || ink.scrollWidth > r.width+2) issues.push(`${id} 文字超出留给它的位置`);
        textRects.push({id,r:ir});
      }
      const img = node.classList.contains("image") && node.querySelector("img");
      if (img && (!img.complete || img.naturalWidth===0)) issues.push(`${id} 图片未加载`);
    }
    for (let i=0; i<textRects.length; i++) for (let j=i+1; j<textRects.length; j++) {
      const a=textRects[i], b=textRects[j];
      if (Math.min(a.r.right,b.r.right)-Math.max(a.r.left,b.r.left)>3 &&
          Math.min(a.r.bottom,b.r.bottom)-Math.max(a.r.top,b.r.top)>3)
        issues.push(`${a.id} 与 ${b.id} 文字重叠`);
    }
    for (const ink of sec.querySelectorAll(".illustration svg text")) {
      if (!visible(ink)) continue;
      const r=ink.getBoundingClientRect();
      if (r.width && (r.left < 0 || r.right > 1920 || r.top < 105 || r.bottom > 933))
        issues.push("线稿文字超出内容区域");
    }
    for (const line of sec.querySelectorAll("[marker-end]")) {
      const id = line.getAttribute("marker-end").match(/#([^)]*)/)?.[1];
      if (!document.getElementById(id)) issues.push("箭头标记缺失");
    }
    for (const id of ["family","words","chapter","credits","sub"]) {
      const e=document.getElementById(id);
      if (e.scrollWidth>e.clientWidth+2 || e.scrollHeight>e.clientHeight+2) issues.push(`${id} 文字溢出`);
    }
    return [...new Set(issues)];
  }
  window.setT = setT;
  window.audit = audit;
  window.filmData = DATA;
})();
