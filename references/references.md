# Curated Research Papers

20 verified papers on context-window degradation in large language models, organized by subtopic. Every entry below was checked against arXiv and/or the publisher record for title, authors, year, venue, and link before inclusion (see `/citation-audit/Citation_Integrity_Audit.md` for the verification log).

## Contents
- [Foundational / Positional Bias Papers](#foundational--positional-bias-papers)
- [Positional Encoding & Length Generalization](#positional-encoding--length-generalization)
- [Long-Context Benchmarks](#long-context-benchmarks)
- [Attention Mechanisms & Efficiency](#attention-mechanisms--efficiency)
- [Retrieval-Augmented Generation vs. Long Context](#retrieval-augmented-generation-vs-long-context)
- [Prompt Compression](#prompt-compression)
- [Faithfulness & Hallucination](#faithfulness--hallucination)
- [Surveys](#surveys)

---

## Foundational / Positional Bias Papers

- **Lost in the Middle: How Language Models Use Long Contexts**
  Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024)
  *Transactions of the Association for Computational Linguistics*, 12, 157–173.
  [Paper (TACL)](https://doi.org/10.1162/tacl_a_00638) · [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
  The founding empirical demonstration of the "lost-in-the-middle" U-shaped performance curve; the single most-cited result in this collection.

- **Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization**
  Hsieh, C.-Y., Chuang, Y.-S., Li, C.-L., Wang, Z., Le, L. T., Kumar, A., Glass, J., Ratner, A., Lee, C.-Y., Krishna, R., & Pfister, T. (2024)
  ACL Findings 2024. [arXiv:2406.16008](https://arxiv.org/abs/2406.16008)
  Traces lost-in-the-middle to an intrinsic U-shaped attention bias and proposes a training-free calibration fix — directly relevant to Section 3.1 of the review paper.

## Positional Encoding & Length Generalization

- **RoFormer: Enhanced Transformer with Rotary Position Embedding**
  Su, J., Ahmed, M., Lu, Y., Pan, S., Bo, W., & Liu, Y. (2024)
  *Neurocomputing*, 568, 127063. [DOI](https://doi.org/10.1016/j.neucom.2023.127063) · [arXiv:2104.09864](https://arxiv.org/abs/2104.09864)
  Introduces RoPE, the positional encoding scheme used by most current long-context LLMs.

- **Train Short, Test Long: Attention with Linear Biases Enables Input Length Extrapolation**
  Press, O., Smith, N. A., & Lewis, M. (2022)
  ICLR 2022. [arXiv:2108.12409](https://arxiv.org/abs/2108.12409)
  Introduces ALiBi, an alternative encoding designed for graceful length extrapolation.

- **The Impact of Positional Encoding on Length Generalization in Transformers**
  Kazemnejad, A., Padhi, I., Ramamurthy, K. N., Das, P., & Reddy, S. (2023)
  NeurIPS 2023. [arXiv:2305.19466](https://arxiv.org/abs/2305.19466)
  Systematic comparison showing no explicit positional scheme reliably matches implicit (no-PE) length generalization on reasoning tasks.

- **Extending Context Window of Large Language Models via Positional Interpolation**
  Chen, S., Wong, S., Chen, L., & Tian, Y. (2023)
  [arXiv:2306.15595](https://arxiv.org/abs/2306.15595)
  Introduces Position Interpolation (PI), extending RoPE-based LLaMA models to 32K tokens with minimal fine-tuning by down-scaling position indices rather than extrapolating.

- **YaRN: Efficient Context Window Extension of Large Language Models**
  Peng, B., Quesnelle, J., Fan, H., & Shippole, E. (2024)
  ICLR 2024. [arXiv:2309.00071](https://arxiv.org/abs/2309.00071) · [Code](https://github.com/jquesnelle/yarn)
  A compute-efficient RoPE extension method requiring 10x fewer tokens than prior approaches to reach 128K context.

## Long-Context Benchmarks

- **RULER: What's the Real Context Size of Your Long-Context Language Models?**
  Hsieh, C.-P., Sun, S., Kriman, S., Acharya, S., Rekesh, D., Jia, F., & Ginsburg, B. (2024)
  COLM 2024. [arXiv:2404.06654](https://arxiv.org/abs/2404.06654) · [Code](https://github.com/hsiehjackson/RULER)
  Extends needle-in-a-haystack with multi-hop tracing and aggregation tasks; shows effective context length is often far below the advertised maximum.

- **LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding**
  Bai, Y., Lv, X., Zhang, J., Lyu, H., Tang, J., Huang, Z., Du, Z., Liu, X., Zeng, A., Hou, L., Dong, Y., Tang, J., & Li, J. (2024)
  ACL 2024 (Volume 1: Long Papers), pp. 3119–3137. [arXiv:2308.14508](https://arxiv.org/abs/2308.14508) · [Code](https://github.com/THUDM/LongBench)
  A realistic, multi-task, bilingual benchmark spanning QA, summarization, and few-shot learning over long documents.

- **Needle In A Haystack — Pressure Testing LLMs**
  Kamradt, G. (2023)
  [Software repository, GitHub](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)
  The original single-fact retrieval diagnostic that established the NIAH paradigm later extended by RULER.

## Attention Mechanisms & Efficiency

- **Efficient Streaming Language Models with Attention Sinks**
  Xiao, G., Tian, Y., Chen, B., Han, S., & Lewis, M. (2024)
  ICLR 2024. [arXiv:2309.17453](https://arxiv.org/abs/2309.17453) · [Code](https://github.com/mit-han-lab/streaming-llm)
  Identifies the "attention sink" phenomenon and shows preserving initial tokens enables stable generalization to effectively unbounded input streams.

## Retrieval-Augmented Generation vs. Long Context

- **Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach**
  Li, Z., Li, C., Zhang, M., Mei, Q., & Bendersky, M. (2024)
  EMNLP 2024 Industry Track, pp. 881–893. [arXiv:2407.16833](https://arxiv.org/abs/2407.16833)
  Finds long-context processing outperforms RAG on average accuracy but at higher cost; proposes Self-Route, a confidence-based hybrid router.

- **LaRA: Benchmarking Retrieval-Augmented Generation and Long-Context LLMs — No Silver Bullet for LC or RAG Routing**
  Li, K., Zhang, L., Jiang, Y., Xie, P., Huang, F., Wang, S., & Cheng, M. (2025)
  [arXiv:2502.09977](https://arxiv.org/abs/2502.09977)
  Argues prior RAG-vs-LC comparisons suffer from benchmark-design flaws; finds RAG competitive on single-location retrieval and better at flagging unanswerable queries.

- **Retrieval Meets Long Context Large Language Models**
  Xu, P., Ping, W., Wu, X., McAfee, L., Zhu, C., Liu, Z., Subramanian, S., Bakhturina, E., Shoeybi, M., & Catanzaro, B. (2024)
  ICLR 2024. [arXiv:2310.03025](https://arxiv.org/abs/2310.03025)
  Shows that combining retrieval with long-context models can outperform either approach alone, complicating a simple RAG-vs-LC dichotomy.

- **LongRAG: Enhancing Retrieval-Augmented Generation with Long-Context LLMs**
  Jiang, Z., Ma, X., & Chen, W. (2024)
  [arXiv:2406.15319](https://arxiv.org/abs/2406.15319)
  Restructures the retrieval unit itself (4K-token "long" units instead of ~100-word passages) to reduce information loss from aggressive chunking.

## Prompt Compression

- **LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models**
  Jiang, H., Wu, Q., Lin, C.-Y., Yang, Y., & Qiu, L. (2023)
  EMNLP 2023. [arXiv:2310.05736](https://arxiv.org/abs/2310.05736) · [Code](https://github.com/microsoft/LLMLingua)
  Coarse-to-fine, budget-controlled token compression achieving up to 20x compression with limited performance loss.

- **LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression**
  Jiang, H., Wu, Q., Luo, X., Li, D., Lin, C.-Y., Yang, Y., & Qiu, L. (2023)
  [arXiv:2310.06839](https://arxiv.org/abs/2310.06839)
  Extends LLMLingua specifically to long-context scenarios, jointly addressing cost, position bias, and performance.

- **LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression**
  Pan, Z., et al. (2024)
  [arXiv:2403.12968](https://arxiv.org/abs/2403.12968)
  Reformulates compression as token classification to better guarantee faithfulness to the original prompt.

## Faithfulness & Hallucination

- **Survey of Hallucination in Natural Language Generation**
  Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023)
  *ACM Computing Surveys*, 55(12), 1–38. [arXiv:2202.03629](https://arxiv.org/abs/2202.03629)
  Broad taxonomy of hallucination and faithfulness metrics across NLG tasks; the natural starting point for the faithfulness-metric gap identified in Section 6.2 of the review.

## Surveys

- **Advancing Transformer Architecture in Long-Context Large Language Models: A Comprehensive Survey**
  Huang, Y., Xu, J., Jiang, Z., Lai, J., Li, Z., Yao, Y., Chen, T., Yang, L., Xin, Z., & Ma, X. (2023)
  [arXiv:2311.12351](https://arxiv.org/abs/2311.12351)
  Catalogues architectural and positional-encoding extension strategies for long-context modeling.

- **A Comprehensive Survey on Long Context Language Modeling**
  Liu, J., Zhu, D., Bai, Z., He, Y., Liao, H., Que, H., et al. (2025)
  [arXiv:2503.17407](https://arxiv.org/abs/2503.17407)
  A recent, large-author survey spanning data, architecture, workflow, and evaluation for long-context LLMs.

---

**Note on scope:** This list intentionally emphasizes the mechanisms, benchmarks, and mitigations discussed in the accompanying AI-assisted paper (`/paper/`). It does not claim to be exhaustive of the (very large and fast-moving) long-context literature.
