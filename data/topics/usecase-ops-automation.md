---
id: usecase-ops-automation
title:
  en: "Use Case: Ops Workflow Automation"
  fr: "Cas d'Usage : Automatisation de Workflows Ops"
summary:
  en: "How autonomous agents handle multi-step operational processes — incident triage, pipeline orchestration, and the human-in-the-loop model."
  fr: "Comment des agents autonomes gèrent des processus opérationnels multi-étapes — triage d'incidents, orchestration de pipelines, et le modèle humain dans la boucle."
tags: [agents, ops, automation, multi-agent, orchestration, incident-response]
related_terms: [agent, tool_use, multi_agent, orchestration]
related_nodes: [uc-ops-workflow, pattern-agent-loop, pattern-multiagent, stack-tools, stack-orchestrator]
status: evolving
date: 2026-04-06
sources: []
---

<!-- LANG:EN -->

## The scenario

An on-call engineer gets paged at 2am. A data pipeline has failed. Normally, they'd open a terminal, check logs, identify the broken step, re-run it with corrected parameters, monitor the recovery, update the incident ticket, and notify stakeholders.

With an AI-powered ops agent: the alert triggers an agent that reads the logs, identifies the root cause, attempts standard remediation, monitors recovery, updates the ticket automatically, and pages a human only if the automated fix fails or if the situation escalates.

This is **ops workflow automation**: agents taking over the toil while keeping humans accountable for the decisions that matter.

## The spectrum of automation

Ops automation exists on a spectrum from purely reactive (humans do everything) to fully autonomous:

```
Manual         →    Assisted         →    Semi-autonomous    →    Autonomous
Human reads    →    AI suggests       →    AI acts,           →    AI acts end-to-end,
logs, acts          next action            human approves          notifies humans
                                           key steps              on completion
```

Most production deployments today sit at **semi-autonomous**: the agent handles the diagnosis and first-line response, but a human approves anything that touches production data or triggers a customer-facing change.

## Architecture: agent loop + tools

The agent loop for ops automation:

```
Trigger (alert / schedule / webhook)
    ↓
[LLM: Understand context]  →  reads alert data, selects relevant tools
    ↓
[LLM: Diagnose]  →  queries logs, metrics, trace data
    ↓
[LLM: Decide]  →  match to known failure patterns, pick remediation
    ↓
[LLM: Act]  →  calls remediation tool (restart service / re-run job / scale resource)
    ↓
[Monitor]  →  polls health checks, reads new logs
    ↓
[LLM: Evaluate]  →  is the issue resolved? escalate or close?
    ↓
[Report]  →  updates ticket, notifies stakeholders
```

Key tools for ops agents:

| Tool | What it does |
|---|---|
| Log query | Search structured logs (Elasticsearch, Datadog, CloudWatch) |
| Metrics query | Fetch time-series data (Prometheus, Grafana, Datadog) |
| Trace lookup | Inspect distributed traces (Jaeger, Zipkin, Datadog APM) |
| Service restart | Restart a containerized service (Kubernetes, ECS) |
| Job re-run | Re-trigger a failed pipeline step |
| Ticket update | Write to JIRA, PagerDuty, Linear |
| Notification | Send Slack message, email, SMS |
| Runbook lookup | Retrieve the relevant runbook from the knowledge base |

## Multi-agent for complex incidents

Simple incidents (single service down, obvious error) can be handled by a single agent loop. Complex incidents require a **multi-agent** setup:

- **Orchestrator agent**: understands the high-level incident, decomposes it into parallel investigation threads
- **Diagnostic agents**: each investigates one subsystem (database, API layer, network, external dependencies)
- **Remediation agent**: aggregates findings, executes the fix
- **Communication agent**: writes the incident summary, updates the status page

This is particularly valuable for cascading failures where multiple systems are affected simultaneously.

## The runbook as structured memory

The most effective ops agents are grounded in **runbooks** — the organization's accumulated operational knowledge.

A runbook describes: the symptom, the likely root causes, and the step-by-step remediation. When the agent encounters an alert, it first retrieves the relevant runbook (via RAG over the runbook corpus), then executes the steps, adapting them to the specific instance.

