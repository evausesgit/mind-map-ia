# LinkedIn post — Nous Research releases Arete-27B, a post-trained Qwen open-weight model

Date: 2026-11-08
Source: https://huggingface.co/NousResearch/Arete-27B
Related news: data/news.yaml

---

Open-weight models make alignment choices inspectable — and changeable.

Nous Research has released Arete-27B, created by supervised fine-tuning of Qwen3.8-27B on roughly 52.8 million tokens. On Nous Research’s own 803-prompt evaluation, the reported rate of answers adopting state-propaganda framing fell from 22% to 0.9%, without a meaningful regression on the capability tests it ran.

The numbers need independent replication. The important enterprise point is methodological: post-training can materially change model behaviour, so the base model name alone is not enough for governance.

Teams should version the exact checkpoint, training recipe, evaluation set and intended values — then test against their own policy and risk requirements.

Source: https://huggingface.co/NousResearch/Arete-27B

#ArtificialIntelligence #AILeadership #EnterpriseAI #OpenSourceAI #OpenWeights #AIGovernance
