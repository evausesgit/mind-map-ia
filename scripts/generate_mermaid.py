#!/usr/bin/env python3
"""Generate a standalone HTML page from a Mermaid diagram YAML file.
Usage: python scripts/generate_mermaid.py data/dense-vs-moe.yaml web/dense-vs-moe.html
"""

import yaml
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"

DATA_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "dense-vs-moe.yaml"
OUTPUT_FILE = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "web" / "dense-vs-moe.html"


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def build_nav(maps, current_output, links=None):
    items = ""
    current_name = Path(current_output).name
    for m in maps:
        active = "active" if m.get("output") == current_name else ""
        title_en = t(m.get("title", ""), "en")
        title_fr = t(m.get("title", ""), "fr") or title_en
        desc_en = t(m.get("description", ""), "en")
        desc_fr = t(m.get("description", ""), "fr") or desc_en
        items += (
            f'<a href="{m["output"]}" class="{active}">'
            f'  <span class="nav-icon">{m.get("icon", "📄")}</span>'
            f'  <span class="nav-info">'
            f'    <span class="nav-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'    <span class="nav-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f"  </span>"
            f"</a>"
        )
    link_items = ""
    for link in (links or []):
        title_en = t(link.get("title", ""), "en")
        title_fr = t(link.get("title", ""), "fr") or title_en
        desc_en = t(link.get("description", ""), "en")
        desc_fr = t(link.get("description", ""), "fr") or desc_en
        url = link.get("url", "")
        link_items += (
            f'<a href="{url}" target="_blank" rel="noopener">'
            f'  <span class="nav-icon">{link.get("icon", "🔗")}</span>'
            f'  <span class="nav-info">'
            f'    <span class="nav-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'    <span class="nav-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'  </span>'
            f'</a>'
        )
    nav = (
        '<div class="nav-menu">'
        '  <button class="nav-btn">≡ Maps ▾</button>'
        '  <div class="nav-dropdown">'
        '    <a href="index.html" class="nav-home">← Home</a>'
        f"   {items}"
        "  </div>"
        "</div>"
    )
    if link_items:
        nav += (
            '<div class="nav-menu">'
            '  <button class="nav-btn">'
            '    <span data-en="Links" data-fr="Liens">Links</span> ▾'
            '  </button>'
            '  <div class="nav-dropdown">'
            f'   {link_items}'
            '  </div>'
            '</div>'
        )
    nav += (
        '<a href="index.html#news" class="nav-btn" style="text-decoration:none;padding:5px 11px;border:1.5px solid #333;border-radius:6px;color:#BDC3C7;font-size:13px;font-weight:600;">'
        '  <span data-en="News" data-fr="Nouveautés">News</span>'
        '</a>'
    )
    return nav


