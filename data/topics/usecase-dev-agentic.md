---
id: usecase-dev-agentic
title:
  en: "Use Case: Agentic Coding"
  fr: "Cas d'Usage : Coding Agentique"
summary:
  en: "How an AI agent assists a developer beyond autocomplete — planning, editing, running tests, and iterating autonomously."
  fr: "Comment un agent IA assiste un développeur au-delà de l'autocomplétion — planification, édition, exécution de tests, et itération autonome."
tags: [agents, coding, ide, mcp, tool-use, developer]
related_terms: [agent, tool_use, context_window, mcp]
related_nodes: [uc-dev-agent, pattern-agent-loop, stack-tools, stack-llm, stack-memory]
status: evolving
date: 2026-04-06
sources: []
---

<!-- LANG:EN -->

## The scenario

A developer describes a task in natural language — "add pagination to the user list endpoint, with tests" — and an AI agent reads the relevant files, writes the code changes, runs the tests, reads the failure output, fixes the issue, and stops when the tests pass.

No copy-paste from ChatGPT. No manual application of suggestions. The agent is in the loop.

This is **agentic coding**: the AI operates as a collaborator with file access, tool use, and iterative execution — not just a text completion engine.

## How it works

The agent runs a loop:

```
Task description (from developer)
    ↓
[LLM: Plan]  →  steps to accomplish the task
    ↓
[LLM: Act]   →  tool call (read file / write file / run command / search docs)
    ↓
[Tool execution]  →  result (file content / test output / error message)
    ↓
[LLM: Observe]  →  interpret result, decide next action
    ↓
... repeat until done or human approval needed
```

The LLM is not just generating text — it is **reasoning about state** and **making decisions**. The tools give it hands.

## Tools an agentic coding assistant uses

| Tool | What it does |
|---|---|
| `read_file` | Read any file in the repo |
| `write_file` | Create or overwrite a file |
| `edit_file` | Make targeted edits (diff-style) |
| `run_command` | Execute shell commands (tests, builds, linters) |
| `search_codebase` | Semantic or keyword search across files |
| `web_search` | Look up documentation, Stack Overflow, GitHub issues |
| `list_directory` | Explore the file tree |

MCP (Model Context Protocol) is the emerging standard for defining and connecting these tools — allowing the same agent to work across different editors and environments.

## What changes compared to autocomplete

Autocomplete is **reactive**: the dev types, the model suggests the next tokens.

Agentic coding is **proactive**: the dev describes intent, the agent figures out what to do, does it, verifies it, and iterates.

| | Autocomplete | Agentic |
|---|---|---|
| Trigger | Dev types | Dev describes task |
| Scope | Current file, cursor position | Entire codebase |
| Execution | Suggestion only | Runs code, tests, commands |
| Iteration | One-shot | Multiple steps |
| Human in loop | Every suggestion | At approval checkpoints |
| Error handling | None | Reads errors, tries to fix |

## The trust and control problem

Agentic coding introduces a new challenge: **the agent takes actions that are hard to reverse**.

Deleting a file is easy. Undoing it after 5 more agent steps is painful. Letting an agent push to `main` without review is dangerous.

Good agentic systems address this with:

**1. Checkpoints.** The agent pauses before destructive actions (file deletion, git push, running migrations) and asks for approval.

**2. Diff review.** All file edits are shown as diffs before being applied. The dev sees exactly what changed.

**3. Sandbox execution.** Shell commands run in a sandboxed environment — the agent can't accidentally affect production.

**4. Scope constraints.** The agent is told which directories it's allowed to modify. It cannot wander outside the task boundary.

**5. Git as a safety net.** Every significant checkpoint creates a commit. If the agent goes off-track, `git reset` brings you back.

## Context window management

An agentic session over a large codebase quickly exhausts the context window. The agent needs to be smart about what it loads:

- **Don't load the entire repo** — only files relevant to the task
- **Summarize read results** — instead of including the full file, extract only the relevant functions
- **Use search first, read second** — search to find the right file, then read only that file

KV cache is critical for performance: large shared context (the task description, coding conventions, architecture overview) is cached and not re-sent on every iteration.

## Practical example: "Add pagination to /users endpoint"

