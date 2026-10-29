"""Shared site chrome — design tokens, header/nav, footer, theme & language persistence.

Every generator uses the same three pieces so the whole site reads as one system:

    head_assets()          inside <head>   fonts, tokens, header CSS, theme bootstrap
    site_header(...)       top of <body>   logo, 4-entry nav, search, FR/EN, theme toggle
    chrome_script()        end of <body>   dropdowns, mobile menu, theme + language memory

Pages keep their own `setLang(lang)` function; chrome_script() wraps it so the
chosen language is remembered from one page to the next.
"""

import re
from functools import lru_cache
from pathlib import Path

import yaml

from global_search import widget_html as gs_widget

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
TOPICS_DIR = ROOT / "data" / "topics"


def _t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def _attr(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


@lru_cache(maxsize=None)
def load_registry():
    with open(MAPS_FILE) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=None)
def load_topics():
    topics = []
    for path in sorted(TOPICS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        body = raw[m.end():]
        # Reading time: count words of the EN half only (content is duplicated per language)
        en = body.split("<!-- LANG:FR -->")[0]
        words = len(re.findall(r"\w+", en))
        fm["_minutes"] = max(2, round(words / 220))
        topics.append(fm)
    topics.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return tuple(topics)


# ── Design tokens ────────────────────────────────────────────────────────────
# Light is the default. Dark only applies when the reader picks it (stored in
# localStorage and set as data-theme="dark" on <html> before first paint).

TOKENS_CSS = """
:root {
  --bg: #FAFAF8;
  --surface: #FFFFFF;
  --sunk: #F3F3F0;
  --ink: #17181C;
  --ink-2: #45474E;
  --muted: #7A7D85;
  --line: #E6E6E2;
  --line-strong: #D2D2CC;
  --accent: #D8432E;
  --accent-ink: #B5361F;
  --accent-soft: #FBEAE6;
  --ok: #2F8F5B;
  --warn: #B7791F;
  --new: #6B4FBB;
  --info: #2F6FB5;
  --shadow-sm: 0 1px 2px rgba(20,20,25,.05);
  --shadow: 0 1px 2px rgba(20,20,25,.04), 0 12px 32px -16px rgba(20,20,25,.18);
  --f-ui: "Geist", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --f-mono: "Geist Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --f-read: "Newsreader", Georgia, "Times New Roman", serif;
  --r: 10px;
  --header-h: 60px;
  color-scheme: light;
}
:root[data-theme="dark"] {
  --bg: #0F1013;
  --surface: #17181C;
  --sunk: #1D1E23;
  --ink: #EDEDEF;
  --ink-2: #BDBFC6;
  --muted: #8E919A;
  --line: #2A2C32;
  --line-strong: #3A3D44;
  --accent: #F0644E;
  --accent-ink: #FF8571;
  --accent-soft: #3A1E19;
  --ok: #5BC48A;
  --warn: #E0A84A;
  --new: #A68BEB;
  --info: #6FA8E8;
  --shadow-sm: 0 1px 2px rgba(0,0,0,.3);
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 16px 40px -16px rgba(0,0,0,.6);
  color-scheme: dark;
}
"""

CHROME_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--f-ui);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
::selection { background: var(--accent-soft); }

