#!/usr/bin/env python3
"""Validate the 20-document QA files, one per gold position (cycle 1).

Run from the repository root, for example:
    python scripts/01_validate_data.py --qa-dir external/lost-in-the-middle/qa_data

Reads files only. Excludes nothing. Writes results/data/validation_report.json.

Exit codes: 0 = no problems found; 1 = a file is missing or structurally invalid;
2 = files readable but some examples have protocol problems (listed in the report).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from positionorder.data import (  # noqa: E402
    DataFormatError,
    PROBLEM_CODES,
    check_across_positions,
    load_qa_file,
    validate_file,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qa-dir", required=True, help="folder holding the per-position files")
    ap.add_argument("--pattern", default="nq-open-20_total_documents_gold_at_{gold}.jsonl.gz",
                    help="file name with {gold} placeholder")
    ap.add_argument("--positions", type=int, nargs="+", default=[0, 4, 9, 14, 19])
    ap.add_argument("--total-documents", type=int, default=20)
    ap.add_argument("--report", default=str(ROOT / "results" / "data" / "validation_report.json"))
    args = ap.parse_args()

    qa_dir = Path(args.qa_dir)
    exit_code = 0
    file_reports, by_position = [], {}

    for g in args.positions:
        path = qa_dir / args.pattern.format(gold=g)
        if not path.is_file():
            print(f"[MISSING] gold_at_{g}: {path}")
            exit_code = max(exit_code, 1)
            continue
        try:
            examples = load_qa_file(path)
            rep = validate_file(path, args.total_documents, expected_gold_index=g, examples=examples)
            by_position[g] = examples
        except DataFormatError as exc:
            print(f"[FORMAT ERROR] gold_at_{g}: {exc}")
            exit_code = max(exit_code, 1)
            continue
        file_reports.append(rep)
        n_prob = rep["n_examples"] - rep["n_clean"]
        tag = "OK" if n_prob == 0 and rep["n_duplicate_question_rows"] == 0 else "PROBLEM"
        print(f"[{tag}] gold_at_{g}: {rep['n_examples']} examples, "
              f"{rep['n_unique_questions']} unique questions, {rep['n_clean']} clean")
        for code in PROBLEM_CODES:
            n = rep["problem_counts"][code]
            if n:
                print(f"    {code}: {n} (example ids: {', '.join(rep['problem_example_ids'][code])})")
        if n_prob or rep["n_duplicate_question_rows"]:
            exit_code = max(exit_code, 2)

    cross = None
    if len(by_position) >= 2:
        cross = check_across_positions(by_position)
        print("Cross-position check:")
        for k in ("n_questions_union", "n_questions_in_all_files",
                  "n_questions_missing_from_some_file", "n_gold_text_differs",
                  "n_distractor_set_differs", "n_distractor_sequence_differs"):
            print(f"    {k}: {cross[k]}")
        if (cross["n_questions_missing_from_some_file"] or cross["n_gold_text_differs"]
                or cross["n_distractor_set_differs"] or cross["n_distractor_sequence_differs"]):
            exit_code = max(exit_code, 2)

    report = {"total_documents": args.total_documents, "positions": args.positions,
              "files": file_reports, "cross_position": cross, "exit_code": exit_code}
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"SUMMARY: exit code {exit_code} (0 clean, 1 missing/format error, 2 protocol problems)")
    print(f"Report written to {out}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
