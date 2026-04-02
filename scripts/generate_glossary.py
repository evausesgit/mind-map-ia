#!/usr/bin/env python3
"""Generate web/glossary.html from data/glossary.yaml"""

import yaml
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
OUTPUT = ROOT / "web" / "glossary.html"


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def generate_html(data):
    terms = data["terms"]
    title_en = t(data["meta"]["title"], "en")
    title_fr = t(data["meta"]["title"], "fr")

    terms_sorted = sorted(terms, key=lambda x: t(x["label"], "en").lower())

    # Build term cards
    cards_html = ""
    for term in terms_sorted:
        tid = term["id"]
        label_en = t(term["label"], "en")
        label_fr = t(term["label"], "fr") or label_en
        desc_en = t(term["description"], "en").strip()
        desc_fr = t(term["description"], "fr").strip() or desc_en
        aliases = term.get("aliases", [])
        aliases_str = ", ".join(a for a in aliases if a.lower() != label_en.lower())
        aliases_html = f'<div class="aliases" data-en="{aliases_str}" data-fr="{aliases_str}">{aliases_str}</div>' if aliases_str else ""

        cards_html += f"""
  <div class="term-card" id="{tid}">
    <div class="term-header">
      <span class="term-label" data-en="{label_en}" data-fr="{label_fr}">{label_en}</span>
      {aliases_html}
    </div>
    <div class="term-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</div>
  </div>"""

    # Build alphabet index
    letters = sorted(set(t(term["label"], "en")[0].upper() for term in terms_sorted))
    index_html = "".join(
        f'<a href="#{next(t2["id"] for t2 in terms_sorted if t(t2["label"], "en")[0].upper() == l)}" class="idx-letter">{l}</a>'
        for l in letters
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_en}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #F8F9FA;
    color: #1A1A2E;
    min-height: 100vh;
  }}
  header {{
    background: #1A1A2E;
    color: white;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }}
  header h1 {{ font-size: 20px; font-weight: 700; }}
  .back-link {{
    color: #BDC3C7;
    text-decoration: none;
    font-size: 14px;
  }}
  .back-link:hover {{ color: white; }}
  .lang-toggle {{ display: flex; gap: 6px; }}
  .lang-btn {{
    background: none;
    border: 1px solid #555;
    border-radius: 4px;
    color: #BDC3C7;
    padding: 4px 10px;
    font-size: 13px;
    cursor: pointer;
  }}
  .lang-btn.active {{ background: white; color: #1A1A2E; border-color: white; }}
  .alphabet-index {{
    background: white;
    border-bottom: 1px solid #E0E0E0;
    padding: 10px 32px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .idx-letter {{
    display: inline-block;
    width: 28px;
    height: 28px;
    line-height: 28px;
    text-align: center;
    border-radius: 4px;
    font-weight: 600;
    font-size: 13px;
    color: #1A1A2E;
    text-decoration: none;
    background: #F0F0F0;
  }}
  .idx-letter:hover {{ background: #1A1A2E; color: white; }}
  .content {{
    max-width: 800px;
    margin: 32px auto;
    padding: 0 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .term-card {{
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 20px 24px;
    scroll-margin-top: 80px;
  }}
  .term-card:target {{
    border-color: #1A1A2E;
    box-shadow: 0 0 0 2px #1A1A2E22;
  }}
  .term-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .term-label {{
    font-size: 18px;
    font-weight: 700;
    color: #1A1A2E;
  }}
  .aliases {{
    font-size: 12px;
    color: #888;
    font-style: italic;
  }}
  .term-desc {{
    font-size: 14px;
    line-height: 1.7;
    color: #444;
  }}
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    <a href="index.html" class="back-link">← Home</a>
    <h1 id="main-title">{title_en}</h1>
  </div>
  <div class="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<div class="alphabet-index">
  {index_html}
</div>

<div class="content">
{cards_html}
</div>

<script>
const TITLES = {{ "en": "{title_en}", "fr": "{title_fr}" }};
let lang = 'en';

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.getElementById('main-title').textContent = TITLES[lang];
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
}}
</script>
</body>
</html>"""
    return html


def main():
    with open(GLOSSARY_FILE) as f:
        data = yaml.safe_load(f)
    html = generate_html(data)
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT}")
    print(f"  {len(data['terms'])} terms")


if __name__ == "__main__":
    main()
