"""Question selection, document assembly, resumable job running and the predictions table (cycle 6).

Nothing here loads a model: the caller passes `generate_fn(prompt) -> (text, n_prompt_tokens,
n_new_tokens, truncated)`. That keeps the logic testable offline with a dummy generator.
"""
from __future__ import annotations

import dataclasses
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .data import QAExample, validate_example
from .scoring import first_line, score_reply
from .seeds import derive_seed, distractor_permutation

ORDERING_SEEDS = {"O1": 101, "O2": 202}   # protocol seeds
CONTROLS = ("C1", "C2")


# ----------------------------------------------------------------- question selection
def eligible_qids(by_position: Dict[int, List[QAExample]], total_documents: int = 20):
    """Questions that are present once and clean in every position file, with the same gold passage and
    the same distractor sequence in all files (amendment C-2). Returns (sorted qids, exclusion counts)."""
    positions = sorted(by_position)
    maps: Dict[int, Dict[str, List[QAExample]]] = {}
    for p in positions:
        m: Dict[str, List[QAExample]] = {}
        for ex in by_position[p]:
            m.setdefault(ex.qid, []).append(ex)
        maps[p] = m
    all_ids = set().union(*[set(m) for m in maps.values()])
    reasons = {"duplicate_in_file": 0, "missing_in_some_file": 0, "validation_problem": 0,
               "inconsistent_across_files": 0}
    ok: List[str] = []
    for q in sorted(all_ids):
        if any(len(m.get(q, [])) > 1 for m in maps.values()):
            reasons["duplicate_in_file"] += 1
            continue
        if any(q not in maps[p] for p in positions):
            reasons["missing_in_some_file"] += 1
            continue
        exs = [maps[p][q][0] for p in positions]
        if any(validate_example(ex, total_documents, p) for ex, p in zip(exs, positions)):
            reasons["validation_problem"] += 1
            continue
        golds = {tuple(x.text.strip() for x in ex.passages if x.isgold) for ex in exs}
        seqs = {tuple(x.text.strip() for x in ex.passages if not x.isgold) for ex in exs}
        if len(golds) != 1 or len(seqs) != 1:
            reasons["inconsistent_across_files"] += 1
            continue
        ok.append(q)
    return ok, reasons


def split_questions(eligible: List[str], seed: int, n_dev: int, n_eval: int) -> Dict[str, List[str]]:
    """Disjoint dev and eval lists, in a seed-determined order (take prefixes for smaller runs)."""
    if len(eligible) < n_dev + n_eval:
        raise ValueError(f"only {len(eligible)} eligible questions; need {n_dev + n_eval}")
    ids = sorted(eligible)
    rng = np.random.Generator(np.random.PCG64(derive_seed(seed, "split")))
    chosen = [ids[i] for i in rng.permutation(len(ids))[: n_dev + n_eval]]
    return {"dev": chosen[:n_dev], "eval": chosen[n_dev:]}


# ----------------------------------------------------------------- documents and jobs
def docs_for(ex: QAExample, condition: str, gold_index: Optional[int]) -> List[dict]:
    """Document dicts for one condition. O0 and R keep the file's order; O1/O2 shuffle only the distractors
    (per-question SHA-256 seed) and put the gold passage at `gold_index`; C1 has no documents; C2 only the gold."""
    passages = [dataclasses.asdict(p) for p in ex.passages]
    gold = [p for p in passages if p["isgold"]]
    dist = [p for p in passages if not p["isgold"]]
    if len(gold) != 1:
        raise ValueError(f"question {ex.qid}: expected exactly one gold passage, found {len(gold)}")
    if condition in ("O0", "R"):
        return passages
    if condition == "C1":
        return []
    if condition == "C2":
        return gold
    if condition in ORDERING_SEEDS:
        if gold_index is None:
            raise ValueError("gold_index required")
        perm = distractor_permutation(ORDERING_SEEDS[condition], ex.qid, len(dist))
        out = [dist[i] for i in perm]
        out.insert(gold_index, gold[0])
        return out
    raise ValueError(f"unknown condition {condition}")


@dataclass(frozen=True)
class Job:
    split: str
    condition: str
    gold_index: Optional[int]
    qid: str
    run_id: int = 0

    def key(self) -> str:
        return f"{self.split}|{self.condition}|{self.gold_index}|{self.qid}|{self.run_id}"


def make_jobs(split: str, qids: Iterable[str], plan: List[Tuple[str, Optional[List[int]]]]) -> List[Job]:
    """plan: [(condition, positions or None)], jobs are grouped by condition block, then position."""
    qids = list(qids)
    jobs: List[Job] = []
    for cond, positions in plan:
        for g in (positions if positions is not None else [None]):
            jobs += [Job(split, cond, g, q) for q in qids]
    return jobs


def load_rows(path) -> List[dict]:
    p = Path(path)
    rows: List[dict] = []
    if not p.exists():
        return rows
    with open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                break          # a half-written last line after a disconnect: it will be redone
    return rows


