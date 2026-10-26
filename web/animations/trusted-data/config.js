/*
 * Trusted Data for Enterprise Agents — editable configuration
 * ------------------------------------------------------------
 * Everything the audience reads is defined here, in English and French.
 * The engine (engine.js) picks `strings[lang]` and builds the animation.
 *
 * Tips
 *  - `speed` scales the whole animation (1.2 = 20% faster).
 *  - Keep labels short: they are rendered on a 1920×1080 stage.
 *  - Sensitivity levels: C3 = secret (never leaves the perimeter),
 *    C2 = confidential (anonymised before leaving), C1 = public.
 */
window.TRUSTED_DATA_CONFIG = {
  speed: 1,

  theme: {
    bg: "#05070B",
    bgGlow: "#0E1522",
    text: "#EEF2F7",
    muted: "#8B94A5",
    faint: "#454D5C",
    line: "rgba(255,255,255,0.13)",
    request: "#7EA6FF",   // user, agent
    mcp: "#3DD6C6",       // MCP servers, tool calls
    data: "#F2C46D",      // data sources, data flowing back
    positive: "#34D399",
    warn: "#F27A7A",
    c3: "#F27A7A",        // secret
    c2: "#F5A55A",        // confidential
    c1: "#34D399",        // public
    perimeter: "#7EA6FF",
    cloud: "#A594FF",
    font: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace",
  },

  strings: {
    // ═══════════════════════════════════════════════════════════════════════
    en: {
      title: "Trusted Data for Enterprise Agents",
      scenes: {
        request: "The request",
        stack: "Agent · MCP · Data",
        quality: "Data quality",
        context: "Data context",
        access: "Who sees what",
        privacy: "Client orders stay private",
        routing: "Where does the model run?",
        result: "The answer",
        final: "Summary",
      },

      user: { label: "SALES", sub: "Cash Equity desk" },
      agent: "SALES AGENT",
      promptMeta: "SALES  ·  CASH EQUITY",
      prompt: "Which clients bought semiconductor stocks this month, how much, and what market context should I send them?",
      mcpTitle: "MCP SERVERS",
      dataTitle: "DATA SOURCES",
      servers: [
        { label: "ORDERS MCP", sub: "executions · positions" },
        { label: "CLIENT MCP", sub: "CRM · coverage" },
        { label: "MARKET MCP", sub: "prices · news · research" },
      ],
      sources: [
        { label: "OMS", sub: "order management" },
        { label: "CRM", sub: "client records" },
        { label: "MARKET DATA", sub: "feeds · research" },
      ],

      cap: {
        s1: "One question. Client data and market data, mixed together.",
        s2: "The agent only sees the data its MCP servers expose.",
        s2Sub: "So what lies behind them, and how it is exposed, decides everything.",
        s3Bad: "Garbage in, confident garbage out.",
        s3BadSub: "The model doesn't know the data is wrong. It answers anyway.",
        s3Good: "Quality is checked before the agent ever reads the data.",
        s4: "If it isn't described, the AI can't find it.",
        s4Sub: "Tool descriptions, field meanings, business glossary, data owner: metadata is part of the product.",
        s5a: "The agent acts on behalf of the user, with the user's rights.",
        s5b: "Same question, different person: a different answer, or none.",
        s5c: "The agent never has more rights than the person it works for.",
        s5Sub: "Identity propagated · entitlements per client · row & column filtering · full audit trail",
        s6a: "What leaves the bank is not what the order says.",
        s6b: "Client orders serve one purpose: answering your question.",
        s7a: "One request, three sensitivity levels.",
        s7b: "Sensitivity decides the path, not convenience.",
        s7c: "Same agent, same gateway: sensitive and everyday questions in one flow.",
        s8: "A useful answer you can trust, and explain.",
      },

      quality: {
        panelTitle: "ORDERS MCP  ·  raw executions",
        cols: ["CLIENT", "STOCK", "QTY", "PRICE", "DATE"],
        rows: [
          ["Client A", "NVDA", "12,000", "118.40", "2026-10-03"],
          ["CLIENT A.", "NVDA", "12,000", "118.40", "2026-10-03"],
          ["Client B", "ASML", "—", "612.00", "2026-10-07"],
          ["Client C", "TSMC", "8,500", "96.10", "2025-10-14"],
        ],
        flags: ["DUPLICATE", "MISSING VALUE", "STALE"],
        fixed: [
          ["Client B", "ASML", "3,200", "612.00", "2026-10-07"],
          ["Client C", "TSMC", "8,500", "101.30", "2026-10-14"],
        ],
        answerBad: "Client A bought 24,000 NVDA shares.",
        answerBadTag: "✕  confident, and wrong",
        answerGood: "Client A bought 12,000 NVDA shares.",
        answerGoodTag: "✓  verified data",
        checksTitle: "QUALITY CHECKS",
        checks: ["Freshness", "Completeness", "Consistency", "Golden source"],
        badge: "QUALITY ✓",
      },

      context: {
        badTitle: "POORLY DESCRIBED",
        goodTitle: "WELL DESCRIBED",
        badTool: "get_data(q)",
        badDesc: "\"Returns data.\"",
        badFields: ["col_7", "qty2", "dt", "cpty"],
        goodTool: "get_client_executions(client, sector, period)",
        goodDesc: "\"Executed equity orders per client. Cancelled orders excluded.\"",
        goodFields: [
          ["notional_eur", "executed value, in EUR"],
          ["sector", "GICS sector, e.g. Semiconductors"],
          ["trade_date", "execution date (UTC)"],
          ["client_id", "golden client ID, shared with the CRM"],
        ],
        goodMeta: ["Business glossary", "Examples", "Owner: Cash Equity Data Office"],
        badGuess: "qty2 = ordered? executed? quoted?",
        badVerdict: "✕  wrong field, wrong answer",
        goodVerdict: "✓  right tool, right field, first try",
        agentProbe: "AGENT  ·  looking for “volume bought”",
      },

      access: {
        userA: { label: "SALES", sub: "Cash Equity · clients A, B" },
        userB: { label: "RESEARCH", sub: "Equity research analyst" },
        token: "on behalf of: sales.a  ·  clients: A, B",
        tokenB: "on behalf of: research.b",
        gate: "IDENTITY & ENTITLEMENTS",
        gateSub: "checked at every call",
        source: "ORDERS MCP",
        sourceSub: "executions",
        rows: ["Client A · NVDA", "Client B · ASML", "Client C · TSMC"],
        filtered: "not your client",
        denied: "✕  information barrier: no access to client orders",
        auditTitle: "AUDIT LOG",
        audit: [
          ["10:42:03", "sales.a", "orders.get_client_executions", "✓ 2 clients"],
          ["10:42:41", "research.b", "orders.get_client_executions", "✕ denied"],
        ],
      },

      privacy: {
        orderTitle: "ORDER #48213  ·  inside the bank",
        outTitle: "WHAT THE MODEL SEES",
        fields: [
          ["client", "Alpha Capital Partners", "CLT_4821"],
          ["trader", "J. Martin", "[masked]"],
          ["side", "BUY", "BUY"],
          ["stock", "NVDA", "NVDA"],
          ["quantity", "12,000", "10k – 20k"],
          ["notional", "€1,420,800", "€1M – €2M"],
        ],
        engine: "ANONYMISATION",
        engineSub: "pseudonyms · masking · ranges",
        vault: "CLT_4821  ↔  Alpha Capital Partners",
        vaultSub: "mapping key: never leaves the perimeter",
        guarantees: [
          "Never used to train models",
          "Zero data retention by the provider",
          "Prompts & logs stay in-house",
          "Re-identification only inside the bank",
        ],
      },

      routing: {
        perimeter: "BANK PERIMETER  ·  ON-PREMISE",
        cloud: "CLOUD  ·  FRONTIER MODELS",
        agent: "SALES AGENT",
        gateway: "ROUTING GATEWAY",
        gatewaySub: "classifies every piece of data",
        gpu: "ON-PREM GPUs",
        gpuSub: "open-weights model",
        anon: "ANONYMISER",
        frontier: "FRONTIER MODEL",
        frontierSub: "private endpoint · EU region",
        link: "encrypted · private link",
        tasks: [
          { level: "C3", label: "Client orders · names, volumes", route: "stays on-prem" },
          { level: "C2", label: "Buying patterns", route: "anonymised, then cloud" },
          { level: "C1", label: "Market context · news", route: "straight to the cloud" },
        ],
        legendTitle: "SENSITIVITY",
        legend: [
          ["C3", "Secret", "never leaves the perimeter"],
          ["C2", "Confidential", "leaves only anonymised"],
          ["C1", "Public", "best model, wherever it runs"],
        ],
        chips: { c3: "C3 · Client A · 12,000 NVDA", c2Before: "C2 · Alpha Capital", c2After: "C2 · CLT_4821", c1: "C1 · market news" },
        bonusPrompt: "“Summarise today's Nvidia news.”",
        bonusTag: "100% public → frontier model, no detour",
      },

      result: {
        title: "SEMICONDUCTOR BUYERS  ·  OCTOBER",
        lines: [
          ["Client A", "NVDA · 12,000 shares"],
          ["Client B", "ASML · 3,200 shares"],
        ],
        contextTitle: "MARKET CONTEXT",
        context: "AI capex upgrades lift chip stocks; Q3 results season ahead.",
        actionTitle: "SUGGESTED ACTION",
        action: "Send the semis note to Clients A and B.",
        trace: [
          "Sources: OMS · CRM · Market data",
          "Quality checks passed",
          "Entitlements: sales.a",
          "0 client names left the bank",
        ],
      },

      final: {
        title: "TRUSTED DATA FOR ENTERPRISE AGENTS",
        subtitle: "An agent is only as good as the data behind its MCP servers.",
        pillars: [
          { label: "QUALITY", text: "Clean, fresh, consistent data", glyph: "check" },
          { label: "CONTEXT", text: "Described so the AI can find it", glyph: "doc" },
          { label: "ACCESS", text: "Only what the user may see", glyph: "key" },
          { label: "SOVEREIGNTY", text: "Sensitive data stays inside", glyph: "shield" },
        ],
      },
    },

    // ═══════════════════════════════════════════════════════════════════════
    fr: {
      title: "Des données de confiance pour les agents",
      scenes: {
        request: "La demande",
        stack: "Agent · MCP · Data",
        quality: "Qualité des données",
        context: "Contexte des données",
        access: "Qui accède à quoi",
        privacy: "Confidentialité des ordres",
        routing: "Où tourne le modèle ?",
        result: "La réponse",
        final: "Synthèse",
      },

      user: { label: "SALES", sub: "Desk Cash Equity" },
      agent: "AGENT SALES",
      promptMeta: "SALES  ·  CASH EQUITY",
      prompt: "Quels clients ont acheté des valeurs semi-conducteurs ce mois-ci, pour quel volume, et quel contexte de marché leur envoyer ?",
      mcpTitle: "SERVEURS MCP",
      dataTitle: "SOURCES DE DONNÉES",
      servers: [
        { label: "MCP ORDRES", sub: "exécutions · positions" },
        { label: "MCP CLIENTS", sub: "CRM · couverture" },
        { label: "MCP MARCHÉ", sub: "prix · news · recherche" },
      ],
      sources: [
        { label: "OMS", sub: "gestion des ordres" },
        { label: "CRM", sub: "fiches clients" },
        { label: "MARKET DATA", sub: "flux · recherche" },
      ],

      cap: {
        s1: "Une seule question. Données clients et données de marché, mêlées.",
        s2: "L’agent ne voit que les données exposées par ses serveurs MCP.",
        s2Sub: "Ce qu’il y a derrière, et la façon dont c’est exposé, décide de tout.",
        s3Bad: "Données fausses en entrée, réponse fausse… et sûre d’elle.",
        s3BadSub: "Le modèle ne sait pas que la donnée est fausse. Il répond quand même.",
        s3Good: "La qualité est contrôlée avant même que l’agent ne lise la donnée.",
        s4: "Ce qui n’est pas décrit n’existe pas pour l’IA.",
        s4Sub: "Description des outils, sens des champs, glossaire métier, propriétaire : les métadonnées font partie du produit.",
        s5a: "L’agent agit au nom de l’utilisateur, avec ses droits.",
        s5b: "Même question, autre personne : une autre réponse, ou aucune.",
        s5c: "L’agent n’a jamais plus de droits que la personne pour qui il travaille.",
        s5Sub: "Identité propagée · habilitations par client · filtrage lignes & colonnes · audit complet",
        s6a: "Ce qui sort de la banque n’est pas ce que dit l’ordre.",
        s6b: "Les ordres clients ne servent qu’à une chose : répondre à votre question.",
        s7a: "Une demande, trois niveaux de sensibilité.",
        s7b: "C’est la sensibilité qui décide du chemin, pas la commodité.",
        s7c: "Même agent, même passerelle : cas sensibles et cas courants dans un seul flux.",
        s8: "Une réponse utile, fiable, et explicable.",
      },

      quality: {
        panelTitle: "MCP ORDRES  ·  exécutions brutes",
        cols: ["CLIENT", "VALEUR", "QTÉ", "PRIX", "DATE"],
        rows: [
          ["Client A", "NVDA", "12 000", "118,40", "2026-10-03"],
          ["CLIENT A.", "NVDA", "12 000", "118,40", "2026-10-03"],
          ["Client B", "ASML", "—", "612,00", "2026-10-07"],
          ["Client C", "TSMC", "8 500", "96,10", "2025-10-14"],
        ],
        flags: ["DOUBLON", "VALEUR MANQUANTE", "PÉRIMÉ"],
        fixed: [
          ["Client B", "ASML", "3 200", "612,00", "2026-10-07"],
          ["Client C", "TSMC", "8 500", "101,30", "2026-10-14"],
        ],
        answerBad: "Le client A a acheté 24 000 titres NVDA.",
        answerBadTag: "✕  affirmatif, et faux",
        answerGood: "Le client A a acheté 12 000 titres NVDA.",
        answerGoodTag: "✓  donnée vérifiée",
        checksTitle: "CONTRÔLES QUALITÉ",
        checks: ["Fraîcheur", "Complétude", "Cohérence", "Source de référence"],
        badge: "QUALITÉ ✓",
      },

      context: {
        badTitle: "MAL DÉCRIT",
        goodTitle: "BIEN DÉCRIT",
        badTool: "get_data(q)",
        badDesc: "\"Renvoie des données.\"",
        badFields: ["col_7", "qty2", "dt", "cpty"],
        goodTool: "get_client_executions(client, sector, period)",
        goodDesc: "\"Ordres actions exécutés par client. Hors ordres annulés.\"",
        goodFields: [
          ["notional_eur", "montant exécuté, en EUR"],
          ["sector", "secteur GICS, ex. Semi-conducteurs"],
          ["trade_date", "date d’exécution (UTC)"],
          ["client_id", "ID client de référence, commun au CRM"],
        ],
        goodMeta: ["Glossaire métier", "Exemples", "Propriétaire : Data Office Cash Equity"],
        badGuess: "qty2 = demandée ? exécutée ? cotée ?",
        badVerdict: "✕  mauvais champ, mauvaise réponse",
        goodVerdict: "✓  bon outil, bon champ, du premier coup",
        agentProbe: "AGENT  ·  cherche « volume acheté »",
      },

      access: {
        userA: { label: "SALES", sub: "Cash Equity · clients A, B" },
        userB: { label: "RECHERCHE", sub: "Analyste actions" },
        token: "au nom de : sales.a  ·  clients : A, B",
        tokenB: "au nom de : research.b",
        gate: "IDENTITÉ & HABILITATIONS",
        gateSub: "vérifiées à chaque appel",
        source: "MCP ORDRES",
        sourceSub: "exécutions",
        rows: ["Client A · NVDA", "Client B · ASML", "Client C · TSMC"],
        filtered: "hors de votre périmètre",
        denied: "✕  muraille de Chine : pas d’accès aux ordres clients",
        auditTitle: "JOURNAL D’AUDIT",
        audit: [
          ["10:42:03", "sales.a", "orders.get_client_executions", "✓ 2 clients"],
          ["10:42:41", "research.b", "orders.get_client_executions", "✕ refusé"],
        ],
      },

      privacy: {
        orderTitle: "ORDRE #48213  ·  dans la banque",
        outTitle: "CE QUE VOIT LE MODÈLE",
        fields: [
          ["client", "Alpha Capital Partners", "CLT_4821"],
          ["trader", "J. Martin", "[masqué]"],
          ["sens", "ACHAT", "ACHAT"],
          ["valeur", "NVDA", "NVDA"],
          ["quantité", "12 000", "10k – 20k"],
          ["nominal", "1 420 800 €", "1 M€ – 2 M€"],
        ],
        engine: "ANONYMISATION",
        engineSub: "pseudonymes · masquage · tranches",
        vault: "CLT_4821  ↔  Alpha Capital Partners",
        vaultSub: "table de correspondance : ne quitte jamais le périmètre",
        guarantees: [
          "Jamais utilisées pour entraîner un modèle",
          "Zéro rétention chez le fournisseur",
          "Prompts et logs conservés en interne",
          "Ré-identification uniquement dans la banque",
        ],
      },

      routing: {
        perimeter: "PÉRIMÈTRE BANQUE  ·  ON-PREMISE",
        cloud: "CLOUD  ·  MODÈLES FRONTIÈRES",
        agent: "AGENT SALES",
        gateway: "PASSERELLE DE ROUTAGE",
        gatewaySub: "classe chaque donnée",
        gpu: "GPU ON-PREMISE",
        gpuSub: "modèle open-weights",
        anon: "ANONYMISEUR",
        frontier: "MODÈLE FRONTIÈRE",
        frontierSub: "endpoint privé · région UE",
        link: "chiffré · lien privé",
        tasks: [
          { level: "C3", label: "Ordres clients · noms, volumes", route: "reste on-premise" },
          { level: "C2", label: "Profils d’achat", route: "anonymisé, puis cloud" },
          { level: "C1", label: "Contexte marché · news", route: "direct vers le cloud" },
        ],
        legendTitle: "SENSIBILITÉ",
        legend: [
          ["C3", "Secret", "ne quitte jamais le périmètre"],
          ["C2", "Confidentiel", "ne sort qu’anonymisé"],
          ["C1", "Public", "le meilleur modèle, où qu’il tourne"],
        ],
        chips: { c3: "C3 · Client A · 12 000 NVDA", c2Before: "C2 · Alpha Capital", c2After: "C2 · CLT_4821", c1: "C1 · news marché" },
        bonusPrompt: "« Résume l’actualité Nvidia du jour. »",
        bonusTag: "100 % public → modèle frontière, sans détour",
      },

      result: {
        title: "ACHETEURS SEMI-CONDUCTEURS  ·  OCTOBRE",
        lines: [
          ["Client A", "NVDA · 12 000 titres"],
          ["Client B", "ASML · 3 200 titres"],
        ],
        contextTitle: "CONTEXTE DE MARCHÉ",
        context: "Hausse des capex IA : les valeurs puces progressent, résultats T3 à venir.",
        actionTitle: "ACTION SUGGÉRÉE",
        action: "Envoyer la note semi-conducteurs aux clients A et B.",
        trace: [
          "Sources : OMS · CRM · Market data",
          "Contrôles qualité OK",
          "Habilitations : sales.a",
          "0 nom de client sorti de la banque",
        ],
      },

      final: {
        title: "DES DONNÉES DE CONFIANCE POUR LES AGENTS",
        subtitle: "Un agent ne vaut que par les données derrière ses serveurs MCP.",
        pillars: [
          { label: "QUALITÉ", text: "Données propres, fraîches, cohérentes", glyph: "check" },
          { label: "CONTEXTE", text: "Décrites pour que l’IA les trouve", glyph: "doc" },
          { label: "ACCÈS", text: "Seulement ce que l’utilisateur peut voir", glyph: "key" },
          { label: "SOUVERAINETÉ", text: "Les données sensibles restent dedans", glyph: "shield" },
        ],
      },
    },
  },
};
