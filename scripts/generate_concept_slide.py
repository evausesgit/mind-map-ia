"""Generate concept slides (frozen diagram + glossary) from data/slides/*.yaml.

Three layouts share the same CSS and glossary behaviour: the default hub diagram
(one language), `layout: routing`, the on-prem / cloud frame of the Trusted
Data animation, and `layout: shift`, the chatbot-versus-agent introduction
(both bilingual, with one <main> per language).

`layout: intro` is for talk openings: a full-screen bilingual diagram with no
glossary, revealed step by step (arrow keys, remote clicker or click), drawn
from scripts/templates/intro-<diagram>.svg (`diagram: timeline` for now).

Usage (from repo root):
    python scripts/generate_concept_slide.py [data/slides/agent-anatomy.yaml ...]

With no argument, every file in data/slides/ is generated.
"""
import html
import math
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "scripts" / "templates"
TEMPLATE = TEMPLATES / "concept-slide.html"
CSS = (TEMPLATES / "concept-slide.css").read_text(encoding="utf-8")
JS = (TEMPLATES / "concept-slide.js").read_text(encoding="utf-8")

# Top-left corner of each block card, then its spoke (card corner -> ring).
SLOTS = [
    {"x": 155, "y": 108, "spoke": "M345 186 L364 314"},
    {"x": 695, "y": 108, "spoke": "M695 186 L676 314"},
    {"x": 155, "y": 748, "spoke": "M345 754 L364 626"},
    {"x": 695, "y": 748, "spoke": "M695 754 L676 626"},
]
CENTER_X = 520
CHAR_WIDTH = 15  # approximate width of a centre label letter, spacing included
BLOCK_CHAR_WIDTH = 13  # same, for block labels


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def block_svg(block: dict, slot: dict) -> str:
    x, y = slot["x"], slot["y"]
    sub = block.get("sub")
    mid = y + (32 if sub else 42)
    left = x + (190 - (24 + len(block["label"]) * BLOCK_CHAR_WIDTH)) // 2
    parts = [
        f'<g class="n" data-n="{esc(block["id"])}" style="--tone:var(--orchestrator)">',
        f'<rect class="base" x="{x}" y="{y}" width="190" height="84" rx="14"/>',
        f'<use href="#{esc(block["glyph"])}" x="{left + 9}" y="{mid}" stroke="#A594FF"/>',
        f'<text x="{left + 33}" y="{mid + 6}">{esc(block["label"])}</text>',
    ]
    if sub:
        parts.append(
            f'<text x="{x + 95}" y="{y + 64}" text-anchor="middle" font-family="\'JetBrains Mono\', monospace" '
            f'font-size="12.5" font-weight="400" letter-spacing=".6" fill="#8B94A5">{esc(sub)}</text>'
        )
    parts.append("</g>")
    return "".join(parts)


def wires_svg(blocks: list) -> str:
    lines = ['<g fill="none" stroke="#A594FF" stroke-opacity=".5" stroke-width="1.3">']
    for block, slot in zip(blocks, SLOTS):
        lines.append(f'<path class="wire" data-n="{esc(block["id"])}" d="{slot["spoke"]}"/>')
    lines.append("</g>")
    lines.append('<path class="wire" data-n="side" d="M740 470 H1006" stroke="#3DD6C6" stroke-opacity=".65" stroke-width="1.3"/>')
    for block, slot in zip(blocks, SLOTS):
        if block.get("via_side"):
            lines.append(
                f'<path class="wire" data-n="{esc(block["id"])} side" d="M885 {slot["y"] + 42} H1006" '
                'stroke="#3DD6C6" stroke-opacity=".8" stroke-width="1.3" stroke-dasharray="5 6"/>'
            )
    return "\n  ".join(lines)


def glossary_html(terms: list) -> str:
    rows = []
    for t in terms:
        tone = t.get("tone") or ("var(--mcp)" if t["node"] == "side" else "var(--orchestrator)")
        cls = "term minor" if t.get("secondary") else "term"
        rows.append(
            f'    <li><button class="{cls}" data-n="{esc(t["node"])}" style="--tone:{tone}">'
            f'<b>{esc(t["term"])}</b><span>{esc(t["text"])}</span></button></li>'
        )
    return "\n".join(rows)


