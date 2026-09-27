# LinkedIn post — Aikido releases Altar-1, an open-weight model for sovereign security workloads

Date: 2026-09-21
Source: https://huggingface.co/AikidoSec/altar-1
Related news: data/news.yaml

---

Open weights are becoming a deployment strategy for specialised, sensitive workloads.

Aikido’s Altar-1 is a 504B-parameter prune of GLM-5.3. It removes 34% of the base model’s experts, quantises the routed experts to INT4, and fits 328 GB of weights across four H200 GPUs. Calibration includes cybersecurity traces, coding, tool use and reasoning.

For enterprise security teams, the proposition is clear:

- keep sensitive code and telemetry on controlled infrastructure;
- tailor serving and observability to internal requirements;
- avoid dependence on a remote API for every analysis.

But open-weight does not automatically mean open source: Altar-1 inherits GLM-5.3’s custom licence, and its claimed fidelity still requires workload-specific validation.

Source: https://huggingface.co/AikidoSec/altar-1

#ArtificialIntelligence #AIGovernance #EnterpriseAI #RiskManagement
