"""Generate concept slides (frozen diagram + glossary) from data/slides/*.yaml.

Usage (from repo root):
    python scripts/generate_concept_slide.py [data/slides/agent-anatomy.yaml ...]

With no argument, every file in data/slides/ is generated.
"""
import html
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "templates" / "concept-slide.html"

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
        tone = "mcp" if t["node"] == "side" else "orchestrator"
        rows.append(
            f'    <li><button class="term" data-n="{esc(t["node"])}" style="--tone:var(--{tone})">'
            f'<b>{esc(t["term"])}</b><span>{esc(t["text"])}</span></button></li>'
        )
    return "\n".join(rows)


def render(spec: dict) -> str:
    blocks = spec["blocks"]
    if len(blocks) != len(SLOTS):
        raise ValueError(f"{spec['output']}: needs exactly {len(SLOTS)} blocks, got {len(blocks)}")
    nodes = {"center", "side", *(b["id"] for b in blocks)}
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
    }
    for key, value in raw.items():
        page = page.replace("{{" + key + "}}", str(value))
    return page


def main() -> None:
    paths = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((ROOT / "data" / "slides").glob("*.yaml"))
    for path in paths:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        out = ROOT / spec["output"]
        out.write_text(render(spec), encoding="utf-8")
        print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
