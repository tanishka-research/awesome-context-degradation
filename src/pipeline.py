"""One full pass: development gate, evaluation runs, audit, results, figures (cycle 6).

The caller supplies a prompt builder and a generator, so this module is testable with a dummy generator.
It writes: raw_outputs.jsonl (resumable), predictions.csv, audit.json, results.csv,
fig_accuracy_by_position.png/.pdf, failure_counts.csv, pipeline_summary.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from . import evaluate as ev
from . import runner as rn
from .scoring import score_reply


def _acc(rows, answers, split, cond, gold=None):
    sel = [r for r in rows if r["split"] == split and r["condition"] == cond and r["gold_index"] == gold]
    if not sel:
        return None, 0
    return sum(score_reply(r["model_answer"], answers[r["qid"]]) for r in sel) / len(sel), len(sel)


def run_pipeline(tag: str, out_dir, by_position, split: Dict[str, List[str]], n_dev: int, n_eval: int,
                 positions, build_prompt, generate_fn, settings: dict, repo_scorer=None, gate: bool = True,
                 n_rerun: int = 100, n_boot: int = 10000, boot_seed: int = 777, log=print,
                 orderings=("O1", "O2")) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "raw_outputs.jsonl"
    first = sorted(by_position)[0]
    answers = {e.qid: e.answers for e in by_position[first]}
    dev, evl = split["dev"][:n_dev], split["eval"][:n_eval]
    positions = list(positions)
    if not {0, 9} <= set(positions):
        raise ValueError("positions must include 0 and 9 (used by the development gate)")
    summary: Dict[str, object] = {"tag": tag, "n_dev": len(dev), "n_eval": len(evl), "positions": positions,
                                  "orderings": list(orderings)}

    # ---- stage 1: development questions (debugging only; never pooled with evaluation)
    dev_jobs = rn.make_jobs("dev", dev, [("C1", None), ("C2", None), ("O0", [0, 9]), ("R", [0])])
    rn.run_jobs(dev_jobs, build_prompt, generate_fn, raw, log=log)
    rows = rn.load_rows(raw)
    c1, n1 = _acc(rows, answers, "dev", "C1")
    c2, n2 = _acc(rows, answers, "dev", "C2")
    o0a, _ = _acc(rows, answers, "dev", "O0", 0)
    o0b, _ = _acc(rows, answers, "dev", "O0", 9)
    dev_o0 = {r["qid"]: score_reply(r["model_answer"], answers[r["qid"]]) for r in rows
              if r["split"] == "dev" and r["condition"] == "O0" and r["gold_index"] == 0}
    dev_r = {r["qid"]: score_reply(r["model_answer"], answers[r["qid"]]) for r in rows
             if r["split"] == "dev" and r["condition"] == "R"}
    common = set(dev_o0) & set(dev_r)
    rerun_flips = sum(dev_o0[q] != dev_r[q] for q in common)
    same_text = sum(1 for a in rows if a["split"] == "dev" and a["condition"] == "R" for b in rows
                    if b["split"] == "dev" and b["condition"] == "O0" and b["gold_index"] == 0
                    and b["qid"] == a["qid"] and b["model_answer"] == a["model_answer"])
    summary["dev"] = {"closed_book_acc": c1, "oracle_acc": c2, "o0_pos0_acc": o0a, "o0_pos9_acc": o0b,
                      "rerun_pairs": len(common), "rerun_correctness_flips": rerun_flips,
                      "rerun_identical_outputs": same_text,
                      "mean_seconds_per_prompt": (sum(r["seconds"] for r in rows) / len(rows)) if rows else None,
                      "truncated_prompts": sum(r["truncated"] for r in rows)}
    log("DEV:", json.dumps(summary["dev"]))
    if gate:
        if c1 is None or c2 is None or not c2 > c1:
            raise RuntimeError(f"GATE FAILED: oracle accuracy ({c2}) is not above closed-book accuracy ({c1}) "
                               "on the development set. Stop and diagnose prompt, scorer or model before continuing.")
        if summary["dev"]["truncated_prompts"]:
            raise RuntimeError("GATE FAILED: truncated prompts on the development set.")

    # ---- stage 2: evaluation questions (controls, then O0, rerun, O1, O2)
    plan = [("C1", None), ("C2", None), ("O0", positions)]
    jobs = rn.make_jobs("eval", evl, plan)
    jobs += rn.make_jobs("eval", evl[:min(n_rerun, len(evl))], [("R", positions)])
    jobs += rn.make_jobs("eval", evl, [(o, positions) for o in orderings])
    rn.run_jobs(jobs, build_prompt, generate_fn, raw, log=log)

    # ---- stage 3: predictions, audit, results
    rows = rn.load_rows(raw)
    df = rn.to_predictions(rows, answers, settings, repo_scorer=repo_scorer)
    df.to_csv(out / "predictions.csv", index=False)
    rep = ev.audit(df, positions=tuple(positions), eval_split="eval")
    (out / "audit.json").write_text(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    for f in rep.findings:
        log(f"[{f.level}] {f.code}: {f.message}")
    if not rep.ok:
        raise RuntimeError("AUDIT FAILED: see audit.json. No metrics were computed.")
    pairs = rn.filter_pairs(df, rn.standard_pairs(positions))
    res = ev.compute_results(df, "eval", n_boot, boot_seed, input_sha256=ev.sha256_file(out / "predictions.csv"),
                             pairs=pairs)
    res.to_csv(out / "results.csv", index=False)
    ev.plot_accuracy(res, out / "fig_accuracy_by_position", conditions=["O0", "O1", "O2"])
    fail = (df[df["split"] == "eval"].fillna({"gold_index": -1})
            .groupby(["condition", "gold_index", "failure"]).size().unstack(fill_value=0).reset_index())
    fail.to_csv(out / "failure_counts.csv", index=False)
    summary.update({"n_prediction_rows": len(df), "n_pairs": len(pairs), "audit_ok": True,
                    "results_csv": str(out / "results.csv")})
    (out / "pipeline_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
