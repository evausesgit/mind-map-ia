#!/usr/bin/env python3
"""Generate web/animations/llm-chatbot.html — the page wrapping the Manim video
"How an LLM chatbot works" (EN/FR videos switch with the language toggle).
Usage: python scripts/generate_llm_chatbot.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from site_chrome import head_assets, site_header, site_footer, chrome_script

ROOT = Path(__file__).parent.parent
OUTPUT_FILE = ROOT / "web" / "animations" / "llm-chatbot.html"

STEPS = [
    ("User input", "Message utilisateur",
     "The user types a message. The model receives raw text.",
     "L'utilisateur écrit un message. Le modèle reçoit du texte brut."),
    ("Tokenisation", "Tokenisation",
     "Text is split into sub-word tokens, each mapped to an integer ID (~100k vocabulary).",
     "Le texte est découpé en sous-mots (tokens), chacun mappé à un entier (~100k vocabulaire)."),
    ("Embeddings", "Embeddings",
     "Each token ID becomes a dense vector (768–4096 dims) + positional encoding.",
     "Chaque ID devient un vecteur dense (768–4096 dims) + encodage positionnel."),
    ("Self-attention", "Self-attention",
     "Each token attends to all others, weighting what's relevant. Repeated across N layers.",
     "Chaque token « regarde » les autres et pondère l'information. Répété sur N couches."),
    ("Generation", "Génération",
     "Output probabilities → next token selected → repeated word by word until done.",
     "Distribution de probabilités → token sélectionné → répété mot par mot jusqu'à la fin."),
]


def generate_html():
    steps_html = "".join(
        f"""
    <li class="step">
      <span class="step-num">{i:02d}</span>
      <span class="step-label" data-en="{l_en}" data-fr="{l_fr}">{l_en}</span>
      <span class="step-desc" data-en="{d_en}" data-fr="{d_fr}">{d_en}</span>
    </li>"""
        for i, (l_en, l_fr, d_en, d_fr) in enumerate(STEPS, 1)
    )
    header_html = site_header(prefix="../", active="maps", current="animations/llm-chatbot.html")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>How an LLM works — Mind Map IA</title>
{head_assets()}
<style>
  body {{ font-size: 16px; line-height: 1.6; }}
  .wrap {{
    max-width: 1080px; margin: 0 auto;
    padding: 0 max(20px, env(safe-area-inset-right, 0px)) 88px max(20px, env(safe-area-inset-left, 0px));
  }}
  .a-hero {{ padding-block: 56px 28px; display: grid; gap: 14px; }}
  .a-hero h1 {{ margin: 0; font-size: clamp(32px, 4.5vw, 46px); font-weight: 600; letter-spacing: -0.03em; line-height: 1.06; text-wrap: balance; }}
  .a-hero p {{ margin: 0; font-family: var(--f-read); font-size: 20px; color: var(--ink-2); max-width: 34em; }}
  .video-wrapper {{
    border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
    background: #000; box-shadow: var(--shadow);
  }}
  video {{ display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; }}
  .steps {{
    list-style: none; margin: 40px 0 0; padding: 0;
    display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0 24px;
  }}
  .step {{ display: grid; gap: 6px; align-content: start; padding-top: 16px; border-top: 1px solid var(--line); }}
  .step-num {{ font: 500 12px var(--f-mono); color: var(--accent); }}
  .step-label {{ font-size: 16px; font-weight: 600; letter-spacing: -0.01em; }}
  .step-desc {{ font-size: 14px; color: var(--ink-2); line-height: 1.5; }}
  .credit {{ margin-top: 40px; font: 12px var(--f-mono); color: var(--muted); }}
  @media (max-width: 860px) {{
    .steps {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px 24px; }}
  }}
  @media (max-width: 520px) {{
    .steps {{ grid-template-columns: minmax(0, 1fr); }}
  }}
</style>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>

{header_html}

<main class="wrap">
  <section class="a-hero">
    <div class="eyebrow" data-en="Animation" data-fr="Animation">Animation</div>
    <h1 data-en="How does an LLM chatbot work?" data-fr="Comment fonctionne un chatbot LLM ?">How does an LLM chatbot work?</h1>
    <p data-en="From the user's message to the generated response — an animated walkthrough of each step inside a large language model."
       data-fr="Du message de l'utilisateur à la réponse générée — un parcours animé de chaque étape à l'intérieur d'un grand modèle de langage.">From the user's message to the generated response — an animated walkthrough of each step inside a large language model.</p>
  </section>

  <div class="video-wrapper">
    <video id="main-video" controls autoplay muted loop playsinline>
      <source id="video-src" src="llm-chatbot-en.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
  </div>

  <ol class="steps">{steps_html}
  </ol>

  <p class="credit">Made with Manim &amp; Claude Code</p>
</main>

{site_footer("../")}

<script>
function setLang(lang) {{
  document.querySelectorAll('[data-en]').forEach(el => {{
    el.textContent = el.dataset[lang] || el.dataset.en;
  }});
  document.querySelectorAll('.lang-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.lang === lang)
  );
  document.documentElement.lang = lang;

  // Switch video source
  const video = document.getElementById('main-video');
  const src = document.getElementById('video-src');
  const currentTime = video.currentTime;
  src.src = lang === 'fr' ? 'llm-chatbot-fr.mp4' : 'llm-chatbot-en.mp4';
  video.load();
  video.currentTime = currentTime;
}}
</script>
{chrome_script()}
</body>
</html>"""


def main():
    OUTPUT_FILE.write_text(generate_html(), encoding="utf-8")
    print(f"✓ Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