This bridges the gap between AI capability and domain-specific operational knowledge. The agent doesn't need to infer how to restart a database replica from first principles — the runbook tells it exactly what to do and what to check afterward.

## Trust, control, and blast radius

Ops automation has higher stakes than coding assistance. A bad command in production can:
- Drop database connections for thousands of users
- Wipe data if a cleanup script has a bug
- Trigger a billing or compliance violation
- Start a cascading failure instead of stopping one

**Key control mechanisms:**

**Blast radius scoping.** Define upfront which actions the agent is allowed to take: can it restart services? Can it scale up? Can it delete anything? Anything outside this scope requires human approval.

**Dry-run mode.** Before executing any remediation, the agent outputs what it *would* do. The human approves, then the agent executes.

**Rollback checkpoints.** Before every state-changing action, take a snapshot or note the reversal command. If the action makes things worse, the agent can undo it.

**Rate limits on actions.** Prevent runaway agents from hammering a service with restart loops. Limit: max N restarts per M minutes.

**Escalation thresholds.** Define conditions that immediately hand off to a human: customer impact detected, SLA breach imminent, action not in the playbook, or confidence below threshold.

## Practical example: failed ETL job

```
01:47  Alert fires: "ETL job 'daily_revenue_aggregation' failed (exit code 1)"
       
01:47  Agent reads: job logs → "Error: connection timeout to source DB replica-2"

01:47  Agent queries: replica-2 health → "replica-2 lag: 2.3 hours (threshold: 30 min)"

01:48  Agent retrieves runbook: "ETL source timeout" 
       → runbook says: switch source to replica-1, re-run job

01:48  Agent checks: replica-1 health → "replica-1 lag: 4 minutes — OK"

01:49  Agent acts: updates ETL config (source → replica-1)
       → DRY RUN output shown in Slack: "Will update config and re-trigger job"
       → Auto-approved (within blast radius policy)

01:49  Agent acts: re-triggers ETL job

02:03  Agent monitors: job completes successfully

02:03  Agent reports:
       - Updates JIRA ticket: "Resolved — source switched to replica-1 (replica-2 lagging)"
       - Sends Slack: "ETL job recovered at 02:03. Replica-2 lag alert still open — DBAs notified."
       - Opens separate ticket for replica-2 lag investigation
```

Total time: 16 minutes, zero human intervention, two tickets created (resolution + follow-up).

## What agents can't (yet) handle well

**Novel failure modes.** Agents work best on patterns they've seen before (via runbooks or training). An entirely new failure type — one with no runbook, no similar precedent — requires human investigation.

**Cross-team coordination.** "This incident requires a change from the platform team and approval from security" — agents can draft the request, but the coordination itself requires humans.

**Judgment calls under uncertainty.** "Should we fail over to the DR region or wait to see if the primary recovers?" — this involves business impact assessment that goes beyond log reading.

**Explaining to customers.** Status page updates and customer communications require nuanced judgment about what to disclose, when, and how.

## Typical stack

| Layer | Examples |
|---|---|
| Trigger | PagerDuty, OpsGenie, custom webhook |
| Log/metrics | Datadog, Grafana + Prometheus, ELK, CloudWatch |
| Agent framework | LangGraph, CrewAI, custom |
| LLM | Claude 3.5/4 (reasoning), GPT-4o |
| Runbook store | Confluence + RAG, Notion + RAG, GitOps runbooks |
| Ticketing | JIRA, Linear, PagerDuty incidents |
| Notification | Slack, PagerDuty, email |

<!-- LANG:FR -->

## Le scénario

Un ingénieur d'astreinte est paginé à 2h du matin. Un pipeline de données a échoué. Normalement, il ouvrirait un terminal, consulterait les logs, identifierait l'étape cassée, la relancerait avec des paramètres corrigés, surveillerait la récupération, mettrait à jour le ticket d'incident, et notifierait les parties prenantes.

Avec un agent ops alimenté par IA : l'alerte déclenche un agent qui lit les logs, identifie la cause racine, tente une remédiation standard, surveille la récupération, met à jour le ticket automatiquement, et page un humain seulement si le correctif automatisé échoue ou si la situation s'aggrave.

