# AI Assistance Log

**Project:** position and order sensitivity of a small local language model in multi-document question answering
**Report version:** v0.1 | **Date:** 2026-11-13

## 0. Evidence basis and limits (read first)

- **Source of this report:** the conversation itself, plus the files the assistant created and tests it ran in its own sandbox. Prompt wording below is summarised; paste the verbatim prompts from your chat export into Appendix A before submitting.
- **No commits exist.** The project folder is not a git repository, so there are no commit hashes. Changes are recorded as dated file edits and the patch archives delivered.
- **Nothing has been executed on the author's machine.** No console output, data file, model output or measured result has been supplied. Every "verification" below was performed by the assistant in a sandbox on synthetic data, unless stated otherwise.
- **Tool:** Claude (model configured as `claude-sonnet-5-5`; the serving model in earlier turns is UNKNOWN) in an agentic coding environment, with a restricted network.
- **Scientific choices were delegated to the AI.** The author instructed that the assistant should decide the topic and the gaps ("take the decision on what topic ... and what gaps"). This must be disclosed in any submission.

## 1. Activity log

| # | Date | Task | Prompt (summary) | AI proposal | Human decision | Verification method | Code or result change | Outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | Oct 2026 | Decision log for a literature-review-to-paper project | P1 | `research_decisions.md` structure, evidence tags | Chose the staged workflow; asked for md and PDF | None by the author recorded; PDF conversion checked in sandbox | Files created | Delivered; later superseded by the topic change |
| 2 | Oct 2026 | Gap matrix from the review | P2 | Five gaps, three ranked | Asked for a final md and PDF with nothing extra | Passage locations cited from the attached review; claims flagged as needing source checks | `gap_matrix.md/.pdf` | Delivered; not checked against originals by the author (UNKNOWN) |
| 3 | Oct 2026 | Pick topic, methods, study | P3-P5 | Replication with decomposition of a published position-sweep protocol; research questions; one-page brief | **Delegated the choice to the AI** | AI searched and read sources through summarising tools; novelty explicitly not claimed | Mapping, feasibility, brief files | Study chosen by AI; author review of the choice not recorded |
| 4 | Oct-Nov 2026 | Dataset, baseline and protocol design | P6, P7 (sent twice) | Dataset plan, controls, orderings, seeds, thresholds, diagrams | Not recorded beyond acceptance | Cross-reference check in the protocol file | Protocol v0.1, config | Thresholds are AI-proposed author choices, to be confirmed |
| 5 | Nov 2026 | Environment and cycle-1 code | P8, P9 | Setup guide, `env_check.py`, seed module, data loader and validator, 12 tests | Asked for work after P8 | Sandbox unit tests on synthetic data | Repo created, `cycle01_files.zip` | Never run by the author on real data |
| 6 | 5 Nov 2026 | Audit of the baseline | P10 | Validation report; loader fix | Not recorded | Probe and tests in sandbox | Loader, script, test, deviation log patched (`patch_v1.1.zip`) | Defect fixed in sandbox; real-data rerun pending |
| 7 | 13 Nov 2026 | Debug-log entry | P11 | Log with one real case plus template | None recorded | None beyond Activity 6 | `ai_debugging_log.md/.pdf` | See 3.1 |
| 8 | 13 Nov 2026 | Pathway comparison and test plan | P12 | Recommended controlled comparison with reproduction first | None recorded | None (no data) | `study_pathways_and_test_plan.md/.pdf` | Plan only |
| 9 | 13 Nov 2026 | Evaluation code | P13 | Audit, bootstrap, paired tests, figure; 11 tests | None recorded | Sandbox tests; synthetic run; figure inspected | `evaluation_v1.zip` | See 3.2 |
| 10 | 13 Nov 2026 | Results analysis, paper draft, review, README | P14-P17 | Scaffolds and status tables; refused to analyse absent data | Left the placeholders unfilled | Test compile (stand-in class); secret scan | `paper_overleaf.zip`, `readme_v1.zip` | See 3.3 and 3.4 |

Prompts P11-P17 were sent with template placeholders unfilled; the assistant did not invent values and asked for the real inputs. That is a real observation, not a success claim about the work.

## 2. Code and file changes with outcomes (all sandbox-verified only)

| Change | Reason | Evidence |
|---|---|---|
| `data.py`: JSON-boolean check for `isgold`, `hasanswer` | String `"false"` loaded as true | Probe in sandbox; new test passes |
| `01_validate_data.py`, `validate_file`: load each file once | Double read | Synthetic CLI run exit 0 |
| `evaluate.py` plot: dodge, fixed ticks, legend below | First render overlapped | Re-rendered image inspected |
| `.gitignore`: weights, data, credentials, raw outputs | Privacy and licence review | Text search found no secrets |
| Tests: 12 initially, 23 after evaluation module | Coverage | Plain runner: 23 run, 0 failed (pytest not installed in sandbox) |

## 3. Real examples of AI limitation, correction and purposeful verification

