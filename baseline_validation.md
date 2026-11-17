> Note: this report was written before the real run, on synthetic data. For the real run see `results/reduced/` and `docs/deviation_log.md` (entries RUN-001 to RUN-005).

# Baseline Validation Report (Pre-Run Audit)

**Project:** Context-Window Degradation and Its Impact on Long-Document Research Synthesis (review -> implementation paper)
**Stage:** 8 (baseline validation) | **Report version:** v0.1 | **Date:** 2026-11-04

**Tags used in the findings.** VERIFIED = confirmed by inspecting a file or by a test run whose log is quoted here, or read in a source page opened in an earlier stage. UNCERTAIN = cannot be judged from what exists; the check is named. NEEDS CORRECTION = a defect or gap found; status given.
**Rule followed.** Running without error is not treated as evidence of correctness. No result is quoted that was not produced.

---

## 1. What was audited, and what was missing

**Parameters filled in.** BASELINE = the original position-sweep protocol (B0) with the closed-book (C1) and oracle (C2) controls. PUBLISHED PAPER / OFFICIAL CODE = Lost in the Middle (arXiv 2307.03172) and its MIT-licensed repository. FILES = everything that exists in the project today.

**Present (inspected):** `src/positionorder/seeds.py`, `src/positionorder/data.py`, `scripts/env_check.py`, `scripts/01_validate_data.py`, `tests/test_seeds.py`, `tests/test_data.py`, `configs/protocol_v0.1.yaml`, `docs/deviation_log.md`, and the protocol documents.

**Absent:** a prompt builder, a scorer, an inference runner, closed-book and oracle builders, the question split lists, any console log from your machine, any model output, and any measured result.

**Consequence.** The baseline is not yet implemented, so it cannot be validated as a baseline. This report audits the parts that exist, compares the planned design with the original methodology, and sets the checks that must pass before any extension (RQ2, RQ3, orderings O1 and O2) is run. No comparison with reported results is possible yet, because no result exists.

---

## 2. Summary of findings

| Class | Count | Items |
|---|---|---|
| VERIFIED | 6 | V-1 to V-6 |
| UNCERTAIN | 10 | U-1 to U-10 |
| NEEDS CORRECTION | 3 | C-1 (fixed, rerun pending), C-2 (protocol text), C-3 (fixed, no effect on results) |

---

## 3. Audit against the original methodology

| Aspect | Original (source) | This project | Assessment | Adaptation class |
|---|---|---|---|---|
| Preprocessing: data | 2,655 NaturalQuestions-Open queries, long answer a paragraph; 20 passages, exactly one gold; distractors are top Contriever (MS-MARCO) passages without annotated answers, shown in decreasing relevance order; files per gold index 0, 4, 9, 14, 19 (paper text and README, as read) | Loader and validator read the same file format; checks for one gold, 20 passages, no `hasanswer` in distractors, gold index equal to file name | VERIFIED on synthetic data only; real data UNCERTAIN (U-5, U-6) | Acceptable if files come from the repo's own script |
| Preprocessing: question set | All 2,655 queries | 100 development plus 300 evaluation questions, drawn from valid ones | **NEEDS CORRECTION (C-2):** the protocol does not say a question must be present and clean in all five position files | Sampling is an acceptable, declared adaptation (wider intervals) |
| Architecture / model | MPT-30B-Instruct (8K), LongChat-13B (16K), GPT-3.5-Turbo, Claude-1.3; Llama-2 supplementary (paper) | Qwen2.5-3B-Instruct, GGUF Q4_K_M, llama.cpp server | Plan only; model and licence terms UNCERTAIN (U-9) | Acceptable and declared; absolute numbers are not comparable |
| Prompt | Documents formatted `Document [i](Title: ...) text`, i from 1; question template loaded from prompt files; closed-book function exists; variants for random ordering and query-aware contextualization (`prompting.py`) | Not implemented | UNCERTAIN (U-2): template text not read; chat template handling in the server unknown (U-4) | Template wording must match the repo's files; chat template adaptation is acceptable if declared |
| Hyperparameters | Greedy decoding (paper). Maximum generation length: not seen | Greedy, batch size 1; 64 new tokens proposed | UNCERTAIN (U-3) | 64 is acceptable only if it cannot cut a complete answer |
| Random seeds | Greedy decoding, so no sampling seed | Seeds fixed for split, orderings, bootstrap; derived per question | VERIFIED (V-2, V-4) | Acceptable (extension-specific) |
| Evaluation metric | Correct if any accepted answer appears in the output (paper); repo scripts report `best_subspan_em` (EXPERIMENTS.md) | Protocol text defines a normalised substring match | UNCERTAIN (U-1): matching rule of the repo function not read | Reimplementing it is a deviation; calling the repo's function is preferred |
| Data split | No train/test split; all queries used | Development / evaluation split of questions; seeds fixed | Design VERIFIED by inspection (V-4); disjointness untested (needs real ids) | Acceptable (no training involved) |
| Benchmark protocol | 10-, 20-, 30-document settings; closed-book and oracle reference results (paper) | 20 documents; C1 and C2; B0 | Matches for 20 documents; positions equal the README's | Acceptable; 10/30 documents optional |
| Runtime / precision | Hugging Face scripts on A100 80 GB (EXPERIMENTS.md); APIs | Quantised 4-bit model, llama.cpp | UNCERTAIN (U-7): quantisation effect unknown | Acceptable if declared and checked |

