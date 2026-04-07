---
id: usecase-chat-qa
title:
  en: "Use Case: Q&A Chat"
  fr: "Cas d'Usage : Chat Q&R"
summary:
  en: "How a non-technical user interacts with an AI over a knowledge base — architecture, UX trade-offs, and failure modes."
  fr: "Comment un utilisateur non technique interagit avec une IA sur une base de connaissance — architecture, compromis UX, et modes d'échec."
tags: [rag, chat, qa, ux, knowledge-base]
related_terms: [rag, embedding, vector_database, hallucination, context_window]
related_nodes: [uc-chat-qa, pattern-rag, stack-llm, stack-vector-db, stack-memory]
status: stable
date: 2026-04-06
sources: []
---

<!-- LANG:EN -->

## The scenario

An end user — a customer, an employee, a citizen — opens a chat interface and asks a question in plain language. The system finds the relevant answer within a corpus (product documentation, internal policies, legal contracts, support tickets) and responds in natural language with citations.

No SQL. No boolean search operators. No reading of 50-page PDFs. Just: ask and receive.

## Architecture

This use case is almost always powered by **RAG** (Retrieval-Augmented Generation). The flow at inference time:

```
User question
    ↓
[Embed question]  →  query vector
    ↓
[Vector DB search]  →  top-k relevant document chunks
    ↓
[Build prompt]  =  system instructions + chunks + question
    ↓
[LLM]  →  grounded answer + source references
    ↓
User sees: answer + citations
```

Two things happen offline, before any user ever types a question:

1. **Ingestion**: documents are split into chunks, each chunk is embedded (converted to a vector), and stored in a vector database.
2. **Index maintenance**: when documents change, the index must be updated. Stale chunks = stale answers.

## What makes a good Q&A chat UX

From the user's perspective, the only thing that matters is **trust**. They will abandon the tool the moment they get one confident-sounding wrong answer with no way to verify it.

Three things build trust:

**1. Citations are mandatory.** Every claim should reference a specific source: document title, section, page. Users should be able to click through and verify. "According to the HR Policy v2.3, Section 4.1..." is far more trustworthy than a bare answer.

**2. "I don't know" is a feature.** When no relevant context is retrieved, the system must say so — not hallucinate. Configuring a confidence threshold below which the system falls back to "I couldn't find relevant information" is non-negotiable.

**3. The answer should be short.** Users read the first two sentences and then decide whether to dig deeper. The LLM should be prompted to give the direct answer first, then optionally expand.

## Key metrics

| Metric | What it measures | Target |
|---|---|---|
| Retrieval recall | Are relevant chunks actually retrieved? | > 85% |
| Answer faithfulness | Does the answer match retrieved chunks? | > 95% |
| Hallucination rate | Does the model invent facts not in context? | < 2% |
| User satisfaction | Do users rate answers as helpful? | > 4/5 |
| Deflection rate | Does the chat reduce human agent load? | varies |

Evaluate retrieval and generation **separately** — bad retrieval cannot be fixed by a better LLM.

## Failure modes

