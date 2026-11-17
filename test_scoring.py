"""Hand-checked cases for the re-implemented scorer. Expected values come from reading the
original rules, not from running the original code (not available offline)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from positionorder import scoring as sc  # noqa: E402


def test_normalisation_order_and_rules():
    assert sc.normalize_answer("The  Eiffel-Tower!") == "eiffeltower"   # punctuation removed, not spaced
    assert sc.normalize_answer("A man, an apple") == "man apple"
    assert sc.normalize_answer("  U.S.A. ") == "usa"


def test_only_first_line_is_scored():
    assert sc.score_reply("Paris\nThe capital of France is Paris", ["Paris"]) == 1
    assert sc.score_reply("\nParis", ["Paris"]) == 0            # blank first line scores 0
    assert sc.score_reply("The answer is unknown\nParis", ["Paris"]) == 0


def test_substring_and_any_answer():
    assert sc.score_reply("It was in 1990.", ["1990", "nineteen ninety"]) == 1
    assert sc.score_reply("It was nineteen ninety", ["1990", "nineteen ninety"]) == 1
    assert sc.score_reply("Barack Obama", ["Obama"]) == 1
    assert sc.score_reply("Paris", ["London"]) == 0


def test_known_leniency_properties():
    assert sc.score_reply("start", ["art"]) == 1                # character substring, not word match
    assert sc.score_reply("anything", ["the"]) == 1             # answer normalises to "" -> always matches
    assert sc.risky_answers(["the", "art", "Paris"]) == ["the", "art"]


def test_cross_check_detects_disagreement():
    ref = lambda prediction, ground_truths: 1.0
    assert sc.cross_check([("x", ["y"])], ref) == [0]
    ok = lambda prediction, ground_truths: sc.best_subspan_em(prediction, ground_truths)
    assert sc.cross_check([("Paris\nz", ["Paris"]), ("no", ["yes"])], ok) == []
