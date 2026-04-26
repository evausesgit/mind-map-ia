#!/usr/bin/env python3
"""
Generate a standalone HTML mind map from ecosystem.yaml
Usage: python scripts/generate.py
"""

import re
import yaml
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from global_search import widget_html as gs_widget

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
LAYOUTS_DIR = ROOT / "data" / "layouts"
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
TOPICS_DIR = ROOT / "data" / "topics"


def load_glossary():
    if not GLOSSARY_FILE.exists():
        return []
    with open(GLOSSARY_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("terms", [])

# CLI: python generate.py [input.yaml [output.html]]
DATA_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ecosystem.yaml"
OUTPUT_FILE = (
    Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "web" / "ecosystem.html"
)


def load_maps():
    if MAPS_FILE.exists():
        with open(MAPS_FILE) as f:
            return yaml.safe_load(f).get("maps", [])
    return []


def load_links():
    if MAPS_FILE.exists():
        with open(MAPS_FILE) as f:
            return yaml.safe_load(f).get("links", [])
    return []


def load_topics_meta():
    """Return list of topic frontmatter dicts from data/topics/*.md."""
    if not TOPICS_DIR.exists():
        return []
    topics = []
    for path in sorted(TOPICS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
        if fm_match:
            topics.append(yaml.safe_load(fm_match.group(1)))
    topics.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return topics


# ── Layout constants ──────────────────────────────────────────
# Horizontal layout: Layer 1 (Foundations) on the RIGHT, Layer 5 (Dev Tools) on the LEFT
# Layer 2 has two columns: providers (right) and models (left)
LAYER_X = {1: 1100, 2: 400, 3: -200, 4: -700, 5: -1200}
LAYER_X_PROVIDERS = 750  # providers column, between layer 1 and layer 2 models
NODE_SPACING_Y = 35  # vertical spacing between nodes in the same layer
NODE_WIDTH = 140
NODE_HEIGHT = 44

STATUS_BORDER = {
    "stable": {"width": 2, "style": "solid", "dash": "none"},
    "evolving": {"width": 3, "style": "solid", "dash": "none"},
    "emerging": {"width": 3, "style": "dashed", "dash": "8 4"},
    "deprecated": {"width": 1, "style": "dotted", "dash": "4 4"},
}

STATUS_LABEL_COLOR = {
    "stable": "#27AE60",
    "evolving": "#E67E22",
    "emerging": "#8E44AD",
    "deprecated": "#95A5A6",
}

LAYER_LABELS = {
    1: "LAYER 1 · FOUNDATIONS",
    2: "LAYER 2 · MODELS",
    3: "LAYER 3 · INFRASTRUCTURE & ACCESS",
    4: "LAYER 4 · BUILDING BLOCKS",
    5: "LAYER 5 · DEVELOPER TOOLS",
}

LAYER_BG = {
    1: "#FFFDE7",
    2: "#F3E5F5",
    3: "#ECEFF1",
    4: "#E8F5E9",
    5: "#E3F2FD",
}


DEFAULT_LAYER_LABELS = {
    1: "LAYER 1",
    2: "LAYER 2",
    3: "LAYER 3",
    4: "LAYER 4",
    5: "LAYER 5",
}

LANGS = ["en", "fr"]


def t(field, lang):
    """Extract text from a field that is either a plain string or {en:..., fr:...}."""
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def clean(text):
    # Preserve intentional line breaks, clean whitespace within each line
    lines = text.strip().split("\n")
    return "\n".join(" ".join(line.split()) for line in lines).strip()


def load_layout(data_file):
    """Return {node_id: {x, y}} from a layout JSON file if it exists."""
    stem = Path(data_file).stem  # e.g. "ecosystem-macro"
    layout_file = LAYOUTS_DIR / f"{stem}-layout.json"
    if layout_file.exists():
        with open(layout_file) as f:
            positions = json.load(f)
        print(
            f"  ↳ Using saved layout: {layout_file.name} ({len(positions)} positions)"
        )
        return positions
    return {}


def build_elements(data, data_file=None):
    category_colors = {c["id"]: c["color"] for c in data["categories"]}
    saved_layout = load_layout(data_file if data_file is not None else DATA_FILE)
    scale = float(data.get("meta", {}).get("node_scale", 1))
    spacing_y = int(NODE_SPACING_Y * scale)
    ltr = data.get("meta", {}).get("layout_direction", "rtl") == "ltr"
    col_scale = float(data.get("meta", {}).get("column_scale", 1.0))
    raw_layers = data.get("layers", DEFAULT_LAYER_LABELS)
    layer_labels = {}
    for k, v in raw_layers.items():
        layer_labels[int(k)] = v  # v may be a string or {en:..., fr:...}

    # Group nodes by layer
    by_layer = {}
    for node in data["nodes"]:
        by_layer.setdefault(node["layer"], []).append(node)

    elements = []

    def make_node_data(node, layer_id):
        nd = {
            "id": node["id"],
            "label": t(node.get("label", ""), "en"),  # default lang
            "category": node["category"],
            "subcategory": node.get("subcategory", ""),
            "node_type": node.get("node_type", ""),
            "layer": node["layer"],
            "status": node.get("status", "stable"),
            "since": str(node.get("since", "")),
            "link": node.get("link", ""),
            "ref": node.get("ref", ""),
            "drilldown": node.get("drilldown", ""),
            "color": category_colors.get(node["category"], "#BDC3C7"),
            "layerLabel": t(
                layer_labels.get(layer_id, f"Layer {layer_id}"), "en"
            ),
        }
        if node.get("parent"):
            nd["parent"] = node["parent"]
        for lang in LANGS:
            nd[f"label_{lang}"] = t(node.get("label", ""), lang)
            nd[f"description_{lang}"] = clean(
                t(node.get("description", ""), lang)
            )
            nd[f"layerLabel_{lang}"] = t(
                layer_labels.get(layer_id, f"Layer {layer_id}"), lang
            )
        return nd

    # Add actual nodes with absolute positions (horizontal layout)
    for layer_id, nodes in sorted(by_layer.items()):
        # Containers (compound nodes) — no position, Cytoscape auto-sizes around children
        containers = [n for n in nodes if n.get("container")]
        leaves = [n for n in nodes if not n.get("container")]

        for node in containers:
            elements.append(
                {
                    "data": make_node_data(node, layer_id),
                    "classes": "container",
                }
            )

        # Layer 2: split providers (right col) vs models (left col)
        if layer_id == 2:
            providers = [n for n in leaves if n.get("node_type") == "provider"]
            models = [n for n in leaves if n.get("node_type") != "provider"]
            buckets = [(LAYER_X_PROVIDERS, providers), (LAYER_X[2], models)]
        else:
            buckets = [(LAYER_X[layer_id], leaves)]

        for x_pos, bucket in buckets:
            x_pos = int(x_pos * col_scale)
            if ltr:
                x_pos = -x_pos
            n = len(bucket)
            for i, node in enumerate(bucket):
                default_x = x_pos
                default_y = (i - (n - 1) / 2) * spacing_y
                saved = saved_layout.get(node["id"])
                x_pos_final = saved["x"] if saved else default_x
                y = saved["y"] if saved else default_y

                classes = f"status-{node['status']}"
                if node.get("drilldown"):
                    classes += " has-drilldown"
                elements.append(
                    {
                        "data": make_node_data(node, layer_id),
                        "position": {"x": x_pos_final, "y": y},
                        "classes": classes,
                    }
                )

    # Add edges
    for edge in data["edges"]:
        elements.append(
            {
                "data": {
                    "id": f"{edge['from']}__{edge['to']}",
                    "source": edge["from"],
                    "target": edge["to"],
                    "label": edge.get("label", ""),
                    "etype": edge.get("type", ""),
                }
            }
        )

    return elements


def build_nav(maps, current_output, topics=None, links=None):
    """Build the site-wide nav: logo + Mind Maps dropdown + Deep Dives dropdown + Links dropdown."""
    current_name = Path(current_output).name

    # ── Mind Maps dropdown ──────────────────────────────────────
    map_items = ""
    for m in maps:
        if m.get("id") == "glossary":
            continue
        is_active = m["output"] == current_name
        title_en = t(m.get("title", ""), "en")
        title_fr = t(m.get("title", ""), "fr") or title_en
        desc_en  = t(m.get("description", ""), "en")
        desc_fr  = t(m.get("description", ""), "fr") or desc_en
        active_cls = " active" if is_active else ""
        map_items += (
            f'<a href="{m["output"]}" class="nav-item{active_cls}">'
            f'<span class="nav-item-icon">{m.get("icon","📄")}</span>'
            f'<span class="nav-item-info">'
            f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'<span class="nav-item-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'</span></a>'
        )

    # ── Deep Dives / Réflexion dropdowns ──────────────────────────
    deep_dives = [tp for tp in (topics or []) if tp.get("category") != "reflexion"]
    reflexions = [tp for tp in (topics or []) if tp.get("category") == "reflexion"]

    def _topic_items(topic_list):
        items = ""
        for topic in topic_list:
            tid = topic.get("id", "")
            title_en  = t(topic.get("title",   ""), "en")
            title_fr  = t(topic.get("title",   ""), "fr") or title_en
            summ_en   = t(topic.get("summary", ""), "en")
            summ_fr   = t(topic.get("summary", ""), "fr") or summ_en
            is_active = current_name == f"{tid}.html"
            active_cls = " active" if is_active else ""
            items += (
                f'<a href="topics/{tid}.html" class="nav-item{active_cls}">'
                f'<span class="nav-item-icon">📝</span>'
                f'<span class="nav-item-info">'
                f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
                f'<span class="nav-item-desc" data-en="{summ_en}" data-fr="{summ_fr}">{summ_en}</span>'
                f'</span></a>'
            )
        return items

    dive_items = _topic_items(deep_dives)
    reflexion_items = _topic_items(reflexions)

    # ── Links dropdown ──────────────────────────────────────────
    link_items = ""
    for link in (links or []):
        title_en = t(link.get("title", ""), "en")
        title_fr = t(link.get("title", ""), "fr") or title_en
        desc_en  = t(link.get("description", ""), "en")
        desc_fr  = t(link.get("description", ""), "fr") or desc_en
        url = link.get("url", "")
        link_items += (
            f'<a href="{url}" class="nav-item" target="_blank" rel="noopener">'
            f'<span class="nav-item-icon">{link.get("icon","🔗")}</span>'
            f'<span class="nav-item-info">'
            f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'<span class="nav-item-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'</span></a>'
        )

    nav = (
        f'<a href="index.html" class="nav-logo" title="Home">'
        f'<svg width="44" height="30" viewBox="0 0 120 82" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="22" y1="34" x2="42" y2="16" stroke="white" stroke-width="1" stroke-opacity="0.55"/>'
        f'<line x1="42" y1="16" x2="60" y2="10" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>'
        f'<line x1="56" y1="38" x2="72" y2="50" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>'
        f'<line x1="72" y1="50" x2="94" y2="44" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>'
        f'<line x1="94" y1="44" x2="108" y2="60" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>'
        f'<line x1="22" y1="34" x2="40" y2="48" stroke="white" stroke-width="1" stroke-opacity="0.55"/>'
        f'<line x1="40" y1="48" x2="56" y2="38" stroke="white" stroke-width="1" stroke-opacity="0.55"/>'
        f'<line x1="56" y1="38" x2="76" y2="20" stroke="white" stroke-width="1" stroke-opacity="0.55"/>'
        f'<circle cx="22"  cy="34" r="5"   fill="#E74C3C"/>'
        f'<circle cx="42"  cy="16" r="3.5" fill="white"/>'
        f'<circle cx="40"  cy="48" r="3"   fill="white"/>'
        f'<circle cx="60"  cy="10" r="4.5" fill="#E74C3C"/>'
        f'<circle cx="56"  cy="38" r="5"   fill="white"/>'
        f'<circle cx="76"  cy="20" r="3.5" fill="white"/>'
        f'<circle cx="72"  cy="50" r="4.5" fill="#E74C3C"/>'
        f'<circle cx="94"  cy="44" r="3"   fill="white"/>'
        f'<circle cx="108" cy="26" r="4.5" fill="#E74C3C"/>'
        f'<circle cx="108" cy="60" r="3.5" fill="white"/>'
        f'</svg>'
        f'</a>'
        f'<div class="nav-group">'
        f'  <button class="nav-btn">'
        f'    <span data-en="Mind Maps" data-fr="Mind Maps">Mind Maps</span> ▾'
        f'  </button>'
        f'  <div class="nav-dropdown">{map_items}</div>'
        f'</div>'
        f'<div class="nav-group">'
        f'  <button class="nav-btn">'
        f'    <span data-en="Deep Dives" data-fr="Articles">Deep Dives</span> ▾'
        f'  </button>'
        f'  <div class="nav-dropdown">{dive_items}</div>'
        f'</div>'
    )
    if reflexion_items:
        nav += (
            f'<div class="nav-group">'
            f'  <button class="nav-btn">'
            f'    <span data-en="Reflection" data-fr="Réflexion">Reflection</span> ▾'
            f'  </button>'
            f'  <div class="nav-dropdown">{reflexion_items}</div>'
            f'</div>'
        )
    if link_items:
        nav += (
            f'<div class="nav-group">'
            f'  <button class="nav-btn">'
            f'    <span data-en="Links" data-fr="Liens">Links</span> ▾'
            f'  </button>'
            f'  <div class="nav-dropdown">{link_items}</div>'
            f'</div>'
        )
    nav += (
        f'<a href="index.html#news" class="nav-btn" style="text-decoration:none;">'
        f'  <span data-en="News" data-fr="Nouveautés">News</span>'
        f'</a>'
    )
    return nav


def load_drilldown_datasets(data, maps):
    """Load sub-map data for all nodes that have a drilldown field."""
    result = {}
    all_maps = maps or []
    for node in data.get("nodes", []):
        url = node.get("drilldown", "")
        if not url:
            continue
        map_entry = next((m for m in all_maps if m.get("output") == url), None)
        if not map_entry or not map_entry.get("data"):
            continue
        data_path = ROOT / map_entry["data"]
        if not data_path.exists():
            continue
        with open(data_path) as f:
            sub_data = yaml.safe_load(f)
        sub_elements = build_elements(sub_data, data_file=data_path)
        meta = sub_data.get("meta", {})
        result[node["id"]] = {
            "title_en": t(meta.get("title", ""), "en"),
            "title_fr": t(meta.get("title", ""), "fr") or t(meta.get("title", ""), "en"),
            "elements": sub_elements,
        }
    return result


def generate_html(data, elements, maps=None, current_output=""):
    meta = data["meta"]
    categories = data["categories"]
    elements_json = json.dumps(elements, indent=2)
    layout_stem = Path(DATA_FILE).stem  # e.g. "ecosystem-macro"
    scale = float(meta.get("node_scale", 1))
    node_w    = int(NODE_WIDTH  * scale)
    node_h    = int(NODE_HEIGHT * scale)
    node_font = int(12 * scale)
    node_text_max     = int(130 * scale)
    node_text_max_prov= int(120 * scale)

    # Glossary terms for inline linking + search
    glossary_terms = load_glossary()
    glossary_js = json.dumps([
        {
            "id": term["id"],
            "aliases": term.get("aliases", []),
            "label_en": t(term["label"], "en"),
            "label_fr": t(term["label"], "fr") or t(term["label"], "en"),
            "description_en": t(term["description"], "en"),
            "description_fr": t(term["description"], "fr") or t(term["description"], "en"),
        }
        for term in glossary_terms
    ])

    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en
    titles_js = json.dumps({"en": title_en, "fr": title_fr})

    categories_js = json.dumps([
        {"id": c["id"], "label_en": t(c.get("label", ""), "en"), "label_fr": t(c.get("label", ""), "fr"), "color": c.get("color", "#aaa")}
        for c in categories
    ])

    # Build legend per lang
    def legend_items(lang):
        return "".join(
            f'<div class="legend-item"><span class="legend-dot" style="background:{c["color"]}"></span>'
            f"{t(c.get('label', ''), lang)}</div>"
            for c in categories
        )

    status_labels = {
        "en": {
            "stable": "stable",
            "evolving": "evolving",
            "emerging": "emerging",
            "deprecated": "deprecated",
        },
        "fr": {
            "stable": "stable",
            "evolving": "en évolution",
            "emerging": "émergent",
            "deprecated": "obsolète",
        },
    }
    status_labels_js = json.dumps(status_labels)

    panel_labels = {
        "en": {
            "click_hint": "Click any node to see its definition and connections",
            "description": "Description",
            "since": "Since",
        },
        "fr": {
            "click_hint": "Cliquez sur un nœud pour voir sa définition et ses connexions",
            "description": "Description",
            "since": "Depuis",
        },
    }
    panel_labels_js = json.dumps(panel_labels)

    legend_en = legend_items("en")
    legend_fr = legend_items("fr")

    topics = load_topics_meta()
    links = load_links()
    nav_html = build_nav(maps or [], current_output, topics=topics, links=links) if maps else ""

    drilldown_datasets = load_drilldown_datasets(data, maps or [])
    drilldown_datasets_js = json.dumps(drilldown_datasets)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_en}</title>
<script src="cytoscape.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #F8F9FA;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }}

  header {{
    background: #0D1117;
    color: white;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    row-gap: 4px;
    flex-shrink: 0;
    border-bottom: 1px solid #1E2D4E;
  }}
  header h1 {{ font-size: 18px; font-weight: 700; letter-spacing: 0.5px; }}
  header .meta {{ font-size: 12px; color: #95A5A6; }}


  .lang-toggle {{
    display: flex;
    gap: 4px;
    margin-left: 16px;
  }}
  .lang-btn {{
    padding: 4px 10px;
    border: 1.5px solid #555;
    border-radius: 6px;
    background: transparent;
    color: #95A5A6;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 0.5px;
    transition: all 0.15s;
  }}
  .lang-btn.active {{
    background: #E74C3C;
    border-color: #E74C3C;
    color: white;
  }}
  .lang-btn:hover:not(.active) {{
    border-color: #aaa;
    color: white;
  }}
  .glossary-header-btn {{
    padding: 5px 11px;
    border: 1.5px solid #555;
    border-radius: 6px;
    background: transparent;
    color: #BDC3C7;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    transition: all 0.15s;
  }}
  .glossary-header-btn:hover {{
    border-color: #C39BD3;
    color: #C39BD3;
  }}
  header {{
    flex-wrap: wrap;
    row-gap: 4px;
  }}
  .hint-bar {{
    width: 100%;
    text-align: center;
    font-size: 12px;
    color: #95A5A6;
  }}
  /* ── Site nav ── */
  .nav-logo {{
    display: flex;
    align-items: center;
    text-decoration: none;
    margin-right: 4px;
    opacity: 0.85;
    transition: opacity 0.15s;
  }}
  .nav-logo:hover {{ opacity: 1; }}
  .nav-group {{
    position: relative;
  }}
  .nav-btn {{
    padding: 5px 11px;
    border: 1.5px solid #333;
    border-radius: 6px;
    background: transparent;
    color: #BDC3C7;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .nav-btn:hover {{ border-color: #888; color: white; }}
  .nav-group:hover .nav-dropdown,
  .nav-group:focus-within .nav-dropdown {{ display: block; }}
  .nav-dropdown {{
    display: none;
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    background: #16213E;
    border: 1px solid #2C3E6E;
    border-radius: 10px;
    min-width: 260px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    z-index: 1000;
    overflow: hidden;
  }}
  .nav-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    color: #BDC3C7;
    text-decoration: none;
    font-size: 13px;
    transition: background 0.12s;
    border-bottom: 1px solid #1E2D4E;
  }}
  .nav-item:last-child {{ border-bottom: none; }}
  .nav-item:hover {{ background: #1E2D4E; color: white; }}
  .nav-item.active {{ background: #1E2D4E; color: white; }}
  .nav-item-icon {{ font-size: 16px; flex-shrink: 0; }}
  .nav-item-info {{ display: flex; flex-direction: column; }}
  .nav-item-title {{ font-weight: 600; font-size: 13px; }}
  .nav-item-desc {{ font-size: 11px; color: #7F8C8D; margin-top: 1px; }}

  .main {{
    display: flex;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }}
  #cy-area {{
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }}
  #cy-wrapper {{
    position: relative;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }}
  #drilldown-section {{
    flex: 0 0 0;
    min-height: 0;
    overflow: hidden;
    position: relative;
    border-top: 2px solid #E74C3C;
    transition: flex-basis 0.35s ease;
  }}
  body.drilldown-active #drilldown-section {{
    flex: 0 0 45%;
  }}
  #drilldown-label-box {{
    position: absolute;
    top: 6px;
    left: 50%;
    transform: translateX(-50%);
    background: #1A1A2E;
    padding: 2px 16px;
    color: #E74C3C;
    font-weight: 700;
    font-size: 12px;
    border-radius: 3px;
    z-index: 10;
    white-space: nowrap;
    pointer-events: none;
  }}
  #drilldown-close {{
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
    background: rgba(30,30,50,0.85);
    border: 1px solid #555;
    border-radius: 4px;
    color: #BDC3C7;
    cursor: pointer;
    padding: 2px 8px;
    font-size: 12px;
  }}
  #drilldown-close:hover {{ background: rgba(231,76,60,0.35); color: white; }}
  #cy2 {{ width: 100%; height: 100%; }}

  #cy {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: #FAFAFA;
  }}

  /* ── Side panel ── */
  #panel {{
    width: 320px;
    background: white;
    border-left: 1px solid #E0E0E0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
  }}

  #panel-header {{
    padding: 20px;
    background: #1A1A2E;
    color: white;
    position: relative;
  }}
  #panel-header .node-label {{
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  #panel-header .node-meta {{
    font-size: 12px;
    color: #BDC3C7;
  }}
  #panel-header .node-status {{
    display: inline-block;
    margin-top: 8px;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  #share-btn {{
    position: absolute;
    top: 12px;
    right: 12px;
    background: none;
    border: 1px solid #ffffff33;
    border-radius: 6px;
    color: #BDC3C7;
    font-size: 13px;
    padding: 4px 8px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  #share-btn:hover {{ border-color: #fff; color: #fff; }}
  #share-btn.copied {{ border-color: #2ECC71; color: #2ECC71; }}

  #panel-body {{
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }}
  #panel-body .section-title {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #95A5A6;
    margin-bottom: 6px;
  }}
  #panel-body .description {{
    font-size: 14px;
    line-height: 1.6;
    color: #2C3E50;
    margin-bottom: 20px;
  }}
  #panel-body .description p {{
    margin-bottom: 10px;
  }}
  #panel-body .description p:last-child {{
    margin-bottom: 0;
  }}
  #panel-body .description ol,
  #panel-body .description ul {{
    margin: 8px 0 10px 18px;
  }}
  #panel-body .description li {{
    margin-bottom: 4px;
  }}
  #panel-body .description strong {{
    font-weight: 600;
    color: #1A1A2E;
  }}
  .gloss-link {{
    text-decoration: underline;
    text-decoration-style: dotted;
    text-underline-offset: 3px;
    cursor: pointer;
    color: inherit;
  }}
  .panel-link {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #3498DB;
    text-decoration: none;
    padding: 4px 8px;
    border: 1px solid #3498DB33;
    border-radius: 6px;
    transition: background 0.15s;
  }}
  .panel-link:hover {{ background: #3498DB11; }}
  .panel-link .link-icon {{ font-size: 14px; }}
  .drilldown-hint {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: #E74C3C;
    background: #E74C3C11;
    border: 1px solid #E74C3C44;
    border-radius: 5px;
    padding: 3px 8px;
    cursor: zoom-in;
  }}
  #panel-body .since {{
    font-size: 12px;
    color: #7F8C8D;
  }}

  .empty-panel {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #BDC3C7;
    text-align: center;
    padding: 20px;
  }}
  .empty-panel .arrow {{ font-size: 32px; margin-bottom: 12px; }}
  .empty-panel p {{ font-size: 13px; line-height: 1.5; }}

  /* ── Legend ── */
  #legend {{
    padding: 10px 14px;
    border-top: 1px solid #F0F0F0;
    background: #FAFAFA;
    display: flex;
    gap: 12px;
  }}
  .legend-col {{
    flex: 1;
    min-width: 0;
  }}
  #legend h3 {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #95A5A6;
    margin-bottom: 6px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #555;
    margin-bottom: 3px;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 2px;
    flex-shrink: 0;
  }}
  .status-badge {{
    border: 1.5px solid;
    border-radius: 10px;
    padding: 1px 6px;
    font-size: 9px;
    font-weight: 600;
  }}

  /* ── Category boxes ── */
  .cat-box {{
    position: absolute;
    border: 2px solid;
    border-radius: 12px;
    pointer-events: none;
    box-sizing: border-box;
  }}
  .cat-box-label {{
    position: absolute;
    top: -11px;
    left: 14px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: #F8F9FA;
    padding: 1px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}

  /* ── Controls ── */
  #controls {{
    position: absolute;
    bottom: 16px;
    left: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 10;
  }}
  .ctrl-btn {{
    width: 36px;
    height: 36px;
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    transition: background 0.15s;
  }}
  .ctrl-btn:hover {{ background: #F0F0F0; }}
  .ctrl-btn.saved {{ border-color: #27AE60; color: #27AE60; }}
  .ctrl-btn[data-tip]:hover::after {{
    content: attr(data-tip);
    position: absolute;
    left: 48px;
    background: rgba(30,30,30,0.92);
    color: #fff;
    font-size: 11px;
    white-space: nowrap;
    padding: 4px 8px;
    border-radius: 5px;
    pointer-events: none;
    z-index: 100;
  }}
  .ctrl-btn {{ position: relative; }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
    {nav_html}
    <div style="margin-left:12px;min-width:0;">
      <h1 id="main-title">{title_en}</h1>
      <div class="meta">v{meta["version"]} · {meta["date"]}</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
    <a href="glossary.html" class="glossary-header-btn">
      <span data-en="📖 Glossary" data-fr="📖 Glossaire">📖 Glossary</span>
    </a>
    {gs_widget('search-index.json')}
    <div class="lang-toggle">
      <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
      <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
    </div>
  </div>
  <div class="meta hint-bar" id="hint-text">Click a node to explore · Scroll to zoom · Drag to pan</div>
</header>

<div class="main">
  <div id="cy-area">
    <div id="cy-wrapper">
      <div id="cy"></div>
      <div id="cat-boxes" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:hidden;"></div>
      <div id="controls">
        <button class="ctrl-btn" onclick="cy.fit()"
          data-tip-en="Fit all nodes" data-tip-fr="Tout afficher">⊞</button>
        <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*1.2)"
          data-tip-en="Zoom in" data-tip-fr="Zoom avant">+</button>
        <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*0.8)"
          data-tip-en="Zoom out" data-tip-fr="Zoom arrière">−</button>
        <button class="ctrl-btn" id="reset-btn" onclick="resetLayout()"
          data-tip-en="Reset positions" data-tip-fr="Réinitialiser">↺</button>
        <button class="ctrl-btn" onclick="exportLayout()"
          data-tip-en="Save layout" data-tip-fr="Sauvegarder la vue">⬇</button>
        <button class="ctrl-btn" onclick="window.open('{OUTPUT_FILE.stem}-slides.html','_blank')"
          data-tip-en="Open as slides" data-tip-fr="Ouvrir en slides">▤</button>
      </div>
    </div>
    <div id="drilldown-section">
      <div id="drilldown-label-box"></div>
      <button id="drilldown-close" onclick="closeDrilldown()">✕</button>
      <div id="cy2"></div>
    </div>
  </div>

  <div id="panel">
    <div id="panel-header" style="display:none;">
      <button id="share-btn" onclick="shareNode()" title="Copy link">🔗</button>
      <div class="node-label" id="ph-label"></div>
      <div class="node-meta" id="ph-meta"></div>
      <span class="node-status" id="ph-status"></span>
      <div id="ph-drilldown" style="display:none;margin-top:6px;">
        <span class="drilldown-hint" id="ph-drilldown-hint"></span>
      </div>
    </div>
    <div id="panel-body">
      <div class="empty-panel" id="empty-msg">
        <div class="arrow">←</div>
        <p>Click any node to see its definition and connections</p>
      </div>
      <div id="panel-content" style="display:none;">
        <div class="section-title">Description</div>
        <div class="description" id="pc-desc"></div>
        <div class="section-title">Since</div>
        <div class="since" id="pc-since"></div>
        <div id="pc-links" style="display:none; margin-top:14px; display:flex; flex-direction:column; gap:6px;"></div>
      </div>
    </div>
    <div id="legend">
      <div class="legend-col">
        <h3 id="legend-cat-title">Categories</h3>
        <div id="legend-en">{legend_en}</div>
        <div id="legend-fr" style="display:none">{legend_fr}</div>
      </div>
      <div class="legend-col">
        <h3 id="legend-status-title">Status</h3>
        <div id="status-legend-items"></div>
      </div>
    </div>
  </div>
</div>

<script>
const elements = {elements_json};
const DRILLDOWN_DATA = {drilldown_datasets_js};
const TITLES        = {titles_js};
const STATUS_LABELS = {status_labels_js};
const PANEL_LABELS  = {panel_labels_js};
const CATEGORIES    = {categories_js};
const STATUS_COLORS = {json.dumps(STATUS_LABEL_COLOR)};
const GLOSSARY_TERMS = {glossary_js};

function linkGlossaryTerms(text) {{
  if (!GLOSSARY_TERMS.length) return text;
  // Escape HTML entities first
  let safe = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  // Build sorted alias→id map (longest first to avoid partial matches)
  const entries = [];
  GLOSSARY_TERMS.forEach(term => {{
    term.aliases.forEach(alias => entries.push({{ alias, id: term.id }}));
  }});
  entries.sort((a, b) => b.alias.length - a.alias.length);
  // Split on existing <span> tags so we never mutate already-linked text or attributes
  entries.forEach(({{ alias, id }}) => {{
    const escaped = alias.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\$&');
    const re = new RegExp(`\\\\b(${{escaped}})\\\\b`, 'gi');
    // Replace only in text segments (outside any HTML tags)
    safe = safe.replace(/(<[^>]*>)|([^<]+)/g, (match, tag, txt) => {{
      if (tag) return tag; // leave HTML tags untouched
      return txt.replace(re, `<span class="gloss-link" onclick="window.open('glossary.html#${{id}}','_blank')">$1</span>`);
    }});
  }});
  return safe;
}}

function formatDesc(rawText) {{
  if (!rawText) return '';
  const lines = rawText.split('\\n');
  let html = '';
  let inOl = false, inUl = false;

  const flush = () => {{
    if (inOl) {{ html += '</ol>'; inOl = false; }}
    if (inUl) {{ html += '</ul>'; inUl = false; }}
  }};

  const inline = (s) => {{
    // Bold: **text**
    const linked = linkGlossaryTerms(s);
    return linked.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  }};

  lines.forEach(line => {{
    const trimmed = line.trim();
    if (!trimmed) {{ flush(); return; }}

    const olMatch = trimmed.match(/^(\\d+)\\. (.+)/);
    const ulMatch = trimmed.match(/^[-*] (.+)/);

    if (olMatch) {{
      if (inUl) {{ html += '</ul>'; inUl = false; }}
      if (!inOl) {{ html += '<ol>'; inOl = true; }}
      html += `<li>${{inline(olMatch[2])}}</li>`;
    }} else if (ulMatch) {{
      if (inOl) {{ html += '</ol>'; inOl = false; }}
      if (!inUl) {{ html += '<ul>'; inUl = true; }}
      html += `<li>${{inline(ulMatch[1])}}</li>`;
    }} else {{
      flush();
      html += `<p>${{inline(trimmed)}}</p>`;
    }}
  }});

  flush();
  return html;
}}

let lang = 'en';

function setLang(newLang) {{
  lang = newLang;

  // Toggle buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.lang === lang);
  }});

  // Update control button tooltips
  document.querySelectorAll('.ctrl-btn[data-tip-en]').forEach(btn => {{
    btn.dataset.tip = btn.dataset['tip' + newLang.charAt(0).toUpperCase() + newLang.slice(1)];
  }});
  drawCategoryBoxes();

  // Header title
  document.getElementById('main-title').textContent = TITLES[lang];

  // Hint text
  document.getElementById('hint-text').textContent =
    lang === 'fr' ? 'Cliquez sur un nœud pour explorer · Molette pour zoomer · Glisser pour naviguer'
                  : 'Click a node to explore · Scroll to zoom · Drag to pan';

  // Legend
  document.getElementById('legend-en').style.display = lang === 'en' ? '' : 'none';
  document.getElementById('legend-fr').style.display = lang === 'fr' ? '' : 'none';
  document.getElementById('legend-cat-title').textContent =
    lang === 'fr' ? 'Catégories' : 'Categories';
  document.getElementById('legend-status-title').textContent =
    lang === 'fr' ? 'Statut' : 'Status';
  renderStatusLegend();

  // Search placeholder

  // Nav dropdown titles
  document.querySelectorAll('.nav-title, .nav-desc').forEach(el => {{
    const txt = el.dataset[lang];
    if (txt) el.textContent = txt;
  }});

  // Node labels in graph
  cy.batch(() => {{
    cy.nodes().forEach(n => {{
      const lbl = n.data(`label_${{lang}}`);
      if (lbl) n.data('label', lbl);
      const ll = n.data(`layerLabel_${{lang}}`);
      if (ll) n.data('layerLabel', ll);
    }});
  }});

  // Refresh open panel
  if (currentNode) showPanel(currentNode);
}}

