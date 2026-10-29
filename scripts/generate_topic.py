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
from site_chrome import head_assets, site_header, site_footer, chrome_script

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


def generate_html(topic, maps, topics=None, links=None):
    tid = topic["id"]
    title_en = t(topic.get("title", ""), "en")
    title_fr = t(topic.get("title", ""), "fr") or title_en
    summary_en = t(topic.get("summary", ""), "en")
    summary_fr = t(topic.get("summary", ""), "fr") or summary_en
    tags = topic.get("tags", [])
    status = topic.get("status", "draft")
    date = str(topic.get("date", ""))
    is_reflexion = topic.get("category") == "reflexion"

    content_en_md = topic["content_en"]
    content_fr_md = topic["content_fr"] or content_en_md

    content_en_html = md_to_html(content_en_md)
    content_fr_html = md_to_html(content_fr_md)

    toc_en = build_toc(content_en_md)
    toc_fr = build_toc(content_fr_md)

    minutes = max(2, round(len(re.findall(r"\w+", content_en_md)) / 220))
    tags_html = "".join(f'<span class="tag">{tag}</span>' for tag in tags)
    kind_en, kind_fr = ("Reflection", "Réflexion") if is_reflexion else ("Deep dive", "Article de fond")
    header_html = site_header(prefix="../", active="articles", current=f"topics/{tid}.html")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title_en} — Mind Map IA</title>
<meta name="description" content="{summary_en.replace('"', '&quot;')}">
{head_assets()}
<style>
  body {{ font-size: 16px; line-height: 1.6; }}
  .page-layout {{
    display: grid;
    grid-template-columns: 200px minmax(0, 680px) minmax(0, 1fr);
    gap: 56px;
    max-width: 1240px;
    margin: 0 auto;
    padding: 64px max(20px, env(safe-area-inset-right, 0px)) 96px max(20px, env(safe-area-inset-left, 0px));
  }}
  main {{ min-width: 0; grid-column: 2; }}

  .article-header {{ margin-bottom: 40px; padding-bottom: 28px; border-bottom: 1px solid var(--line); }}
  .crumb {{
    display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center;
    font: 12px var(--f-mono); color: var(--muted);
  }}
  .crumb a {{ color: var(--muted); text-decoration: none; }}
  .crumb a:hover {{ color: var(--accent); }}
  .article-title {{
    font-family: var(--f-read);
    font-size: clamp(34px, 5vw, 52px);
    font-weight: 500;
    line-height: 1.06;
    letter-spacing: -0.02em;
    margin: 18px 0 16px;
    text-wrap: balance;
  }}
  .article-summary {{
    font-family: var(--f-read);
    font-size: 21px;
    color: var(--ink-2);
    line-height: 1.45;
    margin: 0 0 22px;
  }}
  .article-meta {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
  .tags {{ display: contents; }}
  .tag {{
    font: 12px var(--f-mono); color: var(--muted);
  }}
  .tag::before {{ content: "#"; opacity: .6; }}

  .article-body {{ color: var(--ink); }}
  .article-body > :first-child {{ margin-top: 0; }}
  .article-body h2 {{
    font-size: 24px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.25;
    margin: 52px 0 14px;
    scroll-margin-top: calc(var(--header-h) + 24px);
    text-wrap: balance;
  }}
  .article-body h3 {{
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.01em;
    margin: 32px 0 10px;
    scroll-margin-top: calc(var(--header-h) + 24px);
  }}
  .article-body h4 {{
    font: 500 12px var(--f-mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin: 26px 0 8px;
  }}
  .article-body p, .article-body li {{
    font-family: var(--f-read);
    font-size: 19px;
    line-height: 1.68;
  }}
  .article-body p {{ margin: 0 0 18px; }}
  .article-body ul, .article-body ol {{ margin: 0 0 20px; padding-left: 24px; }}
  .article-body li {{ margin-bottom: 6px; }}
  .article-body li::marker {{ color: var(--muted); }}
  .article-body strong {{ font-weight: 600; }}
  .article-body em {{ color: var(--ink-2); }}
  .article-body code {{
    font-family: var(--f-mono);
    font-size: 0.82em;
    background: var(--sunk);
    padding: 2px 6px;
    border-radius: 5px;
    color: var(--ink);
  }}
  .article-body pre {{
    background: var(--sunk);
    color: var(--ink);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 20px 22px;
    overflow-x: auto;
    margin: 24px 0;
    font-size: 14px;
    line-height: 1.6;
  }}
  .article-body pre code {{ background: none; padding: 0; font-size: inherit; border-radius: 0; }}
  .article-body .table-wrap, .article-body table {{ max-width: 100%; }}
  .article-body table {{
    display: block;
    overflow-x: auto;
    border-collapse: collapse;
    margin: 24px 0;
    font-size: 14.5px;
    line-height: 1.5;
  }}
  .article-body th {{
    font: 500 11.5px var(--f-mono);
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--muted);
    text-align: left;
    padding: 10px 16px 10px 0;
    border-bottom: 1px solid var(--line-strong);
    white-space: nowrap;
  }}
  .article-body td {{
    padding: 12px 16px 12px 0;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }}
  .article-body blockquote {{
    margin: 28px 0;
    padding: 4px 0 4px 22px;
    border-left: 2px solid var(--accent);
    color: var(--ink-2);
  }}
  .article-body blockquote p {{ font-size: 21px; font-style: italic; }}
  .article-body hr {{ border: none; border-top: 1px solid var(--line); margin: 40px 0; }}
  .article-body a {{
    color: var(--ink);
    text-decoration: underline;
    text-decoration-color: var(--accent);
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }}
  .article-body a:hover {{ color: var(--accent); }}
  .article-body img {{ max-width: 100%; border-radius: 12px; }}
  .article-body .mermaid {{
    margin: 28px 0; padding: 24px; overflow-x: auto;
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    text-align: center;
  }}

  /* Sidebar */
  .sidebar {{ grid-column: 1; grid-row: 1; position: sticky; top: calc(var(--header-h) + 32px); align-self: start; max-height: calc(100vh - var(--header-h) - 64px); overflow-y: auto; }}
  .toc {{ display: flex; flex-direction: column; gap: 2px; }}
  .toc-label {{
    font: 500 11px var(--f-mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 12px;
  }}
  .toc a {{
    font-size: 13.5px;
    color: var(--muted);
    text-decoration: none;
    padding: 4px 0 4px 12px;
    border-left: 1px solid var(--line);
    line-height: 1.4;
    transition: color .15s, border-color .15s;
  }}
  .toc a.toc-h3 {{ padding-left: 24px; font-size: 12.5px; }}
  .toc a:hover {{ color: var(--ink); }}
  .toc a.on {{ color: var(--ink); border-left-color: var(--accent); }}

  .article-end {{
    margin-top: 56px; padding-top: 24px; border-top: 1px solid var(--line);
    display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; align-items: center;
    font-size: 14px; color: var(--muted);
  }}
  .article-end a {{ color: var(--ink); text-decoration: none; font-weight: 500; }}
  .article-end a:hover {{ color: var(--accent); }}

  @media (max-width: 1100px) {{
    .page-layout {{ grid-template-columns: 180px minmax(0, 1fr); gap: 40px; }}
  }}
  @media (max-width: 820px) {{
    .page-layout {{ grid-template-columns: minmax(0, 1fr); padding-top: 36px; gap: 0; }}
    main {{ grid-column: 1; }}
    .sidebar {{ display: none; }}
    .article-summary {{ font-size: 18px; }}
    .article-body p, .article-body li {{ font-size: 18px; }}
    .article-body h2 {{ font-size: 21px; margin-top: 40px; }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<div class="page-layout">
  <main>
    <div class="article-header">
      <div class="crumb">
        <a href="../index.html#articles" data-en="Articles" data-fr="Articles">Articles</a><span>/</span>
        <span data-en="{kind_en}" data-fr="{kind_fr}">{kind_en}</span>
        {f'<span>·</span><time datetime="{date}">{date}</time>' if date else ''}
        <span>·</span><span>{minutes} min</span>
      </div>
      <h1 class="article-title" data-en="{title_en}" data-fr="{title_fr}">{title_en}</h1>
      <p class="article-summary" data-en="{summary_en}" data-fr="{summary_fr}">{summary_en}</p>
      <div class="article-meta">
        <span class="chip dot st-{status}">{status}</span>
        <div class="tags">{tags_html}</div>
      </div>
    </div>

    <div class="article-body" id="article-body">
      {content_en_html}
    </div>

    <div class="article-end">
      <a href="../index.html#articles" data-en="← All articles" data-fr="← Tous les articles">← All articles</a>
      <a href="../glossary.html" data-en="Glossary →" data-fr="Glossaire →">Glossary →</a>
    </div>
  </main>

  <aside class="sidebar">
    <div class="toc-label" data-en="On this page" data-fr="Sur cette page">On this page</div>
    <nav class="toc" id="toc-nav">
      {toc_en}
    </nav>
  </aside>
</div>

{site_footer("../")}

<script src="../mermaid.min.js"></script>
<script>
function mermaidTheme() {{
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'neutral';
}}
mermaid.initialize({{ startOnLoad: false, theme: mermaidTheme(), securityLevel: 'loose', fontFamily: 'Geist, system-ui, sans-serif' }});

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

function watchToc() {{
  const links = [...document.querySelectorAll('#toc-nav a')];
  const heads = links.map(a => document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)))).filter(Boolean);
  if (!heads.length || !('IntersectionObserver' in window)) return;
  if (window._tocObs) window._tocObs.disconnect();
  window._tocObs = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      if (!e.isIntersecting) return;
      links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
    }});
  }}, {{ rootMargin: '-80px 0px -70% 0px' }});
  heads.forEach(h => window._tocObs.observe(h));
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
  watchToc();
}}

