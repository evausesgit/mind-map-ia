---
id: usecase-analyst-rag
title:
  en: "Use Case: Knowledge Search for Analysts"
  fr: "Cas d'Usage : Recherche dans la Connaissance pour Analystes"
summary:
  en: "How a business analyst queries private document corpora with AI — architecture, governance, and practical trade-offs."
  fr: "Comment un analyste métier interroge des corpus de documents privés avec l'IA — architecture, gouvernance, et compromis pratiques."
tags: [rag, analyst, enterprise, knowledge-base, governance, citations]
related_terms: [rag, embedding, vector_database, hallucination, context_window]
related_nodes: [uc-analyst-search, pattern-rag, stack-llm, stack-vector-db]
status: stable
date: 2026-04-06
sources: []
---

<!-- LANG:EN -->

## The scenario

A business analyst at a bank, law firm, or large enterprise needs to answer a question like:

- "What are our contractual obligations to client X regarding SLA response times?"
- "Summarize the key risk factors mentioned in our last 5 annual reports."
- "Which internal policies apply to cross-border data transfers to Brazil?"

Manually searching through SharePoint, email threads, and PDF archives takes hours. With a RAG-powered assistant over the right corpus, it takes seconds — with source citations.

## Why this use case is different from consumer Q&A

Consumer chat products use public knowledge. Enterprise knowledge search is harder because:

**1. Documents are private and heterogeneous.** PDFs, Word docs, Excel sheets, PowerPoints, emails, ticketing systems — all in the same corpus, with different formatting, language, and quality.

**2. Accuracy requirements are much higher.** A wrong answer in a legal or compliance context isn't just embarrassing — it can be costly or illegal. Hallucination tolerance is near zero.

**3. Access control is mandatory.** An analyst in the trading desk shouldn't see HR documents. Document-level permissions must be enforced, not just document-level indexing.

**4. Audit trail is required.** In regulated industries, every answer must be traceable: which document, which version, retrieved on which date, by which user.

## Architecture

Same RAG foundation as consumer Q&A, with additional enterprise layers:

```
[Document sources]  →  ingestion pipeline  →  vector index (with ACL metadata)
                                                       ↓
User query  →  [Auth check]  →  [Filtered retrieval]  →  [LLM generation]
                                    (only docs user can see)         ↓
                                                         Answer + citations + source metadata
```

Key difference: **retrieval must be ACL-aware**. When storing chunks, metadata includes the document's access permissions. At query time, the search filters to only chunks the requesting user is authorized to see.

## Ingestion challenges

Getting enterprise documents into a searchable index is often the hardest part:

**Format diversity.** PDFs with scanned content need OCR. Excel tables need special handling (row-by-row vs. summary). PowerPoint decks need slide-by-slide chunking. Email threads need deduplication.

**Metadata extraction.** For good citations and filtering, you need document metadata: title, author, date, department, version, classification. Extracting this automatically is often imperfect.

**Language heterogeneity.** Multinational companies have documents in multiple languages. The embedding model and the LLM must handle all of them well.

**Change management.** Documents are revised regularly. Version control of the index is necessary — knowing that a chunk comes from v2.1 of a contract, not v2.0.

## Making answers trustworthy

In an enterprise context, the answer alone is not enough. The analyst needs to be able to defend the answer to a manager, a regulator, or a client.

**Verbatim citations.** Don't just say "according to document X" — quote the exact sentences from the source document and show the page/section reference.

**Confidence signals.** If retrieval similarity is low (the question is about something not well-covered in the corpus), say so explicitly.

**Date-awareness.** Include the document version and date in citations. "According to the Privacy Policy updated 2025-11-01..." prevents confusion when policies change.

**Human-in-the-loop escalation.** For high-stakes questions, the system should suggest: "This answer involves regulatory risk — you may want to verify with Legal."

## Typical corpus sizes and latency expectations

| Corpus size | Number of chunks | Retrieval latency | Comment |
|---|---|---|---|
| Small (< 500 docs) | < 100K chunks | < 200ms | pgvector is enough |
| Medium (500–5K docs) | 100K–1M chunks | 200–500ms | Dedicated vector DB needed |
| Large (> 5K docs) | > 1M chunks | 500ms–2s | Sharding, approximate search |

For most enterprise knowledge search deployments, medium scale is the norm.

## Failure modes specific to enterprise

