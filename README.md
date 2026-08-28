# Awesome Context-Window Degradation

A curated collection of research papers, datasets, tools, implementations, and learning resources on **context-window degradation in large language models** — the systematic decline in a model's ability to locate, weight, and integrate information as input length grows — and its consequences for long-document research synthesis.

## Contents
- [Overview](#overview)
- [AI-Assisted Research Paper](#ai-assisted-research-paper)
- [Citation Integrity Audit](#citation-integrity-audit)
- [Curated Research Papers](#curated-research-papers)
- [Datasets](#datasets)
- [Tools and Libraries](#tools-and-libraries)
- [GitHub Implementations](#github-implementations)
- [Tutorials and Learning Resources](#tutorials-and-learning-resources)
- [License](#license)

## Overview

Large language models now advertise context windows spanning hundreds of thousands to millions of tokens, prompting expectations that entire corpora, case files, or literature sets can be synthesized in a single pass. Empirical evidence, however, shows that nominal context length and *effective* context utilization diverge substantially.

This repository organizes research around four interacting degradation mechanisms — **primacy-recency ("lost-in-the-middle") bias**, **positional-encoding extrapolation failure**, **attention dilution**, and **distractor accumulation** — and the mitigation strategies developed against them: retrieval-augmented generation (RAG), hybrid RAG/long-context routing, attention-sink and sparse-attention mechanisms, positional-encoding extensions (RoPE scaling, YaRN), and prompt compression.

The problem is especially consequential for **long-document research synthesis**: a task that structurally requires uniform, position-independent attention to many dispersed source passages, unlike single-fact retrieval. A model that quietly underweights sources five through eight in a ten-paper review can produce output that is fluent and locally accurate while systematically misrepresenting the balance of evidence — a failure mode current accuracy-based benchmarks do not reliably catch.

Persistent gaps in the field include the absence of synthesis-specific evaluation protocols, limited mechanistic understanding of multi-hop aggregation failure, and a lack of faithfulness/attribution metrics tailored to multi-source synthesis rather than single-document summarization.

## AI-Assisted Research Paper

**Context-Window Degradation and Its Impact on Long-Document Research Synthesis**
*A Review of Positional, Attentional, and Architectural Constraints on Large Language Model Performance over Extended Inputs*

[View Paper](paper/Context_Window_Degradation_Paper.docx)

The paper reviews the mechanisms, evidence, and mitigations associated with context-window degradation, with specific attention to implications for long-document research synthesis. It surveys positional-bias studies (Liu et al., 2024), comprehensive long-context benchmarks (RULER, LongBench), and comparative evaluations of RAG vs. long-context architectures, before identifying research gaps and future directions.

## Citation Integrity Audit

[View Audit](citation-audit/Citation_Integrity_Audit.md)

Every reference cited in the paper — and every additional paper added to this repository to meet the 20-paper minimum — was independently checked against arXiv, a publisher DOI record, or an official GitHub repository for correct title, authors, year, venue, and a working link, rather than accepted on an AI tool's word alone. All 13 in-paper references verified as genuine and correctly attributed; see the audit for the full verification log and two minor observations.

## Curated Research Papers

[View full categorized list (20 papers)](references/references.md)

Organized into: Foundational/Positional Bias Papers · Positional Encoding & Length Generalization · Long-Context Benchmarks · Attention Mechanisms & Efficiency · RAG vs. Long Context · Prompt Compression · Faithfulness & Hallucination · Surveys.

## Datasets

[View datasets](datasets/datasets.md)

Three standard long-context evaluation benchmarks: **RULER**, **LongBench**, and **Needle In A Haystack (NIAH)**.

## Tools and Libraries

[View tools](tools/tools.md)

Five libraries relevant to measuring or mitigating degradation: **LLMLingua**, **LangChain**, **LlamaIndex**, **StreamingLLM**, and **FlashAttention**.

## GitHub Implementations

[View implementations](implementations/github-repositories.md)

Reference implementations for **RULER**, **LongBench**, **StreamingLLM**, **Needle In A Haystack**, **YaRN**, and **LLMLingua**.

## Tutorials and Learning Resources

[View tutorials](tutorials/tutorials.md)

Includes Anthropic's official long-context prompting documentation, a quantitative long-context recall case study, an agentic context-engineering guide, the RULER reproduction README, and DeepLearning.AI's RAG short course.

## License

Original content in this repository (README text, category summaries, and the citation-integrity audit) is released under the [MIT License](LICENSE). Linked third-party papers, datasets, and code repositories retain their own original licenses — consult each source directly before reuse.

---
