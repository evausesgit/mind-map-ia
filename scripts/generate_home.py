#!/usr/bin/env python3
"""Generate web/index.html — the landing page listing all available mind maps."""

import re
import yaml
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from global_search import widget_html as gs_widget

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
MACRO_FILE = ROOT / "data" / "ecosystem-macro.yaml"
TOPICS_DIR = ROOT / "data" / "topics"
NEWS_FILE = ROOT / "data" / "news.yaml"
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


def load_news(max_items=8):
    """Load news entries from data/news.yaml, sorted by date desc."""
    if not NEWS_FILE.exists():
        return []
    with open(NEWS_FILE) as f:
        data = yaml.safe_load(f)
    entries = data.get("news", [])
    entries.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return entries[:max_items]


def _slugify(text):
    """Turn a title into a URL-friendly slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:60]


def build_news_item(entry):
    date = str(entry.get("date", ""))
    ntype = entry.get("type", "update")
    title_en = t(entry.get("title", ""), "en")
    title_fr = t(entry.get("title", ""), "fr") or title_en
    desc_en = t(entry.get("description", ""), "en")
    desc_fr = t(entry.get("description", ""), "fr") or desc_en
    link = entry.get("link", "")
    type_icons = {"new-content": "📝", "update": "🔄", "new-feature": "✨"}
    type_labels_en = {"new-content": "New content", "update": "Update", "new-feature": "New feature"}
    type_labels_fr = {"new-content": "Nouveau contenu", "update": "Mise à jour", "new-feature": "Nouveauté"}
    icon = type_icons.get(ntype, "📢")
    label_en = type_labels_en.get(ntype, "News")
    label_fr = type_labels_fr.get(ntype, "News")
    anchor = f"news-{date}-{_slugify(title_en)}"
    tag = f'<a href="{link}" id="{anchor}" class="news-item">' if link else f'<div id="{anchor}" class="news-item">'
    end_tag = '</a>' if link else '</div>'
    return f"""
    {tag}
      <div class="news-icon">{icon}</div>
      <div class="news-body">
        <div class="news-meta">
          <span class="news-type" data-en="{label_en}" data-fr="{label_fr}">{label_en}</span>
          <span class="news-date">{date}</span>
        </div>
        <div class="news-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</div>
        <div class="news-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</div>
      </div>
      <button class="news-share" onclick="event.preventDefault();event.stopPropagation();navigator.clipboard.writeText(location.origin+location.pathname+'#{anchor}');this.textContent='✓';setTimeout(()=>this.textContent='🔗',1200)" title="Copy link">🔗</button>
    {end_tag}"""


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
        f'<a href="index.html#news" class="nav-btn" style="text-decoration:none;">'
        f'  <span data-en="News" data-fr="Nouveautés">News</span>'
        f'</a>'
    )


def main():
    with open(MAPS_FILE) as f:
        config = yaml.safe_load(f)
    maps = config.get("maps", [])
    topics = load_topics()
    news = load_news()
    # Split: featured (Big Picture) vs rest
    macro_map   = next((m for m in maps if m.get("id") == "macro"), None)
    other_maps  = [m for m in maps if m.get("id") not in ("macro", "glossary")]
    glossary_map = next((m for m in maps if m.get("id") == "glossary"), None)

    # Featured Big Picture card
    ORGANIC_NET_SVG = """<svg width="80" height="55" viewBox="0 0 120 82" fill="none" xmlns="http://www.w3.org/2000/svg">
      <line x1="10" y1="16" x2="24" y2="8"  stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="10" y1="16" x2="22" y2="34" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="10" y1="52" x2="22" y2="34" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="10" y1="52" x2="28" y2="64" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="24" y1="8"  x2="42" y2="16" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="22" y1="34" x2="42" y2="16" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="22" y1="34" x2="40" y2="48" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="28" y1="64" x2="40" y2="48" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="28" y1="64" x2="46" y2="72" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="42" y1="16" x2="60" y2="10" stroke="#E74C3C" stroke-width="1.4" stroke-opacity="0.9"/>
      <line x1="42" y1="16" x2="56" y2="38" stroke="#E74C3C" stroke-width="1.4" stroke-opacity="0.9"/>
      <line x1="40" y1="48" x2="56" y2="38" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="40" y1="48" x2="58" y2="64" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="46" y1="72" x2="58" y2="64" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="60" y1="10" x2="56" y2="38" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="60" y1="10" x2="76" y2="20" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="56" y1="38" x2="72" y2="50" stroke="#E74C3C" stroke-width="1.4" stroke-opacity="0.9"/>
      <line x1="58" y1="64" x2="72" y2="50" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="58" y1="64" x2="78" y2="72" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="76" y1="20" x2="72" y2="50" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="76" y1="20" x2="92" y2="14" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="72" y1="50" x2="94" y2="44" stroke="#E74C3C" stroke-width="1.4" stroke-opacity="0.9"/>
      <line x1="78" y1="72" x2="94" y2="44" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="92" y1="14" x2="94" y2="44" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="92" y1="14" x2="108" y2="26" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="94" y1="44" x2="108" y2="60" stroke="#E74C3C" stroke-width="1.4" stroke-opacity="0.9"/>
      <line x1="78" y1="72" x2="108" y2="60" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <line x1="108" y1="26" x2="108" y2="60" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <circle cx="10"  cy="16" r="3.5" fill="white"/>
      <circle cx="10"  cy="52" r="3"   fill="white"/>
      <circle cx="24"  cy="8"  r="3"   fill="white"/>
      <circle cx="22"  cy="34" r="5"   fill="#E74C3C"/>
      <circle cx="28"  cy="64" r="3"   fill="white"/>
      <circle cx="42"  cy="16" r="3.5" fill="white"/>
      <circle cx="40"  cy="48" r="3"   fill="white"/>
      <circle cx="46"  cy="72" r="3"   fill="white"/>
      <circle cx="60"  cy="10" r="4.5" fill="#E74C3C"/>
      <circle cx="56"  cy="38" r="5"   fill="white"/>
      <circle cx="58"  cy="64" r="3"   fill="white"/>
      <circle cx="76"  cy="20" r="3.5" fill="white"/>
      <circle cx="72"  cy="50" r="4.5" fill="#E74C3C"/>
      <circle cx="78"  cy="72" r="3"   fill="white"/>
      <circle cx="92"  cy="14" r="3.5" fill="white"/>
      <circle cx="94"  cy="44" r="3"   fill="white"/>
      <circle cx="108" cy="26" r="4.5" fill="#E74C3C"/>
      <circle cx="108" cy="60" r="3.5" fill="white"/>
    </svg>"""

    def build_featured_card(m):
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
        <div class="card-featured-icon">{ORGANIC_NET_SVG}</div>
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
    news_html = "\n".join(build_news_item(n) for n in news)
    nav_html = build_nav_html(maps, topics)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
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
    display: flex;
    align-items: center;
    text-decoration: none;
    margin-right: 4px;
    opacity: 0.9;
    transition: opacity 0.15s;
  }}
  .logo:hover {{ opacity: 1; }}
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


  /* ── Main layout ── */
  main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 40px 64px;
    max-width: 1280px;
    margin: 0 auto;
    width: 100%;
  }}
  .main-layout {{
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 40px;
    width: 100%;
  }}
  .news-sidebar {{
    position: sticky;
    top: 80px;
    align-self: start;
    max-height: calc(100vh - 100px);
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #1E2D4E transparent;
  }}
  .main-content {{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 0;
  }}
  @media (max-width: 860px) {{
    .main-layout {{
      grid-template-columns: 1fr;
    }}
    .news-sidebar {{
      position: static;
      max-height: none;
      order: 1;
    }}
    .main-content {{ order: 0; }}
  }}
  .site-intro {{
    width: 100%;
    font-size: 14px;
    color: #7F8C8D;
    line-height: 1.6;
    margin-bottom: 24px;
    text-align: center;
  }}
  .site-intro strong {{ color: #BDC3C7; font-weight: 700; }}

  /* ── Featured card ── */
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
  .card-featured-icon {{ font-size: 52px; flex-shrink: 0; line-height: 0; }}
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

  /* ── News feed ── */
  .news-feed {{ display: flex; flex-direction: column; gap: 0; width: 100%; }}
  .news-item {{
    display: grid;
    grid-template-columns: 24px 1fr auto;
    align-items: start;
    gap: 10px;
    padding: 14px 14px;
    border-left: 2px solid #1E2D4E;
    text-decoration: none;
    color: inherit;
    transition: all 0.15s;
    position: relative;
    scroll-margin-top: 80px;
  }}
  .news-share {{
    background: none; border: none; cursor: pointer;
    font-size: 13px; opacity: 0; transition: opacity 0.15s;
    padding: 3px 5px; border-radius: 4px; align-self: center;
  }}
  .news-item:hover .news-share {{ opacity: 0.6; }}
  .news-share:hover {{ opacity: 1 !important; background: #1E2D4E; }}
  a.news-item:hover {{
    background: #16213E;
    border-left-color: #E74C3C;
  }}
  .news-icon {{
    font-size: 16px;
    text-align: center;
    padding-top: 2px;
  }}
  .news-body {{ min-width: 0; }}
  .news-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }}
  .news-type {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #E74C3C;
  }}
  .news-date {{
    font-size: 10px;
    color: #555;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }}
  .news-title {{
    font-size: 13px;
    font-weight: 600;
    color: white;
    margin-bottom: 3px;
    line-height: 1.4;
  }}
  .news-desc {{
    font-size: 11px;
    color: #7F8C8D;
    line-height: 1.5;
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
    <a href="index.html" class="logo" title="Home">
      <svg width="44" height="30" viewBox="0 0 120 82" fill="none" xmlns="http://www.w3.org/2000/svg">
        <line x1="22" y1="34" x2="42" y2="16" stroke="white" stroke-width="1" stroke-opacity="0.55"/>
        <line x1="42" y1="16" x2="60" y2="10" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>
        <line x1="56" y1="38" x2="72" y2="50" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>
        <line x1="72" y1="50" x2="94" y2="44" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>
        <line x1="94" y1="44" x2="108" y2="60" stroke="#E74C3C" stroke-width="1.2" stroke-opacity="0.8"/>
        <line x1="22" y1="34" x2="40" y2="48" stroke="white" stroke-width="1" stroke-opacity="0.55"/>
        <line x1="40" y1="48" x2="56" y2="38" stroke="white" stroke-width="1" stroke-opacity="0.55"/>
        <line x1="56" y1="38" x2="76" y2="20" stroke="white" stroke-width="1" stroke-opacity="0.55"/>
        <circle cx="22"  cy="34" r="5"   fill="#E74C3C"/>
        <circle cx="42"  cy="16" r="3.5" fill="white"/>
        <circle cx="40"  cy="48" r="3"   fill="white"/>
        <circle cx="60"  cy="10" r="4.5" fill="#E74C3C"/>
        <circle cx="56"  cy="38" r="5"   fill="white"/>
        <circle cx="76"  cy="20" r="3.5" fill="white"/>
        <circle cx="72"  cy="50" r="4.5" fill="#E74C3C"/>
        <circle cx="94"  cy="44" r="3"   fill="white"/>
        <circle cx="108" cy="26" r="4.5" fill="#E74C3C"/>
        <circle cx="108" cy="60" r="3.5" fill="white"/>
      </svg>
    </a>
    {nav_html}
  </div>
  <div class="header-right">
    <a href="glossary.html" class="glossary-btn">
      <span data-en="📖 Glossary" data-fr="📖 Glossaire">📖 Glossary</span>
    </a>
    {gs_widget('search-index.json')}
    <div class="lang-toggle">
      <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
      <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
    </div>
  </div>
</header>

<main>
  <p class="site-intro" id="site-intro">
    Three ways to learn: <strong>Mind Maps</strong> to visualize the ecosystem,
    <strong>Deep Dives</strong> for in-depth articles,
    <strong>Glossary</strong> to understand the terminology.
  </p>

  {featured_html}

  <div class="main-layout">
    <aside class="news-sidebar">
      <div id="news" class="section-sep">
        <div class="section-sep-line"></div>
        <span class="section-sep-label" data-en="WHAT'S NEW" data-fr="NOUVEAUTÉS">WHAT'S NEW</span>
        <div class="section-sep-line"></div>
      </div>
      <div class="news-feed">
        {news_html}
      </div>
    </aside>

    <div class="main-content">
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
    </div>
  </div>
</main>

<footer>
  <span id="footer-text">Open source · Built to learn and share · </span>
  <a href="https://github.com/evausesgit/mind-map-ia" style="color:#E74C3C;text-decoration:none;">GitHub ↗</a>
</footer>

<script>
const uiTexts = {{
  en: {{
    footer: "Open source · Built to learn and share · ",
    searchPlaceholder: "Search concepts, models, tools…",
    intro: "Three ways to learn: <strong>Mind Maps</strong> to visualize the ecosystem, <strong>Deep Dives</strong> for in-depth articles, <strong>Glossary</strong> to understand the terminology."
  }},
  fr: {{
    footer: "Open source · Construit pour apprendre et partager · ",
    searchPlaceholder: "Rechercher concepts, modèles, outils…",
    intro: "Trois façons d'apprendre : <strong>Mind Maps</strong> pour visualiser l'écosystème, <strong>Deep Dives</strong> pour des articles approfondis, <strong>Glossaire</strong> pour comprendre la terminologie."
  }}
}};
let currentLang = 'en';
function setLang(lang) {{
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  document.getElementById('footer-text').textContent = uiTexts[lang].footer;
  document.getElementById('site-intro').innerHTML = uiTexts[lang].intro;
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = lang === 'fr' ? (el.dataset.fr || el.dataset.en) : el.dataset.en;
  }});
}}

// Highlight news item if URL has a news anchor
if (location.hash.startsWith('#news-')) {{
  const el = document.getElementById(location.hash.slice(1));
  if (el) {{
    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    el.style.borderLeftColor = '#E74C3C';
    el.style.background = '#16213E';
    setTimeout(() => {{ el.style.borderLeftColor = ''; el.style.background = ''; }}, 3000);
  }}
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
