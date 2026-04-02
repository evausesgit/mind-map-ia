#!/usr/bin/env python3
"""
Generate a standalone HTML mind map from ecosystem.yaml
Usage: python scripts/generate.py
"""

import yaml
import json
from pathlib import Path

import sys

ROOT = Path(__file__).parent.parent

# CLI: python generate.py [input.yaml [output.html]]
DATA_FILE  = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "ecosystem.yaml"
OUTPUT_FILE = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "web" / "index.html"

# ── Layout constants ──────────────────────────────────────────
# Horizontal layout: Layer 1 (Foundations) on the RIGHT, Layer 5 (Dev Tools) on the LEFT
# Layer 2 has two columns: providers (right) and models (left)
LAYER_X = {1: 1100, 2: 400, 3: -200, 4: -700, 5: -1200}
LAYER_X_PROVIDERS = 750   # providers column, between layer 1 and layer 2 models
NODE_SPACING_Y = 85   # vertical spacing between nodes in the same layer
NODE_WIDTH = 140
NODE_HEIGHT = 44

STATUS_BORDER = {
    "stable":    {"width": 2,  "style": "solid",  "dash": "none"},
    "evolving":  {"width": 3,  "style": "solid",  "dash": "none"},
    "emerging":  {"width": 3,  "style": "dashed", "dash": "8 4"},
    "deprecated":{"width": 1,  "style": "dotted", "dash": "4 4"},
}

STATUS_LABEL_COLOR = {
    "stable":    "#27AE60",
    "evolving":  "#E67E22",
    "emerging":  "#8E44AD",
    "deprecated":"#95A5A6",
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
    1: "LAYER 1", 2: "LAYER 2", 3: "LAYER 3", 4: "LAYER 4", 5: "LAYER 5",
}

LANGS = ["en", "fr"]


def t(field, lang):
    """Extract text from a field that is either a plain string or {en:..., fr:...}."""
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def clean(text):
    return " ".join(text.strip().split())


def build_elements(data):
    category_colors = {c["id"]: c["color"] for c in data["categories"]}
    raw_layers = data.get("layers", DEFAULT_LAYER_LABELS)
    layer_labels = {}
    for k, v in raw_layers.items():
        layer_labels[int(k)] = v  # v may be a string or {en:..., fr:...}

    # Group nodes by layer
    by_layer = {}
    for node in data["nodes"]:
        by_layer.setdefault(node["layer"], []).append(node)

    elements = []

    # Add actual nodes with absolute positions (horizontal layout)
    for layer_id, nodes in sorted(by_layer.items()):
        # Layer 2: split providers (right col) vs models (left col)
        if layer_id == 2:
            providers = [n for n in nodes if n.get("node_type") == "provider"]
            models    = [n for n in nodes if n.get("node_type") != "provider"]
            buckets = [(LAYER_X_PROVIDERS, providers), (LAYER_X[2], models)]
        else:
            buckets = [(LAYER_X[layer_id], nodes)]

        for x_pos, bucket in buckets:
            n = len(bucket)
            for i, node in enumerate(bucket):
                y = (i - (n - 1) / 2) * NODE_SPACING_Y

                # Build multilingual data fields
                node_data = {
                    "id":          node["id"],
                    "label":       t(node.get("label", ""), "en"),  # default lang
                    "category":    node["category"],
                    "subcategory": node.get("subcategory", ""),
                    "node_type":   node.get("node_type", ""),
                    "layer":       node["layer"],
                    "status":      node["status"],
                    "since":       str(node["since"]),
                    "color":       category_colors.get(node["category"], "#BDC3C7"),
                    "layerLabel":  t(layer_labels.get(layer_id, f"Layer {layer_id}"), "en"),
                }
                for lang in LANGS:
                    node_data[f"label_{lang}"]       = t(node.get("label", ""), lang)
                    node_data[f"description_{lang}"] = clean(t(node.get("description", ""), lang))
                    node_data[f"layerLabel_{lang}"]  = t(layer_labels.get(layer_id, f"Layer {layer_id}"), lang)

                elements.append({
                    "data":     node_data,
                    "position": {"x": x_pos, "y": y},
                    "classes":  f"status-{node['status']}"
                })

    # Add edges
    for edge in data["edges"]:
        elements.append({
            "data": {
                "id": f"{edge['from']}__{edge['to']}",
                "source": edge["from"],
                "target": edge["to"],
                "label": edge.get("label", ""),
                "etype": edge.get("type", ""),
            }
        })

    return elements