def render(spec: dict) -> str:
    blocks = spec["blocks"]
    if len(blocks) != len(SLOTS):
        raise ValueError(f"{spec['output']}: needs exactly {len(SLOTS)} blocks, got {len(blocks)}")
    nodes = {"center", "ring", "side", *(b["id"] for b in blocks)}
    for term in spec["glossary"]:
        if term["node"] not in nodes:
            raise ValueError(f"{term['term']}: unknown node {term['node']!r}")

    center_width = max(272, len(spec["center"]) * CHAR_WIDTH + 110)
    center_left = CENTER_X - center_width // 2
    values = {
        "title": spec["title"], "aria": spec["aria"], "eyebrow": spec["eyebrow"],
        "back_href": spec["back"]["href"], "back_label": spec["back"]["label"],
        "user": spec["user"], "center": spec["center"], "ring": spec["ring"],
        "side_title": spec["side"]["title"], "side_subtitle": spec["side"]["subtitle"],
        "side_reaches": spec["side"]["reaches"],
        "question": spec["question"], "takeaway": spec["takeaway"],
        # Optional, for a slide in another language than English.
        "lang": spec.get("lang", "en"), "home_label": spec.get("home_label", "Home"),
        "glossary_label": spec.get("glossary_label", "Glossary"),
        "glossary_title": spec.get("glossary_title", "Key vocabulary"),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", esc(value))
    raw = {
        "center_left": center_left, "center_width": center_width,
        "center_icon": center_left + 44, "center_text": center_left + 72,
        "wires": wires_svg(blocks),
        "blocks": "\n    ".join(block_svg(b, s) for b, s in zip(blocks, SLOTS)),
        "glossary": glossary_html(spec["glossary"]),
        "css": CSS, "js": JS,
    }
    for key, value in raw.items():
        page = page.replace("{{" + key + "}}", str(value))
    return page


def fill(page: str, values: dict, raw: dict) -> str:
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", esc(value))
    for key, value in raw.items():
        page = page.replace("{{" + key + "}}", str(value))
    return page


def routing_card(card: dict) -> str:
    x, y, cx = card["x"], card["y"], card["x"] + card["w"] // 2
    color = card["color"]
    sub = ""
    if card.get("sub"):
        sub = (
            f'<text class="mono" x="{cx}" y="{y + 80}" text-anchor="middle" font-size="12" '
            f'fill="#8B94A5">{esc(card["sub"])}</text>'
        )
    return (
        f'<g class="n" data-n="{esc(card["nodes"])}" style="--tone:{color}">'
        f'<rect class="base" x="{x}" y="{y}" width="{card["w"]}" height="96" rx="14"/>'
        f'<use href="#{card["glyph"]}" x="{cx}" y="{y + 28}" color="{color}"/>'
        f'<text x="{cx}" y="{y + 60}" text-anchor="middle" font-size="14.5" font-weight="600" '
        f'letter-spacing="1.6" fill="#EEF2F7">{esc(card["label"])}</text>{sub}</g>'
    )


def routing_levels(rows: list) -> str:
    colors = {"C3": "#F27A7A", "C2": "#F5A55A", "C1": "#34D399"}
    parts = []
    for i, row in enumerate(rows):
        y, color = 702 + i * 54, colors[row["level"]]
        parts.append(
            f'<circle cx="78" cy="{y - 5}" r="6" fill="{color}"/>'
            f'<text class="mono" x="94" y="{y}" font-size="14" font-weight="500" fill="{color}">{row["level"]}</text>'
            f'<text x="128" y="{y}" font-size="15" font-weight="600" fill="#EEF2F7">{esc(row["name"])}</text>'
            f'<text x="128" y="{y + 20}" font-size="13.5" fill="#8B94A5">{esc(row["data"])}</text>'
            f'<text class="mono" x="750" y="{y}" text-anchor="end" font-size="13" fill="{color}">→ {esc(row["route"])}</text>'
        )
    return "\n    ".join(parts)


def routing_sees(rows: list) -> str:
    parts = []
    for i, row in enumerate(rows):
        y = 542 + i * 60
        color, mark = ("#34D399", "✓") if row["seen"] else ("#F27A7A", "✕")
        parts.append(
            f'<text class="mono" x="888" y="{y}" font-size="15" fill="{color}">{mark}</text>'
            f'<text x="914" y="{y}" font-size="15" font-weight="600" fill="#EEF2F7">{esc(row["label"])}</text>'
            f'<text x="914" y="{y + 20}" font-size="13" fill="#8B94A5">{esc(row["note"])}</text>'
        )
    return "\n    ".join(parts)


def routing_main(lang: str, s: dict) -> str:
    stay_w = len(s["stay"]) * 8 + 24
    cards = [
        {"x": 52, "y": 332, "w": 150, "label": s["agent"], "glyph": "i-spark", "color": "#7EA6FF", "nodes": "agent"},
        {"x": 250, "y": 332, "w": 240, "label": s["gateway"], "sub": s["gateway_sub"], "glyph": "i-route",
         "color": "#3DD6C6", "nodes": "gateway"},
        {"x": 556, "y": 214, "w": 200, "label": s["anon"], "glyph": "i-mask", "color": "#F5A55A", "nodes": "anon"},
        {"x": 556, "y": 470, "w": 200, "label": s["gpu"], "sub": s["gpu_sub"], "glyph": "i-chip",
         "color": "#7EA6FF", "nodes": "openweights onprem inference"},
        {"x": 872, "y": 290, "w": 256, "label": s["frontier"], "sub": s["frontier_sub"], "glyph": "i-hex",
         "color": "#A594FF", "nodes": "frontier inference endpoint zdr"},
    ]
    strings = ("aria", "eyebrow", "perimeter", "cloud", "stay", "levels_title", "sees_title", "link", "question", "takeaway")
    svg = fill(
        (TEMPLATES / "routing-diagram.svg").read_text(encoding="utf-8"),
        {key: s[key] for key in strings},
        {
            "stay_x": 656 - stay_w // 2, "stay_w": stay_w,
            "cards": "\n  ".join(routing_card(c) for c in cards),
            "levels": routing_levels(s["levels"]),
            "sees": routing_sees(s["sees"]),
        },
    )
    return slide_main(lang, s, svg)


def slide_main(lang: str, s: dict, svg: str) -> str:
    """One language's <main>: the diagram, then its glossary (every term must point at a node)."""
    nodes = {n for attr in re.findall(r'data-n="([^"]+)"', svg) for n in attr.split()}
    for term in s["glossary"]:
        if term["node"] not in nodes:
            raise ValueError(f"{term['term']}: unknown node {term['node']!r}")
    return (
        f'<main class="slide" data-lang="{lang}">\n{svg}\n'
        f'<section class="glossary" aria-label="{esc(s["glossary_title"])}">\n'
        f'  <h1>{esc(s["glossary_title"])}</h1>\n  <ul>\n{glossary_html(s["glossary"])}\n  </ul>\n</section>\n</main>'
    )


def render_routing(spec: dict) -> str:
    return fill(
        (TEMPLATES / "routing-slide.html").read_text(encoding="utf-8"),
        {"title": spec["en"]["title"], "back_href": spec["back"], "back": spec["back_label"]},
        {"css": CSS, "js": JS, "slides": "\n".join(routing_main(lang, spec[lang]) for lang in ("en", "fr"))},
    )


def shift_rows(rows: list, x: int) -> str:
    parts = []
    for i, row in enumerate(rows):
        y = 452 + i * 54
        if i:
            parts.append(f'<path d="M{x} {y - 22} H{x + 497}" stroke="rgba(255,255,255,.08)"/>')
        parts.append(
            f'<text class="mono" x="{x}" y="{y}" font-size="11.5" letter-spacing="1.8" fill="#8B94A5">{esc(row["k"])}</text>'
            f'<text x="{x}" y="{y + 21}" font-size="15.5" fill="#EEF2F7">{esc(row["v"])}</text>'
        )
    return "\n    ".join(parts)


def shift_loop_arrows(cx: float = 812, cy: float = 323, r: float = 56, size: float = 1, color: str = "#A594FF") -> str:
    """Three clockwise arrowheads on the agent loop, between its three labels."""
    parts = []
    for deg in (-30, 90, 210):
        a = math.radians(deg)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)  # clockwise tangent
        nx, ny = math.cos(a), math.sin(a)   # outward normal
        k = size
        tip = (px + tx * 7 * k, py + ty * 7 * k)
        b1 = (px - tx * 3 * k + nx * 5 * k, py - ty * 3 * k + ny * 5 * k)
        b2 = (px - tx * 3 * k - nx * 5 * k, py - ty * 3 * k - ny * 5 * k)
        pts = " ".join(f"{u:.1f},{v:.1f}" for u, v in (tip, b1, b2))
        parts.append(f'<polygon points="{pts}" fill="{color}"/>')
    return "".join(parts)


