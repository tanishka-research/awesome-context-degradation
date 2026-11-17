"""Seed controls for the position/order study.

Design rules
------------
* Never use Python's built-in hash() for seeds: it is salted per process.
* Derive every random draw from (base seed, stable identifiers) with SHA-256,
  so results do not depend on iteration order, resumption, or process restarts.
* Seeds are set in configs/protocol_v0.1.yaml before any result exists and are
  not tuned afterwards. Changing one is a logged protocol amendment.
"""

from __future__ import annotations

import hashlib
import random
from typing import List

import numpy as np


def derive_seed(base_seed: int, *parts: object) -> int:
    """Return a 64-bit seed derived from a base seed and stable identifiers."""
    key = ":".join([str(base_seed)] + [str(p) for p in parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def set_global_seed(seed: int) -> None:
    """Seed Python's and NumPy's global generators.

    Note: PYTHONHASHSEED only takes effect if set before the interpreter starts,
    which is why no result in this project depends on hash().
    """
    random.seed(seed)
    np.random.seed(seed % (2**32))


def distractor_permutation(ordering_seed: int, question_id: str, n: int = 19) -> List[int]:
    """Fixed permutation of n distractors for one question and one ordering seed.

    The same (ordering_seed, question_id) always gives the same permutation,
    whatever else has been generated before. The permutation is NOT a function of
    the gold position, so only the gold index moves between conditions.
    """
    rng = np.random.Generator(np.random.PCG64(derive_seed(ordering_seed, question_id)))
    return [int(i) for i in rng.permutation(n)]
