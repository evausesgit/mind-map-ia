#!/usr/bin/env python3
"""Generate web/topics/*.html from data/topics/*.md

Each topic file is a markdown file with YAML frontmatter and bilingual content
separated by <!-- LANG:EN --> and <!-- LANG:FR --> markers.

Usage:
    python scripts/generate_topic.py
"""

import re
import yaml
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from global_search import widget_html as gs_widget

ROOT = Path(__file__).parent.parent
TOPICS_DIR = ROOT / "data" / "topics"
MAPS_FILE = ROOT / "data" / "maps.yaml"
OUTPUT_DIR = ROOT / "web" / "topics"


# ── Markdown → HTML ───────────────────────────────────────────────────────────

def md_to_html(text):
    """Convert markdown text to HTML. Handles the common subset used in topic files."""
    lines = text.strip().split("\n")
    html_parts = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        code_match = re.match(r"^```(\w*)", line)
        if code_match:
            lang = code_match.group(1)
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            raw_code = "\n".join(code_lines)
            if lang == "mermaid":
                html_parts.append(f'<div class="mermaid">{raw_code}</div>')
            else:
                code = raw_code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                lang_class = f' class="language-{lang}"' if lang else ""
                html_parts.append(f'<pre><code{lang_class}>{code}</code></pre>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            html_parts.append("<hr>")
            i += 1
            continue

        # Table
        if "|" in line and i + 1 < len(lines) and re.match(r"^\|[-| :]+\|", lines[i + 1]):
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            html_parts.append(_parse_table(table_lines))
            continue

        # Headings
        h_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if h_match:
            level = len(h_match.group(1))
            content = inline_md(h_match.group(2))
            slug = re.sub(r"[^\w\s-]", "", h_match.group(2).lower()).strip()
            slug = re.sub(r"[\s]+", "-", slug)
            html_parts.append(f'<h{level} id="{slug}">{content}</h{level}>')
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            inner = md_to_html("\n".join(quote_lines))
            html_parts.append(f"<blockquote>{inner}</blockquote>")
            continue

        # Unordered list
        if re.match(r"^[-*]\s", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s", lines[i]):
                items.append(f"<li>{inline_md(lines[i][2:].strip())}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                content = re.sub(r"^\d+\.\s", "", lines[i]).strip()
                items.append(f"<li>{inline_md(content)}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue

        # Empty line — skip
        if not line.strip():
            i += 1
            continue

        # Paragraph — collect consecutive non-blank, non-structural lines
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_structural(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            html_parts.append(f'<p>{inline_md(" ".join(para_lines))}</p>')

    return "\n".join(html_parts)


def _is_structural(line):
    return (
        re.match(r"^#{1,4}\s", line)
        or re.match(r"^```", line)
        or re.match(r"^[-*]\s", line)
        or re.match(r"^\d+\.\s", line)
        or re.match(r"^---+$", line.strip())
        or line.startswith("> ")
        or ("|" in line)
    )


def _parse_table(table_lines):
    rows = []
    for j, row in enumerate(table_lines):
        if re.match(r"^\|[-| :]+\|", row):
            continue  # separator row
        cells = [c.strip() for c in row.strip("|").split("|")]
        tag = "th" if j == 0 else "td"
        cells_html = "".join(f"<{tag}>{inline_md(c)}</{tag}>" for c in cells)
        rows.append(f"<tr>{cells_html}</tr>")
    header = rows[0] if rows else ""
    body = "".join(rows[1:])
    return f'<table><thead>{header}</thead><tbody>{body}</tbody></table>'


def inline_md(text):
    """Process inline markdown: bold, italic, inline code, links."""
    # Escape HTML first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Inline code (before bold/italic to avoid conflicts)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Links
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


# ── Topic file parsing ────────────────────────────────────────────────────────

def parse_topic(path):
    """Parse a topic .md file. Returns dict with frontmatter + en/fr content."""
    raw = path.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if not fm_match:
        raise ValueError(f"No frontmatter found in {path}")
    frontmatter = yaml.safe_load(fm_match.group(1))
    body = raw[fm_match.end():]

    # Split by language markers
    en_match = re.search(r"<!--\s*LANG:EN\s*-->(.+?)(?=<!--\s*LANG:|$)", body, re.DOTALL)
    fr_match = re.search(r"<!--\s*LANG:FR\s*-->(.+?)(?=<!--\s*LANG:|$)", body, re.DOTALL)

    return {
        **frontmatter,
        "content_en": en_match.group(1).strip() if en_match else "",
        "content_fr": fr_match.group(1).strip() if fr_match else "",
    }


def build_toc(content_md):
    """Extract headings and build a table of contents as HTML."""
    headings = re.findall(r"^(#{2,3})\s+(.+)", content_md, re.MULTILINE)
    if not headings:
        return ""
    items = []
    for hashes, text in headings:
        level = len(hashes)
        slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
        slug = re.sub(r"\s+", "-", slug)
        indent = "toc-h3" if level == 3 else "toc-h2"
        items.append(f'<a href="#{slug}" class="{indent}">{text}</a>')
    return '<nav class="toc">' + "\n".join(items) + "</nav>"


# ── Nav menu ──────────────────────────────────────────────────────────────────

def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def build_nav(maps, topic_id, links=None):
    items = ""
    for m in maps:
        title_en = t(m.get("title", ""), "en")
        title_fr = t(m.get("title", ""), "fr") or title_en
        desc_en = t(m.get("description", ""), "en")
        desc_fr = t(m.get("description", ""), "fr") or desc_en
        items += (
            f'<a href="../{m["output"]}">'
            f'  <span class="nav-icon">{m.get("icon", "📄")}</span>'
            f'  <span class="nav-info">'
            f'    <span class="nav-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'    <span class="nav-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'  </span>'
            f'</a>'
        )
    link_items = ""
    for link in (links or []):
        title_en = t(link.get("title", ""), "en")
        title_fr = t(link.get("title", ""), "fr") or title_en
        desc_en = t(link.get("description", ""), "en")
        desc_fr = t(link.get("description", ""), "fr") or desc_en
        url = link.get("url", "")
        link_items += (
            f'<a href="{url}" target="_blank" rel="noopener">'
            f'  <span class="nav-icon">{link.get("icon", "🔗")}</span>'
            f'  <span class="nav-info">'
            f'    <span class="nav-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</span>'
            f'    <span class="nav-desc" data-en="{desc_en}" data-fr="{desc_fr}">{desc_en}</span>'
            f'  </span>'
            f'</a>'
        )
    nav = (
        '<div class="nav-menu">'
        '  <button class="nav-btn">≡ Maps ▾</button>'
        '  <div class="nav-dropdown">'
        '    <a href="../index.html" class="nav-home">← Home</a>'
        f'   {items}'
        '  </div>'
        '</div>'
    )
    if link_items:
        nav += (
            '<div class="nav-menu">'
            '  <button class="nav-btn">'
            '    <span data-en="Links" data-fr="Liens">Links</span> ▾'
            '  </button>'
            '  <div class="nav-dropdown">'
            f'   {link_items}'
            '  </div>'
            '</div>'
        )
    nav += (
        '<a href="../index.html#news" class="nav-btn" style="text-decoration:none;padding:5px 11px;border:1.5px solid #333;border-radius:6px;color:#BDC3C7;font-size:13px;font-weight:600;">'
        '  <span data-en="News" data-fr="Nouveautés">News</span>'
        '</a>'
    )
    return nav


# ── HTML generation ───────────────────────────────────────────────────────────

def generate_html(topic, maps, links=None):
    tid = topic["id"]
    title_en = t(topic.get("title", ""), "en")
    title_fr = t(topic.get("title", ""), "fr") or title_en
    summary_en = t(topic.get("summary", ""), "en")
    summary_fr = t(topic.get("summary", ""), "fr") or summary_en
    tags = topic.get("tags", [])
    status = topic.get("status", "draft")
    date = str(topic.get("date", ""))

    content_en_md = topic["content_en"]
    content_fr_md = topic["content_fr"] or content_en_md

    content_en_html = md_to_html(content_en_md)
    content_fr_html = md_to_html(content_fr_md)

    toc_en = build_toc(content_en_md)
    toc_fr = build_toc(content_fr_md)

    nav_html = build_nav(maps, tid, links=links)
    tags_html = "".join(f'<span class="tag">{tag}</span>' for tag in tags)

    status_colors = {
        "stable": "#27AE60",
        "draft":  "#E67E22",
        "review": "#3498DB",
    }
    status_color = status_colors.get(status, "#7F8C8D")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
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
    position: sticky;
    top: 0;
    z-index: 100;
  }}
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
  .nav-dropdown a .nav-icon {{ font-size: 18px; }}
  .nav-dropdown a .nav-info {{ display: flex; flex-direction: column; }}
  .nav-dropdown a .nav-title {{ font-weight: 600; }}
  .nav-dropdown a .nav-desc {{ font-size: 11px; color: #7F8C8D; margin-top: 1px; }}
  .nav-home {{ color: #BDC3C7 !important; font-size: 13px !important; border-bottom: 1px solid #1E2D4E; }}
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

  .page-layout {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 32px;
    display: grid;
    grid-template-columns: 1fr 220px;
    gap: 48px;
    align-items: start;
  }}
  @media (max-width: 768px) {{
    .page-layout {{ grid-template-columns: 1fr; }}
    .sidebar {{ display: none; }}
  }}

  .article-header {{ margin-bottom: 32px; }}
  .article-meta {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }}
  .status-badge {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    background: {status_color}22;
    color: {status_color};
    border: 1px solid {status_color}44;
  }}
  .date {{ font-size: 12px; color: #95A5A6; }}
  .article-title {{
    font-size: clamp(24px, 4vw, 36px);
    font-weight: 800;
    line-height: 1.2;
    color: #1A1A2E;
    margin-bottom: 12px;
  }}
  .article-summary {{
    font-size: 16px;
    color: #555;
    line-height: 1.6;
    margin-bottom: 16px;
  }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .tag {{
    font-size: 11px;
    padding: 2px 8px;
    background: #E8EAF6;
    color: #3F51B5;
    border-radius: 4px;
    font-weight: 600;
    letter-spacing: 0.3px;
  }}

  .article-body {{ line-height: 1.75; color: #2C3E50; }}
  .article-body h2 {{
    font-size: 22px;
    font-weight: 700;
    color: #1A1A2E;
    margin: 36px 0 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #E8EAED;
  }}
  .article-body h3 {{
    font-size: 17px;
    font-weight: 700;
    color: #1A1A2E;
    margin: 24px 0 8px;
  }}
  .article-body h4 {{
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #7F8C8D;
    margin: 20px 0 6px;
  }}
  .article-body p {{ margin-bottom: 14px; font-size: 15px; }}
  .article-body ul, .article-body ol {{
    margin: 8px 0 14px 20px;
    font-size: 15px;
  }}
  .article-body li {{ margin-bottom: 4px; }}
  .article-body strong {{ font-weight: 700; color: #1A1A2E; }}
  .article-body em {{ color: #555; }}
  .article-body code {{
    font-family: "SF Mono", "Fira Code", Consolas, monospace;
    font-size: 13px;
    background: #EEF0F3;
    padding: 1px 5px;
    border-radius: 3px;
    color: #C0392B;
  }}
  .article-body pre {{
    background: #1A1A2E;
    color: #E8EAF6;
    border-radius: 8px;
    padding: 20px;
    overflow-x: auto;
    margin: 16px 0;
    font-size: 13px;
    line-height: 1.6;
  }}
  .article-body pre code {{
    background: none;
    color: inherit;
    padding: 0;
    font-size: inherit;
    border-radius: 0;
  }}
  .article-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }}
  .article-body th {{
    background: #1A1A2E;
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
  }}
  .article-body td {{
    padding: 8px 14px;
    border-bottom: 1px solid #E8EAED;
  }}
  .article-body tr:nth-child(even) td {{ background: #F8F9FA; }}
  .article-body blockquote {{
    border-left: 3px solid #1A1A2E;
    padding: 8px 16px;
    margin: 12px 0;
    color: #555;
    background: #F0F0F5;
    border-radius: 0 4px 4px 0;
  }}
  .article-body hr {{
    border: none;
    border-top: 1px solid #E0E0E0;
    margin: 28px 0;
  }}
  .article-body a {{ color: #1A1A2E; font-weight: 600; text-underline-offset: 2px; }}
  .article-body a:hover {{ color: #3498DB; }}

  /* Sidebar */
  .sidebar {{ position: sticky; top: 80px; }}
  .toc {{ display: flex; flex-direction: column; gap: 4px; }}
  .toc-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #95A5A6;
    margin-bottom: 8px;
  }}
  .toc a {{
    font-size: 13px;
    color: #555;
    text-decoration: none;
    padding: 3px 0;
    border-left: 2px solid transparent;
    padding-left: 10px;
    line-height: 1.4;
    transition: all 0.1s;
  }}
  .toc a.toc-h3 {{
    padding-left: 20px;
    font-size: 12px;
    color: #7F8C8D;
  }}
  .toc a:hover {{ color: #1A1A2E; border-left-color: #1A1A2E; }}
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    {nav_html}
  </div>
  {gs_widget('../search-index.json')}
  <div class="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<div class="page-layout">
  <main>
    <div class="article-header">
      <div class="article-meta">
        <span class="status-badge">{status}</span>
        {f'<span class="date">{date}</span>' if date else ''}
      </div>
      <h1 class="article-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</h1>
      <p class="article-summary" data-en="{summary_en}" data-fr="{summary_fr}">{summary_en}</p>
      <div class="tags">{tags_html}</div>
    </div>

    <div class="article-body" id="article-body">
      {content_en_html}
    </div>
  </main>

  <aside class="sidebar">
    <div class="toc-label" data-en="On this page" data-fr="Sur cette page">On this page</div>
    <nav class="toc" id="toc-nav">
      {toc_en}
    </nav>
  </aside>
</div>

<script src="../mermaid.min.js"></script>
<script>
mermaid.initialize({{ startOnLoad: false, theme: 'default', securityLevel: 'loose' }});

const CONTENT = {{
  en: {repr(content_en_html)},
  fr: {repr(content_fr_html)},
}};
const TOC = {{
  en: {repr(toc_en)},
  fr: {repr(toc_fr)},
}};
let lang = 'en';

function renderMermaid() {{
  mermaid.run({{ querySelector: '.mermaid' }});
}}

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.getElementById('article-body').innerHTML = CONTENT[lang] || CONTENT.en;
  document.getElementById('toc-nav').innerHTML = TOC[lang] || TOC.en;
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
  renderMermaid();
}}

document.addEventListener('DOMContentLoaded', renderMermaid);
</script>
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not TOPICS_DIR.exists():
        print(f"No topics directory found at {TOPICS_DIR}")
        return

    topic_files = sorted(TOPICS_DIR.glob("*.md"))
    if not topic_files:
        print("No topic files found.")
        return

    maps = []
    if MAPS_FILE.exists():
        with open(MAPS_FILE) as f:
            maps_config = yaml.safe_load(f)
        maps = maps_config.get("maps", [])
        links = maps_config.get("links", [])
    else:
        links = []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    errors = []
    for path in topic_files:
        try:
            topic = parse_topic(path)
            html = generate_html(topic, maps, links=links)
            out_path = OUTPUT_DIR / f"{topic['id']}.html"
            out_path.write_text(html, encoding="utf-8")
            generated.append((topic["id"], t(topic.get("title", ""), "en")))
            print(f"  ✓ {out_path.relative_to(ROOT)}")
        except Exception as e:
            errors.append((path.name, str(e)))
            print(f"  ✗ {path.name}: {e}")

    print(f"\n{len(generated)} topic(s) generated → web/topics/")
    if errors:
        print(f"{len(errors)} error(s):")
        for name, err in errors:
            print(f"  - {name}: {err}")


if __name__ == "__main__":
    main()