```
Step 1  → search_codebase("users endpoint") 
        → finds src/routes/users.py

Step 2  → read_file("src/routes/users.py")
        → sees: def list_users(): return all_users

Step 3  → read_file("tests/test_users.py")
        → sees: existing tests for list_users

Step 4  → edit_file("src/routes/users.py")
        → adds: page, page_size params + slicing logic

Step 5  → edit_file("tests/test_users.py")
        → adds: tests for pagination edge cases

Step 6  → run_command("pytest tests/test_users.py")
        → output: FAILED – TypeError: unsupported operand

Step 7  → [LLM reads error, identifies off-by-one in slicing]
        → edit_file("src/routes/users.py") — fixes the bug

Step 8  → run_command("pytest tests/test_users.py")
        → output: 4 passed

Done. → presents diff to developer for review
```

## Leading tools in 2026

| Tool | Type | Key feature |
|---|---|---|
| Claude Code | CLI agent | Deep file/shell access, MCP |
| Cursor | Agentic IDE | Codebase-wide context, inline agent |
| GitHub Copilot Workspace | Cloud agent | PR-level tasks, GitHub integration |
| Devin | Autonomous agent | Full-session autonomy, web browsing |
| Windsurf (Codeium) | Agentic IDE | Flow-based agent, fast iteration |

## When agentic coding shines — and when it doesn't

**Good fit:**
- Repetitive, well-defined tasks (add CRUD endpoints, write tests for existing code, migrate a library)
- Debugging with a clear error message and isolated scope
- Exploring an unfamiliar codebase to understand structure

**Poor fit:**
- Architectural decisions that require deep business context
- Tasks requiring access to systems the agent can't reach (production DBs, customer data)
- Long-horizon tasks where the goal keeps changing — the agent needs stable objectives

<!-- LANG:FR -->

## Le scénario

Un développeur décrit une tâche en langage naturel — "ajouter la pagination à l'endpoint liste utilisateurs, avec des tests" — et un agent IA lit les fichiers pertinents, écrit les modifications de code, exécute les tests, lit la sortie d'échec, corrige le problème, et s'arrête quand les tests passent.

Pas de copier-coller depuis ChatGPT. Pas d'application manuelle des suggestions. L'agent est dans la boucle.

C'est le **coding agentique** : l'IA opère comme un collaborateur avec accès aux fichiers, utilisation d'outils, et exécution itérative — pas juste un moteur de complétion de texte.

## Comment ça fonctionne

L'agent exécute une boucle :

```
Description de la tâche (du développeur)
    ↓
[LLM : Planifier]  →  étapes pour accomplir la tâche
    ↓
[LLM : Agir]       →  appel d'outil (lire fichier / écrire fichier / exécuter commande / chercher docs)
    ↓
[Exécution outil]  →  résultat (contenu fichier / sortie tests / message d'erreur)
    ↓
[LLM : Observer]   →  interpréter le résultat, décider l'action suivante
    ↓
... répéter jusqu'à ce que ce soit terminé ou qu'une approbation humaine soit nécessaire
```

Le LLM ne génère pas juste du texte — il **raisonne sur l'état** et **prend des décisions**. Les outils lui donnent des mains.

## Outils qu'un assistant de coding agentique utilise

| Outil | Ce qu'il fait |
|---|---|
| `read_file` | Lire n'importe quel fichier du dépôt |
| `write_file` | Créer ou écraser un fichier |
| `edit_file` | Effectuer des modifications ciblées (style diff) |
| `run_command` | Exécuter des commandes shell (tests, builds, linters) |
| `search_codebase` | Recherche sémantique ou par mots-clés dans les fichiers |
| `web_search` | Consulter la documentation, Stack Overflow, les issues GitHub |
| `list_directory` | Explorer l'arborescence des fichiers |

MCP (Model Context Protocol) est le standard émergent pour définir et connecter ces outils — permettant au même agent de fonctionner dans différents éditeurs et environnements.

## Ce qui change par rapport à l'autocomplétion

L'autocomplétion est **réactive** : le dev tape, le modèle suggère les tokens suivants.

Le coding agentique est **proactif** : le dev décrit l'intention, l'agent détermine quoi faire, le fait, le vérifie, et itère.

