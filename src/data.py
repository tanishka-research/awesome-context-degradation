"""Data loading and validation (cycle 1).

Reads the multi-document QA files of the original Lost-in-the-Middle protocol
(one gzipped JSON-lines file per gold position) and checks them against the
protocol's assumptions. It excludes nothing: it only reports.

File format (from the original repository's README, as read in an earlier stage):
    one JSON object per line with keys
        question (str), answers (list[str]), ctxs (list of passages),
        nq_annotated_gold (dict, not used here)
    each passage: id, title, text, score, hasanswer, original_retrieval_index, isgold

Shapes
------
    load_qa_file(path)         -> list[QAExample]          length N (questions in file)
    QAExample.passages         -> list[Passage]             length 20 in the main design
    validate_file(...)         -> dict (JSON-serialisable)
    check_across_positions(..) -> dict (JSON-serialisable)

This module uses only the standard library.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

PROBLEM_CODES = (
    "bad_question",
    "no_answers",
    "ctx_count",
    "gold_count",
    "gold_index_mismatch",
    "distractor_has_answer",
    "empty_text",
    "duplicate_text",
)


class DataFormatError(ValueError):
    """The file is not in the expected structure (cannot be analysed)."""


@dataclass(frozen=True)
class Passage:
    title: str
    text: str
    isgold: bool
    hasanswer: bool
    original_retrieval_index: Optional[int] = None
    score: Optional[float] = None
    id: Optional[str] = None


@dataclass(frozen=True)
class QAExample:
    question: str
    answers: List[str]
    passages: List[Passage]

    @property
    def qid(self) -> str:
        return question_id(self.question)

    def gold_positions(self) -> List[int]:
        return [i for i, p in enumerate(self.passages) if p.isgold]


# --------------------------------------------------------------------------- ids


def normalize_question(question: str) -> str:
    """Lowercase, Unicode-normalise, drop punctuation, collapse whitespace."""
    q = unicodedata.normalize("NFKC", question).lower()
    q = re.sub(r"[^\w\s]", "", q)
    return re.sub(r"\s+", " ", q).strip()


def question_id(question: str) -> str:
    """Stable 16-hex-character id from the normalised question text.

    The data files carry no question id, so this one is derived. It is used for
    splits and for per-question seeds, and it does not depend on file order.
    """
    return hashlib.sha256(normalize_question(question).encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------------- loading


def _open_text(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def _parse_example(raw: dict, where: str) -> QAExample:
    for key in ("question", "answers", "ctxs"):
        if key not in raw:
            raise DataFormatError(f"{where}: missing key '{key}'")
    if not isinstance(raw["ctxs"], list):
        raise DataFormatError(f"{where}: 'ctxs' is not a list")
    passages: List[Passage] = []
    for j, c in enumerate(raw["ctxs"]):
        for key in ("text", "isgold", "hasanswer"):
            if key not in c:
                raise DataFormatError(f"{where}: passage {j} missing key '{key}'")
        for key in ("isgold", "hasanswer"):
            if not isinstance(c[key], bool):
                raise DataFormatError(
                    f"{where}: passage {j} field '{key}' is {type(c[key]).__name__} "
                    f"({c[key]!r}), expected a JSON boolean"
                )
        passages.append(
            Passage(
                title=str(c.get("title", "")),
                text=str(c["text"]),
                isgold=c["isgold"],
                hasanswer=c["hasanswer"],
                original_retrieval_index=c.get("original_retrieval_index"),
                score=c.get("score"),
                id=None if c.get("id") is None else str(c["id"]),
            )
        )
    return QAExample(
        question=str(raw["question"]),
        answers=[str(a) for a in raw["answers"]],
        passages=passages,
    )


def load_qa_file(path: Path | str, limit: Optional[int] = None) -> List[QAExample]:
    """Read one file. Raises DataFormatError on structural problems."""
    path = Path(path)
    out: List[QAExample] = []
    with _open_text(path) as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            where = f"{path.name} line {line_no}"
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DataFormatError(f"{where}: invalid JSON ({exc.msg})") from exc
            out.append(_parse_example(raw, where))
            if limit is not None and len(out) >= limit:
                break
    return out


# -------------------------------------------------------------------- validation


def validate_example(
    ex: QAExample, total_documents: int = 20, expected_gold_index: Optional[int] = None
) -> List[str]:
    """Return the list of problem codes found in one example (empty list = clean)."""
    problems: List[str] = []
    if not normalize_question(ex.question):
        problems.append("bad_question")
    if not [a for a in ex.answers if a.strip()]:
        problems.append("no_answers")
    if len(ex.passages) != total_documents:
        problems.append("ctx_count")
    golds = ex.gold_positions()
    if len(golds) != 1:
        problems.append("gold_count")
    elif expected_gold_index is not None and golds[0] != expected_gold_index:
        problems.append("gold_index_mismatch")
    if any(p.hasanswer for p in ex.passages if not p.isgold):
        problems.append("distractor_has_answer")
    if any(not p.text.strip() for p in ex.passages):
        problems.append("empty_text")
    texts = [p.text.strip() for p in ex.passages]
    if len(set(texts)) != len(texts):
        problems.append("duplicate_text")
    return problems


def validate_file(
    path: Path | str,
    total_documents: int = 20,
    expected_gold_index: Optional[int] = None,
    examples: Optional[List[QAExample]] = None,
) -> dict:
    """Validate every example in a file. Nothing is excluded or modified.

    Pass `examples` (already loaded from `path`) to avoid reading the file twice.
    """
    if examples is None:
        examples = load_qa_file(path)
    counts = {code: 0 for code in PROBLEM_CODES}
    sample_ids: Dict[str, List[str]] = {code: [] for code in PROBLEM_CODES}
    clean = 0
    for ex in examples:
        found = validate_example(ex, total_documents, expected_gold_index)
        if not found:
            clean += 1
        for code in found:
            counts[code] += 1
            if len(sample_ids[code]) < 5:
                sample_ids[code].append(ex.qid)
    qids = [ex.qid for ex in examples]
    return {
        "file": str(path),
        "expected_gold_index": expected_gold_index,
        "n_examples": len(examples),
        "n_unique_questions": len(set(qids)),
        "n_duplicate_question_rows": len(qids) - len(set(qids)),
        "n_clean": clean,
        "problem_counts": counts,
        "problem_example_ids": sample_ids,
    }


def check_across_positions(by_position: Dict[int, List[QAExample]]) -> dict:
    """Check that files for different gold positions describe the same items.

    The protocol assumes that, for a given question, the 19 distractors and the
    gold passage are the same in every file and only the gold index moves. This
    function tests that assumption; it does not assume it.
    """
    positions = sorted(by_position)
    maps: Dict[int, Dict[str, QAExample]] = {
        p: {ex.qid: ex for ex in by_position[p]} for p in positions
    }
    all_ids = set().union(*[set(m) for m in maps.values()]) if maps else set()
    in_all = set.intersection(*[set(m) for m in maps.values()]) if maps else set()

    gold_differs: List[str] = []
    set_differs: List[str] = []
    seq_differs: List[str] = []
    for qid in sorted(in_all):
        exs = [maps[p][qid] for p in positions]
        gold_texts = {
            tuple(q.text.strip() for q in ex.passages if q.isgold) for ex in exs
        }
        dist_seqs = [
            tuple(q.text.strip() for q in ex.passages if not q.isgold) for ex in exs
        ]
        if len(gold_texts) != 1:
            gold_differs.append(qid)
        if len({frozenset(s) for s in dist_seqs}) != 1:
            set_differs.append(qid)
        if len(set(dist_seqs)) != 1:
            seq_differs.append(qid)
    return {
        "positions": positions,
        "n_questions_union": len(all_ids),
        "n_questions_in_all_files": len(in_all),
        "n_questions_missing_from_some_file": len(all_ids) - len(in_all),
        "n_gold_text_differs": len(gold_differs),
        "n_distractor_set_differs": len(set_differs),
        "n_distractor_sequence_differs": len(seq_differs),
        "example_ids_gold_differs": gold_differs[:5],
        "example_ids_distractor_set_differs": set_differs[:5],
        "example_ids_distractor_sequence_differs": seq_differs[:5],
    }