---

## 4. Findings

### VERIFIED

| ID | Finding | Evidence |
|---|---|---|
| V-1 | The original protocol facts in Section 3 (20 passages, one gold, relevance-ordered distractors, positions 0/4/9/14/19, greedy decoding, any-answer-present metric, MIT licence for the repo code) | Source pages read in earlier stages, through a fetch tool; open the originals to confirm wording |
| V-2 | Seed derivation is repeatable, independent of call order, different for O1 and O2, and stable across processes | Sandbox run of `env_check.py`: four `[PASS] seed:` lines; `tests/test_seeds.py` functions all passed. These ran in a Linux sandbox, not on your machine |
| V-3 | The validator detects injected faults on synthetic files: wrong passage count, two golds, answer-bearing distractor, gold at the wrong index, missing keys, changed distractor order across files | Sandbox log: 8 of 8 tests in `tests/test_data.py` PASS after correction C-1; CLI on a deliberately broken synthetic file exited with code 2, and on a clean one with 0 |
| V-4 | `configs/protocol_v0.1.yaml` matches the protocol document: seeds 1234, 4321, 101, 202, 777, 0; positions 0, 4, 9, 14, 19; 100 development and 300 evaluation questions; 20 documents | File inspection |
| V-5 | The 1-based document numbering in prompts versus the 0-based gold index in files is recorded in the protocol and README | File inspection; source `prompting.py` formatting as read |
| V-6 | No measured result, model output or log from your machine exists in the project | Inventory in Section 1 |

### UNCERTAIN

| ID | Question | Why it matters | Check |
|---|---|---|---|
| U-1 | Does the repo's `best_subspan_em` match by normalised substring, or by token sequence? Which normalisation does it apply? | A more lenient or stricter scorer changes every accuracy and flip rate | E-3 |
| U-2 | Exact wording of `qa.prompt`, `closedbook_qa.prompt`, `qa_ordered_randomly.prompt`, `qa_with_query_aware_contextualization.prompt`; whether the random-ordering variant should be used for O1 and O2 | Using a different template for some orderings would break the paired comparison | E-4 |
| U-3 | Maximum generated tokens and any answer-extraction step in the repo's response scripts | A cap that is too low would cut complete answers | E-4 |
| U-4 | Whether `llama-server` applies the Qwen chat template to `/v1/chat/completions` requests, and which template | A wrong or missing template can change accuracy and the position curve | E-5 |
| U-5 | Whether the repo-generated position files keep the same questions, the same distractors, and the same distractor order (assumptions A-005, A-006) | The ordering design rests on it | E-2 |
| U-6 | Availability of the retrieval file from your network, and which NQ-Open split the 2,655 questions come from | Data cannot be built without it; the split affects contamination reasoning | E-1, E-2 |
| U-7 | Effect of Q4_K_M quantisation on accuracy | Could change the baseline for reasons unrelated to position | E-9 |
| U-8 | Prompt token counts against the context size (truncation) | Silent truncation invalidates a condition | E-6 |
| U-9 | Terms of the `qwen-research` licence; model file hash | Permitted use; reproducibility | E-12 |
| U-10 | Run-to-run determinism of the server at batch size 1 | Sets the noise floor for flip rates | E-7 |

