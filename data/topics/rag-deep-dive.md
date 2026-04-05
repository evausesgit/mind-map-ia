---
id: rag-deep-dive
title:
  en: "RAG: Retrieval-Augmented Generation"
  fr: "RAG : Génération Augmentée par Récupération"
summary:
  en: "How RAG works, when to use it, and trade-offs vs fine-tuning."
  fr: "Comment fonctionne RAG, quand l'utiliser, et compromis vs fine-tuning."
tags: [rag, retrieval, embeddings, vector-db]
related_terms: [rag, embedding, vector_database, hallucination]
related_nodes: [rag_pattern, embeddings, vector_db]
status: stable
date: 2026-04-04
sources: []
---

<!-- LANG:EN -->

## What is RAG?

RAG (Retrieval-Augmented Generation) is a pattern that gives a language model access to an external knowledge base at inference time. Instead of relying solely on what was baked into its weights during training, the model first retrieves relevant documents from a database, then generates a response grounded in that retrieved context.

The key insight: **the model's knowledge and the model's reasoning are separated**. You keep knowledge in a database you control, and use the LLM for what it's actually good at — synthesis, reasoning, and language generation.

## How it works

A RAG pipeline has three stages:

1. **Indexing** (offline, done once): Split your documents into chunks, embed each chunk into a vector, store vectors in a vector database.
2. **Retrieval** (at query time): Embed the user's query, find the top-k chunks whose vectors are closest to the query vector.
3. **Generation**: Inject the retrieved chunks into the model's context window as a prompt prefix, then generate the answer.

```
User query
    ↓
[Embed query] → vector
    ↓
[Vector DB] → top-k relevant chunks
    ↓
[LLM] ← prompt = system + chunks + query
    ↓
Answer grounded in retrieved context
```

The quality of retrieval determines the quality of the answer. Garbage in, garbage out — no matter how good the LLM is.

## When to use it

RAG is the right choice when:

- Your knowledge base **changes frequently** (product docs, internal wikis, news)
- You need **citations** — answers traceable to specific source documents
- You're working with **domain-specific or proprietary information** the model wasn't trained on
- You want to **reduce hallucinations** on factual questions
- **Cost is a concern** — fine-tuning is expensive, RAG can use any base model

## Trade-offs vs fine-tuning

| | RAG | Fine-tuning |
|---|---|---|
| Knowledge update | Change the DB, no retraining | Full or partial retraining |
| Cost | Low (retrieval + inference) | High (GPU training) |
| Hallucination on facts | Lower (grounded in docs) | Higher (baked in weights) |
| Reasoning style / tone | Unchanged | Can be adapted |
| Latency | +retrieval step | Same as base model |
| Knowledge cutoff | None — DB is always current | Frozen at training time |

**Rule of thumb**: Use RAG for *what the model knows*. Use fine-tuning for *how the model behaves*.

## Failure modes to know

- **Chunking too coarsely**: relevant info gets split across chunks that aren't retrieved together
- **Chunking too finely**: chunks lose context, embeddings become noisy
- **Query-document mismatch**: user asks in a different "register" than how docs are written — semantic search struggles
- **Context window overflow**: retrieving too many chunks can push the actual question out of focus
- **Retrieval without reranking**: top-k by cosine similarity ≠ top-k by relevance to the actual question. A reranker (cross-encoder) helps.

## In practice

A minimal RAG stack looks like:

```python
# 1. Embed the query
query_vec = embedder.encode(user_query)

# 2. Retrieve top-k chunks
results = vector_db.search(query_vec, top_k=5)

# 3. Build prompt
context = "\n\n".join(r.text for r in results)
prompt = f"Use the following context to answer.\n\n{context}\n\nQuestion: {user_query}"

# 4. Generate
answer = llm.generate(prompt)
```

In production, you'll want: a reranker after retrieval, hybrid search (dense + BM25), metadata filtering, and eval on retrieval quality separately from generation quality.

<!-- LANG:FR -->

## Qu'est-ce que RAG ?

