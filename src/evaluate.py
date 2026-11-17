"""Evaluation: audit first, then metrics (cycle 5).

Input is a long-format predictions table, one row per (question, condition, gold position, run).
Required columns (see REQUIRED_COLUMNS). `correct` must come from the frozen scorer; this module
does not score text. Nothing is interpreted here: it audits, computes, and exports.

Metric directions (REGISTRY): accuracy higher is better; flip_rate lower means more stable.
Uncertainty: percentile bootstrap over questions (pairs kept together). Paired comparisons also
get an exact McNemar test. p-values are reported unadjusted and Holm-adjusted; no result is
labelled "significant" by this code, and the paired tests assume questions are independent.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import binomtest

REQUIRED_COLUMNS = [
    "qid", "split", "condition", "gold_index", "run_id", "correct",
    "model_id", "template_id", "scorer_version", "decoding", "max_new_tokens",
    "ctx_size", "n_prompt_tokens", "truncated",
]
# Settings that must be identical in every row of a primary comparison.
COMPARATOR_COLUMNS = ["model_id", "template_id", "scorer_version", "decoding",
                      "max_new_tokens", "ctx_size"]
REGISTRY = {"accuracy": "higher", "flip_rate": "lower"}
CONTROLS = ("C1", "C2")  # closed-book, oracle: no gold_index; may use their own template_id
SUBSET_CONDITIONS = ("R",)  # rerun: may cover only a subset of the evaluation questions


@dataclass
class Finding:
    level: str   # "ERROR" blocks metrics; "WARN" is reported
    code: str
    message: str


@dataclass
class AuditReport:
    findings: List[Finding] = field(default_factory=list)

    def add(self, level, code, message):
        self.findings.append(Finding(level, code, message))

    @property
    def ok(self) -> bool:
        return not any(f.level == "ERROR" for f in self.findings)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(df: pd.DataFrame, positions=(0, 4, 9, 14, 19), eval_split="eval",
          primary_conditions=None) -> AuditReport:
    """Run every check before any metric. Returns findings; ERROR means stop."""
    rep = AuditReport()
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        rep.add("ERROR", "columns", f"missing columns: {missing_cols}")
        return rep
    # 1. missing values (gold_index may be empty only for controls)
    for c in REQUIRED_COLUMNS:
        if c == "gold_index":
            bad = df[df[c].isna() & ~df["condition"].isin(CONTROLS)]
        else:
            bad = df[df[c].isna()]
        if len(bad):
            rep.add("ERROR", "missing_values", f"{len(bad)} rows with missing '{c}'")
    # 2. label domain: correct is 0/1, truncated is boolean-like
    if not set(df["correct"].dropna().unique()) <= {0, 1}:
        rep.add("ERROR", "label_domain", "'correct' has values other than 0/1")
    if not set(df["truncated"].dropna().astype(int).unique()) <= {0, 1}:
        rep.add("ERROR", "label_domain", "'truncated' is not 0/1")
    elif int(df["truncated"].astype(int).sum()) > 0:
        rep.add("ERROR", "truncation", f"{int(df['truncated'].astype(int).sum())} rows are truncated prompts")
    if rep.findings and not rep.ok:
        return rep  # later checks assume clean basics
    # 3. partitions and leakage
    splits = set(df["split"].unique())
    if not splits <= {"dev", "eval", "replication"}:
        rep.add("ERROR", "split_values", f"unknown split labels: {sorted(splits - {'dev','eval','replication'})}")
    per_q = df.groupby("qid")["split"].nunique()
    leaked = per_q[per_q > 1]
    if len(leaked):
        rep.add("ERROR", "leakage", f"{len(leaked)} question ids appear in more than one split, e.g. {list(leaked.index[:3])}")
    # 4. duplicates
    key = ["qid", "condition", "gold_index", "run_id"]
    dups = df.fillna({"gold_index": -1}).duplicated(key, keep=False)
    if dups.any():
        rep.add("ERROR", "duplicates", f"{int(dups.sum())} rows share (qid, condition, gold_index, run_id)")
    # 5. gold index domain
    non_ctrl = df[~df["condition"].isin(CONTROLS)]
    badpos = non_ctrl[~non_ctrl["gold_index"].isin(positions)]
    if len(badpos):
        rep.add("ERROR", "gold_index", f"{len(badpos)} rows with gold_index outside {list(positions)}")
    if rep.ok is False:
        return rep
    ev = df[df["split"] == eval_split]
    if ev.empty:
        rep.add("ERROR", "no_eval_rows", f"no rows with split == '{eval_split}'")
        return rep
    # 6. completeness: every eval question has every cell of every non-control condition
    cells = ev.fillna({"gold_index": -1}).groupby(["condition", "gold_index", "run_id"])["qid"].apply(set)
    ref_q = set(ev["qid"])
    for cell, qs in cells.items():
        if cell[0] in SUBSET_CONDITIONS:
            if not qs <= ref_q:
                rep.add("ERROR", "incomplete_cell", f"cell {cell}: {len(qs - ref_q)} questions outside the evaluation set")
            continue
        if qs != ref_q:
            rep.add("ERROR", "incomplete_cell",
                    f"cell {cell}: {len(ref_q - qs)} eval questions missing, {len(qs - ref_q)} extra")
    # 7. incompatible comparator settings
    primary = ev[~ev["condition"].isin(CONTROLS)]
    if primary_conditions is not None:
        primary = primary[primary["condition"].isin(primary_conditions)]
    for c in COMPARATOR_COLUMNS:
        vals = primary[c].astype(str).unique()
        if len(vals) > 1:
            rep.add("ERROR", "comparator_mismatch",
                    f"'{c}' differs across primary conditions: {sorted(vals)}")
    for c in ("model_id", "scorer_version", "decoding", "max_new_tokens", "ctx_size"):
        cv = ev[ev["condition"].isin(CONTROLS)][c].astype(str).unique()
        pv = primary[c].astype(str).unique()
        if len(cv) and len(pv) and set(cv) != set(pv):
            rep.add("WARN", "control_setting", f"controls use different '{c}' ({sorted(cv)}) than primary ({sorted(pv)})")
    return rep


def _boot_idx(n: int, n_boot: int, seed: int) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.integers(0, n, size=(n_boot, n))


def cell_vectors(ev: pd.DataFrame, run_id=0) -> Dict[tuple, pd.Series]:
    """(condition, gold_index) -> correct vector indexed by qid, qids sorted."""
    ev = ev[ev["run_id"] == run_id].fillna({"gold_index": -1})
    out = {}
    for (cond, g), sub in ev.groupby(["condition", "gold_index"]):
        out[(cond, int(g))] = sub.set_index("qid")["correct"].astype(int).sort_index()
    return out


def accuracy_ci(x: np.ndarray, n_boot=10000, seed=777, alpha=0.05):
    idx = _boot_idx(len(x), n_boot, seed)
    means = x[idx].mean(axis=1)
    return x.mean(), *np.quantile(means, [alpha / 2, 1 - alpha / 2])


def paired_compare(a: np.ndarray, b: np.ndarray, n_boot=10000, seed=777, alpha=0.05) -> dict:
    """a, b: 0/1 vectors on the SAME questions in the SAME order. Reports a - b."""
    if a.shape != b.shape:
        raise ValueError("paired vectors must have equal length (same questions)")
    diff = a - b
    idx = _boot_idx(len(a), n_boot, seed)
    boots = diff[idx].mean(axis=1)
    n01 = int(((a == 0) & (b == 1)).sum())   # a wrong, b right
    n10 = int(((a == 1) & (b == 0)).sum())   # a right, b wrong
    p = 1.0 if n01 + n10 == 0 else binomtest(n10, n10 + n01, 0.5).pvalue
    return {"diff": float(diff.mean()), "ci_low": float(np.quantile(boots, alpha / 2)),
            "ci_high": float(np.quantile(boots, 1 - alpha / 2)),
            "a_right_b_wrong": n10, "a_wrong_b_right": n01, "p_exact_mcnemar": float(p),
            "flip_rate": (n01 + n10) / len(a)}


def holm(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def compute_results(df: pd.DataFrame, eval_split="eval", n_boot=10000, seed=777,
                    input_sha256="", pairs=None) -> pd.DataFrame:
    """Build the long results table. `pairs` = list of ((condA,gA),(condB,gB)) to compare."""
    ev = df[df["split"] == eval_split]
    vec = cell_vectors(ev)
    rows = []
    base = {"split": eval_split, "bootstrap_seed": seed, "n_boot": n_boot, "input_sha256": input_sha256}
    for (cond, g), s in sorted(vec.items()):
        est, lo, hi = accuracy_ci(s.to_numpy(), n_boot, seed)
        rows.append({**base, "table": "accuracy", "metric": "accuracy", "direction": REGISTRY["accuracy"],
                     "condition": cond, "gold_index": None if g == -1 else g, "comparator": "",
                     "n": len(s), "estimate": est, "ci_low": lo, "ci_high": hi})
    pair_rows = []
    for (ka, kb) in (pairs or []):
        sa, sb = vec[ka], vec[kb]
        if ka[0] in SUBSET_CONDITIONS or kb[0] in SUBSET_CONDITIONS:
            common = sa.index.intersection(sb.index)      # rerun covers a subset: compare on shared questions
            if len(common) == 0:
                raise ValueError(f"no shared questions between {ka} and {kb}")
            sa, sb = sa.loc[common], sb.loc[common]
        elif not sa.index.equals(sb.index):
            raise ValueError(f"question ids differ between {ka} and {kb}")
        r = paired_compare(sa.to_numpy(), sb.to_numpy(), n_boot, seed)
        pair_rows.append((ka, kb, r, len(sa)))
    adj = holm([r["p_exact_mcnemar"] for _, _, r, _ in pair_rows]) if pair_rows else []
    for (ka, kb, r, n), pa in zip(pair_rows, adj):
        rows.append({**base, "table": "paired", "metric": "accuracy_difference", "direction": REGISTRY["accuracy"],
                     "condition": ka[0], "gold_index": None if ka[1] == -1 else ka[1],
                     "comparator": f"{kb[0]}@{None if kb[1] == -1 else kb[1]}", "n": n,
                     "estimate": r["diff"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                     "a_right_b_wrong": r["a_right_b_wrong"], "a_wrong_b_right": r["a_wrong_b_right"],
                     "p_unadjusted": r["p_exact_mcnemar"], "p_holm": pa, "test": "exact McNemar",
                     "flip_rate": r["flip_rate"]})
    return pd.DataFrame(rows)


def plot_accuracy(results: pd.DataFrame, out_stem: Path, title="Accuracy by gold position", conditions=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    acc = results[(results["table"] == "accuracy") & results["gold_index"].notna()]
    acc = acc[acc["condition"].isin(conditions)] if conditions else acc[~acc["condition"].isin(SUBSET_CONDITIONS)]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    markers = ["o", "s", "^", "D", "v"]
    groups = list(acc.groupby("condition"))
    for i, (cond, sub) in enumerate(groups):
        sub = sub.sort_values("gold_index")
        x = sub["gold_index"].to_numpy() + (i - (len(groups) - 1) / 2) * 0.35  # dodge to avoid overlap
        ax.errorbar(x, sub["estimate"], yerr=[sub["estimate"] - sub["ci_low"], sub["ci_high"] - sub["estimate"]],
                    marker=markers[i % 5], capsize=3, linewidth=1.2, label=cond)
    ctrl = results[(results["table"] == "accuracy") & results["gold_index"].isna()]
    for _, r in ctrl.iterrows():
        ax.axhline(r["estimate"], linestyle="--", linewidth=0.9, color="gray")
        ax.text(0.99, r["estimate"], r["condition"],
                transform=ax.get_yaxis_transform(), ha="right", va="bottom", fontsize=8, color="gray")
    ax.set_xticks(sorted(acc["gold_index"].unique()))
    ax.set_xlabel("Gold passage index (0 = first)")
    ax.set_ylabel("Accuracy (higher is better)")
    ax.set_title(title, fontsize=10)
    ax.legend(title="Ordering", fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=len(groups))
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_stem.with_suffix(".png"), dpi=300)
    fig.savefig(out_stem.with_suffix(".pdf"))
    plt.close(fig)


def plot_flips(results: pd.DataFrame, out_stem: Path):
    """Descriptive flip rates (share of questions whose correctness changes; lower = more stable).
    No intervals are drawn; the paired tests are in results.csv."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pr = results[results["table"] == "paired"]
    series = [("O1", "O0", "O1 vs O0 (distractor order)"), ("O2", "O0", "O2 vs O0 (distractor order)"),
              ("R", "O0", "rerun vs O0 (noise floor)")]
    positions = sorted(pr["gold_index"].dropna().astype(int).unique())
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    w = 0.26
    for k, (cond, comp, label) in enumerate(series):
        sub = pr[(pr["condition"] == cond) & pr["comparator"].str.startswith(comp + "@")]
        sub = sub[sub["comparator"] == sub["gold_index"].apply(lambda g: f"{comp}@{int(g)}")].sort_values("gold_index")
        if sub.empty:
            continue
        x = [positions.index(int(g)) + (k - 1) * w for g in sub["gold_index"]]
        ax.bar(x, sub["flip_rate"], width=w, label=label)
    ax.set_xticks(range(len(positions)))
    ax.set_xticklabels(positions)
    ax.set_xlabel("Gold passage index (0 = first)")
    ax.set_ylabel("Flip rate (lower is more stable)")
    ax.set_title("Share of questions whose correctness changes", fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_stem.with_suffix(".png"), dpi=300)
    fig.savefig(out_stem.with_suffix(".pdf"))
    plt.close(fig)
