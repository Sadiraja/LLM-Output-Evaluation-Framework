"""Deterministic checks: factual consistency vs a reference, and format compliance."""
import json
import re
from dataclasses import dataclass, field

PREAMBLES = ("sure", "certainly", "great question", "of course", "here is", "here's",
             "absolutely", "happy to")


@dataclass
class CheckResult:
    name: str
    score: float            # 0..1
    passed: bool
    detail: str = ""
    rules: dict = field(default_factory=dict)


def norm(s) -> str:
    s = str(s).lower()
    s = re.sub(r"(?<=\d),(?=\d)", "", s)          # 299,792 -> 299792
    s = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", s)     # drop sentence periods, keep decimals
    s = re.sub(r"[^a-z0-9.\s'-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _hit(alt: str, text: str, mode: str) -> bool:
    pat = r"(?<![a-z0-9])" + re.escape(norm(alt))
    if mode != "prefix":
        pat += r"(?![a-z0-9])"
    return re.search(pat, text) is not None


def extract_json(response: str):
    """Lenient JSON extraction (handles code fences / chatter). Returns dict or None."""
    r = re.sub(r"```(?:json)?", "", response)
    i, j = r.find("{"), r.rfind("}")
    if i == -1 or j <= i:
        return None
    try:
        obj = json.loads(r[i:j + 1])
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def factual_consistency(item: dict, response: str) -> CheckResult:
    """Does the response contain the facts in the reference? (pass == score 1.0)"""
    name = "factual_consistency"
    if item["format"] == "json":
        obj = extract_json(response)
        exp = item["expected_json"]
        if obj is None:
            return CheckResult(name, 0.0, False, "no parseable JSON")
        ok = [k for k, v in exp.items() if k in obj and norm(obj[k]) == norm(v)]
        s = len(ok) / len(exp)
        return CheckResult(name, s, s == 1.0, f"{len(ok)}/{len(exp)} fields match")
    text = norm(response)
    groups = item["must_include"]            # list of alternative-lists; one hit per group
    mode = item.get("match", "word")
    hits = sum(any(_hit(a, text, mode) for a in g) for g in groups)
    need = item.get("min_hits", len(groups))
    s = min(1.0, hits / need)
    return CheckResult(name, s, s >= 1.0, f"{hits}/{need} required facts found")


def format_compliance(item: dict, response: str) -> CheckResult:
    """Strict, rule-by-rule format check. score = fraction of rules passed."""
    r = response.strip()
    fmt = item["format"]
    no_pre = not norm(r).startswith(PREAMBLES)
    if fmt == "sentence":
        rules = {"single_line": bool(r) and "\n" not in r,
                 "max_30_words": len(r.split()) <= 30,
                 "no_markdown": not re.search(r"[*#`_]", r),
                 "no_preamble": no_pre}
    elif fmt == "json":
        try:
            obj = json.loads(r)
        except json.JSONDecodeError:
            obj = None
        rules = {"raw_json_only": isinstance(obj, dict),
                 "exact_keys": isinstance(obj, dict) and set(obj) == set(item["expected_json"])}
    elif fmt == "list3":
        lines = [l for l in r.splitlines() if l.strip()]
        rules = {"exactly_3_items": len(lines) == 3,
                 "dash_bullets": bool(lines) and all(l.lstrip().startswith("- ") for l in lines),
                 "no_preamble": no_pre}
    else:
        raise ValueError(f"unknown format {fmt}")
    s = sum(rules.values()) / len(rules)
    failed = [k for k, v in rules.items() if not v]
    return CheckResult("format_compliance", s, not failed,
                       "ok" if not failed else "failed: " + ", ".join(failed), rules)
