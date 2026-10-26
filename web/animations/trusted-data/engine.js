/*
 * Trusted Data for Enterprise Agents — animation engine
 * -----------------------------------------------------
 * TrustedData.mount(container, config, lang) builds a 1920×1080 SVG stage and
 * a single paused GSAP timeline from the config (see config.js).
 *
 * Same scrub-safe rules as the MCP explainer engine:
 *  - Every element is created at build time; the timeline only animates.
 *  - Persistent state changes go through `to()` (explicit fromTo).
 *  - Ephemeral effects go through `fx()`, hidden outside 0 < v < 1.
 *
 * Returns { timeline, duration, scenes: [{id,label,time}], seek(t) }.
 */
(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const W = 1920, H = 1080;

  function mk(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  const easeInOut = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
  const easeOut = (x) => 1 - Math.pow(1 - x, 3);
  const clamp01 = (x) => Math.max(0, Math.min(1, x));

  function mount(container, cfg, lang) {
    const th = cfg.theme;
    const L = cfg.strings[lang] || cfg.strings.en;
    const k = 1 / (cfg.speed || 1);
    const S = (v) => v * k;
    const LV = { C3: th.c3, C2: th.c2, C1: th.c1 };

    // ── SVG scaffold ────────────────────────────────────────────────────────
    const svg = mk("svg", {
      viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet",
      class: "td-stage", role: "img", "aria-label": L.title,
    });
    container.appendChild(svg);
    svg.style.fontFamily = th.font;
    const defs = mk("defs", {}, svg);

    const bgGrad = mk("radialGradient", { id: "td-bg", cx: "50%", cy: "45%", r: "75%" }, defs);
    mk("stop", { offset: "0%", "stop-color": th.bgGlow }, bgGrad);
    mk("stop", { offset: "100%", "stop-color": th.bg }, bgGrad);
    const vig = mk("radialGradient", { id: "td-vig", cx: "50%", cy: "50%", r: "70%" }, defs);
    mk("stop", { offset: "60%", "stop-color": "#000", "stop-opacity": 0 }, vig);
    mk("stop", { offset: "100%", "stop-color": "#000", "stop-opacity": 0.55 }, vig);
    const dots = mk("pattern", { id: "td-dots", width: 36, height: 36, patternUnits: "userSpaceOnUse" }, defs);
    mk("circle", { cx: 18, cy: 18, r: 1.1, fill: "#ffffff", "fill-opacity": 0.07 }, dots);
    const cardFill = mk("linearGradient", { id: "td-card", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    mk("stop", { offset: "0%", "stop-color": "#111723" }, cardFill);
    mk("stop", { offset: "100%", "stop-color": "#0A0E15" }, cardFill);

    const halos = {};
    function halo(color) {
      if (halos[color]) return halos[color];
      const id = "td-halo-" + Object.keys(halos).length;
      const g = mk("radialGradient", { id }, defs);
      mk("stop", { offset: "0%", "stop-color": color, "stop-opacity": 0.32 }, g);
      mk("stop", { offset: "45%", "stop-color": color, "stop-opacity": 0.1 }, g);
      mk("stop", { offset: "100%", "stop-color": color, "stop-opacity": 0 }, g);
      return (halos[color] = `url(#${id})`);
    }

    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#td-bg)" }, svg);
    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#td-dots)" }, svg);
    const worlds = mk("g", {}, svg);
    const screenG = mk("g", {}, svg);
    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#td-vig)", "pointer-events": "none" }, svg);
    const measureG = mk("g", { visibility: "hidden" }, svg);

    // ── Text helpers ────────────────────────────────────────────────────────
    function txt(parent, s, x, y, o = {}) {
      const t = mk("text", {
        x, y,
        "font-family": o.mono ? th.mono : th.font,
        "font-size": o.size || 16,
        "font-weight": o.weight || 500,
        fill: o.fill || th.text,
        "text-anchor": o.anchor || "middle",
        "letter-spacing": o.ls || null,
        "dominant-baseline": "central",
        opacity: o.opacity,
        "font-style": o.italic ? "italic" : null,
      }, parent);
      t.textContent = s;
      return t;
    }
    function measure(s, o = {}) {
      const t = txt(measureG, s, 0, 0, o);
      const w = t.getComputedTextLength();
      measureG.removeChild(t);
      return w;
    }
    function wrap(s, maxW, o) {
      const lines = [];
      let line = "";
      for (const w of s.split(" ")) {
        const tryLine = line ? line + " " + w : w;
        if (line && measure(tryLine, o) > maxW) { lines.push(line); line = w; }
        else line = tryLine;
      }
      if (line) lines.push(line);
      return lines;
    }

    // ── Timeline + state helpers ────────────────────────────────────────────
    const tl = gsap.timeline({ paused: true });
    const state = new Map();
    const DEF = { opacity: 1, x: 0, y: 0, scale: 1, scaleX: 1, scaleY: 1, rotation: 0 };

    function init(el, props) {
      gsap.set(el, props);
      const s = state.get(el) || {};
      for (const key in props) if (typeof props[key] === "number") s[key] = props[key];
      state.set(el, s);
    }
    function to(el, props, at, dur = 0.6, ease = "power2.inOut") {
      const s = state.get(el) || {};
      const from = {};
      for (const key in props) from[key] = key in s ? s[key] : DEF[key];
      tl.fromTo(el, from, { ...props, duration: Math.max(dur, 0.001), ease, immediateRender: false }, at);
      state.set(el, { ...s, ...props });
    }
    const show = (el, at, dur = 0.6, ease = "power3.out") => to(el, { opacity: 1, x: 0, y: 0, scale: 1 }, at, S(dur), ease);
    const hide = (el, at, dur = 0.5) => to(el, { opacity: 0 }, at, S(dur), "power2.in");
    const hidden = (el, extra = {}) => init(el, { opacity: 0, transformOrigin: "50% 50%", ...extra });

    function fx(at, dur, render, ease = "none") {
      const p = { v: 0 };
      render(0);
      tl.fromTo(p, { v: 0 }, {
        v: 1, duration: Math.max(dur, 0.001), ease, immediateRender: false,
        onUpdate: () => render(p.v),
      }, at);
    }
    function win(at, fadeIn, hold, fadeOut, apply) {
      const total = fadeIn + hold + fadeOut;
      fx(at, total, (v) => {
        if (v <= 0 || v >= 1) return apply(0, v);
        const t = v * total;
        const a = t < fadeIn ? t / fadeIn : t > fadeIn + hold ? (total - t) / fadeOut : 1;
        apply(easeOut(clamp01(a)), v);
      });
    }
    function drawIn(path, at, dur, ease = "power2.inOut") {
      const len = path.getTotalLength();
      path.setAttribute("stroke-dasharray", `${len} ${len + 2}`);
      path.setAttribute("stroke-dashoffset", len);
      tl.fromTo(path, { attr: { "stroke-dashoffset": len } }, {
        attr: { "stroke-dashoffset": 0 }, duration: dur, ease, immediateRender: false,
      }, at);
    }

    // ── Visual primitives ───────────────────────────────────────────────────
    function glyph(parent, type, x, y, color, sc = 1) {
      const g = mk("g", { transform: `translate(${x} ${y}) scale(${sc})`, fill: "none", stroke: color, "stroke-width": 1.6, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
      if (type === "hex") {
        const pts = [];
        for (let i = 0; i < 6; i++) { const a = ((60 * i - 30) * Math.PI) / 180; pts.push(`${9 * Math.cos(a)},${9 * Math.sin(a)}`); }
        mk("polygon", { points: pts.join(" ") }, g);
        mk("circle", { r: 2.4, fill: color, stroke: "none" }, g);
      } else if (type === "stack") {
        [-6, 0, 6].forEach((dy) => mk("rect", { x: -9, y: dy - 2, width: 18, height: 4, rx: 2 }, g));
      } else if (type === "plug") {
        mk("rect", { x: -7, y: -3, width: 14, height: 10, rx: 3 }, g);
        mk("path", { d: "M-3,-3 V-9 M3,-3 V-9 M0,7 V11" }, g);
      } else if (type === "spark") {
        mk("path", { d: "M0,-11 C1.2,-3 3,-1.2 11,0 C3,1.2 1.2,3 0,11 C-1.2,3 -3,1.2 -11,0 C-3,-1.2 -1.2,-3 0,-11 Z", fill: color, "fill-opacity": 0.9, stroke: "none" }, g);
      } else if (type === "key") {
        mk("circle", { cx: -4, cy: -4, r: 5 }, g);
        mk("path", { d: "M-0.5,-0.5 L9,9 M4.5,4.5 L7,2 M7,7 L9.5,4.5" }, g);
      } else if (type === "shield") {
        mk("path", { d: "M0,-10 L8,-6.5 V0 C8,6 4,9 0,11 C-4,9 -8,6 -8,0 V-6.5 Z" }, g);
        mk("path", { d: "M-3.5,0.5 L-1,3 L4,-2.5" }, g);
      } else if (type === "doc") {
        mk("rect", { x: -7, y: -10, width: 14, height: 20, rx: 2 }, g);
        mk("path", { d: "M-3.5,-4 H3.5 M-3.5,0 H3.5 M-3.5,4 H1" }, g);
      } else if (type === "check") {
        mk("circle", { r: 9.5 }, g);
        mk("path", { d: "M-4.5,0 L-1.5,3.5 L5,-3.5" }, g);
      } else if (type === "lock") {
        mk("rect", { x: -8, y: -2, width: 16, height: 12, rx: 2.5 }, g);
        mk("path", { d: "M-5,-2 V-6 C-5,-12 5,-12 5,-6 V-2" }, g);
      } else if (type === "chip") {
        mk("rect", { x: -8, y: -8, width: 16, height: 16, rx: 2.5 }, g);
        mk("rect", { x: -3.5, y: -3.5, width: 7, height: 7, rx: 1 }, g);
        mk("path", { d: "M-4,-8 V-11 M0,-8 V-11 M4,-8 V-11 M-4,8 V11 M0,8 V11 M4,8 V11 M-8,-4 H-11 M-8,0 H-11 M-8,4 H-11 M8,-4 H11 M8,0 H11 M8,4 H11" }, g);
      } else if (type === "cloud") {
        mk("path", { d: "M-9,6 C-14,6 -14,-2 -8,-2 C-8,-9 2,-11 4,-4 C10,-6 13,2 8,6 Z" }, g);
      } else if (type === "route") {
        mk("path", { d: "M-11,0 H-2 M-2,0 L8,-8 M-2,0 L8,0 M-2,0 L8,8 M5,-10 L8,-8 L6,-5 M5,0 H8 M6,5 L8,8 L5,10" }, g);
      } else if (type === "mask") {
        mk("path", { d: "M-11,-4 C-6,-7 6,-7 11,-4 C11,4 6,7 0,7 C-6,7 -11,4 -11,-4 Z" }, g);
        mk("path", { d: "M-6,-1 H-2 M2,-1 H6" }, g);
      } else if (type === "user") {
        mk("circle", { cx: 0, cy: -4, r: 5 }, g);
        mk("path", { d: "M-9,10 C-9,2 9,2 9,10" }, g);
      } else {
        mk("circle", { r: 4, fill: color, stroke: "none" }, g);
      }
      return g;
    }

    // Card: outer (static position) > g (animated) > glow + base + content
    function card(parent, o) {
      const { x, y, w, h } = o;
      const r = o.r != null ? o.r : 14;
      const color = o.color || th.request;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("rect", { x: -w / 2 - 70, y: -h / 2 - 70, width: w + 140, height: h + 140, rx: r + 60, fill: halo(color) }, glow);
      mk("rect", { x: -w / 2 - 4, y: -h / 2 - 4, width: w + 8, height: h + 8, rx: r + 4, fill: "none", stroke: color, "stroke-opacity": 0.18, "stroke-width": 8 }, glow);
      const base = mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "url(#td-card)", stroke: o.stroke || th.line, "stroke-width": 1.2 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "none", stroke: color, "stroke-width": 1.4 }, glow);
      const content = mk("g", {}, g);
      init(glow, { opacity: 0 });
      const node = { outer, g, glow, base, content, x, y, w, h, r, color,
        L: { x: x - w / 2, y }, R: { x: x + w / 2, y }, T: { x, y: y - h / 2 }, B: { x, y: y + h / 2 } };
      if (o.label) {
        const size = o.size || 15;
        if (o.align === "left") {
          const lx = -w / 2 + 22;
          if (o.glyph) glyph(content, o.glyph, lx + 9, 0, color);
          const tx = lx + (o.glyph ? 32 : 0);
          node.label = txt(content, o.label, tx, o.sub ? -11 : 0, { size, weight: 600, ls: "0.12em", anchor: "start" });
          if (o.sub) node.sub = txt(content, o.sub, tx, 13, { size: 12, mono: true, fill: th.muted, anchor: "start" });
        } else {
          const lw = measure(o.label, { size, weight: 600, ls: "0.14em" });
          const gw = o.glyph ? 32 : 0;
          const start = -(lw + gw) / 2;
          if (o.glyph) glyph(content, o.glyph, start + 10, o.sub ? -11 : 0, color);
          node.label = txt(content, o.label, start + gw, o.sub ? -11 : 0, { size, weight: 600, ls: "0.14em", anchor: "start" });
          if (o.sub) node.sub = txt(content, o.sub, 0, 14, { size: 12, mono: true, fill: th.muted });
        }
      }
      return node;
    }
    const lit = (n, at, a = 1, dur = 0.4) => to(n.glow, { opacity: a }, at, S(dur));

    // Rounded pill with text. anchor: "middle" (default) or "start"
    function pill(parent, s, x, y, color, o = {}) {
      const size = o.size || 13;
      const tw = measure(s, { size, mono: !o.sans, weight: o.weight || 500 });
      const pad = o.pad || 14;
      const w = tw + pad * 2 + (o.glyph ? 26 : 0);
      const h = o.h || 30;
      const cx = o.anchor === "start" ? x + w / 2 : x;
      const outer = mk("g", { transform: `translate(${cx} ${y})` }, parent);
      const g = mk("g", {}, outer);
      if (o.halo) mk("rect", { x: -w / 2 - 10, y: -h / 2 - 9, width: w + 20, height: h + 18, rx: h, fill: halo(color) }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: h / 2, fill: o.fill || "#0C111A", stroke: color, "stroke-opacity": o.strokeOpacity || 0.9, "stroke-width": 1.2 }, g);
      if (o.glyph) glyph(g, o.glyph, -w / 2 + pad + 8, 0, color, 0.8);
      const t = txt(g, s, -w / 2 + pad + (o.glyph ? 26 : 0), 0, { size, mono: !o.sans, fill: o.textFill || color, weight: o.weight || 500, anchor: "start" });
      return { outer, g, t, w, h, x: cx, y, L: { x: cx - w / 2, y }, R: { x: cx + w / 2, y } };
    }

    // Glowing comet travelling along a path
    function comet(parent, d, color, at, dur, o = {}) {
      const g = mk("g", { opacity: 0 }, parent);
      const sc = o.scale || 1;
      const paths = [[16, 0.06], [7, 0.2], [2.4, 1]].map(([w, a]) =>
        mk("path", { d, fill: "none", stroke: color, "stroke-width": w * sc, "stroke-opacity": a, "stroke-linecap": "round" }, g));
      const head = mk("g", {}, g);
      mk("circle", { r: 20 * sc, fill: color, opacity: 0.1 }, head);
      mk("circle", { r: 8 * sc, fill: color, opacity: 0.4 }, head);
      mk("circle", { r: 3.4 * sc, fill: "#fff" }, head);
      const len = paths[0].getTotalLength();
      const tail = Math.min(o.tail || 170, len * 0.7);
      paths.forEach((p) => p.setAttribute("stroke-dasharray", `${tail} ${len + 3 * tail}`));
      const rev = !!o.reverse;
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { g.setAttribute("opacity", 0); return; }
        g.setAttribute("opacity", 1);
        const s = v * (len + tail);
        const off = rev ? s - len : tail - s;
        paths.forEach((p) => p.setAttribute("stroke-dashoffset", off));
        const hs = Math.min(s, len);
        const pt = paths[0].getPointAtLength(rev ? len - hs : hs);
        head.setAttribute("transform", `translate(${pt.x} ${pt.y})`);
        head.setAttribute("opacity", s <= len ? 1 : 0);
      }, o.ease || "power1.inOut");
    }

    // Data chip carried along a path (start → end)
    function dataChip(parent, label, color) {
      const g = mk("g", { opacity: 0 }, parent);
      const w = measure(label, { size: 13, mono: true }) + 30;
      mk("rect", { x: -w / 2 - 10, y: -24, width: w + 20, height: 48, rx: 22, fill: halo(color) }, g);
      mk("rect", { x: -w / 2, y: -15, width: w, height: 30, rx: 9, fill: "#0E1119", stroke: color, "stroke-width": 1.2 }, g);
      txt(g, label, 0, 0, { size: 13, mono: true, fill: color, weight: 500 });
      return g;
    }
    function carry(chip, d, at, dur) {
      const p = mk("path", { d }, measureG);
      const len = p.getTotalLength();
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { chip.setAttribute("opacity", 0); return; }
        const pt = p.getPointAtLength(easeInOut(v) * len);
        const sc = v < 0.12 ? easeOut(v / 0.12) : v > 0.88 ? Math.max(0.05, (1 - v) / 0.12) : 1;
        chip.setAttribute("opacity", v > 0.88 ? (1 - v) / 0.12 : 1);
        chip.setAttribute("transform", `translate(${pt.x} ${pt.y}) scale(${sc})`);
      });
    }

    function pulse(parent, n, color, at, dur = 0.9) {
      const g = mk("g", { transform: `translate(${n.x} ${n.y})`, opacity: 0 }, parent);
      const inner = mk("g", {}, g);
      if (n.circle) mk("circle", { r: n.circle, fill: "none", stroke: color, "stroke-width": 2 }, inner);
      else mk("rect", { x: -n.w / 2, y: -n.h / 2, width: n.w, height: n.h, rx: n.r || 14, fill: "none", stroke: color, "stroke-width": 2 }, inner);
      fx(at, S(dur), (v) => {
        if (v <= 0 || v >= 1) { g.setAttribute("opacity", 0); return; }
        const e = easeOut(v);
        g.setAttribute("opacity", 0.85 * (1 - v));
        const sx = n.circle ? 1 + e * 0.6 : 1 + (e * 36) / n.w;
        const sy = n.circle ? 1 + e * 0.6 : 1 + (e * 36) / n.h;
        inner.setAttribute("transform", `scale(${sx} ${sy})`);
      });
    }

    const curve = (a, b, bend = 0.5) => {
      const dx = (b.x - a.x) * bend;
      return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
    };
    const rail = (parent, d, color, o = {}) => mk("path", { d, stroke: color, "stroke-opacity": o.opacity || 0.35, "stroke-width": 1.4, fill: "none", "stroke-dasharray": o.dash || null }, parent);

    // Person avatar
    function person(parent, x, y, label, sub, color) {
      const outer = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("circle", { r: 110, fill: halo(color) }, glow);
      mk("circle", { r: 44, fill: "url(#td-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("circle", { r: 44, fill: "none", stroke: color, "stroke-width": 1.4 }, glow);
      init(glow, { opacity: 0 });
      const icon = mk("g", { fill: "none", stroke: th.text, "stroke-width": 1.8, "stroke-linecap": "round" }, g);
      mk("circle", { cx: 0, cy: -9, r: 9 }, icon);
      mk("path", { d: "M-17,19 C-17,5 17,5 17,19" }, icon);
      txt(g, label, 0, 74, { size: 14, weight: 600, ls: "0.2em" });
      txt(g, sub, 0, 98, { size: 12, mono: true, fill: th.muted });
      return { outer, g, glow, x, y, w: 88, h: 88, circle: 44, color, R: { x: x + 48, y }, T: { x, y: y - 48 } };
    }

    // Screen-space caption
    const capLayer = mk("g", {}, screenG);
    function caption(lines, at, hold, o = {}) {
      lines = Array.isArray(lines) ? lines : [lines];
      const size = o.size || 30;
      const lh = size * 1.3;
      const y0 = (o.y || 978) - ((lines.length - 1) * lh) / 2 - (o.sub ? 18 : 0);
      const g = mk("g", { opacity: 0 }, capLayer);
      lines.forEach((l, i) => txt(g, l, W / 2, y0 + i * lh, { size, weight: o.weight || 500, fill: o.fill || th.text, ls: "-0.005em" }));
      if (o.sub) txt(g, o.sub, W / 2, y0 + (lines.length - 1) * lh + size * 0.6 + 24, { size: 17, mono: true, fill: o.subFill || th.muted });
      const fi = S(0.7), fo = S(0.6);
      win(at, fi, hold, fo, (a) => {
        g.setAttribute("opacity", a);
        g.setAttribute("transform", `translate(0 ${(1 - a) * 12})`);
      });
      return at + fi + hold + fo;
    }

    // Eyebrow (scene label, top-left) + chapter marks
    const SCENE_IDS = ["request", "stack", "quality", "context", "access", "privacy", "routing", "result", "final"];
    const eyebrowG = mk("g", {}, screenG);
    const sceneMarks = [];
    function eyebrow(id, at, until) {
      const index = SCENE_IDS.indexOf(id);
      const label = L.scenes[id];
      sceneMarks.push({ id, label, time: at });
      tl.addLabel(id, at);
      const g = mk("g", { opacity: 0 }, eyebrowG);
      mk("line", { x1: 72, y1: 72, x2: 96, y2: 72, stroke: th.mcp, "stroke-width": 2 }, g);
      txt(g, String(index + 1).padStart(2, "0"), 110, 72, { size: 13, mono: true, anchor: "start" });
      txt(g, label.toUpperCase(), 142, 72, { size: 13, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
      win(at + S(0.2), S(0.6), Math.max(0, until - at - S(1.4)), S(0.6), (a) => g.setAttribute("opacity", a));
    }

    // A world = a full-stage group faded in/out per scene
    function world() {
      const root = mk("g", {}, worlds);
      init(root, { opacity: 0 });
      const layers = { rails: mk("g", {}, root), nodes: mk("g", {}, root), fx: mk("g", {}, root), top: mk("g", {}, root) };
      return { root, ...layers };
    }

    let t = 0;

    // ═════════════════════════════════════════════════════════════════════════
    //  WORLD M — Sales → Agent → MCP servers → Data sources (scenes 1–3)
    // ═════════════════════════════════════════════════════════════════════════
    const M = world();
    const arch = mk("g", {}, M.nodes);
    init(arch, { opacity: 1 });
    const user = person(arch, 170, 540, L.user.label, L.user.sub, th.request);
    hidden(user.g, { scale: 0.9 });
    const agent = card(arch, { x: 620, y: 540, w: 300, h: 96, r: 24, label: L.agent, glyph: "spark", color: th.request, size: 18 });
    hidden(agent.g, { scale: 0.92 });
    const railUA = rail(M.rails, `M ${user.R.x + 4} 540 L ${agent.L.x - 4} 540`, th.request);
    init(railUA, { opacity: 0 });

    const SRV_X = 1140, SRC_X = 1650, ROW_Y = [330, 540, 750];
    const colTitle = (s, x) => { const e = txt(arch, s, x, 232, { size: 13, mono: true, fill: th.muted, ls: "0.28em" }); hidden(e, { y: 8 }); return e; };
    const srvTitle = colTitle(L.mcpTitle, SRV_X);
    const srcTitle = colTitle(L.dataTitle, SRC_X);
    const servers = L.servers.map((s, i) => {
      const n = card(arch, { x: SRV_X, y: ROW_Y[i], w: 330, h: 88, label: s.label, sub: s.sub, glyph: "plug", color: th.mcp, align: "left" });
      hidden(n.g, { scale: 0.92 });
      n.rail = rail(M.rails, curve({ x: agent.R.x + 4, y: 540 }, { x: n.L.x - 4, y: n.y }), th.mcp);
      init(n.rail, { opacity: 1 });
      return n;
    });
    const sources = L.sources.map((s, i) => {
      const n = card(arch, { x: SRC_X, y: ROW_Y[i], w: 300, h: 88, label: s.label, sub: s.sub, glyph: "stack", color: th.data, align: "left" });
      hidden(n.g, { scale: 0.92 });
      n.rail = rail(M.rails, `M ${servers[i].R.x + 4} ${n.y} L ${n.L.x - 4} ${n.y}`, th.data);
      init(n.rail, { opacity: 1 });
      return n;
    });
    const badges = servers.map((n) => {
      const b = pill(arch, L.quality.badge, n.x + n.w / 2 - 66, n.y - n.h / 2 - 2, th.positive, { size: 12, h: 26, fill: "#0B1712", halo: true });
      hidden(b.g, { scale: 0.5 });
      return b;
    });

    // Prompt bubble
    const prompt = (() => {
      const cx = 470, cy = 318, w = 600;
      const o = { size: 23, weight: 500 };
      const lines = wrap(L.prompt, w - 64, o);
      const h = 70 + lines.length * 34;
      const outer = mk("g", { transform: `translate(${cx} ${cy})` }, M.top);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 50, y: -h / 2 - 50, width: w + 100, height: h + 100, rx: 70, fill: halo(th.request), opacity: 0.5 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 18, fill: "url(#td-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("path", { d: `M ${-w / 2 + 40} ${h / 2} l -6 22 l 26 -22`, fill: "#0A0E15", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("rect", { x: -w / 2 + 33, y: h / 2 - 2, width: 34, height: 4, fill: "#0A0E15" }, g);
      txt(g, L.promptMeta, -w / 2 + 28, -h / 2 + 26, { size: 11.5, mono: true, fill: th.muted, anchor: "start", ls: "0.14em" });
      const els = lines.map((l, i) => txt(g, "", -w / 2 + 28, -h / 2 + 60 + i * 34, { ...o, anchor: "start" }));
      hidden(g, { y: 12 });
      return { g, lines, els };
    })();

    // ── Scene 1 — the request ───────────────────────────────────────────────
    const S1 = t;
    to(M.root, { opacity: 1 }, S1, S(0.6));
    show(user.g, S1 + S(0.4), 0.9);
    show(prompt.g, S1 + S(1.2), 0.8);
    {
      const total = prompt.lines.reduce((a, l) => a + l.length, 0);
      fx(S1 + S(1.8), S(3.4), (v) => {
        let n = Math.round(v * total);
        if (v >= 1) n = total;
        prompt.lines.forEach((l, i) => {
          const take = Math.max(0, Math.min(l.length, n));
          prompt.els[i].textContent = l.slice(0, take);
          n -= l.length;
        });
      });
    }
    const tSend = S1 + S(5.8);
    show(agent.g, tSend - S(0.3), 0.9);
    to(railUA, { opacity: 1 }, tSend - S(0.2), S(0.5));
    comet(M.fx, `M ${user.R.x + 4} 540 L ${agent.L.x - 4} 540`, th.request, tSend, S(1.0), { tail: 120 });
    lit(agent, tSend + S(0.8), 1);
    pulse(M.fx, agent, th.request, tSend + S(0.85));
    to(prompt.g, { opacity: 0.35 }, tSend + S(2.4), S(0.8));
    t = caption(L.cap.s1, tSend + S(1.2), S(3.4));
    to(prompt.g, { opacity: 0 }, t - S(0.6), S(0.6));
    eyebrow("request", S1, t);

    // ── Scene 2 — the stack ─────────────────────────────────────────────────
    const S2 = t;
    lit(agent, S2, 0.35, 0.6);
    show(srvTitle, S2 + S(0.1), 0.8);
    servers.forEach((n, i) => {
      show(n.g, S2 + S(0.3 + i * 0.25), 0.8);
      drawIn(n.rail, S2 + S(0.3 + i * 0.25), S(0.9));
    });
    show(srcTitle, S2 + S(1.1), 0.8);
    sources.forEach((n, i) => {
      show(n.g, S2 + S(1.3 + i * 0.25), 0.8);
      drawIn(n.rail, S2 + S(1.3 + i * 0.25), S(0.7));
    });
    const tCalls = S2 + S(2.8);
    servers.forEach((n, i) => {
      const tc = tCalls + i * S(0.35);
      comet(M.fx, curve({ x: agent.R.x + 4, y: 540 }, { x: n.L.x - 4, y: n.y }), th.mcp, tc, S(0.9), { tail: 120 });
      lit(n, tc + S(0.7), 0.9);
      comet(M.fx, `M ${n.R.x + 4} ${n.y} L ${sources[i].L.x - 4} ${n.y}`, th.mcp, tc + S(0.85), S(0.6), { tail: 90 });
      lit(sources[i], tc + S(1.35), 0.9);
      comet(M.fx, `M ${n.R.x + 4} ${n.y} L ${sources[i].L.x - 4} ${n.y}`, th.data, tc + S(1.6), S(0.6), { tail: 90, reverse: true });
      comet(M.fx, curve({ x: agent.R.x + 4, y: 540 }, { x: n.L.x - 4, y: n.y }), th.data, tc + S(2.1), S(0.9), { tail: 120, reverse: true });
      lit(n, tc + S(2.6), 0.25, 0.8);
      lit(sources[i], tc + S(2.6), 0.25, 0.8);
    });
    lit(agent, tCalls + S(3.3), 0.9);
    t = caption(L.cap.s2, tCalls + S(3.0), S(3.8), { sub: L.cap.s2Sub });
    eyebrow("stack", S2, t);

    // ── Scene 3 — data quality ──────────────────────────────────────────────
    const S3 = t;
    const Q = L.quality;
    const qG = mk("g", {}, M.top);
    init(qG, { opacity: 0 });
    const QP = { x: 960, y: 440, w: 1080 };
    const QROW = 56;
    QP.h = 34 + 52 + QROW * Q.rows.length + 36;
    const qTop = QP.y - QP.h / 2, qLeft = QP.x - QP.w / 2;
    mk("rect", { x: qLeft - 50, y: qTop - 50, width: QP.w + 100, height: QP.h + 100, rx: 60, fill: halo(th.mcp), opacity: 0.4 }, qG);
    mk("rect", { x: qLeft, y: qTop, width: QP.w, height: QP.h, rx: 18, fill: "url(#td-card)", stroke: th.mcp, "stroke-opacity": 0.5, "stroke-width": 1.2 }, qG);
    glyph(qG, "plug", qLeft + 36, qTop + 34, th.mcp);
    txt(qG, Q.panelTitle, qLeft + 60, qTop + 34, { size: 13, mono: true, fill: th.mcp, anchor: "start", ls: "0.14em" });
    const COLX = [0, 280, 440, 600, 780].map((c) => qLeft + 50 + c);
    const headY = qTop + 34 + 52;
    Q.cols.forEach((c, i) => txt(qG, c, COLX[i], headY, { size: 12, mono: true, fill: th.muted, anchor: "start", ls: "0.18em" }));
    mk("line", { x1: qLeft + 30, y1: headY + 22, x2: qLeft + QP.w - 30, y2: headY + 22, stroke: th.line }, qG);
    const rowY = (i) => headY + 22 + QROW * (i + 0.5) + 4;
    const qRows = Q.rows.map((r, i) => {
      const g = mk("g", {}, qG);
      const tint = mk("rect", { x: qLeft + 24, y: rowY(i) - QROW / 2 + 4, width: QP.w - 48, height: QROW - 8, rx: 8, fill: th.warn, "fill-opacity": 0.1, stroke: th.warn, "stroke-opacity": 0.4 }, g);
      init(tint, { opacity: 0 });
      const cells = r.map((c, j) => txt(g, c, COLX[j], rowY(i), { size: 20, mono: true, anchor: "start" }));
      hidden(g, { x: -12 });
      return { g, tint, cells };
    });
    // the three defects: duplicate row 1, missing qty row 2, stale row 3
    const badCells = [null, [2, 2], [3, 4]].map((rc) => {
      if (!rc) return null;
      const src = qRows[rc[0]].cells[rc[1]];
      const red = txt(qRows[rc[0]].g, src.textContent, COLX[rc[1]], rowY(rc[0]), { size: 20, mono: true, anchor: "start", fill: th.warn });
      init(red, { opacity: 0 });
      return { src, red };
    });
    const flags = Q.flags.map((f, i) => {
      const p = pill(qG, f, qLeft + QP.w + 22, rowY(i + 1), th.warn, { size: 12, anchor: "start", h: 28 });
      hidden(p.g, { x: -10 });
      return p;
    });
    const fixedCells = [
      txt(qG, Q.fixed[0][2], COLX[2], rowY(2), { size: 20, mono: true, anchor: "start", fill: th.positive }),
      txt(qG, Q.fixed[1][3], COLX[3], rowY(3), { size: 20, mono: true, anchor: "start", fill: th.positive }),
      txt(qG, Q.fixed[1][4], COLX[4], rowY(3), { size: 20, mono: true, anchor: "start", fill: th.positive }),
    ];
    fixedCells.forEach((c) => init(c, { opacity: 0 }));
    const strike = mk("line", { x1: qLeft + 40, y1: rowY(1), x2: qLeft + QP.w - 40, y2: rowY(1), stroke: th.warn, "stroke-width": 2 }, qG);
    init(strike, { opacity: 0 });
    const okMarks = [1, 2, 3].map((i) => {
      const g = glyph(qG, "check", qLeft + QP.w + 40, rowY(i), th.positive, 1.1);
      init(g, { opacity: 0 });
      return g;
    });
    const scan = mk("rect", { x: 0, y: headY + 26, width: 3, height: QROW * Q.rows.length - 6, fill: th.mcp }, qG);
    // answer under the panel
    const ansY = qTop + QP.h + 70;
    const ansBad = mk("g", {}, M.top);
    txt(ansBad, Q.answerBad, 960, ansY, { size: 26, weight: 600 });
    txt(ansBad, Q.answerBadTag, 960, ansY + 40, { size: 15, mono: true, fill: th.warn });
    hidden(ansBad, { y: 10 });
    const ansGood = mk("g", {}, M.top);
    txt(ansGood, Q.answerGood, 960, ansY, { size: 26, weight: 600 });
    txt(ansGood, Q.answerGoodTag, 960, ansY + 40, { size: 15, mono: true, fill: th.positive });
    hidden(ansGood, { y: 10 });
    // quality checks row
    const checksG = mk("g", {}, M.top);
    init(checksG, { opacity: 0 });
    const checkTitle = txt(checksG, Q.checksTitle, 960, 148, { size: 13, mono: true, fill: th.positive, ls: "0.28em" });
    const chkW = Q.checks.map((c) => measure(c, { size: 13, mono: true }) + 54);
    const chkGap = 18;
    let cx0 = 960 - (chkW.reduce((a, b) => a + b, 0) + chkGap * (chkW.length - 1)) / 2;
    const checks = Q.checks.map((c, i) => {
      const p = pill(checksG, c, cx0, 192, th.positive, { size: 13, anchor: "start", glyph: "check", h: 32, fill: "#0B1712" });
      cx0 += chkW[i] + chkGap;
      init(p.g, { opacity: 0.25 });
      return p;
    });

    init(M.rails, { opacity: 1 });
    to(arch, { opacity: 0.1 }, S3, S(0.8));
    to(M.rails, { opacity: 0.1 }, S3, S(0.8));
    to(qG, { opacity: 1 }, S3 + S(0.5), S(0.8));
    qRows.forEach((r, i) => show(r.g, S3 + S(0.9 + i * 0.25), 0.6));
    const tFlag = S3 + S(2.6);
    [1, 2, 3].forEach((ri, i) => {
      const tf = tFlag + i * S(0.7);
      to(qRows[ri].tint, { opacity: 1 }, tf, S(0.4));
      show(flags[i].g, tf + S(0.1), 0.5);
      if (badCells[i]) to(badCells[i].red, { opacity: 1 }, tf, S(0.3));
    });
    const tBad = tFlag + S(2.6);
    show(ansBad, tBad, 0.7);
    caption(L.cap.s3Bad, tBad + S(0.4), S(3.6), { sub: L.cap.s3BadSub, fill: th.text });
    const tFix = tBad + S(5.4);
    hide(ansBad, tFix - S(0.4), 0.4);
    to(checksG, { opacity: 1 }, tFix, S(0.5));
    checks.forEach((c, i) => to(c.g, { opacity: 1 }, tFix + S(0.4 + i * 0.35), S(0.35)));
    fx(tFix + S(0.3), S(1.8), (v) => {
      scan.setAttribute("opacity", v <= 0 || v >= 1 ? 0 : 0.8);
      scan.setAttribute("x", qLeft + 30 + v * (QP.w - 60));
    }, "power1.inOut");
    const tRepair = tFix + S(1.9);
    to(strike, { opacity: 1 }, tRepair, S(0.4));
    to(qRows[1].g, { opacity: 0.25 }, tRepair + S(0.5), S(0.6));
    hide(qRows[2].cells[2], tRepair + S(0.4), 0.3);
    hide(badCells[1].red, tRepair + S(0.4), 0.3);
    hide(badCells[2].red, tRepair + S(0.8), 0.3);
    show(fixedCells[0], tRepair + S(0.6), 0.4);
    hide(qRows[3].cells[3], tRepair + S(0.8), 0.3);
    hide(qRows[3].cells[4], tRepair + S(0.8), 0.3);
    show(fixedCells[1], tRepair + S(1.0), 0.4);
    show(fixedCells[2], tRepair + S(1.0), 0.4);
    [1, 2, 3].forEach((ri, i) => {
      to(qRows[ri].tint, { opacity: 0 }, tRepair + S(0.3 + i * 0.3), S(0.4));
      hide(flags[i].g, tRepair + S(0.3 + i * 0.3), 0.3);
      to(okMarks[i], { opacity: 1 }, tRepair + S(0.6 + i * 0.3), S(0.4));
    });
    show(ansGood, tRepair + S(1.6), 0.7);
    const tGoodEnd = caption(L.cap.s3Good, tRepair + S(1.8), S(3.2));
    // back to the architecture: quality badges land on the MCP servers
    const tBack = tRepair + S(5.4);
    hide(qG, tBack, 0.6);
    hide(checksG, tBack, 0.6);
    hide(ansGood, tBack, 0.6);
    to(arch, { opacity: 1 }, tBack + S(0.3), S(0.8));
    to(M.rails, { opacity: 1 }, tBack + S(0.3), S(0.8));
    badges.forEach((b, i) => {
      show(b.g, tBack + S(1.0 + i * 0.25), 0.5, "back.out(2)");
      pulse(M.fx, servers[i], th.positive, tBack + S(1.0 + i * 0.25));
    });
    t = Math.max(tGoodEnd, tBack + S(3.4));
    eyebrow("quality", S3, t);
    hide(M.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 4 — data context: poorly vs well described MCP tools
    // ═════════════════════════════════════════════════════════════════════════
    const S4 = t;
    const C4 = L.context;
    const P4 = world();
    function toolPanel(cx, title, color) {
      const w = 820, h = 540, y = 540;
      const outer = mk("g", { transform: `translate(${cx} ${y})` }, P4.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 40, y: -h / 2 - 40, width: w + 80, height: h + 80, rx: 60, fill: halo(color), opacity: 0.35 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 20, fill: "url(#td-card)", stroke: color, "stroke-opacity": 0.55, "stroke-width": 1.3 }, g);
      txt(g, title, 0, -h / 2 + 34, { size: 14, mono: true, fill: color, ls: "0.3em", weight: 600 });
      mk("line", { x1: -w / 2 + 30, y1: -h / 2 + 60, x2: w / 2 - 30, y2: -h / 2 + 60, stroke: th.line }, g);
      hidden(g, { y: 16 });
      return { outer, g, x: cx, y, w, h, left: -w / 2 + 40, top: -h / 2 + 60 };
    }
    const bad = toolPanel(500, C4.badTitle, th.warn);
    const good = toolPanel(1420, C4.goodTitle, th.positive);
    // bad panel content
    txt(bad.g, "tool", bad.left, bad.top + 44, { size: 13, mono: true, fill: th.muted, anchor: "start" });
    txt(bad.g, C4.badTool, bad.left, bad.top + 80, { size: 26, mono: true, fill: th.mcp, anchor: "start" });
    txt(bad.g, C4.badDesc, bad.left, bad.top + 122, { size: 18, italic: true, fill: th.muted, anchor: "start" });
    txt(bad.g, "fields", bad.left, bad.top + 176, { size: 13, mono: true, fill: th.muted, anchor: "start" });
    let bx = bad.left;
    const badFields = C4.badFields.map((f) => {
      const p = pill(bad.g, f, bx, bad.top + 218, th.faint, { size: 17, anchor: "start", h: 38, textFill: th.text });
      bx += p.w + 14;
      return p;
    });
    const qty = badFields[1];
    const qtyHi = mk("rect", { x: qty.L.x - 4, y: qty.y - 23, width: qty.w + 8, height: 46, rx: 23, fill: "none", stroke: th.c2, "stroke-width": 2 }, bad.g);
    init(qtyHi, { opacity: 0 });
    const guess = txt(bad.g, C4.badGuess, bad.left, bad.top + 290, { size: 19, mono: true, fill: th.c2, anchor: "start" });
    hidden(guess, { y: 8 });
    const badVerdict = txt(bad.g, C4.badVerdict, 0, bad.h / 2 - 50, { size: 20, weight: 600, fill: th.warn });
    hidden(badVerdict, { y: 8 });
    // good panel content
    txt(good.g, "tool", good.left, good.top + 44, { size: 13, mono: true, fill: th.muted, anchor: "start" });
    txt(good.g, C4.goodTool, good.left, good.top + 76, { size: 20, mono: true, fill: th.mcp, anchor: "start" });
    wrap(C4.goodDesc, good.w - 80, { size: 17, italic: true }).forEach((l, i) =>
      txt(good.g, l, good.left, good.top + 112 + i * 24, { size: 17, italic: true, fill: th.text, anchor: "start", opacity: 0.85 }));
    txt(good.g, "fields", good.left, good.top + 176, { size: 13, mono: true, fill: th.muted, anchor: "start" });
    const goodRows = C4.goodFields.map(([f, d], i) => {
      const y = good.top + 210 + i * 40;
      const hi = mk("rect", { x: good.left - 12, y: y - 17, width: good.w - 56, height: 34, rx: 8, fill: th.positive, "fill-opacity": 0.1, stroke: th.positive, "stroke-opacity": 0.5 }, good.g);
      init(hi, { opacity: 0 });
      txt(good.g, f, good.left, y, { size: 16, mono: true, fill: th.mcp, anchor: "start" });
      txt(good.g, d, good.left + 170, y, { size: 16, fill: th.text, anchor: "start" });
      return hi;
    });
    let mx = good.left;
    C4.goodMeta.forEach((m) => {
      const p = pill(good.g, m, mx, good.top + 386, th.data, { size: 12, anchor: "start", h: 28 });
      mx += p.w + 10;
    });
    const goodVerdict = txt(good.g, C4.goodVerdict, 0, good.h / 2 - 50, { size: 20, weight: 600, fill: th.positive });
    hidden(goodVerdict, { y: 8 });
    // the agent looking for a field
    const probe = pill(P4.top, C4.agentProbe, 960, 196, th.request, { size: 14, h: 36, glyph: "spark", halo: true });
    hidden(probe.g, { y: -10 });

    to(P4.root, { opacity: 1 }, S4, S(0.5));
    show(bad.g, S4 + S(0.3), 0.8);
    show(good.g, S4 + S(0.6), 0.8);
    show(probe.g, S4 + S(1.6), 0.6);
    const tProbe = S4 + S(2.6);
    comet(P4.fx, `M 900 214 C 760 300, ${bad.x + qty.x} 600, ${bad.x + qty.x} ${bad.y + bad.top + 196}`, th.request, tProbe, S(1.2), { tail: 140 });
    to(qtyHi, { opacity: 1 }, tProbe + S(1.1), S(0.3));
    show(guess, tProbe + S(1.4), 0.5);
    show(badVerdict, tProbe + S(2.6), 0.5);
    const tProbe2 = tProbe + S(3.4);
    comet(P4.fx, `M 1020 214 C 1160 300, ${good.x + good.left - 20} 440, ${good.x + good.left + 60} ${good.y + good.top + 210}`, th.request, tProbe2, S(1.1), { tail: 140 });
    [0, 1].forEach((i) => to(goodRows[i], { opacity: 1 }, tProbe2 + S(1.0 + i * 0.25), S(0.3)));
    show(goodVerdict, tProbe2 + S(1.6), 0.5);
    t = caption(L.cap.s4, tProbe2 + S(2.2), S(5.0), { sub: L.cap.s4Sub });
    eyebrow("context", S4, t);
    hide(P4.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 5 — who sees what
    // ═════════════════════════════════════════════════════════════════════════
    const S5 = t;
    const A5 = L.access;
    const P5 = world();
    const uA = person(P5.nodes, 170, 360, A5.userA.label, A5.userA.sub, th.request);
    const uB = person(P5.nodes, 170, 730, A5.userB.label, A5.userB.sub, th.cloud);
    hidden(uA.g, { scale: 0.9 });
    hidden(uB.g, { scale: 0.9 });
    const ag5 = card(P5.nodes, { x: 580, y: 540, w: 270, h: 90, r: 22, label: L.agent, glyph: "spark", color: th.request, size: 16 });
    const gate = card(P5.nodes, { x: 1000, y: 540, w: 320, h: 96, label: A5.gate, sub: A5.gateSub, glyph: "shield", color: th.mcp, size: 15 });
    const om = card(P5.nodes, { x: 1400, y: 540, w: 250, h: 88, label: A5.source, sub: A5.sourceSub, glyph: "plug", color: th.mcp, align: "left" });
    [ag5, gate, om].forEach((n) => hidden(n.g, { scale: 0.92 }));
    const gateRed = mk("rect", { x: -gate.w / 2, y: -gate.h / 2, width: gate.w, height: gate.h, rx: gate.r, fill: th.warn, "fill-opacity": 0.08, stroke: th.warn, "stroke-width": 2 }, gate.g);
    init(gateRed, { opacity: 0 });
    const pUA = curve({ x: uA.R.x + 4, y: uA.y }, { x: ag5.L.x - 4, y: 540 });
    const pUB = curve({ x: uB.R.x + 4, y: uB.y }, { x: ag5.L.x - 4, y: 540 });
    const pAG = `M ${ag5.R.x + 4} 540 L ${gate.L.x - 4} 540`;
    const pTok = `M ${ag5.x + 40} ${ag5.T.y - 6} C ${ag5.x + 120} 380, ${gate.x - 140} 380, ${gate.x - 30} ${gate.T.y - 6}`;
    const pGO = `M ${gate.R.x + 4} 540 L ${om.L.x - 4} 540`;
    const r5 = [pUA, pUB, pAG, pGO].map((d) => { const r = rail(P5.rails, d, th.request); init(r, { opacity: 0 }); return r; });
    const rowsX = 1745;
    const dRows = A5.rows.map((s, i) => {
      const y = 420 + i * 120;
      const p = pill(P5.nodes, s, rowsX, y, th.data, { size: 14, h: 36 });
      const r = rail(P5.rails, curve({ x: om.R.x + 4, y: 540 }, { x: p.L.x - 4, y }), th.data, { opacity: 0.25 });
      hidden(p.g, { x: 10 });
      init(r, { opacity: 0 });
      return { p, r, y };
    });
    const cRow = dRows[2];
    const cStrike = mk("line", { x1: cRow.p.L.x + 8, y1: cRow.y, x2: cRow.p.R.x - 8, y2: cRow.y, stroke: th.warn, "stroke-width": 2 }, P5.top);
    init(cStrike, { opacity: 0 });
    const cLabel = txt(P5.top, A5.filtered, rowsX, cRow.y + 34, { size: 13, mono: true, fill: th.warn });
    hidden(cLabel, { y: 6 });
    const denied = txt(P5.top, A5.denied, gate.x, gate.y + 88, { size: 17, weight: 600, fill: th.warn });
    hidden(denied, { y: 8 });
    const tokA = dataChip(P5.fx, A5.token, th.request);
    const tokB = dataChip(P5.fx, A5.tokenB, th.cloud);
    // audit log
    const audit = (() => {
      const x = 1380, y = 200, w = 860, h = 130;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, P5.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 14, fill: "#080B11", stroke: th.line }, g);
      txt(g, A5.auditTitle, -w / 2 + 24, -h / 2 + 24, { size: 12, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
      const lines = A5.audit.map((r, i) => {
        const lg = mk("g", {}, g);
        const ly = -h / 2 + 62 + i * 34;
        const ok = r[3].startsWith("✓");
        txt(lg, r[0], -w / 2 + 24, ly, { size: 14, mono: true, fill: th.muted, anchor: "start" });
        txt(lg, r[1], -w / 2 + 130, ly, { size: 14, mono: true, fill: ok ? th.request : th.cloud, anchor: "start" });
        txt(lg, r[2], -w / 2 + 270, ly, { size: 14, mono: true, fill: th.text, anchor: "start" });
        txt(lg, r[3], w / 2 - 24, ly, { size: 14, mono: true, fill: ok ? th.positive : th.warn, anchor: "end" });
        hidden(lg, { x: -8 });
        return lg;
      });
      hidden(g, { y: -10 });
      return { g, lines };
    })();

    to(P5.root, { opacity: 1 }, S5, S(0.5));
    show(uA.g, S5 + S(0.3), 0.7);
    show(uB.g, S5 + S(0.5), 0.7);
    show(ag5.g, S5 + S(0.7), 0.7);
    show(gate.g, S5 + S(0.9), 0.7);
    show(om.g, S5 + S(1.1), 0.7);
    r5.forEach((r, i) => to(r, { opacity: 1 }, S5 + S(0.8 + i * 0.15), S(0.5)));
    dRows.forEach((d, i) => { show(d.p.g, S5 + S(1.3 + i * 0.15), 0.6); to(d.r, { opacity: 1 }, S5 + S(1.3 + i * 0.15), S(0.5)); });
    show(audit.g, S5 + S(1.8), 0.6);
    // user A — allowed, filtered to their clients
    const tA = S5 + S(2.6);
    lit({ glow: uA.glow }, tA, 1);
    comet(P5.fx, pUA, th.request, tA + S(0.2), S(1.0), { tail: 120 });
    lit(ag5, tA + S(1.1), 0.9);
    caption(L.cap.s5a, tA + S(0.4), S(3.4));
    carry(tokA, pTok, tA + S(1.3), S(1.5));
    lit(gate, tA + S(2.6), 1);
    pulse(P5.fx, gate, th.positive, tA + S(2.7));
    comet(P5.fx, pGO, th.mcp, tA + S(2.9), S(0.7), { tail: 100 });
    lit(om, tA + S(3.4), 0.9);
    [0, 1].forEach((i) => {
      comet(P5.fx, curve({ x: om.R.x + 4, y: 540 }, { x: dRows[i].p.L.x - 4, y: dRows[i].y }), th.data, tA + S(3.7), S(0.8), { tail: 100, reverse: true });
      to(dRows[i].p.g, { scale: 1.06 }, tA + S(4.3), S(0.3));
    });
    to(cRow.p.g, { opacity: 0.35 }, tA + S(4.0), S(0.5));
    to(cStrike, { opacity: 1 }, tA + S(4.0), S(0.4));
    show(cLabel, tA + S(4.2), 0.5);
    comet(P5.fx, pGO, th.data, tA + S(4.7), S(0.7), { tail: 100, reverse: true });
    comet(P5.fx, pAG, th.data, tA + S(5.2), S(0.8), { tail: 120, reverse: true });
    comet(P5.fx, pUA, th.data, tA + S(5.8), S(0.9), { tail: 120, reverse: true });
    show(audit.lines[0], tA + S(5.0), 0.5);
    lit({ glow: uA.glow }, tA + S(6.6), 0, 0.6);
    lit(gate, tA + S(6.6), 0.2, 0.6);
    lit(om, tA + S(6.6), 0.2, 0.6);
    // user B — same question, blocked at the gate
    const tB = tA + S(7.2);
    lit({ glow: uB.glow }, tB, 1);
    comet(P5.fx, pUB, th.cloud, tB + S(0.2), S(1.0), { tail: 120 });
    caption(L.cap.s5b, tB + S(0.4), S(3.4));
    carry(tokB, pTok, tB + S(1.3), S(1.5));
    to(gateRed, { opacity: 1 }, tB + S(2.6), S(0.2));
    pulse(P5.fx, gate, th.warn, tB + S(2.7));
    show(denied, tB + S(2.8), 0.5);
    show(audit.lines[1], tB + S(3.2), 0.5);
    to(gateRed, { opacity: 0 }, tB + S(5.2), S(0.6));
    lit({ glow: uB.glow }, tB + S(5.2), 0, 0.6);
    t = caption(L.cap.s5c, tB + S(5.0), S(4.0), { sub: L.cap.s5Sub });
    eyebrow("access", S5, t);
    hide(P5.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 6 — client orders stay private (anonymisation)
    // ═════════════════════════════════════════════════════════════════════════
    const S6 = t;
    const V = L.privacy;
    const P6 = world();
    function orderCard(cx, title, color) {
      const w = 600, h = 400, y = 400;
      const outer = mk("g", { transform: `translate(${cx} ${y})` }, P6.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 40, y: -h / 2 - 40, width: w + 80, height: h + 80, rx: 60, fill: halo(color), opacity: 0.35 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 18, fill: "url(#td-card)", stroke: color, "stroke-opacity": 0.55, "stroke-width": 1.3 }, g);
      txt(g, title, -w / 2 + 30, -h / 2 + 32, { size: 13, mono: true, fill: color, anchor: "start", ls: "0.16em" });
      mk("line", { x1: -w / 2 + 24, y1: -h / 2 + 58, x2: w / 2 - 24, y2: -h / 2 + 58, stroke: th.line }, g);
      hidden(g, { y: 14 });
      return { g, x: cx, y, w, h, rowY: (i) => y - h / 2 + 100 + i * 50, rowLocal: (i) => -h / 2 + 100 + i * 50 };
    }
    const inC = orderCard(470, V.orderTitle, th.data);
    const outC = orderCard(1450, V.outTitle, th.cloud);
    const outVals = V.fields.map(([key, val, anon], i) => {
      const changed = val !== anon;
      txt(inC.g, key, -inC.w / 2 + 30, inC.rowLocal(i), { size: 15, mono: true, fill: th.muted, anchor: "start" });
      txt(inC.g, val, -inC.w / 2 + 190, inC.rowLocal(i), { size: 21, weight: 500, fill: changed ? th.c3 : th.text, anchor: "start" });
      txt(outC.g, key, -outC.w / 2 + 30, outC.rowLocal(i), { size: 15, mono: true, fill: th.muted, anchor: "start" });
      const v = txt(outC.g, anon, -outC.w / 2 + 190, outC.rowLocal(i), { size: 21, weight: 500, fill: changed ? th.c2 : th.text, anchor: "start", mono: changed });
      hidden(v, { x: -10 });
      return { v, changed, y: inC.rowY(i) };
    });
    const eng = card(P6.nodes, { x: 960, y: 400, w: 250, h: 104, r: 18, label: V.engine, sub: V.engineSub, glyph: "mask", color: th.mcp, size: 14 });
    hidden(eng.g, { scale: 0.92 });
    const vault = (() => {
      const x = 960, y = 700, w = 640, h = 92;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, P6.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 16, fill: "#0A0E15", stroke: th.perimeter, "stroke-opacity": 0.6, "stroke-dasharray": "5 6" }, g);
      glyph(g, "lock", -w / 2 + 40, 0, th.perimeter, 1.4);
      txt(g, V.vault, -w / 2 + 76, -14, { size: 18, mono: true, fill: th.text, anchor: "start" });
      txt(g, V.vaultSub, -w / 2 + 76, 18, { size: 13, mono: true, fill: th.perimeter, anchor: "start" });
      hidden(g, { y: 12 });
      return { g };
    })();
    const vaultLink = rail(P6.rails, `M 960 ${eng.B.y + 4} L 960 ${700 - 50}`, th.perimeter, { dash: "4 6", opacity: 0.6 });
    init(vaultLink, { opacity: 0 });
    const gW = V.guarantees.map((s) => measure(s, { size: 14, mono: true }) + 54);
    const gGap = 16;
    let gx = 960 - (gW.reduce((a, b) => a + b, 0) + gGap * (gW.length - 1)) / 2;
    const guarantees = V.guarantees.map((s, i) => {
      const p = pill(P6.nodes, s, gx, 846, th.positive, { size: 14, anchor: "start", glyph: "check", h: 36, fill: "#0B1712" });
      gx += gW[i] + gGap;
      hidden(p.g, { y: 10 });
      return p;
    });

    to(P6.root, { opacity: 1 }, S6, S(0.5));
    show(inC.g, S6 + S(0.3), 0.8);
    show(eng.g, S6 + S(0.9), 0.7);
    show(outC.g, S6 + S(1.2), 0.8);
    lit(eng, S6 + S(2.0), 0.8);
    const tRows = S6 + S(2.2);
    caption(L.cap.s6a, tRows + S(0.4), S(4.2));
    outVals.forEach((o, i) => {
      const tr = tRows + i * S(0.55);
      comet(P6.fx, curve({ x: inC.x + inC.w / 2 - 20, y: o.y }, { x: eng.L.x - 4, y: 400 }), o.changed ? th.c3 : th.muted, tr, S(0.6), { tail: 70, scale: 0.6 });
      comet(P6.fx, curve({ x: eng.R.x + 4, y: 400 }, { x: outC.x - outC.w / 2 + 20, y: o.y }), o.changed ? th.c2 : th.muted, tr + S(0.5), S(0.6), { tail: 70, scale: 0.6 });
      show(o.v, tr + S(1.0), 0.4);
    });
    const tVault = tRows + V.fields.length * S(0.55) + S(1.0);
    to(vaultLink, { opacity: 1 }, tVault, S(0.5));
    show(vault.g, tVault + S(0.2), 0.7);
    lit(eng, tVault + S(0.6), 0.3, 0.6);
    const tGuar = tVault + S(2.4);
    guarantees.forEach((p, i) => show(p.g, tGuar + S(i * 0.35), 0.5));
    t = caption(L.cap.s6b, tGuar + S(1.4), S(4.2));
    eyebrow("privacy", S6, t);
    hide(P6.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 7 — where does the model run? (routing by sensitivity)
    // ═════════════════════════════════════════════════════════════════════════
    const S7 = t;
    const R = L.routing;
    const P7 = world();
    const zone = (x, w, label, color) => {
      const g = mk("g", {}, P7.rails);
      mk("rect", { x, y: 140, width: w, height: 730, rx: 30, fill: color, "fill-opacity": 0.035, stroke: color, "stroke-opacity": 0.55, "stroke-width": 1.4, "stroke-dasharray": "8 8" }, g);
      glyph(g, color === th.cloud ? "cloud" : "lock", x + 36, 176, color, 1.1);
      txt(g, label, x + 62, 176, { size: 14, mono: true, fill: color, anchor: "start", ls: "0.2em", weight: 600 });
      hidden(g);
      return g;
    };
    const zIn = zone(60, 1130, R.perimeter, th.perimeter);
    const zOut = zone(1300, 560, R.cloud, th.cloud);
    const linkLbl = mk("g", {}, P7.rails);
    glyph(linkLbl, "lock", 1245, 900, th.muted, 0.9);
    txt(linkLbl, R.link, 1245, 926, { size: 12, mono: true, fill: th.muted });
    hidden(linkLbl);
    const ag7 = card(P7.nodes, { x: 230, y: 480, w: 250, h: 84, r: 22, label: R.agent, glyph: "spark", color: th.request, size: 15 });
    const gw = card(P7.nodes, { x: 590, y: 480, w: 300, h: 96, label: R.gateway, sub: R.gatewaySub, glyph: "route", color: th.mcp, size: 14 });
    const anon = card(P7.nodes, { x: 990, y: 330, w: 250, h: 78, label: R.anon, glyph: "mask", color: th.c2, size: 14 });
    const gpu = card(P7.nodes, { x: 990, y: 640, w: 290, h: 92, label: R.gpu, sub: R.gpuSub, glyph: "chip", color: th.perimeter, size: 15 });
    const fm = card(P7.nodes, { x: 1580, y: 400, w: 330, h: 104, r: 18, label: R.frontier, sub: R.frontierSub, glyph: "hex", color: th.cloud, size: 16 });
    [ag7, gw, anon, gpu, fm].forEach((n) => hidden(n.g, { scale: 0.92 }));
    const pAgGw = `M ${ag7.R.x + 4} 480 L ${gw.L.x - 4} 480`;
    const pGwGpu = curve({ x: gw.R.x + 4, y: 492 }, { x: gpu.L.x - 4, y: 640 });
    const pGwAnon = curve({ x: gw.R.x + 4, y: 470 }, { x: anon.L.x - 4, y: 330 });
    const pAnonFm = curve({ x: anon.R.x + 4, y: 330 }, { x: fm.L.x - 4, y: 388 });
    const pGwFm = `M ${gw.x + 40} ${gw.T.y - 4} C ${gw.x + 120} 210, 1360 220, ${fm.x - 60} ${fm.T.y - 4}`;
    const r7 = [[pAgGw, th.request], [pGwGpu, th.c3], [pGwAnon, th.c2], [pAnonFm, th.c2], [pGwFm, th.c1]].map(([d, c]) => {
      const r = rail(P7.rails, d, c, { opacity: 0.3 });
      init(r, { opacity: 0 });
      return r;
    });
    // the three sub-tasks below the agent
    const tasks = R.tasks.map((tk, i) => {
      const y = 640 + i * 62;
      const color = LV[tk.level];
      const p = pill(P7.nodes, `${tk.level}  ${tk.label}`, 90, y, color, { size: 13, anchor: "start", h: 34 });
      const route = txt(P7.nodes, "→ " + tk.route, 90 + p.w + 14, y, { size: 13, mono: true, fill: color, anchor: "start" });
      hidden(p.g, { x: -10 });
      hidden(route, { x: -6 });
      return { p, route, color, y };
    });
    const cC3 = dataChip(P7.fx, R.chips.c3, th.c3);
    const cC2a = dataChip(P7.fx, R.chips.c2Before, th.c2);
    const cC2b = dataChip(P7.fx, R.chips.c2After, th.c2);
    const cC1 = dataChip(P7.fx, R.chips.c1, th.c1);
    const tagStay = pill(P7.top, R.tasks[0].route.toUpperCase(), gpu.x, gpu.B.y + 32, th.c3, { size: 12, h: 26 });
    hidden(tagStay.g, { y: 6 });
    // legend
    const legend = (() => {
      const x = 1580, y = 700, w = 520, h = 196;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, P7.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 14, fill: "#080B11", stroke: th.line }, g);
      txt(g, R.legendTitle, -w / 2 + 22, -h / 2 + 26, { size: 12, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
      R.legend.forEach(([lv, name, rule], i) => {
        const ly = -h / 2 + 68 + i * 44;
        mk("circle", { cx: -w / 2 + 30, cy: ly, r: 6, fill: LV[lv] }, g);
        txt(g, lv, -w / 2 + 46, ly, { size: 14, mono: true, fill: LV[lv], anchor: "start", weight: 600 });
        txt(g, name, -w / 2 + 84, ly, { size: 15, weight: 600, anchor: "start" });
        txt(g, rule, -w / 2 + 210, ly, { size: 14, fill: th.muted, anchor: "start" });
      });
      hidden(g, { y: 10 });
      return g;
    })();
    // bonus: a purely public question
    const bonus = pill(P7.top, R.bonusPrompt, 260, 300, th.c1, { size: 16, h: 40, sans: true, textFill: th.text, halo: true });
    hidden(bonus.g, { y: 10 });
    const bonusTag = txt(P7.top, R.bonusTag, 260, 348, { size: 14, mono: true, fill: th.c1 });
    hidden(bonusTag, { y: 6 });

    to(P7.root, { opacity: 1 }, S7, S(0.5));
    show(zIn, S7 + S(0.3), 0.8);
    show(zOut, S7 + S(0.6), 0.8);
    show(linkLbl, S7 + S(0.9), 0.6);
    show(ag7.g, S7 + S(0.8), 0.7);
    show(gw.g, S7 + S(1.0), 0.7);
    show(anon.g, S7 + S(1.3), 0.7);
    show(gpu.g, S7 + S(1.5), 0.7);
    show(fm.g, S7 + S(1.7), 0.7);
    r7.forEach((r, i) => to(r, { opacity: 1 }, S7 + S(1.2 + i * 0.15), S(0.5)));
    const tSplit = S7 + S(2.6);
    lit(ag7, tSplit, 0.9);
    tasks.forEach((tk, i) => show(tk.p.g, tSplit + S(0.3 + i * 0.3), 0.5));
    caption(L.cap.s7a, tSplit + S(0.3), S(3.0));
    // classification + routing, one task after the other
    const tRoute = tSplit + S(2.2);
    comet(P7.fx, pAgGw, th.request, tRoute, S(0.8), { tail: 120 });
    lit(gw, tRoute + S(0.7), 1);
    // C3 → on-prem GPUs
    const t3 = tRoute + S(1.0);
    pulse(P7.fx, gw, th.c3, t3);
    show(tasks[0].route, t3 + S(0.2), 0.4);
    carry(cC3, pGwGpu, t3 + S(0.2), S(1.6));
    lit(gpu, t3 + S(1.6), 1);
    show(tagStay.g, t3 + S(1.8), 0.4);
    // C2 → anonymiser → frontier
    const t2 = t3 + S(2.0);
    pulse(P7.fx, gw, th.c2, t2);
    show(tasks[1].route, t2 + S(0.2), 0.4);
    carry(cC2a, pGwAnon, t2 + S(0.2), S(1.4));
    lit(anon, t2 + S(1.4), 1);
    pulse(P7.fx, anon, th.c2, t2 + S(1.5));
    carry(cC2b, pAnonFm, t2 + S(1.7), S(1.8));
    lit(fm, t2 + S(3.3), 1);
    // C1 → straight to frontier
    const t1 = t2 + S(2.6);
    pulse(P7.fx, gw, th.c1, t1);
    show(tasks[2].route, t1 + S(0.2), 0.4);
    carry(cC1, pGwFm, t1 + S(0.2), S(1.8));
    caption(L.cap.s7b, t2 + S(0.2), S(4.6));
    // results flow back into the perimeter
    const tRet = t1 + S(2.3);
    comet(P7.fx, pGwGpu, th.data, tRet, S(0.9), { tail: 110, reverse: true });
    comet(P7.fx, pAnonFm, th.data, tRet + S(0.1), S(1.0), { tail: 110, reverse: true });
    comet(P7.fx, pGwAnon, th.data, tRet + S(1.0), S(0.7), { tail: 100, reverse: true });
    comet(P7.fx, pGwFm, th.data, tRet + S(0.2), S(1.4), { tail: 140, reverse: true });
    comet(P7.fx, pAgGw, th.data, tRet + S(1.7), S(0.7), { tail: 110, reverse: true });
    pulse(P7.fx, ag7, th.data, tRet + S(2.3));
    [gpu, anon, fm, gw].forEach((n) => lit(n, tRet + S(2.4), 0.25, 0.6));
    show(legend, tRet + S(0.6), 0.7);
    // bonus: purely public → frontier, no detour
    const tBonus = tRet + S(3.2);
    show(bonus.g, tBonus, 0.6);
    comet(P7.fx, `M ${bonus.x} ${bonus.y + 22} L ${ag7.x} ${ag7.T.y - 4}`, th.c1, tBonus + S(0.7), S(0.5), { tail: 60 });
    comet(P7.fx, pAgGw, th.c1, tBonus + S(1.1), S(0.5), { tail: 90 });
    comet(P7.fx, pGwFm, th.c1, tBonus + S(1.5), S(1.0), { tail: 140 });
    lit(fm, tBonus + S(2.4), 1);
    show(bonusTag, tBonus + S(2.2), 0.5);
    t = caption(L.cap.s7c, tBonus + S(2.6), S(4.0));
    eyebrow("routing", S7, t);
    hide(P7.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 8 — the answer
    // ═════════════════════════════════════════════════════════════════════════
    const S8 = t;
    const Rs = L.result;
    const P8 = world();
    const u8 = person(P8.nodes, 190, 450, L.user.label, L.user.sub, th.request);
    hidden(u8.g, { scale: 0.9 });
    const ans = (() => {
      const x = 1040, y = 450, w = 1160, h = 520;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, P8.nodes);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 50, y: -h / 2 - 50, width: w + 100, height: h + 100, rx: 70, fill: halo(th.request), opacity: 0.45 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 20, fill: "url(#td-card)", stroke: th.request, "stroke-opacity": 0.5, "stroke-width": 1.3 }, g);
      mk("path", { d: `M ${-w / 2} -20 l -22 20 l 22 20`, fill: "#0E131D", stroke: th.request, "stroke-opacity": 0.5, "stroke-width": 1.3 }, g);
      mk("rect", { x: -w / 2 - 1, y: -19, width: 3, height: 38, fill: "#0E131D" }, g);
      glyph(g, "spark", -w / 2 + 40, -h / 2 + 40, th.request);
      txt(g, Rs.title, -w / 2 + 66, -h / 2 + 40, { size: 15, mono: true, fill: th.request, anchor: "start", ls: "0.16em" });
      const items = [];
      Rs.lines.forEach(([c, v], i) => {
        const lg = mk("g", {}, g);
        const ly = -h / 2 + 108 + i * 50;
        txt(lg, c, -w / 2 + 44, ly, { size: 26, weight: 600, anchor: "start" });
        txt(lg, v, -w / 2 + 230, ly, { size: 24, mono: true, fill: th.data, anchor: "start" });
        hidden(lg, { x: -10 });
        items.push(lg);
      });
      const block = (title, body, y0, color) => {
        const bg = mk("g", {}, g);
        txt(bg, title, -w / 2 + 44, y0, { size: 12, mono: true, fill: color, anchor: "start", ls: "0.22em" });
        txt(bg, body, -w / 2 + 44, y0 + 34, { size: 21, anchor: "start" });
        hidden(bg, { x: -10 });
        items.push(bg);
      };
      block(Rs.contextTitle, Rs.context, -h / 2 + 238, th.c1);
      block(Rs.actionTitle, Rs.action, -h / 2 + 330, th.mcp);
      mk("line", { x1: -w / 2 + 30, y1: h / 2 - 82, x2: w / 2 - 30, y2: h / 2 - 82, stroke: th.line }, g);
      const tW = Rs.trace.map((s) => measure(s, { size: 12, mono: true }) + 54);
      const tGap = 12;
      let tx = -(tW.reduce((a, b) => a + b, 0) + tGap * (tW.length - 1)) / 2;
      const trace = Rs.trace.map((s, i) => {
        const color = i === 3 ? th.positive : i === 0 ? th.data : i === 1 ? th.positive : th.mcp;
        const p = pill(g, s, tx, h / 2 - 42, color, { size: 12, anchor: "start", h: 32, glyph: i === 0 ? "stack" : i === 1 ? "check" : i === 2 ? "key" : "lock" });
        tx += tW[i] + tGap;
        hidden(p.g, { y: 8 });
        return p;
      });
      hidden(g, { y: 16 });
      return { g, items, trace };
    })();
    to(P8.root, { opacity: 1 }, S8, S(0.5));
    show(u8.g, S8 + S(0.3), 0.7);
    show(ans.g, S8 + S(0.8), 0.9);
    ans.items.forEach((it, i) => show(it, S8 + S(1.5 + i * 0.45), 0.5));
    const tTrace = S8 + S(1.5 + ans.items.length * 0.45 + 0.4);
    ans.trace.forEach((p, i) => show(p.g, tTrace + S(i * 0.35), 0.5));
    lit({ glow: u8.glow }, tTrace, 1);
    t = caption(L.cap.s8, tTrace + S(1.2), S(4.0));
    eyebrow("result", S8, t);
    hide(P8.root, t - S(0.6), 0.6);

    // ═════════════════════════════════════════════════════════════════════════
    //  Scene 9 — summary: four pillars
    // ═════════════════════════════════════════════════════════════════════════
    const S9 = t;
    const F = L.final;
    const P9 = world();
    const title = txt(P9.top, F.title, 960, 250, { size: 44, weight: 700, ls: "0.12em" });
    const rule = mk("line", { x1: 860, y1: 300, x2: 1060, y2: 300, stroke: th.mcp, "stroke-width": 2 }, P9.top);
    const subtitle = txt(P9.top, F.subtitle, 960, 340, { size: 22, fill: th.muted });
    hidden(title, { y: 12 });
    hidden(rule, { scaleX: 0 });
    hidden(subtitle, { y: 10 });
    const pColors = [th.positive, th.data, th.mcp, th.perimeter];
    const pillars = F.pillars.map((p, i) => {
      const x = 960 + (i - 1.5) * 400;
      const n = card(P9.nodes, { x, y: 590, w: 360, h: 250, r: 20, color: pColors[i] });
      glyph(n.content, p.glyph, 0, -62, pColors[i], 2.2);
      txt(n.content, p.label, 0, 6, { size: 20, weight: 700, ls: "0.16em" });
      wrap(p.text, 300, { size: 18 }).forEach((l, j) => txt(n.content, l, 0, 52 + j * 26, { size: 18, fill: th.muted }));
      hidden(n.g, { y: 20 });
      return n;
    });
    to(P9.root, { opacity: 1 }, S9, S(0.4));
    pillars.forEach((n, i) => { show(n.g, S9 + S(0.5 + i * 0.4), 0.8); lit(n, S9 + S(0.8 + i * 0.4), 0.6); });
    const tTitle = S9 + S(2.6);
    show(title, tTitle, 1.0);
    to(rule, { opacity: 1, scaleX: 1 }, tTitle + S(0.3), S(0.9), "power3.out");
    show(subtitle, tTitle + S(0.7), 1.0);
    t = tTitle + S(7.0);
    eyebrow("final", S9, t);

    // ── Ambient: keep timeline length = t ───────────────────────────────────
    const amb = { v: 0 };
    tl.fromTo(amb, { v: 0 }, { v: 1, duration: t, ease: "none", immediateRender: false }, 0);
    tl.seek(0, false);

    return {
      timeline: tl,
      duration: tl.duration(),
      scenes: sceneMarks,
      svg,
      seek: (time) => tl.seek(time, false),
    };
  }

  window.TrustedData = { mount };
})();
