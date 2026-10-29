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
from site_chrome import head_assets, site_header, chrome_script

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
    "stable": "#2F8F5B",
    "evolving": "#B7791F",
    "emerging": "#6B4FBB",
    "deprecated": "#7A7D85",
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

    context_html = (
        f'<span class="sh-sep">/</span><span class="sh-title" id="main-title">{title_en}</span>'
        f'<span class="sh-meta">v{meta["version"]} · {meta["date"]}</span>'
    )
    header_html = site_header(active="maps", current=Path(current_output).name, context=context_html)

    drilldown_datasets = load_drilldown_datasets(data, maps or [])
    drilldown_datasets_js = json.dumps(drilldown_datasets)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title_en} — Mind Map IA</title>
<script src="cytoscape.min.js"></script>
{head_assets()}
<style>
  html, body {{ height: 100%; }}
  body {{
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
  }}

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
    min-width: 0;
    min-height: 0;
    overflow: hidden;
  }}
  #cy-wrapper {{
    position: relative;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }}
  #cy {{
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 1px 1px, var(--line) 1px, transparent 0) 0 0 / 24px 24px,
      var(--bg);
  }}

  /* ── Drill-down ── */
  #drilldown-section {{
    flex: 0 0 0;
    min-height: 0;
    overflow: hidden;
    position: relative;
    border-top: 1px solid var(--line-strong);
    background: var(--surface);
    transition: flex-basis 0.35s ease;
  }}
  body.drilldown-active #drilldown-section {{ flex: 0 0 45%; }}
  #drilldown-label-box {{
    position: absolute;
    top: 12px;
    left: 16px;
    padding: 4px 10px;
    font: 500 11px/1.2 var(--f-mono);
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--ink);
    background: var(--sunk);
    border-radius: 99px;
    z-index: 10;
    white-space: nowrap;
    pointer-events: none;
  }}
  #drilldown-close {{
    position: absolute;
    top: 10px;
    right: 12px;
    z-index: 10;
    width: 30px; height: 30px;
    display: grid; place-items: center;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--ink-2);
    cursor: pointer;
    font-size: 13px;
  }}
  #drilldown-close:hover {{ color: var(--ink); border-color: var(--line-strong); }}
  #cy2 {{ width: 100%; height: 100%; }}

  /* ── Side panel ── */
  #panel {{
    width: 360px;
    background: var(--surface);
    border-left: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
  }}
  #panel-header {{
    padding: 24px 24px 4px;
    position: relative;
  }}
  #panel-header .node-meta {{
    font: 500 11px/1.3 var(--f-mono);
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    padding-right: 40px;
  }}
  #panel-header .node-label {{
    font-size: 24px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin: 10px 0 12px;
    text-wrap: balance;
  }}
  #panel-header .node-status {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: 99px;
    font: 500 11px/1 var(--f-mono);
    letter-spacing: .02em;
  }}
  #panel-header .node-status::before {{
    content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor;
  }}
  #share-btn {{
    position: absolute;
    top: 18px;
    right: 18px;
    width: 32px; height: 32px;
    display: grid; place-items: center;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--muted);
    cursor: pointer;
    transition: all 0.15s;
  }}
  #share-btn svg {{ width: 15px; height: 15px; }}
  #share-btn:hover {{ color: var(--ink); border-color: var(--line-strong); }}
  #share-btn.copied {{ color: var(--ok); border-color: var(--ok); }}

  #panel-body {{
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px 24px;
  }}
  #panel-body .section-title {{
    font: 500 11px/1 var(--f-mono);
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 8px 0 10px;
  }}
  #panel-body .description {{
    font-size: 15px;
    line-height: 1.65;
    color: var(--ink-2);
    margin-bottom: 22px;
  }}
  #panel-body .description p {{ margin: 0 0 10px; }}
  #panel-body .description p:last-child {{ margin-bottom: 0; }}
  #panel-body .description ol,
  #panel-body .description ul {{ margin: 8px 0 10px 18px; padding: 0; }}
  #panel-body .description li {{ margin-bottom: 4px; }}
  #panel-body .description strong {{ font-weight: 600; color: var(--ink); }}
  .gloss-link {{
    text-decoration: underline;
    text-decoration-thickness: 1px;
    text-decoration-color: color-mix(in srgb, var(--accent) 55%, transparent);
    text-underline-offset: 3px;
    cursor: pointer;
    color: inherit;
  }}
  .gloss-link:hover {{ color: var(--accent); }}
  .panel-link {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
    color: var(--ink);
    text-decoration: none;
    padding: 10px 12px;
    border: 1px solid var(--line);
    border-radius: 9px;
    transition: border-color 0.15s, color 0.15s;
  }}
  .panel-link::after {{ content: "↗"; color: var(--muted); }}
  .panel-link:hover {{ border-color: var(--line-strong); color: var(--accent); }}
  .panel-link .link-icon {{ display: none; }}
  .drilldown-hint {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--accent);
    background: var(--accent-soft);
    border-radius: 8px;
    padding: 7px 11px;
    cursor: zoom-in;
  }}
  #panel-body .since {{ font: 13px var(--f-mono); color: var(--ink-2); }}

  .empty-panel {{
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    gap: 14px;
    height: 100%;
    color: var(--muted);
    padding: 8px 4px;
  }}
  .empty-panel .arrow {{
    width: 40px; height: 40px; display: grid; place-items: center;
    border: 1px dashed var(--line-strong); border-radius: 50%;
    font-size: 16px; color: var(--ink-2);
  }}
  .empty-panel p {{ font-size: 15px; line-height: 1.55; max-width: 24em; margin: 0; }}

  /* ── Legend ── */
  #legend {{
    padding: 16px 24px 20px;
    border-top: 1px solid var(--line);
    display: flex;
    gap: 20px;
  }}
  .legend-col {{ flex: 1; min-width: 0; }}
  #legend h3 {{
    font: 500 10.5px/1 var(--f-mono);
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 10px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    color: var(--ink-2);
    margin-bottom: 5px;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 3px;
    flex-shrink: 0;
  }}
  .status-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    font: 12px var(--f-ui);
    color: var(--ink-2) !important;
    border: 0 !important;
  }}
  .status-badge::before {{
    content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--sb, currentColor);
  }}

  /* ── Category boxes ── */
  .cat-box {{
    position: absolute;
    border: 1.5px solid;
    border-radius: 16px;
    pointer-events: none;
    box-sizing: border-box;
  }}
  .cat-box-label {{
    position: absolute;
    top: -9px;
    left: 14px;
    font: 500 10.5px/1.2 var(--f-mono);
    letter-spacing: .08em;
    text-transform: uppercase;
    background: var(--bg);
    padding: 1px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}

  /* ── Controls ── */
  #controls {{
    position: absolute;
    bottom: max(16px, env(safe-area-inset-bottom, 0px));
    left: max(16px, env(safe-area-inset-left, 0px));
    display: flex;
    gap: 2px;
    padding: 4px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 12px;
    box-shadow: var(--shadow);
    z-index: 10;
  }}
  .ctrl-btn {{
    position: relative;
    width: 34px;
    height: 34px;
    background: none;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    color: var(--ink-2);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, color 0.15s;
  }}
  .ctrl-btn:hover {{ background: var(--sunk); color: var(--ink); }}
  .ctrl-btn.saved {{ color: var(--ok); }}
  .ctrl-btn[data-tip]:hover::after {{
    content: attr(data-tip);
    position: absolute;
    bottom: 44px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--ink);
    color: var(--surface);
    font: 12px var(--f-ui);
    white-space: nowrap;
    padding: 5px 9px;
    border-radius: 6px;
    pointer-events: none;
    z-index: 100;
  }}
  .hint-bar {{
    position: absolute;
    right: 16px;
    bottom: 22px;
    font: 12px var(--f-mono);
    color: var(--muted);
    pointer-events: none;
    z-index: 5;
  }}

  @media (max-width: 760px) {{
    .hint-bar {{ display: none; }}
    .main {{ flex-direction: column; }}
    #cy-area {{ min-height: 0; flex: 1 1 auto; }}
    #cy-wrapper {{ min-height: 300px; }}
    body.drilldown-active #drilldown-section {{ flex-basis: 38%; }}
    #drilldown-label-box {{ max-width: calc(100vw - 90px); overflow: hidden; text-overflow: ellipsis; }}
    #panel {{
      width: 100%;
      height: 40dvh;
      max-height: 46dvh;
      min-height: 200px;
      border-left: 0;
      border-top: 1px solid var(--line);
    }}
    #panel-header {{ padding: 16px 60px 0 16px; }}
    #panel-header .node-label {{ font-size: 19px; margin: 6px 0 8px; }}
    #panel-body {{ padding: 12px 16px 18px; }}
    #legend {{ display: none; }}
    #controls {{ left: 10px; bottom: 10px; }}
    .ctrl-btn[data-tip]:hover::after {{ display: none; }}
    .empty-panel .arrow {{ transform: rotate(90deg); }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<div class="main">
  <div id="cy-area">
    <div id="cy-wrapper">
      <div id="cy"></div>
      <div id="cat-boxes" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:hidden;"></div>
      <div id="controls">
        <button class="ctrl-btn" onclick="cy.fit(undefined, 40)"
          data-tip-en="Fit all nodes" data-tip-fr="Tout afficher" aria-label="Fit">⤢</button>
        <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*1.2)"
          data-tip-en="Zoom in" data-tip-fr="Zoom avant" aria-label="Zoom in">+</button>
        <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*0.8)"
          data-tip-en="Zoom out" data-tip-fr="Zoom arrière" aria-label="Zoom out">−</button>
        <button class="ctrl-btn" id="reset-btn" onclick="resetLayout()"
          data-tip-en="Reset positions" data-tip-fr="Réinitialiser" aria-label="Reset">↺</button>
        <button class="ctrl-btn" onclick="exportLayout()"
          data-tip-en="Save layout" data-tip-fr="Sauvegarder la vue" aria-label="Save layout">⤓</button>
        <button class="ctrl-btn" onclick="window.open('{OUTPUT_FILE.stem}-slides.html','_blank')"
          data-tip-en="Open as slides" data-tip-fr="Ouvrir en slides" aria-label="Slides">▤</button>
      </div>
      <div class="hint-bar" id="hint-text">Click a node to explore · Scroll to zoom · Drag to pan</div>
    </div>
    <div id="drilldown-section">
      <div id="drilldown-label-box"></div>
      <button id="drilldown-close" onclick="closeDrilldown()" aria-label="Close">✕</button>
      <div id="cy2"></div>
    </div>
  </div>

  <div id="panel">
    <div id="panel-header" style="display:none;">
      <button id="share-btn" onclick="shareNode()" title="Copy link" aria-label="Copy link"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg></button>
      <div class="node-meta" id="ph-meta"></div>
      <div class="node-label" id="ph-label"></div>
      <span class="node-status" id="ph-status"></span>
      <div id="ph-drilldown" style="display:none;">
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
        <div id="pc-links" style="display:none; margin-top:18px; display:flex; flex-direction:column; gap:8px;"></div>
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
      `<div class="legend-item"><span class="status-badge" style="--sb:${{STATUS_COLORS[k]}}">${{v}}</span></div>`
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