window.addEventListener('mmia-themechange', () => {{
  mermaid.initialize({{ startOnLoad: false, theme: mermaidTheme(), securityLevel: 'loose', fontFamily: 'Geist, system-ui, sans-serif' }});
  document.getElementById('article-body').innerHTML = CONTENT[lang] || CONTENT.en;
  renderMermaid();
  watchToc();
}});

document.addEventListener('DOMContentLoaded', () => {{ renderMermaid(); watchToc(); }});
</script>
{chrome_script()}
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

    all_topics = [parse_topic(p) for p in topic_files]
    all_topics.sort(key=lambda x: str(x.get("date", "")), reverse=True)

    generated = []
    errors = []
    for topic in all_topics:
        try:
            html = generate_html(topic, maps, topics=all_topics, links=links)
            out_path = OUTPUT_DIR / f"{topic['id']}.html"
            out_path.write_text(html, encoding="utf-8")
            generated.append((topic["id"], t(topic.get("title", ""), "en")))
            print(f"  ✓ {out_path.relative_to(ROOT)}")
        except Exception as e:
            errors.append((topic.get("id", "?"), str(e)))
            print(f"  ✗ {topic.get('id', '?')}: {e}")

    print(f"\n{len(generated)} topic(s) generated → web/topics/")
    if errors:
        print(f"{len(errors)} error(s):")
        for name, err in errors:
            print(f"  - {name}: {err}")


if __name__ == "__main__":
    main()
