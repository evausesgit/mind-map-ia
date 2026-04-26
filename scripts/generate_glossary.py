#!/usr/bin/env python3
"""Generate web/glossary.html from data/glossary.yaml"""

import re
import yaml
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from global_search import widget_html as gs_widget

ROOT = Path(__file__).parent.parent
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
MAPS_FILE = ROOT / "data" / "maps.yaml"
TOPICS_DIR = ROOT / "data" / "topics"
OUTPUT = ROOT / "web" / "glossary.html"


def load_topics_meta():
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


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def build_alias_entries(terms, skip_id=None):
    """Return list of (alias, id) sorted longest-first, excluding skip_id."""
    entries = []
    for term in terms:
        tid = term["id"]
        if tid == skip_id:
            continue
        label_en = t(term["label"], "en")
        aliases = term.get("aliases", [label_en])
        for alias in aliases:
            if alias.strip():
                entries.append((alias, tid))
    entries.sort(key=lambda x: len(x[0]), reverse=True)
    return entries


def link_terms(text, entries):
    """Replace alias occurrences in text with <a href="#id"> links.
    Skips replacements inside existing HTML tags."""
    import html as html_mod
    safe = html_mod.escape(text)
    for alias, tid in entries:
        escaped_alias = re.escape(alias)
        pattern = re.compile(
            r'(<[^>]*>)|(\b' + escaped_alias + r'\b)',
            re.IGNORECASE
        )
        def replacer(m, tid=tid):
            if m.group(1):
                return m.group(1)  # leave HTML tags untouched
            return f'<a href="#{tid}" class="gloss-link">{m.group(2)}</a>'
        safe = pattern.sub(replacer, safe)
    return safe


def format_desc(text, entries):
    """Parse markdown-ish text into HTML paragraphs/lists with glossary links."""
    lines = text.split('\n')
    html = ''
    in_ol = False
    in_ul = False

    def flush():
        nonlocal html, in_ol, in_ul
        if in_ol:
            html += '</ol>'
            in_ol = False
        if in_ul:
            html += '</ul>'
            in_ul = False

    def inline(s):
        linked = link_terms(s, entries)
        linked = re.sub(r'\[(.+?)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', linked)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', linked)

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            flush()
            continue
        ol_match = re.match(r'^(\d+)\. (.+)', trimmed)
        ul_match = re.match(r'^[-*] (.+)', trimmed)
        if ol_match:
            if in_ul:
                html += '</ul>'
                in_ul = False
            if not in_ol:
                html += '<ol>'
                in_ol = True
            html += f'<li>{inline(ol_match.group(2))}</li>'
        elif ul_match:
            if in_ol:
                html += '</ol>'
                in_ol = False
            if not in_ul:
                html += '<ul>'
                in_ul = True
            html += f'<li>{inline(ul_match.group(1))}</li>'
        else:
            flush()
            html += f'<p>{inline(trimmed)}</p>'
    flush()
    return html


def build_nav(maps, topics=None, links=None):
    map_items = ""
    for m in (maps or []):
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

    deep_dives = [tp for tp in (topics or []) if tp.get("category") != "reflexion"]
    reflexions = [tp for tp in (topics or []) if tp.get("category") == "reflexion"]

    def _topic_items(topic_list):
        items = ""
        for topic in topic_list:
            tid = topic.get("id", "")
            title_en = t(topic.get("title",   ""), "en")
            title_fr = t(topic.get("title",   ""), "fr") or title_en
            summ_en  = t(topic.get("summary", ""), "en")
            summ_fr  = t(topic.get("summary", ""), "fr") or summ_en
            items += (
                f'<a href="topics/{tid}.html" class="nav-item">'
                f'<span class="nav-item-icon">📝</span>'
                f'<span class="nav-item-info">'
                f'<span class="nav-item-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
                f'<span class="nav-item-desc" data-en="{summ_en}" data-fr="{summ_fr}">{summ_en}</span>'
                f'</span></a>'
            )
        return items

    dive_items = _topic_items(deep_dives)
    reflexion_items = _topic_items(reflexions)

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


