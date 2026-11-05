# LinkedIn post — Anthropic open-sources FlashProve for cryptographically verifiable model inference

Date: 2026-11-02
Source: https://www.anthropic.com/research/provable-inference
Related news: data/news.yaml

---

How can an enterprise verify that the model it paid for actually produced a response?

Anthropic's open-source FlashProve prototype explores a cryptographic answer. It uses zero-knowledge proofs to verify inference against a committed model without exposing the model weights.

Anthropic reports that, for a 4-bit Llama 4 Maverick:
- one H100 generates proofs at about 110 tokens per second;
- a 1,024-token request produces a proof of roughly 19 MB;
- GPU overhead is still around 70–95 times normal inference.

This is research, not a ready-made control for high-volume banking workloads. But provable inference could eventually strengthen third-party model assurance, routing transparency and evidence that contractual or regulatory model commitments were respected.

Source: https://www.anthropic.com/research/provable-inference

#ArtificialIntelligence #AILeadership #EnterpriseAI #AIGovernance #ModelRisk #ResponsibleAI
