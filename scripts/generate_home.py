#!/usr/bin/env python3
"""Generate web/index.html — the landing page listing all available mind maps."""

import yaml
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
MACRO_FILE = ROOT / "data" / "ecosystem-macro.yaml"
ECOSYSTEM_FILE = ROOT / "data" / "ecosystem.yaml"
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
    output   = m.get("output", "#")
    if "nodes" in m:
        meta_en = f"{m['nodes']} nodes"
        meta_fr = f"{m['nodes']} nœuds"
    elif "terms" in m:
        meta_en = f"{m['terms']} terms"
        meta_fr = f"{m['terms']} termes"
    else:
        meta_en = meta_fr = ""
    return f"""
    <a href="{output}" class="card">
      <div class="card-icon">{icon}</div>
      <div class="card-body">
        <div class="card-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</div>
        <div class="card-desc"  data-en="{desc_en}"  data-fr="{desc_fr}" >{desc_en}</div>
        <div class="card-meta" data-en="{meta_en}" data-fr="{meta_fr}">{meta_en}</div>
      </div>
      <div class="card-arrow">→</div>
    </a>"""


def build_search_index():
    """Build a JSON search index from glossary and all map nodes."""
    items = []

    # Glossary terms
    if GLOSSARY_FILE.exists():
        with open(GLOSSARY_FILE) as f:
            gdata = yaml.safe_load(f)
        for term in gdata.get("terms", []):
            items.append({
                "type": "glossary",
                "id": term["id"],
                "label": term.get("label", {}),
                "aliases": term.get("aliases", []),
                "desc": {k: (v or "")[:120] for k, v in (term.get("description") or {}).items()},
                "url": f"glossary.html#{term['id']}",
            })

    # Map nodes
    map_sources = [
        (MACRO_FILE, "macro.html", {"en": "Big Picture", "fr": "Vue d'Ensemble"}),
        (ECOSYSTEM_FILE, "ecosystem.html", {"en": "Full Ecosystem", "fr": "Écosystème Complet"}),
    ]
    seen_ids = set()
    for yaml_path, page_url, map_label in map_sources:
        if not yaml_path.exists():
            continue
        with open(yaml_path) as f:
            mdata = yaml.safe_load(f)
        for node in mdata.get("nodes", []):
            nid = node.get("id", "")
            if nid in seen_ids:
                continue
            seen_ids.add(nid)
            desc_raw = node.get("description") or {}
            if isinstance(desc_raw, str):
                desc_raw = {"en": desc_raw}
            items.append({
                "type": "node",
                "id": nid,
                "label": node.get("label", {}),
                "aliases": [],
                "desc": {k: (v or "")[:120] for k, v in desc_raw.items()},
                "url": page_url,
                "map": map_label,
            })

    return items


