"""BatchProvider protocol for batch LLM APIs."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from lookout.batch.models import BatchRequest, BatchStatus


@runtime_checkable
class BatchProvider(Protocol):
    """Protocol for batch LLM providers."""

    async def submit(self, requests: list[BatchRequest], model: str) -> str:
        """Submit batch, return provider job ID."""
        ...

    async def poll(self, job_id: str) -> tuple[BatchStatus, dict[str, int]]:
        """Check status. Returns (status, request_counts)."""
        ...

    async def retrieve(self, job_id: str) -> list[dict[str, Any]]:
        """Get raw results when complete."""
        ...

    async def cancel(self, job_id: str) -> None:
        """Cancel a batch job."""
        ...
