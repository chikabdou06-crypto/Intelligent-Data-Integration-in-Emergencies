# Research & References: Agent Architecture Validation

## Overview

This document compiles academic papers, industry research, and architectural comparisons that validate the current Plan-and-Execute pipeline and support the proposed MCP integration roadmap.

---

## Key Academic Papers

### 1. "Beyond ReAct: A Planner-Centric Framework for Complex Tool-Augmented LLM Reasoning" (2025)
- **Link:** https://arxiv.org/abs/2503.07572
- **Relevance:** Argues that Plan-then-Execute is superior to ReAct loops for multi-tool reasoning. Introduces DAG-based planning for parallel tool execution.
- **Connection to our system:** Our Planner → Orchestrator → Synthesizer is exactly this pattern.

### 2. "Architecting Resilient LLM Agents" (2025)
- **Link:** https://arxiv.org/abs/2509.08646
- **Relevance:** Recommends Plan-then-Execute for security and reliability. Finalizing the plan before interacting with untrusted external data maintains control-flow integrity.

### 3. "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG" (2025/2026)
- **Link:** https://arxiv.org/abs/2501.09136
- **Relevance:** The primary reference survey for the entire Agentic RAG field. Our architecture matches the survey's standard taxonomy.

### 4. "Web Agents Should Adopt the Plan-Then-Execute Paradigm" (2026)
- **Link:** https://arxiv.org/abs/2605.14290
- **Relevance:** Directly argues that Plan-then-Execute is more reliable, faster, and more secure than reactive ReAct loops.

### 5. "SoK: Agentic Retrieval-Augmented Generation" (2026)
- **Link:** https://arxiv.org/abs/2507.07637
- **Relevance:** Formalizes agentic RAG systems as finite-horizon POMDPs. Our system maps directly to this formalization.

### 6. "Reflective RAG" (2026) — ACL Anthology
- **Relevance:** Introduces reflection-tagging for self-correction. This is the correction loop we plan to add.

### 7. "SCMRAG: Self-Corrective Multi-hop RAG" (2025) — IFAAMAS
- **Relevance:** Self-corrective agent mechanisms to reduce hallucinations. Validates our planned self-correction loop.

---

## MCP vs. Plan-and-Execute: Complementary Layers

| Aspect | Plan-and-Execute | MCP |
|---|---|---|
| What it is | Reasoning architecture (how the agent thinks) | Connectivity protocol (how the agent talks to tools) |
| Problem it solves | Task decomposition, flow control | Tool discovery, standardized I/O |
| Layer | Above (brain/strategy) | Below (plumbing/transport) |
| Replaces the other? | No | No |

**They are complementary.** MCP standardizes the wiring; Plan-and-Execute provides the reasoning.

---

## Validated Roadmap

| Priority | Improvement | Paper Support |
|---|---|---|
| 1 | Fix & standardize tool responses | Engineering best practice |
| 2 | MCP server for standard tool link | MCP Spec (Linux Foundation) |
| 3 | Self-correction loop | Reflective RAG, SCMRAG |
| 4 | Parallel execution | Beyond ReAct (DAG planning) |
| 5 | Conversational memory | Agentic RAG Survey |
| 6 | Observability & tracing | Production best practices |
