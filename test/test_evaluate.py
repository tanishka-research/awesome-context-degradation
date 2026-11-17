"""Tests use SYNTHETIC tables built here to exercise the code. Values are arbitrary and mean nothing."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from positionorder import evaluate as ev  # noqa: E402

SET = dict(model_id="m", template_id="t", scorer_version="s1", decoding="greedy",
           max_new_tokens=64, ctx_size=4096, n_prompt_tokens=3000, truncated=0)


def make(n=40, conds=("O0", "O1"), positions=(0, 4, 9), split="eval", seed=0, pfx="q"):
    rng = np.random.default_rng(seed)
    rows = []
    for c in conds:
        for g in positions:
            for i in range(n):
                rows.append(dict(qid=f"{pfx}{i}", split=split, condition=c, gold_index=g, run_id=0,
                                 correct=int(rng.random() < 0.5), **SET))
    return pd.DataFrame(rows)


def codes(rep, level="ERROR"):
    return {f.code for f in rep.findings if f.level == level}


def test_clean_table_passes():
    assert ev.audit(make(), positions=(0, 4, 9)).ok


def test_missing_column_and_value():
    df = make().drop(columns=["scorer_version"])
    assert "columns" in codes(ev.audit(df))
    df = make(); df.loc[0, "correct"] = np.nan
    assert "missing_values" in codes(ev.audit(df, positions=(0, 4, 9)))


def test_bad_label_and_truncation():
    df = make(); df.loc[0, "correct"] = 2
    assert "label_domain" in codes(ev.audit(df, positions=(0, 4, 9)))
    df = make(); df.loc[0, "truncated"] = 1
    assert "truncation" in codes(ev.audit(df, positions=(0, 4, 9)))


def test_leakage_between_splits():
    df = pd.concat([make(), make(split="dev", seed=1)])  # same qids in dev and eval
    assert "leakage" in codes(ev.audit(df, positions=(0, 4, 9)))
    df = pd.concat([make(), make(split="dev", seed=1, pfx="d")])
    assert ev.audit(df, positions=(0, 4, 9)).ok


def test_duplicates_and_incomplete_cells():
    df = pd.concat([make(), make().iloc[:1]])
    assert "duplicates" in codes(ev.audit(df, positions=(0, 4, 9)))
    df = make().iloc[1:]
    assert "incomplete_cell" in codes(ev.audit(df, positions=(0, 4, 9)))


def test_comparator_mismatch():
    df = make(); df.loc[df["condition"] == "O1", "max_new_tokens"] = 128
    assert "comparator_mismatch" in codes(ev.audit(df, positions=(0, 4, 9)))


def test_bad_gold_index():
    df = make(); df.loc[0, "gold_index"] = 7
    assert "gold_index" in codes(ev.audit(df, positions=(0, 4, 9)))


def test_paired_compare_known_counts():
    a = np.array([1, 1, 1, 0, 0, 0, 1, 0]); b = np.array([1, 0, 0, 0, 1, 0, 1, 0])
    r = ev.paired_compare(a, b, n_boot=500, seed=1)
    assert r["a_right_b_wrong"] == 2 and r["a_wrong_b_right"] == 1
    assert abs(r["diff"] - 1 / 8) < 1e-12 and abs(r["flip_rate"] - 3 / 8) < 1e-12
    same = ev.paired_compare(a, a, n_boot=200, seed=1)
    assert same["diff"] == 0 and same["p_exact_mcnemar"] == 1.0


def test_holm_is_monotone_and_bounded():
    adj = ev.holm([0.01, 0.04, 0.03])
    assert all(0 <= p <= 1 for p in adj) and abs(adj[0] - 0.03) < 1e-12


def test_bootstrap_is_reproducible():
    x = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 1])
    assert ev.accuracy_ci(x, 500, 5) == ev.accuracy_ci(x, 500, 5)


def test_results_table_and_pair_alignment():
    df = make()
    res = ev.compute_results(df, n_boot=200, pairs=[(("O1", 0), ("O0", 0))])
    assert set(res["table"]) == {"accuracy", "paired"}
    assert (res.loc[res["table"] == "accuracy", "direction"] == "higher").all()
    bad = df.copy(); bad.loc[(bad.condition == "O1") & (bad.gold_index == 0) & (bad.qid == "q0"), "qid"] = "zz"
    try:
        ev.compute_results(bad, n_boot=50, pairs=[(("O1", 0), ("O0", 0))])
    except ValueError:
        pass
    else:
        raise AssertionError("misaligned qids must raise")