function renderStatusLegend() {{
  const sl = STATUS_LABELS[lang];
  document.getElementById('status-legend-items').innerHTML =
    Object.entries(sl).map(([k, v]) =>
      `<div class="legend-item"><span class="status-badge" style="color:${{STATUS_COLORS[k]}};border-color:${{STATUS_COLORS[k]}}">${{v}}</span></div>`
    ).join('');
}}
renderStatusLegend();

function clearSearch() {{
  cy.elements().removeClass('dimmed highlighted');
  currentNode = null;
  document.getElementById('panel-header').style.display = 'none';
  document.getElementById('empty-msg').style.display = 'flex';
  document.getElementById('panel-content').style.display = 'none';
}}


const CY_STYLE = [
    // Provider nodes — ellipse to distinguish from models
    {{
      selector: "node[node_type='provider']",
      style: {{
        "width": {node_w},
        "height": {node_h},
        "shape": "ellipse",
        "background-color": "data(color)",
        "background-opacity": 0.85,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-size": "{node_font}px",
        "font-weight": "700",
        "color": "#1A1A2E",
        "border-width": 2,
        "border-color": "data(color)",
        "text-wrap": "wrap",
        "text-max-width": "{node_text_max_prov}px",
      }}
    }},
    // Nodes
    {{
      selector: "node",
      style: {{
        "width": {node_w},
        "height": {node_h},
        "shape": "round-rectangle",
        "background-color": "data(color)",
        "background-opacity": 0.9,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-size": "{node_font}px",
        "font-weight": "600",
        "color": "#1A1A2E",
        "border-width": 2,
        "border-color": "data(color)",
        "border-opacity": 1,
        "text-wrap": "wrap",
        "text-max-width": "{node_text_max}px",
        "overlay-padding": "6px",
        "transition-property": "border-color, border-width, background-opacity",
        "transition-duration": "0.15s",
      }}
    }},
    // Model types → 1.5× the (already-scaled) base node size
    {{
      selector: "node[category = 'model_types']",
      style: {{
        "width": {int(node_w * 1.5)},
        "height": {int(node_h * 1.5)},
        "text-max-width": "{int(node_w * 1.5) - 10}px",
        "font-size": "{int(node_font * 1.5)}px",
      }}
    }},
    // Status: evolving → orange border
    {{
      selector: ".status-evolving",
      style: {{
        "border-color": "#E67E22",
        "border-width": 3,
      }}
    }},
    // Status: emerging → dashed purple border
    {{
      selector: ".status-emerging",
      style: {{
        "border-color": "#8E44AD",
        "border-width": 3,
        "border-style": "dashed",
      }}
    }},
    // Nodes with drill-down → visible glow + double border
    {{
      selector: ".has-drilldown",
      style: {{
        "border-color": "#E74C3C",
        "border-width": 3,
        "border-style": "double",
        "shadow-blur": 12,
        "shadow-color": "#E74C3C",
        "shadow-offset-x": 0,
        "shadow-offset-y": 0,
        "shadow-opacity": 0.6,
      }}
    }},
    // Status: deprecated → grey, muted
    {{
      selector: ".status-deprecated",
      style: {{
        "background-opacity": 0.4,
        "color": "#999",
        "border-color": "#BDC3C7",
      }}
    }},
    // Hover
    {{
      selector: "node:active, node.highlighted",
      style: {{
        "border-width": 3,
        "border-color": "#1A1A2E",
        "background-opacity": 1,
        "z-index": 999,
      }}
    }},
    // Selected
    {{
      selector: "node:selected",
      style: {{
        "border-width": 3,
        "border-color": "#E74C3C",
        "background-opacity": 1,
      }}
    }},
    // Compound (container / parent) nodes — visual box only, no Cytoscape label.
    // Labels are rendered as HTML overlays in drawCategoryBoxes() so they match
    // the cat-box-label style exactly (same font, size, position).
    {{
      selector: ":parent",
      style: {{
        "background-color": "data(color)",
        "background-opacity": 0.06,
        "border-width": 2,
        "border-color": "data(color)",
        "border-opacity": 0.55,
        "border-style": "solid",
        "border-radius": 12,
        "shape": "round-rectangle",
        "label": "",
        "padding": "26px",
        "shadow-blur": 0,
        "shadow-opacity": 0,
      }}
    }},
    // Edges
    {{
      selector: "edge",
      style: {{
        "width": 1.5,
        "line-color": "#BDC3C7",
        "target-arrow-color": "#BDC3C7",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        "arrow-scale": 1,
        "label": "",
        "font-size": "9px",
        "color": "#7F8C8D",
        "text-background-color": "white",
        "text-background-opacity": 0.8,
        "text-background-padding": "2px",
        "opacity": 0.6,
      }}
    }},
    {{
      selector: "edge.highlighted",
      style: {{
        "width": 2.5,
        "line-color": "#E74C3C",
        "target-arrow-color": "#E74C3C",
        "label": "data(label)",
        "opacity": 1,
        "z-index": 999,
      }}
    }},
    // Dimmed (when a node is selected)
    {{
      selector: ".dimmed",
      style: {{
        "opacity": 0.15,
      }}
    }},
];

