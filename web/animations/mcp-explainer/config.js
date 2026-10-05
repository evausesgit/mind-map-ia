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
