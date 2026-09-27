/*
 * MCP Explainer — animation engine
 * --------------------------------
 * MCPExplainer.mount(container, config) builds a 1920×1080 SVG stage and a
 * single paused GSAP timeline from the config (see config.js).
 *
 * Design rules that keep the timeline scrub-safe (seek anywhere, any order):
 *  - Every element is created at build time; the timeline only animates.
 *  - Persistent state changes go through `to()`, which records the previous
 *    value so each tween is an explicit fromTo.
 *  - Ephemeral effects (comets, pulses, captions) go through `fx()`, whose
 *    render(v) hides the effect outside 0 < v < 1.
 *  - Ambient motion (ring rotation, breathing glows) is a function of time.
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
  const rad = (deg) => (deg * Math.PI) / 180;

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function scaleTimings(timing, k) {
    const out = {};
    for (const s in timing) {
      out[s] = {};
      for (const key in timing[s]) out[s][key] = timing[s][key] * k;
    }
    return out;
  }

  function mount(container, cfg) {
    const th = cfg.theme;
    const k = 1 / (cfg.speed || 1);
    const TM = scaleTimings(cfg.timing, k);
    const S = (v) => v * k; // scale ad-hoc micro-timings too
    const ex = cfg.example;

    // ── SVG scaffold ────────────────────────────────────────────────────────
    const svg = mk("svg", {
      viewBox: `0 0 ${W} ${H}`,
      preserveAspectRatio: "xMidYMid meet",
      class: "mcpx-stage",
      role: "img",
      "aria-label": cfg.title,
    });
    container.appendChild(svg);
    svg.style.fontFamily = th.font;

    const defs = mk("defs", {}, svg);

    const bgGrad = mk("radialGradient", { id: "mcpx-bg", cx: "50%", cy: "45%", r: "75%" }, defs);
    mk("stop", { offset: "0%", "stop-color": th.bgGlow }, bgGrad);
    mk("stop", { offset: "100%", "stop-color": th.bg }, bgGrad);

    const vig = mk("radialGradient", { id: "mcpx-vig", cx: "50%", cy: "50%", r: "70%" }, defs);
    mk("stop", { offset: "60%", "stop-color": "#000", "stop-opacity": 0 }, vig);
    mk("stop", { offset: "100%", "stop-color": "#000", "stop-opacity": 0.55 }, vig);

    const dots = mk("pattern", { id: "mcpx-dots", width: 36, height: 36, patternUnits: "userSpaceOnUse" }, defs);
    mk("circle", { cx: 18, cy: 18, r: 1.1, fill: "#ffffff", "fill-opacity": 0.07 }, dots);

    const cardFill = mk("linearGradient", { id: "mcpx-card", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    mk("stop", { offset: "0%", "stop-color": "#111723" }, cardFill);
    mk("stop", { offset: "100%", "stop-color": "#0A0E15" }, cardFill);

    const mcpFill = mk("linearGradient", { id: "mcpx-mcp", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    mk("stop", { offset: "0%", "stop-color": th.mcp, "stop-opacity": 0.05 }, mcpFill);
    mk("stop", { offset: "50%", "stop-color": th.mcp, "stop-opacity": 0.16 }, mcpFill);
    mk("stop", { offset: "100%", "stop-color": th.mcp, "stop-opacity": 0.05 }, mcpFill);

    const mcpFillH = mk("linearGradient", { id: "mcpx-mcp-h", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
    mk("stop", { offset: "0%", "stop-color": th.mcp, "stop-opacity": 0.04 }, mcpFillH);
    mk("stop", { offset: "50%", "stop-color": th.mcp, "stop-opacity": 0.16 }, mcpFillH);
    mk("stop", { offset: "100%", "stop-color": th.mcp, "stop-opacity": 0.04 }, mcpFillH);

    const halos = {};
    function halo(color) {
      if (halos[color]) return halos[color];
      const id = "mcpx-halo-" + Object.keys(halos).length;
      const g = mk("radialGradient", { id }, defs);
      mk("stop", { offset: "0%", "stop-color": color, "stop-opacity": 0.32 }, g);
      mk("stop", { offset: "45%", "stop-color": color, "stop-opacity": 0.1 }, g);
      mk("stop", { offset: "100%", "stop-color": color, "stop-opacity": 0 }, g);
      return (halos[color] = `url(#${id})`);
    }

    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#mcpx-bg)" }, svg);
    const camG = mk("g", {}, svg);
    mk("rect", { x: -4000, y: -3000, width: 10000, height: 7000, fill: "url(#mcpx-dots)" }, camG);
    const worldA = mk("g", {}, camG);
    const screenG = mk("g", {}, svg);
    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#mcpx-vig)", "pointer-events": "none" }, svg);

    const A = {
      rails: mk("g", {}, worldA),
      ring: mk("g", {}, worldA),
      nodes: mk("g", {}, worldA),
      fx: mk("g", {}, worldA),
      top: mk("g", {}, worldA),
    };
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
      const words = s.split(" ");
      const lines = [];
      let line = "";
      for (const w of words) {
        const tryLine = line ? line + " " + w : w;
        if (line && measure(tryLine, o) > maxW) { lines.push(line); line = w; }
        else line = tryLine;
      }
      if (line) lines.push(line);
      return lines;
    }
    const fillTokens = (s) => {
      const a = cfg.multiAgent.apps.length, n = cfg.multiAgent.systems.length;
      return String(s).replace(/\{A\}/g, a).replace(/\{S\}/g, n)
        .replace(/\{AxS\}/g, a * n).replace(/\{A\+S\}/g, a + n);
    };

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
    function to(el, props, at, dur = 0.6, ease = "power2.inOut", onUpdate) {
      const s = state.get(el) || {};
      const from = {};
      for (const key in props) from[key] = key in s ? s[key] : DEF[key];
      const vars = { ...props, duration: Math.max(dur, 0.001), ease, immediateRender: false };
      if (onUpdate) vars.onUpdate = onUpdate;
      tl.fromTo(el, from, vars, at);
      state.set(el, { ...s, ...props });
    }
    function fx(at, dur, render, ease = "none") {
      const p = { v: 0 };
      render(0);
      tl.fromTo(p, { v: 0 }, {
        v: 1, duration: Math.max(dur, 0.001), ease, immediateRender: false,
        onUpdate: () => render(p.v),
      }, at);
    }
    // fade in → hold → fade out window; apply(alpha 0..1, local progress)
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
      const L = path.getTotalLength();
      path.setAttribute("stroke-dasharray", `${L} ${L + 2}`);
      path.setAttribute("stroke-dashoffset", L);
      tl.fromTo(path, { attr: { "stroke-dashoffset": L } }, {
        attr: { "stroke-dashoffset": 0 }, duration: dur, ease, immediateRender: false,
      }, at);
    }

    // ── Camera ──────────────────────────────────────────────────────────────
    const cam = { x: W / 2, y: H / 2, s: 1 };
    state.set(cam, { x: W / 2, y: H / 2, s: 1 });
    const applyCam = () => camG.setAttribute(
      "transform", `translate(${W / 2} ${H / 2}) scale(${cam.s}) translate(${-cam.x} ${-cam.y})`);
    function camera(x, y, s, at, dur, ease = "power2.inOut") {
      to(cam, { x, y, s }, at, dur, ease, applyCam);
    }

    // ── Visual primitives ───────────────────────────────────────────────────
    function glyph(parent, type, x, y, color) {
      const g = mk("g", { transform: `translate(${x} ${y})`, fill: "none", stroke: color, "stroke-width": 1.6, "stroke-linejoin": "round" }, parent);
      if (type === "hex") {
        const pts = [];
        for (let i = 0; i < 6; i++) pts.push(`${9 * Math.cos(rad(60 * i - 30))},${9 * Math.sin(rad(60 * i - 30))}`);
        mk("polygon", { points: pts.join(" ") }, g);
        mk("circle", { r: 2.4, fill: color, stroke: "none" }, g);
      } else if (type === "stack") {
        [-6, 0, 6].forEach((dy) => mk("rect", { x: -9, y: dy - 2, width: 18, height: 4, rx: 2 }, g));
      } else if (type === "grid") {
        [[-8, -8], [1, -8], [-8, 1], [1, 1]].forEach(([a, b]) => mk("rect", { x: a, y: b, width: 7, height: 7, rx: 1.5 }, g));
      } else if (type === "plug") {
        mk("rect", { x: -7, y: -3, width: 14, height: 10, rx: 3 }, g);
        mk("path", { d: "M-3,-3 V-9 M3,-3 V-9 M0,7 V11" }, g);
      } else if (type === "spark") {
        mk("path", { d: "M0,-11 C1.2,-3 3,-1.2 11,0 C3,1.2 1.2,3 0,11 C-1.2,3 -3,1.2 -11,0 C-3,-1.2 -1.2,-3 0,-11 Z", fill: color, "fill-opacity": 0.9, stroke: "none" }, g);
      } else {
        mk("circle", { r: 4, fill: color, stroke: "none" }, g);
      }
      return g;
    }

    // Card node: outer (static position) > g (animated) > glow + base + content
    function card(parent, o) {
      const { x, y, w, h } = o;
      const r = o.r != null ? o.r : 14;
      const color = o.color || th.request;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("rect", { x: -w / 2 - 70, y: -h / 2 - 70, width: w + 140, height: h + 140, rx: r + 60, fill: halo(color) }, glow);
      mk("rect", { x: -w / 2 - 4, y: -h / 2 - 4, width: w + 8, height: h + 8, rx: r + 4, fill: "none", stroke: color, "stroke-opacity": 0.18, "stroke-width": 8 }, glow);
      const base = mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "url(#mcpx-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "none", stroke: color, "stroke-width": 1.4 }, glow);
      const content = mk("g", {}, g);
      const node = { outer, g, glow, base, content, x, y, w, h, color,
        L: { x: x - w / 2, y }, R: { x: x + w / 2, y }, T: { x, y: y - h / 2 }, B: { x, y: y + h / 2 } };

      if (o.align === "left") {
        const lx = -w / 2 + 22;
        if (o.glyph) glyph(content, o.glyph, lx + 8, 0, color);
        const tx = lx + (o.glyph ? 30 : 0);
        node.label = txt(content, o.label, tx, o.sub ? -11 : 0, { size: o.size || 15, weight: 600, ls: "0.12em", anchor: "start" });
        if (o.sub) node.sub = txt(content, o.sub, tx, 13, { size: 12, mono: true, fill: th.muted, anchor: "start" });
      } else if (o.label) {
        const size = o.size || 15;
        const lw = measure(o.label, { size, weight: 600, ls: o.ls || "0.14em" });
        const gw = o.glyph ? 30 : 0;
        const start = -(lw + gw) / 2;
        if (o.glyph) glyph(content, o.glyph, start + 10, o.sub ? -11 : 0, color);
        node.label = txt(content, o.label, start + gw, o.sub ? -11 : 0, { size, weight: 600, ls: o.ls || "0.14em", anchor: "start" });
        if (o.sub) node.sub = txt(content, o.sub, 0, 14, { size: 12, mono: true, fill: th.muted });
      }
      return node;
    }

    // Glowing comet travelling along a path. Returns path length.
    function comet(d, color, at, dur, o = {}) {
      const g = mk("g", { opacity: 0 }, o.layer || A.fx);
      const sc = o.scale || 1;
      const paths = [[16, 0.06], [7, 0.2], [2.4, 1]].map(([w, a]) =>
        mk("path", { d, fill: "none", stroke: color, "stroke-width": w * sc, "stroke-opacity": a, "stroke-linecap": "round" }, g));
      const head = mk("g", {}, g);
      mk("circle", { r: 20 * sc, fill: color, opacity: 0.1 }, head);
      mk("circle", { r: 8 * sc, fill: color, opacity: 0.4 }, head);
      mk("circle", { r: 3.4 * sc, fill: "#fff" }, head);
      const L = paths[0].getTotalLength();
      const tail = Math.min(o.tail || 170, L * 0.7);
      paths.forEach((p) => p.setAttribute("stroke-dasharray", `${tail} ${L + 3 * tail}`));
      const rev = !!o.reverse;
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { g.setAttribute("opacity", 0); return; }
        g.setAttribute("opacity", 1);
        const s = v * (L + tail);
        const off = rev ? s - L : tail - s;
        paths.forEach((p) => p.setAttribute("stroke-dashoffset", off));
        const hs = Math.min(s, L);
        const pt = paths[0].getPointAtLength(rev ? L - hs : hs);
        head.setAttribute("transform", `translate(${pt.x} ${pt.y})`);
        head.setAttribute("opacity", s <= L ? 1 : 0);
      }, o.ease || "power1.inOut");
      return L;
    }

    // Small structured data chip carried along a path (default: end → start)
    function dataChip(parent, label, color) {
      const g = mk("g", { opacity: 0 }, parent);
      const w = measure(label, { size: 13, mono: true }) + 30;
      mk("rect", { x: -w / 2 - 10, y: -24, width: w + 20, height: 48, rx: 22, fill: halo(color) }, g);
      mk("rect", { x: -w / 2, y: -15, width: w, height: 30, rx: 9, fill: "#15120A", stroke: color, "stroke-width": 1.2 }, g);
      txt(g, label, 0, 0, { size: 13, mono: true, fill: color, weight: 500 });
      return g;
    }
    function carry(chip, d, at, dur, o = {}) {
      const p = mk("path", { d }, measureG);
      const L = p.getTotalLength();
      const fwd = !!o.forward;
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { chip.setAttribute("opacity", 0); return; }
        const e = easeInOut(v);
        const pt = p.getPointAtLength(fwd ? e * L : (1 - e) * L);
        const sc = v < 0.12 ? easeOut(v / 0.12) : v > 0.88 ? Math.max(0.05, (1 - v) / 0.12) : 1;
        chip.setAttribute("opacity", v > 0.88 ? (1 - v) / 0.12 : 1);
        chip.setAttribute("transform", `translate(${pt.x} ${pt.y}) scale(${sc})`);
      });
    }

    function pulse(parent, x, y, shape, color, at, dur = 0.9) {
      const g = mk("g", { transform: `translate(${x} ${y})`, opacity: 0 }, parent);
      const inner = mk("g", {}, g);
      if (shape.r != null) mk("circle", { r: shape.r, fill: "none", stroke: color, "stroke-width": 2 }, inner);
      else mk("rect", { x: -shape.w / 2, y: -shape.h / 2, width: shape.w, height: shape.h, rx: shape.rx || 14, fill: "none", stroke: color, "stroke-width": 2 }, inner);
      fx(at, S(dur), (v) => {
        if (v <= 0 || v >= 1) { g.setAttribute("opacity", 0); return; }
        const e = easeOut(v);
        g.setAttribute("opacity", 0.85 * (1 - v));
        const sx = shape.r != null ? 1 + e * 0.6 : 1 + (e * 36) / shape.w;
        const sy = shape.r != null ? 1 + e * 0.6 : 1 + (e * 36) / shape.h;
        inner.setAttribute("transform", `scale(${sx} ${sy})`);
      });
    }
    const pulseNode = (n, color, at, parent = A.fx) =>
      pulse(parent, n.x, n.y, { w: n.w, h: n.h, rx: n.r || 16 }, color || n.color, at);

    // Screen-space caption (one or two lines + optional sub line)
    const capLayer = mk("g", {}, screenG);
    function caption(lines, at, hold, o = {}) {
      lines = Array.isArray(lines) ? lines : [lines];
      const size = o.size || 30;
      const lh = size * 1.3;
      const y0 = (o.y || 975) - ((lines.length - 1) * lh) / 2 - (o.sub ? 18 : 0);
      const g = mk("g", { opacity: 0 }, capLayer);
      lines.forEach((l, i) => txt(g, l, W / 2, y0 + i * lh, { size, weight: o.weight || 500, fill: o.fill || th.text, ls: "-0.005em" }));
      if (o.sub) txt(g, fillTokens(o.sub), W / 2, y0 + (lines.length - 1) * lh + size * 0.6 + 26, { size: 17, mono: true, fill: o.subFill || th.muted });
      const fi = S(0.7), fo = S(0.6);
      win(at, fi, hold, fo, (a) => {
        g.setAttribute("opacity", a);
        g.setAttribute("transform", `translate(0 ${(1 - a) * 12})`);
      });
      return at + fi + hold + fo;
    }

    // Eyebrow (scene label, top-left)
    const eyebrowG = mk("g", {}, screenG);
    const sceneMarks = [];
    function eyebrow(index, at, until) {
      const sc = cfg.scenes[index];
      sceneMarks.push({ id: sc.id, label: sc.label, time: at });
      tl.addLabel(sc.id, at);
      if (until == null) return;
      const g = mk("g", { opacity: 0 }, eyebrowG);
      mk("line", { x1: 72, y1: 72, x2: 96, y2: 72, stroke: th.mcp, "stroke-width": 2 }, g);
      txt(g, String(index + 1).padStart(2, "0"), 110, 72, { size: 13, mono: true, fill: th.text, anchor: "start" });
      txt(g, sc.label.toUpperCase(), 142, 72, { size: 13, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
      win(at + S(0.2), S(0.6), Math.max(0, until - at - S(1.4)), S(0.6), (a) => g.setAttribute("opacity", a));
    }

    // ═════════════════════════════════════════════════════════════════════════
    //  WORLD A — the Cash Equity agent architecture (scenes 1–6)
    // ═════════════════════════════════════════════════════════════════════════
    const C = { x: 720, y: 540 };
    const RING_R = 250;
    const CAP_R = 410;
    const CAP_ANGLES = [-135, -45, 45, 135];
    const BAR = { x: 1290, y1: 190, y2: 890, w: 64 };
    const SYS_X = 1640, SYS_W = 300, SYS_H = 84;
    const nSys = cfg.systems.length;
    const sysY = (i) => 540 + (i - (nSys - 1) / 2) * Math.min(120, 660 / Math.max(1, nSys - 1));

    // User
    const user = (() => {
      const x = 150, y = 540;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, A.nodes);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("circle", { r: 120, fill: halo(th.request) }, glow);
      mk("circle", { r: 49, fill: "none", stroke: th.request, "stroke-opacity": 0.25, "stroke-width": 8 }, glow);
      mk("circle", { r: 44, fill: "url(#mcpx-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("circle", { r: 44, fill: "none", stroke: th.request, "stroke-width": 1.4 }, glow);
      const icon = mk("g", { fill: "none", stroke: th.text, "stroke-width": 1.8, "stroke-linecap": "round" }, g);
      mk("circle", { cx: 0, cy: -9, r: 9 }, icon);
      mk("path", { d: "M-17,19 C-17,5 17,5 17,19" }, icon);
      txt(g, cfg.user.label, 0, 82, { size: 14, weight: 600, ls: "0.2em" });
      txt(g, cfg.user.sublabel, 0, 106, { size: 12, mono: true, fill: th.muted });
      return { outer, g, glow, x, y, w: 88, h: 88, r: 44, color: th.request, R: { x: x + 46, y } };
    })();

    // Orchestrator ring (drawn behind the agent)
    const ring = (() => {
      const g = mk("g", {}, A.ring);
      const fill = mk("circle", { cx: C.x, cy: C.y, r: RING_R, fill: halo(th.orchestrator), opacity: 0 }, g);
      const dashed = mk("circle", { cx: C.x, cy: C.y, r: RING_R + 14, fill: "none", stroke: th.orchestrator, "stroke-opacity": 0.35, "stroke-width": 1, "stroke-dasharray": "2 10" }, g);
      const solid = mk("path", {
        d: `M ${C.x} ${C.y - RING_R} a ${RING_R} ${RING_R} 0 1 1 -0.01 0`,
        fill: "none", stroke: th.orchestrator, "stroke-opacity": 0.75, "stroke-width": 1.5,
      }, g);
      const arcId = "mcpx-ring-arc";
      const lr = RING_R - 30;
      mk("path", { id: arcId, d: `M ${C.x - lr} ${C.y} A ${lr} ${lr} 0 0 1 ${C.x + lr} ${C.y}`, fill: "none" }, defs);
      const label = mk("text", { "font-family": th.mono, "font-size": 12.5, fill: th.orchestrator, "letter-spacing": "0.26em", "font-weight": 500, opacity: 0 }, g);
      const tp = mk("textPath", { href: `#${arcId}`, startOffset: "50%", "text-anchor": "middle" }, label);
      tp.textContent = cfg.orchestrator.label;
      init(dashed, { opacity: 0 });
      return { g, fill, dashed, solid, label };
    })();
    const ringPt = (deg, r = RING_R) => ({ x: C.x + r * Math.cos(rad(deg)), y: C.y + r * Math.sin(rad(deg)) });

    // Capabilities + spokes
    const caps = {};
    cfg.capabilities.forEach((c, i) => {
      const ang = CAP_ANGLES[i % 4];
      const p = ringPt(ang, CAP_R);
      const n = card(A.nodes, { x: p.x, y: p.y, w: 190, h: 60, r: 14, label: c.label, glyph: c.glyph, color: th.orchestrator });
      const inner = { x: p.x - Math.sign(Math.cos(rad(ang))) * 95, y: p.y - Math.sign(Math.sin(rad(ang))) * 30 };
      const r0 = ringPt(ang, RING_R + 2);
      n.spokeD = `M ${r0.x} ${r0.y} L ${inner.x} ${inner.y}`;
      n.spoke = mk("path", { d: n.spokeD, stroke: th.orchestrator, "stroke-opacity": 0.4, "stroke-width": 1.2, fill: "none" }, A.rails);
      n.angle = ang;
      n.side = Math.cos(rad(ang)) < 0 ? -1 : 1;
      init(n.g, { opacity: 0, scale: 0.9, transformOrigin: "50% 50%" });
      init(n.spoke, { opacity: 0 });
      caps[c.id] = n;
    });

    // Agent (core)
    const agentHalo = mk("g", { opacity: 0 }, A.nodes);
    const agentHaloC = mk("circle", { cx: C.x, cy: C.y, r: 230, fill: halo(th.request) }, agentHalo);
    const agent = card(A.nodes, { x: C.x, y: C.y, w: 320, h: 100, r: 26, label: cfg.agent.label, glyph: "spark", color: th.request, size: 18, ls: "0.16em" });
    init(agent.g, { opacity: 0, scale: 0.92, transformOrigin: "50% 50%" });
    init(agentHalo, { opacity: 0 });

    // Request rail user → agent
    const railUA_D = `M ${user.x + 50} ${C.y} L ${agent.L.x - 4} ${C.y}`;
    const railUA = mk("path", { d: railUA_D, stroke: th.request, "stroke-opacity": 0.35, "stroke-width": 1.4, fill: "none" }, A.rails);
    const railAU_D = `M ${agent.L.x - 4} ${C.y} L ${user.x + 50} ${C.y}`;

    // Prompt card
    const prompt = (() => {
      const cx = 420, cy = 392, w = 560;
      const o = { size: 23, weight: 500 };
      const lines = wrap(ex.prompt, w - 64, o);
      const h = 70 + lines.length * 34;
      const outer = mk("g", { transform: `translate(${cx} ${cy})` }, A.top);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 50, y: -h / 2 - 50, width: w + 100, height: h + 100, rx: 70, fill: halo(th.request), opacity: 0.5 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 18, fill: "url(#mcpx-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("path", { d: `M ${-w / 2 + 50} ${h / 2} l 14 16 l 8 -16`, fill: "#0A0E15", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("rect", { x: -w / 2 + 49, y: h / 2 - 2, width: 24, height: 4, fill: "#0A0E15" }, g);
      txt(g, ex.promptMeta, -w / 2 + 28, -h / 2 + 26, { size: 11.5, mono: true, fill: th.muted, anchor: "start", ls: "0.14em" });
      const lineEls = lines.map((l, i) => txt(g, "", -w / 2 + 28, -h / 2 + 60 + i * 34, { ...o, anchor: "start" }));
      const caret = mk("rect", { x: 0, y: -13, width: 2, height: 26, fill: th.request }, g);
      init(g, { opacity: 0, y: 12, scale: 1, transformOrigin: "50% 50%" });
      return { g, lines, lineEls, caret };
    })();

    // Understand → Plan → Act → Answer
    const loopRow = (() => {
      const g = mk("g", {}, A.top);
      const o = { size: 17, weight: 500 };
      const gap = 46;
      const widths = ex.loop.map((s) => measure(s, o));
      const total = widths.reduce((a, b) => a + b, 0) + gap * (ex.loop.length - 1);
      let x = C.x - total / 2;
      const y = 652;
      const items = ex.loop.map((s, i) => {
        const dim = txt(g, s, x, y, { ...o, anchor: "start", fill: th.faint });
        const lit = txt(g, s, x, y, { ...o, anchor: "start", fill: th.text });
        const bar = mk("rect", { x, y: y + 18, width: widths[i], height: 2, rx: 1, fill: th.request }, g);
        init(lit, { opacity: 0 });
        init(bar, { opacity: 0 });
        if (i < ex.loop.length - 1) {
          const ax = x + widths[i] + gap / 2;
          mk("path", { d: `M ${ax - 7} ${y} L ${ax + 5} ${y} M ${ax + 1} ${y - 4} L ${ax + 5} ${y} L ${ax + 1} ${y + 4}`, stroke: th.faint, "stroke-width": 1.4, fill: "none" }, g);
        }
        x += widths[i] + gap;
        return { dim, lit, bar };
      });
      init(g, { opacity: 0 });
      return { g, items };
    })();

    // Scene 3 — needs + reaching lines
    const needs = ex.needs.map((s, i) => {
      const y = 540 + (i - (ex.needs.length - 1) / 2) * 120;
      const x0 = 1130;
      const o = { size: 17, weight: 500 };
      const w = measure(s, o) + 44;
      const link = mk("path", { d: `M ${agent.R.x + 4} ${C.y} C ${agent.R.x + 130} ${C.y}, ${x0 - 130} ${y}, ${x0} ${y}`, stroke: th.request, "stroke-opacity": 0.5, "stroke-width": 1.3, fill: "none" }, A.rails);
      const pg = mk("g", {}, A.top);
      mk("rect", { x: x0, y: y - 22, width: w, height: 44, rx: 22, fill: "url(#mcpx-card)", stroke: th.request, "stroke-opacity": 0.55, "stroke-width": 1.2 }, pg);
      txt(pg, s, x0 + 22, y, { ...o, anchor: "start", italic: true });
      const reach = mk("path", { d: `M ${x0 + w + 6} ${y} L 1610 ${y}`, stroke: th.muted, "stroke-opacity": 0.55, "stroke-width": 1.3, fill: "none", "stroke-dasharray": "1 0" }, A.rails);
      const sock = mk("g", { transform: `translate(1690 ${y})` }, A.top);
      mk("rect", { x: -40, y: -26, width: 80, height: 52, rx: 12, fill: "none", stroke: th.warn, "stroke-opacity": 0.6, "stroke-width": 1.2, "stroke-dasharray": "4 6" }, sock);
      txt(sock, "?", 0, 1, { size: 20, weight: 500, fill: th.warn });
      init(pg, { opacity: 0, x: -14 });
      init(sock, { opacity: 0 });
      init(link, { opacity: 1 });
      init(reach, { opacity: 1 });
      return { link, pg, reach, sock, y };
    });

    // MCP bar
    const mcp = (() => {
      const g = mk("g", {}, A.nodes);
      const body = mk("g", {}, g);
      const h = BAR.y2 - BAR.y1;
      mk("rect", { x: BAR.x - 110, y: BAR.y1 - 60, width: 220, height: h + 120, rx: 110, fill: halo(th.mcp), opacity: 0.7 }, body);
      mk("rect", { x: BAR.x - BAR.w / 2, y: BAR.y1, width: BAR.w, height: h, rx: BAR.w / 2, fill: "url(#mcpx-mcp)", stroke: th.mcp, "stroke-opacity": 0.7, "stroke-width": 1.4 }, body);
      const bus = mk("line", { x1: BAR.x, y1: BAR.y1 + 26, x2: BAR.x, y2: BAR.y2 - 26, stroke: th.mcp, "stroke-opacity": 0.55, "stroke-width": 1.5, "stroke-dasharray": "3 9" }, body);
      init(body, { opacity: 0, scaleY: 0.02, scaleX: 0.3, transformOrigin: "50% 50%" });
      const title = txt(g, cfg.mcp.title, BAR.x, BAR.y1 - 78, { size: 50, weight: 700, ls: "0.22em", fill: th.text });
      const sub = txt(g, cfg.mcp.subtitle, BAR.x, BAR.y1 - 36, { size: 13, mono: true, ls: "0.3em", fill: th.mcp });
      init(title, { opacity: 0, y: 10 });
      init(sub, { opacity: 0 });
      const ports = [];
      for (let i = 0; i < nSys; i++) {
        const y = sysY(i);
        const pr = [BAR.x - BAR.w / 2, BAR.x + BAR.w / 2].map((px) => {
          const pg = mk("g", { transform: `translate(${px} ${y})` }, g);
          const inner = mk("g", {}, pg);
          mk("rect", { x: -7, y: -7, width: 14, height: 14, rx: 3.5, fill: th.bg, stroke: th.mcp, "stroke-width": 1.4 }, inner);
          const lit = mk("rect", { x: -3.5, y: -3.5, width: 7, height: 7, rx: 1.5, fill: th.mcp }, inner);
          init(inner, { opacity: 0, scale: 0.4, transformOrigin: "50% 50%" });
          init(lit, { opacity: 0 });
          return { g: inner, lit, x: px, y };
        });
        ports.push({ left: pr[0], right: pr[1] });
      }
      // verbs
      const vo = { size: 12.5, mono: true, ls: "0.24em" };
      const verbs = cfg.mcp.verbs;
      const gap = 36;
      const ws = verbs.map((v) => measure(v, vo));
      const tot = ws.reduce((a, b) => a + b, 0) + gap * (verbs.length - 1);
      let vx = BAR.x - tot / 2;
      const verbEls = verbs.map((v, i) => {
        const dim = txt(g, v, vx, BAR.y2 + 46, { ...vo, anchor: "start", fill: th.faint });
        const lit = txt(g, v, vx, BAR.y2 + 46, { ...vo, anchor: "start", fill: th.mcp });
        if (i < verbs.length - 1) mk("circle", { cx: vx + ws[i] + gap / 2, cy: BAR.y2 + 46, r: 1.8, fill: th.faint }, g);
        init(lit, { opacity: 0 });
        vx += ws[i] + gap;
        return { dim, lit };
      });
      const verbsG = verbEls; // individual
      const verbWrap = mk("g", {}, g);
      verbEls.forEach((v) => { verbWrap.appendChild(v.dim); verbWrap.appendChild(v.lit); });
      Array.from(g.querySelectorAll("circle")).forEach((c) => { if (c.getAttribute("cy") == String(BAR.y2 + 46)) verbWrap.appendChild(c); });
      init(verbWrap, { opacity: 0 });
      return { g, body, bus, title, sub, ports, verbs: verbsG, verbWrap };
    })();

    // Trunk agent → MCP and TOOLS → MCP
    const trunk = mk("path", { d: `M ${agent.R.x + 4} ${C.y} L ${BAR.x - BAR.w / 2 - 2} ${C.y}`, stroke: th.mcp, "stroke-opacity": 0.45, "stroke-width": 1.4, fill: "none" }, A.rails);
    const toolsCap = caps.tools || Object.values(caps)[2];
    const toolsLink = mk("path", {
      d: `M ${toolsCap.R.x + 2} ${toolsCap.y} C ${toolsCap.R.x + 80} ${toolsCap.y}, ${BAR.x - 110} ${toolsCap.y}, ${BAR.x - BAR.w / 2 - 2} ${toolsCap.y}`,
      stroke: th.mcp, "stroke-opacity": 0.45, "stroke-width": 1.3, fill: "none", "stroke-dasharray": "4 6",
    }, A.rails);
    init(trunk, { opacity: 1 });
    init(toolsLink, { opacity: 0 });

    // Systems
    const systems = {};
    cfg.systems.forEach((s, i) => {
      const y = sysY(i);
      const n = card(A.nodes, { x: SYS_X, y, w: SYS_W, h: SYS_H, r: 16, label: s.label, sub: s.sub, glyph: "dot", color: th.mcp, align: "left" });
      n.conn = mk("path", { d: `M ${BAR.x + BAR.w / 2 + 8} ${y} L ${SYS_X - SYS_W / 2 - 2} ${y}`, stroke: th.mcp, "stroke-opacity": 0.45, "stroke-width": 1.3, fill: "none" }, A.rails);
      n.callD = `M ${agent.R.x + 4} ${C.y} C ${agent.R.x + 190} ${C.y}, ${BAR.x - 210} ${y}, ${BAR.x - BAR.w / 2} ${y} L ${SYS_X - SYS_W / 2 - 2} ${y}`;
      n.rail = mk("path", { d: n.callD, stroke: th.mcp, "stroke-opacity": 0.3, "stroke-width": 1.2, fill: "none" }, A.rails);
      n.idx = i;
      init(n.g, { opacity: 0, x: 20 });
      init(n.content, { opacity: 0 });
      init(n.rail, { opacity: 0 });
      systems[s.id] = n;
    });

    // Plan list (inside the ring, below the agent)
    const plan = ex.plan.map((s, i) => {
      const y = 636 + i * 36;
      const g = mk("g", {}, A.top);
      const num = txt(g, String(i + 1), 604, y, { size: 13, mono: true, fill: th.request });
      mk("circle", { cx: 604, cy: y, r: 11, fill: "none", stroke: th.request, "stroke-opacity": 0.5 }, g);
      const dimT = txt(g, s, 628, y, { size: 15.5, anchor: "start", fill: th.muted });
      const litT = txt(g, s, 628, y, { size: 15.5, anchor: "start", fill: th.text });
      const tw = measure(s, { size: 15.5 });
      const check = mk("path", { d: `M ${640 + tw} ${y} l 5 5 l 9 -10`, stroke: th.positive, "stroke-width": 2, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
      init(g, { opacity: 0, x: -10 });
      init(litT, { opacity: 0 });
      init(check, { opacity: 0 });
      return { g, dimT, litT, check, num };
    });

    // Result card
    const result = (() => {
      const R = ex.result;
      const w = 480;
      const outer = mk("g", { transform: `translate(${C.x} ${C.y})` }, A.top);
      const mover = mk("g", {}, outer);
      const g = mk("g", {}, mover);
      const rows = []; // [{el, y}]
      let y = 0;
      const addRow = (fn, hgt) => { const rg = mk("g", {}, g); fn(rg, y); rows.push(rg); y += hgt; };
      const lx = -w / 2 + 32;
      addRow((rg, yy) => {
        txt(rg, R.instrument, lx, yy + 22, { size: 30, weight: 700, anchor: "start", ls: "0.02em" });
        txt(rg, R.move, w / 2 - 32, yy + 22, { size: 30, weight: 700, anchor: "end", fill: th.positive });
        txt(rg, R.ticker, lx, yy + 56, { size: 12, mono: true, fill: th.muted, anchor: "start", ls: "0.12em" });
        mk("line", { x1: lx, y1: yy + 80, x2: w / 2 - 32, y2: yy + 80, stroke: th.line }, rg);
      }, 100);
      R.sections.forEach((sec) => {
        addRow((rg, yy) => {
          txt(rg, sec.title, lx, yy + 8, { size: 11.5, mono: true, fill: sec.accent ? th.mcp : th.muted, anchor: "start", ls: "0.22em" });
          sec.items.forEach((it, j) => {
            const iy = yy + 38 + j * 28;
            const t = typeof it === "string" ? { text: it } : it;
            mk("circle", { cx: lx + 4, cy: iy, r: 2.6, fill: sec.accent ? th.mcp : th.text }, rg);
            const te = txt(rg, t.text, lx + 18, iy, { size: 16.5, anchor: "start", fill: sec.accent ? th.text : th.text, weight: sec.accent ? 600 : 500 });
            if (t.note) txt(rg, "·  " + t.note, lx + 26 + te.getComputedTextLength(), iy, { size: 13, mono: true, fill: th.muted, anchor: "start" });
          });
        }, 38 + sec.items.length * 28 + 22);
      });
      addRow((rg, yy) => {
        mk("line", { x1: lx, y1: yy, x2: w / 2 - 32, y2: yy, stroke: th.line }, rg);
        txt(rg, R.sourcesLabel, lx, yy + 30, { size: 10.5, mono: true, fill: th.muted, anchor: "start", ls: "0.22em" });
        let px = lx + measure(R.sourcesLabel, { size: 10.5, mono: true, ls: "0.22em" }) + 16;
        R.sources.forEach((s) => {
          const pw = measure(s, { size: 10.5, mono: true }) + 18;
          mk("rect", { x: px, y: yy + 19, width: pw, height: 22, rx: 11, fill: "none", stroke: th.mcp, "stroke-opacity": 0.6 }, rg);
          txt(rg, s, px + pw / 2, yy + 30, { size: 10.5, mono: true, fill: th.mcp });
          px += pw + 8;
        });
      }, 56);
      const h = y + 44;
      const top = -h / 2 + 30;
      g.setAttribute("transform", `translate(0 ${top})`);
      const bg = mk("g", {}, mover);
      mover.insertBefore(bg, g);
      mk("rect", { x: -w / 2 - 90, y: -h / 2 - 90, width: w + 180, height: h + 180, rx: 120, fill: halo(th.request), opacity: 0.8 }, bg);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 22, fill: "#0B1018", stroke: th.request, "stroke-opacity": 0.5, "stroke-width": 1.3 }, bg);
      mk("rect", { x: -w / 2 + 1, y: -h / 2 + 1, width: w - 2, height: 3, rx: 1.5, fill: th.request, opacity: 0.6 }, bg);
      init(mover, { opacity: 0, scale: 0.6, x: 0, transformOrigin: "50% 50%" });
      rows.forEach((r) => init(r, { opacity: 0, y: 8 }));
      // row elements have translate attr; GSAP y composes with it (parsed)
      return { outer, mover, rows, w, h };
    })();

    // Orchestrator orbiter (ambient-driven)
    const orbiter = (() => {
      const g = mk("g", { opacity: 0 }, A.fx);
      const trail = mk("path", { fill: "none", stroke: th.orchestrator, "stroke-width": 3, "stroke-linecap": "round", "stroke-opacity": 0.7 }, g);
      const trail2 = mk("path", { fill: "none", stroke: th.orchestrator, "stroke-width": 10, "stroke-linecap": "round", "stroke-opacity": 0.12 }, g);
      const head = mk("g", {}, g);
      mk("circle", { r: 18, fill: th.orchestrator, opacity: 0.14 }, head);
      mk("circle", { r: 7, fill: th.orchestrator, opacity: 0.5 }, head);
      mk("circle", { r: 3.4, fill: "#fff" }, head);
      return { g, trail, trail2, head, keys: [], vis: [0, 0] };
    })();
    function orbitAngle(t) {
      const ks = orbiter.keys;
      if (!ks.length) return -90;
      let a = ks[0].a0;
      for (const kf of ks) {
        if (t < kf.t0) break;
        if (t >= kf.t1) { a = kf.a1; continue; }
        a = kf.a0 + (kf.a1 - kf.a0) * easeInOut((t - kf.t0) / (kf.t1 - kf.t0));
        break;
      }
      return a;
    }

    // ═════════════════════════════════════════════════════════════════════════
    //  WORLD B — many agents, one MCP layer (scene 7) — screen space
    // ═════════════════════════════════════════════════════════════════════════
    const B = (() => {
      const root = mk("g", {}, screenG);
      const rails = mk("g", {}, root), nodes = mk("g", {}, root), fxl = mk("g", {}, root);
      const M = cfg.multiAgent;
      const nA = M.apps.length, nS = M.systems.length;
      const appY = 230, barY = 536, sysYb = 810;
      const appW = Math.min(310, 1400 / nA - 40);
      const appX = (i) => 960 + (i - (nA - 1) / 2) * (appW + 50);
      const sysW = Math.min(220, 1500 / nS - 30);
      const sysXb = (i) => 960 + (i - (nS - 1) / 2) * (sysW + 32);
      const apps = M.apps.map((a, i) => {
        const n = card(nodes, { x: appX(i), y: appY, w: appW, h: 86, r: 18, label: a.label, glyph: "spark", color: th.request, size: 15 });
        init(n.g, { opacity: 0, y: -14 });
        n.id = a.id;
        return n;
      });
      const sys = M.systems.map((s, i) => {
        const n = card(nodes, { x: sysXb(i), y: sysYb, w: sysW, h: 78, r: 16, label: s, glyph: "dot", color: th.mcp, size: 13.5, ls: "0.12em" });
        init(n.g, { opacity: 0, y: 14 });
        return n;
      });
      const tangle = mk("g", {}, rails);
      const tangleLines = [];
      apps.forEach((a) => sys.forEach((s) => {
        const p = mk("path", { d: `M ${a.x} ${a.B.y + 2} C ${a.x} ${barY - 20}, ${s.x} ${barY + 20}, ${s.x} ${s.T.y - 2}`, stroke: th.warn, "stroke-opacity": 0.42, "stroke-width": 1.2, fill: "none" }, tangle);
        tangleLines.push(p);
      }));
      init(tangle, { opacity: 1 });
      const x1 = Math.min(appX(0) - appW / 2, sysXb(0) - sysW / 2) - 10;
      const x2 = Math.max(appX(nA - 1) + appW / 2, sysXb(nS - 1) + sysW / 2) + 10;
      const bar = mk("g", {}, nodes);
      mk("rect", { x: x1 - 60, y: barY - 90, width: x2 - x1 + 120, height: 180, rx: 90, fill: halo(th.mcp), opacity: 0.8 }, bar);
      mk("rect", { x: x1, y: barY - 32, width: x2 - x1, height: 64, rx: 32, fill: "url(#mcpx-mcp-h)", stroke: th.mcp, "stroke-opacity": 0.75, "stroke-width": 1.4 }, bar);
      const busB = mk("line", { x1: x1 + 30, y1: barY, x2: x2 - 30, y2: barY, stroke: th.mcp, "stroke-opacity": 0.4, "stroke-width": 1.4, "stroke-dasharray": "3 9" }, bar);
      const lblBg = mk("rect", { x: 960 - 110, y: barY - 18, width: 220, height: 36, rx: 18, fill: th.bg, stroke: th.mcp, "stroke-opacity": 0.5 }, bar);
      txt(bar, M.layerLabel, 960, barY, { size: 15, weight: 700, ls: "0.3em", fill: th.text });
      init(bar, { opacity: 0, scaleX: 0.05, transformOrigin: "50% 50%" });
      const clean = mk("g", {}, rails);
      const appLinks = apps.map((a) => mk("path", { d: `M ${a.x} ${a.B.y + 2} L ${a.x} ${barY - 32}`, stroke: th.mcp, "stroke-opacity": 0.6, "stroke-width": 1.4, fill: "none" }, clean));
      const sysLinks = sys.map((s) => mk("path", { d: `M ${s.x} ${barY + 32} L ${s.x} ${s.T.y - 2}`, stroke: th.mcp, "stroke-opacity": 0.6, "stroke-width": 1.4, fill: "none" }, clean));
      const route = (a, s) => `M ${a.x} ${a.B.y + 2} L ${a.x} ${barY} L ${s.x} ${barY} L ${s.x} ${s.T.y - 2}`;
      init(root, { opacity: 0, scale: 1.1, transformOrigin: "50% 50%" });
      return { root, rails, nodes, fx: fxl, apps, sys, tangle, tangleLines, bar, busB, appLinks, sysLinks, route, barY, lblBg };
    })();

    // ═════════════════════════════════════════════════════════════════════════
    //  WORLD C — final architectural summary — screen space
    // ═════════════════════════════════════════════════════════════════════════
    const Cw = (() => {
      const root = mk("g", {}, screenG);
      const rails = mk("g", {}, root), nodes = mk("g", {}, root), fxl = mk("g", {}, root);
      const rowsY = [130, 238, 346, 454, 596];
      const rows = cfg.finalStack.map((row, ri) => {
        const n = row.items.length;
        const y = rowsY[ri] != null ? rowsY[ri] : 130 + ri * 110;
        const toneColor = row.tone ? th[row.tone] : n > 1 ? th.faint : th.text;
        const w = row.wide ? 780 : n === 1 ? 380 : Math.min(230, 1180 / n - 18);
        const gap = n > 4 ? 18 : 24;
        const chips = row.items.map((label, i) => {
          const x = 960 + (i - (n - 1) / 2) * (w + gap);
          const isHi = row.highlight === label;
          const color = isHi ? th.mcp : row.viaMcp ? th.mcp : row.tone ? th[row.tone] : th.request;
          const c = card(nodes, { x, y, w, h: 58, r: 14, label, color, size: n > 4 ? 13 : 14.5, ls: "0.16em" });
          if (isHi || row.tone) init(c.glow, { opacity: isHi ? 0.9 : 0.55 });
          c.hi = isHi;
          init(c.g, { opacity: 0, y: 10 });
          return c;
        });
        return { y, chips, toneColor, row };
      });
      const links = [];
      for (let ri = 0; ri < rows.length - 1; ri++) {
        const a = rows[ri], b = rows[ri + 1];
        const segs = [];
        if (b.row.viaMcp) {
          const hub = a.chips.find((c) => c.hi) || a.chips[a.chips.length - 1];
          const busY = (hub.B.y + b.chips[0].T.y) / 2;
          const xs = b.chips.map((c) => c.x);
          segs.push({ d: `M ${hub.x} ${hub.B.y + 4} L ${hub.x} ${busY}`, color: th.mcp });
          segs.push({ d: `M ${Math.min(...xs, hub.x)} ${busY} L ${Math.max(...xs, hub.x)} ${busY}`, color: th.mcp });
          b.chips.forEach((c) => segs.push({ d: `M ${c.x} ${busY} L ${c.x} ${c.T.y - 4}`, color: th.mcp }));
          a.hubRoute = b.chips.map((c) => `M ${hub.x} ${hub.B.y + 4} L ${hub.x} ${busY} L ${c.x} ${busY} L ${c.x} ${c.T.y - 4}`);
        } else if (a.chips.length === 1 && b.chips.length > 1) {
          b.chips.forEach((c) => segs.push({ d: `M ${c.x} ${a.chips[0].B.y + 4} L ${c.x} ${c.T.y - 4}`, color: th.faint }));
        } else {
          segs.push({ d: `M 960 ${a.chips[0].B.y + 4} L 960 ${b.chips[0].T.y - 4}`, color: th.faint });
        }
        links.push(segs.map((s) => mk("path", { d: s.d, stroke: s.color === th.faint ? th.muted : s.color, "stroke-opacity": s.color === th.mcp ? 0.7 : 0.5, "stroke-width": 1.4, fill: "none" }, rails)));
      }
      const title = txt(root, cfg.finalTitle, 960, 800, { size: 46, weight: 650, ls: "0.06em" });
      const subtitle = txt(root, cfg.finalSubtitle, 960, 862, { size: 22, fill: th.muted, weight: 400 });
      const rule = mk("line", { x1: 900, y1: 752, x2: 1020, y2: 752, stroke: th.mcp, "stroke-width": 2 }, root);
      init(title, { opacity: 0, y: 14 });
      init(subtitle, { opacity: 0, y: 10 });
      init(rule, { opacity: 0, scaleX: 0, transformOrigin: "50% 50%" });
      init(root, { opacity: 0 });
      return { root, rows, links, title, subtitle, rule, fx: fxl };
    })();

    // ═════════════════════════════════════════════════════════════════════════
    //  TIMELINE
    // ═════════════════════════════════════════════════════════════════════════
    camera(440, 520, 1.6, 0, 0.001);
    let t = 0;

    // ── Scene 1 — the user request ──────────────────────────────────────────
    const s1 = TM.s1;
    const S1 = 0;
    to(user.g, { opacity: 1 }, S1 + S(0.3), S(0.9), "power2.out");
    to(agent.g, { opacity: 1, scale: 1 }, S1 + S(0.7), S(1.0), "power3.out");
    drawIn(railUA, S1 + S(0.9), S(1.0));
    t = S1 + s1.intro;
    to(prompt.g, { opacity: 1, y: 0 }, t, S(0.6), "power3.out");
    const tType = t + S(0.4);
    {
      const full = prompt.lines;
      const total = full.reduce((a, l) => a + l.length, 0);
      fx(tType, s1.typing, (v) => {
        let n = Math.round(v * total);
        let lastEl = prompt.lineEls[0], lastLen = 0;
        full.forEach((l, i) => {
          const take = Math.max(0, Math.min(l.length, n));
          prompt.lineEls[i].textContent = l.slice(0, take);
          if (take > 0 || i === 0) { lastEl = prompt.lineEls[i]; lastLen = take; }
          n -= l.length;
        });
        const bx = +lastEl.getAttribute("x") + (lastLen ? lastEl.getComputedTextLength() : 0) + 3;
        prompt.caret.setAttribute("transform", `translate(${bx} ${lastEl.getAttribute("y")})`);
        prompt.caret.setAttribute("opacity", v >= 1 ? 0 : 1);
      });
    }
    t = tType + s1.typing + s1.readHold;
    // Send: prompt folds into the rail, a request pulse travels to the agent
    to(prompt.g, { opacity: 0, scale: 0.5, y: 120 }, t, S(0.6), "power2.in");
    comet(railUA_D, th.request, t + S(0.25), s1.send, { tail: 180 });
    t += S(0.25) + s1.send;
    to(agent.glow, { opacity: 1 }, t - S(0.1), S(0.4));
    to(agentHalo, { opacity: 1 }, t - S(0.1), S(0.8));
    pulseNode(agent, th.request, t - S(0.05));
    // Understand → Plan → Act → Answer
    t += S(0.5);
    to(loopRow.g, { opacity: 1 }, t, S(0.5));
    const loopStart = t + S(0.3);
    loopRow.items.forEach((it, i) => {
      const ti = loopStart + i * s1.loopStep;
      to(it.lit, { opacity: 1 }, ti, S(0.3));
      to(it.bar, { opacity: 1 }, ti, S(0.3));
      if (i > 0) to(loopRow.items[i - 1].bar, { opacity: 0 }, ti, S(0.3));
    });
    caption(cfg.captions.s1, loopStart + S(0.2), ex.loop.length * s1.loopStep + s1.hold - S(1.2));
    t = loopStart + ex.loop.length * s1.loopStep + s1.hold;
    eyebrow(0, S1, t);

    // ── Scene 2 — reveal the agentic stack ──────────────────────────────────
    const s2 = TM.s2;
    const S2 = t;
    to(loopRow.g, { opacity: 0 }, S2, S(0.6));
    to(agent.glow, { opacity: 0.45 }, S2, S(0.8));
    camera(770, 540, 1.08, S2, s2.zoom);
    // ring
    drawIn(ring.solid, S2 + S(0.8), s2.ring, "power2.inOut");
    to(ring.dashed, { opacity: 1 }, S2 + S(1.4), S(1.0));
    to(ring.fill, { opacity: 0.8 }, S2 + S(1.2), S(1.2));
    to(ring.label, { opacity: 1 }, S2 + S(1.6), S(0.8));
    caption(cfg.captions.s2, S2 + S(1.9), s2.captionHold + S(3.6));
    // capabilities
    const capList = cfg.capabilities.map((c) => caps[c.id]);
    const capStart = S2 + S(2.4);
    capList.forEach((n, i) => {
      const ti = capStart + i * s2.capStagger;
      to(n.g, { opacity: 1, scale: 1 }, ti, S(0.6), "power3.out");
      to(n.spoke, { opacity: 1 }, ti + S(0.2), S(0.5));
    });
    // orchestration
    let tm = capStart + capList.length * s2.capStagger + S(0.5);
    orbiter.vis[0] = tm - S(0.1);
    comet(`M ${C.x} ${agent.T.y - 4} L ${C.x} ${C.y - RING_R + 2}`, th.orchestrator, tm - S(0.4), S(0.5), { tail: 60, scale: 0.8 });
    let curA = -90;
    orbiter.keys.push({ t0: tm, t1: tm + 0.001, a0: -90, a1: -90 });
    const jitter = [0, S(0.15), S(-0.1), S(0.2), 0];
    cfg.orchestration.forEach((mv, j) => {
      const n = caps[mv.cap];
      if (!n) return;
      let target = n.angle;
      while (target - curA > 180) target -= 360;
      while (target - curA < -180) target += 360;
      const t0 = tm + (jitter[j % jitter.length] || 0);
      const travel = S(0.35 + Math.abs(target - curA) / 520);
      orbiter.keys.push({ t0, t1: t0 + travel, a0: curA, a1: target });
      curA = target;
      const arrive = t0 + travel;
      comet(n.spokeD, th.orchestrator, arrive - S(0.05), S(0.35), { tail: 60, scale: 0.8, ease: "power1.out" });
      const alert = mv.tone === "alert";
      const col = alert ? th.data : th.orchestrator;
      to(n.glow, { opacity: 1 }, arrive + S(0.25), S(0.2));
      pulseNode(n, col, arrive + S(0.25));
      if (!alert) {
        to(n.glow, { opacity: 0 }, arrive + S(1.3), S(0.5));
        comet(n.spokeD, th.orchestrator, arrive + S(0.7), S(0.35), { tail: 60, scale: 0.7, reverse: true });
      }
      const tag = mk("g", { opacity: 0 }, A.top);
      const tx = n.side < 0 ? n.x - n.w / 2 - 18 : n.x + n.w / 2 + 18;
      txt(tag, mv.tag, tx, n.y, { size: 15, weight: 500, fill: alert ? th.data : th.text, anchor: n.side < 0 ? "end" : "start" });
      if (alert) {
        const w = measure(mv.tag, { size: 15 });
        mk("line", { x1: tx, y1: n.y + 16, x2: tx + w, y2: n.y + 16, stroke: th.data, "stroke-opacity": 0.6 }, tag);
        win(arrive + S(0.3), S(0.4), s2.hold + S(1.2), S(0.4), (a) => tag.setAttribute("opacity", a));
      } else {
        win(arrive + S(0.3), S(0.35), S(0.9), S(0.4), (a) => tag.setAttribute("opacity", a));
      }
      tm += s2.move;
    });
    // orbiter parks at TOOLS
    t = tm + s2.hold;
    orbiter.vis[1] = t;
    eyebrow(1, S2, t + S(0.6));

    // ── Scene 3 — the problem ───────────────────────────────────────────────
    const s3 = TM.s3;
    const S3 = t;
    camera(930, 540, 1.02, S3, S(1.8));
    const dimCaps = capList.filter((n) => n !== toolsCap);
    dimCaps.forEach((n) => to(n.g, { opacity: 0.3 }, S3, S(0.8)));
    dimCaps.forEach((n) => to(n.spoke, { opacity: 0.3 }, S3, S(0.8)));
    to(toolsCap.glow, { opacity: 0.5 }, S3, S(0.8));
    to(ring.g, { opacity: 0.55 }, S3, S(0.8));
    to(user.g, { opacity: 0.45 }, S3, S(0.8));
    to(agent.glow, { opacity: 1 }, S3 + S(0.6), S(0.5));
    let tn = S3 + S(1.0);
    needs.forEach((nd, i) => {
      const ti = tn + i * s3.needStagger;
      drawIn(nd.link, ti, S(0.6));
      comet(nd.link.getAttribute("d"), th.request, ti, S(0.6), { tail: 90, scale: 0.8 });
      to(nd.pg, { opacity: 1, x: 0 }, ti + S(0.4), S(0.6), "power3.out");
    });
    const tReach = tn + needs.length * s3.needStagger + S(0.2);
    needs.forEach((nd, i) => {
      drawIn(nd.reach, tReach + i * S(0.12), s3.reach * 0.6, "power2.out");
      to(nd.sock, { opacity: 1 }, tReach + s3.reach * 0.5 + i * S(0.12), S(0.5));
    });
    // lines falter: they don't connect
    const tFail = tReach + s3.reach + S(0.2);
    needs.forEach((nd, i) => {
      to(nd.reach, { opacity: 0.25 }, tFail + i * S(0.1), S(0.25), "power1.inOut");
      to(nd.reach, { opacity: 0.75 }, tFail + S(0.35) + i * S(0.1), S(0.2));
      to(nd.reach, { opacity: 0.2 }, tFail + S(0.7) + i * S(0.1), S(0.4));
    });
    // the question
    const tQ = tFail + S(1.4);
    to(worldA, { opacity: 0.16 }, tQ, S(0.9));
    caption(cfg.captions.s3Question, tQ + S(0.3), s3.questionHold, { y: 540, size: 46, weight: 500 });
    const tQEnd = tQ + S(0.3) + S(0.7) + s3.questionHold + S(0.6);
    t = tQEnd;
    eyebrow(2, S3, t);

    // ── Scene 4 — introduce MCP ─────────────────────────────────────────────
    const s4 = TM.s4;
    const S4 = t;
    needs.forEach((nd) => {
      to(nd.pg, { opacity: 0 }, S4 - S(0.5), S(0.4));
      to(nd.sock, { opacity: 0 }, S4 - S(0.5), S(0.4));
      to(nd.link, { opacity: 0 }, S4 - S(0.5), S(0.4));
      to(nd.reach, { opacity: 0 }, S4 - S(0.5), S(0.4));
    });
    to(worldA, { opacity: 1 }, S4, S(1.0));
    camera(975, 540, 0.98, S4, S(1.8));
    to(toolsCap.glow, { opacity: 0 }, S4, S(0.6));
    const tBar = S4 + S(0.9);
    to(mcp.body, { opacity: 1, scaleY: 0.02, scaleX: 0.3 }, tBar, S(0.3));
    to(mcp.body, { scaleY: 1 }, tBar + S(0.2), s4.build * 0.6, "expo.out");
    to(mcp.body, { scaleX: 1 }, tBar + s4.build * 0.45, s4.build * 0.4, "power3.out");
    to(mcp.title, { opacity: 1, y: 0 }, tBar + s4.build * 0.5, S(0.8), "power3.out");
    to(mcp.sub, { opacity: 1 }, tBar + s4.build * 0.7, S(0.8));
    const tPorts = tBar + s4.build;
    mcp.ports.forEach((p, i) => {
      to(p.left.g, { opacity: 1, scale: 1 }, tPorts + i * S(0.07), S(0.35), "back.out(2)");
      to(p.right.g, { opacity: 1, scale: 1 }, tPorts + i * S(0.07) + S(0.05), S(0.35), "back.out(2)");
    });
    // agent (and its tools) connect to MCP
    const tTrunk = tPorts + s4.ports * 0.5;
    drawIn(trunk, tTrunk, S(0.8));
    comet(trunk.getAttribute("d"), th.mcp, tTrunk + S(0.3), S(0.8), { tail: 120 });
    to(toolsLink, { opacity: 1 }, tTrunk + S(0.3), S(0.6));
    to(toolsCap.g, { opacity: 1 }, tTrunk + S(0.3), S(0.6));
    to(ring.g, { opacity: 0.8 }, tTrunk, S(0.8));
    to(user.g, { opacity: 0.6 }, tTrunk, S(0.8));
    const tCap4 = tPorts + s4.ports;
    caption(cfg.captions.s4, tCap4, s4.captionHold + s4.connect, { size: 28, sub: cfg.captions.s4Sub, subFill: th.mcp });
    // enterprise endpoints plug into MCP
    const tConn = tCap4 + S(1.2);
    const sysList = cfg.systems.map((s) => systems[s.id]);
    sysList.forEach((n, i) => {
      const ti = tConn + (i * s4.connect) / (sysList.length + 1);
      to(n.g, { opacity: 0.55, x: 0 }, ti, S(0.6), "power3.out");
      drawIn(n.conn, ti + S(0.25), S(0.45));
      to(mcp.ports[i].right.lit, { opacity: 1 }, ti + S(0.6), S(0.2));
    });
    // discover
    const tDisc = tConn + s4.connect + S(0.3);
    to(mcp.verbWrap, { opacity: 1 }, tDisc - S(0.5), S(0.6));
    to(mcp.verbs[0].lit, { opacity: 1 }, tDisc, S(0.3));
    sysList.forEach((n, i) => {
      comet(n.conn.getAttribute("d"), th.mcp, tDisc + i * S(0.06), S(0.6), { tail: 60, scale: 0.7 });
      comet(n.conn.getAttribute("d"), th.data, tDisc + S(0.75) + i * S(0.06), S(0.6), { tail: 60, scale: 0.7, reverse: true });
      to(n.g, { opacity: 1 }, tDisc + S(0.55) + i * S(0.06), S(0.4));
      to(n.content, { opacity: 1 }, tDisc + S(0.6) + i * S(0.06), S(0.6));
      pulseNode(n, th.mcp, tDisc + S(0.55) + i * S(0.06));
    });
    to(mcp.verbs[0].lit, { opacity: 0 }, tDisc + s4.discover + S(0.4), S(0.4));
    t = tDisc + s4.discover + S(0.6);
    eyebrow(3, S4, t);

    // ── Scene 5 — the Cash Equity MCP ecosystem in action ───────────────────
    const s5 = TM.s5;
    const S5 = t;
    // steps indicator (bottom)
    const steps = (() => {
      const g = mk("g", { opacity: 0 }, screenG);
      const o = { size: 16, weight: 500 };
      const gap = 64;
      const ws = cfg.captions.s5Steps.map((s) => measure(s, o) + 26);
      const tot = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
      let x = 960 - tot / 2;
      const y = 1000;
      const items = cfg.captions.s5Steps.map((s, i) => {
        const dot = mk("circle", { cx: x + 6, cy: y, r: 5, fill: "none", stroke: th.faint, "stroke-width": 1.4 }, g);
        const dotLit = mk("circle", { cx: x + 6, cy: y, r: 5, fill: th.mcp }, g);
        const dim = txt(g, s, x + 24, y, { ...o, anchor: "start", fill: th.faint });
        const lit = txt(g, s, x + 24, y, { ...o, anchor: "start", fill: th.text });
        if (i < ws.length - 1) mk("line", { x1: x + ws[i] + 14, y1: y, x2: x + ws[i] + gap - 14, y2: y, stroke: th.faint, "stroke-width": 1.2 }, g);
        init(dotLit, { opacity: 0 });
        init(lit, { opacity: 0 });
        x += ws[i] + gap;
        return { dotLit, lit, dot };
      });
      init(g, { opacity: 0 });
      return { g, items };
    })();
    const stepOn = (i, at) => { to(steps.items[i].lit, { opacity: 1 }, at, S(0.4)); to(steps.items[i].dotLit, { opacity: 1 }, at, S(0.4)); };

    // prompt echo (top centre)
    const echo = (() => {
      const g = mk("g", {}, screenG);
      const s = ex.promptShort;
      const w = measure(s, { size: 17, italic: true }) + 70;
      mk("rect", { x: 960 - w / 2, y: 50, width: w, height: 44, rx: 22, fill: "#0B1018", stroke: th.request, "stroke-opacity": 0.5 }, g);
      mk("path", { d: `M ${960 - w / 2 + 24} 66 a 7 7 0 1 0 7 7 M ${960 - w / 2 + 31} 60 l 0 6 l -6 0`, fill: "none", stroke: th.request, "stroke-width": 1.5, "stroke-linecap": "round" }, g);
      txt(g, s, 960 - w / 2 + 46, 72, { size: 17, anchor: "start", italic: true, fill: th.text });
      init(g, { opacity: 0, y: -10 });
      return g;
    })();

    to(echo, { opacity: 1, y: 0 }, S5 + S(0.2), S(0.6), "power3.out");
    to(steps.g, { opacity: 1 }, S5 + S(0.4), S(0.6));
    to(user.g, { opacity: 1 }, S5, S(0.5));
    to(user.glow, { opacity: 1 }, S5 + S(0.3), S(0.4));
    comet(railUA_D, th.request, S5 + S(0.5), S(1.1), { tail: 160 });
    to(user.glow, { opacity: 0 }, S5 + S(1.2), S(0.6));
    pulseNode(agent, th.request, S5 + S(1.6));
    // focus: dim what isn't involved
    const tFocus = S5 + S(1.4);
    capList.forEach((n) => to(n.g, { opacity: n === toolsCap ? 0.55 : 0.25 }, tFocus, S(0.8)));
    capList.forEach((n) => to(n.spoke, { opacity: 0.25 }, tFocus, S(0.8)));
    to(toolsLink, { opacity: 0.3 }, tFocus, S(0.8));
    to(ring.g, { opacity: 0.45 }, tFocus, S(0.8));
    to(user.g, { opacity: 0.45 }, tFocus + S(0.6), S(0.8));
    sysList.forEach((n) => to(n.g, { opacity: 0.4 }, tFocus, S(0.8)));
    // plan
    const tPlan = S5 + s5.replay;
    stepOn(0, tPlan);
    plan.forEach((p, i) => to(p.g, { opacity: 1, x: 0 }, tPlan + i * s5.planStagger, S(0.5), "power3.out"));
    // calls
    const tCalls = tPlan + plan.length * s5.planStagger + S(0.5);
    let lastArrive = tCalls;
    let firstBar = Infinity, firstBack = Infinity;
    ex.calls.forEach((call, ci) => {
      const tc = tCalls + ci * s5.callGap;
      const pr = plan[call.plan];
      if (pr) to(pr.litT, { opacity: 1 }, tc - S(0.2), S(0.3));
      call.targets.forEach((tg, ti) => {
        const n = systems[tg.system];
        if (!n) return;
        const t0 = tc + ti * S(0.25);
        to(n.rail, { opacity: 1 }, t0, S(0.4));
        comet(n.callD, th.mcp, t0, s5.call, { tail: 170 });
        const tBarHit = t0 + s5.call * 0.62;
        firstBar = Math.min(firstBar, tBarHit);
        pulse(A.fx, BAR.x, n.y, { w: BAR.w + 20, h: 34, rx: 17 }, th.mcp, tBarHit, 0.7);
        to(mcp.ports[n.idx].left.lit, { opacity: 1 }, tBarHit - S(0.1), S(0.2));
        // call label
        const lab = mk("g", { opacity: 0 }, A.top);
        txt(lab, tg.call, (BAR.x + BAR.w / 2 + SYS_X - SYS_W / 2) / 2, n.y - 32, { size: 12, mono: true, fill: th.mcp });
        win(tBarHit - S(0.1), S(0.25), S(1.2), S(0.4), (a) => lab.setAttribute("opacity", a));
        const tHit = t0 + s5.call;
        to(n.g, { opacity: 1 }, tHit - S(0.2), S(0.3));
        to(n.glow, { opacity: 1 }, tHit - S(0.05), S(0.25));
        pulseNode(n, th.mcp, tHit - S(0.05));
        // data returns
        const chip = dataChip(A.top, tg.returns, th.data);
        const tBack = tHit + S(0.25);
        firstBack = Math.min(firstBack, tBack);
        carry(chip, n.callD, tBack, s5.dataBack);
        comet(n.callD, th.data, tBack, s5.dataBack, { tail: 140, reverse: true, scale: 0.8, ease: "power2.inOut" });
        to(n.glow, { opacity: 0.35 }, tBack + S(0.6), S(0.5));
        const tArr = tBack + s5.dataBack;
        pulseNode(agent, th.data, tArr - S(0.05));
        lastArrive = Math.max(lastArrive, tArr);
        if (pr && ti === call.targets.length - 1) to(pr.check, { opacity: 1 }, tArr, S(0.3));
      });
    });
    stepOn(1, firstBar);
    to(mcp.verbs[1].lit, { opacity: 1 }, firstBar - S(0.2), S(0.3));
    stepOn(2, firstBack + S(0.4));
    to(mcp.verbs[2].lit, { opacity: 1 }, firstBack, S(0.3));
    // combine
    const tComb = lastArrive + S(0.3);
    stepOn(3, tComb);
    to(mcp.verbs[1].lit, { opacity: 0 }, tComb, S(0.5));
    to(mcp.verbs[2].lit, { opacity: 0 }, tComb, S(0.5));
    [0, 0.45, 0.9].forEach((d) => pulse(A.fx, C.x, C.y, { r: 70 }, th.request, tComb + S(d), 1.2));
    to(agentHalo, { scale: 1.25, transformOrigin: "50% 50%" }, tComb, S(0.8), "power2.out");
    to(agentHalo, { scale: 1 }, tComb + S(1.2), S(0.9));
    t = tComb + s5.combine;
    eyebrow(4, S5, t);

    // ── Scene 6 — the result ────────────────────────────────────────────────
    const s6 = TM.s6;
    const S6 = t;
    to(steps.g, { opacity: 0 }, S6, S(0.6));
    to(echo, { opacity: 0 }, S6, S(0.6));
    plan.forEach((p) => to(p.g, { opacity: 0 }, S6, S(0.5)));
    const dimAll = [ring.g, mcp.g, trunk, toolsLink, ...capList.map((n) => n.g), ...capList.map((n) => n.spoke), ...sysList.map((n) => n.g), ...sysList.map((n) => n.rail), ...sysList.map((n) => n.conn)];
    dimAll.forEach((el) => to(el, { opacity: 0.1 }, S6 + S(0.1), S(0.9)));
    to(agent.g, { opacity: 0.35 }, S6 + S(0.4), S(0.8));
    camera(600, 540, 1.1, S6, S(1.6));
    const tCard = S6 + S(0.5);
    to(result.mover, { opacity: 1, scale: 1 }, tCard, S(0.8), "power3.out");
    result.rows.forEach((r, i) => to(r, { opacity: 1, y: 0 }, tCard + S(0.5) + (i * (s6.build - S(0.8))) / result.rows.length, S(0.6), "power3.out"));
    const tDeliver = tCard + s6.build + S(0.3);
    const dx = user.x + 60 + result.w / 2 - C.x + 40;
    to(result.mover, { x: dx }, tDeliver, s6.deliver, "power3.inOut");
    to(agent.g, { opacity: 0.6 }, tDeliver, S(0.5));
    to(agent.g, { opacity: 0.06 }, tDeliver + s6.deliver * 0.6, S(0.6));
    to(agentHalo, { opacity: 0.2 }, tDeliver + s6.deliver * 0.6, S(0.6));
    comet(railAU_D, th.positive, tDeliver, s6.deliver * 0.8, { tail: 200 });
    to(user.g, { opacity: 1 }, tDeliver, S(0.5));
    to(user.glow, { opacity: 1 }, tDeliver + s6.deliver * 0.75, S(0.4));
    pulseNode(user, th.positive, tDeliver + s6.deliver * 0.8);
    const tCap6 = tDeliver + s6.deliver;
    caption(cfg.captions.s6, tCap6, s6.hold - S(0.6), { size: 26 });
    t = tCap6 + s6.hold;
    eyebrow(5, S6, t);

    // ── Scene 7 — why MCP matters ───────────────────────────────────────────
    const s7 = TM.s7;
    const S7 = t;
    camera(960, 540, 0.42, S7, s7.zoom, "power2.inOut");
    to(worldA, { opacity: 0 }, S7 + s7.zoom * 0.35, s7.zoom * 0.6);
    to(B.root, { opacity: 1, scale: 1 }, S7 + s7.zoom * 0.55, S(1.4), "power2.out");
    const tB = S7 + s7.zoom * 0.6;
    B.apps.forEach((n, i) => to(n.g, { opacity: 1, y: 0 }, tB + i * S(0.12), S(0.7), "power3.out"));
    B.sys.forEach((n, i) => to(n.g, { opacity: 1, y: 0 }, tB + S(0.4) + i * S(0.1), S(0.7), "power3.out"));
    // point-to-point tangle
    const tT = tB + s7.build;
    const rnd = mulberry32(7);
    B.tangleLines.forEach((p) => drawIn(p, tT + rnd() * s7.tangle * 0.6, s7.tangle * 0.45));
    caption(cfg.captions.s7Tangle, tT + S(0.4), s7.tangle + s7.tangleHold - S(1.2), { size: 28, sub: cfg.captions.s7TangleSub, subFill: th.warn });
    // resolve through the MCP layer
    const tR = tT + s7.tangle + s7.tangleHold;
    to(B.tangle, { opacity: 0 }, tR, S(0.8));
    to(B.bar, { opacity: 1 }, tR + S(0.3), S(0.3));
    to(B.bar, { scaleX: 1 }, tR + S(0.3), S(1.0), "expo.out");
    B.appLinks.forEach((p, i) => drawIn(p, tR + S(0.9) + i * S(0.08), S(0.5)));
    B.sysLinks.forEach((p, i) => drawIn(p, tR + S(1.1) + i * S(0.08), S(0.5)));
    caption(cfg.captions.s7Once, tR + S(1.0), s7.onceHold, { size: 30, sub: cfg.captions.s7OnceSub, subFill: th.mcp, y: 968 });
    // one agent, many capabilities
    const tO = tR + S(1.0) + S(0.7) + s7.onceHold + S(0.6);
    const focus = B.apps.find((a) => a.id === cfg.multiAgent.focusApp) || B.apps[0];
    B.apps.forEach((a, i) => { if (a !== focus) { to(a.g, { opacity: 0.3 }, tO, S(0.6)); to(B.appLinks[i], { opacity: 0.2 }, tO, S(0.6)); } });
    to(focus.glow, { opacity: 1 }, tO, S(0.5));
    pulseNode(focus, th.request, tO + S(0.2), B.fx);
    B.sys.forEach((sN, i) => {
      const d = B.route(focus, sN);
      const tc = tO + S(0.4) + i * S(0.14);
      comet(d, th.mcp, tc, S(1.2), { tail: 160, layer: B.fx });
      to(sN.glow, { opacity: 1 }, tc + S(1.1), S(0.25));
      comet(d, th.data, tc + S(1.5), S(1.1), { tail: 120, reverse: true, layer: B.fx, scale: 0.8 });
    });
    caption(cfg.captions.s7One, tO + S(0.3), s7.oneAgent - S(1.3), { size: 30 });
    // finale: everything alive
    const tF = tO + s7.oneAgent;
    B.apps.forEach((a, i) => { to(a.g, { opacity: 1 }, tF, S(0.6)); to(B.appLinks[i], { opacity: 1 }, tF, S(0.6)); to(a.glow, { opacity: 0.8 }, tF + i * S(0.1), S(0.5)); });
    B.sys.forEach((sN) => to(sN.glow, { opacity: 0.5 }, tF + S(0.8), S(0.6)));
    const rnd2 = mulberry32(42);
    for (let q = 0; q < 14; q++) {
      const a = B.apps[Math.floor(rnd2() * B.apps.length)];
      const sN = B.sys[Math.floor(rnd2() * B.sys.length)];
      const tc = tF + S(0.2) + rnd2() * (s7.finalHold - S(1.2));
      const back = rnd2() > 0.5;
      comet(B.route(a, sN), back ? th.data : th.mcp, tc, S(1.1), { tail: 140, layer: B.fx, scale: 0.75, reverse: back });
    }
    caption(cfg.captions.s7Final, tF + S(0.2), s7.finalHold - S(0.6), { size: 34, weight: 600 });
    t = tF + s7.finalHold + S(0.6);
    eyebrow(6, S7, t);

    // ── Final frame ─────────────────────────────────────────────────────────
    const sf = TM.final;
    const SF = t;
    to(B.root, { opacity: 0, scale: 0.96 }, SF - S(0.3), S(0.9), "power2.in");
    camera(960, 540, 1, SF + S(0.6), S(0.001));
    to(Cw.root, { opacity: 1 }, SF + S(0.5), S(0.4));
    const rowStep = sf.build / (Cw.rows.length + 1);
    Cw.rows.forEach((row, ri) => {
      const tr = SF + S(0.6) + ri * rowStep;
      row.chips.forEach((c, ci) => to(c.g, { opacity: 1, y: 0 }, tr + ci * S(0.06), S(0.6), "power3.out"));
      if (ri > 0) Cw.links[ri - 1].forEach((p) => drawIn(p, tr - S(0.15), S(0.45)));
    });
    // a request flows down the stack, results flow back up
    const tFlow = SF + S(0.6) + sf.build;
    const hubRow = Cw.rows.find((r) => r.hubRoute);
    const spine = [];
    for (let ri = 0; ri < Cw.rows.length - 1; ri++) {
      const a = Cw.rows[ri], b = Cw.rows[ri + 1];
      if (a.hubRoute) break;
      const bx = b.chips.find((c) => c.hi) ? b.chips.find((c) => c.hi).x : 960;
      const ax = a.chips.length === 1 ? (b.chips.length > 1 ? bx : 960) : bx;
      spine.push(`M ${ax} ${a.chips[0].B.y + 4} L ${bx} ${b.chips[0].T.y - 4}`);
    }
    spine.forEach((d, i) => comet(d, th.request, tFlow + i * S(0.32), S(0.45), { tail: 50, layer: Cw.fx, scale: 0.8 }));
    const tHub = tFlow + spine.length * S(0.32);
    if (hubRow) {
      hubRow.hubRoute.forEach((d, i) => {
        comet(d, th.mcp, tHub + i * S(0.05), S(0.8), { tail: 90, layer: Cw.fx, scale: 0.8 });
        comet(d, th.data, tHub + S(1.0) + i * S(0.05), S(0.8), { tail: 90, layer: Cw.fx, scale: 0.8, reverse: true });
      });
      Cw.rows[Cw.rows.length - 1].chips.forEach((c) => {
        to(c.glow, { opacity: 0.8 }, tHub + S(0.7), S(0.3));
        to(c.glow, { opacity: 0.25 }, tHub + S(1.6), S(0.8));
      });
    }
    const tTitle = tFlow + S(0.4);
    to(Cw.rule, { opacity: 1, scaleX: 1 }, tTitle, S(0.9), "power3.out");
    to(Cw.title, { opacity: 1, y: 0 }, tTitle + S(0.2), S(1.0), "power3.out");
    to(Cw.subtitle, { opacity: 1, y: 0 }, tTitle + S(0.7), S(1.0), "power3.out");
    t = tTitle + sf.titleHold;
    eyebrow(7, SF, null);

    // ── Ambient motion (a pure function of time) ─────────────────────────────
    const total = t;
    const amb = { t: 0 };
    function ambient(tt) {
      ring.dashed.setAttribute("transform", `rotate(${tt * 7} ${C.x} ${C.y})`);
      agentHaloC.setAttribute("opacity", 0.8 + 0.2 * Math.sin(tt * 1.7));
      mcp.bus.setAttribute("stroke-dashoffset", -tt * 30);
      B.busB.setAttribute("stroke-dashoffset", -tt * 30);
      // orbiter
      const [v0, v1] = orbiter.vis;
      if (tt <= v0 || tt >= v1) { orbiter.g.setAttribute("opacity", 0); }
      else {
        const fade = Math.min(1, (tt - v0) / S(0.3), (v1 - tt) / S(0.5));
        orbiter.g.setAttribute("opacity", fade);
        const a = orbitAngle(tt), ap = orbitAngle(Math.max(v0, tt - S(0.18)));
        const p = ringPt(a);
        orbiter.head.setAttribute("transform", `translate(${p.x} ${p.y})`);
        if (Math.abs(a - ap) > 0.5) {
          const q = ringPt(ap);
          const sweep = a > ap ? 1 : 0;
          const large = Math.abs(a - ap) > 180 ? 1 : 0;
          const d = `M ${q.x} ${q.y} A ${RING_R} ${RING_R} 0 ${large} ${sweep} ${p.x} ${p.y}`;
          orbiter.trail.setAttribute("d", d);
          orbiter.trail2.setAttribute("d", d);
        } else {
          orbiter.trail.setAttribute("d", "");
          orbiter.trail2.setAttribute("d", "");
        }
      }
    }
    tl.fromTo(amb, { t: 0 }, { t: total, duration: total, ease: "none", immediateRender: false, onUpdate: () => ambient(amb.t) }, 0);
    applyCam();
    ambient(0);
    tl.seek(0, false);

    return {
      timeline: tl,
      duration: tl.duration(),
      scenes: sceneMarks,
      svg,
      seek: (time) => tl.seek(time, false),
    };
  }

  window.MCPExplainer = { mount };
})();