const cy = cytoscape({{
  container: document.getElementById("cy"),
  elements: elements,
  style: CY_STYLE,
  layout: {{
    name: "preset",
  }},
  wheelSensitivity: 0.3,
  minZoom: 0.2,
  maxZoom: 3,
}});

// ── Fit on load ──────────────────────────────
// ── Layout persistence (localStorage) ───────
const STORAGE_KEY = 'mindmap_positions_' + window.location.pathname;

function savePositions() {{
  const positions = {{}};
  cy.nodes().forEach(n => {{
    const p = n.position();
    positions[n.id()] = {{ x: Math.round(p.x), y: Math.round(p.y) }};
  }});
  localStorage.setItem(STORAGE_KEY, JSON.stringify(positions));
  const btn = document.getElementById('reset-btn');
  btn.classList.add('saved');
  btn.title = 'Reset to auto layout';
}}

async function exportLayout() {{
  const positions = {{}};
  cy.nodes().forEach(n => {{
    const p = n.position();
    positions[n.id()] = {{ x: Math.round(p.x), y: Math.round(p.y) }};
  }});
  const json  = JSON.stringify(positions, null, 2);
  const fname = '{layout_stem}-layout.json';
  const blob  = new Blob([json], {{ type: 'application/json' }});
  if (window.showSaveFilePicker) {{
    try {{
      const handle = await window.showSaveFilePicker({{
        suggestedName: fname,
        types: [{{ description: 'JSON', accept: {{ 'application/json': ['.json'] }} }}]
      }});
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return;
    }} catch (e) {{
      if (e.name === 'AbortError') return; // user cancelled
    }}
  }}
  // Fallback for browsers without File System Access API
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = fname; a.click();
  URL.revokeObjectURL(url);
}}