def generate_html(data, elements):
    meta = data["meta"]
    categories = data["categories"]
    elements_json = json.dumps(elements, indent=2)

    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en
    titles_js = json.dumps({"en": title_en, "fr": title_fr})

    # Build legend per lang
    def legend_items(lang):
        return "".join(
            f'<div class="legend-item"><span class="legend-dot" style="background:{c["color"]}"></span>'
            f'{t(c.get("label",""), lang)}</div>'
            for c in categories
        )

    status_labels = {
        "en": {"stable": "stable", "evolving": "evolving", "emerging": "emerging", "deprecated": "deprecated"},
        "fr": {"stable": "stable",  "evolving": "en évolution", "emerging": "émergent", "deprecated": "obsolète"},
    }
    status_labels_js = json.dumps(status_labels)

    panel_labels = {
        "en": {"click_hint": "Click any node to see its definition and connections",
               "description": "Description", "since": "Since"},
        "fr": {"click_hint": "Cliquez sur un nœud pour voir sa définition et ses connexions",
               "description": "Description", "since": "Depuis"},
    }
    panel_labels_js = json.dumps(panel_labels)

    legend_en = legend_items("en")
    legend_fr = legend_items("fr")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
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
    background: #1A1A2E;
    color: white;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    border-bottom: 3px solid #E74C3C;
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

  .main {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}

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
    padding: 16px 20px;
    border-top: 1px solid #F0F0F0;
    background: #FAFAFA;
  }}
  #legend h3 {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #95A5A6;
    margin-bottom: 10px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #555;
    margin-bottom: 5px;
  }}
  .legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 3px;
    flex-shrink: 0;
  }}
  .status-badge {{
    border: 1.5px solid;
    border-radius: 10px;
    padding: 1px 8px;
    font-size: 10px;
    font-weight: 600;
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
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    <div>
      <h1 id="main-title">{title_en}</h1>
      <div class="meta">v{meta["version"]} · {meta["date"]}</div>
    </div>
    <div class="lang-toggle">
      <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
      <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
    </div>
  </div>
  <div class="meta" id="hint-text">Click a node to explore · Scroll to zoom · Drag to pan</div>
</header>

<div class="main">
  <div style="position:relative;flex:1;overflow:hidden;">
    <div id="cy"></div>
    <div id="controls">
      <button class="ctrl-btn" onclick="cy.fit()" title="Fit all">⊞</button>
      <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*1.2)" title="Zoom in">+</button>
      <button class="ctrl-btn" onclick="cy.zoom(cy.zoom()*0.8)" title="Zoom out">−</button>
    </div>
  </div>

  <div id="panel">
    <div id="panel-header" style="display:none;">
      <div class="node-label" id="ph-label"></div>
      <div class="node-meta" id="ph-meta"></div>
      <span class="node-status" id="ph-status"></span>
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
      </div>
    </div>
    <div id="legend">
      <h3 id="legend-cat-title">Categories</h3>
      <div id="legend-en">{legend_en}</div>
      <div id="legend-fr" style="display:none">{legend_fr}</div>
      <h3 style="margin-top:12px;" id="legend-status-title">Status</h3>
      <div id="status-legend-items"></div>
    </div>
  </div>
</div>

<script>
const elements = {elements_json};
const TITLES        = {titles_js};
const STATUS_LABELS = {status_labels_js};
const PANEL_LABELS  = {panel_labels_js};
const STATUS_COLORS = {json.dumps(STATUS_LABEL_COLOR)};

let lang = 'en';

function setLang(newLang) {{
  lang = newLang;

  // Toggle buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.dataset.lang === lang);
  }});

  // Header title
  document.getElementById('main-title').textContent = TITLES[lang];

  // Hint text
  document.getElementById('hint-text').textContent =
    lang === 'fr' ? 'Cliquez sur un nœud · Molette pour zoomer · Glisser pour naviguer'
                  : 'Click a node to explore · Scroll to zoom · Drag to pan';

  // Legend
  document.getElementById('legend-en').style.display = lang === 'en' ? '' : 'none';
  document.getElementById('legend-fr').style.display = lang === 'fr' ? '' : 'none';
  document.getElementById('legend-cat-title').textContent =
    lang === 'fr' ? 'Catégories' : 'Categories';
  document.getElementById('legend-status-title').textContent =
    lang === 'fr' ? 'Statut' : 'Status';
  renderStatusLegend();

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


