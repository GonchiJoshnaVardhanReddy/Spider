import json
from tqdm import tqdm

INPUT_FILE = "datasets_raw/unprocessed/prompts.filtered.json"
OUTPUT_FILE = "rag/templates/prompts.json"

seen = set()
cleaned = []


def classify(prompt):
    p = prompt.lower()

    if "system prompt" in p:
        return "system_leak"

    if "ignore previous" in p or "override safety" in p:
        return "override"

    if "developer mode" in p or "act as" in p:
        return "roleplay"

    if "base64" in p or "encoded" in p:
        return "encoding"

    if "markdown" in p or "html comment" in p:
        return "indirect_injection"

    if "plugin" in p or "tool call" in p:
        return "tool_exploit"

    return "general"


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in tqdm(data):

    prompt = item["prompt"].strip()

    if prompt not in seen:
        seen.add(prompt)

        item["category"] = classify(prompt)

        cleaned.append(item)


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2)

print("Deduplication complete.")
print("Final templates:", len(cleaned))