function _unused_openPresentation() {{
  const l = lang;
  const title = TITLES[l];

  // Group nodes by layer
  const byLayer = {{}};
  elements.forEach(el => {{
    if (!el.data || !el.data.layer) return;
    const layer = el.data.layer;
    if (!byLayer[layer]) byLayer[layer] = [];
    byLayer[layer].push(el.data);
  }});

  const statusEmoji = {{ stable: '🟢', evolving: '🟡', emerging: '🔵', deprecated: '🔴' }};
  const layerOrder = Object.keys(byLayer).map(Number).sort((a, b) => b - a);
  const slides = [];

  // Title slide
  const subtitle = l === 'en' ? 'AI / LLM Ecosystem' : 'Écosystème IA / LLM';
  slides.push('<div class="slide-type-title"><div class="slide-title-content"><h1>' + title + '</h1><p class="subtitle">' + subtitle + '</p></div></div>');

  // Overview slide per layer
  layerOrder.forEach(layerId => {{
    const nodes = byLayer[layerId];
    const layerLabel = nodes[0]['layerLabel_' + l] || ('Layer ' + layerId);
    const items = nodes.map(n => {{
      const nodeLabel = n['label_' + l] || n.label;
      const desc = n['description_' + l] || '';
      const shortDesc = desc ? desc.split(/[.!?][ \\n]/)[0].replace(/\\n/g, ' ').trim() + '.' : '';
      const emoji = statusEmoji[n.status] || '';
      return '<li>' + emoji + ' <strong>' + nodeLabel + '</strong>' + (shortDesc ? ' — ' + shortDesc : '') + '</li>';
    }}).join('');
    slides.push('<div class="slide-layer-num">Layer ' + layerId + '</div><h2>' + layerLabel + '</h2><ul>' + items + '</ul>');
  }});

  // Detail slide per node
  layerOrder.forEach(layerId => {{
    const nodes = byLayer[layerId];
    const layerLabel = nodes[0]['layerLabel_' + l] || ('Layer ' + layerId);
    nodes.forEach(n => {{
      const nodeLabel = n['label_' + l] || n.label;
      const desc = (n['description_' + l] || '').replace(/\\n/g, '<br>');
      const emoji = statusEmoji[n.status] || '';
      const statusLabel = n.status || '';
      slides.push(
        '<div class="slide-node-layer">' + layerLabel + '</div>' +
        '<h2>' + emoji + ' ' + nodeLabel + '</h2>' +
        (desc ? '<p class="node-desc">' + desc + '</p>' : '') +
        '<span class="slide-status status-' + statusLabel + '">' + statusLabel + '</span>'
      );
    }});
  }});

  // Summary slide
  const totalNodes = elements.filter(el => el.data && el.data.layer).length;
  const summaryTitle = l === 'en' ? 'Summary' : 'Récapitulatif';
  slides.push(
    '<div class="slide-type-title"><div class="slide-title-content">' +
    '<h2>' + summaryTitle + '</h2>' +
    '<p class="stat">' + totalNodes + ' concepts</p>' +
    '<p class="stat">' + layerOrder.length + (l === 'en' ? ' layers' : ' couches') + '</p>' +
    '<p class="generated-from">' + title + '</p>' +
    '</div></div>'
  );

  // Build popup via DOM (avoids script-close tag inside a JS string breaking the outer page)
  const w = window.open('', '_blank');
  if (!w) return;
  const d = w.document;
  d.open();
  d.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + title + '</title></head><body></body></html>');
  d.close();

  const style = d.createElement('style');
  style.textContent = [
    '* {{ box-sizing:border-box; margin:0; padding:0 }}',
    'body {{ background:#0d1117; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:"Segoe UI",sans-serif; overflow:hidden }}',
    '#slide {{ background:#fff; width:min(92vw,960px); aspect-ratio:16/9; border-radius:12px; padding:48px 64px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 20px 60px rgba(0,0,0,.5); position:relative; overflow:hidden }}',
    '#slide h1 {{ font-size:2.4em; color:#1a237e; margin-bottom:16px }}',
    '#slide h2 {{ font-size:1.6em; color:#283593; border-bottom:2px solid #3949ab; padding-bottom:10px; margin-bottom:20px }}',
    '.subtitle {{ font-size:1.2em; color:#555 }}',
    '.slide-type-title {{ display:flex; align-items:center; justify-content:center; text-align:center; height:100% }}',
    '.slide-title-content {{ display:flex; flex-direction:column; gap:12px }}',
    '.slide-layer-num,.slide-node-layer {{ position:absolute; top:20px; right:28px; font-size:.75em; color:#9fa8da; font-weight:600; letter-spacing:1px; text-transform:uppercase }}',
    'ul {{ list-style:none; display:flex; flex-direction:column; gap:8px }}',
    'li {{ font-size:.9em; color:#333; line-height:1.4 }}',
    'li strong {{ color:#1a237e }}',
    '.node-desc {{ font-size:.92em; color:#444; line-height:1.7; margin-top:8px }}',
    '.slide-status {{ position:absolute; bottom:20px; right:28px; font-size:.72em; font-weight:600; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:10px; border:1.5px solid }}',
    '.status-stable {{ color:#2e7d32; border-color:#2e7d32 }}',
    '.status-evolving {{ color:#e65100; border-color:#e65100 }}',
    '.status-emerging {{ color:#1565c0; border-color:#1565c0 }}',
    '.status-deprecated {{ color:#b71c1c; border-color:#b71c1c }}',
    '.stat {{ font-size:1.4em; font-weight:700; color:#3949ab }}',
    '.generated-from {{ font-size:.85em; color:#999; margin-top:12px }}',
    '#nav {{ display:flex; align-items:center; gap:20px; margin-top:20px }}',
    '.nav-btn {{ background:#3949ab; color:#fff; border:none; border-radius:8px; padding:10px 24px; font-size:1em; cursor:pointer; transition:background .15s }}',
    '.nav-btn:hover {{ background:#283593 }}',
    '.nav-btn:disabled {{ background:#555; cursor:default }}',
    '#counter {{ color:#aaa; font-size:.9em; min-width:80px; text-align:center }}',
    '#progress {{ position:absolute; bottom:0; left:0; height:3px; background:#3949ab; transition:width .3s; border-radius:0 0 0 12px }}'
  ].join(' ');
  d.head.appendChild(style);

  d.body.innerHTML =
    '<div id="slide"><div id="progress"></div><div id="slide-content"></div></div>' +
    '<div id="nav">' +
    '<button class="nav-btn" id="prev">&#8592;</button>' +
    '<span id="counter"></span>' +
    '<button class="nav-btn" id="next">&#8594;</button>' +
    '</div>';

  // Pass slides via window property to avoid serialization issues
  w.PRESENTATION_SLIDES = slides;
  const init = d.createElement('script');
  init.textContent = '(function(){{ var s = window.PRESENTATION_SLIDES; var cur = 0; function render(){{ document.getElementById("slide-content").innerHTML = s[cur]; document.getElementById("counter").textContent = (cur+1)+" / "+s.length; document.getElementById("prev").disabled = cur===0; document.getElementById("next").disabled = cur===s.length-1; document.getElementById("progress").style.width = ((cur+1)/s.length*100)+"%"; }} function go(d){{ cur=Math.max(0,Math.min(s.length-1,cur+d)); render(); }} document.getElementById("prev").onclick=function(){{go(-1);}}; document.getElementById("next").onclick=function(){{go(1);}}; document.addEventListener("keydown",function(e){{ if(e.key==="ArrowRight"||e.key==="ArrowDown")go(1); if(e.key==="ArrowLeft"||e.key==="ArrowUp")go(-1); }}); render(); }})();';
  d.body.appendChild(init);
}}

