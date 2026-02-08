"""Storage manager for pattern discovery artifacts.

This module provides file-based storage for patterns at different stages:
- raw: DiscoveredPattern (agent output)
- validated: ValidatedPattern (post-quality-gate)
- compiled: CompiledPattern (with Semgrep rules)
- specs: Sine YAML specs (for Semgrep execution)

Directory structure mirrors pattern categorization for easy navigation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import ValidationError

from sine.discovery.models import (
    CompiledPattern,
    DiscoveredPattern,
    PatternLoadError,
    PatternSearchResult,
    ValidatedPattern,
)

logger = logging.getLogger(__name__)

# Type variable for pattern types
T = TypeVar("T", DiscoveredPattern, ValidatedPattern, CompiledPattern)

PatternStage = Literal["raw", "validated", "compiled"]


class PatternStorage:
    """Manages local storage of pattern discovery artifacts.

    Patterns are stored as JSON files organized by category/subcategory
    in a hierarchical directory structure. Each pattern progresses through
    stages (raw → validated → compiled) and maintains its categorization.

    Example:
        storage = PatternStorage(Path(".ling-patterns"))

        # Save a discovered pattern
        pattern = DiscoveredPattern(...)
        storage.save_pattern(pattern, stage="raw")

        # Load by ID
        pattern = storage.load_pattern(
            "ARCH-DI-001",
            stage="raw",
            model_class=DiscoveredPattern
        )

        # List all security patterns
        results = storage.list_patterns(category="security", stage="validated")
    """

    def __init__(self, storage_dir: Path):
        """Initialize the pattern storage manager.

        Args:
            storage_dir: Root directory for pattern storage (e.g., .ling-patterns)
        """
        self.storage_dir = storage_dir
        self.raw_dir = storage_dir / "raw"
        self.validated_dir = storage_dir / "validated"
        self.compiled_dir = storage_dir / "compiled"
        self.specs_dir = storage_dir / "specs"

    def _get_stage_dir(self, stage: PatternStage) -> Path:
        """Get the directory for a given stage.

        Args:
            stage: Pattern stage (raw, validated, compiled)

        Returns:
            Directory path for that stage
        """
        if stage == "raw":
            return self.raw_dir
        elif stage == "validated":
            return self.validated_dir
        elif stage == "compiled":
            return self.compiled_dir
        else:
            raise ValueError(f"Unknown stage: {stage}")

    def _parse_pattern_id(self, pattern_id: str) -> tuple[str, str]:
        """Parse pattern ID into category and subcategory.

        Examples:
            "ARCH-DI-001" → ("architecture", "dependency-injection")
            "SEC-AUTH-042" → ("security", "authentication")
            "PY-DJANGO-001" → ("languages/python/frameworks", "django")

        Args:
            pattern_id: Pattern identifier

        Returns:
            Tuple of (category_path, subcategory)
        """
        parts = pattern_id.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid pattern ID format: {pattern_id}")

        category_code = parts[0]
        subcategory_code = parts[1]

        # Map category codes to directory paths
        category_map = {
            "ARCH": "architecture",
            "SEC": "security",
            "PERF": "performance",
            "TEST": "testing",
            "DOC": "documentation",
            "ERROR": "error-handling",
            "NAMING": "naming",
            "PY": "languages/python/frameworks",
            "JS": "languages/javascript/frameworks",
            "TS": "languages/typescript/frameworks",
            "JAVA": "languages/java/frameworks",
            "GO": "languages/go/frameworks",
            "RUST": "languages/rust/frameworks",
            "CS": "languages/csharp/frameworks",
            "CPP": "languages/cpp/frameworks",
        }

        # Map subcategory codes to directory names
        subcategory_map = {
            "DI": "dependency-injection",
            "LAY": "layering",
            "MOD": "modularity",
            "AUTH": "authentication",
            "VAL": "input-validation",
            "CRYPTO": "cryptography",
            "DJANGO": "django",
            "FASTAPI": "fastapi",
            "REACT": "react",
            "NEXTJS": "nextjs",
            "SPRING": "spring",
            "DOTNET": "dotnet",
            "CACHE": "caching",
            "QT": "qt",
            "UNITY": "unity",
        }

        category_path = category_map.get(category_code, category_code.lower())
        subcategory = subcategory_map.get(subcategory_code, subcategory_code.lower())

        return category_path, subcategory

    def _get_pattern_path(
        self,
        pattern_id: str,
        stage: PatternStage,
        create_dirs: bool = False,
    ) -> Path:
        """Get the file path for a pattern.

        Args:
            pattern_id: Pattern identifier
            stage: Pattern stage
            create_dirs: Whether to create parent directories

        Returns:
            Path to the pattern JSON file
        """
        category_path, subcategory = self._parse_pattern_id(pattern_id)
        stage_dir = self._get_stage_dir(stage)

        # Build path: stage_dir / category_path / subcategory / PATTERN-ID.json
        file_path = stage_dir / category_path / subcategory / f"{pattern_id}.json"

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        return file_path

    def _get_spec_path(self, pattern_id: str, create_dirs: bool = False) -> Path:
        """Get the file path for a Sine spec.

        Args:
            pattern_id: Pattern identifier
            create_dirs: Whether to create parent directory

        Returns:
            Path to the spec YAML file
        """
        file_path = self.specs_dir / f"{pattern_id}.yaml"

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        return file_path

    def save_pattern(
        self,
        pattern: DiscoveredPattern | ValidatedPattern | CompiledPattern,
        stage: PatternStage,
    ) -> None:
        """Save a pattern to storage.

        Args:
            pattern: The pattern to save
            stage: Which stage directory to save to
        """
        # Determine pattern ID based on type
        if isinstance(pattern, CompiledPattern):
            pattern_id = pattern.validated.discovered.pattern_id
        elif isinstance(pattern, ValidatedPattern):
            pattern_id = pattern.discovered.pattern_id
        else:  # DiscoveredPattern
            pattern_id = pattern.pattern_id

        file_path = self._get_pattern_path(pattern_id, stage, create_dirs=True)

        # Serialize to JSON
        data = pattern.model_dump(mode="json")
        file_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        logger.info(f"Saved {stage} pattern: {pattern_id} → {file_path}")

    def load_pattern(
        self,
        pattern_id: str,
        stage: PatternStage,
        model_class: type[T],
    ) -> T | None:
        """Load a pattern from storage.

        Args:
            pattern_id: Pattern identifier
            stage: Which stage directory to load from
            model_class: Pydantic model class to deserialize into

        Returns:
            Pattern instance if found, None otherwise
        """
        file_path = self._get_pattern_path(pattern_id, stage)

        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return model_class.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to load pattern {pattern_id} from {file_path}: {e}")
            return None

    def list_patterns(
        self,
        stage: PatternStage,
        category: str | None = None,
        subcategory: str | None = None,
    ) -> list[PatternSearchResult]:
        """List patterns in storage.

        Args:
            stage: Which stage directory to list
            category: Optional category filter
            subcategory: Optional subcategory filter

        Returns:
            List of pattern search results (lightweight metadata)
        """
        stage_dir = self._get_stage_dir(stage)

        if not stage_dir.exists():
            return []

        # Build search path
        if category and subcategory:
            search_path = stage_dir / category / subcategory
        elif category:
            search_path = stage_dir / category
        else:
            search_path = stage_dir

        if not search_path.exists():
            return []

        results: list[PatternSearchResult] = []
        errors: list[PatternLoadError] = []

        # Find all JSON files
        for json_file in search_path.rglob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))

                # Extract metadata based on stage
                if stage == "compiled":
                    pattern_id = data["validated"]["discovered"]["pattern_id"]
                    title = data["validated"]["discovered"]["title"]
                    category_val = data["validated"]["discovered"]["category"]
                    subcategory_val = data["validated"]["discovered"].get("subcategory")
                    tier = data["validated"]["effective_tier"]
                    confidence = data["validated"]["discovered"]["confidence"]
                elif stage == "validated":
                    pattern_id = data["discovered"]["pattern_id"]
                    title = data["discovered"]["title"]
                    category_val = data["discovered"]["category"]
                    subcategory_val = data["discovered"].get("subcategory")
                    tier = data["effective_tier"]
                    confidence = data["discovered"]["confidence"]
                else:  # raw
                    pattern_id = data["pattern_id"]
                    title = data["title"]
                    category_val = data["category"]
                    subcategory_val = data.get("subcategory")
                    tier = self._infer_tier_from_data(data)
                    confidence = data["confidence"]

                results.append(
                    PatternSearchResult(
                        pattern_id=pattern_id,
                        title=title,
                        category=category_val,
                        subcategory=subcategory_val,
                        tier=tier,
                        confidence=confidence,
                        stage=stage,
                    )
                )
            except (json.JSONDecodeError, KeyError, ValidationError) as e:
                errors.append(
                    PatternLoadError(
                        file_path=str(json_file),
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )
                )

        # Log errors
        for error in errors:
            logger.warning(
                f"Failed to load pattern from {error.file_path}: "
                f"{error.error_type}: {error.error_message}"
            )

        # Sort by pattern ID
        results.sort(key=lambda r: r.pattern_id)

        return results

    def _infer_tier_from_data(self, data: dict[str, Any]) -> int:
        """Infer tier from raw pattern data (for listing without full model load).

        Args:
            data: Pattern dictionary

        Returns:
            Inferred tier (1, 2, or 3)
        """
        severity = data.get("severity", "warning")
        confidence = data.get("confidence", "medium")
        framework = data.get("framework")

        if severity == "error" and confidence == "high":
            return 1
        elif framework is not None:
            return 3
        else:
            return 2

    def load_category(
        self,
        category: str,
        stage: PatternStage,
        model_class: type[T],
        subcategory: str | None = None,
    ) -> list[T]:
        """Load all patterns in a category.

        Args:
            category: Category to load
            stage: Which stage directory to load from
            model_class: Pydantic model class to deserialize into
            subcategory: Optional subcategory filter

        Returns:
            List of pattern instances
        """
        stage_dir = self._get_stage_dir(stage)

        search_path = (
            stage_dir / category / subcategory if subcategory else stage_dir / category
        )

        if not search_path.exists():
            return []

        patterns: list[T] = []

        for json_file in search_path.rglob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                pattern = model_class.model_validate(data)
                patterns.append(pattern)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to load pattern from {json_file}: {e}")
                continue

        return patterns

    def pattern_exists(self, pattern_id: str, stage: PatternStage) -> bool:
        """Check if a pattern exists at a given stage.

        Args:
            pattern_id: Pattern identifier
            stage: Pattern stage to check

        Returns:
            True if the pattern file exists, False otherwise
        """
        file_path = self._get_pattern_path(pattern_id, stage)
        return file_path.exists()

    def delete_pattern(self, pattern_id: str, stage: PatternStage) -> bool:
        """Delete a pattern from storage.

        Args:
            pattern_id: Pattern identifier
            stage: Stage to delete from

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_pattern_path(pattern_id, stage)

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted {stage} pattern: {pattern_id}")
            return True
        else:
            return False