/* ── Header ── */
.site-header {
  position: sticky; top: 0; z-index: 900;
  height: var(--header-h);
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  -webkit-backdrop-filter: saturate(1.4) blur(12px);
  backdrop-filter: saturate(1.4) blur(12px);
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.sh-inner {
  height: 100%;
  display: flex; align-items: center; gap: 28px;
  padding: 0 max(20px, env(safe-area-inset-right, 0px)) 0 max(20px, env(safe-area-inset-left, 0px));
}
.sh-logo {
  display: flex; align-items: center; gap: 10px;
  color: var(--ink); text-decoration: none;
  font-weight: 600; font-size: 15px; letter-spacing: -0.01em; white-space: nowrap;
}
.sh-logo svg { width: 26px; height: 26px; flex-shrink: 0; }
.sh-nav { display: flex; align-items: center; gap: 4px; }
.sh-group { position: relative; }
.sh-link {
  display: inline-flex; align-items: center; gap: 5px;
  height: 34px; padding: 0 10px;
  font: 500 14px/1 var(--f-ui); color: var(--ink-2);
  background: none; border: 0; border-radius: 8px; cursor: pointer;
  text-decoration: none; white-space: nowrap; position: relative;
  transition: color .15s, background .15s;
}
.sh-link:hover, .sh-group.open > .sh-link { color: var(--ink); background: var(--sunk); }
.sh-link.active { color: var(--ink); }
.sh-link.active::after {
  content: ""; position: absolute; left: 10px; right: 10px; bottom: -13px;
  height: 2px; border-radius: 2px; background: var(--accent);
}
.sh-caret { width: 10px; height: 10px; opacity: .55; transition: transform .15s; }
.sh-group.open .sh-caret { transform: rotate(180deg); }
.sh-menu {
  display: none;
  position: absolute; top: calc(100% + 10px); left: -8px;
  min-width: 340px; max-height: calc(100vh - 90px); overflow-y: auto;
  padding: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: var(--shadow);
}
.sh-menu.wide { min-width: 640px; display: none; grid-template-columns: 1fr 1fr; gap: 4px 8px; }
.sh-group.open > .sh-menu { display: block; }
.sh-group.open > .sh-menu.wide { display: grid; }
@media (hover: hover) and (min-width: 900px) {
  .sh-group:hover > .sh-menu { display: block; }
  .sh-group:hover > .sh-menu.wide { display: grid; }
  .sh-group:hover .sh-caret { transform: rotate(180deg); }
  .sh-menu::before { content: ""; position: absolute; left: 0; right: 0; top: -12px; height: 12px; }
}
.sh-menu-col { display: grid; gap: 2px; align-content: start; }
.sh-menu-label {
  padding: 10px 10px 4px;
  font: 500 11px/1 var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
}
.sh-item {
  display: grid; gap: 2px;
  padding: 8px 10px; border-radius: 8px;
  color: var(--ink); text-decoration: none;
  transition: background .12s;
}
.sh-item:hover, .sh-item.active { background: var(--sunk); }
.sh-item-title { font-size: 14px; font-weight: 500; line-height: 1.3; }
.sh-item-desc { font-size: 12.5px; color: var(--muted); line-height: 1.4; }
.sh-item.active .sh-item-title::before {
  content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); margin-right: 7px; vertical-align: 2px;
}
.sh-menu-foot {
  grid-column: 1 / -1; margin-top: 4px; padding: 10px; border-top: 1px solid var(--line);
  font-size: 13px; color: var(--muted);
}
.sh-menu-foot a { color: var(--ink); font-weight: 500; text-decoration: none; }
.sh-menu-foot a:hover { color: var(--accent); }