function loadPositions() {{
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return false;
  try {{
    const positions = JSON.parse(raw);
    cy.batch(() => {{
      cy.nodes().forEach(n => {{
        if (positions[n.id()]) n.position(positions[n.id()]);
      }});
    }});
    document.getElementById('reset-btn').classList.add('saved');
    return true;
  }} catch(e) {{ return false; }}
}}

function resetLayout() {{
  localStorage.removeItem(STORAGE_KEY);
  document.getElementById('reset-btn').classList.remove('saved');
  document.getElementById('reset-btn').title = 'Reset layout';
  // Restore original positions from elements data
  cy.batch(() => {{
    elements.forEach(el => {{
      if (el.position) {{
        const node = cy.getElementById(el.data.id);
        if (node) node.position(el.position);
      }}
    }});
  }});
  cy.fit(undefined, 40);
  drawCategoryBoxes();
}}

// ── Category bounding boxes ──────────────────
function drawCategoryBoxes() {{
  const container = document.getElementById('cat-boxes');
  if (!container) return;
  container.innerHTML = '';
  const zoom = cy.zoom();
  const pan  = cy.pan();
  const cyRect = document.getElementById('cy').getBoundingClientRect();

  CATEGORIES.forEach(cat => {{
    const nodes = cy.nodes('[category = "' + cat.id + '"]');
    if (nodes.length === 0) return;
    // If this category already has a compound container, skip — that
    // compound is the visual wrapper for the category (avoids duplicate label).
    if (nodes.some(n => n.isParent())) return;
    const bb = nodes.boundingBox();
    const pad = 24;
    const x = (bb.x1 - pad) * zoom + pan.x;
    const y = (bb.y1 - pad) * zoom + pan.y;
    const w = (bb.x2 - bb.x1 + pad * 2) * zoom;
    const h = (bb.y2 - bb.y1 + pad * 2) * zoom;

    const box = document.createElement('div');
    box.className = 'cat-box';
    box.style.left   = x + 'px';
    box.style.top    = y + 'px';
    box.style.width  = w + 'px';
    box.style.height = h + 'px';
    box.style.borderColor = cat.color;
    box.style.opacity = '0.5';

    const lbl = document.createElement('div');
    lbl.className = 'cat-box-label';
    lbl.style.color = cat.color;
    lbl.textContent = cat['label_' + lang] || cat.label_en;
    box.appendChild(lbl);
    container.appendChild(box);
  }});

  // Draw HTML labels for compound container nodes — same style as cat-box-label.
  cy.nodes('.container').forEach(n => {{
    const rbb = n.renderedBoundingBox({{includeLabels: false, includeOverlays: false}});
    const lbl = document.createElement('div');
    lbl.className = 'cat-box-label';
    lbl.style.left  = (rbb.x1 + 14) + 'px';
    lbl.style.top   = (rbb.y1 - 11) + 'px';
    lbl.style.color = n.data('color');
    lbl.textContent = (n.data('label_' + lang) || n.data('label')).toUpperCase();
    container.appendChild(lbl);
  }});
}}

