# LinkedIn post — Anthropic details dynamic workflows in Claude Code

Date: 2026-06-02
Source: https://x.com/trq212/status/2061907337154367865?s=20
Related news: data/news.yaml

---

Claude Code is becoming less like a single coding assistant and more like a system for building task-specific agent harnesses.

Anthropic’s new article on dynamic workflows explains how Claude can generate a JavaScript workflow on the fly, then use it to coordinate subagents with separate context windows. That matters because many difficult tasks fail not because the model cannot reason, but because the work is too long, too parallel, or too easy to bias when everything stays in one context.

A few patterns stand out:

- Fan-out-and-synthesize for splitting a large task into independent pieces, then merging the results.
- Adversarial verification to have separate agents check outputs against a rubric.
- Tournament and loop-until-done patterns for open-ended exploration, triage, sorting, or debugging.

The useful takeaway for builders is practical: agent performance is increasingly about orchestration design, not only model choice. But Anthropic also notes an important caveat — workflows can use more tokens and are not necessary for every task.

Source: https://x.com/trq212/status/2061907337154367865?s=20

#AI #AIAgents #ClaudeCode #Anthropic #DeveloperTools #AgenticAI
