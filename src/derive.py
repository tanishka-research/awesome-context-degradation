"""Derive the position files from the single gold-at-0 file (cycle 6).

The original script (make_qa_data_from_retrieval_results.py, read in full) builds every position
file the same way: take the first N-1 retrieved passages that do not contain the answer, in
retrieval order, and insert the gold passage at the requested index. So the file with the gold
passage at index 0 already holds, in order, every distractor of every other position file, and a
position file for index g is that file with the gold passage moved from index 0 to index g.

Two checks on the real gold-at-0 file support this reading (see docs/deviation_log.md, DEV-010).
This function does not touch the gold passage or any distractor; it only moves the gold passage.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path


class DeriveError(ValueError):
    pass


def derive_position_file(src_path, gold_index: int, out_path, total_documents: int = 20) -> int:
    """Write a gzipped JSONL file with the gold passage at `gold_index`. Returns the number of examples."""
    src_path, out_path = Path(src_path), Path(out_path)
    if not 0 <= gold_index < total_documents:
        raise DeriveError(f"gold_index {gold_index} outside 0..{total_documents - 1}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if str(src_path).endswith(".gz") else open
    n = 0
    with opener(src_path, "rt", encoding="utf-8") as fin, gzip.open(out_path, "wt", encoding="utf-8") as fout:
        for line_no, line in enumerate(fin, start=1):
            if not line.strip():
                continue
            ex = json.loads(line)
            ctxs = ex["ctxs"]
            if len(ctxs) != total_documents:
                raise DeriveError(f"line {line_no}: {len(ctxs)} passages, expected {total_documents}")
            golds = [i for i, c in enumerate(ctxs) if c.get("isgold") is True]
            if golds != [0]:
                raise DeriveError(f"line {line_no}: source must have exactly one gold passage, at index 0 (found {golds})")
            gold, distractors = ctxs[0], ctxs[1:]
            ex["ctxs"] = distractors[:gold_index] + [gold] + distractors[gold_index:]
            fout.write(json.dumps(ex) + "\n")
            n += 1
    return n
