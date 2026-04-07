---
id: mcp-explained
title:
  en: "MCP: The Standard for Connecting AI to Everything"
  fr: "MCP : Le Standard pour Connecter l'IA à Tout"
summary:
  en: "What MCP is, how it works architecturally, and why it matters for AI agent development."
  fr: "Ce qu'est MCP, comment ça fonctionne architecturalement, et pourquoi c'est important pour le développement d'agents IA."
tags: [mcp, agents, tools, protocol, integration]
related_terms: [tool_use, agent, context_window]
related_nodes: [tool_use_pattern, agents_pattern, mcp_pattern]
status: stable
date: 2026-04-04
sources:
  - data/sources/2026-04-04-mcp.md
---

<!-- LANG:EN -->

## What is MCP?

MCP (Model Context Protocol) is an open standard that defines how AI applications connect to external data sources and tools. Think of it as USB-C for AI: instead of every application building its own custom integration with every tool, MCP provides a single protocol that any compliant client and server can speak.

Before MCP, every AI-powered IDE, chat interface, or workflow tool had to build bespoke connectors for every external resource it wanted to access — filesystem, databases, APIs, code interpreters. This was duplicated effort and a maintenance nightmare. MCP solves this with a shared protocol layer.

Governed by the **Linux Foundation** (not proprietary to Anthropic), MCP is a community standard with official SDKs in 10 languages: TypeScript, Python, Java, Kotlin, C#, Go, PHP, Ruby, Rust, and Swift.

## Architecture

MCP follows a **client-server model** with three roles:

- **MCP Host**: the application that wants to use AI + external tools (e.g., an IDE, a chat app)
- **MCP Client**: the component inside the host that speaks the MCP protocol
- **MCP Server**: an independent process exposing specific capabilities (filesystem, database, GitHub API, etc.)

```
┌─────────────────────────┐
│   Host (e.g. IDE)       │
│  ┌───────────────────┐  │
│  │   LLM             │  │
│  │   MCP Client      │◄─┼──► MCP Server A (filesystem)
│  └───────────────────┘  │◄──► MCP Server B (GitHub)
└─────────────────────────┘◄───► MCP Server C (database)
```

The LLM never directly calls external tools. It asks the MCP Client, which routes the request to the right server. This separation keeps the model isolated from transport details.

## The three primitives

Every MCP server exposes up to three types of capabilities:

**Resources** — read-only data the model can access
- Files, database records, API responses
- The model can browse and read, but not modify
- Example: `file://project/src/main.py`

**Tools** — functions the model can call to take action
- Write to a file, run a shell command, send an API request
- These have side effects — they change the world
- Example: `run_tests()`, `create_github_issue()`

**Prompts** — reusable, parameterized prompt templates
- Predefined workflows the user can invoke
- Example: a "code review" prompt template that automatically loads the diff + runs relevant tests

## Why it matters

### For developers building AI features

Before MCP, adding "AI that can read your codebase" to your product meant writing a custom file reader, chunker, search index, and wiring it all to your model. With MCP, you expose a filesystem MCP server and any compliant AI client immediately has access — no custom integration.

### For the agent ecosystem

The arxiv study "How are AI agents used? Evidence from 177,000 MCP tools" (2026) analyzed 177,436 real-world MCP tools created between November 2024 and February 2026. Key findings:

- **67% of all tools are for software development** (90% of downloads)
- **Action tools grew from 27% to 65%** of the ecosystem over 16 months — agents are increasingly modifying external state, not just reading it
- Most action tools handle medium-stakes tasks (file editing), but high-stakes tasks (financial transactions) are emerging

This tells you where the ecosystem is right now: primarily dev tooling, but moving fast toward general-purpose agents with real-world consequences.

### For AI governance

The same study notes that monitoring at the **tool layer** is more tractable for regulation than monitoring at the model output layer. If you want to understand what AI agents are actually doing in the world, MCP's explicit primitives (resources/tools/prompts) give you clear audit points.

## In practice

Setting up a minimal MCP server in Python:

```python
from mcp.server import MCPServer
from mcp.types import Tool, TextContent

server = MCPServer("my-server")

@server.tool("read_file")
def read_file(path: str) -> TextContent:
    """Read a file from the filesystem."""
    with open(path) as f:
        return TextContent(text=f.read())

@server.tool("write_file")
def write_file(path: str, content: str) -> TextContent:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)
    return TextContent(text=f"Written to {path}")

server.run()
```

The MCP client (your AI host) discovers these tools automatically via the protocol handshake. The LLM receives their descriptions and can call them by name.

## The MCP ecosystem

