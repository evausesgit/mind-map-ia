#!/usr/bin/env python3
"""Generate web/search-index.json — global search index for all maps, glossary and topics."""
import json, yaml, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
WEB  = ROOT / "web"


def t(val, lang):
    if isinstance(val, dict):
        return val.get(lang) or val.get("en") or ""
    return str(val) if val else ""


def build_index():
    with open(DATA / "maps.yaml") as f:
        maps_registry = yaml.safe_load(f)["maps"]

    nodes = []
    for m in maps_registry:
        data_path = m.get("data")
        if not data_path:
            continue
        data_file = ROOT / data_path
        if not data_file.exists():
            continue
        try:
            with open(data_file) as f:
                data = yaml.safe_load(f)
        except Exception:
            continue
        if not isinstance(data, dict) or "nodes" not in data:
            continue

        meta = data.get("meta", {})
        map_title_en = t(meta.get("title", m.get("title", {})), "en") or m["id"]
        map_title_fr = t(meta.get("title", m.get("title", {})), "fr") or map_title_en
        map_url = m["output"]

        for node in data.get("nodes", []):
            nodes.append({
                "id": node["id"],
                "label_en": t(node.get("label", ""), "en"),
                "label_fr": t(node.get("label", ""), "fr"),
                "description_en": t(node.get("description", ""), "en").strip(),
                "description_fr": t(node.get("description", ""), "fr").strip(),
                "category": node.get("category", ""),
                "status": node.get("status", ""),
                "map_id": m["id"],
                "map_title_en": map_title_en,
                "map_title_fr": map_title_fr,
                "map_url": map_url,
            })

    # Glossary
    glossary = []
    with open(DATA / "glossary.yaml") as f:
        gloss_data = yaml.safe_load(f)
    for term in gloss_data.get("terms", []):
        glossary.append({
            "id": term["id"],
            "label_en": t(term.get("label", ""), "en"),
            "label_fr": t(term.get("label", ""), "fr"),
            "description_en": t(term.get("description", ""), "en").strip(),
            "description_fr": t(term.get("description", ""), "fr").strip(),
            "aliases": term.get("aliases", []),
        })

    # Topics
    topics = []
    topics_dir = DATA / "topics"
    for md_file in sorted(topics_dir.glob("*.md")):
        text = md_file.read_text()
        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        try:
            fm = yaml.safe_load(fm_match.group(1))
        except Exception:
            continue
        tid = fm.get("id", md_file.stem)
        topics.append({
            "id": tid,
            "title_en": t(fm.get("title", ""), "en"),
            "title_fr": t(fm.get("title", ""), "fr"),
            "summary_en": t(fm.get("summary", ""), "en"),
            "summary_fr": t(fm.get("summary", ""), "fr"),
            "tags": fm.get("tags", []),
            "url": f"topics/{tid}.html",
        })

    return {"nodes": nodes, "glossary": glossary, "topics": topics}


def main():
    index = build_index()
    out = WEB / "search-index.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    n, g, tp = len(index["nodes"]), len(index["glossary"]), len(index["topics"])
    print(f"✓ {out.relative_to(ROOT)}  ({n} nodes · {g} glossary terms · {tp} topics)")


if __name__ == "__main__":
    main()