C'est l'**automatisation de workflows ops** : des agents prenant en charge les tâches répétitives tout en maintenant les humains responsables des décisions qui comptent.

## Le spectre de l'automatisation

L'automatisation ops existe sur un spectre du purement réactif (les humains font tout) à l'entièrement autonome :

```
Manuel         →    Assisté          →    Semi-autonome      →    Autonome
Humain lit     →    L'IA suggère      →    L'IA agit,         →    L'IA agit de bout en bout,
logs, agit          l'action suivante      humain approuve         notifie les humains
                                           les étapes clés         à la fin
```

La plupart des déploiements en production aujourd'hui se situent au niveau **semi-autonome** : l'agent gère le diagnostic et la réponse de premier niveau, mais un humain approuve tout ce qui touche les données de production ou déclenche un changement visible par les clients.

## Architecture : boucle agent + outils

La boucle agent pour l'automatisation ops :

```
Déclencheur (alerte / planification / webhook)
    ↓
[LLM : Comprendre le contexte]  →  lit les données d'alerte, sélectionne les outils pertinents
    ↓
[LLM : Diagnostiquer]  →  interroge les logs, métriques, données de trace
    ↓
[LLM : Décider]  →  fait correspondre aux patterns de défaillance connus, choisit la remédiation
    ↓
[LLM : Agir]  →  appelle l'outil de remédiation (redémarrer service / relancer job / scaler ressource)
    ↓
[Surveiller]  →  interroge les health checks, lit les nouveaux logs
    ↓
[LLM : Évaluer]  →  le problème est-il résolu ? escalader ou fermer ?
    ↓
[Rapporter]  →  met à jour le ticket, notifie les parties prenantes
```

Outils clés pour les agents ops :

| Outil | Ce qu'il fait |
|---|---|
| Requête de logs | Recherche dans les logs structurés (Elasticsearch, Datadog, CloudWatch) |
| Requête de métriques | Récupère les données de séries temporelles (Prometheus, Grafana, Datadog) |
| Consultation de traces | Inspecte les traces distribuées (Jaeger, Zipkin, Datadog APM) |
| Redémarrage de service | Redémarre un service conteneurisé (Kubernetes, ECS) |
| Relance de job | Re-déclenche une étape de pipeline échouée |
| Mise à jour de ticket | Écrit dans JIRA, PagerDuty, Linear |
| Notification | Envoie un message Slack, email, SMS |
| Consultation de runbook | Récupère le runbook pertinent depuis la base de connaissance |

## Multi-agent pour les incidents complexes

Les incidents simples (un service down, erreur évidente) peuvent être gérés par une seule boucle agent. Les incidents complexes nécessitent une configuration **multi-agent** :

- **Agent orchestrateur** : comprend l'incident de haut niveau, le décompose en fils d'investigation parallèles
- **Agents de diagnostic** : chacun enquête sur un sous-système (base de données, couche API, réseau, dépendances externes)
- **Agent de remédiation** : agrège les findings, exécute le correctif
- **Agent de communication** : rédige le résumé d'incident, met à jour la page de statut

C'est particulièrement précieux pour les défaillances en cascade où plusieurs systèmes sont affectés simultanément.

## Le runbook comme mémoire structurée

Les agents ops les plus efficaces sont ancrés dans des **runbooks** — la connaissance opérationnelle accumulée de l'organisation.

Un runbook décrit : le symptôme, les causes racines probables, et la remédiation étape par étape. Quand l'agent rencontre une alerte, il récupère d'abord le runbook pertinent (via RAG sur le corpus de runbooks), puis exécute les étapes, en les adaptant à l'instance spécifique.

Cela comble le fossé entre la capacité IA et la connaissance opérationnelle spécifique au domaine. L'agent n'a pas besoin d'inférer comment redémarrer un réplica de base de données à partir de zéro — le runbook lui dit exactement quoi faire et quoi vérifier ensuite.

## Confiance, contrôle, et rayon de blast

