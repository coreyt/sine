"""Batch orchestrator — main entry point for CLI and TUI."""

from __future__ import annotations

import json
from pathlib import Path

from lookout.batch.grid import build_registry_grid
from lookout.batch.models import (
    BatchJob,
    BatchRequest,
    BatchResult,
    BatchStatus,
    CellStatus,
    RegistryCell,
)
from lookout.batch.prompts import build_batch_prompts
from lookout.batch.providers.base import BatchProvider
from lookout.config import LookoutConfig
from lookout.models import PatternSpecFile
from lookout.prompts import PromptTemplateLoader
from lookout.registry import list_patterns


class BatchOrchestrator:
    """Coordinates batch generation of checks for the pattern registry."""

    def __init__(self, config: LookoutConfig, patterns_dir: Path) -> None:
        self._config = config
        self._patterns_dir = patterns_dir
        self._loader = PromptTemplateLoader()
        self._provider: BatchProvider | None = None
        self._patterns_cache: list[PatternSpecFile] | None = None

    def _create_provider(self) -> BatchProvider:
        provider_name = self._config.batch_provider or self._config.llm_provider
        if provider_name == "anthropic":
            from lookout.batch.providers.anthropic import AnthropicBatchProvider

            return AnthropicBatchProvider()
        elif provider_name == "gemini":
            from lookout.batch.providers.gemini import GeminiBatchProvider

            return GeminiBatchProvider()
        else:
            raise ValueError(f"Unsupported batch provider: {provider_name}")

    def _get_provider(self) -> BatchProvider:
        if self._provider is None:
            self._provider = self._create_provider()
        return self._provider

    def _load_patterns(self) -> list[PatternSpecFile]:
        if self._patterns_cache is None:
            self._patterns_cache = list_patterns(self._patterns_dir)
        return self._patterns_cache

    def invalidate_cache(self) -> None:
        """Clear cached patterns (call after modifying registry on disk)."""
        self._patterns_cache = None

    def build_grid(
        self,
        languages: list[str],
        frameworks: dict[str, list[str]],
    ) -> list[RegistryCell]:
        """Build the grid from registry patterns."""
        return build_registry_grid(self._load_patterns(), languages, frameworks)

    async def submit_batch(self, cells: list[RegistryCell]) -> BatchJob:
        """Build prompts, submit to provider, return job."""
        patterns = self._load_patterns()
        spec_map = {s.pattern.id: s for s in patterns}

        model = self._config.batch_model or self._config.llm_model or "claude-sonnet-4-20250514"
        provider_name = self._config.batch_provider or self._config.llm_provider

        # Cache top-level summaries per pattern to avoid recomputation
        summary_cache: dict[str, tuple[str, str]] = {}
        requests: list[BatchRequest] = []
        for cell in cells:
            spec = spec_map.get(cell.pattern_id)
            if spec is None:
                continue
            cache_key = f"{cell.pattern_id}__{cell.framework or 'generic'}"
            if cache_key not in summary_cache:
                summary_cache[cache_key] = build_batch_prompts(cell, spec, self._loader)
            system, user = summary_cache[cache_key]
            requests.append(
                BatchRequest(
                    custom_id=cell.cell_id,
                    cell=cell,
                    system_prompt=system,
                    user_prompt=user,
                )
            )

        provider = self._get_provider()
        job_id = await provider.submit(requests, model)

        return BatchJob(
            job_id=job_id,
            provider=provider_name,
            model=model,
            status=BatchStatus.SUBMITTED,
            requests=requests,
        )

    async def poll_batch(self, job: BatchJob) -> BatchJob:
        """Update job status from provider."""
        provider = self._get_provider()
        status, counts = await provider.poll(job.job_id)
        job.status = status
        job.request_counts = counts
        return job

    async def retrieve_results(self, job: BatchJob) -> BatchJob:
        """Fetch results, build BatchResult objects."""
        provider = self._get_provider()
        raw_results = await provider.retrieve(job.job_id)

        # Map custom_ids to cells from requests
        cell_map = {r.custom_id: r.cell for r in job.requests}

        results: list[BatchResult] = []
        for r in raw_results:
            custom_id = r["custom_id"]
            cell = cell_map.get(
                custom_id,
                RegistryCell("unknown", "unknown", None, CellStatus.MISSING),
            )
            results.append(
                BatchResult(
                    custom_id=custom_id,
                    cell=cell,
                    success=r["success"],
                    output=r["output"],
                    error=r.get("error"),
                    token_usage=r.get("token_usage", {}),
                )
            )

        job.results = results
        return job

    async def cancel_batch(self, job: BatchJob) -> None:
        """Cancel a batch job."""
        provider = self._get_provider()
        await provider.cancel(job.job_id)

    def save_job(self, job: BatchJob, jobs_dir: Path) -> None:
        """Persist job state to JSON for resumption."""
        jobs_dir.mkdir(parents=True, exist_ok=True)
        path = jobs_dir / f"{job.job_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(job.to_dict(), f, indent=2)

    def load_job(self, path: Path) -> BatchJob:
        """Resume a saved job."""
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return BatchJob.from_dict(data)
