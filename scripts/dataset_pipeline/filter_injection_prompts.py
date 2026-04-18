import json
from tqdm import tqdm

INPUT_FILE = "datasets_raw/unprocessed/prompts.normalized.json"
OUTPUT_FILE = "datasets_raw/unprocessed/prompts.filtered.json"

KEYWORDS = [
    "ignore previous",
    "system prompt",
    "developer mode",
    "internal policy",
    "reveal instructions",
    "override safety",
    "hidden rules",
    "print configuration",
    "bypass restrictions",
    "jailbreak",
    "act as",
    "simulate",
    "pretend",
    "markdown",
    "html comment",
    "base64",
    "encoded",
    "tool call",
    "plugin",
    "function call"
]

filtered = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in tqdm(data):
    prompt = item["prompt"].lower()

    if any(keyword in prompt for keyword in KEYWORDS):
        filtered.append(item)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2)

print("Filtering complete.")
print("Injection prompts:", len(filtered))
