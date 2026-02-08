# Graph-IR Ecosystem Alignment Analysis

**Date**: 2026-02-05
**Status**: Design Phase - Recommendations for Future Integration
**Author**: Strategic Analysis

---

## Executive Summary

**Question**: Should ling join the Graph-IR ecosystem?

**Answer**:
- **v1.0 (Current)**: **No** - Insufficient alignment (17% compatibility score)
- **v2.0 (Sine)**: **Maybe** - Moderate alignment (47% compatibility score)
- **Recommendation**: Strategic partnership with phased integration based on demonstrated interop value

**Key Insight**: Sine's planned dependency graph analysis creates genuine architectural alignment with the Graph-IR ecosystem's core competency, but the Python/TypeScript technology divide and different philosophical approaches (lightweight vs comprehensive) suggest collaboration should be earned through demonstrated value, not forced prematurely.

---

## Background: The Graph-IR Ecosystem

The Graph-IR ecosystem is a suite of TypeScript/JavaScript tools built around a common Graph Intermediate Representation (JSON-based directed acyclic graphs):

### Core Repositories

| Repository | Purpose | Status |
|------------|---------|--------|
| **graph-ir** | Canonical IR specification (JSON Schema) | Complete |
| **graph-ir-tools** | Shared utilities, MCP server, agents | Complete |
| **coral** | Diagramming tool (DSL → visual, Phase 2+4) | Complete |
| **armada** | Code understanding MCP server (Phase 3) | Complete |

### Key Capabilities

- **Isomorphic transformations**: Lossless round-tripping between text, visual, and data
- **AI-native interface**: JSON format for LLM manipulation
- **Tree-sitter based**: Parsing for DSLs (Coral) and code (Armada)
- **MCP integration**: All components expose tools via Model Context Protocol

---

## Evaluation Framework

### Scoring Criteria (Weighted)

| Criterion | Weight | v1.0 Score | v2.0 Score (with Sine) |
|-----------|--------|------------|--------------------------------|
| **Core Alignment** (Graph-IR usage) | 30% | 0/5 | 3/5 |
| **Architectural Fit** (MCP/agents/skills) | 25% | 1/5 | 2/5 |
| **Technology Stack** (TypeScript) | 15% | 0/5 | 0/5 |
| **Problem Domain** (graph visualization) | 20% | 2/5 | 3/5 |
| **Ecosystem Value** (mutual benefit) | 5% | 1/5 | 2/5 |
| **Maintenance Fit** (quality standards) | 5% | 3/5 | 3/5 |
| **Overall Score** | 100% | **17%** | **47%** |

**Threshold for Integration**: 50% minimum

---

## ling v1.0: Current State Analysis

### What ling Does

```
Input:  .eslintrc.json, ruff.toml, prettier.config.js
        ↓
Process: Fetch upstream rule docs from GitHub
        ↓
Output:  Markdown/DOCX coding guidelines
```

**Core Value**: Documentation generation from linter configurations

**Technology**: Python 3.10+, 1,277 tests, mature (v1.0.0 released)

### Why v1.0 Doesn't Align

1. **No Graph Operations**: ling v1.0 is `Config File → Rule List → Documentation` with no graph structures
2. **Different Data Model**: Works with linter configurations, not directed acyclic graphs
3. **Technology Mismatch**: Python vs TypeScript ecosystem
4. **Different Architecture**: CLI-only vs MCP servers + agents + skills
5. **Different Problem**: Documentation drift vs graph visualization

**v1.0 Verdict**: Keep independent

---

## ling v2.0: Sine Changes Everything

### What Sine Adds

**"Sine"** is a planned feature (design phase, not implemented) for architectural guideline detection—rules that linters cannot catch:

```
Traditional Linters (First Shift)      Sine (Architecture)
───────────────────────────────────    ─────────────────────────────
• Syntax correctness                   • Structural correctness
• Style consistency                    • Dependency rules
• Type safety                          • Pattern requirements
• Auto-fixable                         • Engineering judgment

ESLint, Ruff, Prettier                 ling second-shift
```

