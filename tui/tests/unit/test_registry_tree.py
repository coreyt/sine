"""Tests for the RegistryTree widget."""

from __future__ import annotations

from lookout.models import (
    FrameworkVariant,
    GenericVariant,
    LanguageVariant,
    PatternSpec,
    PatternSpecFile,
    RawCheck,
    RuleReporting,
    VariantExamples,
)

from lookout_tui.widgets.registry_tree import (
    FrameworkNodeData,
    LanguageNodeData,
    PatternNodeData,
    RegistryTree,
)


def _reporting() -> RuleReporting:
    return RuleReporting(default_message="msg", confidence="medium")


def _check() -> RawCheck:
    return RawCheck(type="raw", config="rules: []")


def _spec(
    id: str = "TEST-001",
    status: str = "draft",
    variants: list[LanguageVariant] | None = None,
) -> PatternSpecFile:
    return PatternSpecFile(
        schema_version=2,
        pattern=PatternSpec(
            id=id,
            title="Test",
            description="Test pattern",
            rationale="Testing",
            tier=2,
            category="testing",
            severity="warning",
            reporting=_reporting(),
            status=status,
            variants=variants or [],
        ),
    )


class TestRegistryTreePopulate:
    def test_empty_list(self) -> None:
        tree = RegistryTree()
        tree.populate([])
        assert tree.patterns == []

    def test_single_pattern_no_variants(self) -> None:
        tree = RegistryTree()
        spec = _spec(id="ARCH-001")
        tree.populate([spec])

        assert len(tree.patterns) == 1
        # Root should have one child (the pattern node)
        assert len(tree.root.children) == 1
        node = tree.root.children[0]
        assert isinstance(node.data, PatternNodeData)
        assert node.data.spec.pattern.id == "ARCH-001"

    def test_pattern_with_language_variant(self) -> None:
        tree = RegistryTree()
        spec = _spec(
            id="DI-001",
            status="active",
            variants=[
                LanguageVariant(
                    language="python",
                    generic=GenericVariant(check=_check(), examples=VariantExamples()),
                )
            ],
        )
        tree.populate([spec])

        pattern_node = tree.root.children[0]
        assert "DI-001" in str(pattern_node.label)
        assert "✓" in str(pattern_node.label)  # active status

        # Should have language child
        assert len(pattern_node.children) == 1
        lang_node = pattern_node.children[0]
        assert isinstance(lang_node.data, LanguageNodeData)
        assert lang_node.data.language == "python"

    def test_pattern_with_framework_variant(self) -> None:
        tree = RegistryTree()
        spec = _spec(
            id="DI-001",
            variants=[
                LanguageVariant(
                    language="python",
                    generic=GenericVariant(check=_check(), examples=VariantExamples()),
                    frameworks=[
                        FrameworkVariant(
                            name="django",
                            check=_check(),
                            examples=VariantExamples(),
                        )
                    ],
                )
            ],
        )
        tree.populate([spec])

        lang_node = tree.root.children[0].children[0]
        # Should have generic + django
        assert len(lang_node.children) == 2
        generic_leaf = lang_node.children[0]
        assert isinstance(generic_leaf.data, FrameworkNodeData)
        assert generic_leaf.data.framework == "generic"

        django_leaf = lang_node.children[1]
        assert isinstance(django_leaf.data, FrameworkNodeData)
        assert django_leaf.data.framework == "django"

    def test_multiple_patterns_sorted(self) -> None:
        tree = RegistryTree()
        tree.populate([_spec(id="ZZZ-001"), _spec(id="AAA-001"), _spec(id="MMM-001")])

        ids = [
            c.data.spec.pattern.id
            for c in tree.root.children
            if isinstance(c.data, PatternNodeData)
        ]
        assert ids == ["AAA-001", "MMM-001", "ZZZ-001"]

    def test_status_icons(self) -> None:
        tree = RegistryTree()
        tree.populate([
            _spec(id="A-001", status="draft"),
            _spec(id="B-001", status="active"),
            _spec(id="C-001", status="deprecated"),
        ])

        labels = [str(c.label) for c in tree.root.children]
        assert "~" in labels[0]  # draft
        assert "✓" in labels[1]  # active
        assert "✗" in labels[2]  # deprecated

    def test_built_in_tag_in_label(self) -> None:
        tree = RegistryTree()
        tree.populate(
            [_spec(id="A-001"), _spec(id="B-001")],
            built_in_ids={"A-001"},
        )
        labels = [str(c.label) for c in tree.root.children]
        assert "(built-in)" in labels[0]  # A-001 is built-in
        assert "(built-in)" not in labels[1]  # B-001 is user

    def test_version_constraint_in_label(self) -> None:
        tree = RegistryTree()
        spec = _spec(
            variants=[
                LanguageVariant(
                    language="python",
                    version_constraint=">=3.10",
                )
            ]
        )
        tree.populate([spec])

        lang_node = tree.root.children[0].children[0]
        assert ">=3.10" in str(lang_node.label)


class TestNodeDataTypes:
    def test_pattern_node_data(self) -> None:
        spec = _spec()
        data = PatternNodeData(spec=spec)
        assert data.spec is spec

    def test_language_node_data(self) -> None:
        spec = _spec()
        data = LanguageNodeData(spec=spec, language="python")
        assert data.language == "python"

    def test_framework_node_data(self) -> None:
        spec = _spec()
        data = FrameworkNodeData(spec=spec, language="python", framework="django")
        assert data.framework == "django"
