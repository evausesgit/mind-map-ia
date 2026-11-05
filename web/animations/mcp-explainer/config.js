/*
 * MCP Explainer — editable configuration
 * ---------------------------------------
 * Everything the audience sees or feels is defined here: labels, the worked
 * example, the architecture components and the timings. The engine
 * (explainer.js) reads this object and builds the animation from it.
 *
 * Tips
 *  - `speed` scales the whole animation (1.2 = 20% faster).
 *  - Timings are in seconds, before `speed` is applied.
 *  - Keep labels short: they are rendered on a 1920×1080 stage.
 *  - Lists (systems, apps, calls, final stack) can grow or shrink; layouts
 *    are computed from their length.
 */
window.MCP_EXPLAINER_CONFIG = {
  title: "From AI Assistant to Enterprise Agent",

  speed: 1,

  theme: {
    bg: "#05070B",
    bgGlow: "#0E1522",
    text: "#EEF2F7",
    muted: "#8B94A5",
    faint: "#454D5C",
    line: "rgba(255,255,255,0.13)",
    surface: "rgba(255,255,255,0.035)",
    surfaceSolid: "#0B0F16",
    request: "#7EA6FF",      // user requests, agent
    orchestrator: "#A594FF", // harness / orchestrator
    mcp: "#3DD6C6",          // MCP layer, tool calls
    data: "#F2C46D",         // data flowing back
    positive: "#34D399",
    warn: "#F27A7A",
    font: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace",
  },

  // Scene chapters (used by the eyebrow label and the player's chapter bar)
  scenes: [
    { id: "request",   label: "The request" },
    { id: "stack",     label: "The agentic stack" },
    { id: "problem",   label: "The problem" },
    { id: "mcp",       label: "Enter MCP" },
    { id: "ecosystem", label: "Cash Equity MCP ecosystem" },
    { id: "result",    label: "The result" },
    { id: "server",    label: "Inside an MCP server" },
    { id: "lifecycle", label: "From build to run" },
    { id: "why",       label: "Why MCP matters" },
    { id: "final",     label: "Summary" },
  ],

  // ── Architecture ──────────────────────────────────────────────────────────
  user: { label: "TRADER", sublabel: "Cash Equity desk" },
  agent: { label: "CASH EQUITY AGENT" },
  orchestrator: { label: "AGENTIC HARNESS  ·  ORCHESTRATOR" },

  // Four capabilities placed around the orchestrator (diagonals, clockwise
  // from top-left). `glyph`: hex | stack | grid | plug | dot
  capabilities: [
    { id: "model",  label: "MODEL",  glyph: "hex" },
    { id: "skills", label: "SKILLS", glyph: "grid" },
    { id: "tools",  label: "TOOLS",  glyph: "plug" },
    { id: "memory", label: "MEMORY", glyph: "stack" },
  ],

  // Non-sequential orchestration moves shown in scene 2.
  // `tone`: "normal" | "alert" (alert keeps the capability highlighted)
  orchestration: [
    { cap: "model",  tag: "Selects a model" },
    { cap: "memory", tag: "Retrieves desk context" },
    { cap: "skills", tag: "Invokes a skill" },
    { cap: "memory", tag: "Recalls client coverage" },
    { cap: "tools",  tag: "External data required", tone: "alert" },
  ],

  mcp: {
    title: "MCP",
    subtitle: "MODEL CONTEXT PROTOCOL",
    verbs: ["DISCOVER", "CALL", "RETURN"],
  },

  // Enterprise systems exposed through MCP (scene 4/5)
  systems: [
    { id: "market",   label: "MARKET DATA",         sub: "KDB+ tick store" },
    { id: "crm",      label: "CLIENT INTELLIGENCE", sub: "CRM" },
    { id: "research", label: "RESEARCH",            sub: "Equity research" },
    { id: "news",     label: "NEWS",                sub: "Real-time feeds" },
    { id: "exec",     label: "ORDER & EXECUTION",   sub: "OMS · EMS" },
    { id: "docs",     label: "INTERNAL DOCUMENTS",  sub: "Policies · playbooks" },
  ],

  // ── The worked example ────────────────────────────────────────────────────
  example: {
    prompt: "What is happening on NVIDIA, and which of my clients may be interested?",
    promptMeta: "TRADER  ·  08:02",
    promptShort: "“What is happening on NVIDIA…?”",
    loop: ["Understand", "Plan", "Act", "Answer"],
    needs: ["I need market context.", "I need recent information.", "I need client relevance."],
    plan: ["Market context required", "News / research required", "Client relevance required"],

    // Tool calls. `plan` = index in the plan list above.
    calls: [
      {
        plan: 0,
        targets: [
          { system: "market", call: "market.snapshot(\"NVDA\")", returns: "NVDA ▲4.2%  ·  Vol 1.8× ADV" },
        ],
      },
      {
        plan: 1,
        targets: [
          { system: "research", call: "research.latest(\"Semis\")", returns: "Sector upgrade" },
          { system: "news",     call: "news.search(\"NVIDIA\")",    returns: "AI infra announcement" },
        ],
      },
      {
        plan: 2,
        targets: [
          { system: "crm", call: "crm.clients_exposed(\"NVDA\")", returns: "2 clients · semis interest" },
        ],
      },
    ],

    result: {
      instrument: "NVIDIA",
      ticker: "NVDA  ·  intraday",
      move: "+4.2%",
      sections: [
        { title: "KEY DRIVERS", items: ["Semiconductor sector rally", "New AI infrastructure announcement"] },
        { title: "RELEVANT CLIENTS", items: [
          { text: "Client A", note: "overweight semis" },
          { text: "Client B", note: "recent NVDA enquiry" },
        ] },
        { title: "SUGGESTED ACTION", items: ["Contact Client A with a tailored market update"], accent: true },
      ],
      sourcesLabel: "SOURCES VIA MCP",
      sources: ["KDB", "RESEARCH", "NEWS", "CRM"],
    },
  },

  // ── Scene 7: inside one MCP server ────────────────────────────────────────
  // Layers are listed left (agent side) to right (data side); `revealOrder`
  // introduces them from the data outwards. `tone` picks a theme colour.
  // `glyph`: key | shield | doc | stack | hex | grid | plug | dot
  server: {
    title: "INSIDE AN MCP SERVER",
    subtitle: "client-intelligence  ·  exposes the CRM",
    focusSystem: "crm",
    envelope: "MCP SERVER",
    agent: { label: "AGENT", sub: "for the trader" },
    system: { label: "CRM", sub: "Client data" },
    runtimeLabel: "RUNS INSIDE YOUR ARCHITECTURE",
    runtime: ["CONTAINER · K8S", "MCP GATEWAY", "SECRETS VAULT", "LOGS · TRACES"],
    layers: [
      { id: "identity",   label: "IDENTITY & ACCESS", glyph: "key",    tone: "request",
        items: ["OAuth · the user’s token", "Acts on behalf of the user", "Entitlements per client"] },
      { id: "guardrails", label: "GUARDRAILS",        glyph: "shield", tone: "orchestrator",
        items: ["Input schema validation", "Read-only · rate-limited", "PII masked on output"] },
      { id: "context",    label: "DATA CONTEXT",      glyph: "doc",    tone: "mcp",
        items: ["Clear tool descriptions", "Typed schemas · field meaning", "Business glossary · units"] },
      { id: "access",     label: "DATA ACCESS MODEL", glyph: "stack",  tone: "data",
        items: ["Approved views, not tables", "Parameterised queries only", "Row-level filtering"] },
    ],
    revealOrder: ["access", "context", "guardrails", "identity"],
    allowed: {
      call: "crm.clients_exposed(\"NVDA\")",
      checks: { identity: "✓ trader · 12 clients", guardrails: "✓ read-only · valid", context: "✓ tool understood", access: "✓ v_client_exposure" },
      maskAt: "guardrails",
      returns: "2 clients · PII masked",
    },
    denied: { call: "crm.export_all_clients()", at: "identity", reason: "✕ not entitled" },
    captions: {
      intro: "Behind every tool call sits an MCP server, engineered like any enterprise service.",
      runtime: "It runs inside your architecture: your network, your gateway, your secrets.",
      layers: {
        access: "A data access model defines what can be read, and how.",
        context: "Context describes the data, so the model knows what it means.",
        guardrails: "Guardrails bound what goes in and what comes out.",
        identity: "Every call carries the user’s identity and is checked against their rights.",
      },
      allowed: "An authorised call passes every layer, and leaves an audit trail.",
      denied: "Outside the user’s entitlements? The call stops at the gate.",
    },
  },

  // ── Scene 8: from build to run ────────────────────────────────────────────
  // `glyph`: code | check | chain | deploy | pulse. A stage `caption` stays on
  // screen until the next stage that has one.
  lifecycle: {
    title: "FROM BUILD TO RUN",
    subtitle: "the lifecycle of an MCP server",
    stages: [
      { id: "build", label: "BUILD", glyph: "code", status: "v1.3.0",
        items: ["Tools, schemas, descriptions", "Access rules & guardrails as code"],
        caption: "An MCP server is software. It ships like software." },
      { id: "unit", label: "UNIT TESTS", glyph: "check", status: "148 / 148 passed",
        items: ["Each tool in isolation", "Schemas, permissions, edge cases", "Mocked data sources"],
        caption: "Unit-test every tool on its own…" },
      { id: "integration", label: "INTEGRATION TESTS", glyph: "chain", status: "36 scenarios passed",
        items: ["Agent ↔ server ↔ real systems", "Entitlements end-to-end", "Evals: right tool, right answer"],
        caption: "…then test the whole chain, with real identities and rights." },
      { id: "deploy", label: "DEPLOY", glyph: "deploy", status: "v1.3.0 · live",
        items: ["CI/CD · versioned releases", "Staging → production", "Registered in the MCP gateway"],
        caption: "Ship it through CI/CD, like any production service." },
      { id: "monitor", label: "MONITOR", glyph: "pulse", status: "SLO 99.9% met",
        items: ["Latency · errors · usage", "Denied calls · audit trail", "Drift & cost alerts"],
        caption: "Then watch every call in production." },
    ],
    loopLabel: "FEEDBACK LOOP",
    loopCaption: "What you observe feeds the next version.",
    dashboard: {
      title: "PRODUCTION  ·  client-intelligence MCP",
      live: "LIVE",
      kpis: [
        { label: "P95 LATENCY",  value: "180 ms" },
        { label: "CALLS TODAY",  value: "12.4k" },
        { label: "DENIED CALLS", value: "0.3%", tone: "warn" },
        { label: "ERROR RATE",   value: "0.1%", tone: "positive" },
      ],
      spark: "TOOL CALLS / MIN",
    },
  },

  // ── Scene 9: many agents, one MCP layer ───────────────────────────────────
  multiAgent: {
    apps: [
      { id: "sales",    label: "SALES AGENT" },
      { id: "trading",  label: "TRADING AGENT" },
      { id: "research", label: "RESEARCH AGENT" },
      { id: "mgmt",     label: "MANAGEMENT COPILOT" },
    ],
    layerLabel: "MCP LAYER",
    systems: ["KDB", "CRM", "RESEARCH", "NEWS", "EXECUTION DATA", "DOCUMENTS"],
    focusApp: "sales",
  },

  // ── Final frame ───────────────────────────────────────────────────────────
  finalStack: [
    { items: ["USER"] },
    { items: ["CASH EQUITY AGENT"], tone: "request" },
    { items: ["AGENTIC HARNESS  /  ORCHESTRATOR"], tone: "orchestrator", wide: true },
    { items: ["MODELS", "MEMORY", "SKILLS", "MCP"], highlight: "MCP" },
    { items: ["MARKET DATA", "CLIENT DATA", "RESEARCH", "EXECUTION", "INTERNAL SYSTEMS"], viaMcp: true },
  ],
  finalTitle: "FROM AI ASSISTANT TO ENTERPRISE AGENT",
  finalSubtitle: "MCP connects AI reasoning to enterprise tools and data: governed, tested, monitored.",

  // ── On-screen captions ────────────────────────────────────────────────────
  captions: {
    s1: "An agent doesn’t just answer. It reasons about what to do next.",
    s2: "The agent reasons. The orchestrator coordinates.",
    s3Question: ["How does an AI application securely connect", "to enterprise tools and data?"],
    s4: "MCP provides a standard way for AI applications to connect to tools and data.",
    s4Sub: "A universal interface, not another model.",
    s5Steps: ["Agent decides what it needs", "MCP gives standard access", "Data returns", "Agent combines the results"],
    s6: "One question. Four systems. A single, sourced answer.",
    s7Tangle: "Without a standard, every agent rebuilds every integration.",
    s7TangleSub: "4 agents × 6 systems = 24 bespoke integrations",
    s7Once: ["Build the integration once.", "Reuse it across agents."],
    s7OnceSub: "4 + 6 = 10 standard connections",
    s7One: "One agent. Many enterprise capabilities.",
    s7Final: "MCP connects intelligence to the enterprise.",
  },

  // ── Timings (seconds, before `speed`) ─────────────────────────────────────
  timing: {
    s1: { intro: 1.4, typing: 3.0, readHold: 1.0, send: 1.3, loopStep: 0.75, hold: 3.2 },
    s2: { zoom: 2.4, ring: 1.4, captionHold: 2.6, capStagger: 0.3, move: 1.25, hold: 1.6 },
    s3: { needStagger: 0.9, reach: 1.6, questionHold: 4.2 },
    s4: { build: 1.8, ports: 1.0, captionHold: 3.4, connect: 2.2, discover: 1.8 },
    s5: { labels: 1.6, replay: 2.0, planStagger: 0.55, call: 1.25, dataBack: 1.35, callGap: 1.5, combine: 2.4 },
    s6: { build: 3.2, deliver: 1.8, hold: 3.6 },
    server: { zoom: 2.2, introHold: 2.8, envelope: 1.6, runtimeHold: 3.0, layer: 3.8, pass: 2.6, back: 1.9, deny: 1.0, denyHold: 2.8, hold: 1.0 },
    lifecycle: { stage: 2.8, travel: 0.7, spark: 2.4, dashboard: 4.2, loop: 1.8, hold: 2.6 },
    s7: { zoom: 2.4, build: 2.0, tangle: 2.0, tangleHold: 2.6, resolve: 2.2, onceHold: 3.4, oneAgent: 4.2, finalHold: 3.4 },
    final: { build: 3.6, titleHold: 6.0 },
  },
};

