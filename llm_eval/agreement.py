"""Judge-vs-human agreement on a labelled sample."""
import json
import random
from collections import defaultdict
from pathlib import Path

from .stats import cohen_kappa, mean, spearman


def make_sample_sheet(results_path, out_path, n=20, seed=7):
    """Blind labelling sheet (no judge scores), balanced across judge-score levels."""
    rows = [json.loads(l) for l in Path(results_path).read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r["judge_score"] is not None]
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for r in rows:
        buckets[r["judge_score"]].append(r)
    for b in buckets.values():
        rng.shuffle(b)
    picked, keys = [], sorted(buckets)
    while len(picked) < n and any(buckets.values()):
        for k in keys:
            if buckets[k] and len(picked) < n:
                picked.append(buckets[k].pop())
    rng.shuffle(picked)
    sheet = [{"variant": r["variant"], "id": r["id"], "question": r["question"],
              "reference": r["reference"], "response": r["response"], "label": None} for r in picked]
    Path(out_path).write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in sheet) + "\n")
    return sheet


def compute_agreement(results_path, labels_path):
    res = {(r["variant"], r["id"]): r for r in
           (json.loads(l) for l in Path(results_path).read_text().splitlines() if l.strip())}
    labels = [json.loads(l) for l in Path(labels_path).read_text().splitlines() if l.strip()]
    pairs = [(l["label"], res[(l["variant"], l["id"])]["judge_score"], l) for l in labels]
    human = [p[0] for p in pairs]
    judge = [p[1] for p in pairs]
    n = len(pairs)
    cats = [1, 2, 3, 4, 5]
    conf = [[0] * 5 for _ in range(5)]   # rows = human, cols = judge
    for h, j in zip(human, judge):
        conf[h - 1][j - 1] += 1
    hb = [int(h >= 4) for h in human]
    jb = [int(j >= 4) for j in judge]
    out = {
        "n": n,
        "exact_agreement": sum(h == j for h, j in zip(human, judge)) / n,
        "within_1": sum(abs(h - j) <= 1 for h, j in zip(human, judge)) / n,
        "quadratic_weighted_kappa": cohen_kappa(human, judge, cats, "quadratic"),
        "spearman": spearman(human, judge),
        "binary_pass_agreement": sum(a == b for a, b in zip(hb, jb)) / n,
        "binary_pass_kappa": cohen_kappa(hb, jb, [0, 1]),
        "mean_bias_judge_minus_human": mean([j - h for h, j in zip(human, judge)]),
        "confusion_human_rows_judge_cols": conf,
        "disagreements": [{"variant": l["variant"], "id": l["id"], "human": h, "judge": j, "note": l.get("note", "")}
                          for h, j, l in pairs if h != j],
    }
    return out
