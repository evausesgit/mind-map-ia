#!/usr/bin/env python3
"""Generate a standalone HTML page from a Mermaid diagram YAML file.
Usage: python scripts/generate_mermaid.py data/dense-vs-moe.yaml web/dense-vs-moe.html
"""

import yaml
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import head_assets, site_header, site_footer, chrome_script

ROOT = Path(__file__).parent.parent

DATA_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "dense-vs-moe.yaml"
OUTPUT_FILE = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "web" / "dense-vs-moe.html"


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def generate_html(data):
    meta = data["meta"]
    title_en = t(meta.get("title", ""), "en")
    title_fr = t(meta.get("title", ""), "fr") or title_en
    desc_en = t(meta.get("description", ""), "en")
    desc_fr = t(meta.get("description", ""), "fr") or desc_en
    diagram_en = data["diagram"]["en"].strip()
    diagram_fr = data["diagram"]["fr"].strip()
    header_html = site_header(active="maps", current=OUTPUT_FILE.name)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title_en} — Mind Map IA</title>
{head_assets()}
<style>
  body {{ font-size: 16px; line-height: 1.6; }}
  .wrap {{
    max-width: 1180px; margin: 0 auto;
    padding: 0 max(20px, env(safe-area-inset-right, 0px)) 88px max(20px, env(safe-area-inset-left, 0px));
  }}
  .d-hero {{ padding-block: 56px 28px; display: grid; gap: 14px; }}
  .d-hero h1 {{ margin: 0; font-size: clamp(32px, 4.5vw, 46px); font-weight: 600; letter-spacing: -0.03em; line-height: 1.06; }}
  .d-hero p {{ margin: 0; font-family: var(--f-read); font-size: 20px; color: var(--ink-2); max-width: 36em; }}
  .d-meta {{ font: 12px var(--f-mono); color: var(--muted); }}
  .d-figure {{
    margin: 0;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: var(--shadow-sm);
    overflow-x: auto;
  }}
  #mermaid-diagram {{
    padding: clamp(20px, 4vw, 48px);
    display: flex;
    justify-content: center;
    min-width: min-content;
  }}
  #mermaid-diagram svg {{ max-width: 100%; height: auto; }}
  @media (max-width: 640px) {{
    #mermaid-diagram svg {{ max-width: none; }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<main class="wrap">
  <section class="d-hero">
    <div class="eyebrow" data-en="Diagram" data-fr="Diagramme">Diagram</div>
    <h1 id="main-title">{title_en}</h1>
    <p id="diagram-desc">{desc_en}</p>
    <div class="d-meta">v{meta.get("version", "")} · {meta.get("date", "")}</div>
  </section>
  <figure class="d-figure">
    <div id="mermaid-diagram"></div>
  </figure>
</main>

{site_footer()}

<script src="mermaid.min.js"></script>
<script>
const TITLES = {{"en": "{title_en}", "fr": "{title_fr}"}};
const DESCS   = {{"en": "{desc_en}", "fr": "{desc_fr}"}};
const DIAGRAMS = {{
  "en": `{diagram_en}`,
  "fr": `{diagram_fr}`
}};

function cssVar(n) {{ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }}
function initMermaid() {{
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'base',
    fontFamily: 'Geist, system-ui, sans-serif',
    flowchart: {{ curve: 'basis', padding: 20 }},
    themeVariables: {{
      fontSize: '28px',
      fontFamily: 'Geist, system-ui, sans-serif',
      background: cssVar('--surface'),
      primaryColor: cssVar('--sunk'),
      primaryTextColor: cssVar('--ink'),
      primaryBorderColor: cssVar('--line-strong'),
      lineColor: cssVar('--muted'),
      secondaryColor: cssVar('--accent-soft'),
      tertiaryColor: cssVar('--bg'),
      clusterBkg: cssVar('--bg'),
      clusterBorder: cssVar('--line-strong'),
      edgeLabelBackground: cssVar('--surface'),
      titleColor: cssVar('--ink'),
    }}
  }});
}}
initMermaid();

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

window.addEventListener('mmia-themechange', () => {{ initMermaid(); renderDiagram(lang); }});
renderDiagram('en');
</script>
{chrome_script()}
</body>
</html>"""
    return html


def main():
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)

    html = generate_html(data)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