The community registry at [modelcontextprotocol.io](https://modelcontextprotocol.io) lists hundreds of production MCP servers. Common categories:

- **Developer tools**: filesystem, Git, GitHub, terminal, code execution
- **Data sources**: databases (SQLite, PostgreSQL), APIs (Slack, Notion, Google Drive)
- **Web**: browser automation, web scraping, search
- **Observability**: logs, metrics, traces

The MCP Inspector (included in the org) lets you visually test and debug any MCP server before wiring it to a real AI client.

<!-- LANG:FR -->

## Qu'est-ce que MCP ?

MCP (Model Context Protocol) est un standard ouvert qui définit comment les applications IA se connectent à des sources de données et des outils externes. C'est le USB-C de l'IA : au lieu que chaque application construise ses propres connecteurs sur mesure pour chaque outil, MCP fournit un protocole unique que n'importe quel client et serveur compatible peut parler.

Avant MCP, chaque IDE piloté par IA, chaque interface de chat ou workflow devait construire des connecteurs ad hoc pour chaque ressource externe — filesystem, bases de données, APIs, interpréteurs de code. C'était du travail en double et un cauchemar à maintenir. MCP résout ça avec une couche de protocole partagée.

Gouverné par la **Linux Foundation** (pas propriétaire d'Anthropic), MCP est un standard communautaire avec des SDKs officiels dans 10 langages : TypeScript, Python, Java, Kotlin, C#, Go, PHP, Ruby, Rust, et Swift.

## Architecture

MCP suit un **modèle client-serveur** avec trois rôles :

- **MCP Host** : l'application qui veut utiliser l'IA + des outils externes (ex : un IDE, une app de chat)
- **MCP Client** : le composant dans le host qui parle le protocole MCP
- **MCP Server** : un processus indépendant qui expose des capacités spécifiques (filesystem, base de données, API GitHub, etc.)

```
┌─────────────────────────┐
│   Host (ex. IDE)        │
│  ┌───────────────────┐  │
│  │   LLM             │  │
│  │   MCP Client      │◄─┼──► MCP Server A (filesystem)
│  └───────────────────┘  │◄──► MCP Server B (GitHub)
└─────────────────────────┘◄───► MCP Server C (base de données)
```

Le LLM n'appelle jamais directement les outils externes. Il demande au MCP Client, qui route la requête vers le bon serveur. Cette séparation isole le modèle des détails de transport.

## Les trois primitives

Chaque serveur MCP expose jusqu'à trois types de capacités :

**Resources** — données en lecture seule que le modèle peut consulter
- Fichiers, enregistrements de base de données, réponses d'API
- Le modèle peut parcourir et lire, mais pas modifier
- Exemple : `file://projet/src/main.py`

**Tools** — fonctions que le modèle peut appeler pour agir
- Écrire dans un fichier, exécuter une commande shell, envoyer une requête API
- Ces opérations ont des effets de bord — elles changent l'état du monde
- Exemple : `run_tests()`, `create_github_issue()`

**Prompts** — templates de prompts paramétrés et réutilisables
- Workflows prédéfinis que l'utilisateur peut invoquer
- Exemple : un template "code review" qui charge automatiquement le diff + lance les tests pertinents

## Pourquoi c'est important

### Pour les développeurs qui construisent des features IA

Avant MCP, ajouter "une IA qui peut lire ta codebase" à ton produit signifiait écrire un lecteur de fichiers custom, un chunker, un index de recherche, et tout câbler à ton modèle. Avec MCP, tu exposes un serveur MCP filesystem et n'importe quel client IA compatible y a immédiatement accès — sans intégration sur mesure.

### Pour l'écosystème des agents

L'étude arxiv "How are AI agents used? Evidence from 177,000 MCP tools" (2026) a analysé 177 436 tools MCP réels créés entre novembre 2024 et février 2026. Résultats clés :

- **67% des tools concernent le software development** (90% des downloads)
- **Les action tools sont passés de 27% à 65%** de l'écosystème en 16 mois — les agents modifient de plus en plus l'état externe, pas seulement la lecture
- La plupart des action tools gèrent des tâches à enjeux modérés (édition de fichiers), mais les tâches à enjeux élevés (transactions financières) émergent

Ça te dit où en est l'écosystème aujourd'hui : principalement du dev tooling, mais qui évolue rapidement vers des agents généraux aux conséquences réelles.

### Pour la gouvernance de l'IA

La même étude note que le monitoring au **niveau de la couche tool** est plus praticable pour la régulation que le monitoring au niveau du model output. Si tu veux comprendre ce que les agents IA font concrètement dans le monde, les primitives explicites de MCP (resources/tools/prompts) donnent des points d'audit clairs.

## En pratique

Mettre en place un serveur MCP minimal en Python :

```python
from mcp.server import MCPServer
from mcp.types import Tool, TextContent

server = MCPServer("mon-serveur")

@server.tool("read_file")
def read_file(path: str) -> TextContent:
    """Lire un fichier depuis le filesystem."""
    with open(path) as f:
        return TextContent(text=f.read())

@server.tool("write_file")
def write_file(path: str, content: str) -> TextContent:
    """Écrire du contenu dans un fichier."""
    with open(path, "w") as f:
        f.write(content)
    return TextContent(text=f"Écrit dans {path}")

server.run()
```

Le client MCP (ton host IA) découvre ces tools automatiquement via le handshake du protocole. Le LLM reçoit leurs descriptions et peut les appeler par nom.

## L'écosystème MCP

Le registry communautaire sur [modelcontextprotocol.io](https://modelcontextprotocol.io) liste des centaines de serveurs MCP en production. Catégories principales :

- **Outils développeur** : filesystem, Git, GitHub, terminal, exécution de code
- **Sources de données** : bases de données (SQLite, PostgreSQL), APIs (Slack, Notion, Google Drive)
- **Web** : automatisation navigateur, scraping, recherche
- **Observabilité** : logs, métriques, traces

Le MCP Inspector (inclus dans l'org) permet de tester et déboguer visuellement n'importe quel serveur MCP avant de le câbler à un vrai client IA.
