---
id: llm-not-a-truth-machine
title:
  en: "LLMs Are Not Truth Machines"
  fr: "Les LLMs ne sont pas des machines à vérité"
summary:
  en: "Why asking an LLM for ground truth is the wrong mental model — and what RAG does instead."
  fr: "Pourquoi demander la vérité à un LLM est le mauvais modèle mental — et ce que fait RAG à la place."
tags: [llm, inference, hallucination, rag, mental-model, temperature]
related_terms: [hallucination, inference, temperature, context_window, rag, embedding]
related_nodes: [llm_core, rag_pattern, inference_params]
status: stable
date: 2026-04-15
sources: []
---

<!-- LANG:EN -->

## The question nobody asks out loud

When people get a wrong answer from an LLM, the usual reaction is: "it hallucinated." The word implies the model made a mistake it shouldn't have made — like a reliable system that glitched. That framing is wrong, and it leads to a bad mental model for everything that follows.

The better question is: why would a language model ever be *right* about a specific fact?

## What an LLM actually is

A large language model is trained on a massive corpus of text — web pages, books, code, forums. The training process doesn't build a database of facts. It compresses statistical patterns into billions of numerical parameters called **weights**.

When you ask a question, the model doesn't look anything up. It runs a mathematical operation over its weights and the tokens in your prompt to compute **what text is most likely to come next**. That's it. The mechanism is prediction, not recall.

This has a non-obvious consequence: the model can produce a fluent, confident, detailed answer about something it was never directly trained on — by interpolating from related patterns. Sometimes that interpolation is accurate. Sometimes it isn't. The model has no internal signal to tell the difference.

## What changes the output

If you ask the same question twice, you may not get the same answer. Here's why:

**Temperature** is a parameter that controls randomness in the sampling process. At temperature 0, the model always picks the most probable next token — outputs are deterministic. At higher temperatures, lower-probability tokens get more chances to be selected. The same question becomes a probability distribution over possible answers, not a single answer.

**Top-p and top-k** are related sampling parameters that constrain which tokens are eligible at each step. They tune the balance between coherence and diversity.

**The system prompt and context window** change what the model "sees" when generating. A different system prompt — even a subtle one — shifts the probability distribution over outputs. The model doesn't have a view of facts independent of its context; it reasons over what's in front of it.

**The model itself** matters. GPT-4, Claude, Llama 3, and Mistral were trained on different data, with different architectures and different fine-tuning processes (RLHF, RLAIF, DPO...). They have systematically different strengths, biases, and failure modes. On contested facts, they may genuinely disagree.

None of these parameters have a "correct" setting for factual accuracy. The model has no access to ground truth.

## The training cutoff problem

Model weights are frozen at the end of training. Nothing that happened after the cutoff date exists in the model's weights. If you ask about recent events, the model may:

- correctly say it doesn't know
- confabulate something plausible based on earlier patterns
- confidently give you outdated information presented as current

The cutoff is published for each model, but it's not a clean line — data from just before the cutoff is underrepresented compared to older data (the internet takes time to process and discuss events). Models are often less reliable about the year preceding their cutoff than about things from several years earlier.

## Hallucination is not a bug

The word "hallucination" gets used as if it describes an anomaly. It describes the default behavior of the architecture.

When a model generates a citation that doesn't exist, it's doing exactly what it was trained to do: producing a sequence of tokens that looks like a valid citation, based on the patterns of how citations are structured in its training data. The model isn't checking against a database of real papers. There is no such check in the architecture.

The same applies to statistics, dates, names, addresses, code behavior, and legal facts. The model generates plausible continuations. Plausibility is not accuracy.

This doesn't mean LLMs are useless for factual tasks. It means the right use of an LLM for factual tasks requires a different architecture — one that separates retrieval of real data from generation of language.

## The right mental model

Think of an LLM as an expert reasoner with no access to recent documents and an imperfect memory.

Ask it to explain a concept, structure an argument, synthesize multiple perspectives, write code, translate, or reason over something you've given it — it's excellent at these. These are tasks where the quality of reasoning matters more than access to ground truth.

Ask it to tell you what happened last week, whether a specific fact is true, or what a specific document says (without giving it the document) — these are tasks where you need data, not reasoning. An LLM alone is the wrong tool.

## What RAG does

RAG (Retrieval-Augmented Generation) is the standard architectural answer to this problem. Instead of asking the model to recall facts from its weights, you:

