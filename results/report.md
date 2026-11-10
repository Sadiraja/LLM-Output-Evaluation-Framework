# LLM evaluation report: `v1@mock-large` vs `v2@mock-large`

> **SIMULATED RUN.** The models were produced by the offline `MockModel` simulator (`mock-*`), so the numbers below demonstrate the framework, not real model quality. Re-run with real model names and `--judge anthropic` for real results (see README).

- Test set: **50 prompts** (50 scored for both variants)
- Judge: `heuristic-judge`   - Generated: 2026-11-09 20:23:26
- Baseline (A) = first variant, candidate (B) = second variant

## 1. Headline metrics

| Metric | A: v1@mock-large | B: v2@mock-large | Δ (B−A) | 95% bootstrap CI | Significant? |
|---|---|---|---|---|---|
| Factual consistency (mean 0-1) | 0.97 | 0.98 | +0.007 | [-0.053, +0.060] | no |
| Factual pass rate | 96.0% | 98.0% | +0.020 | [-0.040, +0.080] | no |
| Format compliance (mean 0-1) | 0.60 | 0.95 | +0.350 | [+0.235, +0.475] | yes |
| Format pass rate | 32.0% | 92.0% | +0.600 | [+0.440, +0.760] | yes |
| Judge score (mean 1-5) | 4.24 | 4.84 | +0.600 | [+0.340, +0.860] | yes |
| Overall pass rate* | 32.0% | 90.0% | +0.580 | [+0.420, +0.740] | yes |

*Overall pass = factual pass AND format pass AND judge score ≥ 4. CIs come from 2,000 paired bootstrap resamples over prompts.

Judge score head-to-head: **B wins 31, A wins 3, ties 16**.

## 2. Breakdown by task type

| Task | n | Judge A | Judge B | Format pass A | Format pass B | Fact pass A | Fact pass B |
|---|---|---|---|---|---|---|---|
| sentence | 30 | 4.13 | 4.77 | 23% | 90% | 97% | 97% |
| json | 10 | 4.50 | 5.00 | 50% | 100% | 100% | 100% |
| list3 | 10 | 4.30 | 4.90 | 40% | 90% | 90% | 100% |

## 3. Most common failure reasons

- `v1@mock-large`: format: no_preamble ×29, format: max_30_words ×13, format: exactly_3_items ×6, format: dash_bullets ×6, format: raw_json_only ×5
- `v2@mock-large`: format: no_preamble ×4, format: max_30_words ×3, factual: missing/incorrect facts ×1, format: exactly_3_items ×1, format: dash_bullets ×1

## 4. Examples where B is worse than A

**qa18**: What is the capital of Canada?
- A (4): `'Great question! The capital of Canada is Ottawa. This is a well-known fact that is often taught in schools, and it is generally useful to re'`
- B (1): `'It is Toronto.'`

**qa27**: Which language has the most native speakers worldwide?
- A (5): `'Mandarin Chinese has the most native speakers worldwide.'`
- B (4): `'Great question! Mandarin Chinese has the most native speakers worldwide. This is a well-known fact that is often taught in schools, and it i'`

**ls04**: Name exactly 3 renewable energy sources.
- A (5): `'- Geothermal energy\n- Biomass energy\n- Solar power'`
- B (4): `'Sure! Here are some ideas:\n1. Geothermal energy\n2. Solar power\n3. Hydroelectric power\n4. Wind power\n5. Tidal energy'`

## 5. Judge reliability (agreement with manual labels)

Judge scores were compared with 20 hand-labelled samples (rubric in `llm_eval/judge.py`).

| Measure | Value |
|---|---|
| Exact agreement | 95% |
| Within ±1 point | 100% |
| Quadratic-weighted Cohen's κ | 0.98 |
| Spearman ρ | 1.00 |
| Pass/fail agreement (score ≥ 4) | 100% |
| Pass/fail Cohen's κ | 1.00 |
| Mean bias (judge − human) | +0.05 |

Confusion matrix (rows = human, columns = judge, scores 1-5):

```
      judge: 1  2  3  4  5
human 1:    2  0  0  0  0
human 2:    0  0  1  0  0
human 3:    0  0  0  0  0
human 4:    0  0  0  9  0
human 5:    0  0  0  0  8
```

Disagreements:
- `v1@mock-large` ls09: human 2, judge 3: only 1 of 3 bullets is a real tip

## 6. Conclusion

On the overall pass rate, `v2@mock-large` improves on `v1@mock-large` by +58.0 points (statistically distinguishable from zero).
