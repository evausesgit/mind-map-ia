#!/usr/bin/env python3
"""Generate quantization memory visual page.
Usage: python scripts/generate_quantization_visual.py
"""

import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_FILE = ROOT / "data" / "maps.yaml"
OUTPUT_FILE = ROOT / "web" / "quantization.html"


def t(field, lang):
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field) if field else ""


def build_nav(maps, current_output):
    items = ""
    current_name = Path(current_output).name
    for m in maps:
        active = "active" if m.get("output") == current_name else ""
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
        '<a href="index.html#news" class="nav-btn" style="text-decoration:none;padding:5px 11px;border:1.5px solid #333;border-radius:6px;color:#BDC3C7;font-size:13px;font-weight:600;">'
        '  <span data-en="News" data-fr="Nouveautés">News</span>'
        '</a>'
    )


def generate_html(maps):
    nav_html = build_nav(maps, str(OUTPUT_FILE))

    # SVG radii — area proportional to memory size
    # FP32=280GB → r=200 | BF16=140GB → r≈141 | FP8=70GB → r=100 | INT4=35GB → r≈71
    # center = 210,210, viewBox = 420×420

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title data-en="Memory by Format — Quantization" data-fr="Mémoire par Format — Quantisation">Memory by Format — Quantization</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0D1117;
    color: #E6EDF3;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }}

  /* ── Header ── */
  header {{
    background: #161B22;
    border-bottom: 1px solid #21262D;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-shrink: 0;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  header h1 {{ font-size: 17px; font-weight: 700; color: #E6EDF3; }}
  .meta {{ font-size: 11px; color: #6E7681; margin-top: 2px; }}

  /* ── Nav (same pattern as site) ── */
  .nav-menu {{ position: relative; }}
  .nav-btn {{
    padding: 6px 14px; border: 1.5px solid #30363D; border-radius: 8px;
    background: transparent; color: #BDC3C7; font-size: 13px;
    font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap;
  }}
  .nav-btn:hover {{ border-color: #8B949E; color: white; }}
  .nav-dropdown {{
    position: absolute; top: calc(100% + 6px); left: 0; min-width: 260px;
    background: #161B22; border: 1px solid #21262D; border-radius: 10px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6); z-index: 1000; display: none;
  }}
  .nav-menu:hover .nav-dropdown,
  .nav-menu:focus-within .nav-dropdown {{ display: block; }}
  .nav-dropdown a {{
    display: flex; align-items: center; gap: 12px; padding: 10px 14px;
    border-bottom: 1px solid #21262D; text-decoration: none;
    color: #BDC3C7; font-size: 13px; transition: background 0.1s;
  }}
  .nav-dropdown a:last-child {{ border-bottom: none; }}
  .nav-dropdown a:hover {{ background: #21262D; color: white; }}
  .nav-dropdown a.active {{ color: white; background: #21262D; }}
  .nav-dropdown .nav-icon {{ font-size: 17px; }}
  .nav-dropdown .nav-info {{ display: flex; flex-direction: column; }}
  .nav-dropdown .nav-title {{ font-weight: 600; }}
  .nav-dropdown .nav-desc {{ font-size: 11px; color: #6E7681; margin-top: 1px; }}
  .nav-home {{ color: #BDC3C7 !important; font-size: 13px !important; border-bottom: 1px solid #21262D !important; }}
  .nav-home:hover {{ color: #FF6B6B !important; }}
  .lang-toggle {{ display: flex; gap: 6px; }}
  .lang-btn {{
    background: none; border: 1px solid #30363D; border-radius: 4px;
    color: #8B949E; padding: 4px 10px; font-size: 13px; cursor: pointer; transition: all 0.15s;
  }}
  .lang-btn.active {{ background: #E6EDF3; color: #0D1117; border-color: #E6EDF3; font-weight: 600; }}

  /* ── Page layout ── */
  main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 24px 64px;
    gap: 12px;
  }}

  .page-title {{
    font-size: 28px;
    font-weight: 800;
    color: #E6EDF3;
    text-align: center;
    letter-spacing: -0.5px;
  }}

  .page-subtitle {{
    font-size: 15px;
    color: #8B949E;
    text-align: center;
    max-width: 520px;
    line-height: 1.5;
  }}

  /* ── Main visual block ── */
  .visual-block {{
    display: flex;
    align-items: center;
    gap: 56px;
    margin-top: 24px;
    width: 100%;
    max-width: 900px;
  }}

  /* ── SVG container ── */
  .svg-wrap {{
    flex: 0 0 auto;
    width: 420px;
    height: 420px;
    position: relative;
  }}

  .svg-wrap svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}

  /* circle hover glow */
  .mem-ring {{
    transition: filter 0.25s, opacity 0.25s;
    cursor: default;
  }}
  .mem-ring:hover {{
    filter: drop-shadow(0 0 12px var(--glow));
    opacity: 1 !important;
  }}

  /* ── Legend / right panel ── */
  .legend {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-width: 0;
  }}

  .legend-item {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 16px 18px;
    border-radius: 10px;
    border: 1px solid #21262D;
    background: #161B22;
    transition: border-color 0.2s, background 0.2s;
    cursor: default;
  }}
  .legend-item:hover {{
    border-color: var(--accent);
    background: #1C2128;
  }}

  .legend-dot {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 3px;
    box-shadow: 0 0 8px var(--accent);
  }}

  .legend-body {{ display: flex; flex-direction: column; gap: 3px; }}

  .legend-format {{
    font-size: 15px;
    font-weight: 700;
    color: #E6EDF3;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .legend-bits {{
    font-size: 12px;
    font-weight: 500;
    color: #6E7681;
    background: #21262D;
    padding: 1px 7px;
    border-radius: 4px;
  }}

  .legend-mem {{
    font-size: 20px;
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
  }}

  .legend-use {{
    font-size: 12px;
    color: #6E7681;
    margin-top: 1px;
  }}

  /* ── Trade-off note ── */
  .tradeoff {{
    max-width: 900px;
    width: 100%;
    padding: 14px 20px;
    border-radius: 8px;
    border-left: 3px solid #388BFD;
    background: #161B22;
    font-size: 13px;
    color: #8B949E;
    line-height: 1.6;
  }}
  .tradeoff strong {{ color: #E6EDF3; }}

  /* ── Responsive ── */
  @media (max-width: 760px) {{
    .visual-block {{
      flex-direction: column;
      align-items: center;
      gap: 32px;
    }}
    .svg-wrap {{
      width: 300px;
      height: 300px;
    }}
    .legend {{
      width: 100%;
    }}
    .page-title {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

<header>
  <div style="display:flex;align-items:center;gap:16px;">
    {nav_html}
    <div>
      <h1 id="main-title">
        <span data-en="Memory by Format" data-fr="Mémoire par Format">Memory by Format</span>
      </h1>
      <div class="meta">
        <span data-en="Model quantization · 70B parameters reference"
              data-fr="Quantisation du modèle · référence 70B paramètres">
          Model quantization · 70B parameters reference
        </span>
      </div>
    </div>
  </div>
  <div class="lang-toggle">
    <button class="lang-btn active" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="lang-btn" data-lang="fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<main>

  <h2 class="page-title">
    <span data-en="Memory footprint by numerical format"
          data-fr="Empreinte mémoire par format numérique">
      Memory footprint by numerical format
    </span>
  </h2>

  <p class="page-subtitle">
    <span data-en="Same model, different memory — depending on the numerical precision used to store the parameters."
          data-fr="Même modèle, mémoire différente — selon la précision numérique utilisée pour stocker les paramètres.">
      Same model, different memory — depending on the numerical precision used to store the parameters.
    </span>
  </p>

  <div class="visual-block">

    <!-- SVG: concentric circles, area ∝ memory -->
    <!-- radii: FP32=200 BF16=141 FP8/INT8=100 INT4=71  center=210,210 -->
    <div class="svg-wrap">
      <svg viewBox="0 0 420 420" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <radialGradient id="gFP32" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#E74C3C" stop-opacity="0.08"/>
            <stop offset="100%" stop-color="#E74C3C" stop-opacity="0.22"/>
          </radialGradient>
          <radialGradient id="gBF16" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#E67E22" stop-opacity="0.08"/>
            <stop offset="100%" stop-color="#E67E22" stop-opacity="0.28"/>
          </radialGradient>
          <radialGradient id="gFP8" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#1ABC9C" stop-opacity="0.1"/>
            <stop offset="100%" stop-color="#1ABC9C" stop-opacity="0.32"/>
          </radialGradient>
          <radialGradient id="gINT4" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#3498DB" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="#3498DB" stop-opacity="0.42"/>
          </radialGradient>
          <filter id="glow-red">
            <feGaussianBlur stdDeviation="4" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>

        <!-- FP32 — r=200 -->
        <circle class="mem-ring" style="--glow:#E74C3C" cx="210" cy="210" r="200"
          fill="url(#gFP32)" stroke="#E74C3C" stroke-width="2.5" opacity="0.85"/>

        <!-- BF16 — r=141 -->
        <circle class="mem-ring" style="--glow:#E67E22" cx="210" cy="210" r="141"
          fill="url(#gBF16)" stroke="#E67E22" stroke-width="2.5" opacity="0.9"/>

        <!-- FP8 / INT8 — r=100 -->
        <circle class="mem-ring" style="--glow:#1ABC9C" cx="210" cy="210" r="100"
          fill="url(#gFP8)" stroke="#1ABC9C" stroke-width="2.5" opacity="0.9"/>

        <!-- INT4 — r=71 -->
        <circle class="mem-ring" style="--glow:#3498DB" cx="210" cy="210" r="71"
          fill="url(#gINT4)" stroke="#3498DB" stroke-width="2.5"/>

        <!-- Labels on rings -->
        <!-- FP32 label — top of ring -->
        <text x="210" y="16" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="13" font-weight="700" fill="#E74C3C">FP32</text>
        <text x="210" y="30" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="11" fill="#E74C3C" opacity="0.8">~280 GB</text>

        <!-- BF16 label — top-right of ring -->
        <text x="330" y="88" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="12" font-weight="700" fill="#E67E22">BF16</text>
        <text x="330" y="102" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="11" fill="#E67E22" opacity="0.8">~140 GB</text>

        <!-- FP8 label — right of ring -->
        <text x="324" y="196" text-anchor="start" font-family="-apple-system,sans-serif"
              font-size="12" font-weight="700" fill="#1ABC9C">FP8 / INT8</text>
        <text x="324" y="210" text-anchor="start" font-family="-apple-system,sans-serif"
              font-size="11" fill="#1ABC9C" opacity="0.8">~70 GB</text>

        <!-- INT4 label — right of ring -->
        <text x="286" y="248" text-anchor="start" font-family="-apple-system,sans-serif"
              font-size="12" font-weight="700" fill="#3498DB">INT4</text>
        <text x="286" y="262" text-anchor="start" font-family="-apple-system,sans-serif"
              font-size="11" fill="#3498DB" opacity="0.8">~35 GB</text>

        <!-- Center label -->
        <text x="210" y="205" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="13" font-weight="800" fill="#E6EDF3" opacity="0.9">
          <tspan data-en="70B model" data-fr="Modèle 70B">70B model</tspan>
        </text>
        <text x="210" y="222" text-anchor="middle" font-family="-apple-system,sans-serif"
              font-size="10" fill="#8B949E">
          <tspan data-en="same weights" data-fr="mêmes poids">same weights</tspan>
        </text>
      </svg>
    </div>

    <!-- Legend -->
    <div class="legend">

      <div class="legend-item" style="--accent:#E74C3C;">
        <div class="legend-dot" style="background:#E74C3C;--accent:#E74C3C;"></div>
        <div class="legend-body">
          <div class="legend-format">
            FP32 <span class="legend-bits">32 bits / value</span>
          </div>
          <div class="legend-mem">~280 GB</div>
          <div class="legend-use">
            <span data-en="Training reference — rarely used for inference"
                  data-fr="Référence entraînement — rarement utilisé pour l'inférence">
              Training reference — rarely used for inference
            </span>
          </div>
        </div>
      </div>

      <div class="legend-item" style="--accent:#E67E22;">
        <div class="legend-dot" style="background:#E67E22;--accent:#E67E22;"></div>
        <div class="legend-body">
          <div class="legend-format">
            BF16 <span class="legend-bits">16 bits / value</span>
          </div>
          <div class="legend-mem">~140 GB</div>
          <div class="legend-use">
            <span data-en="Standard inference today — half the size of FP32, minimal quality loss"
                  data-fr="Inférence standard aujourd'hui — moitié de FP32, perte de qualité minimale">
              Standard inference today — half the size of FP32, minimal quality loss
            </span>
          </div>
        </div>
      </div>

      <div class="legend-item" style="--accent:#1ABC9C;">
        <div class="legend-dot" style="background:#1ABC9C;--accent:#1ABC9C;"></div>
        <div class="legend-body">
          <div class="legend-format">
            FP8 / INT8 <span class="legend-bits">8 bits / value</span>
          </div>
          <div class="legend-mem">~70 GB</div>
          <div class="legend-use">
            <span data-en="Optimized inference — faster on modern GPUs (H100), near-BF16 quality"
                  data-fr="Inférence optimisée — rapide sur GPUs modernes (H100), qualité proche BF16">
              Optimized inference — faster on modern GPUs (H100), near-BF16 quality
            </span>
          </div>
        </div>
      </div>

      <div class="legend-item" style="--accent:#3498DB;">
        <div class="legend-dot" style="background:#3498DB;--accent:#3498DB;"></div>
        <div class="legend-body">
          <div class="legend-format">
            INT4 <span class="legend-bits">4 bits / value</span>
          </div>
          <div class="legend-mem">~35 GB</div>
          <div class="legend-use">
            <span data-en="Aggressive compression — fits on consumer hardware (GPTQ, AWQ, GGUF)"
                  data-fr="Compression agressive — tient sur matériel grand public (GPTQ, AWQ, GGUF)">
              Aggressive compression — fits on consumer hardware (GPTQ, AWQ, GGUF)
            </span>
          </div>
        </div>
      </div>

    </div>
  </div>

  <div class="tradeoff">
    <strong>
      <span data-en="Trade-off:" data-fr="Trade-off :">Trade-off:</span>
    </strong>
    <span data-en=" less memory means lower numerical precision — but the quality loss is often negligible in practice for inference. Modern quantization methods (AWQ, GPTQ) are optimized to preserve the most important weights."
          data-fr=" moins de mémoire signifie moins de précision numérique — mais la perte de qualité est souvent négligeable en pratique pour l'inférence. Les méthodes modernes (AWQ, GPTQ) sont optimisées pour préserver les poids les plus importants.">
      less memory means lower numerical precision — but the quality loss is often negligible in practice for inference. Modern quantization methods (AWQ, GPTQ) are optimized to preserve the most important weights.
    </span>
  </div>

</main>

<script>
let lang = 'en';

function setLang(newLang) {{
  lang = newLang;
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
}}
</script>
</body>
</html>"""
    return html


def main():
    with open(MAPS_FILE) as f:
        maps_config = yaml.safe_load(f)
    maps = maps_config.get("maps", [])

    html = generate_html(maps)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
