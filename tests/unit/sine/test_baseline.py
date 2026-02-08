from __future__ import annotations

from sine.baseline import Baseline, filter_findings
from sine.models import Finding


def test_filter_findings_removes_known() -> None:
    finding = Finding(
        guideline_id="ARCH-001",
        title="HTTP calls require resilience wrappers",
        severity="error",
        file="src/app.py",
        line=10,
        message="HTTP call outside resilience wrapper (ARCH-001)",
        snippet="requests.get(url)",
        engine="semgrep",
        tier=1,
    )
    baseline = Baseline.from_findings([finding])
    remaining = filter_findings([finding], baseline)

    assert remaining == []

