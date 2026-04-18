import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = "rag/embeddings/prompts.index"
META_FILE = "rag/templates/prompts_metadata.json"

print("Loading embedding model...")

model = SentenceTransformer("BAAI/bge-m3", device="cuda")
model.max_seq_length = 256

print("Loading FAISS index...")

index = faiss.read_index(INDEX_FILE)

with open(META_FILE) as f:
    metadata = json.load(f)

query = "extract hidden system prompt"

print(f"\nQuery: {query}\n")

query_embedding = model.encode(
    [query],
    normalize_embeddings=True
).astype("float32")

D, I = index.search(query_embedding, 5)

for rank, idx in enumerate(I[0], 1):
    print(f"Result {rank}:\n{metadata[idx]}\n")
