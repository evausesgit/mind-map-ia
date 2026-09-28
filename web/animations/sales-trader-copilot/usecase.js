/*
 * Sales Trading Copilot — use-case demo engine
 * --------------------------------------------
 * UseCaseDemo.mount(container, config) builds a 1920×1080 SVG stage and a
 * single paused GSAP timeline from the config (see config.js). It shares the
 * visual language and the scrub-safe rules of the MCP explainer:
 *  - Every element is created at build time; the timeline only animates.
 *  - Persistent state changes go through `to()` (explicit fromTo tweens).
 *  - Ephemeral effects (comets, pulses, captions, typing) go through `fx()`.
 *  - Ambient motion (halo breathing, spinners, blinking) is a function of time.
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
  const plain = (s) => String(s).replace(/\*\*/g, "");

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
    const S = (v) => v * k;

    // ── SVG scaffold ────────────────────────────────────────────────────────
    const svg = mk("svg", {
      viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet",
      class: "stc-stage", role: "img", "aria-label": cfg.title,
    });
    container.appendChild(svg);
    svg.style.fontFamily = th.font;
    const defs = mk("defs", {}, svg);

    const bgGrad = mk("radialGradient", { id: "stc-bg", cx: "50%", cy: "45%", r: "75%" }, defs);
    mk("stop", { offset: "0%", "stop-color": th.bgGlow }, bgGrad);
    mk("stop", { offset: "100%", "stop-color": th.bg }, bgGrad);
    const vig = mk("radialGradient", { id: "stc-vig", cx: "50%", cy: "50%", r: "70%" }, defs);
    mk("stop", { offset: "60%", "stop-color": "#000", "stop-opacity": 0 }, vig);
    mk("stop", { offset: "100%", "stop-color": "#000", "stop-opacity": 0.55 }, vig);
    const dots = mk("pattern", { id: "stc-dots", width: 36, height: 36, patternUnits: "userSpaceOnUse" }, defs);
    mk("circle", { cx: 18, cy: 18, r: 1.1, fill: "#ffffff", "fill-opacity": 0.07 }, dots);
    const cardFill = mk("linearGradient", { id: "stc-card", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    mk("stop", { offset: "0%", "stop-color": "#111723" }, cardFill);
    mk("stop", { offset: "100%", "stop-color": "#0A0E15" }, cardFill);
    const mcpFill = mk("linearGradient", { id: "stc-mcp", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    mk("stop", { offset: "0%", "stop-color": th.mcp, "stop-opacity": 0.05 }, mcpFill);
    mk("stop", { offset: "50%", "stop-color": th.mcp, "stop-opacity": 0.16 }, mcpFill);
    mk("stop", { offset: "100%", "stop-color": th.mcp, "stop-opacity": 0.05 }, mcpFill);
    const mcpFillH = mk("linearGradient", { id: "stc-mcp-h", x1: 0, y1: 0, x2: 1, y2: 0 }, defs);
    mk("stop", { offset: "0%", "stop-color": th.mcp, "stop-opacity": 0.04 }, mcpFillH);
    mk("stop", { offset: "50%", "stop-color": th.mcp, "stop-opacity": 0.16 }, mcpFillH);
    mk("stop", { offset: "100%", "stop-color": th.mcp, "stop-opacity": 0.04 }, mcpFillH);

    const halos = {};
    function halo(color) {
      if (halos[color]) return halos[color];
      const id = "stc-halo-" + Object.keys(halos).length;
      const g = mk("radialGradient", { id }, defs);
      mk("stop", { offset: "0%", "stop-color": color, "stop-opacity": 0.32 }, g);
      mk("stop", { offset: "45%", "stop-color": color, "stop-opacity": 0.1 }, g);
      mk("stop", { offset: "100%", "stop-color": color, "stop-opacity": 0 }, g);
      return (halos[color] = `url(#${id})`);
    }

    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#stc-bg)" }, svg);
    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#stc-dots)" }, svg);
    const L = {
      back: mk("g", {}, svg),
      shared: mk("g", {}, svg),
      fx: mk("g", {}, svg),
      screen: mk("g", {}, svg),
    };
    mk("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#stc-vig)", "pointer-events": "none" }, svg);
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
      if (String(s).includes("**")) {
        String(s).split(/(\*\*[^*]+\*\*)/).forEach((part) => {
          if (!part) return;
          const sp = mk("tspan", {}, t);
          if (part.startsWith("**")) {
            sp.textContent = part.slice(2, -2);
            sp.setAttribute("fill", o.accent || th.mcp);
            sp.setAttribute("font-weight", Math.max(600, o.weight || 500));
          } else sp.textContent = part;
        });
      } else t.textContent = s;
      return t;
    }
    function measure(s, o = {}) {
      const t = txt(measureG, plain(s), 0, 0, o);
      const w = t.getComputedTextLength();
      measureG.removeChild(t);
      return w;
    }
    function wrap(s, maxW, o) {
      const lines = [];
      let line = "";
      for (const w of String(s).split(" ")) {
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
      return at + total;
    }
    function drawIn(path, at, dur, ease = "power2.inOut") {
      const Lp = path.getTotalLength();
      path.setAttribute("stroke-dasharray", `${Lp} ${Lp + 2}`);
      path.setAttribute("stroke-dashoffset", Lp);
      tl.fromTo(path, { attr: { "stroke-dashoffset": Lp } }, {
        attr: { "stroke-dashoffset": 0 }, duration: dur, ease, immediateRender: false,
      }, at);
    }
    // Typewriter over one or several <text> lines
    function typeLines(els, lines, at, dur) {
      const total = lines.reduce((a, l) => a + l.length, 0);
      fx(at, dur, (v) => {
        let n = Math.round(v * total);
        els.forEach((el, i) => {
          const take = Math.max(0, Math.min(lines[i].length, n));
          el.textContent = lines[i].slice(0, take);
          n -= lines[i].length;
        });
      });
    }

    // ── Visual primitives ───────────────────────────────────────────────────
    function glyph(parent, type, x, y, color) {
      const g = mk("g", { transform: `translate(${x} ${y})`, fill: "none", stroke: color, "stroke-width": 1.6, "stroke-linejoin": "round", "stroke-linecap": "round" }, parent);
      if (type === "spark") {
        mk("path", { d: "M0,-11 C1.2,-3 3,-1.2 11,0 C3,1.2 1.2,3 0,11 C-1.2,3 -3,1.2 -11,0 C-3,-1.2 -1.2,-3 0,-11 Z", fill: color, "fill-opacity": 0.9, stroke: "none" }, g);
      } else if (type === "chart") {
        mk("path", { d: "M-9,7 L-3,0 L2,4 L9,-7 M4,-7 H9 V-2" }, g);
      } else if (type === "bolt") {
        mk("path", { d: "M2,-10 L-6,2 H0 L-2,10 L6,-2 H0 Z" }, g);
      } else if (type === "bars") {
        [[-7, 3], [-1, -3], [5, -8]].forEach(([bx, by]) => mk("rect", { x: bx - 2, y: by, width: 4, height: 9 - by, rx: 1 }, g));
      } else if (type === "doc") {
        mk("path", { d: "M-7,-10 H3 L8,-5 V10 H-7 Z M-3,-2 H4 M-3,3 H4" }, g);
      } else if (type === "person") {
        mk("circle", { cx: 0, cy: -4, r: 4.5 }, g);
        mk("path", { d: "M-8,10 C-8,3 8,3 8,10" }, g);
      } else if (type === "lock") {
        mk("rect", { x: -7, y: -2, width: 14, height: 11, rx: 2.5 }, g);
        mk("path", { d: "M-4,-2 V-5 A4,4 0 0 1 4,-5 V-2" }, g);
      } else if (type === "building") {
        mk("path", { d: "M-11,-4 L0,-11 L11,-4 Z M-9,10 H9 M-6,-1 V7 M0,-1 V7 M6,-1 V7" }, g);
      } else {
        mk("circle", { r: 4, fill: color, stroke: "none" }, g);
      }
      return g;
    }

    function card(parent, o) {
      const { x, y, w, h } = o;
      const r = o.r != null ? o.r : 14;
      const color = o.color || th.request;
      const outer = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("rect", { x: -w / 2 - 70, y: -h / 2 - 70, width: w + 140, height: h + 140, rx: r + 60, fill: halo(color) }, glow);
      mk("rect", { x: -w / 2 - 4, y: -h / 2 - 4, width: w + 8, height: h + 8, rx: r + 4, fill: "none", stroke: color, "stroke-opacity": 0.18, "stroke-width": 8 }, glow);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "url(#stc-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: r, fill: "none", stroke: color, "stroke-width": 1.4 }, glow);
      const content = mk("g", {}, g);
      const node = { outer, g, glow, content, x, y, w, h, r, color,
        L: { x: x - w / 2, y }, R: { x: x + w / 2, y }, T: { x, y: y - h / 2 }, B: { x, y: y + h / 2 } };
      const size = o.size || 15;
      const ls = o.ls || "0.14em";
      if (o.align === "left") {
        const lx = -w / 2 + 24;
        if (o.glyph) glyph(content, o.glyph, lx + 8, o.sub ? -11 : 0, color);
        const tx = lx + (o.glyph ? 30 : 0);
        node.label = txt(content, o.label, tx, o.sub ? -11 : 0, { size, weight: 600, ls, anchor: "start" });
        if (o.sub) node.sub = txt(content, o.sub, tx, 14, { size: 12, mono: true, fill: th.muted, anchor: "start" });
      } else if (o.label) {
        const lw = measure(o.label, { size, weight: 600, ls });
        const gw = o.glyph ? 32 : 0;
        const start = -(lw + gw) / 2;
        if (o.glyph) glyph(content, o.glyph, start + 10, o.sub ? -11 : 0, color);
        node.label = txt(content, o.label, start + gw, o.sub ? -11 : 0, { size, weight: 600, ls, anchor: "start" });
        if (o.sub) node.sub = txt(content, o.sub, 0, 14, { size: 12, mono: true, fill: th.muted });
      }
      return node;
    }

    function pill(parent, label, x, y, o = {}) {
      const size = o.size || 13;
      const w = measure(label, { size, mono: true, ls: o.ls || "0.16em" }) + (o.pad || 36);
      const h = o.h || 40;
      const g = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const inner = mk("g", {}, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: h / 2, fill: o.fill || "url(#stc-card)", stroke: o.color || th.line, "stroke-opacity": o.strokeOpacity || 1, "stroke-width": 1.2 }, inner);
      const t = txt(inner, label, 0, 0, { size, mono: true, ls: o.ls || "0.16em", fill: o.textFill || th.text });
      return { g: inner, outer: g, text: t, w, h, x, y };
    }

    // Person node (circle + icon + label)
    function person(parent, x, y, label, sub, color, glyphType = "person") {
      const outer = mk("g", { transform: `translate(${x} ${y})` }, parent);
      const g = mk("g", {}, outer);
      const glow = mk("g", { opacity: 0 }, g);
      mk("circle", { r: 120, fill: halo(color) }, glow);
      mk("circle", { r: 51, fill: "none", stroke: color, "stroke-opacity": 0.25, "stroke-width": 8 }, glow);
      mk("circle", { r: 46, fill: "url(#stc-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("circle", { r: 46, fill: "none", stroke: color, "stroke-width": 1.4, "stroke-opacity": 0.7 }, g);
      if (glyphType === "person") {
        const icon = mk("g", { fill: "none", stroke: th.text, "stroke-width": 1.8, "stroke-linecap": "round" }, g);
        mk("circle", { cx: 0, cy: -9, r: 9 }, icon);
        mk("path", { d: "M-17,19 C-17,5 17,5 17,19" }, icon);
      } else {
        const gg = glyph(g, glyphType, 0, 0, th.text);
        gg.setAttribute("transform", "scale(1.7)");
      }
      if (label) txt(g, label, 0, 84, { size: 14, weight: 600, ls: "0.2em" });
      if (sub) txt(g, sub, 0, 108, { size: 12, mono: true, fill: th.muted });
      return { outer, g, glow, x, y, r: 46, color };
    }

    function comet(d, color, at, dur, o = {}) {
      const g = mk("g", { opacity: 0 }, o.layer || L.fx);
      const sc = o.scale || 1;
      const paths = [[16, 0.06], [7, 0.2], [2.4, 1]].map(([w, a]) =>
        mk("path", { d, fill: "none", stroke: color, "stroke-width": w * sc, "stroke-opacity": a, "stroke-linecap": "round" }, g));
      const head = mk("g", {}, g);
      mk("circle", { r: 20 * sc, fill: color, opacity: 0.1 }, head);
      mk("circle", { r: 8 * sc, fill: color, opacity: 0.4 }, head);
      mk("circle", { r: 3.4 * sc, fill: "#fff" }, head);
      const Lp = paths[0].getTotalLength();
      const tail = Math.min(o.tail || 170, Lp * 0.7);
      paths.forEach((p) => p.setAttribute("stroke-dasharray", `${tail} ${Lp + 3 * tail}`));
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { g.setAttribute("opacity", 0); return; }
        g.setAttribute("opacity", 1);
        const s = v * (Lp + tail);
        paths.forEach((p) => p.setAttribute("stroke-dashoffset", tail - s));
        const pt = paths[0].getPointAtLength(Math.min(s, Lp));
        head.setAttribute("transform", `translate(${pt.x} ${pt.y})`);
        head.setAttribute("opacity", s <= Lp ? 1 : 0);
      }, o.ease || "power1.inOut");
    }

    function chipShape(parent, label, color, o = {}) {
      const g = mk("g", {}, parent);
      const size = o.size || 14;
      const w = measure(label, { size, mono: true }) + 32;
      if (o.halo !== false) mk("rect", { x: -w / 2 - 10, y: -24, width: w + 20, height: 48, rx: 22, fill: halo(color) }, g);
      mk("rect", { x: -w / 2, y: -17, width: w, height: 34, rx: 10, fill: "#15120A", stroke: color, "stroke-width": 1.2 }, g);
      txt(g, label, 0, 0, { size, mono: true, fill: color, weight: 500 });
      return { g, w };
    }
    // Carry a floating chip along a path (default: end → start)
    function carry(label, color, d, at, dur, o = {}) {
      const chip = chipShape(L.fx, label, color).g;
      chip.setAttribute("opacity", 0);
      const p = mk("path", { d }, measureG);
      const Lp = p.getTotalLength();
      const fwd = !!o.forward;
      fx(at, dur, (v) => {
        if (v <= 0 || v >= 1) { chip.setAttribute("opacity", 0); return; }
        const e = easeInOut(v);
        const pt = p.getPointAtLength(fwd ? e * Lp : (1 - e) * Lp);
        const sc = v < 0.12 ? easeOut(v / 0.12) : v > 0.88 ? Math.max(0.05, (1 - v) / 0.12) : 1;
        chip.setAttribute("opacity", v > 0.88 ? (1 - v) / 0.12 : 1);
        chip.setAttribute("transform", `translate(${pt.x} ${pt.y}) scale(${sc})`);
      });
    }

    function pulse(x, y, shape, color, at, dur = 0.9) {
      const g = mk("g", { transform: `translate(${x} ${y})`, opacity: 0 }, L.fx);
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
    // Pulse at a node's *current* on-screen position (pass it explicitly)
    const pulseAt = (x, y, n, color, at) => pulse(x, y, n.r != null && n.w == null ? { r: n.r } : { w: n.w, h: n.h, rx: n.r || 16 }, color || n.color, at);

    // Glow window on a node
    const glowWin = (n, at, hold) => win(at, S(0.3), hold, S(0.4), (a) => n.glow.setAttribute("opacity", a));

    // Screen-space caption
    function caption(lines, at, hold, o = {}) {
      lines = Array.isArray(lines) ? lines : [lines];
      const size = o.size || 30;
      const lh = size * 1.3;
      const y0 = (o.y || 975) - ((lines.length - 1) * lh) / 2 - (o.sub ? 18 : 0);
      const g = mk("g", { opacity: 0 }, L.screen);
      lines.forEach((l, i) => txt(g, l, W / 2, y0 + i * lh, {
        size, weight: o.weight || 500, fill: (o.fills && o.fills[i]) || o.fill || th.text, ls: "-0.005em", accent: o.accent,
      }));
      if (o.sub) txt(g, o.sub, W / 2, y0 + (lines.length - 1) * lh + size * 0.6 + 26, { size: 17, mono: true, fill: th.muted });
      const fi = S(0.7), fo = S(0.6);
      win(at, fi, hold, fo, (a) => {
        g.setAttribute("opacity", a);
        g.setAttribute("transform", `translate(0 ${(1 - a) * 12})`);
      });
      return at + fi + hold + fo;
    }

    // Eyebrow (scene label, top-left) — call once a scene's end is known
    const sceneMarks = [];
    function eyebrow(index, at, until) {
      const sc = cfg.scenes[index];
      sceneMarks.push({ id: sc.id, label: sc.label, time: at });
      tl.addLabel(sc.id, at);
      const g = mk("g", { opacity: 0 }, L.screen);
      mk("line", { x1: 72, y1: 72, x2: 96, y2: 72, stroke: th.mcp, "stroke-width": 2 }, g);
      txt(g, String(index + 1).padStart(2, "0"), 110, 72, { size: 13, mono: true, fill: th.text, anchor: "start" });
      txt(g, sc.label.toUpperCase(), 142, 72, { size: 13, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
      win(at + S(0.2), S(0.6), Math.max(0, until - at - S(1.4)), S(0.6), (a) => g.setAttribute("opacity", a));
    }

    // Disclaimer, always on
    txt(L.screen, cfg.disclaimer, W - 72, 72, { size: 11.5, mono: true, fill: th.faint, anchor: "end", ls: "0.2em" });

    const sceneG = () => mk("g", {}, L.back);

    // ═════════════════════════════════════════════════════════════════════════
    //  SHARED ACTORS — Sales Trader, Copilot, phase bar
    // ═════════════════════════════════════════════════════════════════════════
    const TR0 = { x: 700, y: 540 };
    const trader = person(L.shared, TR0.x, TR0.y, cfg.trader.label, cfg.trader.sub, th.request);
    init(trader.g, { opacity: 0, scale: 0.9, transformOrigin: "50% 50%" });
    const trPos = { x: TR0.x, y: TR0.y };
    function moveTrader(x, y, at, dur, extra = {}) {
      to(trader.g, { x: x - TR0.x, y: y - TR0.y, ...extra }, at, dur);
      trPos.x = x; trPos.y = y;
    }

    const CP0 = { x: 860, y: 540 };
    const copHalo = mk("g", {}, L.shared);
    const copHaloC = mk("circle", { cx: CP0.x, cy: CP0.y, r: 240, fill: halo(th.agent) }, copHalo);
    const cop = card(L.shared, { x: CP0.x, y: CP0.y, w: 380, h: 104, r: 26, label: cfg.copilot.label, glyph: "spark", color: th.agent, size: 18, ls: "0.16em" });
    // "thinking" dashed outline travelling around the copilot
    const spin = mk("rect", { x: -202, y: -64, width: 404, height: 128, rx: 36, fill: "none", stroke: th.agent, "stroke-width": 2, "stroke-dasharray": "90 380", "stroke-linecap": "round", opacity: 0 }, cop.g);
    init(cop.g, { opacity: 0, scale: 0.92, transformOrigin: "50% 50%" });
    init(copHalo, { opacity: 0, transformOrigin: "50% 50%" });
    const cpPos = { x: CP0.x, y: CP0.y, s: 1 };
    function moveCop(x, y, s, at, dur) {
      to(cop.g, { x: x - CP0.x, y: y - CP0.y, scale: s }, at, dur);
      to(copHalo, { x: x - CP0.x, y: y - CP0.y, scale: s }, at, dur);
      Object.assign(cpPos, { x, y, s });
    }
    const copR = () => ({ x: cpPos.x + 190 * cpPos.s, y: cpPos.y });
    const copL = () => ({ x: cpPos.x - 190 * cpPos.s, y: cpPos.y });
    const thinking = (at, dur) => win(at, S(0.3), dur, S(0.4), (a) => spin.setAttribute("opacity", a * 0.9));

    // Phase bar
    const phaseBar = (() => {
      const g = mk("g", {}, L.shared);
      const o = { size: 14, mono: true, ls: "0.22em" };
      const gap = 74;
      const ws = cfg.phases.map((p) => measure(p, o));
      const total = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
      let x = W / 2 - total / 2;
      const y = 150;
      const items = cfg.phases.map((p, i) => {
        const dim = txt(g, p, x, y, { ...o, anchor: "start", fill: th.faint });
        const done = txt(g, p, x, y, { ...o, anchor: "start", fill: th.muted });
        const lit = txt(g, p, x, y, { ...o, anchor: "start", fill: th.agent });
        const bar = mk("rect", { x, y: y + 18, width: ws[i], height: 2, rx: 1, fill: th.agent }, g);
        [done, lit, bar].forEach((e) => init(e, { opacity: 0 }));
        if (i < ws.length - 1) {
          const ax = x + ws[i] + gap / 2;
          mk("path", { d: `M ${ax - 9} ${y} L ${ax + 7} ${y} M ${ax + 2} ${y - 5} L ${ax + 7} ${y} L ${ax + 2} ${y + 5}`, stroke: th.faint, "stroke-width": 1.4, fill: "none" }, g);
        }
        x += ws[i] + gap;
        return { dim, done, lit, bar };
      });
      init(g, { opacity: 0 });
      return { g, items, cur: -1 };
    })();
    function phaseTo(i, at) {
      const P = phaseBar;
      if (P.cur >= 0) {
        to(P.items[P.cur].lit, { opacity: 0 }, at, S(0.4));
        to(P.items[P.cur].bar, { opacity: 0 }, at, S(0.4));
        to(P.items[P.cur].done, { opacity: 1 }, at, S(0.4));
      }
      to(P.items[i].lit, { opacity: 1 }, at, S(0.5));
      to(P.items[i].bar, { opacity: 1 }, at, S(0.5));
      P.cur = i;
    }

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 1 — The client already knows
    // ═════════════════════════════════════════════════════════════════════════
    const T1 = TM.s1;
    let t = S(0.3);
    const S1 = t;
    const g1 = sceneG();
    init(g1, { opacity: 1 });

    const ticker = (() => {
      const outer = mk("g", { transform: "translate(960 250)" }, g1);
      const g = mk("g", {}, outer);
      const w = 580, h = 196;
      mk("rect", { x: -w / 2 - 60, y: -h / 2 - 60, width: w + 120, height: h + 120, rx: 80, fill: halo(th.positive), opacity: 0.5 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 22, fill: "url(#stc-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      txt(g, cfg.event.name, -250, -52, { size: 46, weight: 700, anchor: "start", ls: "0.02em" });
      txt(g, cfg.event.ticker, -250, -12, { size: 13, mono: true, fill: th.muted, anchor: "start", ls: "0.12em" });
      txt(g, cfg.event.move, 250, -52, { size: 46, weight: 700, anchor: "end", fill: th.positive });
      mk("circle", { cx: 196, cy: -12, r: 4, fill: th.positive }, g);
      txt(g, "LIVE", 250, -12, { size: 12, mono: true, fill: th.positive, anchor: "end", ls: "0.2em" });
      // deterministic intraday path: drift, then the jump
      const pts = [];
      for (let i = 0; i <= 60; i++) {
        const x = -250 + (500 * i) / 60;
        const base = 70 - (i > 34 ? (i - 34) * 1.25 : 0) - (i > 36 ? 10 : 0);
        const noise = Math.sin(i * 1.7) * 4 + Math.sin(i * 0.53) * 5;
        pts.push(`${x.toFixed(1)},${(base + noise).toFixed(1)}`);
      }
      const spark = mk("path", { d: "M " + pts.join(" L "), fill: "none", stroke: th.positive, "stroke-width": 2.2, "stroke-linejoin": "round" }, g);
      mk("line", { x1: -250, y1: 70, x2: 250, y2: 70, stroke: th.line, "stroke-dasharray": "2 6" }, g);
      init(g, { opacity: 0, y: 14 });
      return { g, spark };
    })();

    const SRC_Y = 500;
    const sources = cfg.publicSources.map((s, i) => {
      const x = 960 + (i - (cfg.publicSources.length - 1) / 2) * 300;
      const n = card(g1, { x, y: SRC_Y, w: 272, h: 78, r: 16, label: s.label, sub: s.sub, glyph: "dot", color: th.public, align: "left", size: 13.5 });
      init(n.g, { opacity: 0, y: 12 });
      return n;
    });
    const CL = { x: 560, y: 770 };
    const clientLinks = sources.map((n) => {
      const d = `M ${n.x} ${SRC_Y + 40} C ${n.x} ${SRC_Y + 150}, ${CL.x} ${CL.y - 150}, ${CL.x} ${CL.y - 50}`;
      const p = mk("path", { d, stroke: th.public, "stroke-opacity": 0.35, "stroke-width": 1.2, fill: "none" }, g1);
      g1.insertBefore(p, g1.firstChild);
      return { p, d };
    });
    const client = person(g1, CL.x, CL.y, cfg.client.label, cfg.client.sub, th.public, "building");
    init(client.g, { opacity: 0, scale: 0.9, transformOrigin: "50% 50%" });
    const headline = (() => {
      const outer = mk("g", { transform: "translate(1180 770)" }, g1);
      const g = mk("g", {}, outer);
      const w = 900, h = 92;
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 16, fill: "url(#stc-card)", stroke: th.public, "stroke-opacity": 0.5, "stroke-width": 1.2 }, g);
      txt(g, cfg.headlineMeta, -w / 2 + 28, -20, { size: 11.5, mono: true, fill: th.muted, anchor: "start", ls: "0.22em" });
      txt(g, cfg.headline, -w / 2 + 28, 14, { size: 23, weight: 500, anchor: "start" });
      init(g, { opacity: 0, x: -16 });
      return { g };
    })();
    const headLink = mk("path", { d: `M ${CL.x + 52} ${CL.y} L ${1180 - 452} ${CL.y}`, stroke: th.public, "stroke-opacity": 0.5, "stroke-width": 1.2, fill: "none" }, g1);

    const question = mk("g", { opacity: 0 }, L.screen);
    txt(question, cfg.captions.s1Question, W / 2, 540, { size: 60, weight: 600, ls: "-0.01em", accent: th.request });

    to(ticker.g, { opacity: 1, y: 0 }, t, T1.ticker, "power3.out");
    drawIn(ticker.spark, t + S(0.3), T1.spark);
    t += S(1.5);
    sources.forEach((n, i) => to(n.g, { opacity: 1, y: 0 }, t + i * T1.sourceStagger, S(0.6), "power3.out"));
    t += sources.length * T1.sourceStagger + S(0.2);
    to(client.g, { opacity: 1, scale: 1 }, t, S(0.6), "power3.out");
    clientLinks.forEach((l, i) => {
      drawIn(l.p, t + i * S(0.1), S(0.7));
      comet(l.d, th.public, t + S(0.2) + i * S(0.14), T1.flow, { tail: 120, scale: 0.8 });
    });
    t += S(0.2) + sources.length * S(0.14) + T1.flow - S(0.2);
    pulseAt(CL.x, CL.y, client, th.public, t);
    drawIn(headLink, t, S(0.5));
    to(headline.g, { opacity: 1, x: 0 }, t + S(0.3), S(0.7), "power3.out");
    t += S(1.1);
    t = caption(cfg.captions.s1Knows, t, T1.knowsHold) - S(0.3);
    to(g1, { opacity: 0.12 }, t, S(0.9));
    const qEnd = win(t + S(0.3), S(0.9), T1.questionHold, S(0.7), (a) => {
      question.setAttribute("opacity", a);
      question.setAttribute("transform", `translate(0 ${(1 - a) * 14})`);
    });
    to(g1, { opacity: 0 }, qEnd - S(0.8), S(0.7));
    t = qEnd;
    eyebrow(0, 0, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 2 — The Sales Trader's different vantage point
    // ═════════════════════════════════════════════════════════════════════════
    const T2 = TM.s2;
    const S2 = t;
    const g2 = sceneG();
    const VR = 300;
    const vAngles = [-90, -30, 30, 90, 150, 210];
    const boundary = mk("path", {
      d: (() => { const x = 250, y = 180, w = 900, h = 730, r = 40;
        return `M ${x + r} ${y} H ${x + w - r} A ${r} ${r} 0 0 1 ${x + w} ${y + r} V ${y + h - r} A ${r} ${r} 0 0 1 ${x + w - r} ${y + h} H ${x + r} A ${r} ${r} 0 0 1 ${x} ${y + h - r} V ${y + r} A ${r} ${r} 0 0 1 ${x + r} ${y} Z`; })(),
      fill: "none", stroke: th.agent, "stroke-opacity": 0.35, "stroke-width": 1.2, "stroke-dasharray": "3 7",
    }, g2);
    const permLabel = (() => {
      const g = mk("g", { transform: "translate(700 910)" }, g2);
      const w = measure(cfg.permissionLabel, { size: 12, mono: true, ls: "0.2em" }) + 64;
      mk("rect", { x: -w / 2, y: -14, width: w, height: 28, fill: th.bg }, g);
      glyph(g, "lock", -w / 2 + 22, 0, th.agent);
      txt(g, cfg.permissionLabel, 14, 0, { size: 12, mono: true, fill: th.agent, ls: "0.2em" });
      init(g, { opacity: 0 });
      return g;
    })();
    const vCards = cfg.vantage.map((v, i) => {
      const a = (vAngles[i % 6] * Math.PI) / 180;
      const x = TR0.x + VR * Math.cos(a) * 0.87, y = TR0.y + VR * Math.sin(a);
      const spoke = mk("path", { d: `M ${TR0.x} ${TR0.y} L ${x} ${y}`, stroke: th.agent, "stroke-opacity": 0.35, "stroke-width": 1.2, fill: "none", "stroke-dasharray": "2 6" }, g2);
      const n = card(g2, { x, y, w: 340, h: 62, r: 16, label: v.label, glyph: v.glyph, color: th.agent, size: 13.5 });
      init(n.g, { opacity: 0, scale: 0.9, transformOrigin: "50% 50%" });
      init(spoke, { opacity: 0 });
      return { n, spoke };
    });
    const qx = 1250;
    const qTitle = txt(g2, cfg.questionsTitle, qx, 282, { size: 12.5, mono: true, fill: th.muted, anchor: "start", ls: "0.24em" });
    init(qTitle, { opacity: 0 });
    const qItems = cfg.questions.map((q, i) => {
      const g = mk("g", {}, g2);
      const y = 344 + i * 70;
      mk("rect", { x: qx, y: y - 16, width: 3, height: 32, rx: 1.5, fill: th.request }, g);
      txt(g, q, qx + 22, y, { size: 25, weight: 500, anchor: "start" });
      init(g, { opacity: 0, x: -14 });
      return g;
    });

    // The overload: many systems around the trader
    const g2b = sceneG();
    const screenPos = [[330, 240, -4], [700, 190, 2], [1230, 195, -2], [1600, 270, 3], [250, 540, 2], [1670, 560, -3], [380, 780, -2], [760, 785, 3], [1170, 790, -3], [1560, 800, 2]];
    const screens = cfg.screens.map((name, i) => {
      const [x, y, rot] = screenPos[i % screenPos.length];
      const outer = mk("g", { transform: `translate(${x} ${y}) rotate(${rot})` }, g2b);
      const g = mk("g", {}, outer);
      const w = 250, h = 150;
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 12, fill: "url(#stc-card)", stroke: th.line, "stroke-width": 1.2 }, g);
      mk("line", { x1: -w / 2, y1: -h / 2 + 30, x2: w / 2, y2: -h / 2 + 30, stroke: th.line }, g);
      txt(g, name, -w / 2 + 16, -h / 2 + 15, { size: 10.5, mono: true, fill: th.muted, anchor: "start", ls: "0.18em" });
      const dot = mk("circle", { cx: w / 2 - 16, cy: -h / 2 + 15, r: 4.5, fill: th.warn }, g);
      [0, 1, 2].forEach((j) => mk("rect", { x: -w / 2 + 16, y: -h / 2 + 46 + j * 16, width: 60 + ((i * 37 + j * 53) % 120), height: 5, rx: 2.5, fill: "#ffffff", "fill-opacity": 0.1 }, g));
      const pts = [];
      for (let j = 0; j <= 20; j++) pts.push(`${-w / 2 + 16 + j * 10.9},${h / 2 - 22 - Math.abs(Math.sin(j * 0.9 + i)) * 18 - j * 0.5}`);
      mk("path", { d: "M " + pts.join(" L "), fill: "none", stroke: [th.public, th.data, th.mcp, th.request][i % 4], "stroke-opacity": 0.6, "stroke-width": 1.5 }, g);
      init(g, { opacity: 0, scale: 0.85, transformOrigin: "50% 50%" });
      return { g, dot, x, y, phase: i * 0.77 };
    });
    let screensVis = [0, 0];

    let t2 = t + S(0.2);
    to(trader.g, { opacity: 1, scale: 1 }, t2, S(0.8), "power3.out");
    t2 += S(0.6);
    vCards.forEach((c, i) => {
      to(c.spoke, { opacity: 1 }, t2 + i * T2.cardStagger, S(0.5));
      to(c.n.g, { opacity: 1, scale: 1 }, t2 + i * T2.cardStagger, S(0.6), "power3.out");
    });
    t2 += vCards.length * T2.cardStagger;
    drawIn(boundary, t2, S(1.2));
    to(permLabel, { opacity: 1 }, t2 + S(0.8), S(0.6));
    const vantageCapEnd = caption(cfg.captions.s2Vantage, t2 + S(0.4), T2.vantageHold, { size: 27 });
    t2 += S(1.0);
    to(qTitle, { opacity: 1 }, t2, S(0.5));
    qItems.forEach((q, i) => to(q, { opacity: 1, x: 0 }, t2 + S(0.3) + i * T2.questionStagger, S(0.6), "power3.out"));
    t2 += S(0.3) + qItems.length * T2.questionStagger + T2.questionsHold;
    t2 = Math.max(t2, vantageCapEnd);
    // → overload
    to(g2, { opacity: 0 }, t2, S(0.7));
    moveTrader(960, 540, t2 + S(0.2), S(1.0));
    t2 += S(0.8);
    screensVis[0] = t2;
    screens.forEach((s, i) => to(s.g, { opacity: 1, scale: 1 }, t2 + i * T2.screenStagger, S(0.5), "back.out(1.4)"));
    // the trader's attention bouncing between systems
    const hop = [0, 4, 6, 2, 8, 5, 3, 9, 1].map((i) => screens[i]);
    const hopD = "M 960 540 " + hop.map((s) => `L ${s.x} ${s.y}`).join(" ");
    const hopLine = mk("path", { d: hopD, stroke: th.request, "stroke-opacity": 0.22, "stroke-width": 1.2, fill: "none" }, g2b);
    g2b.insertBefore(hopLine, g2b.firstChild);
    drawIn(hopLine, t2 + S(0.6), S(2.4), "none");
    comet(hopD, th.request, t2 + S(0.6), S(2.4), { tail: 200, ease: "none", scale: 0.8 });
    t2 += screens.length * T2.screenStagger + S(0.3);
    t2 = caption(cfg.captions.s2Problem, t2, T2.problemHold, { size: 36, weight: 600, fills: [th.text, th.warn], sub: cfg.captions.s2ProblemSub, y: 950 });
    t = t2 - S(0.4);
    eyebrow(1, S2, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 3 — Introduce the Sales Trading Copilot
    // ═════════════════════════════════════════════════════════════════════════
    const T3 = TM.s3;
    const S3 = t;
    const g3 = sceneG();
    to(g2b, { opacity: 0 }, t, S(0.7));
    screensVis[1] = t + S(0.7);
    moveTrader(230, 540, t + S(0.2), S(1.0));
    to(cop.g, { opacity: 1, scale: 1 }, t + S(0.8), S(0.9), "power3.out");
    to(copHalo, { opacity: 1 }, t + S(0.8), S(1.2));
    t += S(1.6);

    const bubble = (() => {
      const o = { size: 25, weight: 500 };
      const lines = wrap(cfg.prompt, 860, o);
      const w = Math.max(...lines.map((l) => measure(l, o))) + 64;
      const h = lines.length * 38 + 44;
      const x = 150, y = 330 - h / 2;
      const g = mk("g", {}, g3);
      mk("path", { d: `M ${x + 60} ${y + h} L ${x + 80} ${y + h + 22} L ${x + 100} ${y + h} Z`, fill: "#0A0E15", stroke: th.request, "stroke-opacity": 0.55, "stroke-width": 1.2 }, g);
      mk("rect", { x, y, width: w, height: h, rx: 20, fill: "url(#stc-card)", stroke: th.request, "stroke-opacity": 0.55, "stroke-width": 1.2 }, g);
      mk("rect", { x: x + 60, y: y + h - 2, width: 40, height: 4, fill: "#0A0E15" }, g);
      txt(g, cfg.promptMeta, x + 4, y - 22, { size: 12, mono: true, fill: th.request, anchor: "start", ls: "0.2em" });
      const els = lines.map((l, i) => txt(g, "", x + 32, y + 22 + 19 + i * 38, { ...o, anchor: "start" }));
      init(g, { opacity: 0, y: 10 });
      return { g, els, lines };
    })();
    to(bubble.g, { opacity: 1, y: 0 }, t, S(0.6), "power3.out");
    typeLines(bubble.els, bubble.lines, t + S(0.4), T3.typing);
    t += S(0.4) + T3.typing + T3.readHold;
    comet(`M ${280} ${540} L ${copL().x - 6} ${540}`, th.request, t, T3.send, { tail: 140 });
    t += T3.send;
    pulseAt(cpPos.x, cpPos.y, { w: 380, h: 104, r: 26 }, th.agent, t);
    thinking(t, T3.think + TM.s3.planStagger * cfg.plan.length);

    const planG = mk("g", {}, g3);
    const PX = 1160;
    const planHead = txt(planG, "PLAN", PX, 372, { size: 12.5, mono: true, fill: th.agent, anchor: "start", ls: "0.26em" });
    const planLink = mk("path", { d: `M ${copR().x + 4} 540 C ${copR().x + 60} 540, ${PX - 70} 510, ${PX - 22} 510`, stroke: th.agent, "stroke-opacity": 0.5, "stroke-width": 1.2, fill: "none" }, planG);
    const planItems = cfg.plan.map((p, i) => {
      const y = 424 + i * 58;
      const g = mk("g", {}, planG);
      mk("circle", { cx: PX + 14, cy: y, r: 14, fill: "none", stroke: th.agent, "stroke-opacity": 0.6 }, g);
      txt(g, String(i + 1), PX + 14, y, { size: 13, mono: true, fill: th.agent });
      txt(g, p, PX + 44, y, { size: 21, anchor: "start" });
      init(g, { opacity: 0, x: -12 });
      return g;
    });
    init(planHead, { opacity: 0 });
    t += T3.think * 0.5;
    drawIn(planLink, t, S(0.6));
    to(planHead, { opacity: 1 }, t + S(0.3), S(0.5));
    planItems.forEach((g, i) => to(g, { opacity: 1, x: 0 }, t + S(0.5) + i * T3.planStagger, S(0.55), "power3.out"));
    to(phaseBar.g, { opacity: 1 }, t + S(0.5), S(0.8));
    phaseTo(0, t + S(0.8));
    caption(cfg.captions.s3Plan, t + S(0.8), S(2.4));
    t += S(0.5) + planItems.length * T3.planStagger + T3.hold;
    eyebrow(2, S3, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 4 — The Agent uses enterprise capabilities via MCP
    // ═════════════════════════════════════════════════════════════════════════
    const T4 = TM.s4;
    const S4 = t;
    const g4 = sceneG();
    const g4infra = mk("g", {}, g4);
    const g4board = mk("g", {}, g4);
    to(g3, { opacity: 0 }, t, S(0.6));
    moveTrader(190, 330, t + S(0.2), S(1.0), { opacity: 0.5 });
    moveCop(620, 330, 1, t + S(0.2), S(1.0));
    phaseTo(1, t + S(0.4));

    const BAR = { x: 1130, y1: 292, y2: 908, w: 56 };
    const SRV_X = 1530, SRV_W = 440, SRV_H = 92;
    const nSrv = cfg.servers.length;
    const srvY = (i) => 336 + i * ((856 - 336) / Math.max(1, nSrv - 1));
    const COP4 = { x: 620, y: 330 };
    const COP4R = { x: COP4.x + 190, y: COP4.y };

    const mcpBar = (() => {
      const g = mk("g", {}, g4infra);
      const body = mk("g", {}, g);
      const h = BAR.y2 - BAR.y1;
      mk("rect", { x: BAR.x - 100, y: BAR.y1 - 50, width: 200, height: h + 100, rx: 100, fill: halo(th.mcp), opacity: 0.6 }, body);
      mk("rect", { x: BAR.x - BAR.w / 2, y: BAR.y1, width: BAR.w, height: h, rx: BAR.w / 2, fill: "url(#stc-mcp)", stroke: th.mcp, "stroke-opacity": 0.7, "stroke-width": 1.4 }, body);
      const bus = mk("line", { x1: BAR.x, y1: BAR.y1 + 26, x2: BAR.x, y2: BAR.y2 - 26, stroke: th.mcp, "stroke-opacity": 0.55, "stroke-width": 1.5, "stroke-dasharray": "3 9" }, body);
      init(body, { opacity: 0, scaleY: 0.02, scaleX: 0.3, transformOrigin: "50% 50%" });
      const title = txt(g, "MCP", BAR.x, BAR.y1 - 58, { size: 34, weight: 700, ls: "0.22em" });
      const sub = txt(g, "MODEL CONTEXT PROTOCOL", BAR.x, BAR.y1 - 26, { size: 11, mono: true, ls: "0.28em", fill: th.mcp });
      init(title, { opacity: 0 });
      init(sub, { opacity: 0 });
      const portGs = [];
      const ports = cfg.servers.map((_, i) => {
        const pg = mk("g", { transform: `translate(${BAR.x - BAR.w / 2} ${srvY(i)})` }, g);
        mk("rect", { x: -7, y: -7, width: 14, height: 14, rx: 3.5, fill: th.bg, stroke: th.mcp, "stroke-width": 1.4 }, pg);
        const lit = mk("rect", { x: -3.5, y: -3.5, width: 7, height: 7, rx: 1.5, fill: th.mcp, opacity: 0 }, pg);
        portGs.push(pg);
        return lit;
      });
      portGs.forEach((pg) => init(pg, { opacity: 0 }));
      return { body, bus, title, sub, ports, portGs };
    })();

    const servers = cfg.servers.map((s, i) => {
      const y = srvY(i);
      const n = card(g4infra, { x: SRV_X, y, w: SRV_W, h: SRV_H, r: 16, label: s.label, sub: s.sub, glyph: "dot", color: th.mcp, align: "left", size: 14 });
      if (s.permissioned) {
        n.lock = mk("g", {}, n.content);
        glyph(n.lock, "lock", SRV_W / 2 - 30, 0, th.positive);
      }
      n.callD = `M ${COP4R.x + 4} ${COP4R.y} C ${COP4R.x + 160} ${COP4R.y}, ${BAR.x - 200} ${y}, ${BAR.x - BAR.w / 2} ${y} L ${SRV_X - SRV_W / 2 - 2} ${y}`;
      n.rail = mk("path", { d: n.callD, stroke: th.mcp, "stroke-opacity": 0.16, "stroke-width": 1.2, fill: "none" }, g4infra);
      g4infra.insertBefore(n.rail, g4infra.firstChild);
      const mp = mk("path", { d: n.callD }, measureG);
      n.callPt = mp.getPointAtLength(mp.getTotalLength() * 0.36);
      n.cfg = s;
      init(n.g, { opacity: 0, x: 24 });
      init(n.rail, { opacity: 0 });
      return n;
    });

    // Evidence board
    const BOARD = { x: 235, y: 468, w: 650, h: 408 };
    const boardFrame = mk("g", {}, g4board);
    mk("rect", { x: BOARD.x, y: BOARD.y, width: BOARD.w, height: BOARD.h, rx: 22, fill: "#ffffff", "fill-opacity": 0.015, stroke: th.data, "stroke-opacity": 0.3, "stroke-width": 1.2, "stroke-dasharray": "3 7" }, boardFrame);
    txt(boardFrame, cfg.evidenceTitle, BOARD.x + 26, BOARD.y + 30, { size: 12, mono: true, fill: th.data, anchor: "start", ls: "0.26em" });
    const boardLink = mk("path", { d: `M ${COP4.x} ${COP4.y + 52} L ${COP4.x} ${BOARD.y}`, stroke: th.data, "stroke-opacity": 0.35, "stroke-width": 1.2, "stroke-dasharray": "2 6" }, boardFrame);
    init(boardFrame, { opacity: 0 });
    const linkLayer = mk("g", {}, g4board);
    const evidence = [];
    const slot = (j) => ({ x: BOARD.x + (j % 2 === 0 ? 170 : 490), y: BOARD.y + 82 + Math.floor(j / 2) * 56 });
    cfg.servers.forEach((s, si) => s.returns.forEach((label) => {
      const j = evidence.length;
      const p = slot(j);
      const outer = mk("g", { transform: `translate(${p.x} ${p.y})` }, g4board);
      const chip = chipShape(outer, label, th.data, { halo: false, size: 14 });
      init(chip.g, { opacity: 0, scale: 0.7, transformOrigin: "50% 50%" });
      evidence.push({ g: chip.g, w: chip.w, label, x: p.x, y: p.y, server: si });
    }));

    let t4 = t + S(0.6);
    to(mcpBar.body, { opacity: 1, scaleY: 1, scaleX: 1 }, t4, T4.build, "power3.inOut");
    to(mcpBar.title, { opacity: 1 }, t4 + S(0.5), S(0.6));
    to(mcpBar.sub, { opacity: 1 }, t4 + S(0.7), S(0.6));
    mcpBar.portGs.forEach((pg, i) => to(pg, { opacity: 1 }, t4 + S(0.8) + i * S(0.1), S(0.4)));
    servers.forEach((n, i) => {
      to(n.g, { opacity: 1, x: 0 }, t4 + S(0.5) + i * S(0.12), S(0.6), "power3.out");
      to(n.rail, { opacity: 1 }, t4 + S(0.8) + i * S(0.12), S(0.6));
    });
    to(boardFrame, { opacity: 1 }, t4 + S(0.8), S(0.6));
    caption(cfg.captions.s4Select, t4 + S(0.6), S(2.6), { size: 27 });
    t4 += T4.build + S(0.5);
    thinking(t4, nSrv * T4.callGap);

    let ev = 0;
    servers.forEach((n, i) => {
      const tc = t4 + i * T4.callGap;
      const s = n.cfg;
      // select → call
      glowWin(n, tc + T4.call * 0.7, T4.back + s.returns.length * T4.chipStagger);
      fx(tc, T4.call + T4.back + S(0.6), (v) => n.rail.setAttribute("stroke-opacity", v > 0 && v < 1 ? 0.55 : 0.16));
      comet(n.callD, th.mcp, tc, T4.call, { tail: 160 });
      const callPill = pill(L.fx, s.call, n.callPt.x, n.callPt.y, { size: 12.5, ls: "0.02em", color: th.mcp, textFill: th.mcp, h: 32, fill: "#07151A", pad: 30 });
      callPill.outer.setAttribute("opacity", 0);
      win(tc, S(0.2), T4.call + S(0.2), S(0.3), (a) => callPill.outer.setAttribute("opacity", a));
      fx(tc + T4.call * 0.5, T4.call + T4.back, (v) => mcpBar.ports[i].setAttribute("opacity", v > 0 && v < 1 ? 1 : 0));
      pulseAt(n.x, n.y, n, th.mcp, tc + T4.call);
      if (s.permissioned) {
        caption(cfg.captions.s4Permission, tc, S(2.6), { size: 24, fill: th.positive });
        pulse(SRV_X + SRV_W / 2 - 30, n.y, { r: 16 }, th.positive, tc + T4.call);
      }
      // data returns onto the evidence board
      s.returns.forEach((label, j) => {
        const e = evidence[ev++];
        const d = `M ${e.x} ${e.y} C ${e.x + 260} ${e.y}, ${BAR.x - 260} ${n.y}, ${BAR.x - BAR.w / 2} ${n.y} L ${SRV_X - SRV_W / 2 - 2} ${n.y}`;
        const ta = tc + T4.call + S(0.1) + j * T4.chipStagger;
        carry(label, th.data, d, ta, T4.back);
        to(e.g, { opacity: 1, scale: 1 }, ta + T4.back * 0.86, S(0.35), "back.out(1.6)");
      });
    });
    t = t4 + nSrv * T4.callGap + T4.hold;
    eyebrow(3, S4, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 5 — From information to insight
    // ═════════════════════════════════════════════════════════════════════════
    const T5 = TM.s5;
    const S5 = t;
    to(g4infra, { opacity: 0 }, t, S(0.7));
    moveTrader(190, 330, t, S(0.6), { opacity: 0 });
    phaseTo(2, t + S(0.2));
    // correlation web between evidence chips
    const byLabel = (l) => evidence.find((e) => e.label === l);
    const links = cfg.correlations.map(([a, b]) => {
      const A = byLabel(a), B = byLabel(b);
      if (!A || !B) return null;
      const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
      const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
      const bend = A.x === B.x ? 150 : 50;
      const cx = mx - (dy / len) * bend, cy = my + (dx / len) * bend;
      const p = mk("path", { d: `M ${A.x} ${A.y} Q ${cx} ${cy} ${B.x} ${B.y}`, stroke: th.data, "stroke-opacity": 0.75, "stroke-width": 1.6, fill: "none" }, linkLayer);
      return { p, A, B };
    }).filter(Boolean);
    let t5 = t + S(0.5);
    links.forEach((l, i) => {
      const ta = t5 + i * T5.linkStagger;
      drawIn(l.p, ta, S(0.7));
      [l.A, l.B].forEach((e) => pulse(e.x, e.y, { w: e.w, h: 34, rx: 10 }, th.data, ta + S(0.5), 0.8));
    });
    t5 += links.length * T5.linkStagger + S(0.8);
    // everything collapses into the copilot
    evidence.forEach((e, i) => to(e.g, { x: COP4.x - e.x, y: COP4.y - e.y, scale: 0.2, opacity: 0 }, t5 + i * S(0.05), T5.collapse, "power2.in"));
    to(linkLayer, { opacity: 0 }, t5, S(0.5));
    to(boardFrame, { opacity: 0 }, t5, S(0.5));
    t5 += evidence.length * S(0.05) + T5.collapse;
    pulseAt(COP4.x, COP4.y, { w: 380, h: 104, r: 26 }, th.agent, t5);
    glowWin(cop, t5, S(0.8));
    moveCop(270, 540, 0.8, t5 + S(0.5), S(0.9));
    t5 += S(0.9);

    const g5 = sceneG();
    const BC = { x: 1080, y: 565 };
    const plainFact = txt(g5, cfg.plainFact, BC.x, BC.y, { size: 46, weight: 600, fill: th.muted });
    init(plainFact, { opacity: 0, transformOrigin: "50% 50%" });
    to(plainFact, { opacity: 1 }, t5, S(0.6));
    t5 += S(1.3);
    to(plainFact, { opacity: 0, scale: 0.8 }, t5, S(0.5));

    const B = cfg.briefing;
    const brief = (() => {
      const w = 1180, h = 690;
      const outer = mk("g", { transform: `translate(${BC.x} ${BC.y})` }, g5);
      const g = mk("g", {}, outer);
      mk("rect", { x: -w / 2 - 60, y: -h / 2 - 60, width: w + 120, height: h + 120, rx: 90, fill: halo(th.agent), opacity: 0.45 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 26, fill: "url(#stc-card)", stroke: th.agent, "stroke-opacity": 0.55, "stroke-width": 1.3 }, g);
      const lx = -w / 2 + 44, rx = w / 2 - 44, cx2 = 20;
      const rows = [];
      const row = () => { const r = mk("g", {}, g); init(r, { opacity: 0, y: 10 }); rows.push(r); return r; };
      // header
      const hd = row();
      txt(hd, B.title, lx, -290, { size: 42, weight: 700, anchor: "start", ls: "0.02em" });
      txt(hd, B.sub, lx, -252, { size: 12.5, mono: true, fill: th.muted, anchor: "start", ls: "0.14em" });
      txt(hd, B.move, rx, -290, { size: 42, weight: 700, anchor: "end", fill: th.positive });
      const tagW = measure(B.tag, { size: 10.5, mono: true, ls: "0.2em" }) + 22;
      mk("rect", { x: rx - tagW, y: -264, width: tagW, height: 24, rx: 6, fill: "none", stroke: th.data, "stroke-opacity": 0.6 }, hd);
      txt(hd, B.tag, rx - tagW / 2, -252, { size: 10.5, mono: true, fill: th.data, ls: "0.2em" });
      mk("line", { x1: lx, y1: -222, x2: rx, y2: -222, stroke: th.line }, hd);
      const diff = row();
      txt(diff, B.differentTitle, lx, -193, { size: 13, mono: true, fill: th.data, anchor: "start", ls: "0.24em" });
      // facts (2 × 2)
      const bars = [];
      const facts = B.facts.map((f, i) => {
        const r = row();
        const x0 = i % 2 === 0 ? lx : cx2;
        const y0 = i < 2 ? -152 : -28;
        txt(r, f.k, x0, y0, { size: 11.5, mono: true, fill: th.muted, anchor: "start", ls: "0.2em" });
        const vo = { size: 20, weight: 500 };
        const lines = wrap(f.v, 520, vo);
        lines.forEach((l, j) => txt(r, l, x0, y0 + 30 + j * 27, { ...vo, anchor: "start" }));
        if (f.bars) {
          const max = Math.max(...f.bars.map((b) => b[1]));
          const by0 = y0 + 30 + lines.length * 27 + 6;
          f.bars.forEach(([lab, val, disp], j) => {
            const by = by0 + j * 22;
            const hi = j === f.bars.length - 1;
            txt(r, lab, x0, by, { size: 10.5, mono: true, fill: hi ? th.text : th.muted, anchor: "start", ls: "0.14em" });
            const bw = (val / max) * 300;
            const bar = mk("rect", { x: x0 + 90, y: by - 5, width: bw, height: 10, rx: 3, fill: hi ? th.positive : th.faint }, r);
            init(bar, { scaleX: 0, transformOrigin: "0% 50%" });
            bars.push({ bar, row: i });
            txt(r, disp || `${val}×`, x0 + 90 + bw + 12, by, { size: 11.5, mono: true, fill: hi ? th.positive : th.muted, anchor: "start" });
          });
        }
        return r;
      });
      const sep = row();
      mk("line", { x1: lx, y1: 104, x2: rx, y2: 104, stroke: th.line }, sep);
      const rel = row();
      txt(rel, B.relevanceTitle, lx, 134, { size: 13, mono: true, fill: th.request, anchor: "start", ls: "0.24em" });
      txt(rel, B.relevance, lx, 168, { size: 21, weight: 500, anchor: "start", accent: th.request });
      const conv = row();
      txt(conv, B.conversationTitle, lx, 216, { size: 13, mono: true, fill: th.mcp, anchor: "start", ls: "0.24em" });
      const co = { size: 20, weight: 500, italic: true };
      const cLines = wrap(B.conversation, w - 130, co);
      mk("rect", { x: lx, y: 236, width: 3, height: cLines.length * 28 + 8, rx: 1.5, fill: th.mcp }, conv);
      const cEls = cLines.map((l, j) => txt(conv, "", lx + 22, 254 + j * 28, { ...co, anchor: "start" }));
      const foot = row();
      txt(foot, B.sources, 0, h / 2 - 22, { size: 10.5, mono: true, fill: th.faint, ls: "0.16em" });
      init(g, { opacity: 0, scale: 0.45, transformOrigin: "50% 50%" });
      return { g, rows, hd, diff, facts, bars, sep, rel, conv, cEls, cLines, foot };
    })();
    const briefLink = mk("path", { d: `M ${270 + 152} 540 L ${BC.x - 590} 540`, stroke: th.agent, "stroke-opacity": 0.5, "stroke-width": 1.3, fill: "none" }, g5);

    to(brief.g, { opacity: 1, scale: 1 }, t5, S(0.9), "power3.out");
    drawIn(briefLink, t5 + S(0.3), S(0.6));
    t5 += S(0.5);
    to(brief.hd, { opacity: 1, y: 0 }, t5, S(0.5));
    to(brief.diff, { opacity: 1, y: 0 }, t5 + S(0.5), S(0.5));
    caption(cfg.captions.s5Insight, t5 + S(0.6), S(4.6), { size: 27 });
    t5 += S(0.8);
    brief.facts.forEach((r, i) => {
      to(r, { opacity: 1, y: 0 }, t5 + i * T5.factStagger, S(0.55), "power3.out");
      brief.bars.filter((b) => b.row === i).forEach((b, j) => to(b.bar, { scaleX: 1 }, t5 + i * T5.factStagger + S(0.3) + j * S(0.2), S(0.7), "power2.out"));
    });
    t5 += brief.facts.length * T5.factStagger + S(0.4);
    phaseTo(3, t5);
    to(brief.sep, { opacity: 1, y: 0 }, t5, S(0.4));
    to(brief.rel, { opacity: 1, y: 0 }, t5, S(0.6), "power3.out");
    t5 += S(1.0);
    to(brief.conv, { opacity: 1, y: 0 }, t5, S(0.5));
    typeLines(brief.cEls, brief.cLines, t5 + S(0.3), T5.typing);
    to(brief.foot, { opacity: 1, y: 0 }, t5 + S(0.3) + T5.typing, S(0.6));
    t = t5 + S(0.3) + T5.typing + T5.hold;
    eyebrow(4, S5, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 6 — The Human + AI moment
    // ═════════════════════════════════════════════════════════════════════════
    const T6 = TM.s6;
    const S6 = t;
    const g6 = sceneG();
    to(g5, { opacity: 0 }, t, S(0.7));
    moveCop(330, 330, 0.85, t + S(0.2), S(1.0));
    const TR6 = { x: 1640, y: 330 };
    moveTrader(TR6.x, TR6.y, t, S(0.01));
    to(trader.g, { opacity: 1 }, t + S(0.6), S(0.8));
    phaseTo(4, t + S(0.6));
    t += S(1.3);
    const delD = `M ${330 + 162} 318 C 820 170, 1320 170, ${TR6.x - 52} ${TR6.y - 12}`;
    comet(delD, th.agent, t, T6.deliver, { tail: 200 });
    carry("BRIEFING · CLIENT ALPHA", th.agent, delD, t, T6.deliver, { forward: true });
    pulseAt(TR6.x, TR6.y, { r: 46 }, th.request, t + T6.deliver);
    glowWin(trader, t + T6.deliver, S(0.6));
    t += T6.deliver - S(0.2);

    // AI message
    const aiMsg = (() => {
      const o = { size: 25, weight: 500 };
      const w = measure(cfg.aiMessage, o) + 64, h = 70;
      const x = 540, y = 330 - h / 2;
      const g = mk("g", {}, g6);
      mk("path", { d: `M ${x} ${y + 24} L ${x - 20} ${y + 35} L ${x} ${y + 46} Z`, fill: "#0E1119", stroke: th.agent, "stroke-opacity": 0.6, "stroke-width": 1.2 }, g);
      mk("rect", { x, y, width: w, height: h, rx: 20, fill: "url(#stc-card)", stroke: th.agent, "stroke-opacity": 0.6, "stroke-width": 1.2 }, g);
      mk("rect", { x: x - 2, y: y + 26, width: 4, height: 18, fill: "#0E1119" }, g);
      txt(g, "COPILOT", x + 4, y - 22, { size: 12, mono: true, fill: th.agent, anchor: "start", ls: "0.24em" });
      const el = txt(g, "", x + 32, 330, { ...o, anchor: "start" });
      init(g, { opacity: 0, x: -10 });
      return { g, el };
    })();
    to(aiMsg.g, { opacity: 1, x: 0 }, t, S(0.5), "power3.out");
    typeLines([aiMsg.el], [cfg.aiMessage], t + S(0.3), T6.typing);
    t += S(0.3) + T6.typing + S(0.3);

    // three actions
    const actions = cfg.actions.map((a, i) => {
      const x = 960 + (i - 1) * 300, y = 452;
      const b = pill(g6, a, x, y, { size: 13, color: th.agent, strokeOpacity: 0.5, h: 54, pad: 50, textFill: th.text });
      const lit = mk("rect", { x: -b.w / 2, y: -27, width: b.w, height: 54, rx: 27, fill: th.agent, "fill-opacity": 0.22, stroke: th.agent, "stroke-width": 1.8, opacity: 0 }, b.g);
      b.g.insertBefore(lit, b.text);
      init(b.g, { opacity: 0, y: 10 });
      return { ...b, lit, x, y };
    });
    actions.forEach((b, i) => to(b.g, { opacity: 1, y: 0 }, t + i * S(0.15), S(0.5), "power3.out"));
    t += S(0.9);
    // cursor
    const chosen = actions[cfg.chosenAction] || actions[actions.length - 1];
    const cursor = mk("g", { transform: `translate(${TR6.x - 60} ${TR6.y + 110})` }, L.fx);
    const curIn = mk("g", {}, cursor);
    mk("path", { d: "M0,0 L0,26 L7,19 L12,30 L16,28 L11,17 L20,17 Z", fill: th.text, stroke: th.bg, "stroke-width": 1.5, "stroke-linejoin": "round" }, curIn);
    init(curIn, { opacity: 0 });
    to(curIn, { opacity: 1 }, t, S(0.3));
    to(curIn, { x: chosen.x + chosen.w / 2 - 50 - (TR6.x - 60), y: chosen.y + 4 - (TR6.y + 110) }, t, T6.cursor, "power2.inOut");
    t += T6.cursor;
    pulse(chosen.x, chosen.y, { w: chosen.w, h: 54, rx: 27 }, th.agent, t);
    to(chosen.lit, { opacity: 1 }, t, S(0.3));
    actions.forEach((b) => { if (b !== chosen) to(b.g, { opacity: 0.35 }, t + S(0.2), S(0.5)); });
    to(curIn, { opacity: 0 }, t + S(0.4), S(0.4));
    t += S(0.5);

    // draft talking point
    const draft = (() => {
      const w = 1060, h = 212;
      const outer = mk("g", { transform: "translate(960 650)" }, g6);
      const g = mk("g", {}, outer);
      const hl = mk("rect", { x: -w / 2 - 5, y: -h / 2 - 5, width: w + 10, height: h + 10, rx: 22, fill: "none", stroke: th.request, "stroke-width": 2, opacity: 0 }, g);
      mk("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 18, fill: "url(#stc-card)", stroke: th.agent, "stroke-opacity": 0.5, "stroke-width": 1.2 }, g);
      const lx = -w / 2 + 34;
      txt(g, cfg.draftTitle, lx, -h / 2 + 30, { size: 12, mono: true, fill: th.agent, anchor: "start", ls: "0.22em" });
      const o = { size: 21, weight: 500 };
      const lines = wrap(cfg.draft, w - 70, o);
      const els = lines.map((l, i) => txt(g, "", lx, -h / 2 + 72 + i * 30, { ...o, anchor: "start" }));
      const ey = -h / 2 + 72 + lines.length * 30 + 6;
      const edit = txt(g, "", lx, ey, { ...o, anchor: "start", fill: th.request });
      const caret = mk("rect", { x: lx - 10, y: ey - 13, width: 3, height: 26, fill: th.request, opacity: 0 }, g);
      const editTag = txt(g, cfg.draftEditTag, w / 2 - 34, -h / 2 + 30, { size: 11, mono: true, fill: th.request, anchor: "end", ls: "0.2em" });
      const ok = mk("g", { transform: `translate(${w / 2 - 34} ${h / 2 - 28})` }, g);
      const okW = measure("APPROVED", { size: 11.5, mono: true, ls: "0.2em" }) + 50;
      mk("rect", { x: -okW, y: -15, width: okW, height: 30, rx: 15, fill: th.positive, "fill-opacity": 0.12, stroke: th.positive, "stroke-width": 1.2 }, ok);
      mk("path", { d: `M ${-okW + 14} 0 l 5 5 l 9 -10`, stroke: th.positive, "stroke-width": 2, fill: "none", "stroke-linecap": "round", "stroke-linejoin": "round" }, ok);
      txt(ok, "APPROVED", -okW + 34, 0, { size: 11.5, mono: true, fill: th.positive, anchor: "start", ls: "0.2em" });
      [editTag, ok].forEach((e) => init(e, { opacity: 0 }));
      init(g, { opacity: 0, y: 14 });
      return { g, hl, els, lines, edit, caret, editTag, ok, h };
    })();
    to(draft.g, { opacity: 1, y: 0 }, t, S(0.6), "power3.out");
    typeLines(draft.els, draft.lines, t + S(0.3), T6.draftTyping);
    t += S(0.3) + T6.draftTyping + S(0.3);

    // the human steps
    const steps = (() => {
      const g = mk("g", {}, g6);
      const o = { size: 14, mono: true, ls: "0.22em" };
      const gap = 80;
      const ws = cfg.humanSteps.map((s) => measure(s, o) + 22);
      const total = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
      let x = 960 - total / 2;
      const y = 830;
      const items = cfg.humanSteps.map((s, i) => {
        const dim = mk("g", {}, g);
        mk("circle", { cx: x + 5, cy: y, r: 4, fill: th.faint }, dim);
        txt(dim, s, x + 22, y, { ...o, anchor: "start", fill: th.faint });
        const lit = mk("g", {}, g);
        mk("circle", { cx: x + 5, cy: y, r: 4, fill: th.request }, lit);
        txt(lit, s, x + 22, y, { ...o, anchor: "start", fill: th.request });
        init(lit, { opacity: 0 });
        if (i < ws.length - 1) {
          const ax = x + ws[i] + gap / 2;
          mk("path", { d: `M ${ax - 12} ${y} L ${ax + 8} ${y} M ${ax + 3} ${y - 5} L ${ax + 8} ${y} L ${ax + 3} ${y + 5}`, stroke: th.faint, "stroke-width": 1.4, fill: "none" }, g);
        }
        x += ws[i] + gap;
        return lit;
      });
      const head = txt(g, cfg.trader.label + "  ·  IN CONTROL", 960, y - 40, { size: 11.5, mono: true, fill: th.muted, ls: "0.26em" });
      init(g, { opacity: 0 });
      return { g, items, head };
    })();
    to(steps.g, { opacity: 1 }, t, S(0.5));
    // reviews
    to(steps.items[0], { opacity: 1 }, t, S(0.4));
    win(t, S(0.3), T6.stepGap * 0.8, S(0.4), (a) => draft.hl.setAttribute("opacity", a * 0.8));
    t += T6.stepGap;
    // edits
    to(steps.items[1], { opacity: 1 }, t, S(0.4));
    to(draft.editTag, { opacity: 1 }, t, S(0.4));
    fx(t, S(1.6), (v) => draft.caret.setAttribute("opacity", v > 0 && v < 1 ? (Math.floor(v * 8) % 2 ? 0.2 : 1) : 0));
    typeLines([draft.edit], [cfg.draftEdit], t + S(0.2), S(1.3));
    t += S(1.5);
    // decides
    to(steps.items[2], { opacity: 1 }, t, S(0.4));
    to(draft.ok, { opacity: 1 }, t, S(0.4), "power3.out");
    pulse(960 + 530 - 34 - 60, 650 + draft.h / 2 - 28, { w: 120, h: 30, rx: 15 }, th.positive, t);
    t += T6.stepGap;
    // communicates — the Sales Trader, not the AI, contacts the client
    to(steps.items[3], { opacity: 1 }, t, S(0.4));
    const CA = { x: TR6.x, y: 640 };
    const clientA = person(g6, CA.x, CA.y, cfg.clientAlpha.label, cfg.clientAlpha.sub, th.positive, "building");
    init(clientA.g, { opacity: 0, scale: 0.9, transformOrigin: "50% 50%" });
    to(clientA.g, { opacity: 1, scale: 1 }, t - S(0.3), S(0.5), "power3.out");
    const callLine = mk("path", { d: `M ${TR6.x} ${TR6.y + 128} L ${CA.x} ${CA.y - 52}`, stroke: th.request, "stroke-opacity": 0.5, "stroke-width": 1.3, fill: "none" }, g6);
    drawIn(callLine, t, S(0.6));
    comet(`M ${TR6.x} ${TR6.y + 128} L ${CA.x} ${CA.y - 52}`, th.request, t + S(0.1), S(0.8), { tail: 110 });
    pulseAt(CA.x, CA.y, { r: 46 }, th.positive, t + S(0.9));
    glowWin(clientA, t + S(0.9), S(1.8));
    t += S(1.0);
    t = caption(cfg.captions.s6, t, T6.hold, { size: 30, fills: [th.agent, th.text], y: 960 });
    eyebrow(5, S6, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  SCENE 7 — The amplification
    // ═════════════════════════════════════════════════════════════════════════
    const T7 = TM.s7;
    const S7 = t;
    to(g6, { opacity: 0 }, t, S(0.7));
    to(trader.g, { opacity: 0 }, t, S(0.7));
    to(cop.g, { opacity: 0 }, t, S(0.7));
    to(copHalo, { opacity: 0 }, t, S(0.7));
    to(phaseBar.g, { opacity: 0 }, t, S(0.7));
    t += S(0.6);
    const g7 = sceneG();
    init(g7, { opacity: 1 });
    const divider = mk("line", { x1: 960, y1: 200, x2: 960, y2: 870, stroke: th.line }, g7);
    init(divider, { opacity: 0 });
    const beforeTitle = txt(g7, cfg.before.title, 500, 170, { size: 14, mono: true, fill: th.muted, ls: "0.3em" });
    const afterTitle = txt(g7, cfg.after.title, 1420, 170, { size: 14, mono: true, fill: th.agent, ls: "0.3em" });
    [beforeTitle, afterTitle].forEach((e) => init(e, { opacity: 0 }));

    // BEFORE — a long manual chain
    const bTrader = pill(g7, cfg.trader.label, 500, 250, { size: 12.5, color: th.request, textFill: th.request, h: 42 });
    const bSteps = cfg.before.steps.map((s, i) => {
      const x = i % 2 === 0 ? 380 : 620, y = 350 + i * 90;
      const p = pill(g7, s, x, y, { size: 12, color: th.line, textFill: th.muted, h: 40 });
      return p;
    });
    const bPathD = `M 500 271 ` + bSteps.map((p) => `L ${p.x} ${p.y}`).join(" ");
    const bPath = mk("path", { d: bPathD, stroke: th.public, "stroke-opacity": 0.3, "stroke-width": 1.2, fill: "none", "stroke-dasharray": "3 6" }, g7);
    g7.insertBefore(bPath, g7.firstChild);
    [bTrader, ...bSteps].forEach((p) => init(p.g, { opacity: 0, y: 8 }));
    init(bPath, { opacity: 0 });

    // WITH — trader → copilot → MCP → briefing
    const aTrader = pill(g7, cfg.trader.label, 1420, 250, { size: 12.5, color: th.request, textFill: th.request, h: 42 });
    const aCop = card(g7, { x: 1420, y: 370, w: 380, h: 84, r: 22, label: cfg.copilot.label, glyph: "spark", color: th.agent, size: 15 });
    const band = (() => {
      const g = mk("g", {}, g7);
      const w = 640, y = 520;
      mk("rect", { x: 1420 - w / 2, y: y - 24, width: w, height: 48, rx: 24, fill: "url(#stc-mcp-h)", stroke: th.mcp, "stroke-opacity": 0.7, "stroke-width": 1.3 }, g);
      txt(g, cfg.after.mcpLabel, 1420, y - 48, { size: 11, mono: true, fill: th.mcp, ls: "0.26em" });
      const n = cfg.after.mcpItems.length;
      const xs = cfg.after.mcpItems.map((_, i) => 1420 + (i - (n - 1) / 2) * 124);
      cfg.after.mcpItems.forEach((m, i) => {
        mk("rect", { x: xs[i] - 6, y: y - 6, width: 12, height: 12, rx: 3, fill: th.bg, stroke: th.mcp, "stroke-width": 1.3 }, g);
        txt(g, m, xs[i], y + 46, { size: 11, mono: true, fill: th.muted, ls: "0.16em" });
      });
      return { g, xs, y };
    })();
    const aBrief = card(g7, { x: 1420, y: 690, w: 440, h: 76, r: 18, label: cfg.after.result, glyph: "doc", color: th.positive, size: 14 });
    const aLinks = mk("g", {}, g7);
    g7.insertBefore(aLinks, g7.firstChild);
    [[1420, 271, 1420, 328], [1420, 412, 1420, 496], [1420, 544, 1420, 652]].forEach(([x1, y1, x2, y2]) =>
      mk("line", { x1, y1, x2, y2, stroke: th.agent, "stroke-opacity": 0.4, "stroke-width": 1.2 }, aLinks));
    band.xs.forEach((x) => mk("path", { d: `M 1420 412 C 1420 460, ${x} 460, ${x} 514`, stroke: th.mcp, "stroke-opacity": 0.35, "stroke-width": 1.1, fill: "none" }, aLinks));
    [aTrader.g, aCop.g, band.g, aBrief.g].forEach((e) => init(e, { opacity: 0, y: 8 }));
    init(aLinks, { opacity: 0 });

    let t7 = t;
    to(divider, { opacity: 1 }, t7, S(0.6));
    to(beforeTitle, { opacity: 1 }, t7, S(0.6));
    to(afterTitle, { opacity: 1 }, t7 + S(0.2), S(0.6));
    to(bPath, { opacity: 1 }, t7 + S(0.3), S(0.6));
    [bTrader, ...bSteps].forEach((p, i) => to(p.g, { opacity: 1, y: 0 }, t7 + S(0.2) + i * S(0.12), S(0.5), "power3.out"));
    [aTrader.g, aCop.g, band.g, aBrief.g].forEach((e, i) => to(e, { opacity: 1, y: 0 }, t7 + S(0.5) + i * S(0.15), S(0.5), "power3.out"));
    to(aLinks, { opacity: 1 }, t7 + S(0.8), S(0.6));
    t7 += S(1.4);
    comet(bPathD, th.public, t7, T7.slow, { tail: 160, ease: "none", scale: 0.8 });
    bSteps.forEach((p, i) => pulse(p.x, p.y, { w: p.w, h: 40, rx: 20 }, th.public, t7 + ((i + 1) / (bSteps.length + 0.3)) * T7.slow * 0.97, 0.7));
    const fastD = (x) => `M 1420 271 L 1420 370 C 1420 460, ${x} 460, ${x} 520 C ${x} 600, 1420 600, 1420 652`;
    band.xs.forEach((x, i) => comet(fastD(x), th.mcp, t7 + i * S(0.12), T7.fast, { tail: 120, scale: 0.75 }));
    pulseAt(1420, 690, { w: 440, h: 76, r: 18 }, th.positive, t7 + T7.fast + S(0.5));
    glowWin(aBrief, t7 + T7.fast + S(0.4), T7.slow - T7.fast);
    caption(cfg.captions.s7Compress, t7 + S(0.6), T7.slow + T7.compareHold - S(1.6), { size: 28 });
    t7 += T7.slow + T7.compareHold - S(0.4);
    to(g7, { opacity: 0 }, t7, S(0.7));
    t7 += S(0.7);

    // FROM → TO
    const g7b = sceneG();
    const ftHead = mk("g", {}, g7b);
    txt(ftHead, "FROM", 880, 300, { size: 13, mono: true, fill: th.muted, anchor: "end", ls: "0.3em" });
    txt(ftHead, "TO", 1040, 300, { size: 13, mono: true, fill: th.agent, anchor: "start", ls: "0.3em" });
    init(ftHead, { opacity: 0 });
    const ftRows = cfg.fromTo.map(([a, b], i) => {
      const y = 390 + i * 112;
      const from = txt(g7b, a, 880, y, { size: 32, weight: 500, fill: th.muted, anchor: "end" });
      const tt = txt(g7b, b, 1040, y, { size: 32, weight: 600, anchor: "start" });
      const bar = mk("rect", { x: 1040, y: y + 26, width: measure(b, { size: 32, weight: 600 }), height: 2, rx: 1, fill: th.agent }, g7b);
      const arrow = mk("path", { d: `M 912 ${y} L 1004 ${y} M 994 ${y - 7} L 1004 ${y} L 994 ${y + 7}`, stroke: th.agent, "stroke-width": 1.6, fill: "none", "stroke-linecap": "round" }, g7b);
      init(from, { opacity: 0, x: 12 });
      init(tt, { opacity: 0, x: -12 });
      init(bar, { scaleX: 0, transformOrigin: "0% 50%" });
      init(arrow, { opacity: 0 });
      return { from, tt, bar, arrow, y };
    });
    to(ftHead, { opacity: 1 }, t7, S(0.5));
    ftRows.forEach((r, i) => {
      const ta = t7 + S(0.3) + i * T7.rowStagger;
      to(r.from, { opacity: 1, x: 0 }, ta, S(0.5), "power3.out");
      to(r.arrow, { opacity: 1 }, ta + S(0.25), S(0.3));
      comet(`M 912 ${r.y} L 1004 ${r.y}`, th.agent, ta + S(0.2), S(0.45), { tail: 60, scale: 0.6 });
      to(r.tt, { opacity: 1, x: 0 }, ta + S(0.45), S(0.55), "power3.out");
      to(r.bar, { scaleX: 1 }, ta + S(0.6), S(0.6), "power2.out");
    });
    t7 += S(0.3) + ftRows.length * T7.rowStagger + T7.rowsHold;
    to(g7b, { opacity: 0 }, t7, S(0.7));
    t = t7 + S(0.6);
    eyebrow(6, S7, t);

    // ═════════════════════════════════════════════════════════════════════════
    //  FINAL — what it means
    // ═════════════════════════════════════════════════════════════════════════
    const T8 = TM.final;
    const S8 = t;
    const g8 = sceneG();
    const big = (() => {
      const outer = mk("g", { transform: "translate(960 520)" }, g8);
      const g = mk("g", {}, outer);
      const s = `${cfg.event.name} ${cfg.event.move}`;
      const o = { size: 110, weight: 700, ls: "-0.01em" };
      const w = measure(s, o);
      txt(g, cfg.event.name + " ", -w / 2, 0, { ...o, anchor: "start" });
      txt(g, cfg.event.move, w / 2, 0, { ...o, anchor: "end", fill: th.positive });
      const strike = mk("path", { d: `M ${-w / 2 - 30} 8 L ${w / 2 + 30} -4`, stroke: th.warn, "stroke-width": 7, "stroke-linecap": "round", fill: "none" }, g);
      init(g, { opacity: 0, scale: 0.94, transformOrigin: "50% 50%" });
      return { g, strike };
    })();
    let t8 = t + S(0.3);
    to(big.g, { opacity: 1, scale: 1 }, t8, S(0.9), "power3.out");
    t8 += S(0.9) + T8.strikeHold;
    drawIn(big.strike, t8, S(0.6), "power2.out");
    t8 += S(0.8);
    to(big.g, { opacity: 0.3, scale: 0.42, y: -300 }, t8, S(0.9));
    t8 += S(0.6);
    const fq = cfg.finalQuestions.map((q, i) => {
      const e = txt(g8, q, 960, 420 + i * 92, { size: 42, weight: 600, accent: th.request, ls: "-0.01em" });
      init(e, { opacity: 0, y: 14 });
      return e;
    });
    fq.forEach((e, i) => to(e, { opacity: 1, y: 0 }, t8 + i * T8.questionStagger, S(0.7), "power3.out"));
    t8 += fq.length * T8.questionStagger + T8.questionsHold;
    to(g8, { opacity: 0 }, t8, S(0.7));
    t8 += S(0.8);

    const g9 = sceneG();
    const fTitle = txt(g9, cfg.finalTitle, 960, 150, { size: 50, weight: 700, ls: "0.2em" });
    const fSub = txt(g9, cfg.finalSubtitle, 960, 212, { size: 24, weight: 500, fill: th.muted });
    init(fTitle, { opacity: 0, y: 12 });
    init(fSub, { opacity: 0, y: 10 });
    // inputs row
    const inO = { size: 13, mono: true, ls: "0.18em" };
    const inWs = cfg.finalInputs.map((s) => measure(s, inO) + 44);
    const plusGap = 54;
    const inTotal = inWs.reduce((a, b) => a + b, 0) + plusGap * (inWs.length - 1);
    let ix = 960 - inTotal / 2;
    const IN_Y = 340;
    const inputs = cfg.finalInputs.map((s, i) => {
      const x = ix + inWs[i] / 2;
      const p = pill(g9, s, x, IN_Y, { size: 13, color: [th.public, th.data, th.mcp, th.request][i % 4], strokeOpacity: 0.7, h: 46 });
      if (i < inWs.length - 1) {
        const px = ix + inWs[i] + plusGap / 2;
        const plus = txt(g9, "+", px, IN_Y, { size: 24, weight: 500, fill: th.muted });
        init(plus, { opacity: 0 });
        p.plus = plus;
      }
      ix += inWs[i] + plusGap;
      init(p.g, { opacity: 0, y: 10 });
      return p;
    });
    const flowColors = [th.agent, th.request, th.positive];
    const flowYs = [480, 610, 740];
    const flow = cfg.finalFlow.map((s, i) => {
      const w = Math.max(300, measure(s, { size: 15, weight: 600, ls: "0.16em" }) + 90);
      const n = card(g9, { x: 960, y: flowYs[i], w, h: 70, r: 20, label: s, glyph: i === 0 ? "spark" : i === 1 ? "person" : "building", color: flowColors[i], size: 15 });
      init(n.g, { opacity: 0, y: 10 });
      return n;
    });
    const fLinks = mk("g", {}, g9);
    g9.insertBefore(fLinks, g9.firstChild);
    const inD = inputs.map((p) => `M ${p.x} ${IN_Y + 23} C ${p.x} ${IN_Y + 80}, 960 ${flowYs[0] - 90}, 960 ${flowYs[0] - 35}`);
    inD.forEach((d) => mk("path", { d, stroke: th.agent, "stroke-opacity": 0.3, "stroke-width": 1.2, fill: "none" }, fLinks));
    mk("line", { x1: 960, y1: flowYs[0] + 35, x2: 960, y2: flowYs[2] - 35, stroke: th.request, "stroke-opacity": 0.35, "stroke-width": 1.2 }, fLinks);
    init(fLinks, { opacity: 0 });

    to(fTitle, { opacity: 1, y: 0 }, t8, S(0.9), "power3.out");
    to(fSub, { opacity: 1, y: 0 }, t8 + S(0.5), S(0.9), "power3.out");
    t8 += S(1.0);
    inputs.forEach((p, i) => {
      to(p.g, { opacity: 1, y: 0 }, t8 + i * T8.flowStagger, S(0.5), "power3.out");
      if (p.plus) to(p.plus, { opacity: 1 }, t8 + (i + 0.5) * T8.flowStagger, S(0.4));
    });
    t8 += inputs.length * T8.flowStagger;
    to(fLinks, { opacity: 1 }, t8, S(0.6));
    inD.forEach((d, i) => comet(d, th.agent, t8 + i * S(0.08), S(0.9), { tail: 110, scale: 0.75 }));
    flow.forEach((n, i) => {
      const ta = t8 + S(0.6) + i * S(0.75);
      to(n.g, { opacity: 1, y: 0 }, ta, S(0.55), "power3.out");
      glowWin(n, ta + S(0.2), S(0.5));
      if (i > 0) comet(`M 960 ${flowYs[i - 1] + 35} L 960 ${flowYs[i] - 35}`, flowColors[i], ta - S(0.35), S(0.5), { tail: 70, scale: 0.7 });
    });
    t8 += S(0.6) + flow.length * S(0.75) + S(0.4);
    // final message
    const msg = mk("g", {}, L.screen);
    const m1 = txt(msg, cfg.finalMessage[0], 960, 880, { size: 31, weight: 500, fill: th.text });
    const m2 = txt(msg, cfg.finalMessage[1], 960, 926, { size: 31, weight: 600, fill: th.text, accent: th.mcp });
    init(m1, { opacity: 0, y: 12 });
    init(m2, { opacity: 0, y: 12 });
    to(m1, { opacity: 1, y: 0 }, t8, S(0.9), "power3.out");
    to(m2, { opacity: 1, y: 0 }, t8 + S(1.1), S(0.9), "power3.out");
    // a last, slow pulse through the whole chain
    const chainD = `M 960 ${IN_Y + 23} L 960 ${flowYs[2] - 35}`;
    comet(chainD, th.mcp, t8 + S(1.6), S(1.6), { tail: 160, scale: 0.8 });
    glowWin(flow[2], t8 + S(3.0), T8.messageHold - S(2.6));
    t8 += S(1.1) + T8.messageHold;
    t = t8;
    eyebrow(7, S8, t);

    // ── Ambient motion (a pure function of time) ─────────────────────────────
    const total = t;
    const amb = { t: 0 };
    function ambient(tt) {
      copHaloC.setAttribute("opacity", 0.75 + 0.25 * Math.sin(tt * 1.7));
      spin.setAttribute("stroke-dashoffset", -tt * 260);
      mcpBar.bus.setAttribute("stroke-dashoffset", -tt * 30);
      const on = tt > screensVis[0] && tt < screensVis[1];
      if (on) screens.forEach((s) => s.dot.setAttribute("opacity", Math.sin(tt * 5 + s.phase * 7) > 0 ? 1 : 0.15));
    }
    tl.fromTo(amb, { t: 0 }, { t: total, duration: total, ease: "none", immediateRender: false, onUpdate: () => ambient(amb.t) }, 0);
    ambient(0);
    tl.seek(0, false);

    return {
      timeline: tl,
      duration: tl.duration(),
      scenes: sceneMarks.sort((a, b) => a.time - b.time),
      svg,
      seek: (time) => tl.seek(time, false),
    };
  }

  window.UseCaseDemo = { mount };
})();
