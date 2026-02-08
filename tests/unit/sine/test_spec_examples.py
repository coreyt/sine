from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sine.runner import run_sine
from sine.specs import load_rule_specs

# Load all specs once
SPECS_DIR = Path("docs/specs/rule-specs/examples")
SPECS = load_rule_specs(SPECS_DIR)


@pytest.mark.parametrize("spec_file", SPECS, ids=lambda s: s.rule.id)
def test_spec_examples(spec_file):
    """Verify that the examples in the spec behave as expected."""
    rule = spec_file.rule
    is_discovery = rule.check.type == "pattern_discovery"
    
    # Test Bad Examples (should trigger violation for enforcement)
    # Discovery rules usually don't have bad examples, or if they do, 
    # it implies "don't match this", but let's focus on enforcement for bad examples.
    if not is_discovery:
        for i, example in enumerate(rule.examples.bad):
            if example.language != "python":
                continue
                
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / f"bad_{i}.py"
                target_path.write_text(example.code, encoding="utf-8")
                
                findings, _, _, _, _ = run_sine(
                    specs=[spec_file],
                    targets=[target_path],
                )
                
                assert len(findings) > 0, (
                    f"[{rule.id}] Expected violation for bad example #{i+1}, but found none.\n"
                    f"Code:\n{example.code}"
                )

    # Test Good Examples
    # For Enforcement: Should NOT trigger violation.
    # For Discovery: Should trigger pattern instance.
    for i, example in enumerate(rule.examples.good):
        if example.language != "python":
            continue
            
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir) / f"good_{i}.py"
            target_path.write_text(example.code, encoding="utf-8")
            
            findings, _, instances, _, _ = run_sine(
                specs=[spec_file],
                targets=[target_path],
                discovery_only=is_discovery
            )
            
            if is_discovery:
                assert len(instances) > 0, (
                    f"[{rule.id}] Expected pattern discovery for good example #{i+1}, but found none.\n"
                    f"Code:\n{example.code}"
                )
            else:
                assert len(findings) == 0, (
                    f"[{rule.id}] Expected NO violation for good example #{i+1}, but found {len(findings)}.\n"
                    f"Code:\n{example.code}\n"
                    f"Findings: {[f.message for f in findings]}"
                )
