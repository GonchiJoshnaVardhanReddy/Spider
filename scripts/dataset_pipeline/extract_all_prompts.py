import os
import json
import pandas as pd
import jsonlines
from tqdm import tqdm

RAW_DIR = "datasets_raw/external_downloads"
OUTPUT = "datasets_raw/unprocessed/prompts.normalized.json"

PROMPT_KEYS = [
    "prompt",
    "text",
    "instruction",
    "input",
    "query",
    "content"
]

all_prompts = []


def add_prompt(value, source):
    if isinstance(value, str) and len(value) > 5:
        all_prompts.append({
            "prompt": value.strip(),
            "source": source,
            "category": "unknown"
        })


def handle_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    for key in PROMPT_KEYS:
                        if key in row:
                            add_prompt(row[key], path)
    except:
        pass


def handle_jsonl(path):
    try:
        with jsonlines.open(path) as reader:
            for row in reader:
                for key in PROMPT_KEYS:
                    if key in row:
                        add_prompt(row[key], path)
    except:
        pass


def handle_csv(path):
    try:
        df = pd.read_csv(path)
        for col in df.columns:
            if col.lower() in PROMPT_KEYS:
                for val in df[col].dropna():
                    add_prompt(val, path)
    except:
        pass


def handle_parquet(path):
    try:
        df = pd.read_parquet(path)
        for col in df.columns:
            if col.lower() in PROMPT_KEYS:
                for val in df[col].dropna():
                    add_prompt(val, path)
    except:
        pass


def handle_tsv(path):
    try:
        df = pd.read_csv(path, sep="\t")
        for col in df.columns:
            if col.lower() in PROMPT_KEYS:
                for val in df[col].dropna():
                    add_prompt(val, path)
    except:
        pass


for root, _, files in os.walk(RAW_DIR):
    for file in tqdm(files):
        path = os.path.join(root, file)

        if file.endswith(".json"):
            handle_json(path)

        elif file.endswith(".jsonl"):
            handle_jsonl(path)

        elif file.endswith(".csv"):
            handle_csv(path)

        elif file.endswith(".parquet"):
            handle_parquet(path)

        elif file.endswith(".tsv"):
            handle_tsv(path)


os.makedirs("datasets_raw/unprocessed", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(all_prompts, f, indent=2)

print("Extraction complete.")
print("Total prompts:", len(all_prompts))