// ── Theme-aware graph styling ────────────────
// Category colours come from the YAML; nodes get a soft tint of that colour
// as fill and a deeper shade as border, recomputed when the theme changes.
function cssVar(name) {{
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}}
function hexToRgb(h) {{
  h = (h || '#999999').replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}}
function mix(a, b, t) {{
  const x = hexToRgb(a), y = hexToRgb(b);
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('');
}}
function themeColors() {{
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {{
    dark,
    bg: cssVar('--bg') || '#FAFAF8',
    surface: cssVar('--surface') || '#FFFFFF',
    ink: cssVar('--ink') || '#17181C',
    muted: cssVar('--muted') || '#7A7D85',
    edge: cssVar('--line-strong') || '#D2D2CC',
    accent: cssVar('--accent') || '#D8432E',
  }};
}}
function tintNodes(cyInst, th) {{
  cyInst.batch(() => {{
    cyInst.nodes().forEach(n => {{
      const c = n.data('color') || '#999999';
      if (th.dark) {{
        n.data('fill', mix(c, th.bg, 0.72));
        n.data('stroke', mix(c, '#ffffff', 0.1));
      }} else {{
        n.data('fill', mix(c, '#ffffff', 0.72));
        n.data('stroke', mix(c, '#000000', 0.12));
      }}
    }});
  }});
}}

