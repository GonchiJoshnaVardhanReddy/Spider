"""Build semantic embeddings and FAISS index for planner template retrieval."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.lib.format import open_memmap

try:
    import torch
except ImportError:  # pragma: no cover - optional runtime dependency
    torch = None


DEFAULT_PROMPTS_PATH = Path("rag/templates/prompts.json")
DEFAULT_METADATA_PATH = Path("rag/templates/metadata.json")
DEFAULT_EMBEDDINGS_PATH = Path("rag/embeddings/prompts_embeddings.npy")
DEFAULT_INDEX_PATH = Path("rag/embeddings/prompts.index")
DEFAULT_CATEGORY_INDEX_PATH = Path("rag/templates/category_index.json")
DEFAULT_CONFIG_PATH = Path("configs/index_config.json")

MODEL_NAME = "BAAI/bge-m3"


def load_json_list(path: Path) -> list[Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array.")
    return payload


def extract_prompt_text(record: Any, index: int) -> str:
    if isinstance(record, str):
        text = record
    elif isinstance(record, dict):
        text = record.get("prompt")
    else:
        raise ValueError(f"Invalid prompt record at index {index}: {type(record).__name__}")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Prompt text at index {index} is missing or empty.")
    return text


def load_template_texts(prompts_path: Path, metadata_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    prompts_payload = load_json_list(prompts_path)
    metadata_payload = load_json_list(metadata_path)

    if len(prompts_payload) != len(metadata_payload):
        raise ValueError(
            "Dataset/metadata alignment error: prompts.json and metadata.json lengths differ."
        )

    texts: list[str] = []
    for idx, prompt_record in enumerate(prompts_payload):
        text = extract_prompt_text(prompt_record, idx)
        meta = metadata_payload[idx]
        if not isinstance(meta, dict):
            raise ValueError(f"Metadata entry at index {idx} must be an object.")
        meta_prompt = meta.get("prompt")
        if isinstance(meta_prompt, str) and meta_prompt != text:
            raise ValueError(
                f"Dataset/metadata alignment error at index {idx}: prompt mismatch."
            )
        texts.append(text)

    return texts, metadata_payload


def extract_dense_matrix(encoded: Any) -> np.ndarray:
    matrix_source = encoded
    if isinstance(encoded, dict):
        for key in ("dense_vecs", "dense_embeddings", "embeddings"):
            if key in encoded:
                matrix_source = encoded[key]
                break
        else:
            raise ValueError("Embedding payload missing dense vectors.")

    matrix = np.asarray(matrix_source, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError(f"Expected 2D embeddings matrix, got shape {matrix.shape}.")
    return matrix


def build_category_lookup(metadata: list[dict[str, Any]]) -> dict[str, list[int]]:
    category_lookup: dict[str, list[int]] = {}
    for idx, row in enumerate(metadata):
        category = row.get("category")
        if not isinstance(category, str) or not category:
            raise ValueError(f"Missing category in metadata at index {idx}.")
        category_lookup.setdefault(category, []).append(idx)
    return category_lookup


def build_index_config(
    *,
    embedding_dim: int,
    dataset_size: int,
    model_name: str,
    batch_size: int,
    max_length: int,
) -> dict[str, Any]:
    return {
        "model": model_name.replace("BAAI/", "").lower(),
        "embedding_model": model_name,
        "embedding_dim": embedding_dim,
        "normalized": True,
        "metric": "cosine",
        "dataset_size": dataset_size,
        "batch_size": batch_size,
        "max_length": max_length,
    }


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def is_cuda_available() -> bool:
    return bool(torch is not None and torch.cuda.is_available())


def supports_symlinks() -> bool:
    if os.name != "nt":
        return True
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        target = temp_path / "target.txt"
        link = temp_path / "link.txt"
        target.write_text("x", encoding="utf-8")
        try:
            os.symlink(target, link)
        except OSError:
            return False
        return True


class SentenceTransformerAdapter:
    """Adapter to make SentenceTransformer match the BGEM3 encode contract."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def encode(self, texts: list[str], *, batch_size: int, max_length: int) -> np.ndarray:
        self._model.max_seq_length = max_length
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=False,
            convert_to_numpy=True,
            show_progress_bar=False,
        )