.sh-context {
  display: flex; align-items: baseline; gap: 10px; min-width: 0;
  font-size: 14px; color: var(--muted);
}
.sh-context .sh-sep { color: var(--line-strong); }
.sh-context .sh-title {
  color: var(--ink); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sh-context .sh-meta { font: 12px var(--f-mono); color: var(--muted); white-space: nowrap; }

.sh-right { margin-left: auto; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.lang-toggle {
  display: inline-flex; padding: 2px; gap: 2px;
  border: 1px solid var(--line); border-radius: 9px; background: var(--bg);
}
.lang-btn {
  height: 28px; min-width: 34px; padding: 0 8px;
  font: 500 12px/1 var(--f-mono); letter-spacing: .02em;
  color: var(--muted); background: none; border: 0; border-radius: 7px; cursor: pointer;
  transition: color .15s, background .15s;
}
.lang-btn:hover { color: var(--ink); }
.lang-btn.active { background: var(--ink); color: var(--surface); }
.icon-btn {
  width: 34px; height: 34px; display: inline-grid; place-items: center;
  color: var(--ink-2); background: none; border: 1px solid var(--line); border-radius: 9px; cursor: pointer;
  transition: color .15s, border-color .15s, background .15s;
}
.icon-btn:hover { color: var(--ink); border-color: var(--line-strong); background: var(--sunk); }
.icon-btn svg { width: 16px; height: 16px; }
.theme-btn .i-sun { display: none; }
:root[data-theme="dark"] .theme-btn .i-sun { display: block; }
:root[data-theme="dark"] .theme-btn .i-moon { display: none; }
.sh-burger { display: none; }

@media (max-width: 1100px) {
  .sh-context .sh-meta { display: none; }
}
@media (max-width: 960px) {
  .sh-inner { gap: 14px; }
  .sh-context { display: none; }
}
@media (max-width: 899px) {
  .sh-burger { display: inline-grid; }
  .sh-nav {
    display: none;
    position: fixed; left: 0; right: 0; top: var(--header-h); bottom: 0;
    flex-direction: column; align-items: stretch; gap: 2px;
    padding: 12px max(16px, env(safe-area-inset-right, 0px)) 32px max(16px, env(safe-area-inset-left, 0px));
    background: var(--surface); overflow-y: auto;
    border-top: 1px solid var(--line);
  }
  body.sh-menu-open .sh-nav { display: flex; }
  /* backdrop-filter would make the header the containing block of the fixed menu */
  body.sh-menu-open .site-header { -webkit-backdrop-filter: none; backdrop-filter: none; background: var(--surface); }
  body.sh-menu-open { overflow: hidden; }
  .sh-link { height: 44px; font-size: 16px; justify-content: space-between; width: 100%; }
  .sh-link.active::after { display: none; }
  .sh-link.active { color: var(--accent); }
  .sh-menu, .sh-menu.wide {
    position: static; min-width: 0; max-height: none; box-shadow: none; border: 0;
    padding: 0 0 8px 8px; grid-template-columns: 1fr;
  }
  .sh-item-desc { display: none; }
  .sh-right #gs-trigger .gs-placeholder, .sh-right #gs-trigger .gs-kbd { display: none; }
  .sh-right #gs-trigger { min-width: 0; width: 34px; height: 34px; padding: 0; justify-content: center; }
}

/* ── Footer ── */
.site-footer {
  border-top: 1px solid var(--line);
  padding: 28px max(20px, env(safe-area-inset-right, 0px)) 36px max(20px, env(safe-area-inset-left, 0px));
  color: var(--muted); font-size: 13px;
}
.sf-inner { max-width: 1180px; margin: 0 auto; display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: center; justify-content: space-between; }
.sf-inner a { color: var(--ink-2); text-decoration: none; }
.sf-inner a:hover { color: var(--accent); }
.sf-links { display: flex; gap: 18px; flex-wrap: wrap; }

/* ── Shared building blocks ── */
.eyebrow {
  font: 500 12px/1.2 var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
}
.chip {
  display: inline-flex; align-items: center; gap: 5px;
  font: 500 11px/1 var(--f-mono); letter-spacing: .02em;
  padding: 4px 8px; border-radius: 99px; border: 1px solid var(--line); color: var(--ink-2); background: var(--surface);
  white-space: nowrap;
}
.chip.dot::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.chip.st-stable { color: var(--ok); }
.chip.st-evolving { color: var(--warn); }
.chip.st-emerging { color: var(--new); }
.chip.st-deprecated { color: var(--muted); }
.chip.st-draft { color: var(--warn); }
.chip.st-review { color: var(--info); }
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  height: 40px; padding: 0 16px;
  font: 500 14px/1 var(--f-ui); color: var(--ink); text-decoration: none;
  background: var(--surface); border: 1px solid var(--line-strong); border-radius: 9px; cursor: pointer;
  transition: background .15s, border-color .15s, color .15s, transform .15s;
}
.btn:hover { border-color: var(--ink-2); }
.btn.primary { background: var(--ink); border-color: var(--ink); color: var(--surface); }
.btn.primary:hover { background: var(--accent); border-color: var(--accent); }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
}
"""

FONTS_HTML = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500'
    '&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap">'
)

THEME_BOOT = (
    "<script>try{if(localStorage.getItem('mmia-theme')==='dark')"
    "document.documentElement.setAttribute('data-theme','dark')}catch(e){}</script>"
)


def head_assets():
    """Fonts, design tokens, chrome CSS and the no-flash theme bootstrap."""
    return f"{THEME_BOOT}\n{FONTS_HTML}\n<style>{TOKENS_CSS}{CHROME_CSS}</style>"


LOGO_SVG = """<svg viewBox="0 0 26 26" aria-hidden="true">
  <g stroke="var(--line-strong)" stroke-width="1.1" fill="none">
    <path d="M4 9L11 5L18 10L22 6M11 5L12 14L18 10M4 9L12 14L7 20L15 21L22 16L18 10M15 21L12 14"/>
  </g>
  <g fill="var(--ink)"><circle cx="4" cy="9" r="1.8"/><circle cx="11" cy="5" r="1.8"/><circle cx="22" cy="6" r="1.8"/>
  <circle cx="7" cy="20" r="1.8"/><circle cx="15" cy="21" r="1.8"/><circle cx="22" cy="16" r="1.8"/></g>
  <circle cx="18" cy="10" r="2.6" fill="var(--accent)"/><circle cx="12" cy="14" r="2.6" fill="var(--accent)"/>
