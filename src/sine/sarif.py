"""SARIF (Static Analysis Results Interchange Format) support for Sine."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sine.models import Finding


def format_findings_sarif(findings: list[Finding], version: str = "0.1.0") -> str:
    """Format findings as a SARIF JSON string.

    Args:
        findings: List of violations
        version: Sine version

    Returns:
        SARIF JSON string
    """
    results = []
    rules = {}

    for finding in findings:
        # Register rule if not seen
        if finding.guideline_id not in rules:
            rules[finding.guideline_id] = {
                "id": finding.guideline_id,
                "shortDescription": {"text": finding.title},
                "properties": {
                    "category": "architecture",  # We should probably add this to Finding
                    "tier": finding.tier,
                },
            }

        # Create result
        results.append(
            {
                "ruleId": finding.guideline_id,
                "level": _map_severity_to_sarif(finding.severity),
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file},
                            "region": {
                                "startLine": finding.line,
                                "snippet": {"text": finding.snippet},
                            },
                        }
                    }
                ],
            }
        )

    sarif = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Sine",
                        "version": version,
                        "informationUri": "https://github.com/coreyt/sine",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }

    return json.dumps(sarif, indent=2)


def _map_severity_to_sarif(severity: str) -> str:
    mapping = {
        "error": "error",
        "warning": "warning",
        "info": "note",
    }
    return mapping.get(severity.lower(), "warning")
