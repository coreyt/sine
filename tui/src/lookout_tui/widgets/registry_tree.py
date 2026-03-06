"""Registry tree widget — 3-level pattern/language/framework navigation."""

from __future__ import annotations

from dataclasses import dataclass

from lookout.models import PatternSpecFile
from textual.message import Message
from textual.widgets import Tree
from textual.widgets._tree import TreeNode


@dataclass(frozen=True)
class PatternNodeData:
    """Data attached to a pattern-level tree node."""

    spec: PatternSpecFile


@dataclass(frozen=True)
class LanguageNodeData:
    """Data attached to a language-level tree node."""

    spec: PatternSpecFile
    language: str


@dataclass(frozen=True)
class FrameworkNodeData:
    """Data attached to a framework-level tree node."""

    spec: PatternSpecFile
    language: str
    framework: str


NodeData = PatternNodeData | LanguageNodeData | FrameworkNodeData

_STATUS_ICONS = {
    "active": "✓",
    "draft": "~",
    "deprecated": "✗",
}


class RegistryTree(Tree[NodeData]):
    """Three-level tree: pattern > language > framework."""

    class NodeSelected(Message):
        """Emitted when a tree node is selected."""

        def __init__(self, node_data: NodeData) -> None:
            super().__init__()
            self.node_data = node_data

    def __init__(self, id: str | None = None) -> None:
        super().__init__("Registry", id=id)
        self._patterns: list[PatternSpecFile] = []

    def populate(
        self,
        patterns: list[PatternSpecFile],
        built_in_ids: set[str] | None = None,
    ) -> None:
        """Build the tree from a list of PatternSpecFile instances."""
        self._patterns = patterns
        built_in = built_in_ids or set()
        self.clear()
        self.root.expand()

        for spec in sorted(patterns, key=lambda s: s.pattern.id):
            p = spec.pattern
            status_icon = _STATUS_ICONS.get(p.status, "[?]")
            source_tag = " (built-in)" if p.id in built_in else ""
            pattern_node = self.root.add(
                f"{p.id} — {p.title} {status_icon}{source_tag}",
                data=PatternNodeData(spec=spec),
                expand=False,
            )

            if not p.variants:
                pattern_node.add_leaf("(no variants)", data=None)
            else:
                for variant in p.variants:
                    lang_label = variant.language
                    if variant.version_constraint:
                        lang_label += f" {variant.version_constraint}"

                    lang_node = pattern_node.add(
                        lang_label,
                        data=LanguageNodeData(spec=spec, language=variant.language),
                        expand=False,
                    )

                    # Generic variant leaf
                    generic_icon = "✓" if variant.generic else "✗"
                    lang_node.add_leaf(
                        f"generic {generic_icon}",
                        data=FrameworkNodeData(
                            spec=spec,
                            language=variant.language,
                            framework="generic",
                        ),
                    )

                    # Framework variant leaves
                    for fw in variant.frameworks:
                        fw_label = f"{fw.name} ✓"
                        lang_node.add_leaf(
                            fw_label,
                            data=FrameworkNodeData(
                                spec=spec,
                                language=variant.language,
                                framework=fw.name,
                            ),
                        )

    def on_tree_node_highlighted(
        self, event: Tree.NodeHighlighted[NodeData]
    ) -> None:
        """Post NodeSelected when the cursor moves."""
        if event.node.data is not None:
            self.post_message(self.NodeSelected(event.node.data))

    @property
    def patterns(self) -> list[PatternSpecFile]:
        return list(self._patterns)

    def selected_node_data(self) -> NodeData | None:
        """Return the data for the currently highlighted node."""
        node: TreeNode[NodeData] = self.cursor_node  # type: ignore[assignment]
        if node is not None:
            return node.data
        return None
