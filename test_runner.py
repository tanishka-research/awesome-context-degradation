"""Offline tests with SYNTHETIC data and a dummy generator. They test the logic only; no model is involved
and no value here says anything about the real data or model."""
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_data import make_example  # noqa: E402
from positionorder import evaluate as ev  # noqa: E402
from positionorder import prompts_local as pl  # noqa: E402
from positionorder import runner as rn  # noqa: E402
from positionorder.data import QAExample, Passage  # noqa: E402

POS = (0, 4, 9, 14, 19)


def to_ex(d):
    return QAExample(d["question"], d["answers"], [Passage(title=c["title"], text=c["text"], isgold=c["isgold"],
                     hasanswer=c["hasanswer"], original_retrieval_index=c["original_retrieval_index"],
                     score=c["score"], id=c["id"]) for c in d["ctxs"]])


def make_world(n=60):
    return {g: [to_ex(make_example(i, g)) for i in range(n)] for g in POS}


def test_eligibility_and_exclusions():
    w = make_world(30)
    w[4][3] = to_ex(make_example(3, 4, bad_distractor=True))          # validation problem
    w[9] = w[9][:-1]                                                    # one question missing
    w[14][5] = to_ex(make_example(5, 14, shuffle_distractors=True))     # inconsistent distractor order
    ok, reasons = rn.eligible_qids(w)
    assert len(ok) == 30 - 3
    assert reasons == {"duplicate_in_file": 0, "missing_in_some_file": 1, "validation_problem": 1,
                       "inconsistent_across_files": 1}


def test_split_is_disjoint_reproducible_and_prefix_stable():
    ids = [f"q{i:03d}" for i in range(200)]
    a = rn.split_questions(ids, 1234, 20, 50)
    b = rn.split_questions(list(reversed(ids)), 1234, 20, 50)
    assert a == b and not set(a["dev"]) & set(a["eval"]) and len(a["dev"]) == 20 and len(a["eval"]) == 50
    assert rn.split_questions(ids, 1234, 20, 50)["dev"][:5] == a["dev"][:5]
    assert rn.split_questions(ids, 4321, 20, 50) != a


def test_documents_keep_set_and_move_only_gold():
    w = make_world(5)
    d0 = {g: rn.docs_for(w[g][0], "O0", g) for g in POS}
    base = {tuple(x["text"] for x in d0[g] if not x["isgold"]) for g in POS}
    assert len(base) == 1                                             # same distractor order in O0 for all g
    for cond in ("O1", "O2"):
        seqs = set()
        for g in POS:
            d = rn.docs_for(w[g][0], cond, g)
            assert len(d) == 20 and d[g]["isgold"] and sum(x["isgold"] for x in d) == 1
            seqs.add(tuple(x["text"] for x in d if not x["isgold"]))
            assert sorted(x["text"] for x in d) == sorted(x["text"] for x in d0[g])
        assert len(seqs) == 1                                         # same shuffled sequence at every position
        assert seqs != base                                           # and it differs from the original order
    o1 = tuple(x["text"] for x in rn.docs_for(w[0][0], "O1", 0) if not x["isgold"])
    o2 = tuple(x["text"] for x in rn.docs_for(w[0][0], "O2", 0) if not x["isgold"])
    assert o1 != o2
    assert rn.docs_for(w[0][0], "C1", None) == [] and len(rn.docs_for(w[0][0], "C2", None)) == 1


def test_local_prompt_format():
    docs = [pl.Document.from_dict(d) for d in rn.docs_for(make_world(2)[0][0], "O0", 0)[:2]]
    p = pl.get_qa_prompt("Who?", docs)
    assert p.startswith("Write a high-quality answer") and "\n\nDocument [1](Title: G) gold passage 0\nDocument [2](Title: T0)" in p
    assert p.endswith("\n\nQuestion: Who?\nAnswer:")
    assert pl.get_closedbook_qa_prompt("Who?") == "Question: Who?\nAnswer:"