### Three Detection Tiers

| Tier | Detection Type | Engine | Example |
|------|---------------|--------|---------|
| **1** | AST Context (Wrapper) | Semgrep | "HTTP calls must be inside circuit breaker" |
| **2** | Dependency Graph (Topology) | Built-in | "No circular imports", "Layer violations" |
| **3** | Control Flow (Reachability) | CodeQL (opt-in) | "No recursion in hot paths" |

**Key for Graph-IR**: **Tier 2** builds actual dependency graphs using tree-sitter.

### Tier 2 Architecture

```yaml
# Guideline definition
guidelines:
  - id: ARCH-003
    title: "No circular dependencies"
    check:
      type: topology
      rule: no_cycles
      scope: "src/**"
```

**Implementation (Planned)**:
1. Parse imports with tree-sitter (Python, TypeScript, C#)
2. Build directed graph of dependencies
3. Run graph algorithms (cycle detection, forbidden paths, layer violations)
4. Generate violation reports

**This is genuine graph work** - same domain as Graph-IR ecosystem.

---

## Why Sine Creates Alignment

### 1. Dependency Graph Analysis (Core Alignment +3)

Sine will:
- Build directed graphs of code dependencies
- Analyze graph topology (cycles, paths, layers)
- Export graph data structures

**Could use Graph-IR**: Dependency graphs are representable as Graph-IR nodes/edges.

### 2. Tree-sitter Overlap (Architectural Fit +1)

Both ecosystems use tree-sitter:
- **graph-ir-tools**: `tree-sitter-assistant` agent for grammar development
- **Coral**: Tree-sitter for Coral DSL parsing
- **Armada**: Tree-sitter for code indexing (Python, TypeScript, Go)
- **Sine**: Tree-sitter for import parsing (Python, TypeScript, C#)

**Synergy**: Could share grammar development expertise via `tree-sitter-assistant`.

### 3. Complementary Code Understanding (Domain +1)

```
┌────────────────────────────────────────────────────────┐
│               Code Understanding Spectrum               │
│                                                        │
│  Lightweight (CI)         │         Comprehensive      │
│  ling Sine        │         Armada             │
│  ├─ Import-only parsing   │   ├─ Full AST indexing    │
│  ├─ Dependency graph      │   ├─ Semantic relations   │
│  ├─ Architecture rules    │   ├─ Call graphs          │
│  ├─ Fast, in-memory       │   ├─ Memgraph + Qdrant    │
│  └─ Zero dependencies     │   └─ Deep queries         │
│                           │                           │
│  USE CASE:                │   USE CASE:               │
│  Quick CI checks          │   Architecture docs       │
│  Coding guidelines        │   Large codebase analysis │
└────────────────────────────────────────────────────────┘
```

**Different approaches, same problem space**: Understanding code structure and relationships.

### 4. Visualization Potential (Ecosystem Value +1)

```
Workflow:
1. ling second-shift --export-graph > deps.json
2. Convert deps.json → Graph-IR format
3. coral render → visual architecture diagram
```

**Use Case**: "Show me a visual diagram of our circular dependencies"

**Current State**: Sine produces text reports (design phase)

**Potential**: Export dependency graphs → Coral visualizes violations

---

## Why Integration Is Still Questionable

### 1. Technology Mismatch (Score: 0/5, unchanged)

| Technology | ling | Graph-IR Ecosystem |
|------------|------|-------------------|
| Language | Python 3.10+ | TypeScript/JavaScript |
| Build System | Hatch (Python) | npm/pnpm workspaces |
| Testing | pytest | Vitest/Jest |
| Package Manager | pip | npm/pnpm |

**Problem**: Integrating Python into TypeScript monorepo adds significant complexity:
- Separate build/test/release pipelines
- No code sharing between Python and TypeScript
- Cross-language coordination overhead

### 2. Different Philosophical Approaches

**ling Sine**:
- Lightweight, fast, CI-friendly
- "Accept 80% accuracy with regex" for import parsing
- Built-in, zero external dependencies
- Quick checks (< 30 seconds target)

**Armada**:
- Comprehensive, semantic, accurate
- Full AST indexing, vector embeddings
- Requires infrastructure (Memgraph, Qdrant)
- Deep analysis (slower, more thorough)

**Conflict**: ling explicitly chooses lightweight over comprehensive—opposite of Armada's philosophy.

### 3. Core Mission Remains Different

**ling's mission**: Documentation generation (config → docs)
- Sine is a **tool** for ling's documentation mission
- Dependency graphs are a means to an end (violation detection)
- Not becoming a pure graph tool

**Graph-IR ecosystem mission**: Graph visualization and code understanding
- Graphs are the primary artifact
- Multiple views of the same underlying IR

**Reality**: Even with Sine, ling is documentation-first, graphs-second.

### 4. Timeline: Premature

**Sine Status**: Design phase only, no implementation started

**Phases**:
- Phase 0: Schema definition
- Phase 1a: Semgrep orchestration
- Phase 1b: Graph engine (Python) ← **This is when to reevaluate**
- Phase 2: Multi-language expansion
- Phase 3: Baseline management
- Phase 4+: Deep integration

**Risk**: Deciding on integration before Phase 1b ships is premature—unclear if design will work as intended.

---

## Recommended Strategy: Tiered Collaboration

Instead of full integration, pursue a **strategic partnership model** with three phases:

### Phase 1: Independent Development with Awareness (Now)

**Status**: Sine in design, not implemented

**ling Actions**:
- [x] Design Sine with Graph-IR export in mind (future-proofing)
- [x] Use tree-sitter (already planned) for parsing
- [ ] Document graph format in IR-compatible way

**graph-ir-tools Actions**:
- [x] Add "Related Projects" section mentioning ling
- [ ] Document "dependency graph" as a supported Coral diagram type
- [ ] Provide `tree-sitter-assistant` examples for Python/TypeScript import parsing

**Documentation**:
- [x] Cross-reference docs (ling → graph-ir-tools, graph-ir-tools → ling)
- [x] Add this analysis to `ling/docs/research/`
- [x] Add ling reference to `ECOSYSTEM-DEVELOPMENT-PLAN.md`

### Phase 2: Loose Technical Integration (After Phase 1b)

**Trigger**: Sine Phase 1b ships (Python dependency graph engine working)

**Deliverables**:

1. **Export Format Compatibility**:
   ```bash
   ling second-shift --export-format=graph-ir > deps.json
   ```
   Exports dependency graph in Graph-IR format

2. **Coral Import Support**:
   ```bash
   coral import --from=ling deps.json
   coral render deps.json --type=dependency-graph
   ```
   Visualizes ling dependency graphs

3. **Armada Compatibility**:
   - Document how to combine Sine graphs with Armada's knowledge graph
   - Potential MCP tool: `import_dependency_graph(ling_output)`

4. **Shared Tool Development**:
   - Collaborate on tree-sitter grammar improvements
   - Share import resolution strategies
   - Cross-reference documentation

**Success Criteria**:
- Users can export from ling, import to Coral
- Visualization workflow documented and tested
- Evidence of teams using both tools together

### Phase 3: Deeper Integration (If Strong Demand)

**Trigger**:
- Sine reaches Phase 3 (multi-language support)
- Users explicitly request tighter integration
- Evidence that teams use both ecosystems together
- Clear value proposition for unified tooling

**Options to Consider**:

**Option A**: Keep separate, maximize interop
- ling remains Python, exports to Graph-IR
- Ecosystem imports via standard format
- Documentation-heavy integration

**Option B**: ling second-shift TypeScript rewrite
- Matches ecosystem technology
- Enables true code sharing
- High effort, only if clear value

**Option C**: Monorepo with Python subsystem
- Add ling as Python package in ecosystem
- Coordinate releases
- Accept cross-language complexity

**Decision Criteria**:
- User demand (surveys, GitHub issues)
- Technical friction (how painful is current interop?)
- Maintenance burden vs value delivered
- Strategic direction of both projects

---

## Technical Integration Specification

### Graph-IR Export Format (for Phase 2)

When Sine exports dependency graphs, use this mapping:

#### Node Types

```json
{
  "nodes": [
    {
      "id": "src.api.client",
      "symbol": "module",
      "variant": "python_module",
      "label": "src.api.client",
      "properties": {
        "path": "src/api/client.py",
        "language": "python"
      }
    }
  ]
}
```

**Node Symbols**:
- `module`: Python module, TypeScript file, C# namespace
- `package`: Python package, npm package, NuGet package
- `class`: Class definition (if granular)
- `function`: Function/method (if granular)

#### Edge Types

```json
{
  "edges": [
    {
      "id": "edge_1",
      "source": "src.api.client",
      "target": "src.data.models",
      "symbol": "imports",
      "label": "imports",
      "properties": {
        "import_type": "direct"
      }
    },
    {
      "id": "edge_2",
      "source": "src.data.export",
      "target": "src.ui.formatters",
      "symbol": "violates",
      "label": "violates ARCH-003",
      "properties": {
        "guideline_id": "ARCH-003",
        "severity": "error",
        "message": "Data layer cannot import UI layer"
      }
    }
  ]
}
```

**Edge Symbols**:
- `imports`: Direct import relationship
- `depends_on`: Dependency (more general than import)
- `violates`: Architecture rule violation
- `circular`: Circular dependency (annotated edge)

#### Metadata

```json
{
  "metadata": {
    "notation": "ling-dependency-graph",
    "generator": "ling-second-shift",
    "version": "2.0.0",
    "language": "python",
    "timestamp": "2026-02-05T10:30:00Z",
    "guideline_violations": 2
  }
}
```

### Coral Import Implementation

```typescript
// In Coral: packages/language/src/formats/ling-importer.ts

import { GraphIR } from '@graph-ir/types';
import { LingDependencyGraph } from './types';

export class LingImporter {
  import(graphIr: GraphIR): LingDependencyGraph {
    // Validate notation
    if (graphIr.metadata.notation !== 'ling-dependency-graph') {
      throw new Error('Invalid notation for ling import');
    }

    // Transform to Coral's internal format
    // Highlight violation edges in red
    // Show cycle paths differently
    return this.transform(graphIr);
  }
}
```

### Armada Integration

```typescript
// In Armada: packages/core/src/importers/ling-importer.ts

export class LingDependencyImporter {
  async importToKnowledgeGraph(
    lingGraph: GraphIR,
    projectId: string
  ): Promise<void> {
    // Import modules as nodes
    // Import dependencies as relationships
    // Tag violations for querying
    // Merge with existing code analysis
  }
}
```

---

## Decision Matrix

| If... | Then... | Timeline |
|-------|---------|----------|
| **Sine never implements** | Keep separate (status quo) | N/A |
| **Phase 1b ships + low overlap** | Loose collaboration (docs only) | Revisit annually |
| **Phase 1b ships + moderate overlap** | Technical integration (export/import) | 6 months after 1b |
| **Phase 3 ships + heavy overlap** | Reevaluate full integration | 12 months after Phase 3 |
| **Teams demand unified tooling** | Consider TypeScript rewrite | As needed |
| **Python/TS friction too high** | Abandon integration, keep references | As discovered |

---

## Evaluation Checklist (for Phase 2 Decision)

After Sine Phase 1b ships, evaluate these questions:

### User Demand
- [ ] Are teams actually using ling + Coral together?
- [ ] Are teams using ling + Armada together?
- [ ] How many GitHub issues request integration?
- [ ] Survey data on desired workflows

### Technical Compatibility
- [ ] Does Graph-IR export work smoothly from ling?
- [ ] Can Coral import and visualize ling graphs?
- [ ] Are there format compatibility issues?
- [ ] Is the workflow documented and easy?

### Value Proposition
- [ ] What problems does integration solve?
- [ ] Are there alternative solutions (e.g., third-party bridges)?
- [ ] Does integration justify the maintenance burden?
- [ ] Would users pay for/adopt integrated tooling?

### Technical Friction
- [ ] How painful is the Python/TypeScript boundary?
- [ ] Are there version coordination issues?
- [ ] How much effort is required for releases?
- [ ] Are there testing/CI complexities?

### Strategic Alignment
- [ ] Do both projects still have compatible missions?
- [ ] Are architectural philosophies converging or diverging?
- [ ] Is there overlap in maintainer/contributor base?
- [ ] Do communities want this integration?

**Scoring**: If >80% of questions are "yes" or "positive", proceed to Phase 3 planning. If <50%, keep at Phase 2 (interop only).

---

## Open Questions

### For ling Maintainers

1. **Sine Priority**: Is Sine definitively planned, or just exploratory?
2. **Graph Export**: Would `--export-format=graph-ir` be acceptable in design?
3. **Tree-sitter Adoption**: Confirmed that tree-sitter will be used for parsing?
4. **Collaboration Interest**: Is collaboration with graph-ir-tools desirable?

### For Graph-IR Ecosystem

1. **Dependency Graphs**: Should Coral formally support "dependency graph" as a diagram type?
2. **Python Integration**: Is there precedent for Python components in the TypeScript ecosystem?
3. **Armada Integration**: Would Armada benefit from ling's lightweight dependency analysis?
4. **Community Demand**: Do users want this integration?

### Technical Questions

1. **Graph Granularity**: Should ling export file-level, module-level, or class-level graphs?
2. **Violation Representation**: How should architecture violations be represented in Graph-IR?
3. **Circular Dependencies**: Special edge type, or annotation on normal edges?
4. **Performance**: Can Coral/Armada handle graphs with 1000+ nodes (large codebases)?

---

## References

### ling Documentation
- [Sine Design](./second-shift-design.md) - Full architectural spec
- [Project Status](../PROJECT-STATUS.md) - Current implementation status
- [Roadmap v2](./roadmap-version-2.md) - Engineering risk management vision

### Graph-IR Ecosystem Documentation
- [Ecosystem Development Plan](https://github.com/coreyt/graph-ir-tools/blob/main/ECOSYSTEM-DEVELOPMENT-PLAN.md)
- [Graph-IR Specification](https://github.com/coreyt/graph-ir)
- [Coral Documentation](https://github.com/coreyt/coral)
- [Armada Documentation](https://github.com/coreyt/armada)

### Related Tools
- [Semgrep](https://semgrep.dev) - AST-based code analysis (used by Sine Tier 1)
- [Tree-sitter](https://tree-sitter.github.io) - Parser generator (used by both ecosystems)
- [CodeQL](https://codeql.github.com) - Semantic code analysis (Sine Tier 3)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial analysis and recommendations |

---

## Conclusion

**Current Answer (2026-02-05)**:
- Keep ling independent
- Establish lightweight collaboration through documentation cross-references
- Design Sine with Graph-IR export compatibility in mind

**Future Answer (After Phase 1b)**:
- Implement technical integration (export/import)
- Reassess based on user demand and demonstrated value
- Decide on deeper integration only if strong evidence supports it

**The Key Insight**: Sine transforms ling from a pure documentation tool into a **code analysis tool with graph operations**—creating genuine alignment with the Graph-IR ecosystem. But timing, technology differences, and philosophical approaches mean integration should be **earned through proven interop value**, not assumed prematurely.

**Next Steps**:
1. ✅ Add cross-references to both projects' documentation
2. ✅ Create this analysis document
3. [ ] Monitor Sine implementation progress
4. [ ] Implement Phase 2 when Phase 1b ships
5. [ ] Gather user feedback on integration value
6. [ ] Reevaluate periodically based on decision matrix