**Conflicting documents.** Two policy documents say different things (the 2022 version and the 2024 version). The LLM synthesizes a blended answer that's wrong. Fix: surface both sources, let the user see the conflict explicitly.

**Table and chart blindness.** Key data is in a table or graph that the embedding model doesn't represent well as text. Fix: table-aware chunking, description of charts added by preprocessing.

**Jargon and abbreviation mismatch.** The user asks about "the MRO protocol" but the document calls it "Material Requirements Ordering Process." Fix: synonym expansion, ontology-based query enrichment.

**Overconfident answers on edge cases.** The model answers confidently on rare topics with sparse coverage. Fix: retrieval confidence threshold + explicit fallback message.

## The governance checklist

Before deploying a knowledge search tool in an enterprise:

- [ ] Who owns the document corpus and approves indexing?
- [ ] How is document-level access control enforced in the index?
- [ ] What is the data retention policy for query logs?
- [ ] Can the system see PII, confidential, or classified documents? Should it?
- [ ] How are document updates reflected in the index (frequency, lag)?
- [ ] What is the escalation path when the AI answer is wrong?
- [ ] Is there a feedback loop so analysts can flag bad answers?

## Typical stack

| Layer | Examples |
|---|---|
| Ingestion | Unstructured.io, Azure Document Intelligence, Apache Tika |
| Embeddings | Cohere Embed v3, OpenAI text-embedding-3, private models |
| Vector DB | Weaviate (ACL-aware), Qdrant, Elasticsearch with kNN |
| LLM | GPT-4o, Claude 3.5/4, Azure OpenAI (data residency) |
| Orchestration | LangChain, LlamaIndex, custom |
| Access control | Integration with enterprise IAM (Azure AD, Okta) |

<!-- LANG:FR -->

## Le scénario

Un analyste métier dans une banque, un cabinet juridique, ou une grande entreprise doit répondre à des questions comme :

- "Quelles sont nos obligations contractuelles envers le client X concernant les délais de réponse SLA ?"
- "Résume les facteurs de risque clés mentionnés dans nos 5 derniers rapports annuels."
- "Quelles politiques internes s'appliquent aux transferts de données transfrontaliers vers le Brésil ?"

Chercher manuellement dans SharePoint, des fils d'emails, et des archives PDF prend des heures. Avec un assistant RAG sur le bon corpus, ça prend quelques secondes — avec des citations sources.

## Pourquoi ce cas d'usage est différent du Q&A grand public

Les produits de chat grand public utilisent des connaissances publiques. La recherche dans la connaissance entreprise est plus difficile car :

**1. Les documents sont privés et hétérogènes.** PDFs, documents Word, feuilles Excel, PowerPoints, emails, systèmes de ticketing — tout dans le même corpus, avec des formats, langages et qualités différents.

**2. Les exigences de précision sont beaucoup plus élevées.** Une mauvaise réponse dans un contexte légal ou conformité n'est pas juste gênante — elle peut être coûteuse ou illégale. La tolérance aux hallucinations est quasi nulle.

**3. Le contrôle d'accès est obligatoire.** Un analyste du bureau de trading ne devrait pas voir les documents RH. Les permissions au niveau document doivent être appliquées, pas seulement au niveau de l'indexation.

**4. La piste d'audit est requise.** Dans les industries régulées, chaque réponse doit être traçable : quel document, quelle version, récupéré à quelle date, par quel utilisateur.

## Architecture

Même base RAG que le Q&A grand public, avec des couches entreprise additionnelles :

```
[Sources documents]  →  pipeline d'ingestion  →  index vectoriel (avec métadonnées ACL)
                                                              ↓
Requête utilisateur  →  [Vérification auth]  →  [Récupération filtrée]  →  [Génération LLM]
                                                  (seulement docs visibles)           ↓
                                                                       Réponse + citations + métadonnées source
```

Différence clé : **la récupération doit être consciente des ACL**. En stockant les chunks, les métadonnées incluent les permissions d'accès du document. Au moment de la requête, la recherche filtre pour ne retourner que les chunks que l'utilisateur demandeur est autorisé à voir.

## Défis d'ingestion

Mettre les documents entreprise dans un index cherchable est souvent la partie la plus difficile :

**Diversité des formats.** Les PDFs avec contenu scanné nécessitent l'OCR. Les tableaux Excel nécessitent un traitement spécial (ligne par ligne vs. résumé). Les présentations PowerPoint nécessitent un chunking diapo par diapo. Les fils d'emails nécessitent la déduplication.

