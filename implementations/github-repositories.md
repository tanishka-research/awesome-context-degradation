# GitHub Implementations

Reference implementations of specific papers and techniques discussed in this repository's research collection. Selected for documentation quality, active maintenance, and direct traceability to a peer-reviewed or arXiv paper (not for star count alone).

- **RULER** — [github.com/hsiehjackson/RULER](https://github.com/hsiehjackson/RULER)
  
  What it implements: The synthetic benchmark generator and evaluation harness from Hsieh et al. (2024), "RULER: What's the Real Context Size of Your Long-Context Language Models?"
  
  Why it's relevant: The most widely adopted diagnostic for measuring the gap between nominal and effective context length; directly reproducible.

- **LongBench** — [github.com/THUDM/LongBench](https://github.com/THUDM/LongBench)
  
  What it implements: The bilingual multi-task benchmark and evaluation scripts from Bai et al. (2024), maintained by THUDM (Tsinghua).
  
  Why it's relevant: Realistic-document complement to RULER's synthetic tasks; actively maintained through LongBench-v2 (2024–2025).

- **StreamingLLM** — [github.com/mit-han-lab/streaming-llm](https://github.com/mit-han-lab/streaming-llm)
  
  What it implements: The attention-sink streaming-inference framework from Xiao et al. (2024, ICLR), including runnable examples for LLaMA-2, MPT, Falcon, and Pythia.
  
  Why it's relevant: A training-free architectural mitigation for one of the four degradation mechanisms (attention dilution / sink behavior) discussed in Section 3.3.

- **Needle In A Haystack** — [github.com/gkamradt/LLMTest_NeedleInAHaystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)
  
  What it implements: Kamradt's original controlled-depth single-fact retrieval pressure test.
  
  Why it's relevant: The historical baseline diagnostic that motivated RULER's more comprehensive multi-hop and aggregation tasks.

- **YaRN** — [github.com/jquesnelle/yarn](https://github.com/jquesnelle/yarn)
  
  What it implements: The RoPE context-extension method from Peng et al. (2024, ICLR), with published model checkpoints (LLaMA-2 and Mistral variants at 32K/64K/128K).
  
  Why it's relevant: A concrete, reproducible instance of the positional-encoding-extension mitigation family discussed in Section 4.3.

- **LLMLingua** — [github.com/microsoft/LLMLingua](https://github.com/microsoft/LLMLingua)

  What it implements: LLMLingua, LongLLMLingua, and LLMLingua-2 (Jiang et al., 2023–2024; Pan et al., 2024), Microsoft's official prompt-compression codebase.
  
  Why it's relevant: Directly implements the prompt-compression mitigation family from Section 4.4, with reproducible compression-ratio benchmarks.
