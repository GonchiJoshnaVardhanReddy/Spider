"""Default Ollama runtime model wrappers for SPIDER roles."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaRoleModel:
    """A single role-specific Ollama model configuration."""

    name: str
    base_model: str
    purpose: str
    temperature: float
    top_p: float
    num_ctx: int


@dataclass(frozen=True)
class SpiderRuntimeModels:
    """Planner / mutator / evaluator role model bundle."""

    planner: OllamaRoleModel
    mutator: OllamaRoleModel
    evaluator: OllamaRoleModel

    @property
    def default_model(self) -> str:
        """Return the default UI model name."""
        return self.planner.name


PLANNER_MODEL = OllamaRoleModel(
    name="spider-planner",
    base_model="deepseek-r1:7b",
    purpose="multi-turn attack planning and strategy selection",
    temperature=0.6,
    top_p=0.9,
    num_ctx=8192,
)

MUTATOR_MODEL = OllamaRoleModel(
    name="spider-mutator",
    base_model="qwen2.5-coder:7b-instruct",
    purpose="payload mutation, encoding, and jailbreak transformation",
    temperature=0.85,
    top_p=0.9,
    num_ctx=8192,
)

EVALUATOR_MODEL = OllamaRoleModel(
    name="spider-evaluator",
    base_model="llama3.1:8b",
    purpose=(
        "strict classification of jailbreak success, refusal bypass, "
        "system prompt leakage, and tool misuse detection"
    ),
    temperature=0.1,
    top_p=0.1,
    num_ctx=8192,
)

DEFAULT_RUNTIME_MODELS = SpiderRuntimeModels(
    planner=PLANNER_MODEL,
    mutator=MUTATOR_MODEL,
    evaluator=EVALUATOR_MODEL,
)