def pipeline(tmp, world, n_dev=5, n_eval=20, n_rerun=10):
    ok, _ = rn.eligible_qids(world)
    split = rn.split_questions(ok, 1234, n_dev, n_eval)
    maps = {g: {e.qid: e for e in world[g]} for g in POS}
    answers = {e.qid: e.answers for e in world[0]}
    gold_text = {e.qid: next(p.text for p in e.passages if p.isgold) for e in world[0]}

    def build(job):
        ex = maps[job.gold_index if job.gold_index is not None else 0][job.qid]
        docs = rn.docs_for(ex, job.condition, job.gold_index)
        if job.condition == "C1":
            return pl.get_closedbook_qa_prompt(ex.question)
        return pl.get_qa_prompt(ex.question, [pl.Document.from_dict(d) for d in docs])

    def gen(prompt):                                   # dummy: "knows" the answer if the gold text is in the prompt
        m = re.search(r"gold passage (\d+)", prompt)
        return (f"answer {m.group(1)}\nextra" if m else "I don't know"), 1000, 5, 0

    out = Path(tmp) / "raw.jsonl"
    jobs = rn.make_jobs("eval", split["eval"], [("C1", None), ("C2", None), ("O0", list(POS)), ("O1", list(POS)),
                                                ("O2", list(POS))])
    jobs += rn.make_jobs("eval", split["eval"][:n_rerun], [("R", list(POS))])
    jobs += rn.make_jobs("dev", split["dev"], [("O0", [0, 9]), ("C1", None), ("C2", None), ("R", [0])])
    return out, jobs, build, gen, answers, split


SET = dict(model_id="dummy", template_id="qa.prompt", scorer_version="s", decoding="greedy",
           max_new_tokens=100, ctx_size=8192)


def test_end_to_end_with_dummy_generator_and_resume():
    with tempfile.TemporaryDirectory() as tmp:
        world = make_world(60)
        out, jobs, build, gen, answers, split = pipeline(tmp, world)
        n1 = rn.run_jobs(jobs, build, gen, out, log=lambda *_: None)
        assert n1 == len(jobs)
        assert rn.run_jobs(jobs, build, gen, out, log=lambda *_: None) == 0          # resume: nothing to redo
        with open(out, "a") as fh:
            fh.write('{"split": "eval", "condit')                                    # half-written line
        assert len(rn.load_rows(out)) == len(jobs)
        df = rn.to_predictions(rn.load_rows(out), answers, SET)
        rep = ev.audit(df, positions=POS)
        assert rep.ok, [f.message for f in rep.findings]
        pairs = rn.filter_pairs(df, rn.standard_pairs(POS))
        assert len(pairs) == 5 * 4 + 9
        res = ev.compute_results(df, n_boot=200, pairs=pairs)
        acc = res[res["table"] == "accuracy"]
        c2 = acc[acc.condition == "C2"]["estimate"].iloc[0]
        c1 = acc[acc.condition == "C1"]["estimate"].iloc[0]
        assert c2 == 1.0 and c1 == 0.0                                               # dummy knows the answer iff gold present
        assert (acc[acc.condition.isin(["O0", "O1", "O2"])]["estimate"] == 1.0).all()
        paired = res[res["table"] == "paired"]
        assert (paired["flip_rate"] == 0).all() and (paired["n"].isin([20, 10])).all()
        ev.plot_accuracy(res, Path(tmp) / "fig")
        assert (Path(tmp) / "fig.png").exists() and (Path(tmp) / "fig.pdf").exists()


def test_scorer_disagreement_is_caught():
    rows = [{"split": "eval", "condition": "C1", "gold_index": None, "qid": "q", "run_id": 0,
             "model_answer": "Paris", "n_prompt_tokens": 1, "n_new_tokens": 1, "truncated": 0}]
    bad = lambda prediction, ground_truths: 0.0
    try:
        rn.to_predictions(rows, {"q": ["Paris"]}, SET, repo_scorer=bad)
    except ValueError as exc:
        assert "disagreement" in str(exc)
    else:
        raise AssertionError("expected a disagreement error")


