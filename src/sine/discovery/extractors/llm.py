"""LLM-powered pattern extraction.

This extractor uses LLM APIs (Anthropic, OpenAI, Gemini) to analyze web content
and synthesize coding patterns. It's the most accurate extraction method but
has API costs.

Supported Providers:
- Anthropic Claude (claude-sonnet-4-20250514)
- OpenAI GPT (gpt-4o, gpt-4o-mini)
- Google Gemini (gemini-2.0-flash-exp)

Features:
- Structured JSON output for reliable parsing
- Rate limiting and exponential backoff retry
- Token usage tracking
- Cost estimation
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import logging

from sine.discovery.extractors.base import (
    ExtractionContext,
    ExtractionResult,
    PatternExtractor,
)
from sine.discovery.models import (
    DiscoveredPattern,
    PatternExample,
    PatternExamples,
)

logger = logging.getLogger("sine.discovery.llm_extractor")


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


# Default models for each provider
DEFAULT_MODELS = {
    LLMProvider.ANTHROPIC: "claude-sonnet-4-20250514",
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.GEMINI: "gemini-2.0-flash-exp",
}

# API endpoints
API_ENDPOINTS = {
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
    LLMProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
    LLMProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
}

# Pricing (USD per 1M tokens)
# Note: These are approximate and should be updated periodically
PRICING = {
    LLMProvider.ANTHROPIC: {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    },
    LLMProvider.OPENAI: {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    },
    LLMProvider.GEMINI: {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
    },
}


class LLMExtractor(PatternExtractor):
    """LLM-powered pattern extractor.

    Uses LLM APIs to analyze web content and synthesize coding patterns.
    Supports multiple providers for flexibility.

    Example:
        async with LLMExtractor(
            provider=LLMProvider.ANTHROPIC,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ) as extractor:
            context = ExtractionContext(...)
            result = await extractor.extract_patterns(context)
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ):
        """Initialize the LLM extractor.

        Args:
            provider: LLM provider to use
            model: Model name (uses default if not specified)
            api_key: API key (falls back to environment variable)
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts on failure
        """
        self.provider = provider
        self.model = model or DEFAULT_MODELS[provider]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Get API key from parameter or environment
        env_var_map = {
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.GEMINI: "GOOGLE_API_KEY",
        }
        self.api_key = api_key or os.environ.get(env_var_map[provider])

        if not self.api_key:
            raise ValueError(
                f"API key required for {provider}. "
                f"Set {env_var_map[provider]} environment variable or pass api_key parameter."
            )

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> LLMExtractor:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup HTTP client."""
        if self._client:
            await self._client.aclose()

    async def extract_patterns(self, context: ExtractionContext) -> ExtractionResult:
        """Extract patterns using LLM analysis.

        Strategy:
        1. Build structured prompt requesting JSON pattern output
        2. Call LLM API with retry logic
        3. Parse JSON response into DiscoveredPattern objects
        4. Track token usage and confidence

        Args:
            context: Extraction context with source text

        Returns:
            ExtractionResult with discovered patterns
        """
        if not self._client:
            raise RuntimeError("LLMExtractor must be used as async context manager")

        # Build prompt
        prompt = self._build_prompt(context)

        # Call LLM API with retries
        response_data = await self._call_llm_with_retry(prompt)

        # Parse response
        patterns = self._parse_response(response_data, context)

        # Calculate confidence based on response quality
        confidence = self._calculate_confidence(patterns, response_data)

        # Extract token usage
        token_usage = self._extract_token_usage(response_data)

        return ExtractionResult(
            patterns=patterns,
            confidence=confidence,
            method="llm",
            metadata={
                "provider": self.provider.value,
                "model": self.model,
                "token_usage": token_usage,
                "temperature": self.temperature,
            },
        )

    def _build_prompt(self, context: ExtractionContext) -> str:
        """Build structured prompt for pattern extraction.

        Args:
            context: Extraction context

        Returns:
            Formatted prompt string
        """
        return f"""Analyze the following technical content and extract coding patterns/best practices.

