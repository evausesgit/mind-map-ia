/*
 * Sales Trading Copilot — use-case demo — editable configuration
 * -------------------------------------------------------------
 * Continues the visual language of the MCP / Agentic Architecture explainer.
 * Everything the audience reads is defined here; the engine (usecase.js)
 * lays it out and builds a single scrub-safe GSAP timeline from it.
 *
 * Tips
 *  - `speed` scales the whole animation (1.2 = 20% faster).
 *  - Timings are in seconds, before `speed` is applied.
 *  - Keep labels short: they are rendered on a 1920×1080 stage.
 *  - `**word**` inside a line highlights that word in the accent colour.
 *  - All figures are illustrative / simulated.
 */
window.STC_CONFIG = {
  title: "AI-Enabled Sales Trading — a Copilot use case",

  speed: 1.25,

  theme: {
    bg: "#05070B",
    bgGlow: "#0E1522",
    text: "#EEF2F7",
    muted: "#8B94A5",
    faint: "#454D5C",
    line: "rgba(255,255,255,0.13)",
    request: "#7EA6FF",      // sales trader, human actions
    agent: "#A594FF",        // copilot / reasoning
    mcp: "#3DD6C6",          // MCP layer, tool calls
    data: "#F2C46D",         // data flowing back, evidence
    public: "#9FB0C8",       // public information
    positive: "#34D399",
    warn: "#F27A7A",
    font: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace",
  },

  scenes: [
    { id: "knows",     label: "The client already knows" },
    { id: "vantage",   label: "A different vantage point" },
    { id: "copilot",   label: "Sales Trading Copilot" },
    { id: "mcp",       label: "Enterprise capabilities" },
    { id: "insight",   label: "From information to insight" },
    { id: "human",     label: "Human + AI" },
    { id: "amplify",   label: "The amplification" },
    { id: "final",     label: "What it means" },
  ],

  disclaimer: "ILLUSTRATIVE SCENARIO  ·  SIMULATED DATA",

  // ── Scene 1 ───────────────────────────────────────────────────────────────
  event: { name: "NVIDIA", ticker: "NVDA  ·  NASDAQ  ·  intraday", move: "+4.2%" },
  publicSources: [
    { label: "MARKET DATA",      sub: "Real-time prices" },
    { label: "NEWS",             sub: "Wires · headlines" },
    { label: "TERMINAL FEEDS",   sub: "Bloomberg-style" },
    { label: "PUBLIC RESEARCH",  sub: "Street notes" },
    { label: "EARNINGS · FILINGS", sub: "Company disclosures" },
  ],
  client: { label: "INSTITUTIONAL CLIENT", sub: "Own data · own AI" },
  headline: "NVIDIA +4.2% following AI infrastructure announcement.",
  headlineMeta: "ON THE CLIENT’S SCREEN",

  // ── Scene 2 ───────────────────────────────────────────────────────────────
  trader: { label: "SALES TRADER", sub: "Cash Equity" },
  vantage: [
    { label: "MARKET CONTEXT",     glyph: "chart" },
    { label: "EXECUTION INSIGHTS", glyph: "bolt" },
    { label: "LIQUIDITY · VOLUME", glyph: "bars" },
    { label: "RESEARCH",           glyph: "doc" },
    { label: "CLIENT CONTEXT",     glyph: "person" },
    { label: "PERMITTED INTERNAL INSIGHTS", glyph: "lock" },
  ],
  permissionLabel: "SUBJECT TO PERMISSIONS & COMPLIANCE",
  questionsTitle: "THE QUESTIONS THAT MATTER",
  questions: [
    "Is this move significant?",
    "What is unusual?",
    "What is driving it?",
    "How is the market behaving?",
    "Why could this matter to this particular client?",
    "What useful conversation should follow?",
  ],
  screens: ["TERMINAL", "EMS", "TCA", "RESEARCH PORTAL", "CRM", "NEWS", "CHAT", "EMAIL", "RISK", "LIQUIDITY"],

  // ── Scene 3 ───────────────────────────────────────────────────────────────
  copilot: { label: "SALES TRADING COPILOT" },
  prompt: "Give me the real context behind the NVDA move and tell me which of my clients could care.",
  promptMeta: "SALES TRADER  ·  08:04",
  plan: [
    "Understand the market move",
    "Investigate market behaviour",
    "Retrieve relevant research",
    "Identify relevant client context",
    "Build an actionable briefing",
  ],
  phases: ["PLAN", "INVESTIGATE", "CORRELATE", "PERSONALIZE", "BRIEF"],

  // ── Scene 4 — MCP calls ───────────────────────────────────────────────────
  // `returns` land on the evidence board. Keep each chip short.
  servers: [
    { id: "market",   label: "MARKET DATA MCP",         sub: "price · volume · volatility · liquidity",
      call: "market.move(\"NVDA\")",        returns: ["NVDA +4.2%", "Volume 2.3× normal", "Semis sector +1.6%"] },
    { id: "news",     label: "NEWS MCP",                sub: "recent events · announcements",
      call: "news.recent(\"NVDA\")",        returns: ["AI infra announcement", "No other catalyst"] },
    { id: "research", label: "RESEARCH MCP",            sub: "internal research · sector · analyst views",
      call: "research.context(\"NVDA\")",   returns: ["House AI-infra theme", "Recent analyst views"] },
    { id: "exec",     label: "EXECUTION INSIGHTS MCP",  sub: "conditions · liquidity · microstructure",
      call: "execution.conditions(\"NVDA\")", returns: ["Book depth thinner", "Spreads wider than usual"] },
    { id: "client",   label: "CLIENT INTELLIGENCE MCP", sub: "interests · interactions · coverage", permissioned: true,
      call: "clients.relevance(\"NVDA\")",  returns: ["Alpha · AI-infra focus", "Alpha · semis coverage"] },
  ],
  evidenceTitle: "EVIDENCE",
  // Pairs of evidence chips (by text) linked during the correlation step
  correlations: [
    ["NVDA +4.2%", "Semis sector +1.6%"],
    ["Volume 2.3× normal", "Book depth thinner"],
    ["AI infra announcement", "House AI-infra theme"],
    ["House AI-infra theme", "Alpha · AI-infra focus"],
    ["Spreads wider than usual", "Volume 2.3× normal"],
  ],

  // ── Scene 5 — the briefing ────────────────────────────────────────────────
  plainFact: "NVDA is +4.2%.",
  briefing: {
    title: "NVDA",
    sub: "NVIDIA  ·  intraday briefing",
    move: "+4.2%",
    tag: "ILLUSTRATIVE DATA",
    differentTitle: "WHAT IS DIFFERENT?",
    facts: [
      { k: "VOLUME",          v: "2.3× normal", bars: [["20D AVG", 1], ["TODAY", 2.3]] },
      { k: "LIQUIDITY",       v: "Thinner than usual during the move" },
      { k: "MARKET CONTEXT",  v: "Semis also positive, but NVDA is materially outperforming peers", bars: [["SEMIS", 1.6, "+1.6%"], ["NVDA", 4.2, "+4.2%"]] },
      { k: "RESEARCH CONTEXT", v: "Recent AI infrastructure developments reinforce an existing investment theme" },
    ],
    relevanceTitle: "CLIENT RELEVANCE",
    relevance: "**Client Alpha** has demonstrated strong interest in semiconductor / AI infrastructure themes.",
    conversationTitle: "POTENTIAL CONVERSATION",
    conversation: "“The headline is already public, but today’s move appears stronger than the sector move and is occurring on unusually high volume.”",
    sources: "VIA MCP  ·  MARKET DATA  ·  NEWS  ·  RESEARCH  ·  EXECUTION INSIGHTS  ·  CLIENT INTELLIGENCE",
  },

  // ── Scene 6 — human + AI ──────────────────────────────────────────────────
  aiMessage: "I found a potentially relevant opportunity for Client Alpha.",
  actions: ["VIEW EVIDENCE", "DEEPER ANALYSIS", "PREPARE CLIENT BRIEF"],
  chosenAction: 2,
  draftTitle: "PROPOSED TALKING POINT  ·  DRAFT",
  draft: "“NVDA is outperforming the broader semiconductor move today on unusually strong volume. Given your recent focus on AI infrastructure, we thought the move might be worth discussing.”",
  draftEdit: "Happy to walk you through what we’re seeing on liquidity.",
  draftEditTag: "EDITED BY SALES TRADER",
  humanSteps: ["REVIEWS", "EDITS", "DECIDES", "COMMUNICATES"],
  clientAlpha: { label: "CLIENT ALPHA", sub: "Sales Trader’s call" },

  // ── Scene 7 — amplification ───────────────────────────────────────────────
  before: {
    title: "BEFORE",
    steps: ["MULTIPLE TERMINALS", "MULTIPLE SEARCHES", "RESEARCH", "CLIENT HISTORY", "MARKET DATA", "MANUAL SYNTHESIS"],
  },
  after: {
    title: "WITH THE COPILOT",
    mcpLabel: "ENTERPRISE CAPABILITIES VIA MCP",
    mcpItems: ["MARKET", "NEWS", "RESEARCH", "EXECUTION", "CLIENT"],
    result: "CONTEXTUALIZED BRIEFING",
  },
  fromTo: [
    ["Information overload", "Relevant signals"],
    ["Generic market information", "Client-specific context"],
    ["Reactive conversations", "Proactive opportunities"],
    ["Multiple disconnected systems", "One orchestrated investigation"],
  ],

  // ── Final ─────────────────────────────────────────────────────────────────
  finalQuestions: [
    "What does it mean?",
    "Why does it matter?",
    "Why does it matter to **THIS** client?",
    "What should we investigate or discuss next?",
  ],
  finalTitle: "AI-ENABLED SALES TRADING",
  finalSubtitle: "From market information to client-relevant insight.",
  finalInputs: ["MARKET", "RESEARCH", "EXECUTION CONTEXT", "CLIENT CONTEXT"],
  finalFlow: ["AI AGENT", "SALES TRADER", "RELEVANT CLIENT CONVERSATION"],
  finalMessage: [
    "The Agent doesn’t replace the Sales Trader’s edge.",
    "It helps the Sales Trader find and use that edge **at scale**.",
  ],

  // ── On-screen captions ────────────────────────────────────────────────────
  captions: {
    s1Knows: "The client already knows the news.",
    s1Question: "So what can the **Sales Trader** add?",
    s2Vantage: "Not repeating public information — reading it from a different vantage point.",
    s2Problem: ["Too much information.", "Too little time."],
    s2ProblemSub: "Many systems, dashboards and sources to build one picture.",
    s3Plan: "The copilot plans before it answers.",
    s4Select: "It selects the enterprise capabilities it needs — one call at a time.",
    s4Permission: "Permissioned context only — no confidential orders, MNPI or other clients’ activity.",
    s5Insight: "Not what happened — what is different, and who it matters to.",
    s6: ["AI finds the signal.", "The Sales Trader provides the judgment and relationship."],
    s7Compress: "Not faster search — one orchestrated investigation.",
  },

  // ── Timings (seconds, before `speed`) ─────────────────────────────────────
  timing: {
    s1: { ticker: 1.0, spark: 1.4, sourceStagger: 0.18, flow: 1.1, knowsHold: 1.6, questionHold: 2.4 },
    s2: { cardStagger: 0.22, vantageHold: 2.0, questionStagger: 0.45, questionsHold: 1.0, screenStagger: 0.1, problemHold: 2.2 },
    s3: { typing: 2.6, readHold: 0.5, send: 1.0, think: 1.2, planStagger: 0.4, hold: 1.1 },
    s4: { build: 1.2, callGap: 1.85, call: 0.75, back: 0.9, chipStagger: 0.25, hold: 0.6 },
    s5: { linkStagger: 0.3, collapse: 0.7, factStagger: 0.45, typing: 2.0, hold: 2.0 },
    s6: { deliver: 1.1, typing: 1.4, cursor: 0.9, draftTyping: 2.3, stepGap: 0.8, hold: 2.6 },
    s7: { slow: 3.8, fast: 1.5, compareHold: 1.6, rowStagger: 0.7, rowsHold: 1.6 },
    final: { strikeHold: 0.8, questionStagger: 0.85, questionsHold: 1.0, flowStagger: 0.3, messageHold: 4.8 },
  },
};