def shift_tools(tools: list) -> str:
    parts = []
    for i, label in enumerate(tools):
        y = 266 + i * 38
        parts.append(
            f'<g class="n" data-n="tools mcp" style="--tone:var(--mcp)">'
            f'<rect class="base" x="952" y="{y}" width="176" height="31" rx="15.5"/>'
            f'<text class="mono" x="1040" y="{y + 20}" text-anchor="middle" font-size="12.5" letter-spacing="1.4" '
            f'fill="#EEF2F7">{esc(label)}</text></g>'
        )
    return "\n  ".join(parts)


SHIFT_STEPS = (  # glossary nodes and colour of each autonomy step
    ("chatbot autonomy", "#7EA6FF"),
    ("tools autonomy", "#8FA0FF"),
    ("agent loop autonomy", "#A594FF"),
    ("agent autonomy", "#3DD6C6"),
)


def shift_steps(steps: list) -> str:
    if len(steps) != len(SHIFT_STEPS):
        raise ValueError(f"layout shift needs {len(SHIFT_STEPS)} ladder steps, got {len(steps)}")
    parts = []
    for i, (step, (nodes, color)) in enumerate(zip(steps, SHIFT_STEPS)):
        x = 170 + i * 280
        parts.append(
            f'<g class="n" data-n="{nodes}" style="--tone:{color}">'
            f'<circle cx="{x}" cy="778" r="9" fill="#080B11" stroke="{color}" stroke-width="2"/>'
            f'<circle cx="{x}" cy="778" r="3.5" fill="{color}"/>'
            f'<text x="{x}" y="814" text-anchor="middle" font-size="16" font-weight="600" fill="#EEF2F7">{esc(step["label"])}</text>'
            f'<text class="mono" x="{x}" y="836" text-anchor="middle" font-size="12" fill="{color}">{esc(step["when"])}</text>'
            f'<text x="{x}" y="857" text-anchor="middle" font-size="13.5" fill="#8B94A5">{esc(step["text"])}</text></g>'
        )
    return "\n  ".join(parts)


