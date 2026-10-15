# LinkedIn post — Third Moment runs 10,000 long-duration agents in quantitative research

Date: 2026-10-14
Source: https://openai.com/index/third-moment-research/
Related news: data/news.yaml

---

Long-running agents are becoming an infrastructure and control problem, not just a model capability demo.

An OpenAI customer case says Third Moment Research runs 10,000 agents concurrently for 36–48-hour investigations, including quantitative-finance experiments. It also describes an optimisation that reduced a year-long order-level US equity backtest from roughly three hours to three to five minutes.

What stands out is the operating design:
- isolated environments and an outer harness for retry, termination and escalation;
- explicit attention to token waste and context pollution;
- automated security tests before simulations run.

The claims are vendor-reported, not independently audited. Still, the pattern is useful: scaling agents safely depends as much on orchestration, cost telemetry and kill switches as on model intelligence.

Source: https://openai.com/index/third-moment-research/

#ArtificialIntelligence #AILeadership #EnterpriseAI #AgenticAI #CapitalMarkets #RiskManagement
