"""Google Gemini batch API provider."""

from __future__ import annotations

from typing import Any

from lookout.batch.models import BatchRequest, BatchStatus

_STATE_MAP = {
    "JOB_STATE_SUCCEEDED": BatchStatus.COMPLETED,
    "JOB_STATE_FAILED": BatchStatus.FAILED,
    "JOB_STATE_CANCELLED": BatchStatus.CANCELLED,
    "JOB_STATE_RUNNING": BatchStatus.PROCESSING,
    "JOB_STATE_PENDING": BatchStatus.PENDING,
}


class GeminiBatchProvider:
    """Batch provider using Google GenAI Batch API."""

    def __init__(self, client: Any = None) -> None:
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai  # type: ignore[import-untyped]

            self._client = genai.Client()
        return self._client

    async def submit(self, requests: list[BatchRequest], model: str) -> str:
        """Submit inline batch requests to Gemini."""
        client = self._get_client()

        inline_requests = []
        for req in requests:
            inline_requests.append(
                {
                    "key": req.custom_id,
                    "request": {
                        "model": model,
                        "contents": [{"role": "user", "parts": [{"text": req.user_prompt}]}],
                        "system_instruction": {"parts": [{"text": req.system_prompt}]},
                    },
                }
            )

        batch = client.batches.create(
            model=model,
            src={"inlined_requests": inline_requests},
            config={"display_name": f"lookout-batch-{model}"},
        )
        return str(batch.name)

    async def poll(self, job_id: str) -> tuple[BatchStatus, dict[str, int]]:
        """Check batch status."""
        client = self._get_client()
        batch = client.batches.get(name=job_id)

        state_str = str(batch.state)
        status = _STATE_MAP.get(state_str, BatchStatus.PROCESSING)

        return status, {}

    async def retrieve(self, job_id: str) -> list[dict[str, Any]]:
        """Fetch results from completed batch."""
        client = self._get_client()
        batch = client.batches.get(name=job_id)

        results: list[dict[str, Any]] = []
        for resp in batch.dest.inlined_responses:
            try:
                text = resp.response.candidates[0].content.parts[0].text
                results.append(
                    {
                        "custom_id": resp.key,
                        "success": True,
                        "output": text,
                        "error": None,
                        "token_usage": {
                            "input_tokens": resp.response.usage_metadata.prompt_token_count,
                            "output_tokens": resp.response.usage_metadata.candidates_token_count,
                        },
                    }
                )
            except (AttributeError, IndexError) as e:
                results.append(
                    {
                        "custom_id": resp.key,
                        "success": False,
                        "output": "",
                        "error": str(e),
                        "token_usage": {},
                    }
                )

        return results

    async def cancel(self, job_id: str) -> None:
        """Cancel a batch job."""
        client = self._get_client()
        client.batches.cancel(name=job_id)
