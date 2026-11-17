# Data

No data are stored in this repository.

Source: the 20-document NaturalQuestions-Open file with the gold passage at index 0 (`nq-open-20_total_documents_gold_at_0.jsonl.gz`, 2,655 questions) from the data release of the original *Lost in the Middle* authors, repository commit `29b8a6d042ce29abccee3db1a73171a107d7e6af`.

File used in the reported run: SHA-256 `69a8dd87a45f07fb3ed9b804917a89db975cd6e488682fc838edca029cc3881f`.

The files for gold indices 4, 9, 14 and 19 were built from it by `src/positionorder/derive.py`; their hashes are in `configs/freeze_reduced.json` (hashes differ between runs because of compression headers). Validation output of the run: `results/reduced/data_validation_report.json`.
