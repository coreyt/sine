"""Tests for pattern discovery functionality in Second Shift."""

from __future__ import annotations

from sine.models import (
    ForbiddenCheck,
    PatternDiscoveryCheck,
    PatternInstance,
    RuleCheck,
    RuleExamples,
    RuleReporting,
    RuleSpec,
    RuleSpecFile,
)
from sine.semgrep import compile_semgrep_config, parse_semgrep_output


def test_pattern_discovery_check_type():
    """Test that pattern_discovery is a valid check type."""
    check = PatternDiscoveryCheck(
        type="pattern_discovery",
        patterns=[
            "class $MODEL(BaseModel):\n  ...",
            "@dataclass(frozen=True)\nclass $CLASS:\n  ...",
        ],
    )
    assert check.type == "pattern_discovery"
    assert check.patterns is not None
    assert len(check.patterns) == 2


def test_compile_pattern_discovery():
    """Test compilation of pattern_discovery rules to Semgrep."""
    spec = RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="PATTERN-TEST-001",
            title="Test Pattern",
            description="Test pattern discovery",
            rationale="Testing",
            tier=1,
            category="test",
            severity="info",
            languages=["python"],
            check=PatternDiscoveryCheck(
                type="pattern_discovery",
                patterns=["class $MODEL(BaseModel):\n  ..."],
            ),
            reporting=RuleReporting(
                default_message="Pattern found",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )

    config = compile_semgrep_config([spec])

    assert "rules" in config
    assert len(config["rules"]) == 1

    rule = config["rules"][0]
    assert rule["id"] == "pattern-test-001-impl"
    assert rule["severity"] == "INFO"
    assert "patterns" in rule
    assert len(rule["patterns"]) == 1
    assert "pattern-either" in rule["patterns"][0]


def test_parse_semgrep_output_pattern_discovery():
    """Test parsing Semgrep output distinguishes findings from pattern instances."""
    spec_enforcement = RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="ARCH-001",
            title="Enforcement Rule",
            description="Test enforcement",
            rationale="Testing",
            tier=1,
            category="test",
            severity="error",
            languages=["python"],
            check=ForbiddenCheck(type="forbidden", pattern="eval(...)"),
            reporting=RuleReporting(
                default_message="Forbidden pattern",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )

    spec_discovery = RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="PATTERN-001",
            title="Discovery Rule",
            description="Test discovery",
            rationale="Testing",
            tier=1,
            category="test",
            severity="info",
            languages=["python"],
            check=PatternDiscoveryCheck(
                type="pattern_discovery",
                patterns=["class $MODEL(BaseModel):\n  ..."],
            ),
            reporting=RuleReporting(
                default_message="Pattern found",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )

    semgrep_output = """
    {
        "results": [
            {
                "check_id": "arch-001-impl",
                "path": "test.py",
                "start": {"line": 10},
                "extra": {
                    "message": "Forbidden pattern",
                    "lines": "eval(x)"
                }
            },
            {
                "check_id": "pattern-001-impl",
                "path": "test.py",
                "start": {"line": 20},
                "extra": {
                    "message": "Pattern found",
                    "lines": "class User(BaseModel):"
                }
            }
        ]
    }
    """

    spec_index = {
        "ARCH-001": spec_enforcement,
        "PATTERN-001": spec_discovery,
    }

    findings, pattern_instances, errors = parse_semgrep_output(semgrep_output, spec_index)

    # Should have 1 finding (enforcement) and 1 pattern instance (discovery)
    assert len(findings) == 1
    assert len(pattern_instances) == 1

    # Verify finding
    assert findings[0].guideline_id == "ARCH-001"
    assert findings[0].severity == "error"
    assert findings[0].line == 10

    # Verify pattern instance
    assert pattern_instances[0].pattern_id == "PATTERN-001"
    assert pattern_instances[0].category == "test"
    assert pattern_instances[0].line == 20
    assert pattern_instances[0].confidence == "high"


def test_pattern_instance_immutable():
    """Test that PatternInstance is immutable (frozen dataclass)."""
    instance = PatternInstance(
        pattern_id="TEST-001",
        title="Test",
        category="test",
        file="test.py",
        line=1,
        snippet="code",
        confidence="high",
    )

    # Should not be able to modify
    try:
        instance.line = 2  # type: ignore
        assert False, "Should not be able to modify frozen dataclass"
    except (AttributeError, TypeError):
        pass  # Expected


def test_compile_pattern_discovery_with_metavariable_regex():
    """Test compilation of pattern_discovery rules with metavariable_regex."""
    from sine.models import MetavariableRegex

    spec = RuleSpecFile(
        schema_version=1,
        rule=RuleSpec(
            id="PATTERN-TEST-REGEX",
            title="Regex Pattern",
            description="Test regex",
            rationale="Testing",
            tier=1,
            category="test",
            severity="info",
            languages=["python"],
            check=PatternDiscoveryCheck(
                type="pattern_discovery",
                patterns=["def $FUNC(...): ..."],
                metavariable_regex=[
                    MetavariableRegex(metavariable="$FUNC", regex="^create_.*")
                ],
            ),
            reporting=RuleReporting(
                default_message="Pattern found",
                confidence="high",
                documentation_url=None,
            ),
            examples=RuleExamples(good=[], bad=[]),
            references=[],
        ),
    )

    config = compile_semgrep_config([spec])
    rule = config["rules"][0]
    
    assert len(rule["patterns"]) == 2
    assert "pattern-either" in rule["patterns"][0]
    assert "metavariable-regex" in rule["patterns"][1]
    
    mr = rule["patterns"][1]["metavariable-regex"]
    assert mr["metavariable"] == "$FUNC"
    assert mr["regex"] == "^create_.*"