/*
 * French text, laid over the English config above when the page runs with
 * lang=fr (see mergeLocale). Only text lives here: ids, glyphs, tones and
 * timings come from the English config. Arrays are merged item by item, so
 * keep the same order and length as above.
 */
window.MCP_EXPLAINER_CONFIG_FR = {
  title: "De l’assistant IA à l’agent d’entreprise",

  scenes: [
    { label: "La demande" },
    { label: "La stack agentique" },
    { label: "Le problème" },
    { label: "Voici MCP" },
    { label: "L’écosystème MCP Cash Equity" },
    { label: "Le résultat" },
    { label: "Dans un serveur MCP" },
    { label: "Du build au run" },
    { label: "Pourquoi MCP compte" },
    { label: "Synthèse" },
  ],

  user: { label: "TRADER", sublabel: "Desk Cash Equity" },
  agent: { label: "AGENT CASH EQUITY" },
  orchestrator: { label: "HARNESS AGENTIQUE  ·  ORCHESTRATEUR" },

  capabilities: [
    { label: "MODÈLE" },
    { label: "SKILLS" },
    { label: "OUTILS" },
    { label: "MÉMOIRE" },
  ],

  orchestration: [
    { tag: "Choisit un modèle" },
    { tag: "Récupère le contexte du desk" },
    { tag: "Invoque un skill" },
    { tag: "Rappelle la couverture client" },
    { tag: "Données externes requises" },
  ],

  mcp: { verbs: ["DÉCOUVRIR", "APPELER", "RENVOYER"] },

  systems: [
    { label: "DONNÉES DE MARCHÉ",   sub: "Base tick KDB+" },
    { label: "INTELLIGENCE CLIENT", sub: "CRM" },
    { label: "RECHERCHE",           sub: "Recherche actions" },
    { label: "ACTUALITÉS",          sub: "Flux temps réel" },
    { label: "ORDRES & EXÉCUTION",  sub: "OMS · EMS" },
    { label: "DOCUMENTS INTERNES",  sub: "Politiques · procédures" },
  ],

  example: {
    prompt: "Que se passe-t-il sur NVIDIA, et lesquels de mes clients pourraient être intéressés ?",
    promptShort: "« Que se passe-t-il sur NVIDIA… ? »",
    loop: ["Comprendre", "Planifier", "Agir", "Répondre"],
    needs: ["Il me faut le contexte de marché.", "Il me faut l’actualité récente.", "Il me faut les clients concernés."],
    plan: ["Contexte de marché requis", "Actualités / recherche requises", "Pertinence client requise"],
    calls: [
      { targets: [{ returns: "NVDA ▲4,2 %  ·  Vol 1,8× ADV" }] },
      { targets: [{ returns: "Relèvement du secteur" }, { returns: "Annonce infra IA" }] },
      { targets: [{ returns: "2 clients · intérêt semis" }] },
    ],
    result: {
      ticker: "NVDA  ·  en séance",
      move: "+4,2 %",
      sections: [
        { title: "FACTEURS CLÉS", items: ["Rallye des semi-conducteurs", "Nouvelle annonce d’infrastructure IA"] },
        { title: "CLIENTS CONCERNÉS", items: [
          { note: "surpondéré semis" },
          { note: "demande récente sur NVDA" },
        ] },
        { title: "ACTION SUGGÉRÉE", items: ["Appeler le client A avec un point marché dédié"] },
      ],
      sourcesLabel: "SOURCES VIA MCP",
      sources: ["KDB", "RECHERCHE", "ACTUALITÉS", "CRM"],
    },
  },

  server: {
    title: "DANS UN SERVEUR MCP",
    subtitle: "client-intelligence  ·  expose le CRM",
    envelope: "SERVEUR MCP",
    agent: { sub: "pour le trader" },
    system: { sub: "Données clients" },
    runtimeLabel: "TOURNE DANS VOTRE ARCHITECTURE",
    runtime: ["CONTENEUR · K8S", "PASSERELLE MCP", "COFFRE DE SECRETS", "LOGS · TRACES"],
    layers: [
      { label: "IDENTITÉ & ACCÈS",
        items: ["OAuth · jeton de l’utilisateur", "Agit au nom de l’utilisateur", "Droits par client"] },
      { label: "GARDE-FOUS",
        items: ["Validation du schéma d’entrée", "Lecture seule · débit limité", "Données perso masquées"] },
      { label: "CONTEXTE DES DONNÉES",
        items: ["Descriptions d’outils claires", "Schémas typés · champs", "Glossaire métier · unités"] },
      { label: "MODÈLE D’ACCÈS",
        items: ["Vues validées, pas de tables", "Requêtes paramétrées", "Filtrage par ligne"] },
    ],
    allowed: {
      checks: { guardrails: "✓ lecture seule · valide", context: "✓ outil compris" },
      returns: "2 clients · anonymisés",
    },
    denied: { reason: "✕ non autorisé" },
    captions: {
      intro: "Derrière chaque appel d’outil, un serveur MCP, conçu comme tout service d’entreprise.",
      runtime: "Il tourne dans votre architecture : votre réseau, votre passerelle, vos secrets.",
      layers: {
        access: "Un modèle d’accès aux données définit ce qui peut être lu, et comment.",
        context: "Le contexte décrit les données, pour que le modèle sache ce qu’elles signifient.",
        guardrails: "Des garde-fous encadrent ce qui entre et ce qui sort.",
        identity: "Chaque appel porte l’identité de l’utilisateur et respecte ses droits.",
      },
      allowed: "Un appel autorisé traverse chaque couche, et laisse une piste d’audit.",
      denied: "Hors des droits de l’utilisateur ? L’appel s’arrête à l’entrée.",
    },
  },

  lifecycle: {
    title: "DU BUILD AU RUN",
    subtitle: "le cycle de vie d’un serveur MCP",
    stages: [
      { items: ["Outils, schémas, descriptions", "Règles d’accès & garde-fous en code"],
        caption: "Un serveur MCP est un logiciel. Il se livre comme un logiciel." },
      { label: "TESTS UNITAIRES", status: "148 / 148 réussis",
        items: ["Chaque outil isolément", "Schémas, droits, cas limites", "Sources de données simulées"],
        caption: "Tester chaque outil isolément…" },
      { label: "TESTS D’INTÉGRATION", status: "36 scénarios réussis",
        items: ["Agent ↔ serveur ↔ vrais systèmes", "Droits de bout en bout", "Évals : bon outil, bonne réponse"],
        caption: "…puis toute la chaîne, avec de vraies identités et de vrais droits." },
      { label: "DÉPLOIEMENT", status: "v1.3.0 · en prod",
        items: ["CI/CD · versions publiées", "Recette → production", "Inscrit dans la passerelle MCP"],
        caption: "Le livrer en CI/CD, comme tout service de production." },
      { label: "SUPERVISION", status: "SLO 99,9 % tenu",
        items: ["Latence · erreurs · usage", "Appels refusés · piste d’audit", "Alertes dérive & coûts"],
        caption: "Puis surveiller chaque appel en production." },
    ],
    loopLabel: "BOUCLE DE RETOUR",
    loopCaption: "Ce que l’on observe nourrit la version suivante.",
    dashboard: {
      title: "PRODUCTION  ·  MCP client-intelligence",
      live: "EN DIRECT",
      kpis: [
        { label: "LATENCE P95" },
        { label: "APPELS DU JOUR", value: "12,4k" },
        { label: "APPELS REFUSÉS", value: "0,3 %" },
        { label: "TAUX D’ERREUR",  value: "0,1 %" },
      ],
      spark: "APPELS D’OUTILS / MIN",
    },
  },

  multiAgent: {
    apps: [
      { label: "AGENT VENTE" },
      { label: "AGENT TRADING" },
      { label: "AGENT RECHERCHE" },
      { label: "COPILOTE MANAGEMENT" },
    ],
    layerLabel: "COUCHE MCP",
    systems: ["KDB", "CRM", "RECHERCHE", "ACTUALITÉS", "EXÉCUTION", "DOCUMENTS"],
  },

  finalStack: [
    { items: ["UTILISATEUR"] },
    { items: ["AGENT CASH EQUITY"] },
    { items: ["HARNESS AGENTIQUE  /  ORCHESTRATEUR"] },
    { items: ["MODÈLES", "MÉMOIRE", "SKILLS", "MCP"] },
    { items: ["DONNÉES DE MARCHÉ", "DONNÉES CLIENTS", "RECHERCHE", "EXÉCUTION", "SYSTÈMES INTERNES"] },
  ],
  finalTitle: "DE L’ASSISTANT IA À L’AGENT D’ENTREPRISE",
  finalSubtitle: "MCP relie le raisonnement de l’IA aux outils et aux données de l’entreprise : gouverné, testé, supervisé.",

  captions: {
    s1: "Un agent ne se contente pas de répondre. Il réfléchit à la suite.",
    s2: "L’agent raisonne. L’orchestrateur coordonne.",
    s3Question: ["Comment une application d’IA se connecte-t-elle", "en sécurité aux outils et données de l’entreprise ?"],
    s4: "MCP offre aux applications d’IA un moyen standard d’accéder aux outils et aux données.",
    s4Sub: "Une interface universelle, pas un modèle de plus.",
    s5Steps: ["L’agent décide ce dont il a besoin", "MCP donne un accès standard", "Les données reviennent", "L’agent combine les résultats"],
    s6: "Une question. Quatre systèmes. Une seule réponse sourcée.",
    s7Tangle: "Sans standard, chaque agent refait chaque intégration.",
    s7TangleSub: "4 agents × 6 systèmes = 24 intégrations sur mesure",
    s7Once: ["Construire l’intégration une fois.", "La réutiliser entre agents."],
    s7OnceSub: "4 + 6 = 10 connexions standard",
    s7One: "Un agent. De nombreuses capacités d’entreprise.",
    s7Final: "MCP connecte l’intelligence à l’entreprise.",
  },
};

/*
 * Lay a locale over the base config: objects merge key by key, arrays item by
 * item, strings replace. French spaces before ? : ; ! % » become no-break
 * spaces so the punctuation never wraps onto its own line.
 */
window.mergeLocale = function mergeLocale(base, over) {
  if (typeof over === "string") return over.replace(/ ([?:;!%»])/g, " $1").replace(/« /g, "« ");
  if (Array.isArray(over)) {
    const out = Array.isArray(base) ? base.slice() : [];
    over.forEach((v, i) => { out[i] = mergeLocale(out[i], v); });
    return out;
  }
  if (over && typeof over === "object") {
    const out = base && typeof base === "object" && !Array.isArray(base) ? { ...base } : {};
    for (const k of Object.keys(over)) out[k] = mergeLocale(out[k], over[k]);
    return out;
  }
  return over;
};
