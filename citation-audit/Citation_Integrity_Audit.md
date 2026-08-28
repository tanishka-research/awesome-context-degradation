# Citation Integrity Audit

**Paper audited:** *Context-Window Degradation and Its Impact on Long-Document Research Synthesis*
**Audit method:** Every reference in the paper's "Complete References" list was checked against arXiv, the publisher/DOI record, or (for one software resource) the GitHub repository itself, for: correct title, correct authors, correct year, correct venue, working DOI/arXiv ID, and confirmation that the paper genuinely exists and matches the citing text. Verification sources used: arXiv.org, Semantic Scholar, publisher DOI pages, ACL Anthology, and OpenReview/ICLR proceedings pages.

## Verification Log — In-Paper References

| # | Reference (short form) | Title/Authors/Year Verified? | Venue Verified? | Link Verified & Resolves? | Notes |
|---|---|---|---|---|---|
| 1 | Bai et al., 2024 — LongBench | ✅ | ✅ ACL 2024 | ✅ arXiv:2308.14508 | Confirmed against GitHub (THUDM/LongBench) and ACL Anthology record. |
| 2 | Hsieh et al., 2024 — RULER | ✅ | ✅ COLM 2024 | ✅ arXiv:2404.06654 | Confirmed against official repo (hsiehjackson/RULER). |
| 3 | Huang et al., 2023 — Long-context transformer survey | ✅ | ✅ arXiv preprint | ✅ arXiv:2311.12351 | Survey status confirmed (not peer-reviewed at time of citation; correctly presented as such). |
| 4 | Kamradt, 2023 — Needle in a Haystack | ✅ | N/A (software) | ✅ GitHub repo | Correctly cited as a software repository, not a paper — appropriate practice. |
| 5 | Kazemnejad et al., 2023 — Positional encoding & length generalization | ✅ | ✅ NeurIPS 2023 | ✅ arXiv:2305.19466 | Matches claim in Section 2.1 about no PE scheme matching implicit generalization. |
| 6 | Li, K. et al., 2025 — LaRA | ✅ | ✅ arXiv preprint | ✅ arXiv:2502.09977 | Confirmed the paper explicitly argues against prior RAG-vs-LC benchmark design, as cited. |
| 7 | Li, Z. et al., 2024 — RAG or Long-Context LLMs? | ✅ | ✅ EMNLP 2024 Industry Track | ✅ arXiv:2407.16833 | Confirmed "Self-Route" hybrid method is correctly attributed. |
| 8 | Liu, J. et al., 2025 — Long-context survey | ✅ | ✅ arXiv preprint | ✅ arXiv:2503.17407 | Large-author-list survey; author list in paper is abbreviated with "et al." appropriately given >30 authors. |
| 9 | Liu, N. F. et al., 2024 — Lost in the Middle | ✅ | ✅ TACL, Vol. 12 | ✅ DOI 10.1162/tacl_a_00638 / arXiv:2307.03172 | Core citation; confirmed U-shaped curve finding matches paper's description exactly. |
| 10 | Press et al., 2022 — ALiBi | ✅ | ✅ ICLR 2022 | ✅ arXiv:2108.12409 | Confirmed. |
| 11 | Su et al., 2024 — RoFormer | ✅ | ✅ Neurocomputing | ✅ DOI 10.1016/j.neucom.2023.127063 / arXiv:2104.09864 | Note: original preprint 2021, journal version 2024 — paper correctly cites the journal (2024) version. |
| 12 | Xiao et al., 2024 — StreamingLLM | ✅ | ✅ ICLR 2024 | ✅ arXiv:2309.17453 | Confirmed against official repo (mit-han-lab/streaming-llm). |
| 13 | Xu et al., 2024 — Retrieval meets long context | ✅ | ✅ ICLR 2024 | ✅ arXiv:2310.03025 | Listed in references but not directly cited in-text by name; flagged below. |

**Result: 13/13 references verified as genuine, correctly attributed, and correctly linked.** No fabricated, mismatched, or non-existent references were found.

## Observations / Minor Issues Flagged

1. **Xu et al. (2024)** appears in the reference list but is not explicitly named in the body text (it may be folded into general discussion of RAG/long-context hybrids in Section 2.4/4.1). Recommendation: either cite it explicitly where relevant or remove it — currently it is a orphaned reference. *(Kept in this repository's collection because it is independently verifiable and topically relevant.)*
2. **In-text claims were spot-checked against source abstracts**, not full-text re-derivation of every statistic (e.g., specific accuracy percentages from RULER or Liu et al. were not independently re-run). This audit confirms the *references exist, are correctly attributed, and plausibly support the claims made*, not that every quantitative figure was independently reproduced — that would require re-running the cited benchmarks, which is outside the scope of a citation-integrity audit.
3. No AI-generated or "hallucinated" citations were detected. All DOIs and arXiv IDs resolved to the correct paper on the first attempt.

## Additional Papers Added for This Repository

To meet the 20-paper minimum for the Awesome repository (the review paper itself cites 13 sources), 7 additional papers were sourced and independently verified using the same method before being added to `/references/references.md`:

- Hsieh, C.-Y. et al. (2024) — *Found in the Middle* (arXiv:2406.16008)
- Chen, S. et al. (2023) — *Position Interpolation* (arXiv:2306.15595)
- Peng, B. et al. (2024) — *YaRN* (arXiv:2309.00071)
- Jiang, H. et al. (2023) — *LLMLingua* (arXiv:2310.05736)
- Jiang, H. et al. (2023) — *LongLLMLingua* (arXiv:2310.06839)
- Pan, Z. et al. (2024) — *LLMLingua-2* (arXiv:2403.12968)
- Jiang, Z. et al. (2024) — *LongRAG* (arXiv:2406.15319)
- Ji, Z. et al. (2023) — *Survey of Hallucination in NLG* (arXiv:2202.03629)

Each was checked for title/author/year accuracy and link resolution against arXiv directly, following the same verification standard applied above.

## Core Rule Compliance

Per the activity's core rule — *"Never accept a reference merely because an AI tool generated it"* — every reference in this repository, whether originally cited in the paper or added to reach the 20-paper minimum, was independently checked against a primary source (arXiv abstract page, publisher DOI, or official GitHub repository) rather than accepted on the basis of an AI tool's output alone.