def main():
    with open(MAPS_FILE) as f:
        config = yaml.safe_load(f)
    maps = config.get("maps", [])
    cards_html = "\n".join(build_card(m) for m in maps)
    search_index_json = json.dumps(build_search_index(), ensure_ascii=False)

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

  /* Search */
  .search-wrapper {{
    position: relative;
    width: 260px;
  }}
  .search-icon {{
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 13px;
    pointer-events: none;
    color: #555;
  }}
  .search-input {{
    width: 100%;
    background: #0F0F1A;
    border: 1.5px solid #1E2D4E;
    border-radius: 8px;
    color: white;
    font-size: 13px;
    padding: 7px 28px 7px 30px;
    outline: none;
    transition: border-color 0.15s;
  }}
  .search-input::placeholder {{ color: #444; }}
  .search-input:focus {{ border-color: #E74C3C; }}
  .search-clear {{
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #555;
    font-size: 14px;
    cursor: pointer;
    display: none;
    line-height: 1;
    padding: 0;
  }}
  .search-clear:hover {{ color: white; }}
  .search-dropdown {{
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: #16213E;
    border: 1px solid #1E2D4E;
    border-radius: 10px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    z-index: 100;
    max-height: 360px;
    overflow-y: auto;
    display: none;
  }}
  .search-dropdown.open {{ display: block; }}
  .search-item {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 14px;
    border-bottom: 1px solid #1E2D4E;
    text-decoration: none;
    color: inherit;
    transition: background 0.1s;
  }}
  .search-item:last-child {{ border-bottom: none; }}
  .search-item:hover {{ background: #1E2D4E; }}
  .search-item-top {{ display: flex; align-items: center; gap: 8px; }}
  .search-item-badge {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 1px 6px;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  .badge-glossary {{ background: #2C3E6E; color: #BDC3C7; }}
  .badge-node    {{ background: #1E3A2E; color: #82C8A0; }}
  .search-item-label {{ font-size: 13px; font-weight: 600; color: white; }}
  .search-item-sub   {{ font-size: 11px; color: #7F8C8D; }}
  .search-item-match {{ font-size: 11px; color: #E74C3C; font-style: italic; }}
  .search-empty {{
    padding: 16px;
    text-align: center;
    color: #555;
    font-size: 13px;
  }}
</style>
</head>
<body>

<header>
  <div class="logo">🧠 mind-map-ia</div>
  <div class="search-wrapper">
    <span class="search-icon">🔍</span>
    <input class="search-input" id="search-input" type="text"
           placeholder="Search..." autocomplete="off" spellcheck="false">
    <button class="search-clear" id="search-clear" onclick="clearSearch()">✕</button>
    <div class="search-dropdown" id="search-dropdown"></div>
  </div>
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
    footer: "Open source · Built to learn and share · ",
    searchPlaceholder: "Search concepts, models, tools…"
  }},
  fr: {{
    title: "Cartes Mentales de<br>l'Écosystème LLM & IA",
    desc: "Des cartes pédagogiques interactives pour comprendre le paysage de l'IA — modèles, outils, concepts et leurs connexions.",
    footer: "Open source · Construit pour apprendre et partager · ",
    searchPlaceholder: "Rechercher concepts, modèles, outils…"
  }}
}};

let currentLang = 'en';

function setLang(lang) {{
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  document.getElementById('hero-title').innerHTML = heroTexts[lang].title;
  document.getElementById('hero-desc').textContent = heroTexts[lang].desc;
  document.getElementById('footer-text').textContent = heroTexts[lang].footer;
  document.getElementById('search-input').placeholder = heroTexts[lang].searchPlaceholder;
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = lang === 'fr' ? (el.dataset.fr || el.dataset.en) : el.dataset.en;
  }});
  const q = document.getElementById('search-input').value.trim();
  if (q) renderResults(doSearch(q));
}}

// ── Search ──────────────────────────────────────────────────────────────────
const SEARCH_INDEX = {search_index_json};

function normalize(s) {{
  return (s || '').toLowerCase().normalize('NFD').replace(/\\p{{Diacritic}}/gu, '');
}}

function doSearch(query) {{
  const q = normalize(query);
  if (q.length < 2) return [];
  const results = [];
  for (const item of SEARCH_INDEX) {{
    const label = item.label[currentLang] || item.label.en || '';
    const desc  = item.desc[currentLang]  || item.desc.en  || '';
    const aliases = (item.aliases || []).join(' ');
    const mapLabel = item.map ? (item.map[currentLang] || item.map.en || '') : '';

    let matchText = null;
    let score = 0;
    const nLabel   = normalize(label);
    const nAliases = normalize(aliases);
    const nDesc    = normalize(desc);

    if (nLabel.startsWith(q))         {{ score = 3; }}
    else if (nLabel.includes(q))      {{ score = 2; }}
    else if (nAliases.includes(q))    {{ score = 1; matchText = aliases.split(',').find(a => normalize(a).includes(q))?.trim(); }}
    else if (nDesc.includes(q))       {{ score = 0.5; const i = nDesc.indexOf(q); matchText = '…' + desc.slice(Math.max(0,i-20), i+40).trim() + '…'; }}

    if (score > 0) results.push({{ item, label, desc, mapLabel, matchText, score }});
  }}
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, 8);
}}

function renderResults(results) {{
  const dd = document.getElementById('search-dropdown');
  if (!results.length) {{
    dd.innerHTML = `<div class="search-empty">${{currentLang === 'fr' ? 'Aucun résultat' : 'No results'}}</div>`;
    dd.classList.add('open');
    return;
  }}
  dd.innerHTML = results.map(r => {{
    const {{ item, label, desc, mapLabel, matchText }} = r;
    const badge = item.type === 'glossary'
      ? `<span class="search-item-badge badge-glossary">${{currentLang === 'fr' ? 'Glossaire' : 'Glossary'}}</span>`
      : `<span class="search-item-badge badge-node">${{mapLabel}}</span>`;
    const sub = matchText
      ? `<div class="search-item-match">${{matchText}}</div>`
      : (desc ? `<div class="search-item-sub">${{desc.slice(0,80)}}…</div>` : '');
    return `<a class="search-item" href="${{item.url}}">
      <div class="search-item-top">${{badge}}<span class="search-item-label">${{label}}</span></div>
      ${{sub}}
    </a>`;
  }}).join('');
  dd.classList.add('open');
}}

function clearSearch() {{
  const inp = document.getElementById('search-input');
  inp.value = '';
  inp.focus();
  document.getElementById('search-dropdown').classList.remove('open');
  document.getElementById('search-clear').style.display = 'none';
}}

document.addEventListener('DOMContentLoaded', () => {{
  const inp = document.getElementById('search-input');
  const dd  = document.getElementById('search-dropdown');
  const clr = document.getElementById('search-clear');

  inp.addEventListener('input', () => {{
    const q = inp.value.trim();
    clr.style.display = q ? 'block' : 'none';
    if (q.length >= 2) renderResults(doSearch(q));
    else dd.classList.remove('open');
  }});

  inp.addEventListener('keydown', e => {{
    if (e.key === 'Escape') clearSearch();
    if (e.key === 'Enter') {{
      const first = dd.querySelector('.search-item');
      if (first) window.location.href = first.href;
    }}
  }});

  document.addEventListener('click', e => {{
    if (!inp.closest('.search-wrapper').contains(e.target)) dd.classList.remove('open');
  }});

  inp.addEventListener('focus', () => {{
    if (inp.value.trim().length >= 2) dd.classList.add('open');
  }});
}});
</script>
</body>
</html>"""

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT} ({len(maps)} maps)")


if __name__ == "__main__":
    main()
