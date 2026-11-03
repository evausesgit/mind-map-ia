"""Generate concept slides (frozen diagram + glossary) from data/slides/*.yaml.

Two layouts share the same CSS and glossary behaviour: the default hub diagram
(one language), and `layout: routing`, the on-prem / cloud frame of the Trusted
Data animation (bilingual, with one <main> per language).

Usage (from repo root):
    python scripts/generate_concept_slide.py [data/slides/agent-anatomy.yaml ...]

With no argument, every file in data/slides/ is generated.
"""
import html
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
        rows.append(
            f'    <li><button class="term" data-n="{esc(t["node"])}" style="--tone:{tone}">'
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


def main() -> None:
    paths = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((ROOT / "data" / "slides").glob("*.yaml"))
    for path in paths:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        out = ROOT / spec["output"]
        page = render_routing(spec) if spec.get("layout") == "routing" else render(spec)
        out.write_text(page, encoding="utf-8")
        print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
