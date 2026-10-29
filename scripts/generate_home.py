#!/usr/bin/env python3
"""Generate web/index.html (landing page) and web/news.html (full news feed)."""

import re
import yaml
from pathlib import Path
from urllib.parse import urlparse
import sys
sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import head_assets, site_header, site_footer, chrome_script, load_topics, load_registry

ROOT = Path(__file__).parent.parent
GLOSSARY_FILE = ROOT / "data" / "glossary.yaml"
MACRO_FILE = ROOT / "data" / "ecosystem-macro.yaml"
NEWS_FILE = ROOT / "data" / "news.yaml"
OUTPUT = ROOT / "web" / "index.html"
NEWS_OUTPUT = ROOT / "web" / "news.html"

HOME_NEWS_COUNT = 8

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
}
MONTHS_SHORT = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}
NEWS_TYPES = {
    "update":      {"en": "Industry", "fr": "Actu"},
    "research":    {"en": "Research", "fr": "Recherche"},
    "new-content": {"en": "On the site", "fr": "Sur le site"},
    "new-feature": {"en": "On the site", "fr": "Sur le site"},
}


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def esc(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def bi(field, tag="span", cls="", fallback=""):
    """Bilingual element swapped by setLang() through data-en / data-fr."""
    en = t(field, "en") or fallback
    fr = t(field, "fr") or en
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-en="{esc(en)}" data-fr="{esc(fr)}">{esc(en)}</{tag}>'


def load_news():
    """Load all news entries from data/news.yaml, sorted by date desc."""
    if not NEWS_FILE.exists():
        return []
    with open(NEWS_FILE) as f:
        data = yaml.safe_load(f)
    entries = data.get("news", [])
    entries.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return entries


def _slugify(text):
    """Turn a title into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:60]


def news_anchor(entry):
    return f"news-{entry.get('date', '')}-{_slugify(t(entry.get('title', ''), 'en'))}"


def short_date(date):
    try:
        y, m, d = (int(x) for x in str(date).split("-"))
    except ValueError:
        return {"en": str(date), "fr": str(date)}
    return {"en": f"{MONTHS_SHORT['en'][m-1]} {d}", "fr": f"{d} {MONTHS_SHORT['fr'][m-1]}"}


def source_of(link):
    host = urlparse(link).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def count_glossary_terms():
    if not GLOSSARY_FILE.exists():
        return 0
    with open(GLOSSARY_FILE) as f:
        return len((yaml.safe_load(f) or {}).get("terms", []))


# ── Shared page styles (home + news) ──────────────────────────────────────────

PAGE_CSS = """
:root {
  --l1: #F5EBCF; --l1s: #B8913A;
  --l2: #ECE4F6; --l2s: #7E5DB8;
  --l3: #E8EAEE; --l3s: #6E7684;
  --l4: #DFF0E7; --l4s: #3A8F66;
  --l5: #E0EBF6; --l5s: #4479B3;
}
:root[data-theme="dark"] {
  --l1: #3A3220; --l1s: #D9B45E; --l2: #2E2640; --l2s: #B49AE6; --l3: #26292F; --l3s: #9AA3B2;
  --l4: #1E3329; --l4s: #6CC79A; --l5: #1E2B3B; --l5s: #7FB0E6;
}
body { font-size: 16px; line-height: 1.6; }
.wrap {
  max-width: 1180px; margin: 0 auto;
  padding-left: max(20px, env(safe-area-inset-left, 0px));
  padding-right: max(20px, env(safe-area-inset-right, 0px));
}
h1, h2, h3 { margin: 0; text-wrap: balance; letter-spacing: -0.02em; }
p { margin: 0; }
a { color: inherit; }

.sec { padding-block: 56px 0; scroll-margin-top: calc(var(--header-h) + 16px); }
.sec-head {
  display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
  padding-bottom: 12px; border-bottom: 1px solid var(--line);
}
.sec-head h2 { font-size: 22px; font-weight: 600; }
.sec-head .more { font-size: 14px; color: var(--muted); text-decoration: none; white-space: nowrap; }
.sec-head .more:hover { color: var(--accent); }

/* Hero */
.hero { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: 56px; align-items: center; padding-block: 64px 8px; }
.hero h1 { font-size: clamp(36px, 5vw, 56px); line-height: 1.04; font-weight: 600; letter-spacing: -0.035em; margin-top: 16px; }
.hero .lede { font-size: 18px; color: var(--ink-2); margin-top: 18px; max-width: 30em; }
.hero .ctas { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
.hero .stats { display: flex; flex-wrap: wrap; gap: 6px 20px; margin-top: 28px; font: 13px var(--f-mono); color: var(--muted); }
.hero .stats b { color: var(--ink); font-weight: 500; }
.preview {
  display: block; position: relative; text-decoration: none;
  aspect-ratio: 16 / 11; max-width: 100%;
  border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
  background: radial-gradient(circle at 1px 1px, var(--line) 1px, transparent 0) 0 0 / 22px 22px, var(--surface);
  box-shadow: var(--shadow);
  transition: transform .25s, box-shadow .25s;
}
.preview:hover { transform: translateY(-3px); }
.preview svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.preview svg text { font-family: var(--f-ui); }
.preview-cap {
  position: absolute; left: 16px; right: 16px; bottom: 14px;
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  font: 12px var(--f-mono); color: var(--muted);
}
.preview-cap .go { color: var(--ink); font-family: var(--f-ui); font-size: 14px; font-weight: 500; }
.preview:hover .preview-cap .go { color: var(--accent); }
@media (prefers-reduced-motion: no-preference) {
  .pulse { animation: pulse 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
}

/* Tiles (maps, animations) */
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0 28px; }
.tile {
  display: grid; gap: 6px; align-content: start;
  padding-block: 18px 20px; border-bottom: 1px solid var(--line);
  text-decoration: none; color: var(--ink);
}
.tile .k { display: flex; align-items: center; gap: 8px; font: 500 11px/1 var(--f-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.tile .k i { width: 8px; height: 8px; border-radius: 2px; background: var(--l4s); }
.tile.diagram .k i { background: var(--l1s); }
.tile.anim .k i { background: var(--l2s); }
.tile .k .n { margin-left: auto; letter-spacing: 0; text-transform: none; }
.tile h3 { font-size: 16px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.3; transition: color .15s; }
.tile p { font-size: 14px; color: var(--ink-2); line-height: 1.5; }
.tile:hover h3 { color: var(--accent); }

/* Articles + news */
.split { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr); gap: 56px; }
.art {
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 20px;
  padding-block: 16px; border-bottom: 1px solid var(--line); text-decoration: none; color: var(--ink);
}
.art h3 { font-family: var(--f-read); font-size: 21px; font-weight: 500; line-height: 1.25; letter-spacing: -0.01em; transition: color .15s; }
.art p { font-size: 14px; color: var(--muted); grid-column: 1; line-height: 1.5; }
.art .m { grid-row: 1; grid-column: 2; font: 12px var(--f-mono); color: var(--muted); white-space: nowrap; padding-top: 5px; }
.art:hover h3 { color: var(--accent); }
.nws {
  display: grid; grid-template-columns: 58px minmax(0, 1fr); gap: 2px 14px;
  padding-block: 13px; border-bottom: 1px solid var(--line); text-decoration: none; color: var(--ink);
}
.nws time { grid-row: span 2; font: 12px var(--f-mono); color: var(--muted); padding-top: 2px; white-space: nowrap; }
.nws h3 { font-size: 14.5px; font-weight: 500; line-height: 1.4; letter-spacing: -0.005em; transition: color .15s; }
.nws .s { font: 12px var(--f-mono); color: var(--muted); }
.nws:hover h3 { color: var(--accent); }

/* Resources */
.res { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0 28px; }
.res a { display: grid; gap: 4px; padding-block: 14px; border-bottom: 1px solid var(--line); text-decoration: none; }
.res .h { display: flex; justify-content: space-between; gap: 8px; font-size: 15px; font-weight: 500; }
.res .h span:last-child { color: var(--muted); }
.res a:hover .h span:first-child { color: var(--accent); }
.res p { font-size: 13px; color: var(--muted); line-height: 1.45; }
main { padding-bottom: 88px; }

@media (max-width: 1000px) {
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .res { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 860px) {
  .hero { grid-template-columns: minmax(0, 1fr); gap: 36px; padding-block: 40px 0; }
  .split { grid-template-columns: minmax(0, 1fr); gap: 8px; }
}
@media (max-width: 560px) {
  .tiles, .res { grid-template-columns: minmax(0, 1fr); }
  .art { grid-template-columns: minmax(0, 1fr); }
  .art .m { grid-row: auto; grid-column: 1; padding-top: 0; }
  .sec { padding-block: 40px 0; }
}

/* ── News page ── */
.nf-hero { padding-block: 56px 28px; display: grid; gap: 14px; }
.nf-hero h1 { font-size: clamp(34px, 4.5vw, 48px); font-weight: 600; letter-spacing: -0.03em; line-height: 1.05; }
.nf-hero p { color: var(--ink-2); font-size: 17px; max-width: 36em; }
.nf-bar {
  position: sticky; top: var(--header-h); z-index: 50;
  display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
  padding-block: 12px; background: var(--bg); border-bottom: 1px solid var(--line);
}
.nf-filter {
  height: 32px; padding: 0 12px; font: 500 13px var(--f-ui); color: var(--ink-2);
  background: var(--surface); border: 1px solid var(--line); border-radius: 99px; cursor: pointer;
}
.nf-filter:hover { border-color: var(--line-strong); color: var(--ink); }
.nf-filter.on { background: var(--ink); border-color: var(--ink); color: var(--surface); }
.nf-filter .c { font: 11px var(--f-mono); opacity: .65; margin-left: 4px; }
.nf-search {
  margin-left: auto; height: 34px; width: min(280px, 100%); padding: 0 12px;
  font: 14px var(--f-ui); color: var(--ink); background: var(--surface);
  border: 1px solid var(--line); border-radius: 9px; outline: none;
}
.nf-search:focus { border-color: var(--ink-2); }
.nf-month {
  display: flex; align-items: baseline; justify-content: space-between;
  padding-block: 40px 10px; border-bottom: 1px solid var(--line);
  scroll-margin-top: calc(var(--header-h) + 70px);
}
.nf-month h2 { font-size: 20px; font-weight: 600; }
.nf-month span { font: 12px var(--f-mono); color: var(--muted); }
.nf-item {
  display: grid; grid-template-columns: 76px minmax(0, 1fr); gap: 4px 20px;
  padding-block: 20px; border-bottom: 1px solid var(--line);
  scroll-margin-top: calc(var(--header-h) + 70px);
  transition: background .6s;
}
.nf-item.flash { background: var(--accent-soft); }
.nf-item time { font: 12px var(--f-mono); color: var(--muted); padding-top: 4px; white-space: nowrap; }
.nf-body { display: grid; gap: 6px; max-width: 760px; }
.nf-body h3 { font-size: 18px; font-weight: 600; line-height: 1.35; letter-spacing: -0.01em; }
.nf-body h3 a { text-decoration: none; }
.nf-body h3 a:hover { color: var(--accent); }
.nf-body p { font-size: 15px; color: var(--ink-2); line-height: 1.6; }
.nf-foot { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; margin-top: 4px; font: 12px var(--f-mono); color: var(--muted); }
.nf-foot a { color: var(--muted); text-decoration: none; }
.nf-foot a:hover { color: var(--accent); }
.nf-copy { background: none; border: 0; padding: 0; font: inherit; color: var(--muted); cursor: pointer; }
.nf-copy:hover { color: var(--ink); }
.chip.ty-research { color: var(--info); }
.chip.ty-site { color: var(--accent); }
.nf-empty { padding: 48px 0; color: var(--muted); text-align: center; }
@media (max-width: 640px) {
  .nf-item { grid-template-columns: minmax(0, 1fr); }
  .nf-search { margin-left: 0; width: 100%; }
}
"""

LANG_JS = """
<script>
let currentLang = 'en';
function setLang(lang) {
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  document.querySelectorAll('[data-en]').forEach(el => {
    el.textContent = lang === 'fr' ? (el.dataset.fr || el.dataset.en) : el.dataset.en;
  });
  document.querySelectorAll('[data-ph-en]').forEach(el => {
    el.placeholder = lang === 'fr' ? el.dataset.phFr : el.dataset.phEn;
  });
}
</script>"""


def page(title, body, active, current, extra_js=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="Interactive maps, deep dives and a glossary to understand the LLM and generative AI ecosystem.">
{head_assets()}
<style>{PAGE_CSS}</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
{site_header(active=active, current=current)}
{body}
{site_footer()}
{LANG_JS}
{extra_js}
{chrome_script()}
</body>
</html>"""


# ── Home ─────────────────────────────────────────────────────────────────────

HERO_SVG = """<svg viewBox="0 0 480 330" aria-hidden="true">
  <g stroke="var(--line-strong)" stroke-width="1.2" fill="none">
    <path d="M92 80 C150 80 160 140 214 140"/><path d="M92 196 C150 196 160 140 214 140"/>
    <path d="M110 268 C170 268 180 226 236 226"/><path d="M302 140 C340 140 340 92 372 92"/>
    <path d="M302 140 C340 140 350 186 384 186"/><path d="M290 226 C330 226 350 186 384 186"/>
    <path d="M412 104 L412 172"/><path d="M412 200 L412 252"/>
  </g>
  <g stroke="var(--accent)" stroke-width="1.8" fill="none">
    <path d="M92 196 C150 196 160 140 214 140"/><path d="M302 140 C340 140 340 92 372 92"/><path d="M302 140 C340 140 350 186 384 186"/>
  </g>
  <g font-size="12" font-weight="500" text-anchor="middle" fill="var(--ink)">
    <rect x="24" y="66" width="128" height="28" rx="14" fill="var(--l5)" stroke="var(--l5s)"/><text x="88" y="84">Coding assistants</text>
    <rect x="24" y="182" width="128" height="28" rx="14" fill="var(--l4)" stroke="var(--l4s)" stroke-width="1.6"/><text x="88" y="200">AI Agents</text>
    <rect x="40" y="254" width="128" height="28" rx="14" fill="var(--l4)" stroke="var(--l4s)"/><text x="104" y="272">RAG</text>
    <rect x="214" y="126" width="88" height="28" rx="14" fill="var(--l3)" stroke="var(--l3s)"/><text x="258" y="144">Public API</text>
    <rect x="200" y="212" width="90" height="28" rx="14" fill="var(--l4)" stroke="var(--l4s)"/><text x="245" y="230">MCP</text>
    <rect x="348" y="78" width="120" height="28" rx="14" fill="var(--l1)" stroke="var(--l1s)"/><text x="408" y="96">Transformer</text>
    <rect x="348" y="172" width="120" height="28" rx="14" fill="var(--l2)" stroke="var(--l2s)"/><text x="408" y="190">Language model</text>
    <rect x="348" y="252" width="120" height="28" rx="14" fill="var(--l1)" stroke="var(--l1s)"/><text x="408" y="270">Tokens</text>
  </g>
  <rect class="pulse" x="17" y="175" width="142" height="42" rx="21" fill="none" stroke="var(--accent)" stroke-width="1.4"/>
  <g font-family="var(--f-mono)" font-size="10" fill="var(--muted)" letter-spacing="1">
    <text x="24" y="52">DEV TOOLS · PATTERNS</text><text x="206" y="112">ACCESS</text><text x="348" y="64">FOUNDATIONS</text>
  </g>
</svg>"""


def build_home(maps, animations, links, topics, news):
    macro = next((m for m in maps if m.get("id") == "macro"), None)
    others = [m for m in maps if m.get("id") not in ("macro", "glossary")]
    n_terms = count_glossary_terms()

    def tile(m, kind_en, kind_fr, cls=""):
        n = m.get("nodes")
        count = f'<span class="n">{n}</span>' if n else ""
        return (
            f'<a class="tile {cls}" href="{m["output"]}">'
            f'<div class="k"><i></i>{bi({"en": kind_en, "fr": kind_fr})}{count}</div>'
            f'{bi(m["title"], "h3")}{bi(m.get("description", ""), "p")}</a>'
        )

    map_tiles = "".join(
        tile(m, "Diagram", "Diagramme", "diagram") if m.get("kind") == "diagram" else tile(m, "Map", "Carte")
        for m in others
    )
    anim_tiles = "".join(tile(a, "Animation", "Animation", "anim") for a in animations)

    arts = ""
    for tp in topics:
        cat = {"en": "Reflection", "fr": "Réflexion"} if tp.get("category") == "reflexion" else {"en": "Deep dive", "fr": "Article"}
        arts += (
            f'<a class="art" href="topics/{tp["id"]}.html">{bi(tp.get("title", ""), "h3")}'
            f'<span class="m">{bi(cat)} · {tp["_minutes"]} min</span>'
            f'{bi(tp.get("summary", ""), "p")}</a>'
        )

    nws = ""
    for n in news[:HOME_NEWS_COUNT]:
        href = f"news.html#{news_anchor(n)}"
        src = source_of(n["link"]) if n.get("link") else "mind-map-ia"
        nws += (
            f'<a class="nws" href="{href}"><time>{bi(short_date(n.get("date", "")))}</time>'
            f'{bi(n.get("title", ""), "h3")}<span class="s">{esc(src)}</span></a>'
        )

    res = ""
    for ln in links:
        res += (
            f'<a href="{ln["url"]}" target="_blank" rel="noopener">'
            f'<span class="h">{bi(ln["title"])}<span>↗</span></span>{bi(ln.get("description", ""), "p")}</a>'
        )

    macro_href = macro["output"] if macro else "macro.html"
    macro_nodes = macro.get("nodes", 26) if macro else 26
    body = f"""<main>
  <div class="wrap">
    <section class="hero">
      <div>
        {bi({"en": "Understand the LLM ecosystem", "fr": "Comprendre l'écosystème des LLM"}, "div", "eyebrow")}
        {bi({"en": "Generative AI, explained one map at a time.", "fr": "L'IA générative, expliquée une carte à la fois."}, "h1")}
        {bi({"en": "Interactive maps, deep dives and a glossary to see how models, tools and architecture patterns fit together.",
             "fr": "Des cartes interactives, des articles de fond et un glossaire pour voir comment les modèles, les outils et les patterns s'articulent."}, "p", "lede")}
        <div class="ctas">
          <a class="btn primary" href="{macro_href}">{bi({"en": "Start with the big picture", "fr": "Commencer par la vue d'ensemble"})} <span aria-hidden="true">→</span></a>
          <a class="btn" href="glossary.html">{bi({"en": "Browse the glossary", "fr": "Parcourir le glossaire"})}</a>
        </div>
        <div class="stats">
          <span><b>{len(maps)}</b> {bi({"en": "maps & diagrams", "fr": "cartes et diagrammes"})}</span>
          <span><b>{len(topics)}</b> {bi({"en": "articles", "fr": "articles"})}</span>
          <span><b>{n_terms}</b> {bi({"en": "glossary terms", "fr": "termes"})}</span>
          <span><b>{len(news)}</b> {bi({"en": "news items", "fr": "actualités"})}</span>
        </div>
      </div>
      <a class="preview" href="{macro_href}" aria-label="Open the big picture map">
        {HERO_SVG}
        <div class="preview-cap"><span>{macro_nodes} {bi({"en": "concepts · 5 layers", "fr": "concepts · 5 couches"})}</span>
        <span class="go">{bi({"en": "Open the map →", "fr": "Ouvrir la carte →"})}</span></div>
      </a>
    </section>

    <section class="sec" id="maps">
      <div class="sec-head">{bi({"en": "Maps & diagrams", "fr": "Cartes et diagrammes"}, "h2")}
        <a class="more" href="ecosystem.html">{bi({"en": "Full ecosystem map →", "fr": "Carte complète de l'écosystème →"})}</a></div>
      <div class="tiles">{map_tiles}</div>
    </section>

    <section class="sec split">
      <div id="articles" style="scroll-margin-top:calc(var(--header-h) + 16px)">
        <div class="sec-head">{bi({"en": "Articles", "fr": "Articles"}, "h2")}
          <span class="more">{len(topics)} {bi({"en": "pieces", "fr": "textes"})}</span></div>
        {arts}
      </div>
      <div id="latest">
        <div class="sec-head">{bi({"en": "Latest news", "fr": "Actualités"}, "h2")}
          <a class="more" href="news.html">{bi({"en": f"All {len(news)} →", "fr": f"Voir les {len(news)} →"})}</a></div>
        {nws}
      </div>
    </section>

    <section class="sec" id="animations">
      <div class="sec-head">{bi({"en": "Animations", "fr": "Animations"}, "h2")}</div>
      <div class="tiles">{anim_tiles}</div>
    </section>

    <section class="sec" id="resources">
      <div class="sec-head">{bi({"en": "Resources elsewhere", "fr": "Ressources ailleurs"}, "h2")}</div>
      <div class="res">{res}</div>
    </section>
  </div>
</main>"""

    # Old news anchors (index.html#news-…) now live on news.html
    redirect = """<script>
if (location.hash === '#news' || location.hash.indexOf('#news-') === 0) location.replace('news.html' + (location.hash === '#news' ? '' : location.hash));
</script>"""
    return page("Mind Map IA — Understand the LLM & AI ecosystem", body, "", "index.html", redirect)


# ── News page ────────────────────────────────────────────────────────────────

def build_news_page(news):
    def kind(n):
        ty = n.get("type", "update")
        return "site" if ty in ("new-content", "new-feature") else ty

    counts = {"all": len(news)}
    for n in news:
        counts[kind(n)] = counts.get(kind(n), 0) + 1

    filters = [("all", {"en": "All", "fr": "Tout"}), ("update", NEWS_TYPES["update"]),
               ("research", NEWS_TYPES["research"]), ("site", NEWS_TYPES["new-content"])]
    filter_html = "".join(
        f'<button class="nf-filter{" on" if k == "all" else ""}" data-k="{k}" onclick="nfFilter(\'{k}\')">'
        f'{bi(lbl)}<span class="c">{counts.get(k, 0)}</span></button>'
        for k, lbl in filters if counts.get(k)
    )

    items, month = "", None
    for n in news:
        date = str(n.get("date", ""))
        ym = date[:7]
        if ym != month:
            month = ym
            try:
                y, m = int(ym[:4]), int(ym[5:7])
                label = {"en": f"{MONTHS['en'][m-1]} {y}", "fr": f"{MONTHS['fr'][m-1].capitalize()} {y}"}
            except ValueError:
                label = {"en": ym, "fr": ym}
            month_count = sum(1 for x in news if str(x.get("date", ""))[:7] == ym)
            items += f'<div class="nf-month" data-month="{ym}">{bi(label, "h2")}<span>{month_count}</span></div>'
        k = kind(n)
        anchor = news_anchor(n)
        link = n.get("link", "")
        title = bi(n.get("title", ""))
        title_html = f'<a href="{link}" target="_blank" rel="noopener">{title}</a>' if link else title
        type_lbl = NEWS_TYPES.get(n.get("type", "update"), NEWS_TYPES["update"])
        chip_cls = {"research": " ty-research", "site": " ty-site"}.get(k, "")
        src = f'<a href="{link}" target="_blank" rel="noopener">{esc(source_of(link))} ↗</a>' if link else ""
        search_txt = esc((t(n.get("title", ""), "en") + " " + t(n.get("title", ""), "fr") + " " +
                          t(n.get("description", ""), "en") + " " + t(n.get("description", ""), "fr")).lower())
        items += f"""
<article class="nf-item" id="{anchor}" data-k="{k}" data-month="{ym}" data-q="{search_txt}">
  <time datetime="{date}">{bi(short_date(date))}</time>
  <div class="nf-body">
    <h3>{title_html}</h3>
    {bi(n.get("description", ""), "p")}
    <div class="nf-foot"><span class="chip{chip_cls}">{bi(type_lbl)}</span>{src}
      <button class="nf-copy" onclick="nfCopy(this,'{anchor}')">{bi({"en": "Copy link", "fr": "Copier le lien"})}</button></div>
  </div>
</article>"""

    body = f"""<main>
  <div class="wrap">
    <section class="nf-hero">
      {bi({"en": "News", "fr": "Actualités"}, "div", "eyebrow")}
      {bi({"en": "What changed in AI, and on this site", "fr": "Ce qui bouge dans l'IA, et sur ce site"}, "h1")}
      {bi({"en": "Daily briefings on models, labs and enterprise AI, plus every new map and article published here.",
           "fr": "Des brèves quotidiennes sur les modèles, les labos et l'IA en entreprise, et chaque nouvelle carte ou article publié ici."}, "p")}
    </section>
    <div class="nf-bar">
      {filter_html}
      <input class="nf-search" id="nf-q" type="search" placeholder="Filter news…" data-ph-en="Filter news…" data-ph-fr="Filtrer les actualités…" oninput="nfApply()">
    </div>
    <div id="nf-list">{items}</div>
    <div class="nf-empty" id="nf-empty" hidden>{bi({"en": "No news matches this filter.", "fr": "Aucune actualité ne correspond à ce filtre."})}</div>
  </div>
</main>"""

    js = """<script>
let nfKind = 'all';
function nfFilter(k) {
  nfKind = k;
  document.querySelectorAll('.nf-filter').forEach(b => b.classList.toggle('on', b.dataset.k === k));
  nfApply();
}
function nfApply() {
  const q = document.getElementById('nf-q').value.trim().toLowerCase();
  const seen = {};
  let shown = 0;
  document.querySelectorAll('.nf-item').forEach(el => {
    const ok = (nfKind === 'all' || el.dataset.k === nfKind) && (!q || el.dataset.q.indexOf(q) !== -1);
    el.hidden = !ok;
    if (ok) { seen[el.dataset.month] = (seen[el.dataset.month] || 0) + 1; shown++; }
  });
  document.querySelectorAll('.nf-month').forEach(m => {
    m.hidden = !seen[m.dataset.month];
    const c = m.querySelector('span:last-child'); if (c) c.textContent = seen[m.dataset.month] || '';
  });
  document.getElementById('nf-empty').hidden = shown > 0;
}
function nfCopy(btn, anchor) {
  const url = location.origin + location.pathname + '#' + anchor;
  const done = () => { const old = btn.innerHTML; btn.textContent = '✓'; setTimeout(() => { btn.innerHTML = old; }, 1200); };
  if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
}
if (location.hash.indexOf('#news-') === 0) {
  const el = document.getElementById(location.hash.slice(1));
  if (el) {
    el.scrollIntoView({ block: 'center' });
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 2600);
  }
}
</script>"""
    return page("News — Mind Map IA", body, "news", "news.html", js)


def main():
    config = load_registry()
    maps = config.get("maps", [])
    animations = config.get("animations", [])
    links = config.get("links", [])
    topics = list(load_topics())
    news = load_news()

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(build_home(maps, animations, links, topics, news), encoding="utf-8")
    print(f"✓ Generated {OUTPUT} ({len(maps)} maps)")
    NEWS_OUTPUT.write_text(build_news_page(news), encoding="utf-8")
    print(f"✓ Generated {NEWS_OUTPUT} ({len(news)} news)")


if __name__ == "__main__":
    main()
