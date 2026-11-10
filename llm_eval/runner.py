"""Runs variants (prompt@model) over a test set: generate -> checks -> judge."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .backends import make_model
from .checks import factual_consistency, format_compliance
from .prompts import build_prompt

JUDGE_PASS = 4  # judge score >= 4 counts as a content pass


def load_testset(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def evaluate_one(variant, model, judge, item):
    prompt = build_prompt(variant.split("@")[0], item)
    response = model.generate(prompt, item, variant)
    fc, fm, j = factual_consistency(item, response), format_compliance(item, response), judge.score(item, response)
    js = j["score"]
    return {"variant": variant, "id": item["id"], "format": item["format"], "question": item["question"],
            "reference": item["reference"], "response": response,
            "fact_score": fc.score, "fact_pass": fc.passed, "fact_detail": fc.detail,
            "fmt_score": fm.score, "fmt_pass": fm.passed, "fmt_detail": fm.detail,
            "judge_score": js, "judge_rationale": j["rationale"],
            "overall_pass": bool(fc.passed and fm.passed and js is not None and js >= JUDGE_PASS)}


def run(testset_path, variants, judge, out_dir, workers=4, limit=None):
    items = load_testset(testset_path)[: limit or None]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    models = {v: make_model(v.split("@", 1)[1]) for v in variants}
    jobs = [(v, models[v], it) for v in variants for it in items]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(lambda a: evaluate_one(a[0], a[1], judge, a[2]), jobs))
    (out / "results.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    simulated = any(v.split("@", 1)[1].startswith("mock") for v in variants)
    meta = {"variants": variants, "n_items": len(items), "judge": judge.name,
            "simulated_models": simulated, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return rows, meta