function buildCyStyle(th) {{
  return [
    // Provider nodes — ellipse to distinguish from models
    {{
      selector: "node[node_type='provider']",
      style: {{
        "width": {node_w},
        "height": {node_h},
        "shape": "ellipse",
        "background-color": "data(fill)",
        "background-opacity": 1,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-family": "Geist, system-ui, sans-serif",
        "font-size": "{node_font}px",
        "font-weight": "600",
        "color": th.ink,
        "border-width": 1.5,
        "border-color": "data(stroke)",
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
        "background-color": "data(fill)",
        "background-opacity": 1,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-family": "Geist, system-ui, sans-serif",
        "font-size": "{node_font}px",
        "font-weight": "500",
        "color": th.ink,
        "border-width": 1.5,
        "border-color": "data(stroke)",
        "border-opacity": 1,
        "text-wrap": "wrap",
        "text-max-width": "{node_text_max}px",
        "overlay-padding": "6px",
        "overlay-opacity": 0,
        "transition-property": "border-color, border-width, opacity",
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
        "font-weight": "600",
      }}
    }},
    // Status: evolving → warm border
    {{
      selector: ".status-evolving",
      style: {{
        "border-color": "{STATUS_LABEL_COLOR['evolving']}",
        "border-width": 2,
      }}
    }},
    // Status: emerging → dashed violet border
    {{
      selector: ".status-emerging",
      style: {{
        "border-color": "{STATUS_LABEL_COLOR['emerging']}",
        "border-width": 2,
        "border-style": "dashed",
      }}
    }},
    // Nodes with drill-down → accent border + soft halo
    {{
      selector: ".has-drilldown",
      style: {{
        "border-color": th.accent,
        "border-width": 2,
        "shadow-blur": 14,
        "shadow-color": th.accent,
        "shadow-offset-x": 0,
        "shadow-offset-y": 0,
        "shadow-opacity": 0.25,
        "label": ele => ele.data("label") + "  ↗",
      }}
    }},
    // Status: deprecated → muted
    {{
      selector: ".status-deprecated",
      style: {{
        "background-opacity": 0.5,
        "color": th.muted,
        "border-color": th.edge,
        "border-style": "dotted",
      }}
    }},
    // Hover / connected
    {{
      selector: "node:active, node.highlighted",
      style: {{
        "border-width": 2,
        "border-color": th.ink,
        "z-index": 999,
      }}
    }},
    // Selected
    {{
      selector: "node:selected",
      style: {{
        "border-width": 2.5,
        "border-color": th.accent,
      }}
    }},
    // Compound (container / parent) nodes — visual box only, no Cytoscape label.
    // Labels are rendered as HTML overlays in drawCategoryBoxes() so they match
    // the cat-box-label style exactly (same font, size, position).
    {{
      selector: ":parent",
      style: {{
        "background-color": "data(color)",
        "background-opacity": th.dark ? 0.06 : 0.045,
        "border-width": 1.5,
        "border-color": "data(color)",
        "border-opacity": 0.45,
        "border-style": "solid",
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
        "width": 1.2,
        "line-color": th.edge,
        "target-arrow-color": th.edge,
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        "arrow-scale": 0.8,
        "label": "",
        "font-family": "Geist Mono, ui-monospace, monospace",
        "font-size": "9px",
        "color": th.muted,
        "text-background-color": th.bg,
        "text-background-opacity": 0.9,
        "text-background-padding": "3px",
        "text-background-shape": "round-rectangle",
        "opacity": 0.8,
      }}
    }},
    {{
      selector: "edge.highlighted",
      style: {{
        "width": 2,
        "line-color": th.accent,
        "target-arrow-color": th.accent,
        "label": "data(label)",
        "opacity": 1,
        "z-index": 999,
      }}
    }},
    // Dimmed (when a node is selected)
    {{
      selector: ".dimmed",
      style: {{
        "opacity": 0.18,
      }}
    }},
  ];
}}

