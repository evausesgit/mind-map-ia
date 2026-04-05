# Prompt — Bootstrapper un repo de mémoire personnelle augmentée

Copie ce prompt dans une nouvelle session Claude Code, dans le répertoire de ton nouveau repo.

---

## LE PROMPT

```
Je veux construire un système de mémoire personnelle augmentée sous forme de repo git.

Le principe est simple : je fournis des sources brutes (articles, notes, liens, tweets,
réflexions), tu les ingères, tu les structures, et le tout est rendu consultable via
un site statique généré automatiquement.

---

## Architecture cible

data/
  sources/        ← mes inputs bruts, jamais modifiés (nommés YYYY-MM-DD-slug.md)
  topics/         ← articles de fond structurés que tu écris à partir des sources
  entries/        ← entrées courtes : une idée, une citation, un fait notable
  index.yaml      ← registre de tout le contenu (généré automatiquement)

scripts/
  generate_site.py     ← génère tout le site statique
  generate_topic.py    ← markdown topic → page HTML
  generate_entry.py    ← entrée courte → fiche HTML

web/
  index.html      ← page d'accueil avec recherche
  topics/         ← pages articles
  entries/        ← fiches courtes

KNOWLEDGE.md      ← le schéma du système : ton mode d'emploi pour travailler avec moi

---

## Ce que je veux pouvoir faire

1. **Ingérer une source** : je te donne un texte, une URL, un screenshot, des notes
   brutes — tu identifies ce qu'on peut en tirer et tu proposes quoi créer.

2. **Poser une question** : tu lis ce qui existe dans data/ et tu synthétises une réponse.
   Si la réponse est bonne, on en fait une nouvelle entrée.

3. **Explorer des connexions** : tu identifies des liens entre des topics/entrées existants
   que je n'aurais pas vus.

4. **Faire évoluer le schéma** : si mes besoins changent, on adapte ensemble la structure.

---

## Différence avec une simple prise de notes

- Les sources restent brutes et intactes dans data/sources/
- Toi tu fais le travail de structuration, reformulation, cross-linking
- Tout est versionné dans git → historique complet
- Le site généré est navigable, cherchable, partageable
- Je peux retrouver n'importe quelle connaissance par recherche full-text ou par thème

---

## Première chose à faire

Commence par créer KNOWLEDGE.md avec :
1. Le contexte de ce repo (ce que c'est, à quoi ça sert)
2. Mon profil (ce que tu sais de moi, ma façon de penser, mes domaines d'intérêt)
3. Le workflow d'ingestion step by step
4. Le format exact de chaque type de fichier (source, topic, entry)
5. Les règles de décision : quand créer un topic vs une entry vs juste enrichir l'existant
6. Ce que tu dois toujours faire après chaque session (log, mise à jour de l'index)

Demande-moi ce qu'il manque avant de commencer.
```

---

## Ce qui différencie ce système d'une prise de notes classique

| Notion / Obsidian | Ce système |
|---|---|
| Tu structures toi-même | Claude structure pour toi |
| Tu retrouves ce que tu as écrit | Claude synthétise et connecte |
| Format figé | Format évolue avec tes besoins |
| Siloed dans l'app | Git → versionné, portable, déployable |
| Recherche full-text basique | Recherche + navigation thématique générée |

## Variations possibles selon l'usage

**Mémoire professionnelle** — veille techno, comptes-rendus de réunions, décisions prises et pourquoi  
**Journal de pensées** — réflexions, lectures, citations, questions ouvertes  
**Base de connaissances domaine** — comme ce repo mais sur n'importe quel sujet  
**Portfolio de projets** — historique de tes projets, leçons apprises, patterns récurrents  

Le prompt ci-dessus fonctionne pour tous ces cas — change juste le contexte dans KNOWLEDGE.md.
