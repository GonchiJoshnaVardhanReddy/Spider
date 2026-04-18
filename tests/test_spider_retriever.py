"""Retriever fallback behavior tests."""

from __future__ import annotations

import spider_retriever


def test_retrieve_payloads_falls_back_to_unfiltered_when_category_empty(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        spider_retriever,
        "_load_template_metadata",
        lambda: (
            {"prompt": "p1", "category": "roleplay"},
            {"prompt": "p2", "category": "override"},
        ),
    )
    monkeypatch.setattr(spider_retriever, "_load_category_index_safe", lambda: ({}, True))

    def fake_search(*, category=None, **_kwargs):
        if category is None:
            return [{"prompt": "unfiltered-choice", "category": "general"}]
        return []

    monkeypatch.setattr(spider_retriever, "search", fake_search)
    monkeypatch.setattr(spider_retriever, "_load_random_mutation_payload", lambda **_kwargs: None)
    monkeypatch.setattr(spider_retriever, "load_random_template_payload", lambda **_kwargs: None)

    payloads, diagnostics = spider_retriever.retrieve_payloads_with_diagnostics(
        query="q",
        category="context_poisoning",
        k=25,
    )

    assert payloads
    assert payloads[0]["prompt"] == "unfiltered-choice"
    assert diagnostics["fallback"] == "unfiltered"


def test_retrieve_payloads_uses_taxonomy_then_mutation_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        spider_retriever,
        "_load_template_metadata",
        lambda: ({"prompt": "p1", "category": "roleplay"},),
    )
    monkeypatch.setattr(spider_retriever, "_load_category_index_safe", lambda: ({}, True))
    monkeypatch.setattr(spider_retriever, "search", lambda **_kwargs: [])
    monkeypatch.setattr(
        spider_retriever,
        "_load_random_mutation_payload",
        lambda **_kwargs: {"prompt": "mutation-backup", "category": "general"},
    )
    monkeypatch.setattr(spider_retriever, "load_random_template_payload", lambda **_kwargs: None)

    payloads, diagnostics = spider_retriever.retrieve_payloads_with_diagnostics(
        query="q",
        category="nonexistent",
        k=25,
    )

    assert payloads[0]["prompt"] == "mutation-backup"
    assert diagnostics["fallback"] == "mutation_reservoir"


def test_retrieve_payloads_never_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(spider_retriever, "_load_template_metadata", lambda: tuple())
    monkeypatch.setattr(spider_retriever, "_load_category_index_safe", lambda: ({}, False))
    monkeypatch.setattr(spider_retriever, "search", lambda **_kwargs: [])
    monkeypatch.setattr(spider_retriever, "_load_random_mutation_payload", lambda **_kwargs: None)
    monkeypatch.setattr(spider_retriever, "load_random_template_payload", lambda **_kwargs: None)

    payloads, diagnostics = spider_retriever.retrieve_payloads_with_diagnostics(
        query="q",
        category="roleplay",
        k=25,
    )

    assert len(payloads) == 1
    assert "prompt" in payloads[0]
    assert diagnostics["fallback"] == "hardcoded"


def test_retrieve_payloads_disables_category_filter_without_index(monkeypatch) -> None:
    monkeypatch.setattr(
        spider_retriever,
        "_load_template_metadata",
        lambda: ({"prompt": "any", "category": "roleplay"},),
    )
    monkeypatch.setattr(spider_retriever, "_load_category_index_safe", lambda: ({}, False))

    observed_categories: list[str | None] = []

    def fake_search(*, category=None, **_kwargs):
        observed_categories.append(category)
        return [{"prompt": "any", "category": "roleplay"}]

    monkeypatch.setattr(spider_retriever, "search", fake_search)

    payloads, diagnostics = spider_retriever.retrieve_payloads_with_diagnostics(
        query="q",
        category="override",
        k=25,
    )

    assert payloads[0]["prompt"] == "any"
    assert diagnostics["category_filter_enabled"] is False
    assert observed_categories == [None]