1. **Retrieve** relevant documents from a database you control (recent, verified, specific)
2. **Inject** those documents into the model's context window
3. **Ask the model to reason** over the provided documents

The model's job becomes reasoning and synthesis over real data you supplied — not recalling compressed patterns from training. The knowledge comes from your database. The reasoning comes from the model. These two responsibilities are cleanly separated.

This is why RAG dramatically reduces hallucinations on factual questions: the model is no longer asked to generate facts from memory. It's asked to extract and synthesize facts from documents it can actually see.

See the [RAG deep dive](/topics/rag-deep-dive.html) for the full technical breakdown.

## What this means in practice

When you use an LLM:

- **Don't verify outputs by asking the same model again.** The model will confirm its own confabulations fluently.
- **Treat confidence of phrasing as unrelated to accuracy.** A model can be maximally confident and maximally wrong simultaneously.
- **For factual tasks, give the model the documents.** Paste in the relevant text, policy, or data. RAG automates this at scale.
- **For reasoning tasks, LLMs are powerful.** Analysis, synthesis, writing, code generation — these are not ground-truth tasks and LLMs excel at them.
- **Different models, different answers.** If a question matters, cross-check across models and treat disagreement as a signal to verify externally.

The mental model shift: stop thinking of an LLM as a search engine that knows things. Start thinking of it as a powerful reasoning engine that needs you to supply the data.

<!-- LANG:FR -->

## La question que personne ne pose à voix haute

Quand on obtient une mauvaise réponse d'un LLM, la réaction habituelle est : "il a halluciné." Le mot suggère que le modèle a fait une erreur qu'il n'aurait pas dû faire — comme un système fiable qui a bugué. Ce cadrage est faux, et il mène à un mauvais modèle mental pour tout ce qui suit.

La meilleure question est : pourquoi un modèle de langage serait-il *exact* sur un fait précis ?

## Ce qu'est vraiment un LLM

Un grand modèle de langage est entraîné sur un corpus massif de textes — pages web, livres, code, forums. Le processus d'entraînement ne construit pas une base de données de faits. Il compresse des patterns statistiques dans des milliards de paramètres numériques appelés **poids**.

Quand tu poses une question, le modèle ne cherche rien. Il exécute une opération mathématique sur ses poids et les tokens de ton prompt pour calculer **quel texte a la plus grande probabilité de suivre**. C'est tout. Le mécanisme est la prédiction, pas la mémorisation.

Ça a une conséquence contre-intuitive : le modèle peut produire une réponse fluide, confiante et détaillée sur quelque chose qu'il n'a jamais vu directement à l'entraînement — par interpolation de patterns voisins. Parfois cette interpolation est exacte. Parfois non. Le modèle n'a aucun signal interne pour faire la différence.

## Ce qui change la réponse

Si tu poses la même question deux fois, tu ne peux pas garantir la même réponse. Voici pourquoi.

**La température** est un paramètre qui contrôle l'aléatoire dans le processus d'échantillonnage. À température 0, le modèle choisit toujours le token suivant le plus probable — les sorties sont déterministes. À des températures plus élevées, les tokens moins probables ont plus de chances d'être sélectionnés. La même question devient une distribution de probabilité sur des réponses possibles, pas une réponse unique.

**Top-p et top-k** sont des paramètres d'échantillonnage voisins qui contraignent quels tokens sont éligibles à chaque étape. Ils règlent l'équilibre entre cohérence et diversité.

**Le system prompt et la fenêtre de contexte** changent ce que le modèle "voit" en générant. Un system prompt différent — même subtilement — déplace la distribution de probabilité sur les sorties. Le modèle n'a pas de point de vue sur les faits indépendant de son contexte ; il raisonne sur ce qui est devant lui.

**Le modèle lui-même** compte. GPT-4, Claude, Llama 3 et Mistral ont été entraînés sur des données différentes, avec des architectures et des processus de fine-tuning différents (RLHF, RLAIF, DPO...). Ils ont des forces, des biais et des modes d'échec systématiquement différents. Sur des faits controversés, ils peuvent sincèrement ne pas être d'accord.

Aucun de ces paramètres n'a un réglage "correct" pour l'exactitude factuelle. Le modèle n'a pas accès à une vérité de référence.

## Le problème du knowledge cutoff

Les poids du modèle sont gelés à la fin de l'entraînement. Rien de ce qui s'est passé après la date de cutoff n'existe dans les poids. Si tu poses une question sur des événements récents, le modèle peut :

