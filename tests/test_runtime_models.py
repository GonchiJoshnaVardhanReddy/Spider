"""Runtime model configuration tests."""

from spider.core import DEFAULT_RUNTIME_MODELS, SpiderAgentPipeline


def test_default_runtime_model_configs() -> None:
    """Each role should use the required custom Ollama runtime model."""
    runtime = DEFAULT_RUNTIME_MODELS

    assert runtime.planner.name == "spider-planner"
    assert runtime.planner.temperature == 0.6
    assert runtime.planner.top_p == 0.9
    assert runtime.planner.num_ctx == 8192

    assert runtime.mutator.name == "spider-mutator"
    assert runtime.mutator.temperature == 0.85
    assert runtime.mutator.top_p == 0.9
    assert runtime.mutator.num_ctx == 8192

    assert runtime.evaluator.name == "spider-evaluator"
    assert runtime.evaluator.temperature == 0.1
    assert runtime.evaluator.top_p == 0.1
    assert runtime.evaluator.num_ctx == 8192


def test_pipeline_uses_role_models_by_default() -> None:
    """The pipeline should boot with planner/mutator/evaluator defaults."""
    pipeline = SpiderAgentPipeline()

    assert pipeline.default_model == "spider-planner"
    assert pipeline.runtime_models.planner.name == "spider-planner"
    assert pipeline.runtime_models.mutator.name == "spider-mutator"
    assert pipeline.runtime_models.evaluator.name == "spider-evaluator"
