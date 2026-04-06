# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A static site generator that produces interactive, bilingual (EN/FR) mind maps and educational pages about the LLM/AI ecosystem. Python scripts read YAML/Markdown data files and output standalone HTML pages. Deployed to GitHub Pages.

## Commands

```bash
# Regenerate all pages (run from repo root)
python scripts/generate_home.py                                              # index.html (landing page)
python scripts/generate.py data/ecosystem-macro.yaml web/macro.html         # "Big Picture" map
python scripts/generate.py data/ecosystem.yaml web/ecosystem.html           # "Full Ecosystem" map
python scripts/generate.py data/rag-pattern.yaml web/rag-pattern.html       # RAG pattern map
python scripts/generate.py data/cloud-managed.yaml web/cloud-managed.html   # Cloud Managed AI map
python scripts/generate.py data/ai-agents.yaml web/ai-agents.html           # AI Agents map
python scripts/generate.py data/ai-coding-assistants.yaml web/ai-coding-assistants.html
python scripts/generate.py data/open-weights-models.yaml web/open-weights-models.html
python scripts/generate.py data/proprietary-models.yaml web/proprietary-models.html
python scripts/generate_mermaid.py data/dense-vs-moe.yaml web/dense-vs-moe.html  # Mermaid diagram
python scripts/generate_glossary.py                                          # web/glossary.html
python scripts/generate_topic.py                                             # web/topics/*.html
```

Only dependency: `pyyaml` (`pip install pyyaml`).

**Note:** The CI pipeline only regenerates `macro.html`, `ecosystem.html`, `dense-vs-moe.html`, `glossary.html`, and `index.html`. All other pages (topic maps, slides, topic articles) must be regenerated locally and committed.

## Architecture

```
data/
  *.yaml          → scripts/generate.py        → web/*.html       (Cytoscape.js maps)
  dense-vs-moe.yaml → scripts/generate_mermaid.py → web/dense-vs-moe.html
  glossary.yaml   → scripts/generate_glossary.py → web/glossary.html
  topics/*.md     → scripts/generate_topic.py  → web/topics/*.html
  maps.yaml       → scripts/generate_home.py   → web/index.html
```

All generated HTML files are committed to the repo and served directly via GitHub Pages.

## Data layer (`data/`)

- **`maps.yaml`** — registry of all maps (id, icon, title EN/FR, description EN/FR, output path, data source path). Referenced by all generators to build the nav.
- **`ecosystem.yaml`** — full ecosystem map (~53 nodes)
- **`ecosystem-macro.yaml`** — simplified "big picture" map (~26 nodes)
- **`rag-pattern.yaml`**, **`cloud-managed.yaml`**, **`ai-agents.yaml`**, **`ai-coding-assistants.yaml`**, **`open-weights-models.yaml`**, **`proprietary-models.yaml`** — thematic Cytoscape maps
- **`dense-vs-moe.yaml`** — Mermaid diagram (different format: describes flowchart steps, not graph nodes)
- **`glossary.yaml`** — glossary terms (id, label EN/FR, definition EN/FR, aliases, related terms)
- **`topics/*.md`** — educational articles with YAML frontmatter + bilingual Markdown content (separated by `<!-- LANG:EN -->` / `<!-- LANG:FR -->` markers)
- **`layouts/`** — JSON layout overrides (e.g. `ecosystem-macro-layout.json`) for persisting manual node positions
- **`sources/`** — raw source material (articles, notes) used to populate data, named `YYYY-MM-DD-slug.md`. Never modified by generators.

### Node schema (Cytoscape maps)

Each node has: `id`, `layer` (1–5), `category`, `label` (EN/FR), `description` (EN/FR), `status` (`stable` | `evolving` | `emerging` | `deprecated`), and optionally `link`.

## Scripts

### `scripts/generate.py` (~2100 lines)

Generates Cytoscape.js mind map pages. Key responsibilities:
- Parses YAML and builds Cytoscape.js `elements` (nodes + edges)
- Computes a **5-layer horizontal layout** (Layer 1 = Foundations on the right, Layer 5 = Dev Tools on the left). Layer 2 is split into two columns: providers (right) and models (left). Layout constants at top of file (`LAYER_X`, `NODE_SPACING_Y`, etc.)
- Generates self-contained HTML with all JS/CSS inlined (Cytoscape.js loaded from `web/cytoscape.min.js`)
- Features: bilingual toggle (EN/FR), full-text search, layer background panels, status legend, `localStorage`-based drag-and-drop persistence
- Also generates `*-slides.html` variants (presentation mode)

### `scripts/generate_mermaid.py` (~238 lines)

Generates a standalone HTML page embedding a Mermaid.js diagram from a YAML spec. Used for `dense-vs-moe.html`.

### `scripts/generate_glossary.py` (~543 lines)

Generates `web/glossary.html` from `data/glossary.yaml`. Features: alphabetical index, search, bilingual toggle, cross-links between terms.

### `scripts/generate_topic.py` (~633 lines)

Generates `web/topics/*.html` from `data/topics/*.md`. Each topic file has YAML frontmatter (id, title EN/FR, summary, tags, related_terms, related_nodes, status, date) and bilingual Markdown content.

### `scripts/generate_home.py` (~612 lines)

Reads `maps.yaml` and generates `web/index.html` — the landing page with a bilingual card grid linking to each map and topic.

## Frontend (`web/`)

- `cytoscape.min.js` — vendored Cytoscape.js asset
- `mermaid.min.js` — vendored Mermaid.js asset
- `topics/` — generated topic article pages
- All other `.html` files are generated (do not edit by hand)

## Content workflow

See `KNOWLEDGE.md` for the full content ingestion workflow (how to add new terms, nodes, or topic articles from a source).