L'automatisation ops a des enjeux plus élevés que l'assistance au coding. Une mauvaise commande en production peut :
- Couper les connexions de base de données pour des milliers d'utilisateurs
- Supprimer des données si un script de nettoyage a un bug
- Déclencher une violation de facturation ou de conformité
- Provoquer une défaillance en cascade au lieu de l'arrêter

**Mécanismes de contrôle clés :**

**Délimitation du rayon de blast.** Définir à l'avance quelles actions l'agent est autorisé à prendre : peut-il redémarrer des services ? Peut-il scaler ? Peut-il supprimer quelque chose ? Tout ce qui est hors périmètre nécessite une approbation humaine.

**Mode dry-run.** Avant d'exécuter toute remédiation, l'agent affiche ce qu'il *ferait*. L'humain approuve, puis l'agent exécute.

**Checkpoints de rollback.** Avant chaque action changeant l'état, prendre un snapshot ou noter la commande d'inversion. Si l'action aggrave les choses, l'agent peut l'annuler.

**Limites de taux sur les actions.** Empêcher les agents incontrôlés de marteler un service avec des boucles de redémarrage. Limite : max N redémarrages par M minutes.

**Seuils d'escalade.** Définir des conditions qui transfèrent immédiatement à un humain : impact client détecté, violation SLA imminente, action absente du playbook, ou confiance sous le seuil.

## Exemple pratique : job ETL échoué

```
01:47  Alerte : "Job ETL 'daily_revenue_aggregation' échoué (code sortie 1)"
       
01:47  L'agent lit : logs du job → "Erreur : timeout connexion vers DB source replica-2"

01:47  L'agent interroge : santé de replica-2 → "lag replica-2 : 2h3min (seuil : 30 min)"

01:48  L'agent récupère le runbook : "Timeout source ETL" 
       → runbook indique : basculer la source vers replica-1, relancer le job

01:48  L'agent vérifie : santé de replica-1 → "lag replica-1 : 4 minutes — OK"

01:49  L'agent agit : met à jour la config ETL (source → replica-1)
       → Sortie DRY RUN montrée dans Slack : "Mettra à jour la config et re-déclenchera le job"
       → Auto-approuvé (dans la politique de rayon de blast)

01:49  L'agent agit : re-déclenche le job ETL

02:03  L'agent surveille : le job se termine avec succès

02:03  L'agent rapporte :
       - Met à jour le ticket JIRA : "Résolu — source basculée sur replica-1 (replica-2 en retard)"
       - Envoie sur Slack : "Job ETL récupéré à 02:03. Alerte lag replica-2 toujours ouverte — DBAs notifiés."
       - Ouvre un ticket séparé pour l'investigation du lag replica-2
```

Temps total : 16 minutes, zéro intervention humaine, deux tickets créés (résolution + suivi).

## Ce que les agents ne gèrent pas encore bien

**Modes de défaillance nouveaux.** Les agents fonctionnent mieux sur des patterns qu'ils ont déjà vus (via les runbooks ou l'entraînement). Un type de défaillance entièrement nouveau — sans runbook, sans précédent similaire — nécessite une investigation humaine.

**Coordination inter-équipes.** "Cet incident nécessite un changement de l'équipe plateforme et une approbation de la sécurité" — les agents peuvent rédiger la demande, mais la coordination elle-même nécessite des humains.

**Jugements sous l'incertitude.** "Devrions-nous basculer sur la région DR ou attendre que le primaire récupère ?" — cela implique une évaluation d'impact métier qui dépasse la lecture de logs.

**Expliquer aux clients.** Les mises à jour de page de statut et les communications clients nécessitent un jugement nuancé sur quoi divulguer, quand, et comment.

## Stack typique

| Couche | Exemples |
|---|---|
| Déclencheur | PagerDuty, OpsGenie, webhook custom |
| Logs/métriques | Datadog, Grafana + Prometheus, ELK, CloudWatch |
| Framework agent | LangGraph, CrewAI, custom |
| LLM | Claude 3.5/4 (raisonnement), GPT-4o |
| Stockage runbooks | Confluence + RAG, Notion + RAG, runbooks GitOps |
| Ticketing | JIRA, Linear, incidents PagerDuty |
| Notification | Slack, PagerDuty, email |
