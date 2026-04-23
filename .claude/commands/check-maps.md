# /check-maps

After creating or modifying a mind map, run this checklist to ensure consistency across the project.

## 1. maps.yaml — registry check

Read `data/maps.yaml`. Verify that the map being created/modified has an entry with:
- `id` matching the output filename (without `.html`)
- `title` in both `en` and `fr`
- `description` in both `en` and `fr`
- `output` pointing to the correct `web/*.html` path
- `data` pointing to the correct `data/*.yaml` path
- `nodes` count matching the actual number of nodes in the data file (run a quick count)

If the entry is missing or outdated, update `maps.yaml` and regenerate `web/index.html` with `python scripts/generate_home.py`.

## 2. Glossary — new terms check

Read `data/glossary.yaml`. For each new node added to the map, check whether its concept already has a glossary entry (search by `id` or `label`).

Flag any node whose concept is missing from the glossary. For each gap, ask Eva whether she wants to add a glossary entry — if yes, add it to `data/glossary.yaml` and regenerate with `python scripts/generate_glossary.py`.

## 3. Report

Output a short summary:
- ✅ maps.yaml: entry present and up to date / ⚠️ missing or outdated (what's wrong)
- ✅ glossary: all new terms covered / ⚠️ N terms missing (list them)