- dire correctement qu'il ne sait pas
- confabuler quelque chose de plausible basé sur des patterns antérieurs
- te donner confidemment une information obsolète présentée comme actuelle

Le cutoff est publié pour chaque modèle, mais ce n'est pas une ligne nette — les données de juste avant le cutoff sont sous-représentées par rapport aux données plus anciennes (internet prend du temps pour traiter et discuter des événements). Les modèles sont souvent moins fiables sur l'année qui précède leur cutoff que sur des choses de plusieurs années plus tôt.

## L'hallucination n'est pas un bug

Le mot "hallucination" est utilisé comme s'il décrivait une anomalie. Il décrit le comportement par défaut de l'architecture.

Quand un modèle génère une citation qui n'existe pas, il fait exactement ce pour quoi il a été entraîné : produire une séquence de tokens qui ressemble à une citation valide, basée sur les patterns de la façon dont les citations sont structurées dans ses données d'entraînement. Le modèle ne vérifie pas contre une base de vrais articles. Cette vérification n'existe pas dans l'architecture.

La même chose s'applique aux statistiques, aux dates, aux noms, aux adresses, au comportement du code et aux faits juridiques. Le modèle génère des continuations plausibles. La plausibilité n'est pas l'exactitude.

Ça ne veut pas dire que les LLMs sont inutiles pour les tâches factuelles. Ça veut dire que le bon usage d'un LLM pour des tâches factuelles nécessite une architecture différente — une qui sépare la récupération de données réelles de la génération de langage.

## Le bon modèle mental

Pense à un LLM comme à un expert raisonnant sans accès aux documents récents et avec une mémoire imparfaite.

Demande-lui d'expliquer un concept, structurer un argument, synthétiser plusieurs perspectives, écrire du code, traduire, ou raisonner sur quelque chose que tu lui as fourni — il est excellent pour ça. Ce sont des tâches où la qualité du raisonnement compte plus que l'accès à la vérité de référence.

Demande-lui ce qui s'est passé la semaine dernière, si un fait précis est vrai, ou ce que dit un document spécifique (sans lui donner le document) — là tu as besoin de données, pas de raisonnement. Un LLM seul est le mauvais outil.

## Ce que fait RAG

RAG (Retrieval-Augmented Generation) est la réponse architecturale standard à ce problème. Au lieu de demander au modèle de rappeler des faits depuis ses poids, tu :

1. **Récupères** des documents pertinents depuis une base de données que tu contrôles (récente, vérifiée, spécifique)
2. **Injectes** ces documents dans la fenêtre de contexte du modèle
3. **Demandes au modèle de raisonner** sur les documents fournis

Le travail du modèle devient le raisonnement et la synthèse sur des données réelles que tu as fournies — pas le rappel de patterns compressés depuis l'entraînement. La connaissance vient de ta base de données. Le raisonnement vient du modèle. Ces deux responsabilités sont clairement séparées.

C'est pourquoi RAG réduit drastiquement les hallucinations sur les questions factuelles : le modèle n'est plus invité à générer des faits de mémoire. Il est invité à extraire et synthétiser des faits depuis des documents qu'il peut réellement voir.

Voir le [deep dive sur RAG](/topics/rag-deep-dive.html) pour l'analyse technique complète.

## Ce que ça veut dire en pratique

Quand tu utilises un LLM :

- **Ne vérifie pas les sorties en reposant la même question au même modèle.** Le modèle confirmera ses propres confabulations avec fluidité.
- **Traite la confiance du style comme sans rapport avec l'exactitude.** Un modèle peut être maximalement confiant et maximalement dans l'erreur simultanément.
- **Pour les tâches factuelles, donne les documents au modèle.** Colle le texte, la politique ou les données pertinentes. RAG automatise ça à l'échelle.
- **Pour les tâches de raisonnement, les LLMs sont puissants.** Analyse, synthèse, rédaction, génération de code — ce ne sont pas des tâches de vérité de référence et les LLMs y excellent.
- **Modèles différents, réponses différentes.** Si une question compte, vérifie en croisant les modèles et traite le désaccord comme un signal pour vérifier en externe.

Le changement de modèle mental : arrête de penser à un LLM comme à un moteur de recherche qui sait des choses. Commence à le voir comme un moteur de raisonnement puissant qui a besoin que tu lui fournisses les données.