def load_embedding_model(model_name: str, use_gpu: bool) -> tuple[Any, str]:
    if not supports_symlinks():
        from sentence_transformers import SentenceTransformer

        device = "cuda" if use_gpu else "cpu"
        model = SentenceTransformer(model_name, device=device)
        return SentenceTransformerAdapter(model), "sentence-transformers"

    try:
        from FlagEmbedding import BGEM3FlagModel

        return BGEM3FlagModel(
    model_name,
    use_fp16=True,
    device="cuda"
), "FlagEmbedding"
    except (ImportError, OSError):  # pragma: no cover - fallback runtime dependency
        from sentence_transformers import SentenceTransformer

        device = "cuda" if use_gpu else "cpu"
        model = SentenceTransformer(model_name, device=device)
        return SentenceTransformerAdapter(model), "sentence-transformers"


def encode_batch(
    model: Any,
    texts: list[str],
    *,
    batch_size: int,
    max_length: int,
) -> np.ndarray:
    encoded = model.encode(texts, batch_size=batch_size, max_length=max_length)
    return extract_dense_matrix(encoded)


def encode_with_adaptive_batch(
    model: Any,
    texts: list[str],
    *,
    batch_size: int,
    max_length: int,
) -> tuple[np.ndarray, int]:
    current_batch = batch_size
    while True:
        try:
            vectors = encode_batch(
                model,
                texts,
                batch_size=current_batch,
                max_length=max_length,
            )
            return vectors, current_batch
        except RuntimeError as exc:
            message = str(exc).lower()
            is_oom = "out of memory" in message
            if not is_oom or current_batch <= 1:
                raise
            next_batch = max(1, current_batch // 2)
            print(f"OOM at batch size {current_batch}; retrying with batch size {next_batch}.")
            current_batch = next_batch
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()


def load_state(state_path: Path) -> dict[str, Any] | None:
    if not state_path.exists():
        return None
    with state_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(
    state_path: Path,
    *,
    completed: int,
    total: int,
    embedding_dim: int,
    batch_size: int,
    max_length: int,
    model_name: str,
) -> None:
    save_json(
        state_path,
        {
            "completed": completed,
            "total": total,
            "embedding_dim": embedding_dim,
            "batch_size": batch_size,
            "max_length": max_length,
            "model": model_name,
        },
    )


def generate_embeddings(
    model: Any,
    texts: list[str],
    embeddings_path: Path,
    *,
    model_name: str,
    batch_size: int,
    max_length: int,
) -> np.ndarray:
    total = len(texts)
    state_path = embeddings_path.with_suffix(".state.json")
    state = load_state(state_path)

    if embeddings_path.exists() and state is None:
        cached = np.load(embeddings_path, mmap_mode="r")
        if cached.shape[0] != total:
            raise ValueError(
                "Embedding cache size mismatch. Remove prompts_embeddings.npy and rebuild."
            )
        return cached

    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    completed = 0
    current_batch = batch_size
    mmap_array: np.memmap | None = None

    if embeddings_path.exists() and state is not None:
        if state.get("total") != total:
            raise ValueError("Resume state total does not match current dataset.")
        completed = int(state.get("completed", 0))
        current_batch = int(state.get("batch_size", batch_size))
        mmap_array = open_memmap(str(embeddings_path), mode="r+")

    if mmap_array is None:
        first_count = min(current_batch, total)
        first_vectors, current_batch = encode_with_adaptive_batch(
            model,
            texts[:first_count],
            batch_size=current_batch,
            max_length=max_length,
        )
        mmap_array = open_memmap(
            str(embeddings_path),
            mode="w+",
            dtype=np.float32,
            shape=(total, first_vectors.shape[1]),
        )
        mmap_array[:first_count] = first_vectors
        completed = first_count
        save_state(
            state_path,
            completed=completed,
            total=total,
            embedding_dim=first_vectors.shape[1],
            batch_size=current_batch,
            max_length=max_length,
            model_name=model_name,
        )

    while completed < total:
        end = min(completed + current_batch, total)
        vectors, current_batch = encode_with_adaptive_batch(
            model,
            texts[completed:end],
            batch_size=current_batch,
            max_length=max_length,
        )
        chunk_size = vectors.shape[0]
        mmap_array[completed : completed + chunk_size] = vectors
        completed += chunk_size
        if completed % max(current_batch * 8, 512) == 0 or completed == total:
            mmap_array.flush()
            save_state(
                state_path,
                completed=completed,
                total=total,
                embedding_dim=mmap_array.shape[1],
                batch_size=current_batch,
                max_length=max_length,
                model_name=model_name,
            )

    mmap_array.flush()
    if state_path.exists():
        state_path.unlink()
    return np.load(embeddings_path, mmap_mode="r")


def build_faiss_index(normalized_vectors: np.ndarray) -> faiss.IndexFlatIP:
    embedding_dim = normalized_vectors.shape[1]
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(normalized_vectors)
    return index


def run_retrieval_validation(
    *,
    index: faiss.IndexFlatIP,
    model: Any,
    texts: list[str],
    metadata: list[dict[str, Any]],
    query: str,
    batch_size: int,
    max_length: int,
    top_k: int = 5,
) -> None:
    query_vectors, _ = encode_with_adaptive_batch(
        model,
        [query],
        batch_size=max(1, min(batch_size, 8)),
        max_length=max_length,
    )
    faiss.normalize_L2(query_vectors)

    scores, indices = index.search(query_vectors, top_k)
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
        prompt = texts[idx]
        category = metadata[idx].get("category", "unknown")
        print(f"{rank}. score={score:.4f} category={category}")
        print(f"   {prompt}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build planner semantic retrieval index.")
    parser.add_argument("--prompts-path", type=Path, default=DEFAULT_PROMPTS_PATH)
    parser.add_argument("--metadata-path", type=Path, default=DEFAULT_METADATA_PATH)
    parser.add_argument("--embeddings-path", type=Path, default=DEFAULT_EMBEDDINGS_PATH)
    parser.add_argument("--index-path", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--category-index-path", type=Path, default=DEFAULT_CATEGORY_INDEX_PATH)
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--query", default="ignore previous instructions")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Loading dataset...")
    texts, metadata = load_template_texts(args.prompts_path, args.metadata_path)

    use_gpu = is_cuda_available()
    device_name = "GPU" if use_gpu else "CPU"
    model, backend_name = load_embedding_model(MODEL_NAME, use_gpu=use_gpu)
    print(f"Embedding backend: {backend_name}")

    print(f"Generating embeddings on {device_name}...")
    embeddings = generate_embeddings(
        model,
        texts,
        args.embeddings_path,
        model_name=MODEL_NAME,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    print("Saving embedding cache...")

    print("Normalizing vectors...")
    normalized = np.asarray(embeddings, dtype=np.float32).copy()
    faiss.normalize_L2(normalized)

    print("Building FAISS index...")
    index = build_faiss_index(normalized)

    print("Saving index...")
    args.index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(args.index_path))

    print("Generating category index...")
    category_lookup = build_category_lookup(metadata)
    save_json(args.category_index_path, category_lookup)

    print("Writing config file...")
    config = build_index_config(
        embedding_dim=normalized.shape[1],
        dataset_size=len(texts),
        model_name=MODEL_NAME,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    save_json(args.config_path, config)

    print("Running retrieval validation...")
    run_retrieval_validation(
        index=index,
        model=model,
        texts=texts,
        metadata=metadata,
        query=args.query,
        batch_size=args.batch_size,
        max_length=args.max_length,
        top_k=args.top_k,
    )
    print("Vector index ready for planner retrieval")


if __name__ == "__main__":
    main()
