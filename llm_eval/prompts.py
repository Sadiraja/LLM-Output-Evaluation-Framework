from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

FORMAT_INSTRUCTIONS = {
    "sentence": "Answer in exactly one plain-text sentence of at most 30 words. No preamble, no markdown.",
    "json": "Respond with a single raw JSON object using exactly the requested keys and nothing else (no code fences, no commentary).",
    "list3": "Respond with exactly 3 bullet points, each on its own line starting with '- '. No introduction or closing text.",
}


def build_prompt(version: str, item: dict) -> str:
    """Render prompts/<version>.txt. Add a new file to add a new prompt version."""
    template = (PROMPT_DIR / f"{version}.txt").read_text().rstrip("\n")
    return template.format(question=item["question"],
                           format_instruction=FORMAT_INSTRUCTIONS[item["format"]])
