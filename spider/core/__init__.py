"""SPIDER core functionality."""

from spider.core.ollama_models import DEFAULT_RUNTIME_MODELS
from spider.core.pipeline import SpiderAgentPipeline

__all__ = ["DEFAULT_RUNTIME_MODELS", "SpiderAgentPipeline"]
