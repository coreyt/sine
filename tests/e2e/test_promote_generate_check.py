"""End-to-end test: research → validate → promote --generate-check.

Exercises the full discovery-to-enforcement pipeline using real filesystem
storage and the CLI, with only the LLM HTTP call mocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import yaml
from click.testing import CliRunner

from sine.cli import cli
from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    ValidatedPattern,
)
from sine.discovery.storage import PatternStorage
from sine.models import ForbiddenCheck, PatternDiscoveryCheck
from sine.promotion import promote_to_spec
from sine.semgrep import compile_semgrep_config


def _sample_discovered() -> DiscoveredPattern:
    """A realistic discovered pattern with good/bad examples."""
    return DiscoveredPattern(
        pattern_id="ARCH-DI-001",
        title="Avoid direct instantiation in service layer",
        category="architecture",
        subcategory="dependency-injection",
        description=(
            "Services should receive dependencies via constructor injection "
            "rather than instantiating them directly."
        ),
        rationale=(
            "Direct instantiation couples services tightly to concrete "
            "implementations and makes unit testing difficult."
        ),
        severity="error",
        confidence="high",
        languages=["python"],
        examples=PatternExamples(
            good=[
                PatternExample(
                    language="python",
                    code=(
                        "class OrderService:\n"
                        "    def __init__(self, repo: OrderRepo):\n"
                        "        self.repo = repo"
                    ),
                ),
            ],
            bad=[
                PatternExample(
                    language="python",
                    code=(
                        "class OrderService:\n"
                        "    def __init__(self):\n"
                        "        self.repo = OrderRepo()"
                    ),
                ),
            ],
        ),
        discovered_by="architecture-agent",
        references=["https://example.com/dependency-injection"],
    )


def _mock_anthropic_post(check_json: str) -> AsyncMock:
    """Build an AsyncMock that returns a canned Anthropic response."""
    return AsyncMock(
        return_value=Mock(
            status_code=200,
            json=lambda: {
                "id": "msg_e2e",
                "content": [{"text": check_json}],
                "usage": {"input_tokens": 800, "output_tokens": 150},
            },
            raise_for_status=lambda: None,
        )
    )


class TestPromoteWithGenerateCheckE2E:
    """Full pipeline e2e: disk storage → CLI validate → CLI promote --generate-check."""

    def test_full_pipeline_raw_to_enforced_rule(self, tmp_path: Path, monkeypatch: object) -> None:
        """Raw pattern on disk → validate CLI → promote --generate-check → YAML with real check."""
        patterns_dir = tmp_path / ".sine-patterns"
        rules_dir = tmp_path / ".sine-rules"

        # ── Step 1: Save a raw pattern to disk ──────────────────────────
        storage = PatternStorage(patterns_dir)
        raw = _sample_discovered()
        storage.save_pattern(raw, "raw")

        # Verify it landed on disk
        loaded = storage.load_pattern("ARCH-DI-001", stage="raw", model_class=DiscoveredPattern)
        assert loaded is not None
        assert loaded.pattern_id == "ARCH-DI-001"

        # ── Step 2: Validate via CLI ────────────────────────────────────
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "validate",
                "ARCH-DI-001",
                "--patterns-dir",
                str(patterns_dir),
                "--tier",
                "1",
                "--notes",
                "E2E test validation",
            ],
        )
        assert result.exit_code == 0, f"validate failed: {result.output}"
        assert "Validated ARCH-DI-001" in result.output

        # Verify validated pattern on disk
        validated = storage.load_pattern(
            "ARCH-DI-001", stage="validated", model_class=ValidatedPattern
        )
        assert validated is not None
        assert validated.effective_tier == 1
        assert validated.validation.review_notes == "E2E test validation"

        # ── Step 3: Promote with --generate-check (LLM mocked) ─────────
        check_json = json.dumps({"type": "forbidden", "pattern": "OrderRepo()"})

        # RuleGenerator.__init__ needs an API key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-e2e")  # type: ignore[attr-defined]

        # Mock the httpx client inside RuleGenerator
        import sine.rule_generator as rg

        original_aenter = rg.RuleGenerator.__aenter__

        async def patched_aenter(self: rg.RuleGenerator) -> rg.RuleGenerator:
            inst = await original_aenter(self)
            assert inst._client is not None
            inst._client.post = _mock_anthropic_post(check_json)  # type: ignore[assignment]
            return inst

        monkeypatch.setattr(rg.RuleGenerator, "__aenter__", patched_aenter)  # type: ignore[attr-defined]

        result = runner.invoke(
            cli,
            [
                "promote",
                "ARCH-DI-001",
                "--patterns-dir",
                str(patterns_dir),
                "--output-dir",
                str(rules_dir),
                "--generate-check",
                "--provider",
                "anthropic",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"promote failed: {result.output}"
        assert "Promoted ARCH-DI-001" in result.output

        # ── Step 4: Verify the output YAML ──────────────────────────────
        yaml_path = rules_dir / "ARCH-DI-001.yaml"
        assert yaml_path.exists(), f"Expected YAML at {yaml_path}"

        spec_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        assert spec_data["schema_version"] == 1
        assert spec_data["rule"]["id"] == "ARCH-DI-001"
        assert spec_data["rule"]["check"]["type"] == "forbidden"
        assert spec_data["rule"]["check"]["pattern"] == "OrderRepo()"
        assert spec_data["rule"]["tier"] == 1
        assert spec_data["rule"]["severity"] == "error"

        # ── Step 5: Verify it compiles to valid Semgrep config ──────────
        from sine.models import RuleSpecFile

        spec = RuleSpecFile.model_validate(spec_data)
        config = compile_semgrep_config([spec])
        assert len(config["rules"]) == 1

        semgrep_rule = config["rules"][0]
        assert semgrep_rule["id"] == "arch-di-001-impl"
        assert semgrep_rule["languages"] == ["python"]
        assert semgrep_rule["severity"] == "ERROR"

    def test_promote_without_generate_check_uses_placeholder(self, tmp_path: Path) -> None:
        """Without --generate-check, promote falls back to PatternDiscoveryCheck placeholder."""
        patterns_dir = tmp_path / ".sine-patterns"
        rules_dir = tmp_path / ".sine-rules"

        # Save raw + validate in-process (not via CLI to keep test focused)
        storage = PatternStorage(patterns_dir)
        raw = _sample_discovered()
        storage.save_pattern(raw, "raw")
        validated = ValidatedPattern.from_discovered(raw, validated_by="e2e-test")
        storage.save_pattern(validated, "validated")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "promote",
                "ARCH-DI-001",
                "--patterns-dir",
                str(patterns_dir),
                "--output-dir",
                str(rules_dir),
            ],
        )
        assert result.exit_code == 0, f"promote failed: {result.output}"

        yaml_path = rules_dir / "ARCH-DI-001.yaml"
        spec_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

        # Should use placeholder since no --generate-check and no proposed_check
        assert spec_data["rule"]["check"]["type"] == "pattern_discovery"
        assert "..." in spec_data["rule"]["check"]["patterns"]

    def test_promote_generate_check_llm_failure_falls_back(
        self, tmp_path: Path, monkeypatch: object
    ) -> None:
        """When LLM fails, promote still succeeds with placeholder check."""
        patterns_dir = tmp_path / ".sine-patterns"
        rules_dir = tmp_path / ".sine-rules"

        storage = PatternStorage(patterns_dir)
        raw = _sample_discovered()
        storage.save_pattern(raw, "raw")
        validated = ValidatedPattern.from_discovered(raw, validated_by="e2e-test")
        storage.save_pattern(validated, "validated")

        # RuleGenerator.__init__ needs an API key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-e2e")  # type: ignore[attr-defined]

        # Mock the LLM to return garbage
        import sine.rule_generator as rg

        original_aenter = rg.RuleGenerator.__aenter__

        async def patched_aenter(self: rg.RuleGenerator) -> rg.RuleGenerator:
            inst = await original_aenter(self)
            assert inst._client is not None
            inst._client.post = AsyncMock(  # type: ignore[assignment]
                return_value=Mock(
                    status_code=200,
                    json=lambda: {
                        "id": "msg_bad",
                        "content": [{"text": "I cannot generate a check for this pattern."}],
                        "usage": {"input_tokens": 100, "output_tokens": 50},
                    },
                    raise_for_status=lambda: None,
                )
            )
            return inst

        monkeypatch.setattr(rg.RuleGenerator, "__aenter__", patched_aenter)  # type: ignore[attr-defined]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "promote",
                "ARCH-DI-001",
                "--patterns-dir",
                str(patterns_dir),
                "--output-dir",
                str(rules_dir),
                "--generate-check",
                "--provider",
                "anthropic",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"promote failed: {result.output}"
        assert "Promoted ARCH-DI-001" in result.output

        yaml_path = rules_dir / "ARCH-DI-001.yaml"
        spec_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

        # Should fall back to placeholder
        assert spec_data["rule"]["check"]["type"] == "pattern_discovery"

    def test_promote_generate_check_must_wrap(self, tmp_path: Path, monkeypatch: object) -> None:
        """LLM generates a must_wrap check — verify it compiles correctly."""
        patterns_dir = tmp_path / ".sine-patterns"
        rules_dir = tmp_path / ".sine-rules"

        storage = PatternStorage(patterns_dir)
        raw = _sample_discovered()
        storage.save_pattern(raw, "raw")
        validated = ValidatedPattern.from_discovered(raw, validated_by="e2e-test")
        storage.save_pattern(validated, "validated")

        check_json = json.dumps(
            {
                "type": "must_wrap",
                "target": ["OrderRepo()"],
                "wrapper": ["inject"],
            }
        )

        # RuleGenerator.__init__ needs an API key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-e2e")  # type: ignore[attr-defined]

        import sine.rule_generator as rg

        original_aenter = rg.RuleGenerator.__aenter__

        async def patched_aenter(self: rg.RuleGenerator) -> rg.RuleGenerator:
            inst = await original_aenter(self)
            assert inst._client is not None
            inst._client.post = _mock_anthropic_post(check_json)  # type: ignore[assignment]
            return inst

        monkeypatch.setattr(rg.RuleGenerator, "__aenter__", patched_aenter)  # type: ignore[attr-defined]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "promote",
                "ARCH-DI-001",
                "--patterns-dir",
                str(patterns_dir),
                "--output-dir",
                str(rules_dir),
                "--generate-check",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"promote failed: {result.output}"

        yaml_path = rules_dir / "ARCH-DI-001.yaml"
        spec_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        assert spec_data["rule"]["check"]["type"] == "must_wrap"
        assert spec_data["rule"]["check"]["target"] == ["OrderRepo()"]

        # Verify Semgrep compilation
        from sine.models import RuleSpecFile

        spec = RuleSpecFile.model_validate(spec_data)
        config = compile_semgrep_config([spec])
        assert len(config["rules"]) == 1


class TestPromoteToSpecWithRuleGeneratorUnit:
    """Unit-level integration: RuleGenerator output → promote_to_spec → compile."""

    def test_forbidden_check_round_trip(self) -> None:
        """ForbiddenCheck from RuleGenerator flows through promotion to compilation."""
        raw = _sample_discovered()
        validated = ValidatedPattern.from_discovered(raw, validated_by="test")

        check = ForbiddenCheck(type="forbidden", pattern="OrderRepo()")
        spec = promote_to_spec(validated, check_override=check)

        assert spec.rule.check == check
        assert spec.rule.id == "ARCH-DI-001"

        config = compile_semgrep_config([spec])
        rules = config["rules"]
        assert len(rules) == 1
        assert rules[0]["severity"] == "ERROR"

    def test_no_override_produces_placeholder(self) -> None:
        """Without override and no proposed_check, get PatternDiscoveryCheck placeholder."""
        raw = _sample_discovered()
        validated = ValidatedPattern.from_discovered(raw, validated_by="test")

        spec = promote_to_spec(validated)
        assert isinstance(spec.rule.check, PatternDiscoveryCheck)
        assert "..." in spec.rule.check.patterns