def shift_main(lang: str, s: dict) -> str:
    req_w = int(len(s["request"]) * 9.4) + 64
    strings = ("aria", "eyebrow", "request", "chatbot_head", "agent_head", "you", "llm", "answer", "human_loop",
               "signoff", "plan", "act", "check", "mcp", "ladder_title", "ladder_left", "ladder_right",
               "question", "takeaway")
    svg = fill(
        (TEMPLATES / "shift-diagram.svg").read_text(encoding="utf-8"),
        {key: s[key] for key in strings},
        {
            "req_x": 590 - req_w // 2, "req_w": req_w,
            "question_size": 30 if len(s["question"]) <= 64 else 27,
            "rows_chatbot": shift_rows(s["chatbot_rows"], 54),
            "rows_agent": shift_rows(s["agent_rows"], 629),
            "loop_arrows": shift_loop_arrows(),
            "tools": shift_tools(s["tools"]),
            "steps": shift_steps(s["steps"]),
        },
    )
    return slide_main(lang, s, svg)


def render_shift(spec: dict) -> str:
    back = "".join(f'<span data-lang="{lang}">{esc(spec[lang]["back_label"])}</span>' for lang in ("en", "fr"))
    return fill(
        (TEMPLATES / "routing-slide.html").read_text(encoding="utf-8"),
        {"title": spec["en"]["title"], "back_href": spec["back"]},
        {"back": back, "css": CSS, "js": JS, "slides": "\n".join(shift_main(lang, spec[lang]) for lang in ("en", "fr"))},
    )