</svg>"""

CARET = '<svg class="sh-caret" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 4l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'


def _bi(en, fr, tag="span", cls=""):
    """Bilingual span: page setLang() swaps textContent using data-en / data-fr."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-en="{_attr(en)}" data-fr="{_attr(fr or en)}">{en}</{tag}>'


def _item(href, title, desc, active=False, external=False):
    ext = ' target="_blank" rel="noopener"' if external else ""
    act = " active" if active else ""
    return (
        f'<a href="{href}" class="sh-item{act}"{ext}>'
        + _bi(_t(title, "en"), _t(title, "fr"), cls="sh-item-title")
        + _bi(_t(desc, "en"), _t(desc, "fr"), cls="sh-item-desc")
        + "</a>"
    )


def build_nav(prefix="", active="", current=""):
    """The 4-entry site nav: Maps ▾ · Articles ▾ · News · Glossary."""
    reg = load_registry()
    maps = [m for m in reg.get("maps", []) if m.get("id") != "glossary"]
    animations = reg.get("animations", [])
    links = reg.get("links", [])
    topics = load_topics()
    dives = [tp for tp in topics if tp.get("category") != "reflexion"]
    refl = [tp for tp in topics if tp.get("category") == "reflexion"]

    map_items = [m for m in maps if m.get("kind") != "diagram"]
    diagram_items = [m for m in maps if m.get("kind") == "diagram"]

    maps_menu = '<div class="sh-menu wide"><div class="sh-menu-col">'
    maps_menu += '<div class="sh-menu-label">' + _bi("Maps", "Cartes") + "</div>"
    for m in map_items:
        maps_menu += _item(prefix + m["output"], m["title"], m.get("description", ""), active=current == m["output"])
    maps_menu += '</div><div class="sh-menu-col">'
    maps_menu += '<div class="sh-menu-label">' + _bi("Diagrams", "Diagrammes") + "</div>"
    for m in diagram_items:
        maps_menu += _item(prefix + m["output"], m["title"], m.get("description", ""), active=current == m["output"])
    if animations:
        maps_menu += '<div class="sh-menu-label">' + _bi("Animations", "Animations") + "</div>"
        for a in animations:
            maps_menu += _item(prefix + a["output"], a["title"], a.get("description", ""), active=current == a["output"])
    maps_menu += "</div></div>"

    art_menu = '<div class="sh-menu wide"><div class="sh-menu-col">'
    art_menu += '<div class="sh-menu-label">' + _bi("Deep dives", "Articles de fond") + "</div>"
    for tp in dives:
        href = f"{prefix}topics/{tp['id']}.html"
        art_menu += _item(href, tp.get("title", ""), tp.get("summary", ""), active=current == f"topics/{tp['id']}.html")
    art_menu += '</div><div class="sh-menu-col">'
    if refl:
        art_menu += '<div class="sh-menu-label">' + _bi("Reflection", "Réflexion") + "</div>"
        for tp in refl:
            href = f"{prefix}topics/{tp['id']}.html"
            art_menu += _item(href, tp.get("title", ""), tp.get("summary", ""), active=current == f"topics/{tp['id']}.html")
    if links:
        art_menu += '<div class="sh-menu-label">' + _bi("Resources", "Ressources") + "</div>"
        for ln in links:
            art_menu += _item(ln["url"], ln["title"], ln.get("description", ""), external=True)
    art_menu += "</div></div>"

    def top(key, en, fr, href=None, menu=None):
        cls = "sh-link active" if active == key else "sh-link"
        if menu:
            return (
                f'<div class="sh-group"><button class="{cls}" aria-haspopup="true" aria-expanded="false">'
                f"{_bi(en, fr)}{CARET}</button>{menu}</div>"
            )
        return f'<a href="{href}" class="{cls}">{_bi(en, fr)}</a>'

    return (
        '<nav class="sh-nav" aria-label="Site">'
        + top("maps", "Maps", "Cartes", menu=maps_menu)
        + top("articles", "Articles", "Articles", menu=art_menu)
        + top("news", "News", "Actualités", href=prefix + "news.html")
        + top("glossary", "Glossary", "Glossaire", href=prefix + "glossary.html")
        + "</nav>"
    )


