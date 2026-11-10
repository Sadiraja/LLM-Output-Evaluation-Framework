"""Model + API clients. AnthropicClient/AnthropicModel need ANTHROPIC_API_KEY.
MockModel is a deterministic *simulator* so the pipeline can run offline."""
import json
import os
import random
import time
import urllib.error
import urllib.request


class AnthropicClient:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set ANTHROPIC_API_KEY to use the Anthropic backend.")

    def complete(self, system: str, user: str, max_tokens: int = 500, temperature: float = 0.0) -> str:
        body = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
                "messages": [{"role": "user", "content": user}]}
        if system:
            body["system"] = system
        req = urllib.request.Request(self.URL, data=json.dumps(body).encode(), method="POST", headers={
            "content-type": "application/json", "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.load(resp)
                return "".join(b.get("text", "") for b in data["content"] if b["type"] == "text")
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise


class AnthropicModel:
    def __init__(self, name: str):
        self.name = name
        self.client = AnthropicClient(name)

    def generate(self, prompt: str, item: dict, variant: str) -> str:
        return self.client.complete("", prompt, max_tokens=400, temperature=0.0)


# ---- simulator -------------------------------------------------------------
MODEL_ERROR_RATE = {"mock-large": 0.04, "mock-small": 0.14}
FLUFF = " This is a well-known fact that is often taught in schools, and it is generally useful to remember in everyday life."


class MockModel:
    """Simulates a model: v1-style prompts usually yield chatty/unformatted output,
    v2-style prompts usually comply. Errors are random but seeded per (variant, item)."""

    def __init__(self, name: str):
        self.name = name
        self.err = MODEL_ERROR_RATE.get(name, 0.08)

    def generate(self, prompt: str, item: dict, variant: str) -> str:
        pv = variant.split("@")[0]
        rng = random.Random(f"{variant}|{item['id']}")
        wrong = rng.random() < self.err
        messy = rng.random() < (0.75 if pv == "v1" else 0.06)
        hints = item["mock"]
        fmt = item["format"]
        if fmt == "sentence":
            core = f"It is {hints['wrong']}." if wrong else item["reference"]
            return f"Great question! {core}{FLUFF}" if messy else core
        if fmt == "json":
            obj = dict(item["expected_json"])
            if wrong:
                k = rng.choice(list(obj))
                obj[k] = obj[k] + 1 if isinstance(obj[k], int) else "Unknown"
            if messy:
                return "Here is the extracted data:\n```json\n" + json.dumps(obj, indent=2) + "\n```"
            return json.dumps(obj)
        concepts = hints["concepts"]
        if wrong:
            chosen = [rng.choice(concepts), "It is generally a good idea.", "Many people find it helpful."]
        else:
            chosen = rng.sample(concepts, 5 if messy else 3)
        if messy:
            return "Sure! Here are some ideas:\n" + "\n".join(f"{i+1}. {c}" for i, c in enumerate(chosen))
        return "\n".join(f"- {c}" for c in chosen)


def make_model(name: str):
    return MockModel(name) if name.startswith("mock") else AnthropicModel(name)
