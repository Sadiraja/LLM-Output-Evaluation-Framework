"""Markdown comparison report for two variants (baseline A vs candidate B)."""
import json
from collections import Counter
from pathlib import Path

from .stats import bootstrap_ci, mean

METRICS = [("Factual consistency (mean 0-1)", "fact_score"), ("Factual pass rate", "fact_pass"),
           ("Format compliance (mean 0-1)", "fmt_score"), ("Format pass rate", "fmt_pass"),
           ("Judge score (mean 1-5)", "judge_score"), ("Overall pass rate*", "overall_pass")]


def _load(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def _fmt(x, rate=False):
    return f"{x*100:.1f}%" if rate else f"{x:.2f}"


def build_report(out_dir, agreement_path=None):
    out = Path(out_dir)
    meta = json.loads((out / "meta.json").read_text())
    rows = _load(out / "results.jsonl")
    A, B = meta["variants"][:2]
    by = {v: {r["id"]: r for r in rows if r["variant"] == v} for v in (A, B)}
    ids = [i for i in by[A] if i in by[B] and by[A][i]["judge_score"] is not None and by[B][i]["judge_score"] is not None]
    n = len(ids)
    L = [f"# LLM evaluation report: `{A}` vs `{B}`", ""]
    if meta["simulated_models"]:
        L += ["> **SIMULATED RUN.** The models were produced by the offline `MockModel` simulator "
              "(`mock-*`), so the numbers below demonstrate the framework, not real model quality. "
              "Re-run with real model names and `--judge anthropic` for real results (see README).", ""]
    L += [f"- Test set: **{meta['n_items']} prompts** ({n} scored for both variants)",
          f"- Judge: `{meta['judge']}`   - Generated: {meta['timestamp']}",
          "- Baseline (A) = first variant, candidate (B) = second variant", "",
          "## 1. Headline metrics", "",
          f"| Metric | A: {A} | B: {B} | Δ (B−A) | 95% bootstrap CI | Significant? |", "|---|---|---|---|---|---|"]
    sig_notes = []
    for label, key in METRICS:
        rate = key.endswith("pass") or key == "overall_pass"
        a = [float(by[A][i][key]) for i in ids]
        b = [float(by[B][i][key]) for i in ids]
        d = [y - x for x, y in zip(a, b)]
        lo, hi = bootstrap_ci(d)
        sig = "yes" if (lo > 0 or hi < 0) else "no"
        L.append(f"| {label} | {_fmt(mean(a), rate)} | {_fmt(mean(b), rate)} | {mean(d):+.3f} | [{lo:+.3f}, {hi:+.3f}] | {sig} |")
        sig_notes.append((label, mean(d), sig))
    L += ["", "*Overall pass = factual pass AND format pass AND judge score ≥ 4. "
          "CIs come from 2,000 paired bootstrap resamples over prompts.", ""]
    ja = [by[A][i]["judge_score"] for i in ids]
    jb = [by[B][i]["judge_score"] for i in ids]
    w = sum(y > x for x, y in zip(ja, jb)); l = sum(y < x for x, y in zip(ja, jb)); t = n - w - l
    L += [f"Judge score head-to-head: **B wins {w}, A wins {l}, ties {t}**.", "", "## 2. Breakdown by task type", "",
          "| Task | n | Judge A | Judge B | Format pass A | Format pass B | Fact pass A | Fact pass B |", "|---|---|---|---|---|---|---|---|"]
    for fmt in ("sentence", "json", "list3"):
        s = [i for i in ids if by[A][i]["format"] == fmt]
        g = lambda v, k: mean([float(by[v][i][k]) for i in s])
        L.append(f"| {fmt} | {len(s)} | {g(A,'judge_score'):.2f} | {g(B,'judge_score'):.2f} | "
                 f"{g(A,'fmt_pass')*100:.0f}% | {g(B,'fmt_pass')*100:.0f}% | {g(A,'fact_pass')*100:.0f}% | {g(B,'fact_pass')*100:.0f}% |")
    L += ["", "## 3. Most common failure reasons", ""]
    for v in (A, B):
        c = Counter()
        for i in ids:
            r = by[v][i]
            if not r["fmt_pass"]:
                for rule in r["fmt_detail"].replace("failed: ", "").split(", "):
                    c[f"format: {rule}"] += 1
            if not r["fact_pass"]:
                c["factual: missing/incorrect facts"] += 1
        L.append(f"- `{v}`: " + (", ".join(f"{k} ×{x}" for k, x in c.most_common(5)) or "none"))
    L += ["", "## 4. Examples where B is worse than A", ""]
    worse = [i for i in ids if by[B][i]["judge_score"] < by[A][i]["judge_score"]][:3]
    if not worse:
        L.append("_None: B was never scored lower than A by the judge._")
    for i in worse:
        L += [f"**{i}**: {by[A][i]['question']}", f"- A ({by[A][i]['judge_score']}): `{by[A][i]['response'][:140]!r}`",
              f"- B ({by[B][i]['judge_score']}): `{by[B][i]['response'][:140]!r}`", ""]
    if agreement_path and Path(agreement_path).exists():
        ag = json.loads(Path(agreement_path).read_text())
        k = lambda x: "n/a" if x is None else f"{x:.2f}"
        L += ["## 5. Judge reliability (agreement with manual labels)", "",
              f"Judge scores were compared with {ag['n']} hand-labelled samples (rubric in `llm_eval/judge.py`).", "",
              "| Measure | Value |", "|---|---|",
              f"| Exact agreement | {ag['exact_agreement']*100:.0f}% |", f"| Within ±1 point | {ag['within_1']*100:.0f}% |",
              f"| Quadratic-weighted Cohen's κ | {k(ag['quadratic_weighted_kappa'])} |", f"| Spearman ρ | {k(ag['spearman'])} |",
              f"| Pass/fail agreement (score ≥ 4) | {ag['binary_pass_agreement']*100:.0f}% |",
              f"| Pass/fail Cohen's κ | {k(ag['binary_pass_kappa'])} |",
              f"| Mean bias (judge − human) | {ag['mean_bias_judge_minus_human']:+.2f} |", "",
              "Confusion matrix (rows = human, columns = judge, scores 1-5):", "", "```"]
        L += ["      judge: 1  2  3  4  5"] + [f"human {i+1}:    " + "  ".join(str(x) for x in row) for i, row in enumerate(ag["confusion_human_rows_judge_cols"])]
        L += ["```", ""]
        if ag["disagreements"]:
            L.append("Disagreements:")
            L += [f"- `{d['variant']}` {d['id']}: human {d['human']}, judge {d['judge']}: {d['note']}" for d in ag["disagreements"]]
            L.append("")
    L += ["## 6. Conclusion", ""]
    best = next(s for s in sig_notes if s[0].startswith("Overall"))
    verdict = "improves" if best[1] > 0 else "worsens" if best[1] < 0 else "does not change"
    L.append(f"On the overall pass rate, `{B}` {verdict} on `{A}` by {best[1]*100:+.1f} points "
             f"({'statistically distinguishable from zero' if best[2]=='yes' else 'not significant at 95%'}).")
    (out / "report.md").write_text("\n".join(L) + "\n")
    return out / "report.md"
