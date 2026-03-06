"""Tests for batch data models."""

from __future__ import annotations

from datetime import datetime, timezone

from lookout.batch.models import (
    BatchJob,
    BatchRequest,
    BatchResult,
    BatchStatus,
    CellStatus,
    RegistryCell,
)


class TestCellStatus:
    def test_values(self) -> None:
        assert CellStatus.PRESENT == "present"
        assert CellStatus.POSSIBLY_STALE == "stale_soft"
        assert CellStatus.LIKELY_STALE == "stale_hard"
        assert CellStatus.MISSING == "missing"


class TestRegistryCell:
    def test_frozen(self) -> None:
        cell = RegistryCell(
            pattern_id="DI-001",
            language="python",
            framework=None,
            status=CellStatus.MISSING,
        )
        assert cell.pattern_id == "DI-001"
        assert cell.language == "python"
        assert cell.framework is None
        assert cell.status == CellStatus.MISSING

    def test_framework_cell(self) -> None:
        cell = RegistryCell(
            pattern_id="DI-001",
            language="python",
            framework="django",
            status=CellStatus.PRESENT,
        )
        assert cell.framework == "django"

    def test_cell_id_generic(self) -> None:
        cell = RegistryCell(
            pattern_id="DI-001",
            language="python",
            framework=None,
            status=CellStatus.MISSING,
        )
        assert cell.cell_id == "DI-001__python__generic"

    def test_cell_id_framework(self) -> None:
        cell = RegistryCell(
            pattern_id="DI-001",
            language="python",
            framework="django",
            status=CellStatus.MISSING,
        )
        assert cell.cell_id == "DI-001__python__django"


class TestBatchRequest:
    def test_creation(self) -> None:
        cell = RegistryCell("DI-001", "python", None, CellStatus.MISSING)
        req = BatchRequest(
            custom_id="DI-001__python__generic",
            cell=cell,
            system_prompt="You are...",
            user_prompt="Generate...",
        )
        assert req.custom_id == "DI-001__python__generic"
        assert req.system_prompt == "You are..."


class TestBatchResult:
    def test_creation(self) -> None:
        cell = RegistryCell("DI-001", "python", None, CellStatus.MISSING)
        result = BatchResult(
            custom_id="DI-001__python__generic",
            cell=cell,
            success=True,
            output="```yaml\nrules: ...\n```",
            error=None,
            token_usage={"input_tokens": 100, "output_tokens": 200},
        )
        assert result.success is True
        assert result.error is None

    def test_failed_result(self) -> None:
        cell = RegistryCell("DI-001", "python", None, CellStatus.MISSING)
        result = BatchResult(
            custom_id="DI-001__python__generic",
            cell=cell,
            success=False,
            output="",
            error="Rate limit exceeded",
            token_usage={},
        )
        assert result.success is False
        assert result.error == "Rate limit exceeded"


class TestBatchJob:
    def test_creation(self) -> None:
        now = datetime.now(tz=timezone.utc)
        job = BatchJob(
            job_id="msgbatch_01Hkc",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            status=BatchStatus.PENDING,
            requests=[],
            results=[],
            created_at=now,
            completed_at=None,
            request_counts={},
        )
        assert job.job_id == "msgbatch_01Hkc"
        assert job.status == BatchStatus.PENDING
        assert job.completed_at is None

    def test_status_values(self) -> None:
        assert BatchStatus.PENDING == "pending"
        assert BatchStatus.SUBMITTED == "submitted"
        assert BatchStatus.PROCESSING == "processing"
        assert BatchStatus.COMPLETED == "completed"
        assert BatchStatus.FAILED == "failed"
        assert BatchStatus.CANCELLED == "cancelled"

    def test_to_dict_and_from_dict(self) -> None:
        now = datetime.now(tz=timezone.utc)
        cell = RegistryCell("DI-001", "python", None, CellStatus.MISSING)
        req = BatchRequest("DI-001__python__generic", cell, "sys", "usr")
        job = BatchJob(
            job_id="batch123",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            status=BatchStatus.SUBMITTED,
            requests=[req],
            results=[],
            created_at=now,
            completed_at=None,
            request_counts={"processing": 1},
        )
        data = job.to_dict()
        assert data["job_id"] == "batch123"
        assert data["status"] == "submitted"
        assert len(data["requests"]) == 1
        assert data["requests"][0]["custom_id"] == "DI-001__python__generic"

        restored = BatchJob.from_dict(data)
        assert restored.job_id == job.job_id
        assert restored.status == BatchStatus.SUBMITTED
        assert restored.requests[0].cell.pattern_id == "DI-001"
        assert restored.created_at == now
