#!/usr/bin/env python3
"""Generate quantization memory visual page.
Usage: python scripts/generate_quantization_visual.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import head_assets, site_header, site_footer, chrome_script

ROOT = Path(__file__).parent.parent
OUTPUT_FILE = ROOT / "web" / "quantization.html"


FORMATS = [
    # (id, label, bits, memory GB, radius, callout y, anchor x, use EN, use FR)
    ("fp32", "FP32", 32, 280, 200, 90, 370,
     "Training reference — rarely used for inference",
     "Référence entraînement — rarement utilisé pour l'inférence"),
    ("bf16", "BF16", 16, 140, 141, 145, 335,
     "Standard inference today — half the size of FP32, minimal quality loss",
     "Inférence standard aujourd'hui — moitié de FP32, perte de qualité minimale"),
    ("fp8", "FP8 / INT8", 8, 70, 100, 195, 309,
     "Optimized inference — faster on modern GPUs (H100), near-BF16 quality",
     "Inférence optimisée — rapide sur GPUs modernes (H100), qualité proche BF16"),
    ("int4", "INT4", 4, 35, 71, 245, 272,
     "Aggressive compression — fits on consumer hardware (GPTQ, AWQ, GGUF)",
     "Compression agressive — tient sur matériel grand public (GPTQ, AWQ, GGUF)"),
]


def generate_html():
    # SVG radii — area proportional to memory size
    # FP32=280GB → r=200 | BF16=140GB → r≈141 | FP8=70GB → r=100 | INT4=35GB → r≈71
    # center = 210,210, viewBox = 560×420 (callouts on the right)
    rings, callouts, legend = "", "", ""
    for fid, label, bits, gb, r, cy, ax, use_en, use_fr in FORMATS:
        rings += (
            f'<circle class="ring q-{fid}" cx="210" cy="210" r="{r}" '
            f'data-f="{fid}" onmouseenter="qFocus(\'{fid}\')" onmouseleave="qFocus(null)"/>'
        )
        callouts += (
            f'<g class="callout" data-f="{fid}">'
            f'<circle cx="{ax}" cy="{cy}" r="3.5" class="dot q-{fid}"/>'
            f'<line x1="{ax}" y1="{cy}" x2="428" y2="{cy}" class="lead"/>'
            f'<text x="436" y="{cy - 2}" class="c-fmt">{label}</text>'
            f'<text x="436" y="{cy + 13}" class="c-mem">~{gb} GB · {bits} bits</text>'
            f'</g>'
        )
        legend += f"""
      <div class="row" data-f="{fid}" onmouseenter="qFocus('{fid}')" onmouseleave="qFocus(null)">
        <span class="sw q-{fid}"></span>
        <div class="fmt">{label}<span class="bits">{bits} bits</span></div>
        <div class="mem">~{gb}<span> GB</span></div>
        <p data-en="{use_en}" data-fr="{use_fr}">{use_en}</p>
      </div>"""

    header_html = site_header(active="maps", current=OUTPUT_FILE.name)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Quantization — Mind Map IA</title>
{head_assets()}
<style>
  :root {{
    --q-fp32: #B5361F; --q-bf16: #D8432E; --q-fp8: #E9826F; --q-int4: #F2B3A6;
  }}
  :root[data-theme="dark"] {{
    --q-fp32: #FF9C8A; --q-bf16: #F0644E; --q-fp8: #B8483A; --q-int4: #7A3329;
  }}
  body {{ font-size: 16px; line-height: 1.6; }}
  .wrap {{
    max-width: 1080px; margin: 0 auto;
    padding: 0 max(20px, env(safe-area-inset-right, 0px)) 88px max(20px, env(safe-area-inset-left, 0px));
  }}
  .q-hero {{ padding-block: 56px 32px; display: grid; gap: 14px; }}
  .q-hero h1 {{ margin: 0; font-size: clamp(32px, 4.5vw, 46px); font-weight: 600; letter-spacing: -0.03em; line-height: 1.06; text-wrap: balance; }}
  .q-hero p {{ margin: 0; font-family: var(--f-read); font-size: 20px; color: var(--ink-2); max-width: 34em; }}

  .visual {{
    display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 48px; align-items: center;
    padding: clamp(20px, 4vw, 40px);
    background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
  }}
  .visual svg {{ width: 100%; height: auto; display: block; overflow: visible; }}
  .ring {{ fill-opacity: .16; stroke-width: 1.5; transition: fill-opacity .2s, opacity .2s; }}
  .q-fp32 {{ fill: var(--q-fp32); stroke: var(--q-fp32); background: var(--q-fp32); }}
  .q-bf16 {{ fill: var(--q-bf16); stroke: var(--q-bf16); background: var(--q-bf16); }}
  .q-fp8  {{ fill: var(--q-fp8);  stroke: var(--q-fp8);  background: var(--q-fp8); }}
  .q-int4 {{ fill: var(--q-int4); stroke: var(--q-int4); background: var(--q-int4); }}
  .dot {{ fill-opacity: 1; }}
  .lead {{ stroke: var(--line-strong); stroke-width: 1; stroke-dasharray: 3 3; }}
  .c-fmt {{ font: 600 13px var(--f-ui); fill: var(--ink); }}
  .c-mem {{ font: 11px var(--f-mono); fill: var(--muted); }}
  .center-1 {{ font: 600 14px var(--f-ui); fill: var(--ink); }}
  .center-2 {{ font: 11px var(--f-mono); fill: var(--muted); }}
  .visual.focus .ring, .visual.focus .callout {{ opacity: .3; }}
  .visual.focus .ring.on {{ opacity: 1; fill-opacity: .32; }}
  .visual.focus .callout.on {{ opacity: 1; }}

  .legend {{ display: grid; }}
  .row {{
    display: grid; grid-template-columns: 12px minmax(0, 1fr) auto; gap: 2px 14px; align-items: baseline;
    padding-block: 14px; border-bottom: 1px solid var(--line); cursor: default;
    transition: opacity .2s;
  }}
  .row:first-child {{ border-top: 1px solid var(--line); }}
  .sw {{ width: 12px; height: 12px; border-radius: 3px; align-self: center; }}
  .fmt {{ font-weight: 600; font-size: 16px; display: flex; gap: 10px; align-items: baseline; }}
  .bits {{ font: 12px var(--f-mono); color: var(--muted); font-weight: 400; }}
  .mem {{ font-size: 22px; font-weight: 600; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }}
  .mem span {{ font-size: 13px; color: var(--muted); font-weight: 500; }}
  .row p {{ grid-column: 2 / -1; margin: 0; font-size: 14px; color: var(--ink-2); line-height: 1.5; }}
  .visual.focus .row {{ opacity: .4; }}
  .visual.focus .row.on {{ opacity: 1; }}

  .tradeoff {{
    margin-top: 28px; max-width: 760px;
    padding: 4px 0 4px 20px; border-left: 2px solid var(--accent);
    font-family: var(--f-read); font-size: 18px; color: var(--ink-2); line-height: 1.6;
  }}
  .tradeoff strong {{ color: var(--ink); font-weight: 600; }}
  @media (max-width: 820px) {{
    .visual {{ grid-template-columns: minmax(0, 1fr); gap: 24px; }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<main class="wrap">
  <section class="q-hero">
    <div class="eyebrow" data-en="Diagram · 70B parameters reference" data-fr="Diagramme · référence 70B paramètres">Diagram · 70B parameters reference</div>
    <h1 data-en="Memory footprint by numerical format" data-fr="Empreinte mémoire par format numérique">Memory footprint by numerical format</h1>
    <p data-en="Same model, different memory — depending on the numerical precision used to store the parameters. Circle area is proportional to memory."
       data-fr="Même modèle, mémoire différente — selon la précision numérique utilisée pour stocker les paramètres. La surface des cercles est proportionnelle à la mémoire.">Same model, different memory — depending on the numerical precision used to store the parameters. Circle area is proportional to memory.</p>
  </section>

  <div class="visual" id="visual">
    <svg viewBox="0 0 560 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Concentric circles: FP32 280 GB, BF16 140 GB, FP8 70 GB, INT4 35 GB">
      {rings}
      {callouts}
      <text x="210" y="206" text-anchor="middle" class="center-1"><tspan data-en="70B model" data-fr="Modèle 70B">70B model</tspan></text>
      <text x="210" y="222" text-anchor="middle" class="center-2"><tspan data-en="same weights" data-fr="mêmes poids">same weights</tspan></text>
    </svg>
    <div class="legend">{legend}
    </div>
  </div>

  <p class="tradeoff">
    <strong data-en="Trade-off:" data-fr="Trade-off :">Trade-off:</strong>
    <span data-en=" less memory means lower numerical precision — but the quality loss is often negligible in practice for inference. Modern quantization methods (AWQ, GPTQ) are optimized to preserve the most important weights."
          data-fr=" moins de mémoire signifie moins de précision numérique — mais la perte de qualité est souvent négligeable en pratique pour l'inférence. Les méthodes modernes (AWQ, GPTQ) sont optimisées pour préserver les poids les plus importants."> less memory means lower numerical precision — but the quality loss is often negligible in practice for inference. Modern quantization methods (AWQ, GPTQ) are optimized to preserve the most important weights.</span>
  </p>
</main>

{site_footer()}

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

function qFocus(f) {{
  const v = document.getElementById('visual');
  v.classList.toggle('focus', !!f);
  v.querySelectorAll('[data-f]').forEach(el => el.classList.toggle('on', el.dataset.f === f));
}}
</script>
{chrome_script()}
</body>
</html>"""
    return html


def main():
    html = generate_html()
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    print(f"✓ Generated {OUTPUT_FILE}")



if __name__ == "__main__":
    main()