// Must be declared before cy.ready() since Cytoscape fires ready() synchronously
// when the graph is already initialised. Placing `let` after the cy.ready() call
// leaves currentNode in the TDZ when navigateToHash() → showPanel() runs on
// hash-navigation (global search), causing a silent ReferenceError that also
// prevents the hashchange listener and tap handlers from being registered.
let currentNode = null;

cy.ready(() => {{
  if (!loadPositions()) {{
    cy.fit(undefined, 40);
  }}
  // Init tooltips in default language
  document.querySelectorAll('.ctrl-btn[data-tip-en]').forEach(btn => {{
    btn.dataset.tip = btn.dataset.tipEn;
  }});
  drawCategoryBoxes();

  // Open node from URL hash (shareable links & global search)
  function navigateToHash() {{
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const node = cy.getElementById(hash);
    if (node.empty()) return;
    cy.animate({{ center: {{ eles: node }}, zoom: 1.4 }}, {{ duration: 400 }});
    showPanel(node);
    cy.elements().addClass('dimmed');
    node.removeClass('dimmed');
    node.connectedEdges().removeClass('dimmed').addClass('highlighted');
    node.connectedEdges().connectedNodes().removeClass('dimmed');
    node.addClass('highlighted');
  }}
  navigateToHash();
  window.addEventListener('hashchange', navigateToHash);
}});

