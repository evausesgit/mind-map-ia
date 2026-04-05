# KNOWLEDGE.md — Schéma de la base de connaissance

## Contexte

Site éducatif sur l'écosystème LLM/IA. Cible : développeurs et professionnels tech qui veulent comprendre l'IA en profondeur.
Ton attendu : technique mais accessible, pas de flou, mental models clairs, trade-offs expliqués.

---

## Architecture des données

```
data/
  sources/          ← inputs bruts (jamais modifiés, jamais générés)
  topics/           ← articles pédagogiques structurés (EN + FR)
  glossary.yaml     ← définitions courtes de termes
  ecosystem.yaml    ← noeuds de la carte complète
  ecosystem-macro.yaml ← noeuds de la vue simplifiée

web/
  topics/           ← pages HTML générées par generate_topic.py
  glossary.html     ← généré par generate_glossary.py
  index.html        ← généré par generate_home.py
```

---

## Workflow d'ingestion

Quand l'utilisateur donne une source (article, lien, notes) :

1. **Lire** la source
2. **Identifier** ce qui peut en être extrait :
   - Nouveaux termes pour le glossaire (`glossary.yaml`)
   - Enrichissements de noeuds existants (`ecosystem.yaml` / `ecosystem-macro.yaml`)
   - Une page topic à créer (`data/topics/`)
   - Contradictions avec le contenu existant (signaler)
3. **Proposer** la liste à l'utilisateur avant d'écrire
4. **Écrire** les fichiers après validation
5. L'utilisateur régénère + push

---

## Format des sources (`data/sources/`)

Nommage : `YYYY-MM-DD-slug.md`

```markdown
# Titre de la source
Source: https://...
Date: 2026-04-04
Type: article | tweet | paper | notes

---

[Contenu collé brut — aucun formatage requis]
```

Les sources sont des inputs bruts, jamais modifiés. Elles servent de référence pour tracer l'origine des informations.

---

## Format des topic pages (`data/topics/`)

Nommage : `slug.md` (ex: `rag-deep-dive.md`, `transformers-explained.md`)

```markdown
---
id: rag-deep-dive
title:
  en: "RAG: Retrieval-Augmented Generation"
  fr: "RAG : Génération Augmentée par Récupération"
summary:
  en: "How RAG works, when to use it, and trade-offs vs fine-tuning."
  fr: "Comment fonctionne RAG, quand l'utiliser, et compromis vs fine-tuning."
tags: [rag, retrieval, embeddings, vector-db]
related_terms: [rag, embedding, vector_database]
related_nodes: [rag_pattern, embeddings]
status: draft        # draft | stable | review
date: 2026-04-04
sources:
  - data/sources/2026-04-04-article-rag.md
---

<!-- LANG:EN -->

## What is RAG?

...

## How it works

...

<!-- LANG:FR -->

## Qu'est-ce que RAG ?

...

## Comment ça fonctionne

...
```

### Sections recommandées pour un topic technique

- **What is X** / **Qu'est-ce que X** — définition courte, 2-3 phrases
- **How it works** / **Comment ça fonctionne** — le mécanisme, avec schéma si utile
- **When to use it** / **Quand l'utiliser** — cas d'usage concrets
- **Trade-offs** / **Compromis** — limites, alternatives, ce que ça ne fait pas
- **In practice** / **En pratique** — exemple de code ou de configuration si pertinent

---

## Règles de décision : glossaire vs topic

| Situation | Action |
|-----------|--------|
| Nouveau terme, 1-2 paragraphes suffisent | Entrée glossaire |
| Concept qui mérite une explication en profondeur (>3 paragraphes) | Page topic |
| Comparaison entre deux approches | Page topic |
| Tutoriel ou cas d'usage concret | Page topic |
| Correction d'une description existante | Update glossaire/noeud |

---

## Ce que je log après chaque ingestion

À la fin de chaque session d'ingestion, je liste :
- Fichiers créés ou modifiés
- Termes ajoutés au glossaire
- Topics créés
- Noeuds enrichis sur les cartes
- Questions ouvertes ou contradictions trouvées

---

## Commandes de génération

```bash
# Générer toutes les pages topic
python scripts/generate_topic.py

# Régénérer tout le site
python scripts/generate_home.py
python scripts/generate.py data/ecosystem-macro.yaml web/macro.html
python scripts/generate.py data/ecosystem.yaml web/ecosystem.html
python scripts/generate_glossary.py
python scripts/generate_topic.py
```