| | Autocomplétion | Agentique |
|---|---|---|
| Déclencheur | Le dev tape | Le dev décrit la tâche |
| Périmètre | Fichier courant, position curseur | Toute la codebase |
| Exécution | Suggestion seulement | Exécute code, tests, commandes |
| Itération | Passage unique | Plusieurs étapes |
| Humain dans la boucle | Chaque suggestion | Aux points d'approbation |
| Gestion des erreurs | Aucune | Lit les erreurs, essaie de corriger |

## Le problème de confiance et de contrôle

Le coding agentique introduit un nouveau défi : **l'agent prend des actions difficiles à annuler**.

Supprimer un fichier est facile. L'annuler après 5 autres étapes de l'agent est pénible. Laisser un agent pousser sur `main` sans relecture est dangereux.

Les bons systèmes agentiques adressent cela avec :

**1. Les checkpoints.** L'agent fait une pause avant les actions destructrices (suppression de fichier, git push, exécution de migrations) et demande une approbation.

**2. La revue de diff.** Toutes les modifications de fichiers sont montrées comme des diffs avant d'être appliquées. Le dev voit exactement ce qui a changé.

**3. L'exécution en sandbox.** Les commandes shell s'exécutent dans un environnement sandboxé — l'agent ne peut pas accidentellement affecter la production.

**4. Les contraintes de périmètre.** L'agent sait quels répertoires il est autorisé à modifier. Il ne peut pas s'égarer hors du périmètre de la tâche.

**5. Git comme filet de sécurité.** Chaque checkpoint significatif crée un commit. Si l'agent déraille, `git reset` ramène en arrière.

## Gestion de la fenêtre de contexte

Une session agentique sur une grande codebase épuise rapidement la fenêtre de contexte. L'agent doit être intelligent sur ce qu'il charge :

- **Ne pas charger tout le dépôt** — seulement les fichiers pertinents pour la tâche
- **Résumer les résultats de lecture** — au lieu d'inclure le fichier entier, extraire seulement les fonctions pertinentes
- **Chercher d'abord, lire ensuite** — rechercher pour trouver le bon fichier, puis lire seulement ce fichier

Le KV cache est critique pour la performance : le contexte partagé large (description de la tâche, conventions de code, vue d'architecture) est mis en cache et non renvoyé à chaque itération.

## Exemple pratique : "Ajouter la pagination à l'endpoint /users"

```
Étape 1  → search_codebase("users endpoint") 
         → trouve src/routes/users.py

Étape 2  → read_file("src/routes/users.py")
         → voit : def list_users(): return all_users

Étape 3  → read_file("tests/test_users.py")
         → voit : tests existants pour list_users

Étape 4  → edit_file("src/routes/users.py")
         → ajoute : params page, page_size + logique de slicing

Étape 5  → edit_file("tests/test_users.py")
         → ajoute : tests pour les cas limites de pagination

Étape 6  → run_command("pytest tests/test_users.py")
         → sortie : FAILED – TypeError: unsupported operand

Étape 7  → [LLM lit l'erreur, identifie un off-by-one dans le slicing]
         → edit_file("src/routes/users.py") — corrige le bug

Étape 8  → run_command("pytest tests/test_users.py")
         → sortie : 4 passed

Terminé. → présente le diff au développeur pour revue
```

## Outils leaders en 2026

| Outil | Type | Caractéristique clé |
|---|---|---|
| Claude Code | Agent CLI | Accès profond fichiers/shell, MCP |
| Cursor | IDE agentique | Contexte à l'échelle de la codebase, agent inline |
| GitHub Copilot Workspace | Agent cloud | Tâches niveau PR, intégration GitHub |
| Devin | Agent autonome | Autonomie session complète, navigation web |
| Windsurf (Codeium) | IDE agentique | Agent basé sur les flux, itération rapide |

## Quand le coding agentique brille — et quand il ne brille pas

**Bon fit :**
- Tâches répétitives et bien définies (ajouter des endpoints CRUD, écrire des tests pour du code existant, migrer une librairie)
- Débogage avec un message d'erreur clair et un périmètre isolé
- Explorer une codebase inconnue pour comprendre la structure

**Mauvais fit :**
- Décisions architecturales nécessitant un contexte métier profond
- Tâches nécessitant l'accès à des systèmes que l'agent ne peut pas atteindre (BDD production, données clients)
- Tâches à long horizon où le but change constamment — l'agent a besoin d'objectifs stables
