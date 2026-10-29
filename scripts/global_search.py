"""Global search widget — injected into every generated page."""


def widget_html(index_path: str) -> str:
    """Return the complete HTML/CSS/JS for the global search widget.

    index_path: relative path from the page to search-index.json
                e.g. 'search-index.json' for root pages,
                     '../search-index.json' for topics/
    """
    return f"""
<!-- ── Global Search Widget ── -->
<style>
#gs-trigger {{
  display: inline-flex; align-items: center; gap: 8px;
  height: 34px; padding: 0 8px 0 10px; border-radius: 9px; min-width: 220px;
  background: var(--bg, #FAFAF8); border: 1px solid var(--line, #E6E6E2);
  color: var(--muted, #7A7D85); font: 13px var(--f-ui, system-ui); cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}}
#gs-trigger:hover {{ border-color: var(--line-strong, #ccc); color: var(--ink, #17181C); }}
#gs-trigger .gs-placeholder {{ flex: 1; text-align: left; white-space: nowrap; }}
#gs-trigger .gs-kbd {{
  font: 11px var(--f-mono, monospace); color: var(--muted, #7A7D85);
  border: 1px solid var(--line, #E6E6E2); padding: 1px 5px; border-radius: 5px; white-space: nowrap;
}}
#gs-overlay {{
  display: none; position: fixed; inset: 0; z-index: 9999;
  background: color-mix(in srgb, var(--ink, #17181C) 28%, transparent); backdrop-filter: blur(3px);
  align-items: flex-start; justify-content: center; padding: 12vh 16px 16px;
}}
#gs-overlay.open {{ display: flex; }}
#gs-modal {{
  width: 100%; max-width: 640px; background: var(--surface, #fff);
  border: 1px solid var(--line, #E6E6E2); border-radius: 16px;
  box-shadow: var(--shadow, 0 24px 64px rgba(0,0,0,0.2)); overflow: hidden;
  font-family: var(--f-ui, system-ui);
}}
#gs-input-wrap {{
  display: flex; align-items: center; gap: 10px; color: var(--muted, #7A7D85);
  padding: 16px 18px; border-bottom: 1px solid var(--line, #E6E6E2);
}}
#gs-input-wrap svg {{ flex-shrink: 0; }}
#gs-input {{
  flex: 1; min-width: 0; background: none; border: none; outline: none;
  color: var(--ink, #17181C); font: 17px var(--f-ui, system-ui);
}}
#gs-input::placeholder {{ color: var(--muted, #999); }}
#gs-esc {{
  font: 11px var(--f-mono, monospace); color: var(--muted, #7A7D85);
  border: 1px solid var(--line, #E6E6E2); padding: 2px 7px; border-radius: 5px; cursor: pointer;
  white-space: nowrap;
}}
#gs-results {{
  max-height: min(440px, 60vh); overflow-y: auto; padding: 6px;
}}
#gs-results:empty::after {{
  content: ''; display: block;
}}
.gs-empty {{ padding: 24px; text-align: center; color: var(--muted, #7A7D85); font-size: 14px; }}
.gs-section {{ padding: 10px 12px 4px; font: 500 11px var(--f-mono, monospace);
  letter-spacing: 0.08em; color: var(--muted, #7A7D85); text-transform: uppercase; }}
.gs-item {{
  display: flex; align-items: flex-start; gap: 12px;
  padding: 10px 12px; border-radius: 10px; cursor: pointer; transition: background 0.1s;
}}
.gs-item:hover, .gs-item.active {{ background: var(--sunk, #F3F3F0); }}
.gs-dot {{
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 7px;
}}
.gs-body {{ flex: 1; min-width: 0; }}
.gs-label {{ font-size: 14px; font-weight: 500; color: var(--ink, #17181C); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }}
.gs-meta {{ font: 11px var(--f-mono, monospace); color: var(--muted, #7A7D85); margin-top: 2px; }}
.gs-excerpt {{ font-size: 12.5px; color: var(--ink-2, #45474E); margin-top: 3px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.gs-badge {{
  font: 10px var(--f-mono, monospace); padding: 2px 7px; border-radius: 99px;
  border: 1px solid var(--line, #E6E6E2); color: var(--muted, #7A7D85); white-space: nowrap;
  align-self: center; flex-shrink: 0;
}}
</style>

<button id="gs-trigger" onclick="gsOpen()" title="Global search (⌘K)">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
  <span class="gs-placeholder">Search everywhere…</span>
  <span class="gs-kbd">⌘K</span>
</button>

<div id="gs-overlay" onclick="gsOverlayClick(event)">
  <div id="gs-modal">
    <div id="gs-input-wrap">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input id="gs-input" placeholder="Search all maps, glossary, articles…"
             oninput="gsSearch(this.value)" autocomplete="off" spellcheck="false">
      <span id="gs-esc" onclick="gsClose()">Esc</span>
    </div>
    <div id="gs-results"></div>
  </div>
</div>

<script>
(function() {{
  const INDEX_PATH = '{index_path}';
  let gsData = null, gsActive = -1, gsItems = [];

  async function gsLoad() {{
    if (gsData) return;
    try {{
      const r = await fetch(INDEX_PATH);
      gsData = await r.json();
    }} catch(e) {{
      console.warn('Global search: could not load index', e);
      gsData = {{ nodes: [], glossary: [], terms: [], topics: [] }};
    }}
  }}

  window.gsOpen = function() {{
    document.getElementById('gs-overlay').classList.add('open');
    document.getElementById('gs-input').focus();
    gsLoad();
  }};

  window.gsClose = function() {{
    document.getElementById('gs-overlay').classList.remove('open');
    gsActive = -1;
  }};

  window.gsOverlayClick = function(e) {{
    if (e.target === document.getElementById('gs-overlay')) gsClose();
  }};

  function currentLang() {{
    return (typeof lang !== 'undefined' ? lang : null) ||
           document.querySelector('.lang-btn.active')?.dataset?.lang || 'en';
  }}

  function excerpt(text, q) {{
    if (!text) return '';
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i === -1) return text.slice(0, 80) + (text.length > 80 ? '…' : '');
    const s = Math.max(0, i - 20), e = Math.min(text.length, i + q.length + 50);
    return (s > 0 ? '…' : '') + text.slice(s, e) + (e < text.length ? '…' : '');
  }}

  function matches(fields, q) {{
    return fields.some(f => f && f.toLowerCase().includes(q));
  }}

  window.gsSearch = async function(raw) {{
    await gsLoad();
    const q = raw.toLowerCase().trim();
    const el = document.getElementById('gs-results');
    gsActive = -1; gsItems = [];
    if (!q) {{ el.innerHTML = ''; return; }}
    const l = currentLang();

    const nodeHits = gsData.nodes.filter(n =>
      matches([n.label_en, n.label_fr, n.description_en, n.description_fr, n.category], q)
    ).slice(0, 6);

    const glossHits = gsData.glossary.filter(g =>
      matches([g.label_en, g.label_fr, g.description_en, g.description_fr, ...(g.aliases||[])], q)
    ).slice(0, 4);

    const topicHits = gsData.topics.filter(t =>
      matches([t.title_en, t.title_fr, t.summary_en, t.summary_fr, ...(t.tags||[])], q)
    ).slice(0, 4);

    if (!nodeHits.length && !glossHits.length && !topicHits.length) {{
      el.innerHTML = `<div class="gs-empty">${{l === 'fr' ? 'Aucun résultat' : 'No results'}}</div>`;
      return;
    }}

    let html = '';
    const CAT_COLORS = {{
      org:'#58D68D', provider:'#58D68D', model:'#D5F5E3', model_family:'#A9CCE3',
      persona:'#9B59B6', usecase:'#1ABC9C', pattern:'#E67E22', component:'#3498DB',
      stage:'#58D68D', tool:'#85C1E9', block:'#F4D03F', framework:'#85C1E9',
      default:'#7f8c8d'
    }};

    function color(cat) {{ return CAT_COLORS[cat] || CAT_COLORS.default; }}

    if (nodeHits.length) {{
      html += `<div class="gs-section">${{l==='fr'?'Cartes':'Maps'}}</div>`;
      nodeHits.forEach(n => {{
        const label = (l==='fr'?n.label_fr:n.label_en) || n.label_en;
        const desc  = (l==='fr'?n.description_fr:n.description_en) || n.description_en;
        const map   = (l==='fr'?n.map_title_fr:n.map_title_en) || n.map_id;
        gsItems.push({{ url: n.map_url + '#' + n.id, label }});
        html += `<div class="gs-item" data-url="${{n.map_url}}#${{n.id}}" onclick="gsGo(this)">
          <div class="gs-dot" style="background:${{color(n.category)}}"></div>
          <div class="gs-body">
            <div class="gs-label">${{label}}</div>
            <div class="gs-excerpt">${{excerpt(desc, raw)}}</div>
          </div>
          <span class="gs-badge">${{map}}</span>
        </div>`;
      }});
    }}

    if (glossHits.length) {{
      html += `<div class="gs-section">${{l==='fr'?'Glossaire':'Glossary'}}</div>`;
      glossHits.forEach(g => {{
        const label = (l==='fr'?g.label_fr:g.label_en) || g.label_en;
        const desc  = (l==='fr'?g.description_fr:g.description_en) || g.description_en;
        const glossUrl = INDEX_PATH.replace('search-index.json','') + 'glossary.html#' + g.id;
        gsItems.push({{ url: glossUrl, label }});
        html += `<div class="gs-item" data-url="${{glossUrl}}" onclick="gsGo(this)">
          <div class="gs-dot" style="background:var(--muted)"></div>
          <div class="gs-body">
            <div class="gs-label">${{label}}</div>
            <div class="gs-excerpt">${{excerpt(desc, raw)}}</div>
          </div>
          <span class="gs-badge">Glossary</span>
        </div>`;
      }});
    }}

    if (topicHits.length) {{
      html += `<div class="gs-section">${{l==='fr'?'Articles':'Articles'}}</div>`;
      topicHits.forEach(tp => {{
        const label = (l==='fr'?tp.title_fr:tp.title_en) || tp.title_en;
        const desc  = (l==='fr'?tp.summary_fr:tp.summary_en) || tp.summary_en;
        const tUrl  = INDEX_PATH.replace('search-index.json','') + tp.url;
        gsItems.push({{ url: tUrl, label }});
        html += `<div class="gs-item" data-url="${{tUrl}}" onclick="gsGo(this)">
          <div class="gs-dot" style="background:var(--accent)"></div>
          <div class="gs-body">
            <div class="gs-label">${{label}}</div>
            <div class="gs-excerpt">${{excerpt(desc, raw)}}</div>
          </div>
          <span class="gs-badge">Article</span>
        </div>`;
      }});
    }}

    el.innerHTML = html;
  }};

  window.gsGo = function(el) {{
    const url = el.dataset.url;
    const hashIdx = url.indexOf('#');
    // If navigating to a hash on the same page, force hashchange even if hash is identical
    if (hashIdx !== -1) {{
      const page = url.slice(0, hashIdx) || location.pathname;
      const samePage = location.pathname.endsWith(page) || page === location.pathname;
      if (samePage) {{
        const newHash = url.slice(hashIdx);
        if (location.hash === newHash) {{
          // Same hash — dispatch manually since browser won't fire hashchange
          window.dispatchEvent(new HashChangeEvent('hashchange'));
        }} else {{
          location.hash = newHash;
        }}
        gsClose();
        return;
      }}
    }}
    window.location.href = url;
    gsClose();
  }};

  // Keyboard navigation
  document.addEventListener('keydown', e => {{
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
      e.preventDefault(); gsOpen(); return;
    }}
    if (!document.getElementById('gs-overlay').classList.contains('open')) return;
    if (e.key === 'Escape') {{ gsClose(); return; }}
    const items = document.querySelectorAll('.gs-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      gsActive = Math.min(gsActive + 1, items.length - 1);
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      gsActive = Math.max(gsActive - 1, 0);
    }} else if (e.key === 'Enter' && gsActive >= 0) {{
      e.preventDefault();
      items[gsActive].click(); return;
    }}
    items.forEach((el, i) => el.classList.toggle('active', i === gsActive));
    if (gsActive >= 0) items[gsActive].scrollIntoView({{block:'nearest'}});
  }});
}})();
</script>
"""