Focus: {context.focus.description}
Category: {context.focus.focus_type}

Source Content:
{context.source_text[:8000]}

Extract coding patterns and return them as a JSON array of pattern objects. Each pattern should have:
- pattern_id: A unique identifier (format: CATEGORY-SUBCATEGORY-NNN, e.g., ARCH-DI-001, SEC-AUTH-042)
- title: Clear, concise title (5-120 chars)
- category: Primary category ({context.focus.focus_type})
- subcategory: Specific subcategory (e.g., dependency-injection, authentication)
- description: What the pattern requires (20+ chars)
- rationale: Why this pattern exists and what it prevents (20+ chars)
- confidence: Your confidence level (high/medium/low)
- severity: How critical (error/warning/info)
- languages: Applicable programming languages (empty array if language-agnostic)
- framework: Specific framework if tier 3 pattern (null otherwise)
- examples_good: Array of good code examples with {{language, code, description}}
- examples_bad: Array of bad code examples with {{language, code, description}}
- tags: 1-5 relevant tags

Return ONLY valid JSON (no markdown, no explanation):
[
  {{
    "pattern_id": "SEC-SQL-001",
    "title": "Prevent SQL Injection",
    "category": "security",
    "subcategory": "injection",
    "description": "Use parameterized queries...",
    "rationale": "Prevents SQL injection attacks...",
    "confidence": "high",
    "severity": "error",
    "languages": ["python", "java"],
    "framework": null,
    "examples_good": [{{"language": "python", "code": "...", "description": "..."}}],
    "examples_bad": [{{"language": "python", "code": "...", "description": "..."}}],
    "tags": ["sql", "security", "injection"]
  }}
]

