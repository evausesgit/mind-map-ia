# LinkedIn post — Linkup releases the 149M-parameter SPARSEUP retriever under Apache 2.0

Date: 2026-09-19
Source: https://huggingface.co/Linkup-Platform/linkup-sparseup-embed-v1
Related news: data/news.yaml

---

Open models are improving not only at generation, but at the retrieval layer.

Linkup has released SPARSEUP, a 149M-parameter sparse retrieval model based on ModernBERT, under Apache 2.0. Its model card reports 56.4 nDCG@10 on BEIR-13 excluding MS MARCO—the strongest public vocabulary-based sparse encoder below 150M parameters in Linkup’s comparison.

Why sparse retrieval is useful:
- outputs can be inspected as weighted vocabulary terms;
- indexes can be efficient and compatible with search infrastructure;
- a small, self-hostable model can reduce cost and data exposure.

The reported results are vendor benchmarks and should be reproduced on domain data. For RAG in regulated environments, retrieval quality, latency, interpretability and licence clarity all belong in the evaluation.

Source: https://huggingface.co/Linkup-Platform/linkup-sparseup-embed-v1

#OpenSourceAI #OpenWeights #RAG #InformationRetrieval #EnterpriseAI
