# Datasets and Benchmarks

Context-window degradation is primarily studied through synthetic and realistic long-context *benchmarks* rather than conventional labeled datasets. The three below are the field's standard diagnostic suites and are all referenced directly in the accompanying paper.

- **RULER**
  Source: [github.com/hsiehjackson/RULER](https://github.com/hsiehjackson/RULER) (Hsieh et al., 2024, COLM)
  Description: A synthetic benchmark generator with configurable sequence length (4K–128K+) across four task categories — retrieval, multi-hop tracing, aggregation, and question answering. Configurations are generated on demand rather than distributed as a static file.
  Use in this repo's research: Cited throughout Section 3 and 5 of the paper as the primary evidence that "effective" context length is often far shorter than the advertised maximum, and that aggregation/tracing tasks degrade faster than simple retrieval.
  [Paper (arXiv:2404.06654)](https://arxiv.org/abs/2404.06654)

- **LongBench / LongBench-v2**
  Source: [github.com/THUDM/LongBench](https://github.com/THUDM/LongBench) · [Hugging Face: THUDM/LongBench](https://huggingface.co/datasets/THUDM/LongBench)
  Description: A bilingual (English/Chinese), realistic-document benchmark spanning single- and multi-document QA, summarization, few-shot learning, and code tasks, with document lengths averaging 5K–15K tokens (LongBench) and up to 2M words (LongBench-v2).
  Use in this repo's research: Cited as complementary evidence to RULER that context degradation is a general architectural property, not an artifact of synthetic-task design.
  [Paper (arXiv:2308.14508)](https://arxiv.org/abs/2308.14508)

- **Needle In A Haystack (NIAH)**
  Source: [github.com/gkamradt/LLMTest_NeedleInAHaystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack) (Kamradt, 2023)
  Description: The original controlled-depth single-fact retrieval test — a "needle" fact is inserted at varying depths within a long distractor document. Now considered a necessary but insufficient diagnostic (see RULER's critique).
  Use in this repo's research: Establishes the baseline paradigm that RULER and later benchmarks extend beyond single-fact retrieval toward aggregation and synthesis-relevant tasks.

**Note on scope:** No conventional "training" datasets are listed because the paper's subject — context-window degradation — is an evaluation phenomenon, not a task with a standard supervised dataset. If your own AI-assisted paper is on a topic where labeled training/eval datasets genuinely don't apply, the instruction sheet allows you to state this explicitly (Section 8) — this file does so above.
