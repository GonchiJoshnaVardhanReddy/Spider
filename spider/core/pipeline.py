"""SPIDER runtime pipeline defaults."""

from __future__ import annotations

from spider.core.ollama_models import DEFAULT_RUNTIME_MODELS, SpiderRuntimeModels


class SpiderAgentPipeline:
    """Pipeline metadata holder for role-model defaults."""

    def __init__(self, runtime_models: SpiderRuntimeModels = DEFAULT_RUNTIME_MODELS) -> None:
        self.runtime_models = runtime_models

    @property
    def default_model(self) -> str:
        """Return the model shown as active by default in the UI."""
        return self.runtime_models.default_model

    def placeholder_response(self, user_prompt: str) -> str:
        """Return the current placeholder response with pipeline model details."""
        models = self.runtime_models
        return (
            f"Processing: {user_prompt}\n\n"
            "Pipeline runtime defaults:\n"
            f"- Planner: {models.planner.name} ({models.planner.base_model})\n"
            f"- Mutator: {models.mutator.name} ({models.mutator.base_model})\n"
            f"- Evaluator: {models.evaluator.name} ({models.evaluator.base_model})\n\n"
            "Connect your model backend in spider/core for real execution."
        )
