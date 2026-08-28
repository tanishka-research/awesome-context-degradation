# Tools and Libraries

Software libraries relevant to studying, measuring, or mitigating context-window degradation.

- **LLMLingua**
  [github.com/microsoft/LLMLingua](https://github.com/microsoft/LLMLingua)
  
  Microsoft's official prompt-compression toolkit implementing LLMLingua, LongLLMLingua, and LLMLingua-2. Directly operationalizes the "prompt compression" mitigation family discussed in Section 4.4 of the paper.

- **LangChain**
  [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
  
  A widely used orchestration framework for building retrieval-augmented generation (RAG) pipelines — chunking, embedding, retrieval, and prompt assembly. Relevant to the RAG mitigation strategy (Section 4.1).

- **LlamaIndex**
  [github.com/run-llama/llama_index](https://github.com/run-llama/llama_index)
  
  A data-framework alternative/complement to LangChain, purpose-built for connecting LLMs to external document corpora via indexing and retrieval — the core architecture RAG-based mitigations rely on.

- **StreamingLLM**
  [github.com/mit-han-lab/streaming-llm](https://github.com/mit-han-lab/streaming-llm)
  
  Reference implementation of the attention-sink-preserving streaming inference framework from Xiao et al. (2024), enabling stable generation over effectively unbounded input by retaining a small number of initial "sink" tokens.

- **FlashAttention**
  [github.com/Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention)
  An IO-aware exact-attention implementation that reduces the memory/compute cost of the quadratic self-attention operation discussed in Section 2.1 of the paper — a computational prerequisite for practical long-context inference, distinct from (but complementary to) the positional and attentional mitigations discussed in Section 4.