**Retrieval misses.** The right document exists but isn't retrieved. Usually caused by: poor chunking (breaking key sentences at chunk boundaries), embedding model mismatch (model wasn't trained on your domain), or sparse keyword coverage (the user's phrasing doesn't match the document's phrasing). Fix: hybrid search (dense vectors + BM25 keyword), reranker, query reformulation.

**Context overflow.** Retrieving too many chunks fills the context window and dilutes focus. The LLM starts averaging across chunks rather than answering the specific question. Fix: a reranker to keep only the top 3–5 truly relevant chunks.

**Cross-chunk dependencies.** The answer spans multiple sections of a document. No single chunk contains it. Fix: larger chunks with overlap, or recursive chunk expansion.

**Stale knowledge base.** Documents are updated but the index isn't. Users get outdated answers — worse than getting no answer, because they trust it. Fix: automated re-indexing on document update, TTL on chunks.

**Prompt injection.** A malicious user tries to override the system prompt via their question. Fix: input sanitization, a strict system prompt that doesn't allow instruction-following from user input.

## Typical stack

| Layer | Examples |
|---|---|
| LLM | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro |
| Embeddings | OpenAI text-embedding-3, Cohere Embed v3 |
| Vector DB | Pinecone, Weaviate, Qdrant, pgvector |
| Reranker | Cohere Rerank, BGE Reranker, Jina Reranker |
| Orchestration | LangChain, LlamaIndex, custom |
| UI | Vercel AI SDK, Streamlit, custom React |

## When to go beyond RAG

RAG is not always enough:

- **Multi-step reasoning**: "Compare our Q3 revenue across all business units and identify the outlier" → agent loop with code execution
- **Real-time data**: RAG can't retrieve live database state — use tool-calling to query a live source
- **Complex workflows**: the user wants to *act*, not just *read* → agentic assistant

<!-- LANG:FR -->

## Le scénario

Un utilisateur final — un client, un employé, un citoyen — ouvre une interface de chat et pose une question en langage naturel. Le système trouve la réponse pertinente dans un corpus (documentation produit, politiques internes, contrats légaux, tickets support) et répond en langage naturel avec des citations.

Pas de SQL. Pas d'opérateurs de recherche booléenne. Pas de lecture de PDFs de 50 pages. Juste : demander et recevoir.

## Architecture

Ce cas d'usage est presque toujours alimenté par **RAG** (Retrieval-Augmented Generation). Le flux au moment de l'inférence :

```
Question utilisateur
    ↓
[Embedder la question]  →  vecteur de requête
    ↓
[Recherche Vector DB]  →  top-k chunks de documents pertinents
    ↓
[Construire le prompt]  =  instructions système + chunks + question
    ↓
[LLM]  →  réponse ancrée + références sources
    ↓
L'utilisateur voit : réponse + citations
```

Deux choses se passent offline, avant qu'un utilisateur tape quoi que ce soit :

1. **Ingestion** : les documents sont découpés en chunks, chaque chunk est embedé (converti en vecteur), et stocké dans une base vectorielle.
2. **Maintenance de l'index** : quand les documents changent, l'index doit être mis à jour. Des chunks périmés = des réponses périmées.

## Ce qui fait un bon UX de chat Q&R

Du point de vue de l'utilisateur, la seule chose qui compte est la **confiance**. Ils abandonneront l'outil dès qu'ils obtiendront une mauvaise réponse formulée avec assurance, sans moyen de la vérifier.

Trois choses construisent la confiance :

**1. Les citations sont obligatoires.** Chaque affirmation doit référencer une source précise : titre du document, section, page. Les utilisateurs doivent pouvoir cliquer et vérifier. "Selon la Politique RH v2.3, Section 4.1..." est bien plus digne de confiance qu'une réponse nue.

**2. "Je ne sais pas" est une fonctionnalité.** Quand aucun contexte pertinent n'est récupéré, le système doit le dire — pas halluciner. Configurer un seuil de confiance en dessous duquel le système répond "Je n'ai pas trouvé d'information pertinente" est non négociable.

**3. La réponse doit être courte.** Les utilisateurs lisent les deux premières phrases puis décident de creuser. Le LLM doit être prompté pour donner la réponse directe d'abord, puis éventuellement développer.

## Métriques clés

| Métrique | Ce qu'elle mesure | Cible |
|---|---|---|
| Recall de récupération | Les chunks pertinents sont-ils récupérés ? | > 85% |
| Fidélité des réponses | La réponse correspond-elle aux chunks récupérés ? | > 95% |
| Taux d'hallucination | Le modèle invente-t-il des faits absents du contexte ? | < 2% |
| Satisfaction utilisateur | Les utilisateurs notent-ils les réponses utiles ? | > 4/5 |
| Taux de deflexion | Le chat réduit-il la charge sur les agents humains ? | variable |

Évaluer la récupération et la génération **séparément** — une mauvaise récupération ne peut pas être corrigée par un meilleur LLM.

## Modes d'échec

**Ratés de récupération.** Le bon document existe mais n'est pas récupéré. Causes : mauvais chunking (coupure des phrases clés aux frontières de chunks), inadéquation du modèle d'embedding (le modèle n'a pas été entraîné sur votre domaine), ou couverture de mots-clés insuffisante (la formulation de l'utilisateur ne correspond pas à celle du document). Correction : recherche hybride (vecteurs denses + BM25), reranker, reformulation de requête.

**Débordement de contexte.** Récupérer trop de chunks remplit la fenêtre de contexte et dilue le focus. Le LLM commence à moyenner sur les chunks plutôt qu'à répondre à la question spécifique. Correction : un reranker pour ne garder que les 3–5 chunks vraiment pertinents.

**Dépendances inter-chunks.** La réponse s'étend sur plusieurs sections d'un document. Aucun chunk ne la contient seul. Correction : chunks plus larges avec chevauchement, ou expansion récursive de chunks.

**Base de connaissance périmée.** Les documents sont mis à jour mais l'index ne l'est pas. Les utilisateurs obtiennent des réponses obsolètes — pire que pas de réponse, car ils lui font confiance. Correction : réindexation automatisée à la mise à jour des documents, TTL sur les chunks.

**Injection de prompt.** Un utilisateur malveillant tente de contourner le prompt système via sa question. Correction : sanitisation des entrées, prompt système strict qui ne permet pas de suivre des instructions depuis les entrées utilisateur.

## Stack typique

| Couche | Exemples |
|---|---|
| LLM | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro |
| Embeddings | OpenAI text-embedding-3, Cohere Embed v3 |
| Vector DB | Pinecone, Weaviate, Qdrant, pgvector |
| Reranker | Cohere Rerank, BGE Reranker, Jina Reranker |
| Orchestration | LangChain, LlamaIndex, custom |
| UI | Vercel AI SDK, Streamlit, React custom |

## Quand aller au-delà du RAG

RAG ne suffit pas toujours :

- **Raisonnement multi-étapes** : "Compare notre CA Q3 sur toutes les BUs et identifie l'anomalie" → boucle agent avec exécution de code
- **Données en temps réel** : RAG ne peut pas récupérer l'état d'une base de données en direct — utiliser le tool-calling vers une source live
- **Workflows complexes** : l'utilisateur veut *agir*, pas juste *lire* → assistant agentique
