"""SPIDER executor connectors for target LLM payload transmission."""

from spider.executor.executor import Executor, ExecutorConfig
from spider.executor.openai_adapter import OpenAIAdapter, OpenAIAdapterConfig
from spider.executor.rest_adapter import RESTAdapter, RESTAdapterConfig
from spider.executor.session import ExecutorSession

__all__ = [
    "Executor",
    "ExecutorConfig",
    "ExecutorSession",
    "OpenAIAdapter",
    "OpenAIAdapterConfig",
    "RESTAdapter",
    "RESTAdapterConfig",
]
