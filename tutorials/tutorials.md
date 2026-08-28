# Tutorials and Learning Resources

- **Long Context Prompting Tips** (Anthropic official documentation)
  [docs.anthropic.com/en/docs/long-context-window-tips](https://docs.anthropic.com/en/docs/long-context-window-tips)
  
  Practical guidance on document placement, XML structuring, and quote-grounding for long-context prompts — a hands-on counterpart to the positional-bias mitigations discussed academically in Section 3.1 of the paper.

- **Prompting Long Context: A Quantitative Case Study** (Anthropic engineering blog)
  [anthropic.com/news/prompting-long-context](https://www.anthropic.com/news/prompting-long-context)
  
  A reproducible case study (with linked Anthropic Cookbook code) quantifying how quote-extraction and contextual examples improve long-context recall.

- **Effective Context Engineering for AI Agents** (Anthropic engineering blog)
  [anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  
  Frames context as a finite, curated resource for agentic systems — useful background for why curation/compression mitigations (Section 4.4) matter beyond single-turn synthesis.

- **RULER GitHub README and reproduction guide**
  [github.com/hsiehjackson/RULER](https://github.com/hsiehjackson/RULER)
  
  Beyond being a benchmark implementation (also listed under Implementations), the README doubles as a practical tutorial for running your own effective-context-length evaluation on a model of your choice.

- **Retrieval Augmented Generation (RAG)** — DeepLearning.AI short course
  [deeplearning.ai/courses/retrieval-augmented-generation](https://www.deeplearning.ai/courses/retrieval-augmented-generation)
  
  A hands-on course covering retrievers, vector databases, chunking, and evaluation — the practical skill set underlying the RAG-vs-long-context comparisons in Section 2.4 and 4.1 of the paper.
