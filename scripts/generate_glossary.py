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
OUTPUT = ROOT / "web" / "glossary.html"


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


def build_nav(maps):
    items = ""
    for m in maps:
        if m.get("id") == "glossary":
            active = "active"
        else:
            active = ""
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
    return (
        '<div class="nav-menu">'
        '  <button class="nav-btn">≡ Maps ▾</button>'
        '  <div class="nav-dropdown">'
        '    <a href="index.html" class="nav-home">← Home</a>'
        f"   {items}"
        "  </div>"
        "</div>"
    )


def generate_html(data, maps):
    terms = data["terms"]
    title_en = t(data["meta"]["title"], "en")
    title_fr = t(data["meta"]["title"], "fr")
    nav_html = build_nav(maps)

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
  .nav-menu {{ position: relative; }}
  .nav-btn {{
    padding: 6px 14px;
    border: 1.5px solid #444;
    border-radius: 8px;
    background: transparent;
    color: #BDC3C7;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .nav-btn:hover {{ border-color: #aaa; color: white; }}
  .nav-dropdown {{
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    min-width: 260px;
    background: #16213E;
    border: 1px solid #1E2D4E;
    border-radius: 10px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    z-index: 1000;
    display: none;
  }}
  .nav-menu:hover .nav-dropdown,
  .nav-menu:focus-within .nav-dropdown {{ display: block; }}
  .nav-dropdown a {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid #1E2D4E;
    text-decoration: none;
    color: #BDC3C7;
    font-size: 13px;
    transition: background 0.1s;
  }}
  .nav-dropdown a:last-child {{ border-bottom: none; }}
  .nav-dropdown a:hover {{ background: #1E2D4E; color: white; }}
  .nav-dropdown a.active {{ color: white; background: #1E2D4E; }}
  .nav-dropdown a .nav-icon {{ font-size: 18px; }}
  .nav-dropdown a .nav-info {{ display: flex; flex-direction: column; }}
  .nav-dropdown a .nav-title {{ font-weight: 600; }}
  .nav-dropdown a .nav-desc {{ font-size: 11px; color: #7F8C8D; margin-top: 1px; }}
  .nav-home {{
    color: #BDC3C7 !important;
    font-size: 13px !important;
    border-bottom: 1px solid #1E2D4E;
  }}
  .nav-home:hover {{ color: #FF6B6B !important; }}
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
  /* ── Search ── */
  .search-wrapper {{
    position: relative;
    margin-left: 8px;
  }}
  .search-input {{
    background: #0D1117;
    border: 1.5px solid #333;
    border-radius: 8px;
    color: white;
    font-size: 13px;
    padding: 6px 32px 6px 32px;
    width: 180px;
    outline: none;
    transition: all 0.2s;
  }}
  .search-input::placeholder {{ color: #555; }}
  .search-input:focus {{
    border-color: #E74C3C;
    width: 260px;
    background: #111;
  }}
  .search-icon {{
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 13px;
    color: #555;
    pointer-events: none;
  }}
  .search-clear {{
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #555;
    font-size: 14px;
    cursor: pointer;
    display: none;
    line-height: 1;
  }}
  .search-clear:hover {{ color: white; }}
  .search-empty-msg {{
    text-align: center;
    padding: 40px 20px;
    color: #95A5A6;
    font-size: 14px;
  }}
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    {nav_html}
    <h1 id="main-title">{title_en}</h1>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input class="search-input" id="search-input" type="text"
             placeholder="Search..." autocomplete="off" />
      <button class="search-clear" id="search-clear" onclick="clearSearch()">✕</button>
    </div>
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
<div class="search-empty-msg" id="no-results" style="display:none">
  <span id="no-results-text">No results</span>
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
  document.getElementById('search-input').placeholder = lang === 'fr' ? 'Rechercher...' : 'Search...';
  document.getElementById('no-results-text').textContent = lang === 'fr' ? 'Aucun résultat' : 'No results';
  // Plain text elements
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
  // Term descriptions (contain linked HTML — use innerHTML)
  document.querySelectorAll('.term-desc[data-tid]').forEach(el => {{
    const d = TERM_DESCS[el.dataset.tid];
    if (d) el.innerHTML = d[lang] || d.en;
  }});
  // Re-apply search filter in new language
  const q = document.getElementById('search-input').value.trim();
  if (q) filterCards(q);
}}

// ── Search / filter ──────────────────────────
const searchInput = document.getElementById('search-input');
const searchClear = document.getElementById('search-clear');

function normalize(s) {{ return (s || '').toLowerCase(); }}

function cardMatches(card, q) {{
  const tid = card.querySelector('.term-desc') && card.querySelector('.term-desc').dataset.tid;
  const label = normalize(card.querySelector('.term-label') ? card.querySelector('.term-label').textContent : '');
  const aliases = normalize(card.querySelector('.aliases') ? card.querySelector('.aliases').textContent : '');
  const desc = tid && TERM_DESCS[tid] ? normalize(TERM_DESCS[tid][lang] || TERM_DESCS[tid].en) : '';
  return label.includes(q) || aliases.includes(q) || desc.includes(q);
}}

function filterCards(q) {{
  const cards = document.querySelectorAll('.term-card');
  let visible = 0;
  cards.forEach(card => {{
    const show = cardMatches(card, normalize(q));
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('no-results').style.display = visible === 0 ? 'block' : 'none';
}}

function clearSearch() {{
  searchInput.value = '';
  searchClear.style.display = 'none';
  document.querySelectorAll('.term-card').forEach(c => c.style.display = '');
  document.getElementById('no-results').style.display = 'none';
}}

searchInput.addEventListener('input', () => {{
  const q = searchInput.value;
  searchClear.style.display = q ? 'block' : 'none';
  if (!q.trim()) {{ clearSearch(); return; }}
  filterCards(q.trim());
}});

searchInput.addEventListener('keydown', e => {{
  if (e.key === 'Escape') clearSearch();
}});
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
    html = generate_html(data, maps)
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT}")
    print(f"  {len(data['terms'])} terms")


if __name__ == "__main__":
    main()