def site_header(prefix="", active="", current="", context=""):
    """Sticky site header.

    prefix:  relative path to web/ root ("" or "../")
    active:  top-level section to underline (maps | articles | news | glossary)
    current: page path relative to web/ (e.g. "macro.html", "topics/rag-deep-dive.html")
    context: optional HTML shown after the nav (e.g. the current map title)
    """
    ctx = f'<div class="sh-context">{context}</div>' if context else ""
    return f"""<header class="site-header">
  <div class="sh-inner">
    <a href="{prefix}index.html" class="sh-logo" title="Mind Map IA">{LOGO_SVG}<span>Mind Map IA</span></a>
    {build_nav(prefix, active, current)}
    {ctx}
    <div class="sh-right">
      {gs_widget(prefix + 'search-index.json')}
      <div class="lang-toggle" role="group" aria-label="Language">
        <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
        <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
      </div>
      <button class="icon-btn theme-btn" onclick="mmiaToggleTheme()" title="Light / dark" aria-label="Toggle dark mode">
        <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>
        <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      </button>
      <button class="icon-btn sh-burger" onclick="document.body.classList.toggle('sh-menu-open')" aria-label="Menu">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
    </div>
  </div>
</header>"""


def site_footer(prefix=""):
    return f"""<footer class="site-footer">
  <div class="sf-inner">
    <span>{_bi("Mind Map IA · Open source, built to learn and share", "Mind Map IA · Open source, construit pour apprendre et partager")}</span>
    <div class="sf-links">
      <a href="{prefix}index.html#maps">{_bi("Maps", "Cartes")}</a>
      <a href="{prefix}index.html#articles">{_bi("Articles", "Articles")}</a>
      <a href="{prefix}news.html">{_bi("News", "Actualités")}</a>
      <a href="{prefix}glossary.html">{_bi("Glossary", "Glossaire")}</a>
      <a href="https://github.com/evausesgit/mind-map-ia" target="_blank" rel="noopener">GitHub ↗</a>
    </div>
  </div>
</footer>"""


CHROME_JS = r"""
<script>
(function () {
  // Dropdowns: click to toggle (touch + keyboard); hover handled in CSS on desktop.
  document.querySelectorAll('.sh-group > .sh-link').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var g = btn.parentElement, open = !g.classList.contains('open');
      document.querySelectorAll('.sh-group.open').forEach(function (o) { o.classList.remove('open'); });
      g.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.sh-group')) document.querySelectorAll('.sh-group.open').forEach(function (o) { o.classList.remove('open'); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.sh-group.open').forEach(function (o) { o.classList.remove('open'); });
      document.body.classList.remove('sh-menu-open');
    }
  });

  // Theme
  window.mmiaToggleTheme = function () {
    var dark = document.documentElement.getAttribute('data-theme') !== 'dark';
    if (dark) document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
    try { localStorage.setItem('mmia-theme', dark ? 'dark' : 'light'); } catch (e) {}
    window.dispatchEvent(new CustomEvent('mmia-themechange', { detail: { dark: dark } }));
  };

  // Language memory: wrap the page's setLang, then restore the saved choice.
  if (typeof window.setLang === 'function') {
    var pageSetLang = window.setLang;
    window.setLang = function (l) {
      try { localStorage.setItem('mmia-lang', l); } catch (e) {}
      document.documentElement.lang = l;
      var r = pageSetLang.apply(this, arguments);
      document.querySelectorAll('.site-header [data-en], .site-footer [data-en]').forEach(function (el) {
        el.textContent = l === 'fr' ? (el.dataset.fr || el.dataset.en) : el.dataset.en;
      });
      document.querySelectorAll('.lang-btn').forEach(function (b) { b.classList.toggle('active', b.dataset.lang === l); });
      return r;
    };
    var saved = null;
    try { saved = localStorage.getItem('mmia-lang'); } catch (e) {}
    if (!saved) saved = (navigator.language || '').toLowerCase().indexOf('fr') === 0 ? 'fr' : 'en';
    if (saved !== 'en') window.setLang(saved);
  }
})();
</script>"""


def chrome_script():
    return CHROME_JS