def generate_html(data, maps, links=None):
    meta = data["meta"]
    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en
    desc_en = t(meta.get("description", ""), "en")
    desc_fr = t(meta.get("description", ""), "fr") or desc_en
    diagram_en = data["diagram"]["en"].strip()
    diagram_fr = data["diagram"]["fr"].strip()
    nav_html = build_nav(maps, str(OUTPUT_FILE), links=links)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_en}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #F8F9FA;
    color: #1A1A2E;
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
    gap: 16px;
    flex-shrink: 0;
  }}
  header h1 {{ font-size: 18px; font-weight: 700; }}
  .meta {{ font-size: 12px; color: #7F8C8D; margin-top: 2px; }}
  .nav-menu {{ position: relative; }}
  .nav-btn {{
    padding: 6px 14px; border: 1.5px solid #444; border-radius: 8px;
    background: transparent; color: #BDC3C7; font-size: 13px;
    font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap;
  }}
  .nav-btn:hover {{ border-color: #aaa; color: white; }}
  .nav-dropdown {{
    position: absolute; top: calc(100% + 6px); left: 0; min-width: 260px;
    background: #16213E; border: 1px solid #1E2D4E; border-radius: 10px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.5); z-index: 1000; display: none;
  }}
  .nav-menu:hover .nav-dropdown,
  .nav-menu:focus-within .nav-dropdown {{ display: block; }}
  .nav-dropdown a {{
    display: flex; align-items: center; gap: 12px; padding: 10px 14px;
    border-bottom: 1px solid #1E2D4E; text-decoration: none;
    color: #BDC3C7; font-size: 13px; transition: background 0.1s;
  }}
  .nav-dropdown a:last-child {{ border-bottom: none; }}
  .nav-dropdown a:hover {{ background: #1E2D4E; color: white; }}
  .nav-dropdown a.active {{ color: white; background: #1E2D4E; }}
  .nav-dropdown a .nav-icon {{ font-size: 18px; }}
  .nav-dropdown a .nav-info {{ display: flex; flex-direction: column; }}
  .nav-dropdown a .nav-title {{ font-weight: 600; }}
  .nav-dropdown a .nav-desc {{ font-size: 11px; color: #7F8C8D; margin-top: 1px; }}
  .nav-home {{ color: #BDC3C7 !important; font-size: 13px !important; border-bottom: 1px solid #1E2D4E; }}
  .nav-home:hover {{ color: #FF6B6B !important; }}
  .lang-toggle {{ display: flex; gap: 6px; }}
  .lang-btn {{
    background: none; border: 1px solid #555; border-radius: 4px;
    color: #BDC3C7; padding: 4px 10px; font-size: 13px; cursor: pointer;
  }}
  .lang-btn.active {{ background: white; color: #1A1A2E; border-color: white; }}
  .diagram-container {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px;
    overflow: auto;
  }}
  .diagram-desc {{
    font-size: 14px;
    color: #555;
    margin-bottom: 24px;
    text-align: center;
  }}
  #mermaid-diagram {{
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    max-width: 100%;
  }}
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    {nav_html}
    <div>
      <h1 id="main-title">{title_en}</h1>
      <div class="meta">v{meta.get("version", "")} · {meta.get("date", "")}</div>
    </div>
  </div>
  <div class="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<div class="diagram-container">
  <p class="diagram-desc" id="diagram-desc">{desc_en}</p>
  <div id="mermaid-diagram"></div>
</div>

<script src="mermaid.min.js"></script>
<script>
const TITLES = {{"en": "{title_en}", "fr": "{title_fr}"}};
const DESCS   = {{"en": "{desc_en}", "fr": "{desc_fr}"}};
const DIAGRAMS = {{
  "en": `{diagram_en}`,
  "fr": `{diagram_fr}`
}};

mermaid.initialize({{
  startOnLoad: false,
  theme: 'default',
  flowchart: {{ curve: 'basis', padding: 20 }},
  themeVariables: {{
    fontSize: '32px',
    primaryColor: '#E8F4FD',
    primaryTextColor: '#1A1A2E',
    primaryBorderColor: '#3498DB',
    lineColor: '#555',
    secondaryColor: '#F3E5F5',
    tertiaryColor: '#E8F5E9'
  }}
}});

let lang = 'en';

async function renderDiagram(l) {{
  const container = document.getElementById('mermaid-diagram');
  container.removeAttribute('data-processed');
  container.innerHTML = '';
  const {{ svg }} = await mermaid.render('mermaid-svg-' + Date.now(), DIAGRAMS[l]);
  container.innerHTML = svg;
}}

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.getElementById('main-title').textContent = TITLES[lang];
  document.getElementById('diagram-desc').textContent = DESCS[lang];
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
  renderDiagram(lang);
}}

renderDiagram('en');
</script>
</body>
</html>"""
    return html


def main():
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)
    with open(MAPS_FILE) as f:
        maps_config = yaml.safe_load(f)
    maps = maps_config.get("maps", [])
    links = maps_config.get("links", [])

    html = generate_html(data, maps, links)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
