"""LLM-as-judge with an explicit 1-5 rubric, plus an offline heuristic stand-in."""
import json
import re

from .checks import PREAMBLES, factual_consistency, norm

RUBRIC = """Score the RESPONSE against the REFERENCE on content quality, from 1 to 5:
5 = Fully correct and complete relative to the reference; answers directly; no unsupported claims.
4 = Correct and complete, but padded: prose preamble, filler, or needless elaboration.
3 = Partially correct or incomplete: some required facts right, others missing or wrong.
2 = Mostly incorrect; only a small relevant fragment.
1 = Incorrect, contradicts the reference, off-topic, or a refusal.
Rules: the reference is the source of truth. Do NOT penalise code fences or bullet style by themselves
(formatting is checked separately); DO penalise prose padding. Do not reward length."""

JUDGE_SYSTEM = ("You are a strict, consistent grader of LLM answers.\n" + RUBRIC +
                '\nReply with ONLY a JSON object: {"rationale": "<one sentence>", "score": <1-5 integer>}')

JUDGE_USER = "QUESTION:\n{question}\n\nREFERENCE:\n{reference}\n\nRESPONSE:\n{response}"


def reference_text(item: dict) -> str:
    return json.dumps(item["expected_json"]) if item["format"] == "json" else item["reference"]


class LLMJudge:
    def __init__(self, client):
        self.client = client
        self.name = f"llm-judge:{client.model}"

    def score(self, item: dict, response: str) -> dict:
        user = JUDGE_USER.format(question=item["question"], reference=reference_text(item), response=response)
        for _ in range(2):
            raw = self.client.complete(JUDGE_SYSTEM, user, max_tokens=300, temperature=0.0)
            m = re.search(r"\{.*\}", raw, re.S)
            try:
                obj = json.loads(m.group(0))
                s = int(obj["score"])
                if 1 <= s <= 5:
                    return {"score": s, "rationale": str(obj.get("rationale", ""))}
            except (AttributeError, ValueError, KeyError, json.JSONDecodeError):
                pass
        return {"score": None, "rationale": "judge output unparseable"}


class HeuristicJudge:
    """Offline stand-in that applies the same rubric with simple rules. NOT a real LLM judge:
    use it only to exercise the pipeline. Use --judge anthropic for real scores."""
    name = "heuristic-judge"

    def score(self, item: dict, response: str) -> dict:
        f = factual_consistency(item, response).score
        if f >= 1.0:
            words = len(response.split())
            padded = norm(response).startswith(PREAMBLES)
            if item["format"] == "sentence":
                padded = padded or words > 40
            if item["format"] == "list3":
                padded = padded or len([l for l in response.splitlines() if l.strip()]) > 3
            return {"score": 4 if padded else 5, "rationale": "correct" + (", padded" if padded else "")}
        if f >= 0.5:
            return {"score": 3, "rationale": "partially correct"}
        if f > 0:
            return {"score": 2, "rationale": "mostly incorrect"}
        return {"score": 1, "rationale": "incorrect"}