### 3.1 A plausible defect written by the AI (caught by audit)
The AI-written loader used `bool()` on JSON flags, so `"false"` became true; the validator then reported a distractor containing an answer. It was found during the audit requested in P10, confirmed with a probe, and fixed with a strict check and a test. **Lesson:** code that ran and passed its own first tests was still wrong. The original tests did not exercise string-typed flags.

### 3.2 A visual defect in generated output
The first evaluation figure had overlapping error bars at each position, a legend on top of data, and tick labels at 2.5 and 12.5 for positions that are 0, 4, 9, 14, 19. The AI looked at the image, then added horizontal offsets, set ticks to the design positions and moved the legend. The figure used synthetic data and is not a result.

### 3.3 A dependency gap introduced by the AI
The evaluation module imports `matplotlib`, but `requirements.in` did not list it. It was found only during the README review and is flagged there, not yet fixed in the file. Tests in the sandbox did not catch it because the sandbox had the package.

### 3.4 Blocked verification and mislabelled attachments
- The sandbox could not reach the package index, the dataset host, or most pages; several pages were read through a summarising fetch tool, not verbatim. Consequence: no package versions were stated, the scorer and prompt text were not read, and the evidence tags state "read through a summarising tool".
- The attachments in one turn belonged to a different project (the labelling review); the AI noticed, said so, and worked from the files supplied.
- A protocol file had wrong section cross-references (15 vs 16, 4 vs 5); fixed with a text replace and not re-reviewed by the author (UNKNOWN).
- In the first turn a PDF conversion was reported as not run; it was rerun when the context was supplied again.

At least four real items exist, so the three-example minimum is met from the record. No item here is a claim of performance gain.

## 4. Which conclusions depended on human reasoning

| Conclusion or decision | Who made it | Status |
|---|---|---|
| Topic, gap and study design | The AI, by delegation | The author has not recorded an independent justification. **Write one before submission** |
| Decision thresholds (5 points and others) | The AI proposed; "to be confirmed" by the author | Open |
| Sandbox-only test results | The AI | Not substitutes for author runs |
| Honest reporting that no results exist | The AI, held in every turn | Author should keep this discipline |
| Real-data validity, model behaviour, any scientific finding | No one yet | UNKNOWN: no experiment run |

At present there is no recorded conclusion that rests on the author's own reasoning or measurements. This is the main integrity gap.

## 5. What was learned about AI-assisted ("vibe") coding, from the events above

1. Fluent, tested code can hide a wrong assumption (3.1). Tests written by the same assistant that wrote the code share its blind spots.
2. Passing synthetic tests proves the code matches the assistant's description of the data, not the real data.
3. Inspecting outputs (the figure) and probing inputs found defects that reading the code did not.
4. Network limits mean facts about versions, files and licences stay unverified; the labels UNKNOWN and "printed only" kept that visible.
5. Template prompts with blanks invite invented content; refusing to fill them avoided fabricated results but stalled progress until real inputs exist.

## 6. Remaining risks

- No real data, model, run, log or result exists; scientific claims cannot yet be made.
- Study choice was delegated; reviewers or instructors may ask for the author's reasoning.
- Novelty unverified: nearby published work exists and the logged search is incomplete.
- Source facts rest partly on summarising tools: re-read originals.
- Scorer semantics, prompt template, token cap, chat template, quantisation effect: unresolved.
- Citation metadata incomplete (`{TO VERIFY}`).
- Licence terms for the model and data not confirmed; repository licence undecided.
- The PDFs and archives are not under version control; commit hashes are absent.

## 7. Actions that would close the gaps

1. Initialise git, commit the current state, record the first hash.
2. Run the tests, environment check and data validation on your machine; paste the outputs into the log.
3. Add your own written rationale for the topic, gap and thresholds, with dates.
4. Re-read each cited source in full; fix the bibliography.
5. Fill Appendix A with your verbatim prompts.

## Appendix A: verbatim prompts

`[TO FILL]` Paste P1-P17 exactly from your chat export.


## Update after the real run (Nov 2026)

- The experiment was run by the author on Google Colab (Tesla T4). The output bundle is in `results/reduced/`; it replaces the statement above that nothing had been executed on the author's machine.
- The AI assistant recomputed every accuracy and paired test from `predictions.csv` independently of the project's evaluation code; all values matched `results.csv`.
- The AI assistant wrote the paper text; tables are generated from `results.csv` by `paper/experiment/make_tables.py`. Reference metadata (authors, titles) was taken from the arXiv pages. The paper's descriptions of related work rest on abstracts only.
- The decision rule in `configs/freeze_reduced.json` was proposed by the AI assistant; the author is to confirm it. The topic and design were also chosen by the AI assistant on the author's delegation.
- Requests to fabricate results or to disguise AI use were declined. The paper carries an AI-assistance statement.
- Still open: labelling of the manual audit sample; the second shuffle and the two missing gold positions; the question-repetition test.
