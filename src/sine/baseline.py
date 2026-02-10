from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from sine.models import Finding


@dataclass(frozen=True)
class BaselineEntry:
    guideline_id: str
    file: str
    line: int
    hash: str


@dataclass(frozen=True)
class Baseline:
    entries: set[BaselineEntry]

    @classmethod
    def from_findings(cls, findings: Iterable[Finding]) -> Baseline:
        return cls(entries={_entry_from_finding(finding) for finding in findings})

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "violations": [
                {
                    "guideline_id": entry.guideline_id,
                    "file": entry.file,
                    "line": entry.line,
                    "hash": entry.hash,
                }
                for entry in sorted(
                    self.entries, key=lambda item: (item.guideline_id, item.file, item.line)
                )
            ],
        }


BASELINE_PATH = Path(".sine-baseline.json")


def load_baseline(path: Path = BASELINE_PATH) -> Baseline | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = {
        BaselineEntry(
            guideline_id=item["guideline_id"],
            file=item["file"],
            line=item["line"],
            hash=item["hash"],
        )
        for item in data.get("violations", [])
    }
    return Baseline(entries=entries)


def write_baseline(baseline: Baseline, path: Path = BASELINE_PATH) -> None:
    path.write_text(json.dumps(baseline.to_dict(), indent=2) + "\n", encoding="utf-8")


def filter_findings(findings: list[Finding], baseline: Baseline | None) -> list[Finding]:
    if baseline is None:
        return findings
    baseline_hashes = {entry.hash for entry in baseline.entries}
    return [
        finding for finding in findings if _entry_from_finding(finding).hash not in baseline_hashes
    ]


def _entry_from_finding(finding: Finding) -> BaselineEntry:
    fingerprint = f"{finding.guideline_id}|{finding.file}|{finding.line}|{finding.message}"
    hash_value = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:8]
    return BaselineEntry(
        guideline_id=finding.guideline_id,
        file=finding.file,
        line=finding.line,
        hash=hash_value,
    )
