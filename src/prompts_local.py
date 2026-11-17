"""Local copy of the original repository's QA prompt construction (cycle 6).

Source: `lost_in_the_middle/prompting.py` and `prompts/qa.prompt`, `prompts/closedbook_qa.prompt`
(MIT licence), printed by the project author. Used (a) offline for tests and (b) as a cross-check
against the repository's own functions in the notebook. When the repository functions can be
imported, they are the reference and the two must give identical strings.
Only the plain QA prompt and the closed-book prompt are copied; the other templates are not used.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import List, Optional

# Template files are read with trailing newlines removed (rstrip("\n")) in the original.
QA_TEMPLATE = (
    "Write a high-quality answer for the given question using only the provided search results "
    "(some of which might be irrelevant).\n\n{search_results}\n\nQuestion: {question}\nAnswer:"
)
CLOSEDBOOK_TEMPLATE = "Question: {question}\nAnswer:"


@dataclass(frozen=True)
class Document:
    title: str
    text: str
    id: Optional[str] = None
    score: Optional[float] = None
    hasanswer: Optional[bool] = None
    isgold: Optional[bool] = None
    original_retrieval_index: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        names = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})


def get_qa_prompt(question: str, documents: List[Document], mention_random_ordering: bool = False,
                  query_aware_contextualization: bool = False) -> str:
    if not question:
        raise ValueError("question must be truthy")
    if not documents:
        raise ValueError("documents must be truthy")
    if mention_random_ordering or query_aware_contextualization:
        raise NotImplementedError("only the plain qa.prompt is copied locally")
    formatted = [f"Document [{i + 1}](Title: {d.title}) {d.text}" for i, d in enumerate(documents)]
    return QA_TEMPLATE.format(question=question, search_results="\n".join(formatted))


def get_closedbook_qa_prompt(question: str) -> str:
    if not question:
        raise ValueError("question must be truthy")
    return CLOSEDBOOK_TEMPLATE.format(question=question)
