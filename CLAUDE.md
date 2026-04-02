# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A static site generator that produces interactive, bilingual (EN/FR) mind maps of the LLM/AI ecosystem. Python scripts read YAML data files and output standalone HTML pages with embedded Cytoscape.js graph visualizations. Deployed to GitHub Pages.

## Commands

```bash
# Regenerate all pages
python scripts/generate_home.py                                          # index.html (landing page)
python scripts/generate.py data/ecosystem-macro.yaml web/macro.html     # "Big Picture" map
python scripts/generate.py data/ecosystem.yaml web/ecosystem.html       # "Full Ecosystem" map
```

Only dependency: `pyyaml` (`pip install pyyaml`).

The CI pipeline (`.github/workflows/deploy.yml`) runs all three commands on push to `main` and deploys to GitHub Pages.

## Architecture

```
data/*.yaml  →  scripts/generate*.py  →  web/*.html  (committed + deployed)
```

### Data layer (`data/`)

- **`maps.yaml`** — registry of available maps (id, icon, title EN/FR, description EN/FR, output path, data source path)
- **`ecosystem.yaml`** — full ecosystem map (~53 nodes)
- **`ecosystem-macro.yaml`** — simplified "big picture" map (~26 nodes)

Each node in an ecosystem YAML file has: `id`, `layer` (1–5), `category`, `label` (EN/FR), `description` (EN/FR), `status` (`stable` | `evolving` | `emerging` | `deprecated`), and optionally `link`.

### Generator (`scripts/generate.py`)

Single ~1100-line script. Key responsibilities:
- Parses YAML and builds Cytoscape.js `elements` (nodes + edges)
- Computes a **5-layer horizontal layout** (Layer 1 = Foundations on the right, Layer 5 = Dev Tools on the left). Layer 2 is split into two columns: providers (right) and models (left). Layout constants live at the top of the file (`LAYER_X`, `NODE_SPACING_Y`, etc.).
- Generates a self-contained HTML string with all JS/CSS inlined (Cytoscape.js is loaded from `cytoscape.min.js` in the same `web/` directory)
- The generated HTML includes: bilingual toggle (EN/FR), full-text search, layer background panels, status legend, and `localStorage`-based drag-and-drop persistence

### Landing page generator (`scripts/generate_home.py`)

~215 lines. Reads `maps.yaml` and generates `web/index.html` with a bilingual card grid linking to each map.

### Frontend (`web/`)

Generated HTML files are standalone (no build step). `cytoscape.min.js` is a vendored asset checked into `web/`. The generated files are committed to the repo and served directly via GitHub Pages.