def row_key(r: dict) -> str:
    return f"{r['split']}|{r['condition']}|{r['gold_index']}|{r['qid']}|{r['run_id']}"


def run_jobs(jobs: List[Job], build_prompt: Callable[[Job], str], generate_fn, out_path,
             progress_every: int = 100, log=print) -> int:
    """Run jobs not yet in `out_path`, appending one JSON line per job. Returns the number run now."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {row_key(r) for r in load_rows(out_path)}
    todo = [j for j in jobs if j.key() not in done]
    log(f"{len(jobs)} jobs, {len(done)} already done, {len(todo)} to run")
    t0 = time.time()
    n = 0
    with open(out_path, "a", encoding="utf-8") as fh:
        for j in todo:
            prompt = build_prompt(j)
            t = time.time()
            text, n_prompt, n_new, truncated = generate_fn(prompt)
            fh.write(json.dumps({"split": j.split, "condition": j.condition, "gold_index": j.gold_index,
                                 "qid": j.qid, "run_id": j.run_id, "model_answer": text,
                                 "n_prompt_tokens": n_prompt, "n_new_tokens": n_new,
                                 "truncated": int(truncated), "seconds": round(time.time() - t, 4)}) + "\n")
            fh.flush()
            n += 1
            if n % progress_every == 0:
                el = time.time() - t0
                log(f"  {n}/{len(todo)} done, {el / n:.2f} s per prompt, about {(len(todo) - n) * el / n / 60:.0f} min left")
    return n


# ----------------------------------------------------------------- predictions and analysis helpers
FAILURE_RULES = [  # fixed before any result is seen; first matching rule wins
    ("empty_first_line", lambda fl: fl == ""),
    ("no_answer_or_refusal", lambda fl: re.search(
        r"\b(no information|no answer|not (mentioned|provided|specified|stated|found|clear|say)|do not|does not|did not|don't|doesn't|cannot|can't|unknown|unable)\b",
        fl.lower()) is not None),
]


def failure_category(model_answer: str, correct: int) -> str:
    if correct:
        return "correct"
    fl = first_line(model_answer)
    for name, rule in FAILURE_RULES:
        if rule(fl):
            return name
    return "other_wrong"


def to_predictions(rows: List[dict], answers_by_qid: Dict[str, List[str]], settings: dict,
                   repo_scorer=None) -> pd.DataFrame:
    """Long table in the schema of docs/evaluation_schema.md. If `repo_scorer` (the repository's
    best_subspan_em) is given, every score is cross-checked and a mismatch raises."""
    keys = [row_key(r) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate job keys in the raw output file")
    out = []
    for r in rows:
        ans = answers_by_qid[r["qid"]]
        c = score_reply(r["model_answer"], ans)
        if repo_scorer is not None:
            ref = int(repo_scorer(prediction=first_line(r["model_answer"]), ground_truths=ans))
            if ref != c:
                raise ValueError(f"scorer disagreement for {row_key(r)}: local {c}, repository {ref}")
        out.append({"qid": r["qid"], "split": r["split"], "condition": r["condition"],
                    "gold_index": np.nan if r["gold_index"] is None else r["gold_index"],
                    "run_id": r["run_id"], "correct": c, "n_prompt_tokens": r["n_prompt_tokens"],
                    "truncated": r["truncated"], **settings,
                    "failure": failure_category(r["model_answer"], c)})
    return pd.DataFrame(out)


def standard_pairs(positions=(0, 4, 9, 14, 19), position_pairs=((0, 9), (0, 19), (9, 19))):
    """Paired comparisons fixed in advance: order effect, position effect, rerun noise."""
    pairs = []
    for g in positions:
        pairs += [(("O1", g), ("O0", g)), (("O2", g), ("O0", g)), (("O2", g), ("O1", g)), (("R", g), ("O0", g))]
    for o in ("O0", "O1", "O2"):
        pairs += [((o, a), (o, b)) for a, b in position_pairs]
    return pairs


def filter_pairs(df: pd.DataFrame, pairs, eval_split: str = "eval"):
    have = set(map(tuple, df[df["split"] == eval_split].fillna({"gold_index": -1})[["condition", "gold_index"]]
                   .astype({"gold_index": int}).drop_duplicates().itertuples(index=False, name=None)))
    return [p for p in pairs if p[0] in have and p[1] in have]


def make_build_prompt(by_position: Dict[int, List[QAExample]], qa_fn, closedbook_fn, doc_cls):
    """Return build(job) -> prompt string, using the given prompt functions (repository or local copy)."""
    maps = {g: {e.qid: e for e in exs} for g, exs in by_position.items()}
    first = sorted(by_position)[0]

    def build(job: Job) -> str:
        ex = maps[job.gold_index if job.gold_index is not None else first][job.qid]
        if job.condition == "C1":
            return closedbook_fn(ex.question)
        docs = docs_for(ex, job.condition, job.gold_index)
        return qa_fn(ex.question, [doc_cls.from_dict(d) for d in docs],
                     mention_random_ordering=False, query_aware_contextualization=False)
    return build
