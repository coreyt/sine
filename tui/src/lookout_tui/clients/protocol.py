"""LLM client protocol — provider-agnostic interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client implementations."""

    async def __aenter__(self) -> LLMClient: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse: ...