cy.on('viewport position dragfree', drawCategoryBoxes);

// Auto-save on drag
cy.on('dragfree', 'node', savePositions);

function shareNode() {{
  const url = window.location.href.split('#')[0] + '#' + currentNode.id();
  navigator.clipboard.writeText(url).then(() => {{
    const btn = document.getElementById('share-btn');
    btn.textContent = '✓';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = '🔗'; btn.classList.remove('copied'); }}, 1800);
  }});
}}

function showPanel(node) {{
  currentNode = node;
  const d = node.data();
  history.replaceState(null, '', '#' + d.id);
  const pl = PANEL_LABELS[lang];
  const sl = STATUS_LABELS[lang];

  document.getElementById("panel-header").style.display = "block";
  document.getElementById("ph-label").textContent = d[`label_${{lang}}`] || d.label;

  let meta = `Layer ${{d.layer}}`;
  if (d.node_type) meta += ` · ${{d.node_type}}`;
  if (d.subcategory) meta += ` · ${{d.subcategory}}`;
  document.getElementById("ph-meta").textContent = meta;

  const statusEl = document.getElementById("ph-status");
  statusEl.textContent = sl[d.status] || d.status;
  statusEl.style.background = STATUS_COLORS[d.status] + "33";
  statusEl.style.color = STATUS_COLORS[d.status];
  statusEl.style.border = `1px solid ${{STATUS_COLORS[d.status]}}`;

  document.getElementById("empty-msg").style.display = "none";
  document.getElementById("panel-content").style.display = "block";
  document.querySelector("#panel-content .section-title").textContent = pl.description;
  document.querySelectorAll("#panel-content .section-title")[1].textContent = pl.since;
  document.getElementById("pc-desc").innerHTML = formatDesc(d[`description_${{lang}}`] || "");
  document.getElementById("pc-since").textContent = d.since;

  const linksEl = document.getElementById("pc-links");
  linksEl.innerHTML = "";
  if (d.link) {{
    const a = document.createElement("a");
    a.href = d.link; a.target = "_blank"; a.rel = "noopener";
    a.className = "panel-link";
    a.innerHTML = '<span class="link-icon">🌐</span>' + (lang === "fr" ? "Site officiel" : "Official site");
    linksEl.appendChild(a);
  }}
  if (d.ref) {{
    const a = document.createElement("a");
    a.href = d.ref; a.target = "_blank"; a.rel = "noopener";
    a.className = "panel-link";
    a.innerHTML = '<span class="link-icon">📄</span>' + (lang === "fr" ? "Référence" : "Reference");
    linksEl.appendChild(a);
  }}
  linksEl.style.display = (d.link || d.ref) ? "flex" : "none";

  const drilldownEl = document.getElementById("ph-drilldown");
  const drilldownHint = document.getElementById("ph-drilldown-hint");
  if (DRILLDOWN_DATA[d.id]) {{
    drilldownEl.style.display = "block";
    drilldownHint.textContent = lang === "fr" ? "↗ Cliquez pour explorer" : "↗ Click to explore";
    drilldownHint.onclick = () => {{
      const dd = DRILLDOWN_DATA[d.id];
      if (dd) showDrilldown(dd, d[`label_${{lang}}`] || d.label, d.color);
    }};
  }} else {{
    drilldownEl.style.display = "none";
  }}
}}

// ── Node click → panel ───────────────────────
cy.on("tap", "node", function(evt) {{
  const node = evt.target;
  showPanel(node);
  if (cy2) cy2.elements().removeClass("dimmed highlighted");
  // Don't dim compound parents — their opacity cascades to children,
  // making the clicked card appear transparent inside a faded container.
  cy.elements().not(":parent").addClass("dimmed");
  node.removeClass("dimmed");
  const connected = node.connectedEdges();
  connected.removeClass("dimmed").addClass("highlighted");
  connected.connectedNodes().removeClass("dimmed");
  cy.nodes().not(node).not(connected.connectedNodes()).each(n => {{
    n.removeClass("highlighted");
  }});
  node.addClass("highlighted");
}});

// ── Node tap → drill-down inline (single click) ──────
cy.on("tap", "node", function(evt) {{
  const node = evt.target;
  if (!DRILLDOWN_DATA[node.id()]) return;
  showDrilldown(DRILLDOWN_DATA[node.id()],
    node.data(`label_${{lang}}`) || node.data("label"),
    node.data("color"));
}});

let cy2 = null;

function showDrilldown(dd, label, color) {{
  const col = color || "#E74C3C";
  const labelBox = document.getElementById("drilldown-label-box");
  labelBox.textContent = label;
  labelBox.style.color = col;
  document.getElementById("drilldown-section").style.borderTopColor = col;
  document.body.classList.add("drilldown-active");

  if (cy2) {{ cy2.destroy(); cy2 = null; }}

  // Wait for CSS transition (350ms) before initializing so the container has its final size
  setTimeout(() => {{
    cy2 = cytoscape({{
      container: document.getElementById("cy2"),
      elements: dd.elements,
      style: CY_STYLE,
      layout: {{ name: "preset" }},
      wheelSensitivity: 0.3,
      minZoom: 0.1,
      maxZoom: 3,
    }});

    cy2.style()
      .selector("node")
      .style({{ "width": 90, "height": 26, "font-size": "9px", "text-max-width": "84px" }})
      .selector("node[node_type='provider']")
      .style({{ "width": 90, "height": 26, "font-size": "9px", "text-max-width": "84px" }})
      .update();

    cy2.resize();
    cy2.fit(undefined, 30);

    // ── cy2: node click → shared panel ───────────
    cy2.on("tap", "node", function(evt) {{
      const node = evt.target;
      showPanel(node);
      cy.elements().removeClass("dimmed highlighted");
      cy2.elements().addClass("dimmed");
      node.removeClass("dimmed");
      const connected = node.connectedEdges();
      connected.removeClass("dimmed").addClass("highlighted");
      connected.connectedNodes().removeClass("dimmed");
      node.addClass("highlighted");
    }});

    cy2.on("tap", function(evt) {{
      if (evt.target === cy2) {{
        currentNode = null;
        cy2.elements().removeClass("dimmed highlighted");
        document.getElementById("panel-header").style.display = "none";
        document.getElementById("empty-msg").style.display = "flex";
        document.getElementById("panel-content").style.display = "none";
      }}
    }});

    cy2.on("mouseover", "edge", function(evt) {{ evt.target.addClass("highlighted"); }});
    cy2.on("mouseout", "edge", function(evt) {{
      if (!evt.target.source().hasClass("highlighted")) evt.target.removeClass("highlighted");
    }});
  }}, 380);
}}

function closeDrilldown() {{
  document.body.classList.remove("drilldown-active");
  if (cy2) {{ cy2.destroy(); cy2 = null; }}
}}

// ── Click background → reset ─────────────────
cy.on("tap", function(evt) {{
  if (evt.target === cy) {{
    currentNode = null;
    history.replaceState(null, '', window.location.pathname + window.location.search);
    cy.elements().removeClass("dimmed highlighted");
    if (cy2) cy2.elements().removeClass("dimmed highlighted");
    document.getElementById("panel-header").style.display = "none";
    document.getElementById("empty-msg").style.display = "flex";
    document.getElementById("panel-content").style.display = "none";
  }}
}});

// ── Drilldown nodes: ↗ label + cursor + glow pulse ──
const cyContainer = document.getElementById("cy");
cy.on("mouseover", "node.has-drilldown", () => {{ cyContainer.style.cursor = "zoom-in"; }});
cy.on("mouseout",  "node.has-drilldown", () => {{ cyContainer.style.cursor = ""; }});

// Append ↗ indicator to label (function style overrides data reference)
cy.style()
  .selector(".has-drilldown")
  .style({{ "label": ele => ele.data("label") + "  ↗" }})
  .update();

(function pulseDrilldowns() {{
  cy.nodes(".has-drilldown").forEach(node => {{
    (function pulse(n) {{
      n.animate(
        {{ style: {{ "shadow-blur": 22, "shadow-opacity": 0.9, "border-width": 4, "border-color": "#FF6B6B" }} }},
        {{ duration: 950, easing: "ease-in-out", complete: () =>
          n.animate(
            {{ style: {{ "shadow-blur": 8, "shadow-opacity": 0.4, "border-width": 2, "border-color": "#E74C3C" }} }},
            {{ duration: 950, easing: "ease-in-out", complete: () => pulse(n) }}
          )
        }}
      );
    }})(node);
  }});
}})();