INTRO_X = (260, 620, 980, 1340)  # timeline stations
INTRO_COLORS = ("#7EA6FF", "#8FA0FF", "#A594FF", "#3DD6C6")


def intro_pills(labels: list, x: float, cy: float, w: float, h: float, gap: float, size: float) -> str:
    parts = []
    top = cy - (len(labels) * h + (len(labels) - 1) * gap) / 2
    for i, label in enumerate(labels):
        y = top + i * (h + gap)
        parts.append(
            f'<rect class="card" x="{x}" y="{y:.0f}" width="{w}" height="{h}" rx="{h / 2}" style="stroke:#3DD6C6;stroke-opacity:.55"/>'
            f'<text class="mono" x="{x + w / 2}" y="{y + h / 2 + size * .36:.0f}" text-anchor="middle" font-size="{size}" '
            f'letter-spacing="1.2" fill="#EEF2F7">{esc(label)}</text>'
        )
    return "\n    ".join(parts)


def intro_picto(i: int, cx: int, s: dict, color: str) -> str:
    """The small diagram on each timeline card (centre y = 370)."""
    arrow = f'fill="none" stroke="{color}" stroke-width="2"'
    llm = lambda x, y, w=104: (  # noqa: E731
        f'<rect class="card" x="{x}" y="{y}" width="{w}" height="60" rx="16"/>'
        f'<use href="#i-spark" x="{x + 26}" y="{y + 30}" color="{color}"/>'
        f'<text x="{x + 64}" y="{y + 37}" text-anchor="middle" font-size="19" font-weight="600" fill="#EEF2F7">{esc(s["llm"])}</text>'
    )
    if i == 0:  # you <-> LLM
        return (
            f'<circle class="card" cx="{cx - 72}" cy="370" r="38"/>'
            f'<text x="{cx - 72}" y="376" text-anchor="middle" font-size="16" font-weight="600" fill="#EEF2F7">{esc(s["you"])}</text>'
            + llm(cx + 16, 340)
            + f'<path {arrow} d="M{cx - 28} 356 H{cx + 8} M{cx} 350 L{cx + 8} 356 L{cx} 362"/>'
            f'<path {arrow} stroke-dasharray="4 5" d="M{cx + 8} 386 H{cx - 28}"/><path {arrow} d="M{cx - 20} 380 L{cx - 28} 386 L{cx - 20} 392"/>'
        )
    if i == 1:  # LLM <-> documents
        return (
            llm(cx - 124, 340)
            + f'<path {arrow} d="M{cx - 14} 358 H{cx + 34} M{cx + 26} 352 L{cx + 34} 358 L{cx + 26} 364"/>'
            f'<path {arrow} stroke-dasharray="4 5" d="M{cx + 34} 384 H{cx - 14}"/><path {arrow} d="M{cx - 6} 378 L{cx - 14} 384 L{cx - 6} 390"/>'
            f'<use href="#i-db" transform="translate({cx + 78} 366) scale(1.35)" color="{color}"/>'
            f'<text class="mono" x="{cx + 78}" y="428" text-anchor="middle" font-size="13" letter-spacing="1.2" fill="#8B94A5">{esc(s["docs"])}</text>'
        )
    if i == 2:  # agent loop -> tools
        lx = cx - 48
        return (
            f'<circle cx="{lx}" cy="370" r="50" fill="#0B0F16" stroke="{color}" stroke-width="2"/>'
            + shift_loop_arrows(lx, 370, 50, 1.2, color)
            + f'<use href="#i-spark" transform="translate({lx} 356) scale(.9)" color="{color}"/>'
            f'<text x="{lx}" y="390" text-anchor="middle" font-size="16" font-weight="600" fill="#EEF2F7">{esc(s["llm"])}</text>'
            f'<path fill="none" stroke="#3DD6C6" stroke-opacity=".8" stroke-width="1.8" '
            f'd="M{lx + 50} 370 H{cx + 22} M{cx + 22} 370 C{cx + 30} 370 {cx + 30} 336 {cx + 40} 336 M{cx + 22} 370 H{cx + 40} '
            f'M{cx + 22} 370 C{cx + 30} 370 {cx + 30} 404 {cx + 40} 404"/>'
            + intro_pills(s["tools"], cx + 40, 370, 88, 26, 8, 11)
        )
    # agent teams: an orchestrator delegating to three agents
    kids = (cx - 86, cx, cx + 86)
    lines = " ".join(f"M{cx} 350 L{k} 390" for k in kids)
    agents = "".join(
        f'<circle cx="{k}" cy="414" r="26" fill="#0B0F16" stroke="{color}" stroke-width="1.8"/>'
        + shift_loop_arrows(k, 414, 26, .8, color)
        + f'<use href="#i-spark" transform="translate({k} 414) scale(.75)" color="{color}"/>'
        for k in kids
    )
    return (
        f'<path d="{lines}" stroke="{color}" stroke-opacity=".6" stroke-width="1.8"/>'
        f'<circle cx="{cx}" cy="322" r="30" fill="#0B0F16" stroke="{color}" stroke-width="2.2"/>'
        + shift_loop_arrows(cx, 322, 30, .9, color)
        + f'<use href="#i-spark" x="{cx}" y="322" color="{color}"/>' + agents
    )