def test_failure_categories():
    assert rn.failure_category("Paris", 1) == "correct"
    assert rn.failure_category("\nParis", 0) == "empty_first_line"
    assert rn.failure_category("The documents do not say.", 0) == "no_answer_or_refusal"
    assert rn.failure_category("London", 0) == "other_wrong"


def test_pipeline_function_with_dummy_generator():
    from positionorder import pipeline as pp
    with tempfile.TemporaryDirectory() as tmp:
        world = make_world(60)
        ok, _ = rn.eligible_qids(world)
        split = rn.split_questions(ok, 1234, 8, 20)
        build = rn.make_build_prompt(world, pl.get_qa_prompt, pl.get_closedbook_qa_prompt, pl.Document)

        def gen(prompt):
            m = re.search(r"gold passage (\d+)", prompt)
            return (f"answer {m.group(1)}" if m else "I don't know"), 900, 4, 0

        s = pp.run_pipeline("t", tmp, world, split, 8, 20, POS, build, gen, SET, n_rerun=10, n_boot=100,
                            log=lambda *_: None)
        assert s["audit_ok"] and s["dev"]["oracle_acc"] == 1.0 and s["dev"]["closed_book_acc"] == 0.0
        assert s["dev"]["rerun_correctness_flips"] == 0
        for name in ("results.csv", "predictions.csv", "audit.json", "fig_accuracy_by_position.png",
                     "failure_counts.csv", "pipeline_summary.json"):
            assert (Path(tmp) / name).exists(), name
        # gate: a generator that never answers must stop the pipeline
        bad = lambda p: ("I don't know", 900, 4, 0)
        try:
            pp.run_pipeline("t2", Path(tmp) / "b", world, split, 8, 20, POS, build, bad, SET, n_boot=50,
                            log=lambda *_: None)
        except RuntimeError as exc:
            assert "GATE FAILED" in str(exc)
        else:
            raise AssertionError("gate should fail when oracle is not above closed-book")


def test_plot_flips_runs_on_dummy_results():
    import pandas as pd
    from positionorder import pipeline as pp
    with tempfile.TemporaryDirectory() as tmp:
        world = make_world(60)
        ok, _ = rn.eligible_qids(world)
        split = rn.split_questions(ok, 1234, 8, 20)
        build = rn.make_build_prompt(world, pl.get_qa_prompt, pl.get_closedbook_qa_prompt, pl.Document)
        gen = lambda p: ("answer 1", 900, 4, 0)
        try:
            pp.run_pipeline("t", tmp, world, split, 8, 20, POS, build, gen, SET, gate=False, n_rerun=10, n_boot=50,
                            log=lambda *_: None)
        except RuntimeError:
            raise
        res = pd.read_csv(Path(tmp) / "results.csv")
        ev.plot_flips(res, Path(tmp) / "flips")
        assert (Path(tmp) / "flips.png").exists() and (Path(tmp) / "flips.pdf").exists()


def test_reduced_design_runs_and_skips_o2():
    from positionorder import pipeline as pp
    with tempfile.TemporaryDirectory() as tmp:
        world = make_world(60)
        ok, _ = rn.eligible_qids(world)
        split = rn.split_questions(ok, 1234, 8, 20)
        build = rn.make_build_prompt(world, pl.get_qa_prompt, pl.get_closedbook_qa_prompt, pl.Document)

        def gen(prompt):
            m = re.search(r"gold passage (\d+)", prompt)
            return (f"answer {m.group(1)}" if m else "I don't know"), 900, 4, 0

        s = pp.run_pipeline("r", tmp, world, split, 8, 20, [0, 9, 19], build, gen, SET, n_rerun=10, n_boot=50,
                            orderings=("O1",), log=lambda *_: None)
        df = __import__("pandas").read_csv(Path(tmp) / "predictions.csv")
        assert s["audit_ok"] and set(df[df.split == "eval"].condition) == {"C1", "C2", "O0", "O1", "R"}
        assert set(df[df.split == "eval"].gold_index.dropna().astype(int)) == {0, 9, 19}
        ev.plot_flips(__import__("pandas").read_csv(Path(tmp) / "results.csv"), Path(tmp) / "fl")
