# Awesome Context-Window Degradation

A curated collection of research papers, datasets, tools, implementations, and learning resources on **context-window degradation in large language models** — the systematic decline in a model's ability to locate, weight, and integrate information as input length grows — and its consequences for long-document research synthesis. The repository also contains a **reproducible experiment** that measures one of these effects, position bias in multi-document question answering, with a small open model.

## Contents
- [Overview](#overview)
- [AI-Assisted Research Paper](#ai-assisted-research-paper)
- [Citation Integrity Audit](#citation-integrity-audit)
- [Curated Research Papers](#curated-research-papers)
- [Datasets](#datasets)
- [Tools and Libraries](#tools-and-libraries)
- [GitHub Implementations](#github-implementations)
- [Tutorials and Learning Resources](#tutorials-and-learning-resources)
- [Experiment: Position and Order Sensitivity](#experiment-position-and-order-sensitivity)
- [Repository Structure](#repository-structure)
- [Reproducibility and AI Assistance](#reproducibility-and-ai-assistance)
- [License](#license)

## Overview

Large language models now advertise context windows spanning hundreds of thousands to millions of tokens, prompting expectations that entire corpora, case files, or literature sets can be synthesized in a single pass. Empirical evidence, however, shows that nominal context length and *effective* context utilization diverge substantially.

This repository organizes research around four interacting degradation mechanisms — **primacy-recency ("lost-in-the-middle") bias**, **positional-encoding extrapolation failure**, **attention dilution**, and **distractor accumulation** — and the mitigation strategies developed against them: retrieval-augmented generation (RAG), hybrid RAG/long-context routing, attention-sink and sparse-attention mechanisms, positional-encoding extensions (RoPE scaling, YaRN), and prompt compression.

The problem is especially consequential for **long-document research synthesis**: a task that structurally requires uniform, position-independent attention to many dispersed source passages, unlike single-fact retrieval. A model that quietly underweights sources five through eight in a ten-paper review can produce output that is fluent and locally accurate while systematically misrepresenting the balance of evidence — a failure mode current accuracy-based benchmarks do not reliably catch.

Persistent gaps in the field include the absence of synthesis-specific evaluation protocols, limited mechanistic understanding of multi-hop aggregation failure, and a lack of faithfulness/attribution metrics tailored to multi-source synthesis rather than single-document summarization.

The repository has two parts. The first is the review: a paper, a citation audit and curated lists of papers, datasets, tools, implementations and tutorials. The second is an experiment that tests one of the reviewed effects, primacy-recency bias, directly: code, frozen settings, real outputs and a written report.

## AI-Assisted Research Paper

**Context-Window Degradation and Its Impact on Long-Document Research Synthesis**
*A Review of Positional, Attentional, and Architectural Constraints on Large Language Model Performance over Extended Inputs*

[View Paper](paper/context_window_degradation_paper.pdf)

The paper reviews the mechanisms, evidence, and mitigations associated with context-window degradation, with specific attention to implications for long-document research synthesis. It surveys positional-bias studies (Liu et al., 2024), comprehensive long-context benchmarks (RULER, LongBench), and comparative evaluations of RAG vs. long-context architectures, before identifying research gaps and future directions.

## Citation Integrity Audit

[View Audit](citation-audit/Citation_Integrity_Audit.pdf)

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

Reference implementations for **RULER**, **LongBench**, **StreamingLLM**, **Needle In A Haystack**, **YaRN**, and **LLMLingua**. The code written for this repository's own experiment is separate: see `src/`, `scripts/`, `notebooks/` and `test/`, described below.

## Tutorials and Learning Resources

[View tutorials](tutorials/tutorials.md)

Includes Anthropic's official long-context prompting documentation, a quantitative long-context recall case study, an agentic context-engineering guide, the RULER reproduction README, and DeepLearning.AI's RAG short course.

## Experiment: Position and Order Sensitivity

**Question.** In the 20-passage question-answering test of Liu et al. (*Lost in the Middle*, arXiv:2307.03172), how much of the answer variation comes from where the gold passage sits, and how much from how the 19 distractor passages are ordered? Model: Qwen2.5-3B-Instruct. Data: 300 NaturalQuestions-Open evaluation questions. The written report (LaTeX source) is in `paper/`.

### Results (reduced design)

| Condition | Gold first | Gold 10th | Gold last |
|---|---|---|---|
| O0 original distractor order | 62.0 % | 52.7 % | 56.3 % |
| O1 shuffled distractors | 60.3 % | 52.7 % | 58.0 % |

Closed-book (no passages): 21.3 %. Gold passage only: 85.0 %. Intervals, paired tests and flip rates are in `results/reduced/results.csv`.

- Gold first versus tenth: +9.3 points, 95 % interval 4.0 to 14.7, Holm-adjusted p = 0.009 (original order).
- Shuffling the distractors changed accuracy by at most 1.7 points, but changed the correctness of 16 to 20 % of individual questions, in both directions.
- Repeated greedy runs were identical (rerun flip rate 0).

### Limits

- One 3B model, one dataset, three gold positions, one shuffle seed, 300 questions.
- Data files for gold positions 9 and 19 were derived from the official gold-at-0 file (`src/positionorder/derive.py`) and not compared with the official files.
- Scoring is the original repository's first-line substring match. The 200-row manual audit sample (`results/reduced/manual_audit_sample.csv`) is not labelled, so the scorer's error rate is unknown.
- The question-repetition test in `configs/protocol_v0.1.yaml` was not run.
- The decision rule (`configs/freeze_reduced.json`) was recorded before the evaluation outputs existed.

### Reproduce

1. Obtain `nq-open-20_total_documents_gold_at_0.jsonl.gz` from the original authors' data release (see `data/README.md`).
2. Open `notebooks/position_order_colab.ipynb` in Google Colab with a GPU, set the data link in the settings cell, choose mode `reduced`, and run all. The reported run used a Tesla T4 at about 3.5 s per prompt.
3. Offline tests (no GPU needed): `python -m pytest test`.

Exact versions: `requirements.txt` and `results/reduced/environment.json`. Model revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`; original repository commit `29b8a6d042ce29abccee3db1a73171a107d7e6af` (MIT).

## Repository Structure

````
README.md                  this file
requirements.txt           package versions used in the experiment run
configs/                   protocol and frozen settings of the run
data/README.md             where the data come from (no data stored)
notebooks/                 one-click Colab notebook
src/                       positionorder package: seeds, data, scoring, prompts, runner, pipeline, evaluation
scripts/                   environment check, data validation, evaluation entry points
test/                      offline unit tests on synthetic data
results/reduced/           real outputs: results, predictions, raw outputs, figures, audit
paper/                     review paper and the experiment paper source
research_decisions.md      literature-to-experiment decisions
baseline_validation.md     reproduction checks and deviations (written before the real run)
ai_assistance_log.md       AI assistance and human verification
citation-audit/ references/ datasets/ tools/ implementations/ tutorials/    curated review material
````

## Reproducibility and AI Assistance

Every number in the experiment report comes from `results/reduced/results.csv`. Settings, seeds and file hashes of the run are in `configs/freeze_reduced.json`. Deviations from the original protocol are discussed in `baseline_validation.md`. AI assistance in both parts of this repository is documented in `ai_assistance_log.md`, and the experiment report carries an AI-assistance statement.

## License

Original content in this repository (README text, category summaries, and the citation-integrity audit) is released under the [MIT License](LICENSE). Linked third-party papers, datasets, and code repositories retain their own original licenses — consult each source directly before reuse. The experiment data, the Qwen model and the original *Lost in the Middle* code are not redistributed here and keep their own licenses.

---