let THEME = themeColors();
tintNodesData(elements);
const CY_STYLE = buildCyStyle(THEME);

// Pre-compute tints on raw element data so the first paint is already right.
function tintNodesData(els) {{
  els.forEach(el => {{
    if (!el.data || el.group === 'edges' || el.data.source) return;
    const c = el.data.color || '#999999';
    el.data.fill = THEME.dark ? mix(c, THEME.bg, 0.72) : mix(c, '#ffffff', 0.72);
    el.data.stroke = THEME.dark ? mix(c, '#ffffff', 0.1) : mix(c, '#000000', 0.12);
  }});
}}

window.addEventListener('mmia-themechange', () => {{
  THEME = themeColors();
  [cy, cy2].forEach(inst => {{
    if (!inst) return;
    tintNodes(inst, THEME);
    inst.style(buildCyStyle(THEME));
  }});
  if (cy2) applyDrilldownSizing(cy2);
  drawCategoryBoxes();
}});

const cy = cytoscape({{
  container: document.getElementById("cy"),
  elements: elements,
  style: CY_STYLE,
  layout: {{
    name: "preset",
  }},
  wheelSensitivity: 0.3,
  minZoom: 0.08,
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
function groupInk(c) {{ return THEME.dark ? mix(c, '#ffffff', 0.25) : mix(c, '#000000', 0.38); }}

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
    lbl.style.color = groupInk(cat.color);
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
    lbl.style.color = groupInk(n.data('color'));
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
  const hasSavedPositions = loadPositions();
  if (!hasSavedPositions) {{
    cy.fit(undefined, 40);
  }}
  // Fonts and the final container size settle after first paint: refit once loaded.
  window.addEventListener('load', () => {{
    cy.resize();
    if (!hasSavedPositions && !window.location.hash) cy.fit(undefined, 40);
    drawCategoryBoxes();
  }});
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
    const icon = btn.innerHTML;
    btn.textContent = '✓';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.innerHTML = icon; btn.classList.remove('copied'); }}, 1800);
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
  statusEl.style.background = STATUS_COLORS[d.status] + "1F";
  statusEl.style.color = STATUS_COLORS[d.status];

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
    tintNodesData(dd.elements);
    cy2 = cytoscape({{
      container: document.getElementById("cy2"),
      elements: dd.elements,
      style: buildCyStyle(THEME),
      layout: {{ name: "preset" }},
      wheelSensitivity: 0.3,
      minZoom: 0.1,
      maxZoom: 3,
    }});
    applyDrilldownSizing(cy2);

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

