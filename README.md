# LLM Output Evaluation Framework

A small, **zero-dependency** (Python 3.10+ stdlib only) framework that scores LLM responses automatically,
compares two prompt versions or two models, and measures how far you can trust its LLM judge.

## What it does

| Check | Type | How it works |
|---|---|---|
| **Factual consistency** | deterministic | Compares the response with a reference: required facts (with accepted alternatives) for QA/lists, field-by-field match for JSON. Score 0-1. |
| **Format compliance** | deterministic | Rule-by-rule: single sentence ≤30 words / raw JSON with exact keys / exactly 3 `- ` bullets, and no chatty preamble. Score = fraction of rules passed. |
| **LLM-as-judge** | model-based | 1-5 rubric (see `llm_eval/judge.py`), reference-guided, JSON output. `LLMJudge` calls the Anthropic API; `HeuristicJudge` is an offline stand-in. |

`overall pass = factual pass AND format pass AND judge ≥ 4`. Two variants are compared with paired bootstrap
confidence intervals, win/loss/tie counts, per-task breakdowns and failure reasons.

## Repo layout

```
llm_eval/        checks.py  judge.py  backends.py  runner.py  report.py  agreement.py  stats.py  cli.py
prompts/         v1.txt (plain)  v2.txt (explicit format rules)  <- add vN.txt to add a prompt version
data/            test_set.jsonl (50 prompts)   manual_labels.jsonl (20 human labels)
scripts/         build_testset.py (generates the test set)
results/         results.jsonl  report.md  agreement.json  manual_label_sheet.jsonl
tests/           unit tests for checks and stats
```

## Quick start (offline, no API key)

```bash
./run_all.sh            # tests + 50-prompt run + agreement + report  ->  results/report.md
```

## Real evaluation with Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# compare two prompt versions on one model
python -m llm_eval run --variants v1@claude-haiku-5-5 v2@claude-haiku-5-5 --judge anthropic --out results_real
# or compare two models on one prompt
python -m llm_eval run --variants v2@claude-haiku-5-5 v2@claude-sonnet-5-5 --judge anthropic --out results_models
```
A *variant* is `<prompt_file>@<model>`. Model names not starting with `mock` go to the Anthropic Messages API
(adjust `AnthropicModel`/`AnthropicClient` in `backends.py` to plug in another provider).

## Judge-vs-human agreement workflow

```bash
python -m llm_eval sample       # blind sheet of 20 samples (judge scores hidden) -> results/manual_label_sheet.jsonl
# label each: write data/manual_labels.jsonl lines {"variant","id","label":1-5,"note"}
python -m llm_eval agreement    # exact %, ±1 %, quadratic-weighted κ, Spearman, pass/fail κ, confusion matrix
python -m llm_eval report
```

## Test set

50 prompts: 30 factual QA (one sentence), 10 JSON extraction, 10 "exactly 3 items" lists. Each has a reference
and a format requirement. The `mock` field is used only by the simulator.

## Results shipped in this repo, and their limits (please read)

- The shipped `results/` come from the **offline simulator** (`mock-large`) with the **heuristic judge**.
  They prove the pipeline works end to end; they say nothing about real model quality. Simulated finding:
  prompt v2 raises overall pass rate from 32% to 90% (mostly format), with no significant factual change.
- **The 20 manual labels were written by Claude (the AI that built this), not by a human**, using the rubric
  and without seeing judge scores. For a defensible reliability number, re-label `results/manual_label_sheet.jsonl` yourself.
- Agreement on the shipped sample is high (95% exact, κ≈0.98) but n=20 is small and the sample is mostly easy cases.
  The heuristic judge applies the same rubric through rules, so high agreement is expected. In an earlier
  iteration of the sample, I labelled fenced JSON with a prose preamble as 4 (padding per the rubric) while the heuristic judge scored it 5:
  a real blind spot that remains in `HeuristicJudge`.
- A bug found through the agreement check: a stem (`mitochondri`) in the test set failed the word-boundary match, causing a false factual
  failure. Fixed; this is the kind of issue manual labelling is meant to surface.
- Factual consistency is keyword/field matching: it cannot catch a correct answer plus a contradicting claim.

## Tests

`python -m unittest discover -s tests -v`
