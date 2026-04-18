"""Unit tests for the vector index builder helpers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts.vector_index_builder.build_vector_index import (
    build_category_lookup,
    build_index_config,
    extract_dense_matrix,
    load_template_texts,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_template_texts_preserves_alignment(tmp_path: Path) -> None:
    prompts_path = tmp_path / "prompts.json"
    metadata_path = tmp_path / "metadata.json"
    _write_json(prompts_path, [{"prompt": "a"}, {"prompt": "b"}])
    _write_json(
        metadata_path,
        [
            {"id": 0, "prompt": "a", "category": "override"},
            {"id": 1, "prompt": "b", "category": "roleplay"},
        ],
    )

    texts, metadata = load_template_texts(prompts_path, metadata_path)

    assert texts == ["a", "b"]
    assert metadata[1]["category"] == "roleplay"


def test_load_template_texts_rejects_prompt_mismatch(tmp_path: Path) -> None:
    prompts_path = tmp_path / "prompts.json"
    metadata_path = tmp_path / "metadata.json"
    _write_json(prompts_path, [{"prompt": "a"}, {"prompt": "b"}])
    _write_json(
        metadata_path,
        [
            {"id": 0, "prompt": "a", "category": "override"},
            {"id": 1, "prompt": "different", "category": "roleplay"},
        ],
    )

    with pytest.raises(ValueError, match="alignment"):
        load_template_texts(prompts_path, metadata_path)


def test_extract_dense_matrix_from_flagembedding_payload() -> None:
    encoded = {"dense_vecs": [[0.1, 0.2], [0.3, 0.4]]}

    matrix = extract_dense_matrix(encoded)

    assert matrix.shape == (2, 2)
    assert matrix.dtype == np.float32


def test_build_category_lookup_groups_ids_in_order() -> None:
    metadata = [
        {"id": 0, "category": "override"},
        {"id": 1, "category": "system_leak"},
        {"id": 2, "category": "override"},
    ]

    lookup = build_category_lookup(metadata)

    assert lookup["override"] == [0, 2]
    assert lookup["system_leak"] == [1]


def test_build_index_config_has_required_contract() -> None:
    config = build_index_config(
        embedding_dim=1024,
        dataset_size=80_000,
        model_name="bge-m3",
        batch_size=64,
        max_length=512,
    )

    assert config["model"] == "bge-m3"
    assert config["embedding_dim"] == 1024
    assert config["normalized"] is True
    assert config["metric"] == "cosine"
    assert config["dataset_size"] == 80_000
