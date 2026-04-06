#!/usr/bin/env python3
"""Generate web/index.html — the landing page listing all available mind maps."""

import re
import yaml
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
MACRO_FILE = ROOT / "data" / "ecosystem-macro.yaml"
ECOSYSTEM_FILE = ROOT / "data" / "ecosystem.yaml"
TOPICS_DIR = ROOT / "data" / "topics"
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


def parse_topic_frontmatter(path):
    """Extract YAML frontmatter from a topic .md file."""
    raw = path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if not fm_match:
        return None
    return yaml.safe_load(fm_match.group(1))


def load_topics():
    """Return list of topic frontmatter dicts, sorted by date desc."""
    if not TOPICS_DIR.exists():
        return []
    topics = []
    for path in sorted(TOPICS_DIR.glob("*.md")):
        fm = parse_topic_frontmatter(path)
        if fm:
            topics.append(fm)
    topics.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return topics


def build_topic_card(topic):
    tid = topic.get("id", "")
    title_en = t(topic.get("title", ""), "en")
    title_fr = t(topic.get("title", ""), "fr") or title_en
    summary_en = t(topic.get("summary", ""), "en")
    summary_fr = t(topic.get("summary", ""), "fr") or summary_en
    tags = topic.get("tags", [])
    status = topic.get("status", "draft")
    tags_html = "".join(f'<span class="topic-tag">{tag}</span>' for tag in tags[:4])
    status_colors = {"stable": "#27AE60", "draft": "#E67E22", "review": "#3498DB"}
    status_color = status_colors.get(status, "#7F8C8D")
    return f"""
    <a href="topics/{tid}.html" class="topic-card">
      <div class="topic-card-body">
        <div class="topic-card-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</div>
        <div class="topic-card-desc" data-en="{summary_en}" data-fr="{summary_fr}">{summary_en}</div>
        <div class="topic-card-footer">
          <div class="topic-tags">{tags_html}</div>
          <span class="topic-status" style="color:{status_color}">{status}</span>
        </div>
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

    # Topics
    for topic in load_topics():
        tid = topic.get("id", "")
        summary = topic.get("summary") or {}
        if isinstance(summary, str):
            summary = {"en": summary}
        items.append({
            "type": "topic",
            "id": tid,
            "label": topic.get("title", {}),
            "aliases": topic.get("tags", []),
            "desc": {k: (v or "")[:120] for k, v in summary.items()},
            "url": f"topics/{tid}.html",
        })

    return items


def build_nav_html(maps, topics):
    """Build the site-wide nav: Mind Maps dropdown + Deep Dives dropdown + Glossary link."""
    map_items = ""
    for m in maps:
        if m.get("id") == "glossary":
            continue
        title_en = t(m.get("title", ""), "en")
        title_fr = t(m.get("title", ""), "fr") or title_en
        desc_en  = t(m.get("description", ""), "en")
        desc_fr  = t(m.get("description", ""), "fr") or desc_en
        map_items += (
            f'<a href="{m["output"]}" class="nav-item">'
            f'<span class="nav-item-icon">{m.get("icon","📄")}</span>'
            f'<span class="nav-item-info">'
            f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'<span class="nav-item-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'</span></a>'
        )
    dive_items = ""
    for topic in topics:
        tid = topic.get("id", "")
        title_en = t(topic.get("title",   ""), "en")
        title_fr = t(topic.get("title",   ""), "fr") or title_en
        summ_en  = t(topic.get("summary", ""), "en")
        summ_fr  = t(topic.get("summary", ""), "fr") or summ_en
        dive_items += (
            f'<a href="topics/{tid}.html" class="nav-item">'
            f'<span class="nav-item-icon">📝</span>'
            f'<span class="nav-item-info">'
            f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'<span class="nav-item-desc" data-en="{summ_en}" data-fr="{summ_fr}">{summ_en}</span>'
            f'</span></a>'
        )
    return (
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


def main():
    with open(MAPS_FILE) as f:
        config = yaml.safe_load(f)
    maps = config.get("maps", [])
    topics = load_topics()
    search_index_json = json.dumps(build_search_index(), ensure_ascii=False)

    # Split: featured (Big Picture) vs rest
    macro_map   = next((m for m in maps if m.get("id") == "macro"), None)
    other_maps  = [m for m in maps if m.get("id") not in ("macro", "glossary")]
    glossary_map = next((m for m in maps if m.get("id") == "glossary"), None)

    # Featured Big Picture card
    def build_featured_card(m):
        icon     = m.get("icon", "🗺️")
        title_en = t(m.get("title", ""), "en")
        title_fr = t(m.get("title", ""), "fr") or title_en
        desc_en  = t(m.get("description", ""), "en")
        desc_fr  = t(m.get("description", ""), "fr") or desc_en
        nodes    = m.get("nodes", "")
        meta_en  = f"{nodes} nodes" if nodes else ""
        meta_fr  = f"{nodes} nœuds" if nodes else ""
        return f"""
    <a href="{m['output']}" class="card card-featured">
      <div class="featured-badge" data-en="Start here · Best entry point" data-fr="Commencer ici · Meilleur point d'entrée">Start here · Best entry point</div>
      <div class="card-featured-body">
        <div class="card-featured-icon">{icon}</div>
        <div class="card-body">
          <div class="card-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</div>
          <div class="card-desc"  data-en="{desc_en}"  data-fr="{desc_fr}" >{desc_en}</div>
          <div class="card-meta"  data-en="{meta_en}"  data-fr="{meta_fr}" >{meta_en}</div>
        </div>
        <div class="card-arrow">→</div>
      </div>
    </a>"""

    featured_html = build_featured_card(macro_map) if macro_map else ""
    other_cards_html = "\n".join(build_card(m) for m in other_maps)
    glossary_card_html = build_card(glossary_map) if glossary_map else ""
    topics_html = "\n".join(build_topic_card(topic) for topic in topics)
    nav_html = build_nav_html(maps, topics)

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

  /* ── Header ── */
  header {{
    padding: 14px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid #1E2D4E;
    background: #0D1117;
  }}
  .header-left {{ display: flex; align-items: center; gap: 8px; }}
  .logo {{
    font-size: 20px;
    text-decoration: none;
    margin-right: 4px;
  }}
  .header-right {{ display: flex; align-items: center; gap: 8px; }}

  /* ── Nav dropdowns ── */
  .nav-group {{ position: relative; }}
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
    min-width: 280px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
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
  .nav-item-icon {{ font-size: 16px; flex-shrink: 0; }}
  .nav-item-info {{ display: flex; flex-direction: column; }}
  .nav-item-title {{ font-weight: 600; font-size: 13px; }}
  .nav-item-desc {{ font-size: 11px; color: #7F8C8D; margin-top: 1px; }}

  /* ── Glossary button ── */
  .glossary-btn {{
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
  .glossary-btn:hover {{ border-color: #C39BD3; color: #C39BD3; }}

  /* ── Lang ── */
  .lang-toggle {{ display: flex; gap: 5px; }}
  .lang-btn {{
    padding: 4px 10px;
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

  /* ── Search ── */
  .search-wrapper {{ position: relative; width: 220px; }}
  .search-icon {{
    position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
    font-size: 13px; pointer-events: none; color: #555;
  }}
  .search-input {{
    width: 100%;
    background: #0F0F1A;
    border: 1.5px solid #1E2D4E;
    border-radius: 8px;
    color: white;
    font-size: 13px;
    padding: 6px 26px 6px 30px;
    outline: none;
    transition: border-color 0.15s;
  }}
  .search-input::placeholder {{ color: #444; }}
  .search-input:focus {{ border-color: #E74C3C; }}
  .search-clear {{
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: #555; font-size: 14px;
    cursor: pointer; display: none; line-height: 1; padding: 0;
  }}
  .search-clear:hover {{ color: white; }}
  .search-dropdown {{
    position: absolute; top: calc(100% + 6px); left: 0; right: 0;
    background: #16213E; border: 1px solid #1E2D4E; border-radius: 10px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.5); z-index: 200;
    max-height: 360px; overflow-y: auto; display: none;
  }}
  .search-dropdown.open {{ display: block; }}
  .search-item {{
    display: flex; flex-direction: column; gap: 2px;
    padding: 10px 14px; border-bottom: 1px solid #1E2D4E;
    text-decoration: none; color: inherit; transition: background 0.1s;
  }}
  .search-item:last-child {{ border-bottom: none; }}
  .search-item:hover {{ background: #1E2D4E; }}
  .search-item-top {{ display: flex; align-items: center; gap: 8px; }}
  .search-item-badge {{
    font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
    text-transform: uppercase; padding: 1px 6px; border-radius: 4px; flex-shrink: 0;
  }}
  .badge-glossary {{ background: #2C3E6E; color: #BDC3C7; }}
  .badge-node    {{ background: #1E3A2E; color: #82C8A0; }}
  .badge-topic   {{ background: #3B1F4E; color: #C39BD3; }}
  .search-item-label {{ font-size: 13px; font-weight: 600; color: white; }}
  .search-item-sub   {{ font-size: 11px; color: #7F8C8D; }}
  .search-item-match {{ font-size: 11px; color: #E74C3C; font-style: italic; }}
  .search-empty {{ padding: 16px; text-align: center; color: #555; font-size: 13px; }}

  /* ── Main layout ── */
  main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 40px 64px;
    max-width: 960px;
    margin: 0 auto;
    width: 100%;
  }}
  .hero {{ text-align: center; margin-bottom: 40px; }}
  .hero h1 {{
    font-size: clamp(26px, 4vw, 44px);
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 14px;
    background: linear-gradient(135deg, #fff 40%, #C39BD3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .hero p {{
    font-size: 15px;
    color: #7F8C8D;
    max-width: 500px;
    line-height: 1.6;
    margin: 0 auto;
  }}

  /* ── Featured card (Big Picture) ── */
  .card-featured {{
    width: 100%;
    background: linear-gradient(135deg, #16213E 60%, #1A2847);
    border: 2px solid #E74C3C;
    border-radius: 20px;
    padding: 32px 36px;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 16px;
    transition: all 0.2s;
    margin-bottom: 8px;
    box-shadow: 0 4px 24px rgba(231,76,60,0.12);
  }}
  .card-featured:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(231,76,60,0.25);
    border-color: #FF6B6B;
  }}
  .featured-badge {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #E74C3C;
  }}
  .card-featured-body {{
    display: flex;
    align-items: center;
    gap: 24px;
  }}
  .card-featured-icon {{ font-size: 52px; flex-shrink: 0; }}
  .card-featured .card-title {{ font-size: 22px; margin-bottom: 8px; }}
  .card-featured .card-desc  {{ font-size: 14px; margin-bottom: 10px; }}
  .card-featured .card-arrow {{ font-size: 24px; color: #E74C3C; flex-shrink: 0; transition: transform 0.2s; }}
  .card-featured:hover .card-arrow {{ transform: translateX(6px); }}

  /* ── Section separator ── */
  .section-sep {{
    width: 100%;
    display: flex;
    align-items: center;
    gap: 16px;
    margin: 32px 0 24px;
  }}
  .section-sep-line {{ flex: 1; height: 1px; background: #1E2D4E; }}
  .section-sep-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #2C3E6E;
    white-space: nowrap;
  }}

  /* ── Regular cards grid ── */
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; width: 100%; }}
  .card {{
    background: #16213E;
    border: 1px solid #1E2D4E;
    border-radius: 14px;
    padding: 22px;
    display: flex;
    align-items: center;
    gap: 16px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }}
  .card:hover {{
    border-color: #E74C3C;
    background: #1A2847;
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(231,76,60,0.12);
  }}
  .card-icon {{ font-size: 30px; flex-shrink: 0; }}
  .card-body {{ flex: 1; min-width: 0; }}
  .card-title {{ font-size: 15px; font-weight: 700; margin-bottom: 5px; color: white; }}
  .card-desc  {{ font-size: 12px; color: #7F8C8D; line-height: 1.5; margin-bottom: 8px; }}
  .card-meta  {{ font-size: 10px; color: #E74C3C; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
  .card-arrow {{ font-size: 18px; color: #2C3E6E; flex-shrink: 0; transition: all 0.2s; }}
  .card:hover .card-arrow {{ color: #E74C3C; transform: translateX(4px); }}

  /* ── Deep Dives ── */
  .topic-card {{
    background: #16213E;
    border: 1px solid #1E2D4E;
    border-radius: 14px;
    padding: 20px 22px;
    display: flex;
    align-items: center;
    gap: 14px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }}
  .topic-card:hover {{
    border-color: #C39BD3;
    background: #1A2047;
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(195,155,211,0.12);
  }}
  .topic-card:hover .card-arrow {{ color: #C39BD3; transform: translateX(4px); }}
  .topic-card-body {{ flex: 1; }}
  .topic-card-title {{ font-size: 15px; font-weight: 700; margin-bottom: 4px; color: white; }}
  .topic-card-desc  {{ font-size: 12px; color: #7F8C8D; line-height: 1.5; margin-bottom: 8px; }}
  .topic-card-footer {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  .topic-tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .topic-tag {{
    font-size: 10px; padding: 1px 6px;
    background: #3B1F4E; color: #C39BD3;
    border-radius: 4px; font-weight: 600;
  }}
  .topic-status {{
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0;
  }}

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
  <div class="header-left">
    <a href="index.html" class="logo" title="Home">🧠</a>
    {nav_html}
  </div>
  <div class="header-right">
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input class="search-input" id="search-input" type="text"
             placeholder="Search…" autocomplete="off" spellcheck="false">
      <button class="search-clear" id="search-clear" onclick="clearSearch()">✕</button>
      <div class="search-dropdown" id="search-dropdown"></div>
    </div>
    <a href="glossary.html" class="glossary-btn">
      <span data-en="📖 Glossary" data-fr="📖 Glossaire">📖 Glossary</span>
    </a>
    <div class="lang-toggle">
      <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
      <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
    </div>
  </div>
</header>

<main>
  <div class="hero">
    <h1 id="hero-title">LLM & AI Ecosystem<br>Mind Maps</h1>
    <p id="hero-desc">Interactive pedagogical maps to understand the AI landscape — models, tools, concepts and how they connect.</p>
  </div>

  {featured_html}

  <div class="section-sep">
    <div class="section-sep-line"></div>
    <span class="section-sep-label" data-en="ALL MAPS" data-fr="TOUTES LES CARTES">ALL MAPS</span>
    <div class="section-sep-line"></div>
  </div>

  <div class="cards">
    {other_cards_html}
    {glossary_card_html}
  </div>

  <div class="section-sep" style="margin-top:40px;">
    <div class="section-sep-line"></div>
    <span class="section-sep-label" data-en="DEEP DIVES" data-fr="ARTICLES DE FOND">DEEP DIVES</span>
    <div class="section-sep-line"></div>
  </div>
  <div class="cards" style="grid-template-columns:1fr">
    {topics_html}
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
    let matchText = null, score = 0;
    const nLabel = normalize(label), nAliases = normalize(aliases), nDesc = normalize(desc);
    if (nLabel.startsWith(q))      {{ score = 3; }}
    else if (nLabel.includes(q))   {{ score = 2; }}
    else if (nAliases.includes(q)) {{ score = 1; matchText = aliases.split(',').find(a => normalize(a).includes(q))?.trim(); }}
    else if (nDesc.includes(q))    {{ score = 0.5; const i = nDesc.indexOf(q); matchText = '…' + desc.slice(Math.max(0,i-20), i+40).trim() + '…'; }}
    if (score > 0) results.push({{ item, label, desc, mapLabel, matchText, score }});
  }}
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, 8);
}}
function renderResults(results) {{
  const dd = document.getElementById('search-dropdown');
  if (!results.length) {{
    dd.innerHTML = `<div class="search-empty">${{currentLang === 'fr' ? 'Aucun résultat' : 'No results'}}</div>`;
    dd.classList.add('open'); return;
  }}
  dd.innerHTML = results.map(r => {{
    const {{ item, label, desc, mapLabel, matchText }} = r;
    const badge = item.type === 'glossary'
      ? `<span class="search-item-badge badge-glossary">${{currentLang === 'fr' ? 'Glossaire' : 'Glossary'}}</span>`
      : item.type === 'topic'
      ? `<span class="search-item-badge badge-topic">${{currentLang === 'fr' ? 'Article' : 'Deep Dive'}}</span>`
      : `<span class="search-item-badge badge-node">${{mapLabel}}</span>`;
    const sub = matchText
      ? `<div class="search-item-match">${{matchText}}</div>`
      : (desc ? `<div class="search-item-sub">${{desc.slice(0,80)}}…</div>` : '');
    return `<a class="search-item" href="${{item.url}}">
      <div class="search-item-top">${{badge}}<span class="search-item-label">${{label}}</span></div>${{sub}}</a>`;
  }}).join('');
  dd.classList.add('open');
}}
function clearSearch() {{
  const inp = document.getElementById('search-input');
  inp.value = ''; inp.focus();
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
    if (e.key === 'Enter') {{ const first = dd.querySelector('.search-item'); if (first) window.location.href = first.href; }}
  }});
  document.addEventListener('click', e => {{
    if (!inp.closest('.search-wrapper').contains(e.target)) dd.classList.remove('open');
  }});
  inp.addEventListener('focus', () => {{ if (inp.value.trim().length >= 2) dd.classList.add('open'); }});
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