// ── Edge hover → show label ──────────────────
cy.on("mouseover", "edge", function(evt) {{
  evt.target.addClass("highlighted");
}});
cy.on("mouseout", "edge", function(evt) {{
  if (!evt.target.source().hasClass("highlighted")) {{
    evt.target.removeClass("highlighted");
  }}
}});
</script>

</body>
</html>"""
    return html


def generate_slides_html(data):
    """Generate a standalone slides HTML file from map data."""
    meta = data["meta"]
    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en

    STATUS_EMOJI = {"stable": "🟢", "evolving": "🟡", "emerging": "🔵", "deprecated": "🔴"}

    # Group nodes by layer — skip container (compound) nodes, they're visual groupings only
    by_layer = {}
    for node in data["nodes"]:
        if node.get("container"):
            continue
        by_layer.setdefault(node["layer"], []).append(node)

    def make_slides(lang):
        slides = []
        subtitle = "AI / LLM Ecosystem" if lang == "en" else "Écosystème IA / LLM"
        title = title_en if lang == "en" else title_fr
        slides.append(
            f'<div class="slide-type-title"><div class="slide-title-content">'
            f'<h1>{title}</h1><p class="subtitle">{subtitle}</p></div></div>'
        )
        layer_order = sorted(by_layer.keys(), reverse=True)
        for layer_id in layer_order:
            nodes = by_layer[layer_id]
            layer_label = t(data.get("layers", {}).get(layer_id, f"Layer {layer_id}"), lang)
            items = ""
            for n in nodes:
                lbl = t(n.get("label", ""), lang)
                desc = clean(t(n.get("description", ""), lang))
                short = (desc.split(". ")[0] + ".") if desc else ""
                emoji = STATUS_EMOJI.get(n.get("status", ""), "")
                items += f"<li>{emoji} <strong>{lbl}</strong>{' — ' + short if short else ''}</li>"
            slides.append(
                f'<div class="slide-layer-num">Layer {layer_id}</div>'
                f'<h2>{layer_label}</h2><ul>{items}</ul>'
            )
        for layer_id in layer_order:
            nodes = by_layer[layer_id]
            layer_label = t(data.get("layers", {}).get(layer_id, f"Layer {layer_id}"), lang)
            for n in nodes:
                lbl = t(n.get("label", ""), lang)
                desc = clean(t(n.get("description", ""), lang)).replace("\n", "<br>")
                emoji = STATUS_EMOJI.get(n.get("status", ""), "")
                status = n.get("status", "")
                slides.append(
                    f'<div class="slide-node-layer">{layer_label}</div>'
                    f'<h2>{emoji} {lbl}</h2>'
                    + (f'<p class="node-desc">{desc}</p>' if desc else "")
                    + f'<span class="slide-status status-{status}">{status}</span>'
                )
        total = sum(len(v) for v in by_layer.values())
        summary = "Summary" if lang == "en" else "Récapitulatif"
        layers_label = "layers" if lang == "en" else "couches"
        slides.append(
            f'<div class="slide-type-title"><div class="slide-title-content">'
            f'<h2>{summary}</h2>'
            f'<p class="stat">{total} concepts</p>'
            f'<p class="stat">{len(layer_order)} {layers_label}</p>'
            f'<p class="generated-from">{title}</p>'
            f'</div></div>'
        )
        return slides

    slides_en = json.dumps(make_slides("en"))
    slides_fr = json.dumps(make_slides("fr"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_en} — Slides</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ background:#0d1117; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:"Segoe UI",sans-serif; overflow:hidden }}
  #slide {{ background:#fff; width:min(92vw,960px); aspect-ratio:16/9; border-radius:12px; padding:48px 64px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 20px 60px rgba(0,0,0,.5); position:relative; overflow:hidden }}
  #slide h1 {{ font-size:2.4em; color:#1a237e; margin-bottom:16px }}
  #slide h2 {{ font-size:1.6em; color:#283593; border-bottom:2px solid #3949ab; padding-bottom:10px; margin-bottom:20px }}
  .subtitle {{ font-size:1.2em; color:#555 }}
  .slide-type-title {{ display:flex; align-items:center; justify-content:center; text-align:center; height:100% }}
  .slide-title-content {{ display:flex; flex-direction:column; gap:12px }}
  .slide-layer-num,.slide-node-layer {{ position:absolute; top:20px; right:28px; font-size:.75em; color:#9fa8da; font-weight:600; letter-spacing:1px; text-transform:uppercase }}
  ul {{ list-style:none; display:flex; flex-direction:column; gap:8px }}
  li {{ font-size:.9em; color:#333; line-height:1.4 }}
  li strong {{ color:#1a237e }}
  .node-desc {{ font-size:.92em; color:#444; line-height:1.7; margin-top:8px }}
  .slide-status {{ position:absolute; bottom:20px; right:28px; font-size:.72em; font-weight:600; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:10px; border:1.5px solid }}
  .status-stable {{ color:#2e7d32; border-color:#2e7d32 }}
  .status-evolving {{ color:#e65100; border-color:#e65100 }}
  .status-emerging {{ color:#1565c0; border-color:#1565c0 }}
  .status-deprecated {{ color:#b71c1c; border-color:#b71c1c }}
  .stat {{ font-size:1.4em; font-weight:700; color:#3949ab }}
  .generated-from {{ font-size:.85em; color:#999; margin-top:12px }}
  #nav {{ display:flex; align-items:center; gap:20px; margin-top:20px }}
  .nav-btn {{ background:#3949ab; color:#fff; border:none; border-radius:8px; padding:10px 24px; font-size:1em; cursor:pointer; transition:background .15s }}
  .nav-btn:hover {{ background:#283593 }}
  .nav-btn:disabled {{ background:#555; cursor:default }}
  #counter {{ color:#aaa; font-size:.9em; min-width:80px; text-align:center }}
  #progress {{ position:absolute; bottom:0; left:0; height:3px; background:#3949ab; transition:width .3s; border-radius:0 0 0 12px }}
  #lang-toggle {{ position:fixed; top:16px; right:16px; display:flex; gap:6px }}
  .lang-btn {{ background:none; border:1px solid #555; border-radius:4px; color:#aaa; padding:4px 10px; font-size:12px; cursor:pointer }}
  .lang-btn.active {{ background:white; color:#1a237e; border-color:white }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
<div id="lang-toggle">
  <button class="lang-btn active" onclick="setLang('en')">EN</button>
  <button class="lang-btn" onclick="setLang('fr')">FR</button>
</div>
<div id="slide"><div id="progress"></div><div id="slide-content"></div></div>
<div id="nav">
  <button class="nav-btn" id="prev">&#8592;</button>
  <span id="counter"></span>
  <button class="nav-btn" id="next">&#8594;</button>
</div>
<script>
const ALL_SLIDES = {{ en: {slides_en}, fr: {slides_fr} }};
let lang = 'en', cur = 0;
function slides() {{ return ALL_SLIDES[lang]; }}
function render() {{
  document.getElementById('slide-content').innerHTML = slides()[cur];
  document.getElementById('counter').textContent = (cur+1) + ' / ' + slides().length;
  document.getElementById('prev').disabled = cur === 0;
  document.getElementById('next').disabled = cur === slides().length - 1;
  document.getElementById('progress').style.width = ((cur+1)/slides().length*100) + '%';
}}
function go(d) {{ cur = Math.max(0, Math.min(slides().length-1, cur+d)); render(); }}
function setLang(l) {{
  lang = l; cur = 0;
  document.querySelectorAll('#lang-toggle .lang-btn').forEach(b => b.classList.toggle('active', b.textContent === l.toUpperCase()));
  render();
}}
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.addEventListener('keydown', e => {{
  if (e.key==='ArrowRight'||e.key==='ArrowDown') go(1);
  if (e.key==='ArrowLeft'||e.key==='ArrowUp') go(-1);
}});
render();
</script>
</body></html>"""


def main():
    maps = load_maps()
    print(f"Reading {DATA_FILE}...")
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)

    elements = build_elements(data)
    html = generate_html(data, elements, maps=maps, current_output=str(OUTPUT_FILE))

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    # Generate companion slides file
    slides_file = OUTPUT_FILE.with_name(OUTPUT_FILE.stem + "-slides.html")
    with open(slides_file, "w") as f:
        f.write(generate_slides_html(data))

    node_count = sum(1 for e in elements if "position" in e)
    edge_count = sum(1 for e in elements if "position" not in e and "classes" not in e)
    print(f"✓ Generated {OUTPUT_FILE}")
    print(f"  {node_count} nodes · {edge_count} edges")
    print(f"  ↳ Slides: {slides_file.name}")


if __name__ == "__main__":
    main()
