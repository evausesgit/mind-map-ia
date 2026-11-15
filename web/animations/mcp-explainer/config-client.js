/*
 * MCP Explainer — client version
 * -------------------------------
 * Same engine as config.js, told from the side of a client using the Cash
 * Equity platform: the question is about their own basket, the sources are
 * their own orders, market data and TCA, and the server scene shows that
 * they only ever reach their own data. The "build to run" scene is left out
 * (no `lifecycle` key), and a disclaimer badge stays on screen throughout.
 *
 * Load after config.js: it reuses its theme, timings and mergeLocale, then
 * replaces MCP_EXPLAINER_CONFIG and MCP_EXPLAINER_CONFIG_FR.
 * Voice-over cues: data/narration/mcp-agentic-architecture-client-{en,fr}.yaml.
 */
(function () {
  const base = window.MCP_EXPLAINER_CONFIG;

  window.MCP_EXPLAINER_CONFIG = {
    title: "From a Business Question to a Coordinated Answer",
    speed: 1,
    theme: base.theme,
    disclaimer: "FICTIONAL EXAMPLE  ·  FOR ILLUSTRATION ONLY",

    scenes: [
      { id: "request",   label: "The request" },
      { id: "stack",     label: "The agent’s building blocks" },
      { id: "problem",   label: "The problem" },
      { id: "mcp",       label: "Enter MCP" },
      { id: "ecosystem", label: "Your sources via MCP" },
      { id: "result",    label: "The result" },
      { id: "server",    label: "Controlled access" },
      { id: "why",       label: "Why MCP matters" },
      { id: "final",     label: "Summary" },
    ],

    user: { label: "YOU", sublabel: "Cash Equity platform" },
    agent: { label: "AI AGENT" },
    orchestrator: { label: "ORCHESTRATOR" },

    capabilities: [
      { id: "model",  label: "MODEL",  glyph: "hex" },
      { id: "skills", label: "SKILLS", glyph: "grid" },
      { id: "tools",  label: "TOOLS",  glyph: "plug" },
      { id: "memory", label: "MEMORY", glyph: "stack" },
    ],

    orchestration: [
      { cap: "model",  tag: "Interprets your request" },
      { cap: "memory", tag: "Recalls your report format" },
      { cap: "skills", tag: "Applies the TCA method" },
      { cap: "tools",  tag: "Your data required", tone: "alert" },
    ],

    mcp: base.mcp,

    systems: [
      { id: "orders", label: "YOUR ORDERS",    sub: "Orders · fills" },
      { id: "market", label: "MARKET DATA",    sub: "Prices · volumes · spreads" },
      { id: "tca",    label: "TCA ANALYTICS",  sub: "Benchmarks · slippage" },
      { id: "news",   label: "NEWS & EVENTS",  sub: "Market events" },
      { id: "ref",    label: "REFERENCE DATA", sub: "Instruments · calendars" },
      { id: "docs",   label: "DOCUMENTATION",  sub: "Algo guides" },
    ],

    example: {
      prompt: "Why did my basket underperform VWAP this morning?",
      promptMeta: "YOU  ·  11:45",
      promptShort: "“Why did my basket underperform…?”",
      loop: ["Understand", "Plan", "Act", "Answer"],
      needs: ["I need your orders and fills.", "I need the market context.", "I need a slippage calculation."],
      plan: ["Your orders & fills required", "Market context required", "Slippage vs VWAP required"],
      calls: [
        { plan: 0, targets: [
          { system: "orders", call: "orders.basket(\"today\")", returns: "40 lines · 312 fills" },
        ] },
        { plan: 1, targets: [
          { system: "market", call: "market.intraday(basket)", returns: "Spread ×2 on 3 names" },
          { system: "news",   call: "news.events(\"09:00–11:30\")", returns: "Macro release 10:00" },
        ] },
        { plan: 2, targets: [
          { system: "tca", call: "tca.slippage(basket, \"VWAP\")", returns: "−6.2 bps vs VWAP" },
        ] },
      ],
      result: {
        instrument: "YOUR BASKET",
        ticker: "40 LINES  ·  09:00–11:30  ·  VS VWAP",
        move: "−6.2 bps",
        moveTone: "warn",
        sections: [
          { title: "MAIN CONTRIBUTORS", items: [
            { text: "3 small caps", note: "spread ×2 after 10:00" },
            { text: "Macro release 10:00", note: "volume spike" },
          ] },
          { title: "POINTS TO CHECK", items: ["Participation rate on the 3 names", "2 fills not yet reported"], accent: true },
        ],
        sourcesLabel: "SOURCES VIA MCP",
        sources: ["ORDERS", "MARKET", "NEWS", "TCA"],
      },
      // Scene 5: the model lights up while the data is analysed
      combine: { cap: "model", tag: "Analyses the data" },
    },

    server: {
      title: "CONTROLLED ACCESS",
      subtitle: "orders server  ·  exposes your order history",
      focusSystem: "orders",
      envelope: "MCP SERVER",
      agent: { label: "AI AGENT", sub: "on your behalf" },
      system: { label: "ORDERS", sub: "Your order history" },
      runtimeLabel: "RUNS IN A CONTROLLED ENVIRONMENT",
      runtime: ["SECURE HOSTING", "MCP GATEWAY", "SECRETS VAULT", "AUDIT LOGS"],
      layers: [
        { id: "identity",   label: "IDENTITY & ACCESS", glyph: "key",    tone: "request",
          items: ["Your identity, your token", "Acts on your behalf only", "Your accounts only"] },
        { id: "guardrails", label: "GUARDRAILS",        glyph: "shield", tone: "orchestrator",
          items: ["Read-only access", "Validated requests", "Rate-limited"] },
        { id: "context",    label: "DATA CONTEXT",      glyph: "doc",    tone: "mcp",
          items: ["Clear tool descriptions", "Defined fields & units", "Benchmark definitions"] },
        { id: "access",     label: "DATA ACCESS MODEL", glyph: "stack",  tone: "data",
          items: ["Approved views only", "Filtered to your orders", "No other client’s data"] },
      ],
      revealOrder: ["access", "context", "guardrails", "identity"],
      allowed: {
        call: "orders.basket(\"today\")",
        checks: { identity: "✓ you · your accounts", guardrails: "✓ read-only · valid", context: "✓ tool understood", access: "✓ your orders only" },
        maskAt: "guardrails",
        returns: "40 lines · your account",
      },
      denied: { call: "orders.of_client(\"other\")", at: "identity", reason: "✕ not entitled" },
      captions: {
        intro: "Behind each tool call sits an MCP server that controls access.",
        runtime: "It runs in a controlled environment, and every call is logged.",
        layers: {
          access: "It only exposes approved views: your orders, nothing else.",
          context: "It describes the data, so the model reads it correctly.",
          guardrails: "Guardrails bound what goes in and what comes out.",
          identity: "Every call carries your identity and is checked against your rights.",
        },
        allowed: "An authorised call passes every check, and leaves an audit trail.",
        denied: "Another client’s orders? The call stops at the gate.",
      },
    },

    multiAgent: {
      apps: [
        { id: "exec",    label: "EXECUTION AGENT" },
        { id: "pre",     label: "PRE-TRADE AGENT" },
        { id: "post",    label: "REPORTING AGENT" },
        { id: "support", label: "SUPPORT AGENT" },
      ],
      layerLabel: "MCP LAYER",
      systems: ["ORDERS", "MARKET DATA", "TCA", "NEWS", "REFERENCE", "DOCS"],
      focusApp: "exec",
    },

    finalStack: [
      { items: ["YOU"] },
      { items: ["AI AGENT"], tone: "request" },
      { items: ["ORCHESTRATOR"], tone: "orchestrator", wide: true },
      { items: ["MODEL", "MEMORY", "SKILLS", "MCP"], highlight: "MCP" },
      { items: ["YOUR ORDERS", "MARKET DATA", "TCA", "NEWS", "DOCUMENTATION"], viaMcp: true },
    ],
    finalTitle: "ONE BUSINESS REQUEST, COORDINATED STEPS",
    finalSubtitle: "Controlled access: MCP standardises the connections, the systems enforce the rights.",

    captions: {
      s1: "An agent doesn’t just answer. It plans the steps.",
      s2: "The model interprets. The orchestrator coordinates.",
      s2Def: "An agentic solution: a model surrounded by tools, memory and methods.",
      s2DefSub: "It plans, acts, checks, then answers.",
      s3Question: ["How does an AI application securely connect", "to enterprise tools and data?"],
      s4: "MCP provides a standard way for AI applications to connect to tools and data.",
      s4Sub: "A universal interface, not another model.",
      s4Discover: "Each system describes its tools once. Any agent can use them.",
      s5Steps: ["The agent decides what it needs", "MCP gives standard access", "Data returns", "The model analyses it"],
      s6: "One question. Four systems. A sourced answer, still to be checked.",
      s7Tangle: "Without a standard, every agent rebuilds every integration.",
      s7TangleSub: "4 agents × 6 systems = 24 bespoke integrations",
      s7Once: ["Build each connection once.", "Reuse it across agents."],
      s7OnceSub: "4 + 6 = 10 standard connections",
      s7One: "One request. Several coordinated sources.",
      s7Final: "MCP standardises the connections. Controls stay with the systems.",
    },

    // Longer holds than the bank version, so the voice-over can explain what
    // an agentic solution is (scene 2), what MCP does (scene 4) and the
    // model's analysis of the data (scene 5).
    timing: Object.assign({}, base.timing, {
      s2: Object.assign({}, base.timing.s2, { hold: 12.2 }),
      s4: Object.assign({}, base.timing.s4, { discover: 8.2 }),
      s5: Object.assign({}, base.timing.s5, { combine: 6.9 }),
    }),
  };

  // French text, laid over the English config above (same order and length).
  window.MCP_EXPLAINER_CONFIG_FR = {
    title: "D’une question métier à une réponse coordonnée",
    disclaimer: "EXEMPLE FICTIF  ·  ILLUSTRATION PÉDAGOGIQUE",

    scenes: [
      { label: "La demande" },
      { label: "Les briques de l’agent" },
      { label: "Le problème" },
      { label: "Voici MCP" },
      { label: "Vos sources via MCP" },
      { label: "Le résultat" },
      { label: "Des accès contrôlés" },
      { label: "Pourquoi MCP compte" },
      { label: "Synthèse" },
    ],

    user: { label: "VOUS", sublabel: "Plateforme Cash Equity" },
    agent: { label: "AGENT IA" },
    orchestrator: { label: "ORCHESTRATEUR" },

    capabilities: [
      { label: "MODÈLE" },
      { label: "SKILLS" },
      { label: "OUTILS" },
      { label: "MÉMOIRE" },
    ],

    orchestration: [
      { tag: "Interprète votre demande" },
      { tag: "Rappelle votre format de rapport" },
      { tag: "Applique la méthode TCA" },
      { tag: "Vos données sont requises" },
    ],

    mcp: { verbs: ["DÉCOUVRIR", "APPELER", "RENVOYER"] },

    systems: [
      { label: "VOS ORDRES",            sub: "Ordres · exécutions" },
      { label: "DONNÉES DE MARCHÉ",     sub: "Prix · volumes · spreads" },
      { label: "ANALYSE TCA",           sub: "Benchmarks · écarts" },
      { label: "ACTUALITÉS",            sub: "Événements de marché" },
      { label: "RÉFÉRENTIEL",           sub: "Instruments · calendriers" },
      { label: "DOCUMENTATION",         sub: "Guides des algos" },
    ],

    example: {
      prompt: "Pourquoi mon panier a-t-il sous-performé le VWAP ce matin ?",
      promptMeta: "VOUS  ·  11:45",
      promptShort: "« Pourquoi mon panier… ? »",
      loop: ["Comprendre", "Planifier", "Agir", "Répondre"],
      needs: ["Il me faut vos ordres et exécutions.", "Il me faut le contexte de marché.", "Il me faut un calcul d’écart."],
      plan: ["Vos ordres & exécutions requis", "Contexte de marché requis", "Écart vs VWAP requis"],
      calls: [
        { targets: [{ returns: "40 lignes · 312 exécutions" }] },
        { targets: [{ returns: "Spread ×2 sur 3 titres" }, { returns: "Publication macro 10h00" }] },
        { targets: [{ returns: "−6,2 bps vs VWAP" }] },
      ],
      result: {
        instrument: "VOTRE PANIER",
        ticker: "40 LIGNES  ·  09:00–11:30  ·  VS VWAP",
        move: "−6,2 bps",
        sections: [
          { title: "PRINCIPAUX CONTRIBUTEURS", items: [
            { text: "3 small caps", note: "spread ×2 après 10h" },
            { text: "Publication macro 10h00", note: "pic de volume" },
          ] },
          { title: "POINTS À VÉRIFIER", items: ["Taux de participation sur les 3 titres", "2 exécutions pas encore remontées"] },
        ],
        sourcesLabel: "SOURCES VIA MCP",
        sources: ["ORDRES", "MARCHÉ", "ACTUALITÉS", "TCA"],
      },
      combine: { tag: "Analyse les données" },
    },

    server: {
      title: "DES ACCÈS CONTRÔLÉS",
      subtitle: "serveur ordres  ·  expose votre historique d’ordres",
      envelope: "SERVEUR MCP",
      agent: { label: "AGENT IA", sub: "en votre nom" },
      system: { label: "ORDRES", sub: "Votre historique" },
      runtimeLabel: "TOURNE DANS UN ENVIRONNEMENT CONTRÔLÉ",
      runtime: ["HÉBERGEMENT SÉCURISÉ", "PASSERELLE MCP", "COFFRE DE SECRETS", "JOURNAUX D’AUDIT"],
      layers: [
        { label: "IDENTITÉ & ACCÈS",
          items: ["Votre identité, votre jeton", "Agit en votre nom seulement", "Vos comptes uniquement"] },
        { label: "GARDE-FOUS",
          items: ["Accès en lecture seule", "Requêtes validées", "Débit limité"] },
        { label: "CONTEXTE DES DONNÉES",
          items: ["Descriptions d’outils claires", "Champs & unités définis", "Définition des benchmarks"] },
        { label: "MODÈLE D’ACCÈS",
          items: ["Vues validées uniquement", "Filtré sur vos ordres", "Rien d’un autre client"] },
      ],
      allowed: {
        checks: { identity: "✓ vous · vos comptes", guardrails: "✓ lecture seule · valide", context: "✓ outil compris", access: "✓ vos ordres seulement" },
        returns: "40 lignes · votre compte",
      },
      denied: { reason: "✕ non autorisé" },
      captions: {
        intro: "Derrière chaque appel d’outil, un serveur MCP qui contrôle les accès.",
        runtime: "Il tourne dans un environnement contrôlé, et chaque appel est journalisé.",
        layers: {
          access: "Il n’expose que des vues validées : vos ordres, rien d’autre.",
          context: "Il décrit les données, pour que le modèle les lise correctement.",
          guardrails: "Des garde-fous encadrent ce qui entre et ce qui sort.",
          identity: "Chaque appel porte votre identité et respecte vos droits.",
        },
        allowed: "Un appel autorisé passe chaque contrôle, et laisse une piste d’audit.",
        denied: "Les ordres d’un autre client ? L’appel s’arrête à l’entrée.",
      },
    },

    multiAgent: {
      apps: [
        { label: "AGENT D’EXÉCUTION" },
        { label: "AGENT PRÉ-TRADE" },
        { label: "AGENT DE REPORTING" },
        { label: "AGENT SUPPORT" },
      ],
      layerLabel: "COUCHE MCP",
      systems: ["ORDRES", "MARCHÉ", "TCA", "ACTUALITÉS", "RÉFÉRENTIEL", "DOCS"],
    },

    finalStack: [
      { items: ["VOUS"] },
      { items: ["AGENT IA"] },
      { items: ["ORCHESTRATEUR"] },
      { items: ["MODÈLE", "MÉMOIRE", "SKILLS", "MCP"] },
      { items: ["VOS ORDRES", "DONNÉES DE MARCHÉ", "TCA", "ACTUALITÉS", "DOCUMENTATION"] },
    ],
    finalTitle: "UNE DEMANDE MÉTIER, DES ÉTAPES COORDONNÉES",
    finalSubtitle: "Des accès contrôlés : MCP standardise les connexions, les systèmes appliquent les droits.",

    captions: {
      s1: "Un agent ne se contente pas de répondre. Il planifie les étapes.",
      s2: "Le modèle interprète. L’orchestrateur coordonne.",
      s2Def: "Une solution agentique : un modèle entouré d’outils, de mémoire et de méthodes.",
      s2DefSub: "Il planifie, agit, vérifie, puis répond.",
      s3Question: ["Comment une application d’IA se connecte-t-elle", "en sécurité aux outils et données de l’entreprise ?"],
      s4: "MCP offre aux applications d’IA un moyen standard d’accéder aux outils et aux données.",
      s4Sub: "Une interface universelle, pas un modèle de plus.",
      s4Discover: "Chaque système décrit ses outils une fois. Tout agent peut les utiliser.",
      s5Steps: ["L’agent décide ce dont il a besoin", "MCP donne un accès standard", "Les données reviennent", "Le modèle les analyse"],
      s6: "Une question. Quatre systèmes. Une réponse sourcée, à vérifier.",
      s7Tangle: "Sans standard, chaque agent refait chaque intégration.",
      s7TangleSub: "4 agents × 6 systèmes = 24 intégrations sur mesure",
      s7Once: ["Construire chaque connexion une fois.", "La réutiliser entre agents."],
      s7OnceSub: "4 + 6 = 10 connexions standard",
      s7One: "Une demande. Plusieurs sources coordonnées.",
      s7Final: "MCP standardise les connexions. Les contrôles restent dans les systèmes.",
    },
  };
})();
