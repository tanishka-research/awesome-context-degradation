import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from positionorder.seeds import derive_seed, distractor_permutation  # noqa: E402


def test_derive_seed_is_stable():
    assert derive_seed(101, "q1") == derive_seed(101, "q1")
    assert derive_seed(101, "q1") != derive_seed(202, "q1")
    assert derive_seed(101, "q1") != derive_seed(101, "q2")


def test_permutation_is_valid_and_repeatable():
    p1 = distractor_permutation(101, "q1")
    p2 = distractor_permutation(101, "q1")
    assert p1 == p2
    assert sorted(p1) == list(range(19))


def test_permutation_does_not_depend_on_call_order():
    ids = ["a", "b", "c", "d"]
    forward = {q: distractor_permutation(202, q) for q in ids}
    backward = {q: distractor_permutation(202, q) for q in reversed(ids)}
    assert forward == backward


def test_two_orderings_differ():
    assert distractor_permutation(101, "q1") != distractor_permutation(202, "q1")