Extract 1-5 high-quality patterns from the content. Focus on actionable, specific patterns."""

    async def _call_llm_with_retry(self, prompt: str) -> dict[str, Any]:
        """Call LLM API with exponential backoff retry.

        Args:
            prompt: Prompt to send

        Returns:
            API response data

        Raises:
            Exception: If all retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                if self.provider == LLMProvider.ANTHROPIC:
                    return await self._call_anthropic(prompt)
                elif self.provider == LLMProvider.OPENAI:
                    return await self._call_openai(prompt)
                elif self.provider == LLMProvider.GEMINI:
                    return await self._call_gemini(prompt)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Rate limited by {self.provider}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"LLM API error: {e}, retrying (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(2**attempt)

        raise RuntimeError(f"Failed to call {self.provider} API after {self.max_retries} attempts")

    async def _call_anthropic(self, prompt: str) -> dict[str, Any]:
        """Call Anthropic Messages API.

        Args:
            prompt: Prompt to send

        Returns:
            API response
        """
        assert self._client is not None

        response = await self._client.post(
            API_ENDPOINTS[LLMProvider.ANTHROPIC],
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()

    async def _call_openai(self, prompt: str) -> dict[str, Any]:
        """Call OpenAI Chat Completions API.

        Args:
            prompt: Prompt to send

        Returns:
            API response
        """
        assert self._client is not None

        response = await self._client.post(
            API_ENDPOINTS[LLMProvider.OPENAI],
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        return response.json()

    async def _call_gemini(self, prompt: str) -> dict[str, Any]:
        """Call Google Gemini API.

        Args:
            prompt: Prompt to send

        Returns:
            API response
        """
        assert self._client is not None

        url = API_ENDPOINTS[LLMProvider.GEMINI].format(model=self.model)
        response = await self._client.post(
            f"{url}?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens,
                },
            },
        )
        response.raise_for_status()
        return response.json()

    def _parse_response(
        self, response_data: dict[str, Any], context: ExtractionContext
    ) -> list[DiscoveredPattern]:
        """Parse LLM response into DiscoveredPattern objects.

        Args:
            response_data: API response
            context: Extraction context

        Returns:
            List of discovered patterns
        """
        # Extract text content based on provider
        if self.provider == LLMProvider.ANTHROPIC:
            text = response_data["content"][0]["text"]
        elif self.provider == LLMProvider.OPENAI:
            text = response_data["choices"][0]["message"]["content"]
        elif self.provider == LLMProvider.GEMINI:
            text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Parse JSON
        try:
            # Handle markdown-wrapped JSON
            if text.strip().startswith("```"):
                text = text.strip().removeprefix("```json").removeprefix("```")
                text = text.strip().removesuffix("```")

            patterns_data = json.loads(text)

            # Handle single pattern vs array
            if isinstance(patterns_data, dict):
                patterns_data = [patterns_data]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}\nResponse: {text[:500]}")
            return []

        # Convert to DiscoveredPattern objects
        patterns: list[DiscoveredPattern] = []
        for i, pattern_data in enumerate(patterns_data):
            try:
                # Build examples
                examples = PatternExamples(
                    good=[
                        PatternExample(**ex)
                        for ex in pattern_data.get("examples_good", [])
                    ],
                    bad=[
                        PatternExample(**ex)
                        for ex in pattern_data.get("examples_bad", [])
                    ],
                )

                pattern = DiscoveredPattern(
                    pattern_id=pattern_data["pattern_id"],
                    title=pattern_data["title"],
                    category=pattern_data["category"],
                    subcategory=pattern_data.get("subcategory"),
                    description=pattern_data["description"],
                    rationale=pattern_data["rationale"],
                    confidence=pattern_data["confidence"],
                    severity=pattern_data.get("severity", "warning"),
                    languages=pattern_data.get("languages", []),
                    framework=pattern_data.get("framework"),
                    examples=examples,
                    tags=pattern_data.get("tags", []),
                    discovered_by=f"llm-{self.provider.value}",
                    discovered_at=datetime.now(),
                    source_files=[],
                    evidence={
                        "source_url": context.source_url,
                        "model": self.model,
                        "provider": self.provider.value,
                    },
                    references=[context.source_url],
                )
                patterns.append(pattern)

            except Exception as e:
                logger.warning(f"Failed to parse pattern {i}: {e}")
                continue

        return patterns

    def _calculate_confidence(
        self, patterns: list[DiscoveredPattern], response_data: dict[str, Any]
    ) -> float:
        """Calculate overall extraction confidence.

        Args:
            patterns: Extracted patterns
            response_data: API response

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not patterns:
            return 0.0

        # Average pattern confidences
        confidence_map = {"high": 1.0, "medium": 0.66, "low": 0.33}
        avg_pattern_confidence = sum(
            confidence_map[p.confidence] for p in patterns
        ) / len(patterns)

        return avg_pattern_confidence

    def _extract_token_usage(self, response_data: dict[str, Any]) -> dict[str, int]:
        """Extract token usage from API response.

        Args:
            response_data: API response

        Returns:
            Token usage dict with input/output tokens
        """
        if self.provider == LLMProvider.ANTHROPIC:
            usage = response_data.get("usage", {})
            return {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }
        elif self.provider == LLMProvider.OPENAI:
            usage = response_data.get("usage", {})
            return {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }
        elif self.provider == LLMProvider.GEMINI:
            metadata = response_data.get("usageMetadata", {})
            return {
                "input_tokens": metadata.get("promptTokenCount", 0),
                "output_tokens": metadata.get("candidatesTokenCount", 0),
            }
        else:
            return {"input_tokens": 0, "output_tokens": 0}

    def estimate_cost(self, context: ExtractionContext) -> float:
        """Estimate extraction cost based on input size.

        Args:
            context: Extraction context

        Returns:
            Estimated cost in USD
        """
        # Rough token estimate: ~4 chars per token
        input_tokens = len(context.source_text) // 4
        # Output tokens: assume ~1000 tokens for pattern JSON
        output_tokens = 1000

        # Get pricing
        model_pricing = PRICING.get(self.provider, {}).get(self.model)
        if not model_pricing:
            return 0.0  # Unknown pricing

        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

        return input_cost + output_cost
