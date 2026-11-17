#!/usr/bin/env python3
"""Audit a predictions CSV, then compute metrics and export results.csv and figures.

    python scripts/05_evaluate.py --predictions results/predictions.csv --out results/eval

Stops with exit code 2 if the audit finds an ERROR. No interpretation is printed.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from positionorder import evaluate as ev  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", default=str(ROOT / "results" / "eval"))
    ap.add_argument("--split", default="eval")
    ap.add_argument("--baseline", default="O0", help="condition used as comparator in paired tests")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=777)
    a = ap.parse_args()

    df = pd.read_csv(a.predictions)
    rep = ev.audit(df, eval_split=a.split)
    for f in rep.findings:
        print(f"[{f.level}] {f.code}: {f.message}")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    if not rep.ok:
        print("AUDIT FAILED: no metrics computed."); return 2
    print("AUDIT PASSED (WARN items, if any, are listed above).")

    sub = df[df["split"] == a.split]
    conds = sorted(set(sub["condition"]) - set(ev.CONTROLS))
    positions = sorted(sub.loc[~sub["condition"].isin(ev.CONTROLS), "gold_index"].dropna().astype(int).unique())
    pairs = []
    if a.baseline in conds:
        for c in conds:
            if c != a.baseline:
                pairs += [((c, g), (a.baseline, g)) for g in positions]
    res = ev.compute_results(df, a.split, a.n_boot, a.seed, ev.sha256_file(a.predictions), pairs)
    res.to_csv(out / "results.csv", index=False)
    ev.plot_accuracy(res, out / "fig_accuracy_by_position")
    print(f"Wrote {out/'results.csv'} ({len(res)} rows) and figures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