def intro_stations(s: dict) -> str:
    if len(s["steps"]) != len(INTRO_X):
        raise ValueError(f"layout intro timeline needs {len(INTRO_X)} steps, got {len(s['steps'])}")
    parts = []
    for i, (step, cx, color) in enumerate(zip(s["steps"], INTRO_X, INTRO_COLORS)):
        parts.append(
            f'<g data-step="{i + 1}" style="--tone:{color}">\n'
            f'    <rect class="card" x="{cx - 150}" y="262" width="300" height="208" rx="24"/>\n'
            f'    {intro_picto(i, cx, s, color)}\n'
            f'    <path d="M{cx} 470 V506" stroke="{color}" stroke-opacity=".5" stroke-width="1.6"/>\n'
            f'    <circle cx="{cx}" cy="520" r="10" fill="#05070B" stroke="{color}" stroke-width="2.4"/>\n'
            f'    <text class="mono" x="{cx}" y="574" text-anchor="middle" font-size="17" letter-spacing="1.6" fill="{color}">{esc(step["when"])}</text>\n'
            f'    <text x="{cx}" y="620" text-anchor="middle" font-size="29" font-weight="600" fill="#EEF2F7">{esc(step["label"])}</text>\n'
            f'    <text x="{cx}" y="658" text-anchor="middle" font-size="20" fill="#8B94A5">{esc(step["text"])}</text>\n'
            f'  </g>'
        )
    return "\n  ".join(parts)


def intro_main(lang: str, s: dict, diagram: str) -> str:
    """Intro slides: one diagram, no glossary, revealed step by step while the speaker talks."""
    svg = (TEMPLATES / f"intro-{diagram}.svg").read_text(encoding="utf-8")
    strings = {k: v for k, v in s.items() if isinstance(v, str)}
    raw = {"stations": intro_stations(s), "cursor": ",".join(map(str, INTRO_X))}
    svg = fill(svg, strings, raw)
    left = re.findall(r"\{\{(\w+)\}\}", svg)
    if left:
        raise ValueError(f"intro-{diagram}: missing strings {sorted(set(left))} for {lang}")
    return f'<main class="slide" data-lang="{lang}">\n{svg}\n</main>'


def render_intro(spec: dict) -> str:
    back = "".join(f'<span data-lang="{lang}">{esc(spec[lang]["back_label"])}</span>' for lang in ("en", "fr"))
    return fill(
        (TEMPLATES / "intro-slide.html").read_text(encoding="utf-8"),
        {"title": spec["en"]["title"], "back_href": spec["back"]},
        {"back": back, "slides": "\n".join(intro_main(lang, spec[lang], spec["diagram"]) for lang in ("en", "fr"))},
    )


def main() -> None:
    paths = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((ROOT / "data" / "slides").glob("*.yaml"))
    for path in paths:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        out = ROOT / spec["output"]
        renderers = {"routing": render_routing, "shift": render_shift, "intro": render_intro}
        page = renderers.get(spec.get("layout"), render)(spec)
        out.write_text(page, encoding="utf-8")
        print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
