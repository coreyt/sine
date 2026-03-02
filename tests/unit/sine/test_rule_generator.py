"""Tests for LLM-based Semgrep rule generation at promotion time."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from sine.discovery.extractors.llm import LLMProvider
from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
    ValidatedPattern,
)
from sine.models import (
    ForbiddenCheck,
    MustWrapCheck,
    PatternDiscoveryCheck,
    RawCheck,
    RequiredWithCheck,
)
from sine.rule_generator import RuleGenerator


def _make_validated_pattern(
    pattern_id: str = "ARCH-DI-001",
    description: str = "Services should receive dependencies via constructor injection rather than instantiating them directly.",
    rationale: str = "Direct instantiation couples services tightly and makes unit testing difficult.",
    languages: list[str] | None = None,
    good_examples: list[PatternExample] | None = None,
    bad_examples: list[PatternExample] | None = None,
) -> ValidatedPattern:
    """Create a ValidatedPattern for testing."""
    discovered = DiscoveredPattern(
        pattern_id=pattern_id,
        title="Avoid direct instantiation in service layer",
        description=description,
        rationale=rationale,
        category="architecture",
        severity="error",
        confidence="high",
        languages=languages or ["python"],
        examples=PatternExamples(
            good=good_examples
            or [
                PatternExample(
                    language="python",
                    code="class Service:\n    def __init__(self, repo: Repo):\n        self.repo = repo",
                )
            ],
            bad=bad_examples
            or [
                PatternExample(
                    language="python",
                    code="class Service:\n    def __init__(self):\n        self.repo = Repo()",
                )
            ],
        ),
        discovered_by="test-agent",
        references=["https://example.com/di"],
    )
    return ValidatedPattern.from_discovered(discovered, validated_by="reviewer")


def _anthropic_response(check_json: str) -> dict:
    """Build a mock Anthropic API response."""
    return {
        "id": "msg_test",
        "content": [{"text": check_json}],
        "usage": {"input_tokens": 500, "output_tokens": 200},
    }


def _openai_response(check_json: str) -> dict:
    """Build a mock OpenAI API response."""
    return {
        "choices": [{"message": {"content": check_json}}],
        "usage": {"prompt_tokens": 400, "completion_tokens": 150},
    }


def _gemini_response(check_json: str) -> dict:
    """Build a mock Gemini API response."""
    return {
        "candidates": [{"content": {"parts": [{"text": check_json}]}}],
        "usageMetadata": {"promptTokenCount": 300, "candidatesTokenCount": 100},
    }


# ============================================================================
# TestRuleGeneratorInit
# ============================================================================


class TestRuleGeneratorInit:
    def test_explicit_api_key(self) -> None:
        gen = RuleGenerator(api_key="test-key-123")
        assert gen.api_key == "test-key-123"

    def test_env_var_fallback_anthropic(self) -> None:
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            gen = RuleGenerator(provider=LLMProvider.ANTHROPIC)
            assert gen.api_key == "env-key"

    def test_env_var_fallback_openai(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "oai-key"}):
            gen = RuleGenerator(provider=LLMProvider.OPENAI)
            assert gen.api_key == "oai-key"

    def test_env_var_fallback_gemini(self) -> None:
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "gem-key"}):
            gen = RuleGenerator(provider=LLMProvider.GEMINI)
            assert gen.api_key == "gem-key"

    def test_missing_api_key_raises(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="API key required"),
        ):
            RuleGenerator(provider=LLMProvider.ANTHROPIC)

    def test_default_model_anthropic(self) -> None:
        gen = RuleGenerator(api_key="k", provider=LLMProvider.ANTHROPIC)
        assert "claude" in gen.model

    def test_custom_model(self) -> None:
        gen = RuleGenerator(api_key="k", model="custom-model")
        assert gen.model == "custom-model"

    def test_default_temperature(self) -> None:
        gen = RuleGenerator(api_key="k")
        assert gen.temperature == 0.0

    def test_default_max_retries(self) -> None:
        gen = RuleGenerator(api_key="k")
        assert gen.max_retries == 3


# ============================================================================
# TestBuildPrompt
# ============================================================================


class TestBuildPrompt:
    def test_prompt_includes_description(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        assert "constructor injection" in prompt

    def test_prompt_includes_rationale(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        assert "unit testing" in prompt

    def test_prompt_includes_languages(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern(languages=["python", "java"])
        prompt = gen._build_prompt(pattern)
        assert "python" in prompt
        assert "java" in prompt

    def test_prompt_includes_good_examples(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        assert "self.repo = repo" in prompt

    def test_prompt_includes_bad_examples(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        assert "self.repo = Repo()" in prompt

    def test_prompt_includes_check_type_catalog(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        # Should mention all 5 check types
        assert "forbidden" in prompt
        assert "must_wrap" in prompt
        assert "required_with" in prompt
        assert "raw" in prompt
        assert "pattern_discovery" in prompt

    def test_prompt_requests_json_output(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern()
        prompt = gen._build_prompt(pattern)
        assert "JSON" in prompt

    def test_prompt_handles_no_examples(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern(good_examples=[], bad_examples=[])
        prompt = gen._build_prompt(pattern)
        # Should not crash, still contains description
        assert "constructor injection" in prompt

    def test_prompt_handles_no_languages(self) -> None:
        gen = RuleGenerator(api_key="k")
        pattern = _make_validated_pattern(languages=[])
        prompt = gen._build_prompt(pattern)
        assert "constructor injection" in prompt


# ============================================================================
# TestParseCheck
# ============================================================================


class TestParseCheck:
    def test_parse_forbidden_check(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        result = gen._parse_check(data)
        assert isinstance(result, ForbiddenCheck)
        assert result.pattern == "Repo()"

    def test_parse_must_wrap_check(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps(
            {
                "type": "must_wrap",
                "target": ["requests.get"],
                "wrapper": ["circuit_breaker"],
            }
        )
        result = gen._parse_check(data)
        assert isinstance(result, MustWrapCheck)
        assert result.target == ["requests.get"]

    def test_parse_required_with_check(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps(
            {
                "type": "required_with",
                "if_present": "open(",
                "must_have": "close(",
            }
        )
        result = gen._parse_check(data)
        assert isinstance(result, RequiredWithCheck)
        assert result.if_present == "open("

    def test_parse_raw_check(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps(
            {
                "type": "raw",
                "config": "rules:\n  - id: test\n    pattern: foo()",
                "engine": "semgrep",
            }
        )
        result = gen._parse_check(data)
        assert isinstance(result, RawCheck)

    def test_parse_pattern_discovery_check(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps(
            {
                "type": "pattern_discovery",
                "patterns": ["class $C:\n  def __init__(self): ..."],
            }
        )
        result = gen._parse_check(data)
        assert isinstance(result, PatternDiscoveryCheck)
        assert len(result.patterns) == 1

    def test_parse_markdown_wrapped_json(self) -> None:
        gen = RuleGenerator(api_key="k")
        inner = json.dumps({"type": "forbidden", "pattern": "eval(...)"})
        data = f"```json\n{inner}\n```"
        result = gen._parse_check(data)
        assert isinstance(result, ForbiddenCheck)
        assert result.pattern == "eval(...)"

    def test_parse_markdown_no_lang_tag(self) -> None:
        gen = RuleGenerator(api_key="k")
        inner = json.dumps({"type": "forbidden", "pattern": "exec(...)"})
        data = f"```\n{inner}\n```"
        result = gen._parse_check(data)
        assert isinstance(result, ForbiddenCheck)

    def test_invalid_json_returns_none(self) -> None:
        gen = RuleGenerator(api_key="k")
        result = gen._parse_check("this is not json")
        assert result is None

    def test_unknown_type_returns_none(self) -> None:
        gen = RuleGenerator(api_key="k")
        data = json.dumps({"type": "nonexistent_type", "foo": "bar"})
        result = gen._parse_check(data)
        assert result is None

    def test_missing_required_fields_returns_none(self) -> None:
        gen = RuleGenerator(api_key="k")
        # forbidden requires "pattern" field
        data = json.dumps({"type": "forbidden"})
        result = gen._parse_check(data)
        assert result is None

    def test_extra_fields_returns_none(self) -> None:
        gen = RuleGenerator(api_key="k")
        # extra="forbid" on all check models should reject extra fields
        data = json.dumps({"type": "forbidden", "pattern": "foo()", "extra_field": "bad"})
        result = gen._parse_check(data)
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        gen = RuleGenerator(api_key="k")
        result = gen._parse_check("")
        assert result is None


# ============================================================================
# TestGenerateCheck
# ============================================================================


class TestGenerateCheck:
    @pytest.mark.asyncio
    async def test_anthropic_generate_check(self) -> None:
        check_json = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        mock_resp = _anthropic_response(check_json)

        async with RuleGenerator(api_key="test-key", provider=LLMProvider.ANTHROPIC) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            result = await gen.generate_check(_make_validated_pattern())

        assert isinstance(result, ForbiddenCheck)
        assert result.pattern == "Repo()"

    @pytest.mark.asyncio
    async def test_openai_generate_check(self) -> None:
        check_json = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        mock_resp = _openai_response(check_json)

        async with RuleGenerator(api_key="test-key", provider=LLMProvider.OPENAI) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            result = await gen.generate_check(_make_validated_pattern())

        assert isinstance(result, ForbiddenCheck)

    @pytest.mark.asyncio
    async def test_gemini_generate_check(self) -> None:
        check_json = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        mock_resp = _gemini_response(check_json)

        async with RuleGenerator(api_key="test-key", provider=LLMProvider.GEMINI) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            result = await gen.generate_check(_make_validated_pattern())

        assert isinstance(result, ForbiddenCheck)

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self) -> None:
        check_json = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        mock_responses = [
            Mock(
                status_code=429,
                raise_for_status=Mock(
                    side_effect=httpx.HTTPStatusError(
                        "Rate limited",
                        request=Mock(),
                        response=Mock(status_code=429),
                    )
                ),
            ),
            Mock(
                status_code=200,
                json=lambda: _anthropic_response(check_json),
                raise_for_status=lambda: None,
            ),
        ]

        async with RuleGenerator(
            api_key="test-key", provider=LLMProvider.ANTHROPIC, max_retries=2
        ) as gen:
            mock_post = AsyncMock(side_effect=mock_responses)
            gen._client.post = mock_post  # type: ignore[union-attr]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await gen.generate_check(_make_validated_pattern())

        assert isinstance(result, ForbiddenCheck)
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_returns_none(self) -> None:
        error_resp = Mock(
            status_code=500,
            raise_for_status=Mock(
                side_effect=httpx.HTTPStatusError(
                    "Server error",
                    request=Mock(),
                    response=Mock(status_code=500),
                )
            ),
        )

        async with RuleGenerator(
            api_key="test-key", provider=LLMProvider.ANTHROPIC, max_retries=2
        ) as gen:
            gen._client.post = AsyncMock(side_effect=[error_resp, error_resp])  # type: ignore[union-attr]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await gen.generate_check(_make_validated_pattern())

        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_llm_response_returns_none(self) -> None:
        mock_resp = _anthropic_response("not valid json at all")

        async with RuleGenerator(api_key="test-key", provider=LLMProvider.ANTHROPIC) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            result = await gen.generate_check(_make_validated_pattern())

        assert result is None

    @pytest.mark.asyncio
    async def test_context_manager_initializes_client(self) -> None:
        async with RuleGenerator(api_key="test-key") as gen:
            assert gen._client is not None

    @pytest.mark.asyncio
    async def test_context_manager_cleans_up_client(self) -> None:
        gen = RuleGenerator(api_key="test-key")
        async with gen:
            pass
        # After exiting, client should be closed (set to None or aclose called)
        # We just verify it doesn't raise


# ============================================================================
# TestGenerateCheckIntegration
# ============================================================================


class TestGenerateCheckIntegration:
    """End-to-end: generate_check → promote_to_spec → compile_semgrep_config."""

    @pytest.mark.asyncio
    async def test_generated_forbidden_check_compiles(self) -> None:
        from sine.promotion import promote_to_spec
        from sine.semgrep import compile_semgrep_config

        check_json = json.dumps({"type": "forbidden", "pattern": "Repo()"})
        mock_resp = _anthropic_response(check_json)

        pattern = _make_validated_pattern()
        async with RuleGenerator(api_key="test-key", provider=LLMProvider.ANTHROPIC) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            check = await gen.generate_check(pattern)

        assert check is not None
        spec = promote_to_spec(pattern, check_override=check)
        assert spec.rule.check == check

        # Should compile to valid Semgrep config
        config = compile_semgrep_config([spec])
        assert len(config["rules"]) == 1
        assert config["rules"][0]["id"] == "arch-di-001-impl"

    @pytest.mark.asyncio
    async def test_generated_must_wrap_check_compiles(self) -> None:
        from sine.promotion import promote_to_spec
        from sine.semgrep import compile_semgrep_config

        check_json = json.dumps(
            {
                "type": "must_wrap",
                "target": ["Repo()"],
                "wrapper": ["inject"],
            }
        )
        mock_resp = _anthropic_response(check_json)

        pattern = _make_validated_pattern()
        async with RuleGenerator(api_key="test-key", provider=LLMProvider.ANTHROPIC) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            check = await gen.generate_check(pattern)

        assert check is not None
        spec = promote_to_spec(pattern, check_override=check)
        config = compile_semgrep_config([spec])
        assert len(config["rules"]) == 1

    @pytest.mark.asyncio
    async def test_none_check_falls_through_to_placeholder(self) -> None:
        from sine.promotion import promote_to_spec

        # Simulate LLM returning garbage → generate_check returns None
        mock_resp = _anthropic_response("garbage")

        pattern = _make_validated_pattern()
        async with RuleGenerator(api_key="test-key", provider=LLMProvider.ANTHROPIC) as gen:
            gen._client.post = AsyncMock(  # type: ignore[union-attr]
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_resp,
                    raise_for_status=lambda: None,
                )
            )
            check = await gen.generate_check(pattern)

        assert check is None
        spec = promote_to_spec(pattern, check_override=check)
        # Should fall through to PatternDiscoveryCheck placeholder
        assert isinstance(spec.rule.check, PatternDiscoveryCheck)