def generate_html(data, maps, topics=None, links=None):
    terms = data["terms"]
    title_en = t(data["meta"]["title"], "en")
    title_fr = t(data["meta"]["title"], "fr")
    nav_html = build_nav(maps, topics=topics, links=links)

    terms_sorted = sorted(terms, key=lambda x: t(x["label"], "en").lower())

    # Build linked descriptions for every term (EN + FR)
    term_descs = {}
    for term in terms_sorted:
        tid = term["id"]
        entries = build_alias_entries(terms_sorted, skip_id=tid)
        raw_en = t(term["description"], "en").strip()
        raw_fr = t(term["description"], "fr").strip() or raw_en
        term_descs[tid] = {
            "en": format_desc(raw_en, entries),
            "fr": format_desc(raw_fr, entries),
        }
    term_descs_js = json.dumps(term_descs, ensure_ascii=False)

    # Build term cards
    cards_html = ""
    for term in terms_sorted:
        tid = term["id"]
        label_en = t(term["label"], "en")
        label_fr = t(term["label"], "fr") or label_en
        aliases = term.get("aliases", [])
        aliases_str = ", ".join(a for a in aliases if a.lower() != label_en.lower())
        aliases_html = (
            f'<div class="aliases" data-en="{aliases_str}" data-fr="{aliases_str}">{aliases_str}</div>'
            if aliases_str else ""
        )

        see_also = term.get("see_also")
        see_also_html = ""
        if see_also:
            sa_url = see_also.get("url", "")
            sa_label_en = t(see_also.get("label", ""), "en")
            sa_label_fr = t(see_also.get("label", ""), "fr") or sa_label_en
            see_also_html = (
                f'<div class="see-also">'
                f'→ <a href="{sa_url}" class="see-also-link" data-en="{sa_label_en}" data-fr="{sa_label_fr}">{sa_label_en}</a>'
                f'</div>'
            )

        linked_desc_en = term_descs[tid]["en"]

        cards_html += f"""
  <div class="term-card" id="{tid}">
    <div class="term-header">
      <span class="term-label" data-en="{label_en}" data-fr="{label_fr}">{label_en}</span>
      {aliases_html}
    </div>
    <div class="term-desc" data-tid="{tid}">{linked_desc_en}</div>
    {see_also_html}
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
<link rel="icon" type="image/svg+xml" href="favicon.svg">
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
    background: #0D1117;
    color: white;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid #1E2D4E;
  }}
  header h1 {{ font-size: 20px; font-weight: 700; }}
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
    min-width: 110px;
    text-align: center;
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
  .term-desc p {{ margin-bottom: 8px; }}
  .term-desc p:last-child {{ margin-bottom: 0; }}
  .term-desc ol, .term-desc ul {{ margin: 6px 0 8px 18px; }}
  .term-desc li {{ margin-bottom: 3px; }}
  .term-desc strong {{ font-weight: 600; color: #1A1A2E; }}
  .gloss-link {{
    color: #1A1A2E;
    text-decoration: underline;
    text-decoration-style: dotted;
    text-underline-offset: 3px;
    font-weight: 500;
  }}
  .gloss-link:hover {{ color: #3498DB; text-decoration-style: solid; }}
  .see-also {{ margin-top: 10px; font-size: 13px; color: #555; }}
  .see-also-link {{ color: #1A1A2E; font-weight: 600; text-decoration: underline; text-underline-offset: 2px; }}
  .see-also-link:hover {{ color: #3498DB; }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    {nav_html}
    <h1 id="main-title">{title_en}</h1>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    {gs_widget('search-index.json')}
    <div class="lang-toggle">
      <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
      <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
    </div>
  </div>
</header>

<div class="alphabet-index">
  {index_html}
</div>

<div class="content" id="cards-container">
{cards_html}
</div>

<script>
const TITLES = {{ "en": "{title_en}", "fr": "{title_fr}" }};
const TERM_DESCS = {term_descs_js};
let lang = 'en';

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.getElementById('main-title').textContent = TITLES[lang];
  // Plain text elements
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
  // Term descriptions (contain linked HTML — use innerHTML)
  document.querySelectorAll('.term-desc[data-tid]').forEach(el => {{
    const d = TERM_DESCS[el.dataset.tid];
    if (d) el.innerHTML = d[lang] || d.en;
  }});
}}
</script>
</body>
</html>"""
    return html


def main():
    with open(GLOSSARY_FILE) as f:
        data = yaml.safe_load(f)
    with open(MAPS_FILE) as f:
        maps_config = yaml.safe_load(f)
    maps = maps_config.get("maps", [])
    links = maps_config.get("links", [])
    topics = load_topics_meta()
    html = generate_html(data, maps, topics=topics, links=links)
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT}")
    print(f"  {len(data['terms'])} terms")


if __name__ == "__main__":
    main()
