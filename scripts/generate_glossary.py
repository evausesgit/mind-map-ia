#!/usr/bin/env python3
"""Generate web/glossary.html from data/glossary.yaml"""

import re
import yaml
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import head_assets, site_header, site_footer, chrome_script

ROOT = Path(__file__).parent.parent
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
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


def generate_html(data):
    terms = data["terms"]
    title_en = t(data["meta"]["title"], "en")
    title_fr = t(data["meta"]["title"], "fr") or title_en

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

    # Term rows, grouped under a letter heading
    cards_html = ""
    current_letter = None
    for term in terms_sorted:
        tid = term["id"]
        label_en = t(term["label"], "en")
        label_fr = t(term["label"], "fr") or label_en
        letter = label_en[0].upper()
        if letter != current_letter:
            current_letter = letter
            cards_html += f'\n  <h2 class="letter" id="letter-{letter}">{letter}</h2>'
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
                f'<a href="{sa_url}" class="see-also-link" data-en="{sa_label_en} →" data-fr="{sa_label_fr} →">{sa_label_en} →</a>'
                f'</div>'
            )

        search_txt = " ".join([label_en, label_fr] + aliases).lower().replace('"', "")
        cards_html += f"""
  <article class="term-card" id="{tid}" data-letter="{letter}" data-q="{search_txt}">
    <div class="term-header">
      <h3 class="term-label" data-en="{label_en}" data-fr="{label_fr}">{label_en}</h3>
      {aliases_html}
    </div>
    <div class="term-main">
      <div class="term-desc" data-tid="{tid}">{term_descs[tid]["en"]}</div>
      {see_also_html}
    </div>
  </article>"""

    letters = sorted(set(t(term["label"], "en")[0].upper() for term in terms_sorted))
    index_html = "".join(f'<a href="#letter-{l}" class="idx-letter">{l}</a>' for l in letters)
    header_html = site_header(active="glossary", current="glossary.html")

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
    max-width: 1080px; margin: 0 auto;
    padding-left: max(20px, env(safe-area-inset-left, 0px));
    padding-right: max(20px, env(safe-area-inset-right, 0px));
  }}
  .g-hero {{ padding-block: 56px 28px; display: grid; gap: 14px; }}
  .g-hero h1 {{ margin: 0; font-size: clamp(34px, 4.5vw, 48px); font-weight: 600; letter-spacing: -0.03em; line-height: 1.05; }}
  .g-hero p {{ margin: 0; font-size: 17px; color: var(--ink-2); max-width: 36em; }}
  .alphabet-index {{
    position: sticky; top: var(--header-h); z-index: 50;
    display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
    padding-block: 12px; background: var(--bg); border-bottom: 1px solid var(--line);
  }}
  .idx-letter {{
    width: 30px; height: 30px; display: grid; place-items: center;
    border-radius: 8px;
    font: 500 13px var(--f-mono);
    color: var(--ink-2);
    text-decoration: none;
  }}
  .idx-letter:hover {{ background: var(--sunk); color: var(--ink); }}
  .g-filter {{
    margin-left: auto; height: 34px; width: min(260px, 100%); padding: 0 12px;
    font: 14px var(--f-ui); color: var(--ink); background: var(--surface);
    border: 1px solid var(--line); border-radius: 9px; outline: none;
  }}
  .g-filter:focus {{ border-color: var(--ink-2); }}
  .content {{ padding-bottom: 96px; }}
  .letter {{
    margin: 0; padding: 40px 0 10px;
    font: 500 13px var(--f-mono); letter-spacing: .08em; color: var(--accent);
    border-bottom: 1px solid var(--line);
    scroll-margin-top: calc(var(--header-h) + 64px);
  }}
  .term-card {{
    display: grid; grid-template-columns: minmax(0, 260px) minmax(0, 1fr); gap: 8px 40px;
    padding-block: 24px; border-bottom: 1px solid var(--line);
    scroll-margin-top: calc(var(--header-h) + 72px);
    transition: background .6s;
  }}
  .term-card:target {{ background: var(--accent-soft); }}
  .term-header {{ display: grid; gap: 6px; align-content: start; }}
  .term-label {{ margin: 0; font-size: 19px; font-weight: 600; letter-spacing: -0.015em; line-height: 1.3; }}
  .aliases {{ font: 12px/1.5 var(--f-mono); color: var(--muted); }}
  .term-main {{ min-width: 0; max-width: 640px; }}
  .term-desc {{ font-family: var(--f-read); font-size: 18px; line-height: 1.65; color: var(--ink); }}
  .term-desc p {{ margin: 0 0 12px; }}
  .term-desc p:last-child {{ margin-bottom: 0; }}
  .term-desc ol, .term-desc ul {{ margin: 6px 0 12px; padding-left: 22px; }}
  .term-desc li {{ margin-bottom: 4px; }}
  .term-desc strong {{ font-weight: 600; }}
  .term-desc a {{ color: var(--ink); text-underline-offset: 3px; text-decoration-color: var(--accent); }}
  .gloss-link {{
    color: inherit;
    text-decoration: underline;
    text-decoration-thickness: 1px;
    text-decoration-color: color-mix(in srgb, var(--accent) 55%, transparent);
    text-underline-offset: 3px;
  }}
  .gloss-link:hover {{ color: var(--accent); text-decoration-style: solid; }}
  .see-also {{ margin-top: 14px; font-size: 14px; }}
  .see-also-link {{ color: var(--ink); font-weight: 500; text-decoration: none; border-bottom: 1px solid var(--line-strong); }}
  .see-also-link:hover {{ color: var(--accent); border-color: var(--accent); }}
  .g-empty {{ padding: 48px 0; text-align: center; color: var(--muted); }}
  @media (max-width: 720px) {{
    .term-card {{ grid-template-columns: minmax(0, 1fr); }}
    .alphabet-index {{ flex-wrap: nowrap; overflow-x: auto; }}
    .g-filter {{ display: none; }}
    .term-desc {{ font-size: 17px; }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<main class="wrap">
  <section class="g-hero">
    <div class="eyebrow" data-en="Glossary" data-fr="Glossaire">Glossary</div>
    <h1 id="main-title">{title_en}</h1>
    <p data-en="{len(terms)} terms used across the maps and articles, each with plain definitions and links to related terms."
       data-fr="{len(terms)} termes utilisés dans les cartes et les articles, avec des définitions simples et des liens vers les termes liés.">{len(terms)} terms used across the maps and articles, each with plain definitions and links to related terms.</p>
  </section>

  <div class="alphabet-index">
    {index_html}
    <input class="g-filter" id="g-filter" type="search" placeholder="Filter terms…" oninput="gFilter(this.value)" aria-label="Filter terms">
  </div>

  <div class="content" id="cards-container">
  {cards_html}
  </div>
  <div class="g-empty" id="g-empty" hidden data-en="No term matches this filter." data-fr="Aucun terme ne correspond à ce filtre.">No term matches this filter.</div>
</main>

{site_footer()}

<script>
const TITLES = {{ "en": {json.dumps(title_en)}, "fr": {json.dumps(title_fr)} }};
const TERM_DESCS = {term_descs_js};
let lang = 'en';

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.getElementById('main-title').textContent = TITLES[lang];
  document.getElementById('g-filter').placeholder = lang === 'fr' ? 'Filtrer les termes…' : 'Filter terms…';
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

function gFilter(q) {{
  q = q.trim().toLowerCase();
  const seen = {{}};
  let shown = 0;
  document.querySelectorAll('.term-card').forEach(el => {{
    const ok = !q || el.dataset.q.indexOf(q) !== -1 || el.textContent.toLowerCase().indexOf(q) !== -1;
    el.hidden = !ok;
    if (ok) {{ seen[el.dataset.letter] = true; shown++; }}
  }});
  document.querySelectorAll('.letter').forEach(h => {{ h.hidden = !seen[h.textContent]; }});
  document.getElementById('g-empty').hidden = shown > 0;
}}
</script>
{chrome_script()}
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
