"""Tests for positionorder.data using SYNTHETIC files built on the fly.

The synthetic files imitate the documented format only. Passing these tests shows
that the loader and validator behave as specified; it says nothing about the real
data. The real data must be validated with scripts/01_validate_data.py.
"""

import gzip
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from positionorder.data import (  # noqa: E402
    DataFormatError,
    check_across_positions,
    load_qa_file,
    normalize_question,
    question_id,
    validate_example,
    validate_file,
)


def make_example(i, gold_index, n_docs=20, break_gold_count=False, bad_distractor=False,
                 shuffle_distractors=False):
    distractors = [
        {"id": f"d{i}-{j}", "title": f"T{j}", "text": f"distractor {i} number {j}",
         "score": 1.0 / (j + 1), "hasanswer": False, "original_retrieval_index": j, "isgold": False}
        for j in range(n_docs - 1)
    ]
    if shuffle_distractors:
        distractors = distractors[::-1]
    if bad_distractor:
        distractors[3]["hasanswer"] = True
    gold = {"id": f"g{i}", "title": "G", "text": f"gold passage {i}", "score": 0.5,
            "hasanswer": True, "original_retrieval_index": 99, "isgold": True}
    ctxs = distractors[:gold_index] + [gold] + distractors[gold_index:]
    if break_gold_count:
        ctxs[0]["isgold"] = True
    return {"question": f"Question number {i}?", "answers": [f"answer {i}"], "ctxs": ctxs,
            "nq_annotated_gold": {"title": "G", "long_answer": "x", "chunked_long_answer": "x",
                                  "short_answers": [f"answer {i}"]}}


def write_file(directory, gold_index, examples):
    path = Path(directory) / f"nq-open-20_total_documents_gold_at_{gold_index}.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for ex in examples:
            fh.write(json.dumps(ex) + "\n")
    return path


def test_loader_shapes_and_ids():
    with tempfile.TemporaryDirectory() as d:
        path = write_file(d, 9, [make_example(i, 9) for i in range(3)])
        exs = load_qa_file(path)
        assert len(exs) == 3
        assert all(len(e.passages) == 20 for e in exs)
        assert all(e.gold_positions() == [9] for e in exs)
        assert len({e.qid for e in exs}) == 3


def test_question_id_is_stable_and_normalised():
    assert question_id("Who  is X?") == question_id("who is x")
    assert normalize_question("  A,B  c. ") == "ab c"
    assert len(question_id("anything")) == 16


def test_clean_file_has_no_problems():
    with tempfile.TemporaryDirectory() as d:
        path = write_file(d, 4, [make_example(i, 4) for i in range(5)])
        rep = validate_file(path, 20, expected_gold_index=4)
        assert rep["n_examples"] == 5 and rep["n_clean"] == 5
        assert all(v == 0 for v in rep["problem_counts"].values())


def test_detects_gold_count_distractor_answer_and_ctx_count():
    with tempfile.TemporaryDirectory() as d:
        exs = [make_example(0, 4), make_example(1, 4, break_gold_count=True),
               make_example(2, 4, bad_distractor=True), make_example(3, 4, n_docs=10)]
        path = write_file(d, 4, exs)
        rep = validate_file(path, 20, expected_gold_index=4)
        assert rep["n_examples"] == 4
        assert rep["problem_counts"]["gold_count"] == 1
        assert rep["problem_counts"]["distractor_has_answer"] == 1
        assert rep["problem_counts"]["ctx_count"] == 1
        assert rep["n_clean"] == 1


def test_detects_gold_index_mismatch():
    with tempfile.TemporaryDirectory() as d:
        path = write_file(d, 9, [make_example(0, 9)])
        ex = load_qa_file(path)[0]
        assert validate_example(ex, 20, expected_gold_index=9) == []
        assert validate_example(ex, 20, expected_gold_index=4) == ["gold_index_mismatch"]


def test_structural_errors_raise():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "bad.jsonl"
        bad.write_text('{"question": "q", "answers": ["a"]}\n', encoding="utf-8")
        try:
            load_qa_file(bad)
        except DataFormatError as exc:
            assert "ctxs" in str(exc)
        else:
            raise AssertionError("expected DataFormatError")


def test_cross_position_consistent_and_inconsistent():
    with tempfile.TemporaryDirectory() as d:
        by_pos = {}
        for g in (0, 9, 19):
            by_pos[g] = load_qa_file(write_file(d, g, [make_example(i, g) for i in range(4)]))
        rep = check_across_positions(by_pos)
        assert rep["n_questions_in_all_files"] == 4
        assert rep["n_gold_text_differs"] == 0
        assert rep["n_distractor_set_differs"] == 0
        assert rep["n_distractor_sequence_differs"] == 0
        # Now change the distractor ORDER for one question in one file only.
        exs = [make_example(i, 9) for i in range(4)]
        exs[2] = make_example(2, 9, shuffle_distractors=True)
        by_pos[9] = load_qa_file(write_file(d, 9, exs))
        rep2 = check_across_positions(by_pos)
        assert rep2["n_distractor_sequence_differs"] == 1
        assert rep2["n_distractor_set_differs"] == 0


def test_non_boolean_flags_are_rejected():
    """A string such as "false" must not be silently read as True."""
    with tempfile.TemporaryDirectory() as d:
        ex = make_example(0, 4)
        ex["ctxs"][0]["hasanswer"] = "false"
        path = write_file(d, 4, [ex])
        try:
            load_qa_file(path)
        except DataFormatError as exc:
            assert "hasanswer" in str(exc) and "boolean" in str(exc)
        else:
            raise AssertionError("expected DataFormatError for a string flag")


def test_derive_position_file_moves_only_the_gold_passage():
    from positionorder.derive import DeriveError, derive_position_file
    with tempfile.TemporaryDirectory() as d:
        src = write_file(d, 0, [make_example(i, 0) for i in range(5)])
        for g in (0, 4, 19):
            out = Path(d) / f"derived_{g}.jsonl.gz"
            assert derive_position_file(src, g, out, 20) == 5
            derived = load_qa_file(out)
            direct = load_qa_file(write_file(d, g, [make_example(i, g) for i in range(5)]))
            assert [e.passages for e in derived] == [e.passages for e in direct]
            assert validate_file(out, 20, expected_gold_index=g)["n_clean"] == 5
        bad = write_file(d, 4, [make_example(0, 4)])        # gold not at index 0 -> must refuse
        try:
            derive_position_file(bad, 9, Path(d) / "x.jsonl.gz", 20)
        except DeriveError:
            pass
        else:
            raise AssertionError("expected DeriveError")
