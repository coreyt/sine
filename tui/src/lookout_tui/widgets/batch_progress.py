"""BatchProgress widget — shows batch job progress."""

from __future__ import annotations

from lookout.batch.models import BatchJob


class BatchProgress:
    """In-memory progress model for a batch job.

    Used by BatchGridScreen to track and display job progress.
    """

    def __init__(self) -> None:
        self._job: BatchJob | None = None

    def show_job(self, job: BatchJob) -> None:
        """Update with latest job state."""
        self._job = job

    @property
    def job(self) -> BatchJob | None:
        return self._job

    def format_status(self) -> str:
        """Format job status as a display string."""
        if self._job is None:
            return "No active batch job"

        parts = [
            f"Batch {self._job.job_id} ({self._job.provider}/{self._job.model})",
            f"Status: {self._job.status.value}",
        ]

        if self._job.request_counts:
            count_parts = [
                f"{v} {k}" for k, v in self._job.request_counts.items() if v
            ]
            if count_parts:
                parts.append(f"Progress: {', '.join(count_parts)}")

        parts.append(f"Total requests: {len(self._job.requests)}")

        if self._job.results:
            succeeded = sum(1 for r in self._job.results if r.success)
            failed = sum(1 for r in self._job.results if not r.success)
            parts.append(f"Results: {succeeded} succeeded, {failed} failed")

        return "\n".join(parts)