### NEEDS CORRECTION

| ID | Defect | Status |
|---|---|---|
| C-1 | **Boolean parsing.** The loader used `bool(...)` on `isgold` and `hasanswer`. A string `"false"` was read as true. Probe log (sandbox): input string `'false'` for `hasanswer` -> loaded value `True`, and the validator then reported `['distractor_has_answer']`. | **Fixed in v1.1:** the loader now requires JSON booleans and raises `DataFormatError`. New test `test_non_boolean_flags_are_rejected` passes in the sandbox. Real-data rerun pending |
| C-2 | **Protocol gap.** The protocol (Section 5, Section 6) samples questions from the valid ones but does not require a question to be present and clean in all five position files. Without this rule a question could enter the evaluation set for some positions and not others, breaking the pairing. | Not yet applied. Amendment text for protocol v0.2: "Eligible questions are those present in all five position files with no problem code in any file. Development and evaluation questions are drawn only from this set." Apply before the freeze and log it |
| C-3 | **Efficiency.** `01_validate_data.py` read each file twice. No effect on results. | Fixed in v1.1 (`validate_file` accepts loaded examples). CLI rerun on synthetic files: exit code 0 |

---

## 5. Unit and sanity tests

| ID | Test | Protects against | Status | Pass condition |
|---|---|---|---|---|
| T-1 | Seed determinism, call-order independence, cross-process stability | Irreproducible orderings | Implemented; passes in sandbox | All pass on your machine too |
| T-2 | Loader and validator on synthetic faults | Silent data problems | Implemented; passes in sandbox (8 tests) | All pass on your machine |
| T-3 | Validator on the real files | Wrong data, A-002 to A-006 | Needs real data | Exit code 0, or each problem explained and handled by a logged rule |
| T-4 | Eligible-question rule: intersection of clean questions across five files | C-2 | To write in cycle 2 | Set sizes logged; every selected question present in all files |
| T-5 | Split: development and evaluation disjoint; duplicates removed first | Leakage | To write in cycle 2 | Intersection empty; hashes recorded |
| T-6 | Prompt builder: gold appears as `Document [p+1]`; the 19 distractors keep the same relative order across p; for O1 and O2 the distractor sequence is the same across p | Design violations | To write | All properties hold on 100 development questions |
| T-7 | Scorer vs repo function on a fixed list of (prediction, answers) pairs, including case, punctuation, articles, partial-word matches, multiple answers | U-1 | To write after E-3 | Identical decision on every pair, or each difference explained |
| T-8 | Controls ordering: oracle accuracy above closed-book accuracy on the development set | Prompt, scorer or data-pipeline bug | Needs runs | Holds; if not, stop and diagnose before any other step. The original paper reports oracle above closed-book for each listed model (VERIFIED, as read), which is why this is a sanity rule. It is a pipeline check, not an expected outcome of the study |
| T-9 | No silent truncation: prompt tokens plus new tokens within context size for every prompt | U-8 | Needs tokenizer and runs | Zero violations |
| T-10 | Determinism: 100 development prompts run twice | U-10 | Needs runs | Zero differing outputs, or the differences reported as the noise floor |
| T-11 | Quantisation sensitivity: Q4_K_M vs a higher-precision file on 100 development questions at positions 0 and 9 | U-7 | Needs runs and memory headroom | Differences reported with intervals; large differences flagged before extensions |

---

## 6. Comparison with reported results

No measured results exist, so no comparison is possible now.

