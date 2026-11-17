"""Scorer that mirrors the original repository's metric (cycle 6).

Source of the logic: `scripts/evaluate_qa_responses.py` and `lost_in_the_middle/metrics.py` of
the Lost-in-the-Middle repository (MIT licence), pasted by the project author. This file is a
re-implementation for offline testing. On Colab the repository function is called as well and
the two must agree on every output (see cross_check). The original is the reference.

Rules (VERIFIED from the pasted code):
  1. Only the text before the first newline of the reply is scored, after strip().
  2. Normalisation (SQuAD): lowercase, remove ASCII punctuation, remove the words a/an/the, fix spaces.
  3. Correct (1.0) if ANY normalised accepted answer is a SUBSTRING of the normalised reply, else 0.0.
Known properties of rule 3 (reported, not changed): matching is by character substring, not by word,
so a short answer such as "art" matches inside "start"; an accepted answer that normalises to the
empty string matches every reply.
"""
from __future__ import annotations

import re
import string
from typing import Iterable, List

_PUNC = set(string.punctuation)


def normalize_answer(s: str) -> str:
    s = s.lower()
    s = "".join(ch for ch in s if ch not in _PUNC)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def first_line(model_answer: str) -> str:
    return model_answer.split("\n")[0].strip()


def best_subspan_em(prediction: str, ground_truths: List[str]) -> float:
    p = normalize_answer(prediction)
    for g in ground_truths:
        if normalize_answer(g).lower() in p.lower():
            return 1.0
    return 0.0


def score_reply(model_answer: str, answers: List[str]) -> int:
    """The 0/1 value written to the `correct` column."""
    return int(best_subspan_em(first_line(model_answer), answers))


def risky_answers(answers: Iterable[str], min_len: int = 4) -> List[str]:
    """Accepted answers that are empty or very short after normalisation (substring-leniency risk)."""
    return [a for a in answers if len(normalize_answer(a)) < min_len]


def cross_check(rows, reference_fn) -> List[int]:
    """rows: iterable of (model_answer, answers). reference_fn: the repository's best_subspan_em.
    Returns indices where this scorer and the original disagree (must be empty)."""
    bad = []
    for i, (reply, answers) in enumerate(rows):
        mine = score_reply(reply, answers)
        ref = int(reference_fn(prediction=first_line(reply), ground_truths=answers))
        if mine != ref:
            bad.append(i)
    return bad