const cy = cytoscape({{
  container: document.getElementById("cy"),
  elements: elements,
  style: [
    // Provider nodes — ellipse to distinguish from models
    {{
      selector: "node[node_type='provider']",
      style: {{
        "width": {NODE_WIDTH},
        "height": {NODE_HEIGHT},
        "shape": "ellipse",
        "background-color": "data(color)",
        "background-opacity": 0.85,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-size": "12px",
        "font-weight": "700",
        "color": "#1A1A2E",
        "border-width": 2,
        "border-color": "data(color)",
        "text-wrap": "wrap",
        "text-max-width": "120px",
      }}
    }},
    // Nodes
    {{
      selector: "node",
      style: {{
        "width": {NODE_WIDTH},
        "height": {NODE_HEIGHT},
        "shape": "round-rectangle",
        "background-color": "data(color)",
        "background-opacity": 0.9,
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-size": "12px",
        "font-weight": "600",
        "color": "#1A1A2E",
        "border-width": 2,
        "border-color": "data(color)",
        "border-opacity": 1,
        "text-wrap": "wrap",
        "text-max-width": "130px",
        "overlay-padding": "6px",
        "transition-property": "border-color, border-width, background-opacity",
        "transition-duration": "0.15s",
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
  ],
  layout: {{
    name: "preset",
  }},
  wheelSensitivity: 0.3,
  minZoom: 0.2,
  maxZoom: 3,
}});

// ── Fit on load ──────────────────────────────
cy.ready(() => {{
  cy.fit(undefined, 40);
}});

let currentNode = null;

function showPanel(node) {{
  currentNode = node;
  const d = node.data();
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
  document.getElementById("pc-desc").textContent = d[`description_${{lang}}`] || "";
  document.getElementById("pc-since").textContent = d.since;
}}

// ── Node click → panel ───────────────────────
cy.on("tap", "node", function(evt) {{
  const node = evt.target;

  showPanel(node);

  // Highlight node + connected edges/nodes
  cy.elements().addClass("dimmed");
  node.removeClass("dimmed");
  const connected = node.connectedEdges();
  connected.removeClass("dimmed").addClass("highlighted");
  connected.connectedNodes().removeClass("dimmed");
  cy.nodes().not(node).not(connected.connectedNodes()).each(n => {{
    n.removeClass("highlighted");
  }});
  node.addClass("highlighted");
}});

// ── Click background → reset ─────────────────
cy.on("tap", function(evt) {{
  if (evt.target === cy) {{
    currentNode = null;
    cy.elements().removeClass("dimmed highlighted");
    document.getElementById("panel-header").style.display = "none";
    document.getElementById("empty-msg").style.display = "flex";
    document.getElementById("panel-content").style.display = "none";
  }}
}});

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


def main():
    print(f"Reading {DATA_FILE}...")
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)

    elements = build_elements(data)
    html = generate_html(data, elements)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    node_count = sum(1 for e in elements if "position" in e)
    edge_count = sum(1 for e in elements if "position" not in e and "classes" not in e)
    print(f"✓ Generated {OUTPUT_FILE}")
    print(f"  {node_count} nodes · {edge_count} edges")
    print(f"  Open in browser: open {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
