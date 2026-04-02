#!/usr/bin/env python3
"""Generate web/index.html — the landing page listing all available mind maps."""

import yaml
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
OUTPUT = ROOT / "web" / "index.html"


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def build_card(m):
    icon = m.get("icon", "📄")
    title_en = t(m.get("title", ""), "en")
    title_fr = t(m.get("title", ""), "fr") or title_en
    desc_en  = t(m.get("description", ""), "en")
    desc_fr  = t(m.get("description", ""), "fr") or desc_en
    nodes    = m.get("nodes", "")
    output   = m.get("output", "#")
    return f"""
    <a href="{output}" class="card">
      <div class="card-icon">{icon}</div>
      <div class="card-body">
        <div class="card-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</div>
        <div class="card-desc"  data-en="{desc_en}"  data-fr="{desc_fr}" >{desc_en}</div>
        <div class="card-meta">{nodes} nodes</div>
      </div>
      <div class="card-arrow">→</div>
    </a>"""


def main():
    with open(MAPS_FILE) as f:
        config = yaml.safe_load(f)
    maps = config.get("maps", [])
    cards_html = "\n".join(build_card(m) for m in maps)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM & AI Mind Maps</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0F0F1A;
    color: white;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  header {{
    padding: 20px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1E2D4E;
  }}
  .logo {{
    font-size: 14px;
    font-weight: 700;
    color: #E74C3C;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .lang-toggle {{ display: flex; gap: 6px; }}
  .lang-btn {{
    padding: 4px 12px;
    border: 1.5px solid #333;
    border-radius: 6px;
    background: transparent;
    color: #666;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .lang-btn.active {{ background: #E74C3C; border-color: #E74C3C; color: white; }}
  .lang-btn:hover:not(.active) {{ border-color: #aaa; color: white; }}

  main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 40px;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }}
  .hero {{ text-align: center; margin-bottom: 60px; }}
  .hero h1 {{
    font-size: clamp(28px, 5vw, 48px);
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #fff 40%, #C39BD3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .hero p {{
    font-size: 16px;
    color: #7F8C8D;
    max-width: 520px;
    line-height: 1.6;
    margin: 0 auto;
  }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; width: 100%; }}
  .card {{
    background: #16213E;
    border: 1px solid #1E2D4E;
    border-radius: 16px;
    padding: 28px;
    display: flex;
    align-items: center;
    gap: 20px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
    cursor: pointer;
  }}
  .card:hover {{
    border-color: #E74C3C;
    background: #1A2847;
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(231,76,60,0.15);
  }}
  .card-icon {{ font-size: 36px; flex-shrink: 0; }}
  .card-body {{ flex: 1; }}
  .card-title {{ font-size: 18px; font-weight: 700; margin-bottom: 6px; color: white; }}
  .card-desc  {{ font-size: 13px; color: #7F8C8D; line-height: 1.5; margin-bottom: 10px; }}
  .card-meta  {{ font-size: 11px; color: #E74C3C; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
  .card-arrow {{ font-size: 20px; color: #2C3E6E; flex-shrink: 0; transition: all 0.2s; }}
  .card:hover .card-arrow {{ color: #E74C3C; transform: translateX(4px); }}

  footer {{
    text-align: center;
    padding: 24px;
    color: #2C3E6E;
    font-size: 12px;
    border-top: 1px solid #1A1A2E;
  }}
</style>
</head>
<body>

<header>
  <div class="logo">🧠 mind-map-ia</div>
  <div class="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<main>
  <div class="hero">
    <h1 id="hero-title">LLM & AI Ecosystem<br>Mind Maps</h1>
    <p id="hero-desc">Interactive pedagogical maps to understand the AI landscape — models, tools, concepts and how they connect.</p>
  </div>
  <div class="cards">
    {cards_html}
  </div>
</main>

<footer>
  <span id="footer-text">Open source · Built to learn and share · </span>
  <a href="https://github.com/evausesgit/mind-map-ia" style="color:#E74C3C;text-decoration:none;">GitHub ↗</a>
</footer>

<script>
const heroTexts = {{
  en: {{
    title: "LLM & AI Ecosystem<br>Mind Maps",
    desc: "Interactive pedagogical maps to understand the AI landscape — models, tools, concepts and how they connect.",
    footer: "Open source · Built to learn and share · "
  }},
  fr: {{
    title: "Cartes Mentales de<br>l'Écosystème LLM & IA",
    desc: "Des cartes pédagogiques interactives pour comprendre le paysage de l'IA — modèles, outils, concepts et leurs connexions.",
    footer: "Open source · Construit pour apprendre et partager · "
  }}
}};

function setLang(lang) {{
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  document.getElementById('hero-title').innerHTML = heroTexts[lang].title;
  document.getElementById('hero-desc').textContent = heroTexts[lang].desc;
  document.getElementById('footer-text').textContent = heroTexts[lang].footer;
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = lang === 'fr' ? (el.dataset.fr || el.dataset.en) : el.dataset.en;
  }});
}}
</script>
</body>
</html>"""

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT} ({len(maps)} maps)")


if __name__ == "__main__":
    main()