**Extraction des métadonnées.** Pour de bonnes citations et du filtrage, vous avez besoin des métadonnées du document : titre, auteur, date, département, version, classification. L'extraction automatique de celles-ci est souvent imparfaite.

**Hétérogénéité linguistique.** Les entreprises multinationales ont des documents en plusieurs langues. Le modèle d'embedding et le LLM doivent tous deux bien les gérer.

**Gestion des changements.** Les documents sont régulièrement révisés. Le contrôle de version de l'index est nécessaire — savoir qu'un chunk provient de la v2.1 d'un contrat, pas de la v2.0.

## Rendre les réponses dignes de confiance

Dans un contexte entreprise, la réponse seule ne suffit pas. L'analyste doit pouvoir défendre la réponse devant un manager, un régulateur, ou un client.

**Citations verbatim.** Ne pas juste dire "selon le document X" — citer les phrases exactes du document source et montrer la référence page/section.

**Signaux de confiance.** Si la similarité de récupération est faible (la question porte sur quelque chose peu couvert dans le corpus), le dire explicitement.

**Conscience de la date.** Inclure la version et la date du document dans les citations. "Selon la Politique de Confidentialité mise à jour le 2025-11-01..." évite la confusion quand les politiques changent.

**Escalade humaine dans la boucle.** Pour les questions à forts enjeux, le système devrait suggérer : "Cette réponse implique un risque réglementaire — vous pourriez vouloir vérifier avec le Juridique."

## Tailles de corpus typiques et attentes de latence

| Taille corpus | Nombre de chunks | Latence récupération | Commentaire |
|---|---|---|---|
| Petit (< 500 docs) | < 100K chunks | < 200ms | pgvector suffit |
| Moyen (500–5K docs) | 100K–1M chunks | 200–500ms | Vector DB dédié nécessaire |
| Grand (> 5K docs) | > 1M chunks | 500ms–2s | Sharding, recherche approximative |

Pour la plupart des déploiements de recherche dans la connaissance entreprise, l'échelle moyenne est la norme.

## Modes d'échec spécifiques à l'entreprise

**Documents conflictuels.** Deux documents de politique disent des choses différentes (la version 2022 et la version 2024). Le LLM synthétise une réponse hybride qui est fausse. Correction : afficher les deux sources, laisser l'utilisateur voir le conflit explicitement.

**Cécité aux tableaux et graphiques.** Les données clés sont dans un tableau ou graphique que le modèle d'embedding ne représente pas bien en texte. Correction : chunking conscient des tableaux, description des graphiques ajoutée par prétraitement.

**Inadéquation jargon et abréviations.** L'utilisateur demande "le protocole MRO" mais le document l'appelle "Processus de Commande des Exigences Matérielles". Correction : expansion des synonymes, enrichissement de requête basé sur une ontologie.

**Réponses trop confiantes sur les cas limites.** Le modèle répond avec assurance sur des sujets rares avec une couverture sparse. Correction : seuil de confiance de récupération + message de fallback explicite.

## La checklist de gouvernance

Avant de déployer un outil de recherche dans la connaissance en entreprise :

- [ ] Qui possède le corpus de documents et approuve l'indexation ?
- [ ] Comment le contrôle d'accès au niveau document est-il appliqué dans l'index ?
- [ ] Quelle est la politique de rétention des données pour les logs de requêtes ?
- [ ] Le système peut-il voir des documents PII, confidentiels ou classifiés ? Devrait-il ?
- [ ] Comment les mises à jour des documents se reflètent-elles dans l'index (fréquence, délai) ?
- [ ] Quel est le chemin d'escalade quand la réponse IA est fausse ?
- [ ] Y a-t-il une boucle de feedback pour que les analystes puissent signaler les mauvaises réponses ?

## Stack typique

| Couche | Exemples |
|---|---|
| Ingestion | Unstructured.io, Azure Document Intelligence, Apache Tika |
| Embeddings | Cohere Embed v3, OpenAI text-embedding-3, modèles privés |
| Vector DB | Weaviate (conscient des ACL), Qdrant, Elasticsearch avec kNN |
| LLM | GPT-4o, Claude 3.5/4, Azure OpenAI (résidence des données) |
| Orchestration | LangChain, LlamaIndex, custom |
| Contrôle d'accès | Intégration avec IAM entreprise (Azure AD, Okta) |