function applyDrilldownSizing(inst) {{
  inst.style()
    .selector("node")
    .style({{ "width": 90, "height": 26, "font-size": "9px", "text-max-width": "84px" }})
    .selector("node[node_type='provider']")
    .style({{ "width": 90, "height": 26, "font-size": "9px", "text-max-width": "84px" }})
    .update();
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

// Gentle halo breathing on explorable nodes (the ↗ label suffix lives in buildCyStyle)
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
  cy.nodes(".has-drilldown").forEach(node => {{
    (function pulse(n) {{
      n.animate(
        {{ style: {{ "shadow-blur": 20, "shadow-opacity": 0.45 }} }},
        {{ duration: 1400, easing: "ease-in-out", complete: () =>
          n.animate(
            {{ style: {{ "shadow-blur": 10, "shadow-opacity": 0.15 }} }},
            {{ duration: 1400, easing: "ease-in-out", complete: () => pulse(n) }}
          )
        }}
      );
    }})(node);
  }});
}}

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
{chrome_script()}
</body>
</html>"""
    return html


def generate_slides_html(data):
    """Generate a standalone slides HTML file from map data."""
    meta = data["meta"]
    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en

    STATUS_EMOJI = {k: f'<span class="sd sd-{k}"></span>' for k in ("stable", "evolving", "emerging", "deprecated")}

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
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title_en} — Slides</title>
{head_assets()}
<style>
  body {{ background:var(--sunk); display:flex; flex-direction:column; align-items:center; justify-content:center; gap:20px; height:100vh; height:100dvh; overflow:hidden; padding:16px }}
  #slide {{ background:var(--surface); color:var(--ink); width:min(92vw,1000px); aspect-ratio:16/9; border:1px solid var(--line); border-radius:16px; padding:clamp(24px,5vw,56px) clamp(24px,6vw,72px); display:flex; flex-direction:column; justify-content:center; box-shadow:var(--shadow); position:relative; overflow:hidden; font-size:clamp(12px,1.6vw,18px) }}
  #slide h1 {{ font-size:2.6em; font-weight:600; letter-spacing:-.03em; line-height:1.05; margin:0 0 14px }}
  #slide h2 {{ font-size:1.7em; font-weight:600; letter-spacing:-.02em; line-height:1.15; margin:0 0 22px; display:flex; align-items:center; gap:.45em }}
  .subtitle {{ font-family:var(--f-read); font-size:1.3em; color:var(--ink-2); margin:0 }}
  .slide-type-title {{ display:flex; align-items:center; justify-content:center; text-align:center; height:100% }}
  .slide-title-content {{ display:flex; flex-direction:column; gap:12px; align-items:center }}
  .slide-layer-num,.slide-node-layer {{ position:absolute; top:24px; left:clamp(24px,6vw,72px); font:500 .7em/1 var(--f-mono); color:var(--muted); letter-spacing:.08em; text-transform:uppercase }}
  ul {{ list-style:none; display:flex; flex-direction:column; gap:10px; margin:0; padding:0 }}
  li {{ font-size:.92em; color:var(--ink-2); line-height:1.45; display:flex; gap:10px; align-items:baseline }}
  li strong {{ color:var(--ink); font-weight:600 }}
  .sd {{ display:inline-block; width:.5em; height:.5em; border-radius:50%; flex-shrink:0; transform:translateY(-.1em) }}
  .sd-stable {{ background:var(--ok) }} .sd-evolving {{ background:var(--warn) }}
  .sd-emerging {{ background:var(--new) }} .sd-deprecated {{ background:var(--muted) }}
  .node-desc {{ font-family:var(--f-read); font-size:1.15em; color:var(--ink); line-height:1.6; margin:4px 0 0; max-width:38em }}
  .slide-status {{ position:absolute; bottom:24px; right:clamp(24px,6vw,72px); font:500 .7em/1 var(--f-mono); letter-spacing:.04em; padding:5px 10px; border-radius:99px; border:1px solid currentColor }}
  .status-stable {{ color:var(--ok) }}
  .status-evolving {{ color:var(--warn) }}
  .status-emerging {{ color:var(--new) }}
  .status-deprecated {{ color:var(--muted) }}
  .stat {{ font-size:1.5em; font-weight:600; margin:0 }}
  .generated-from {{ font:.8em var(--f-mono); color:var(--muted); margin-top:12px }}
  #nav {{ display:flex; align-items:center; gap:14px }}
  .nav-btn {{ width:44px; height:44px; display:grid; place-items:center; background:var(--surface); color:var(--ink); border:1px solid var(--line-strong); border-radius:12px; font-size:1.1em; cursor:pointer; transition:background .15s, border-color .15s }}
  .nav-btn:hover {{ border-color:var(--ink) }}
  .nav-btn:disabled {{ opacity:.35; cursor:default }}
  #counter {{ color:var(--muted); font:13px var(--f-mono); min-width:80px; text-align:center }}
  #progress {{ position:absolute; bottom:0; left:0; height:3px; background:var(--accent); transition:width .3s }}
  .slides-top {{ position:fixed; top:max(16px, env(safe-area-inset-top, 0px)); left:16px; right:16px; display:flex; justify-content:space-between; align-items:center; gap:10px }}
  .slides-top a {{ font-size:14px; color:var(--ink-2); text-decoration:none }}
  .slides-top a:hover {{ color:var(--accent) }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
<div class="slides-top">
  <a href="{OUTPUT_FILE.name}">← {title_en}</a>
  <div class="lang-toggle" id="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
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
{chrome_script()}
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