**What will be compared later, and how.**
- The original reports closed-book and oracle accuracies for its own models, and a U-shaped position curve (paper, as read). The models differ from yours, so exact numerical agreement is neither expected nor required.
- Validation criteria are about the pipeline: T-6 to T-11. Whether this model shows a U-shape is a study result (RQ1), not a validation test, because a small model may not show it.
- A baseline counts as validated when the pipeline checks pass and every adaptation is declared. It does not count as validated because its numbers resemble published ones.

---

## 7. Acceptable adaptations and changes that would invalidate comparison

**Acceptable if declared in `docs/deviation_log.md`:** a smaller, quantised model; the llama.cpp runner; a 300-question sample instead of 2,655; the Qwen chat template around the original prompt content; 64 or another generation cap that provably does not cut answers; a different GPU.

**Invalidating or requiring re-labelling as a different protocol:**
- Building distractors differently (for example randomly instead of by retrieval) while still calling it the original protocol.
- Using different questions, or different eligible sets, in different conditions.
- Dropping or editing questions after seeing model outputs.
- A scorer more lenient or stricter than the original's without disclosure.
- Different prompt templates across orderings or positions.
- Silent truncation of long prompts.
- Tuning the template, scorer or thresholds on the evaluation questions.
- Reusing development questions in the evaluation set.
- Non-greedy decoding without declaring it.

---

## 8. Exact additional checks required (paste the outputs back)

| # | Check | What to run or read | Resolves |
|---|---|---|---|
| E-1 | Download the retrieval file; record size and SHA-256 | `Invoke-WebRequest ...` and `Get-FileHash ...` from the README | U-6 |
| E-2 | Generate the five position files with the repo's own loop, then validate | `python scripts\01_validate_data.py --qa-dir external\lost-in-the-middle\qa_data` (use the corrected v1.1 files) | U-5, U-6, T-3 |
| E-3 | Read `scripts/evaluate_qa_responses.py` and the function behind `best_subspan_em`; paste its matching and normalisation logic | Open the file | U-1, T-7 |
| E-4 | Read the four prompt files and the response scripts' generation arguments; paste the template text and the maximum-new-tokens setting | Open `prompts/` and `scripts/get_qa_responses_from_*.py` | U-2, U-3 |
| E-5 | Start `llama-server` with the model; paste the start-up log lines about the chat template and layer offload; send one test chat request and paste the raw response | Server log; one request | U-4 |
| E-6 | Tokenise a sample of prompts; paste min, median, max token counts | Cycle 2 prompt builder | U-8, T-9 |
| E-7 | Run the 100-prompt determinism test; paste the count of differing outputs | Cycle 3 | U-10, T-10 |
| E-8 | Run closed-book and oracle on the development set; paste the two accuracies with N | Cycle 3 | T-8 |
| E-9 | If memory allows, repeat 100 development questions at positions 0 and 9 with a higher-precision file | Cycle 3 | U-7, T-11 |
| E-10 | Paste the console output of `python -m pytest tests -q` and `python scripts\env_check.py` | Your machine | T-1, T-2, environment |
| E-11 | Read the model's LICENSE text; record the model file SHA-256 (the environment test prints it) | Files | U-9 |
| E-12 | Apply amendment C-2 to the protocol (v0.2) and log it before the freeze | Edit and log | C-2 |

---

## 9. Gate

No extension is to be run, and no result is to be interpreted, until: C-1 is confirmed on real data; C-2 is applied; U-1 to U-6 are resolved; T-3 to T-10 pass; and the outputs of E-1 to E-11 have been shared and reviewed. Then the baseline (B0, C1, C2) is run on the development set first, then frozen and run on the evaluation set.

---

## Sources

- [Lost in the Middle repository](https://www.github.com/nelson-liu/lost-in-the-middle), [`prompting.py`](https://github.com/nelson-liu/lost-in-the-middle/blob/main/src/lost_in_the_middle/prompting.py), [EXPERIMENTS.md](https://github.com/nelson-liu/lost-in-the-middle/blob/main/EXPERIMENTS.md); [paper, arXiv 2307.03172](https://arxiv.org/abs/2307.03172v3) and a [full-text copy](https://ar5iv.labs.arxiv.org/html/2307.03172).
- Earlier project documents: experimental protocol v0.1, dataset and baseline plan, environment setup guide, deviation log.