RAG (Retrieval-Augmented Generation) est un pattern qui donne au modèle de langage accès à une base de connaissance externe au moment de l'inférence. Plutôt que de s'appuyer uniquement sur ce qui a été intégré dans ses poids pendant l'entraînement, le modèle commence par récupérer des documents pertinents, puis génère une réponse ancrée dans ce contexte récupéré.

L'idée centrale : **la connaissance du modèle et son raisonnement sont séparés**. Tu gardes la connaissance dans une base que tu contrôles, et tu utilises le LLM pour ce qu'il fait vraiment bien — la synthèse, le raisonnement, et la génération de texte.

## Comment ça fonctionne

Un pipeline RAG comporte trois étapes :

1. **Indexation** (offline, fait une fois) : découper les documents en chunks, embedder chaque chunk, stocker les vecteurs dans une base vectorielle.
2. **Récupération** (au moment de la requête) : embedder la question de l'utilisateur, trouver les top-k chunks dont les vecteurs sont les plus proches.
3. **Génération** : injecter les chunks récupérés dans la fenêtre de contexte du modèle, puis générer la réponse.

```
Question utilisateur
    ↓
[Embed query] → vecteur
    ↓
[Vector DB] → top-k chunks pertinents
    ↓
[LLM] ← prompt = système + chunks + question
    ↓
Réponse ancrée dans le contexte récupéré
```

La qualité de la récupération détermine la qualité de la réponse. Peu importe la puissance du LLM — si la récupération est mauvaise, la réponse le sera aussi.

## Quand l'utiliser

RAG est le bon choix quand :

- Ta base de connaissance **change fréquemment** (docs produit, wikis internes, actualités)
- Tu as besoin de **citations** — des réponses traçables vers des documents sources précis
- Tu travailles avec des **informations spécifiques au domaine ou propriétaires** que le modèle n'a pas vues à l'entraînement
- Tu veux **réduire les hallucinations** sur les questions factuelles
- Le **coût est un critère** — le fine-tuning est cher, RAG peut utiliser n'importe quel modèle de base

## Compromis vs fine-tuning

| | RAG | Fine-tuning |
|---|---|---|
| Mise à jour des connaissances | Changer la DB, pas de ré-entraînement | Ré-entraînement complet ou partiel |
| Coût | Faible (récupération + inférence) | Élevé (entraînement GPU) |
| Hallucinations sur les faits | Plus faibles (ancré dans les docs) | Plus élevées (intégré dans les poids) |
| Style de raisonnement / ton | Inchangé | Peut être adapté |
| Latence | +étape de récupération | Identique au modèle de base |
| Cutoff des connaissances | Aucun — la DB est toujours à jour | Figé au moment de l'entraînement |

**Règle empirique** : RAG pour *ce que le modèle sait*. Fine-tuning pour *comment le modèle se comporte*.

## Modes d'échec à connaître

- **Chunks trop gros** : les informations pertinentes sont réparties sur des chunks non récupérés ensemble
- **Chunks trop petits** : les chunks perdent leur contexte, les embeddings deviennent bruités
- **Décalage requête-document** : l'utilisateur pose la question différemment de comment les docs sont rédigés — la recherche sémantique s'en sort mal
- **Débordement de la fenêtre de contexte** : trop de chunks peuvent éclipser la question elle-même
- **Récupération sans reranking** : top-k par similarité cosinus ≠ top-k par pertinence réelle. Un reranker (cross-encoder) aide.

## En pratique

Un stack RAG minimal ressemble à :

```python
# 1. Embedder la requête
query_vec = embedder.encode(user_query)

# 2. Récupérer les top-k chunks
results = vector_db.search(query_vec, top_k=5)

# 3. Construire le prompt
context = "\n\n".join(r.text for r in results)
prompt = f"Utilise le contexte suivant pour répondre.\n\n{context}\n\nQuestion : {user_query}"

# 4. Générer
answer = llm.generate(prompt)
```

En production : ajoute un reranker après la récupération, une recherche hybride (dense + BM25), du filtrage par métadonnées, et évalue la qualité de la récupération séparément de la génération.
