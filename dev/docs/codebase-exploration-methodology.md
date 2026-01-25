# Codebase Exploration & Pattern Discovery Methodology

## Executive Summary

This document provides a systematic methodology for:
1. **Exploring** an unfamiliar codebase
2. **Discovering** patterns, aspects, and anti-patterns
3. **Detecting** these patterns as expressed in code
4. **Persisting** findings in a queryable data structure

The approach is language-agnostic in methodology but produces language/framework-specific insights.

---

# Part 1: Codebase Exploration Methodology

## 1.1 The Exploration Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CODEBASE EXPLORATION PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1: RECONNAISSANCE                                                │
│  ────────────────────────                                               │
│  • Project structure analysis                                           │
│  • Configuration file discovery                                         │
│  • Dependency identification                                            │
│  • Technology stack detection                                           │
│                        │                                                │
│                        ▼                                                │
│  Phase 2: STRUCTURAL ANALYSIS                                           │
│  ───────────────────────────                                            │
│  • Module/namespace organization                                        │
│  • Class hierarchy mapping                                              │
│  • Interface inventory                                                  │
│  • Dependency graph construction                                        │
│                        │                                                │
│                        ▼                                                │
│  Phase 3: SEMANTIC ANALYSIS                                             │
│  ──────────────────────────                                             │
│  • Type relationship analysis                                           │
│  • Method signature patterns                                            │
│  • Data flow analysis                                                   │
│  • Control flow patterns                                                │
│                        │                                                │
│                        ▼                                                │
│  Phase 4: PATTERN RECOGNITION                                           │
│  ───────────────────────────                                            │
│  • Known pattern matching                                               │
│  • Cluster analysis (unknown patterns)                                  │
│  • Consistency analysis                                                 │
│  • Anomaly detection                                                    │
│                        │                                                │
│                        ▼                                                │
│  Phase 5: SYNTHESIS                                                     │
│  ──────────────────────                                                 │
│  • Pattern documentation                                                │
│  • Quality scoring                                                      │
│  • Recommendation generation                                            │
│  • Report compilation                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Phase 1: Reconnaissance

### Objective
Establish the technological context before analyzing code.

### Activities

#### 1.2.1 Project Structure Analysis
```
Questions to Answer:
├── What is the directory organization pattern?
│   ├── By layer? (Controllers/, Services/, Repositories/)
│   ├── By feature? (Users/, Orders/, Products/)
│   ├── By type? (Models/, Views/, Controllers/)
│   └── Hybrid?
│
├── Are there multiple projects/packages?
│   ├── Monorepo structure?
│   ├── Solution with multiple projects?
│   └── Workspaces (npm/yarn)?
│
└── What is the test organization?
    ├── Parallel structure (src/ → tests/)?
    ├── Colocated (Component.tsx + Component.test.tsx)?
    └── Separate test project?
```

**Implementation:**
```python
def analyze_project_structure(root_path: Path) -> ProjectStructure:
    """
    Scan directory tree and classify organization pattern.
    """
    structure = ProjectStructure()
    
    # Collect all directories
    dirs = [d for d in root_path.rglob('*') if d.is_dir()]
    
    # Classify by common patterns
    layer_indicators = ['controllers', 'services', 'repositories', 'models', 'views']
    feature_indicators = identify_domain_terms(dirs)  # e.g., 'users', 'orders'
    
    layer_score = sum(1 for d in dirs if d.name.lower() in layer_indicators)
    feature_score = len(feature_indicators)
    
    if layer_score > feature_score:
        structure.organization = OrganizationPattern.BY_LAYER
    elif feature_score > layer_score:
        structure.organization = OrganizationPattern.BY_FEATURE
    else:
        structure.organization = OrganizationPattern.HYBRID
    
    return structure
```

#### 1.2.2 Configuration File Discovery
```
Priority Configuration Files:

Language Detection:
├── C#:       *.sln, *.csproj, global.json
├── TypeScript: tsconfig.json, package.json
├── Python:   pyproject.toml, setup.py, requirements.txt
└── Java:     pom.xml, build.gradle

Framework Detection:
├── Angular:  angular.json, nx.json
├── React:    next.config.js, gatsby-config.js, vite.config.ts
├── ASP.NET:  appsettings.json, Program.cs with WebApplication
├── FastAPI:  main.py with FastAPI(), uvicorn in requirements
└── Django:   settings.py, manage.py

Build/Tool Configuration:
├── Linting:  .eslintrc, .pylintrc, .editorconfig
├── Testing:  jest.config.js, pytest.ini, xunit.runner.json
├── CI/CD:    .github/workflows/, azure-pipelines.yml, Jenkinsfile
└── Container: Dockerfile, docker-compose.yml
```

#### 1.2.3 Dependency Analysis
```python
def analyze_dependencies(project: Project) -> DependencyProfile:
    """
    Build a profile of external dependencies and what they indicate.
    """
    profile = DependencyProfile()
    
    # Load dependencies from appropriate file
    deps = load_dependencies(project)  # package.json, csproj, requirements.txt
    
    # Categorize dependencies
    for dep in deps:
        category = categorize_dependency(dep)
        profile.add(dep, category)
    
    # Infer patterns from dependencies
    if 'MediatR' in deps:
        profile.inferred_patterns.append('Mediator/CQRS')
    if 'Polly' in deps:
        profile.inferred_patterns.append('Resilience Patterns')
    if '@ngrx/store' in deps:
        profile.inferred_patterns.append('Redux/NgRx State Management')
    if 'rxjs' in deps:
        profile.inferred_patterns.append('Reactive Programming')
    
    return profile
```

### Reconnaissance Output
```yaml
reconnaissance_report:
  project:
    name: "MyApplication"
    root: "/path/to/project"
    
  languages:
    primary: "typescript"
    secondary: ["scss", "html"]
    
  frameworks:
    detected:
      - name: "angular"
        version: "17.0.0"
        confidence: 0.95
      - name: "ngrx"
        version: "17.0.0"
        confidence: 0.90
        
  structure:
    organization: "by_feature"
    test_pattern: "colocated"
    
  dependencies:
    count: 142
    categories:
      core: 12
      ui: 8
      state_management: 3
      testing: 15
      utilities: 24
      
  inferred_patterns:
    - "Reactive Programming (RxJS)"
    - "Redux State Management (NgRx)"
    - "Component-Based Architecture"
```

---

## 1.3 Phase 2: Structural Analysis

### Objective
Build a complete map of code organization and relationships.

### Activities

#### 1.3.1 Module/Namespace Mapping
```
Build hierarchical map of:

Namespaces/Modules
├── MyApp.Core
│   ├── MyApp.Core.Entities
│   ├── MyApp.Core.Interfaces
│   └── MyApp.Core.Services
├── MyApp.Infrastructure
│   ├── MyApp.Infrastructure.Data
│   └── MyApp.Infrastructure.External
└── MyApp.Web
    ├── MyApp.Web.Controllers
    └── MyApp.Web.ViewModels

Look for:
• Layering patterns (Core → Infrastructure → Web)
• Dependency direction (should flow inward)
• Module cohesion (related things together)
• Cross-cutting concerns (logging, auth across modules)
```

#### 1.3.2 Type Inventory
```python
def build_type_inventory(codebase: Codebase) -> TypeInventory:
    """
    Catalog all types with their characteristics.
    """
    inventory = TypeInventory()
    
    for code_unit in codebase.code_units:
        type_record = TypeRecord(
            name=code_unit.name,
            fully_qualified_name=code_unit.fully_qualified_name,
            kind=code_unit.kind,
            
            # Structural characteristics
            member_count=len(code_unit.members),
            method_count=len([m for m in code_unit.members if m.kind == MemberKind.Method]),
            property_count=len([m for m in code_unit.members if m.kind == MemberKind.Property]),
            
            # Relationship characteristics
            base_type_count=len(code_unit.base_types),
            interface_count=len(code_unit.implemented_interfaces),
            dependency_count=len(code_unit.dependencies),
            
            # Naming patterns
            name_suffix=extract_suffix(code_unit.name),  # "Repository", "Service", etc.
            name_pattern=classify_name(code_unit.name),
            
            # Location
            module=code_unit.module,
            file_path=code_unit.location.file_path,
        )
        
        inventory.add(type_record)
    
    return inventory
```

#### 1.3.3 Dependency Graph Construction
```
Build directed graph where:
- Nodes = Types (classes, interfaces, modules)
- Edges = Dependencies (inheritance, implementation, composition, usage)

Edge Types:
├── INHERITS:      Class → Base Class
├── IMPLEMENTS:    Class → Interface
├── DEPENDS_ON:    Class → Injected Dependency
├── USES:          Method → Called Type
├── CREATES:       Factory → Created Type
└── AGGREGATES:    Class → Composed Type

Graph Queries:
• Find cycles (circular dependencies)
• Calculate coupling metrics
• Identify hub types (many connections)
• Find orphan types (no connections)
```

```python
def build_dependency_graph(inventory: TypeInventory) -> DependencyGraph:
    """
    Construct a directed graph of type relationships.
    """
    graph = DependencyGraph()
    
    for type_record in inventory.types:
        # Add node
        graph.add_node(type_record.fully_qualified_name, {
            'kind': type_record.kind,
            'module': type_record.module,
        })
        
        # Add inheritance edges
        for base in type_record.base_types:
            graph.add_edge(
                type_record.fully_qualified_name,
                base.fully_qualified_name,
                EdgeType.INHERITS
            )
        
        # Add implementation edges
        for interface in type_record.interfaces:
            graph.add_edge(
                type_record.fully_qualified_name,
                interface.fully_qualified_name,
                EdgeType.IMPLEMENTS
            )
        
        # Add dependency edges
        for dep in type_record.dependencies:
            graph.add_edge(
                type_record.fully_qualified_name,
                dep.target.fully_qualified_name,
                EdgeType.DEPENDS_ON,
                {'injection_method': dep.injection_site.kind}
            )
    
    return graph
```

---

## 1.4 Phase 3: Semantic Analysis

### Objective
Understand the meaning and behavior of code beyond structure.

### Activities

#### 1.4.1 Method Signature Pattern Analysis
```
Analyze method signatures across the codebase:

Input:
├── Parameter types and counts
├── Generic type usage
├── Optional parameters
└── Cancellation token presence

Output:
├── Return type patterns
├── Task/Promise wrapping
├── Result type usage
└── Collection types

Naming:
├── Verb prefixes (Get, Find, Create, Update, Delete)
├── Async suffix
├── Handler suffix
└── Domain terminology
```

```python
def analyze_method_signatures(inventory: TypeInventory) -> SignaturePatterns:
    """
    Identify common method signature patterns across the codebase.
    """
    patterns = SignaturePatterns()
    
    all_methods = []
    for type_record in inventory.types:
        for member in type_record.members:
            if member.kind == MemberKind.Method:
                all_methods.append(MethodSignature(
                    name=member.name,
                    containing_type=type_record.name,
                    parameters=[p.type for p in member.parameters],
                    return_type=member.return_type,
                    is_async=member.is_async,
                ))
    
    # Group by signature shape
    signature_groups = group_by_signature_shape(all_methods)
    
    # Identify dominant patterns
    for shape, methods in signature_groups.items():
        if len(methods) >= PATTERN_THRESHOLD:
            patterns.add(SignaturePattern(
                shape=shape,
                occurrences=len(methods),
                examples=methods[:5],
                is_dominant=(len(methods) / len(all_methods)) > 0.1
            ))
    
    return patterns
```

#### 1.4.2 Data Flow Analysis
```
Track how data moves through the system:

Entry Points → Processing → Persistence → Response

For each entry point:
1. Identify input types
2. Trace transformations
3. Identify validation points
4. Track persistence calls
5. Map to output types

Look for:
• DTO/Entity boundaries
• Mapping patterns (AutoMapper, manual)
• Validation locations
• Transaction boundaries
```

#### 1.4.3 Annotation/Decorator Analysis
```
Catalog all annotations/attributes/decorators:

Framework Annotations:
├── Routing: [Route], [HttpGet], @GetMapping
├── DI: [Inject], @Injectable, @Autowired
├── Validation: [Required], @IsNotEmpty
└── ORM: [Table], [Column], @Entity

Custom Annotations:
├── Identify custom attributes
├── Analyze usage patterns
└── Infer intent from naming

Usage Patterns:
├── Which types are annotated?
├── Annotation combinations?
└── Missing expected annotations?
```

---

## 1.5 Phase 4: Pattern Recognition

### Objective
Identify both known and novel patterns in the codebase.

### Activities

#### 1.5.1 Known Pattern Matching
```
Apply pattern catalog against discovered types:

For each type in inventory:
    For each pattern in catalog:
        Calculate signal matches
        Calculate anti-signal violations
        Compute confidence score
        If confidence > threshold:
            Record pattern match

Handle overlapping patterns:
• Same type may match multiple patterns
• Rank by confidence
• Check for pattern conflicts
```

#### 1.5.2 Cluster Analysis for Unknown Patterns
```
Identify groups of similar code that may represent codebase-specific patterns:

1. Feature Extraction
   Extract features from each type:
   - Member counts and kinds
   - Dependency patterns
   - Naming conventions
   - Annotation usage
   - Method signature shapes

2. Similarity Calculation
   Calculate pairwise similarity between types
   using appropriate distance metric

3. Clustering
   Apply clustering algorithm (DBSCAN, hierarchical)
   to group similar types

4. Pattern Extraction
   For each significant cluster:
   - Identify common characteristics
   - Generate pattern definition
   - Validate against examples
```

```python
def discover_patterns(inventory: TypeInventory, known_patterns: PatternCatalog) -> List[DiscoveredPattern]:
    """
    Use clustering to discover codebase-specific patterns.
    """
    # Extract feature vectors
    features = []
    for type_record in inventory.types:
        vector = extract_feature_vector(type_record)
        features.append((type_record, vector))
    
    # Cluster similar types
    clusters = cluster_types(features, min_cluster_size=3)
    
    discovered = []
    for cluster in clusters:
        # Check if cluster matches known pattern
        known_match = match_to_known_pattern(cluster, known_patterns)
        
        if known_match:
            # This is a variant of a known pattern
            discovered.append(DiscoveredPattern(
                name=f"{known_match.name} (Variant)",
                is_novel=False,
                base_pattern=known_match,
                examples=cluster.members,
                local_variations=identify_variations(cluster, known_match)
            ))
        else:
            # This is a novel codebase-specific pattern
            discovered.append(DiscoveredPattern(
                name=generate_pattern_name(cluster),
                is_novel=True,
                signature=extract_pattern_signature(cluster),
                examples=cluster.members,
                confidence=cluster.cohesion_score
            ))
    
    return discovered
```

#### 1.5.3 Consistency Analysis
```
For each detected pattern:
1. Find all instances in codebase
2. Extract implementation details from each
3. Identify the "majority approach"
4. Flag deviations from majority
5. Classify deviations:
   - Intentional variant
   - Evolution (old vs new style)
   - Inconsistency (potential issue)
```

#### 1.5.4 Anti-Pattern Detection
```
Look for known anti-patterns:

Structural Anti-Patterns:
├── God Class: Too many responsibilities
├── Feature Envy: Uses others' data more than own
├── Data Class: No behavior, just data
├── Shotgun Surgery: Changes require many edits
└── Parallel Inheritance: Matching hierarchies

Dependency Anti-Patterns:
├── Circular Dependencies: A → B → A
├── Service Locator: Runtime resolution
├── Inappropriate Intimacy: Too much coupling
└── Middle Man: Delegates everything

Implementation Anti-Patterns:
├── Primitive Obsession: Strings for everything
├── Magic Numbers: Unexplained literals
├── Long Method: Too many lines
└── Long Parameter List: Too many params
```

---

## 1.6 Phase 5: Synthesis

### Objective
Compile findings into actionable insights.

### Activities

#### 1.6.1 Pattern Documentation
```
For each detected pattern:
- Name and description
- All instances found
- Confidence score per instance
- Consistency score across instances
- Variations observed
- Recommendations
```

#### 1.6.2 Quality Scoring
```
Calculate composite quality score:

Score Components:
├── Pattern Consistency (30%)
│   How consistently are patterns applied?
│
├── Anti-Pattern Avoidance (25%)
│   How many anti-patterns detected?
│
├── Structural Quality (25%)
│   Coupling, cohesion, complexity metrics
│
└── Best Practice Adherence (20%)
    Following language/framework conventions
```

#### 1.6.3 Recommendation Generation
```python
def generate_recommendations(analysis: AnalysisResult) -> List[Recommendation]:
    """
    Generate prioritized recommendations based on findings.
    """
    recommendations = []
    
    # High priority: Anti-patterns
    for anti_pattern in analysis.anti_patterns:
        recommendations.append(Recommendation(
            priority=Priority.HIGH,
            category="Anti-Pattern",
            title=f"Refactor {anti_pattern.name}",
            description=anti_pattern.description,
            affected=anti_pattern.locations,
            effort=estimate_effort(anti_pattern),
            impact=anti_pattern.severity
        ))
    
    # Medium priority: Inconsistencies
    for inconsistency in analysis.inconsistencies:
        recommendations.append(Recommendation(
            priority=Priority.MEDIUM,
            category="Consistency",
            title=f"Standardize {inconsistency.pattern_name}",
            description=f"Align {len(inconsistency.locations)} implementations",
            affected=inconsistency.locations,
            effort=Effort.LOW,
            impact=Impact.MAINTAINABILITY
        ))
    
    # Low priority: Best practice improvements
    for improvement in analysis.best_practice_gaps:
        recommendations.append(Recommendation(
            priority=Priority.LOW,
            category="Best Practice",
            title=improvement.title,
            description=improvement.description,
            affected=improvement.locations,
            effort=improvement.effort,
            impact=Impact.CODE_QUALITY
        ))
    
    return sorted(recommendations, key=lambda r: r.priority)
```

---

# Part 2: Discovering New Patterns and Aspects

## 2.1 What Is a "Pattern" in This Context?

```
A Pattern consists of:

┌─────────────────────────────────────────────────────────────┐
│                     PATTERN DEFINITION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Identity                                                   │
│  ├── Name: What is it called?                              │
│  ├── Category: Creational/Structural/Behavioral/etc.       │
│  └── Scope: Universal/Language/Framework/Codebase          │
│                                                             │
│  Intent                                                     │
│  ├── Problem: What problem does it solve?                  │
│  ├── Context: When should it be used?                      │
│  └── Forces: What tensions does it balance?                │
│                                                             │
│  Structure                                                  │
│  ├── Participants: What types are involved?                │
│  ├── Relationships: How do they relate?                    │
│  └── Variations: What forms can it take?                   │
│                                                             │
│  Detection                                                  │
│  ├── Signals: Indicators of presence                       │
│  ├── Anti-Signals: Indicators of absence/misuse           │
│  └── Confidence: How certain can we be?                    │
│                                                             │
│  Quality                                                    │
│  ├── Consistency Rules: How should it be applied?         │
│  └── Anti-Patterns: What should be avoided?               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Pattern Discovery Process

### Step 1: Observation
```
Collect observations about code:

Structural Observations:
- "Several classes have names ending in 'Repository'"
- "These classes all depend on DbContext"
- "They all have similar methods: GetById, Add, Update, Delete"

Behavioral Observations:
- "All async methods accept CancellationToken"
- "Return types are wrapped in Result<T>"
- "Validation happens before business logic"

Convention Observations:
- "Services are registered with Scoped lifetime"
- "Controllers don't have business logic"
- "DTOs are used at API boundaries"
```

### Step 2: Abstraction
```
Generalize observations into pattern characteristics:

From Observations:
"Several classes have names ending in 'Repository'"
"These classes all depend on DbContext"
"They all have similar methods"

Extract Signals:
├── Naming: Class name ends with "Repository"
├── Dependency: Constructor depends on DbContext
├── Methods: Has CRUD-style method signatures
└── Interface: Implements IRepository<T> or similar

Define Pattern:
Name: Repository Pattern
Signals: [naming, dependency, methods, interface]
Anti-Signals: [business logic, UI dependencies]
```

### Step 3: Validation
```
Test pattern definition against codebase:

1. Find all potential matches
2. Calculate confidence for each
3. Review false positives (high confidence, not actually pattern)
4. Review false negatives (low confidence, actually is pattern)
5. Adjust signals and weights
6. Iterate until stable
```

### Step 4: Documentation
```yaml
# New pattern definition
pattern:
  name: ResultWrapper
  scope: codebase_specific
  category: behavioral
  
  description: |
    All service methods return Result<T> wrapper that indicates
    success/failure without exceptions for expected failures.
  
  signals:
    - name: ReturnsResult
      weight: 0.4
      detector: ReturnTypeMatch
      config:
        pattern: "Result<*>"
    
    - name: NoExceptionThrow
      weight: 0.3
      detector: MethodBodyAnalysis
      config:
        forbidden: "throw new.*Exception"
    
    - name: ServiceMethod
      weight: 0.2
      detector: ContainingType
      config:
        type_pattern: "*Service"
    
    - name: PublicMethod
      weight: 0.1
      detector: Visibility
      config:
        visibility: "public"
  
  discovered_from:
    date: "2024-01-15"
    sample_size: 47
    confidence: 0.89
```

## 2.3 Aspect Discovery

### What Is an "Aspect"?
```
Aspects are cross-cutting concerns that span multiple patterns/types:

Examples:
├── Error Handling: How errors are managed throughout
├── Logging: Where and how logging occurs
├── Authentication: How auth is enforced
├── Validation: Where input is validated
├── Transactions: How transaction boundaries work
├── Caching: Where and how caching is applied
└── Observability: Metrics, tracing, monitoring
```

### Aspect Detection Methodology
```
1. Identify Cross-Cutting Code
   - Find code that appears in many places
   - Look for decorator/attribute patterns
   - Analyze middleware/filter chains

2. Classify Aspect Type
   - Security aspects
   - Performance aspects
   - Reliability aspects
   - Observability aspects

3. Map Aspect Implementation
   - How is it implemented? (decorators, middleware, AOP)
   - Where is it applied?
   - Is application consistent?

4. Assess Aspect Health
   - Complete coverage?
   - Consistent implementation?
   - Appropriate placement?
```

```python
def discover_aspects(analysis: AnalysisResult) -> List[Aspect]:
    """
    Identify cross-cutting concerns in the codebase.
    """
    aspects = []
    
    # Logging aspect
    logging_calls = find_method_calls(analysis, patterns=['_logger.*', 'Log.*', 'console.log'])
    if logging_calls:
        aspects.append(Aspect(
            name="Logging",
            implementation=classify_logging_impl(logging_calls),
            coverage=calculate_coverage(logging_calls, analysis.types),
            consistency=assess_consistency(logging_calls),
            locations=logging_calls
        ))
    
    # Validation aspect
    validation_markers = find_annotations(analysis, patterns=['Validate*', 'Valid', 'Required'])
    validation_calls = find_method_calls(analysis, patterns=['Validate', 'IsValid'])
    if validation_markers or validation_calls:
        aspects.append(Aspect(
            name="Validation",
            implementation=classify_validation_impl(validation_markers, validation_calls),
            coverage=calculate_validation_coverage(analysis),
            consistency=assess_validation_consistency(analysis),
            locations=validation_markers + validation_calls
        ))
    
    # Transaction aspect
    transaction_markers = find_annotations(analysis, patterns=['Transactional', 'Transaction'])
    transaction_calls = find_method_calls(analysis, patterns=['BeginTransaction', 'Commit', 'Rollback'])
    if transaction_markers or transaction_calls:
        aspects.append(Aspect(
            name="Transactions",
            implementation=classify_transaction_impl(transaction_markers, transaction_calls),
            boundaries=identify_transaction_boundaries(analysis),
            consistency=assess_transaction_consistency(analysis)
        ))
    
    return aspects
```

## 2.4 Anti-Pattern Discovery

### Process
```
1. Define Quality Thresholds
   - Maximum method length
   - Maximum class size
   - Maximum dependency count
   - Maximum complexity

2. Find Violations
   - Scan for threshold violations
   - Identify outliers in metrics

3. Classify Violations
   - Map to known anti-patterns
   - Document unknown violations as potential new anti-patterns

4. Assess Impact
   - How severe is this violation?
   - What is the maintenance impact?
   - Is it isolated or systemic?
```

### Discovery Heuristics
```
God Class Indicators:
├── Method count > 20
├── Line count > 500
├── Dependency count > 10
├── Multiple unrelated responsibilities
└── Low cohesion score

Feature Envy Indicators:
├── Method accesses other class more than own
├── Many getter calls on other objects
├── Chains of method calls (a.b.c.d())
└── Would be simpler if moved

Data Class Indicators:
├── Only getters/setters
├── No methods with logic
├── All fields public or have accessors
└── Used by many other classes

Inappropriate Intimacy:
├── Bidirectional dependencies
├── Accessing private/internal members
├── Knowledge of implementation details
└── Tight coupling between specific classes
```

---

# Part 3: Pattern Expression in Code

## 3.1 How Patterns Manifest

```
Pattern manifestation varies by:

Language:
├── C#: Interfaces, classes, attributes, async/await
├── TypeScript: Interfaces, classes, decorators, types
├── Python: Protocols, ABCs, decorators, duck typing
└── JavaScript: Prototypes, closures, modules

Framework:
├── Angular: Decorators, modules, services, observables
├── React: Hooks, components, context, props
├── ASP.NET: Controllers, middleware, DI, attributes
└── FastAPI: Decorators, dependencies, Pydantic models

Maturity:
├── Textbook: Exact match to pattern definition
├── Adapted: Modified for specific context
├── Evolved: Changed over time, mixed styles
└── Degraded: Original intent lost
```

## 3.2 Signal Types for Detection

```
┌─────────────────────────────────────────────────────────────┐
│                     SIGNAL TAXONOMY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STRUCTURAL SIGNALS                                         │
│  ├── Type Relationships                                     │
│  │   ├── Inheritance (extends, inherits)                   │
│  │   ├── Implementation (implements)                        │
│  │   └── Composition (has-a, contains)                     │
│  │                                                          │
│  ├── Member Characteristics                                 │
│  │   ├── Method count and signatures                       │
│  │   ├── Property count and types                          │
│  │   └── Field visibility                                  │
│  │                                                          │
│  └── Generic Usage                                          │
│      ├── Type parameters                                   │
│      └── Constraints                                        │
│                                                             │
│  BEHAVIORAL SIGNALS                                         │
│  ├── Method Body Patterns                                   │
│  │   ├── Delegation (calls another method)                 │
│  │   ├── Creation (instantiates objects)                   │
│  │   └── Transformation (maps data)                        │
│  │                                                          │
│  ├── Control Flow                                           │
│  │   ├── Conditional complexity                            │
│  │   ├── Loop patterns                                     │
│  │   └── Exception handling                                │
│  │                                                          │
│  └── Data Flow                                              │
│      ├── Input/output mapping                              │
│      └── State mutations                                    │
│                                                             │
│  CONVENTION SIGNALS                                         │
│  ├── Naming Patterns                                        │
│  │   ├── Prefix (I for interface)                          │
│  │   ├── Suffix (Repository, Service, Factory)             │
│  │   └── Case (PascalCase, camelCase)                      │
│  │                                                          │
│  ├── Annotation/Decorator Presence                          │
│  │   ├── Framework annotations                             │
│  │   └── Custom annotations                                │
│  │                                                          │
│  └── File/Directory Placement                               │
│      ├── Layer-based location                              │
│      └── Feature-based location                            │
│                                                             │
│  DEPENDENCY SIGNALS                                         │
│  ├── Constructor Parameters                                 │
│  │   ├── Interface dependencies                            │
│  │   ├── Concrete dependencies                             │
│  │   └── Configuration dependencies                        │
│  │                                                          │
│  ├── Import/Using Statements                                │
│  │   ├── Framework imports                                 │
│  │   └── Library imports                                   │
│  │                                                          │
│  └── Runtime Dependencies                                   │
│      ├── Service locator calls                             │
│      └── Factory usage                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3.3 Confidence Calculation

```python
def calculate_pattern_confidence(
    signals: List[Signal],
    anti_signals: List[Signal],
    language: Language
) -> float:
    """
    Calculate confidence score for pattern match.
    """
    # Sum positive signals
    positive_score = 0.0
    for signal in signals:
        if signal.present:
            # Adjust weight based on language
            adjusted_weight = adjust_for_language(signal.weight, signal.type, language)
            positive_score += adjusted_weight
    
    # Sum negative signals (anti-patterns)
    negative_score = 0.0
    for anti in anti_signals:
        if anti.present:
            negative_score += abs(anti.weight)
    
    # Calculate raw confidence
    raw_confidence = positive_score - negative_score
    
    # Normalize to 0-1 range
    normalized = max(0.0, min(1.0, raw_confidence))
    
    # Apply language-specific adjustment
    # (lower confidence for dynamic languages)
    language_factor = get_language_confidence_factor(language)
    
    return normalized * language_factor


def adjust_for_language(base_weight: float, signal_type: SignalType, language: Language) -> float:
    """
    Adjust signal weight based on language capabilities.
    """
    adjustments = {
        Language.CSharp: {
            SignalType.TYPE_RELATIONSHIP: 1.0,
            SignalType.INTERFACE_IMPLEMENTATION: 1.0,
            SignalType.NAMING_CONVENTION: 0.8,
        },
        Language.TypeScript: {
            SignalType.TYPE_RELATIONSHIP: 0.95,
            SignalType.INTERFACE_IMPLEMENTATION: 0.9,
            SignalType.NAMING_CONVENTION: 0.85,
        },
        Language.Python: {
            SignalType.TYPE_RELATIONSHIP: 0.6,
            SignalType.INTERFACE_IMPLEMENTATION: 0.5,  # Protocols are optional
            SignalType.NAMING_CONVENTION: 1.2,  # More important in Python
        },
    }
    
    factor = adjustments.get(language, {}).get(signal_type, 1.0)
    return base_weight * factor
```

---

# Part 4: Data Model for Findings

## 4.1 Design Considerations

```
Requirements:
├── Store hierarchical data (project → modules → types → members)
├── Capture relationships (dependencies, inheritance, patterns)
├── Support flexible queries (find all Repositories, find inconsistencies)
├── Handle evolution (track changes over time)
├── Scale to large codebases (millions of lines)
└── Support multiple analysis runs

Options:
├── Relational (PostgreSQL): Good for structured queries, reporting
├── Document (MongoDB): Good for flexible schema, nested data
├── Graph (Neo4j): Good for relationship traversal, pattern matching
└── Hybrid: Combine strengths of multiple approaches
```

## 4.2 Recommended Approach: Hybrid Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐     ┌─────────────────────────────────────┐  │
│  │   GRAPH DATABASE    │     │        DOCUMENT DATABASE            │  │
│  │      (Neo4j)        │     │          (MongoDB)                  │  │
│  │                     │     │                                     │  │
│  │  • Type nodes       │     │  • Full code unit details          │  │
│  │  • Relationship     │     │  • Pattern match details           │  │
│  │    edges            │     │  • Analysis results                │  │
│  │  • Pattern          │     │  • Configuration                   │  │
│  │    instances        │     │                                     │  │
│  │                     │     │                                     │  │
│  │  Good for:          │     │  Good for:                         │  │
│  │  - Path queries     │     │  - Flexible schema                 │  │
│  │  - Dependency       │     │  - Nested data                     │  │
│  │    analysis         │     │  - Full-text search                │  │
│  │  - Cycle detection  │     │  - Evolution tracking              │  │
│  └─────────────────────┘     └─────────────────────────────────────┘  │
│              │                               │                         │
│              └───────────────┬───────────────┘                         │
│                              │                                         │
│                              ▼                                         │
│               ┌─────────────────────────────┐                         │
│               │   RELATIONAL DATABASE       │                         │
│               │      (PostgreSQL)           │                         │
│               │                             │                         │
│               │  • Metrics time series      │                         │
│               │  • Aggregated statistics    │                         │
│               │  • Reporting queries        │                         │
│               │  • User management          │                         │
│               │                             │                         │
│               │  Good for:                  │                         │
│               │  - Complex aggregations     │                         │
│               │  - Trend analysis           │                         │
│               │  - Dashboards               │                         │
│               └─────────────────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4.3 Graph Database Schema (Neo4j)

```cypher
// NODE TYPES

// Project node - root of analysis
CREATE (p:Project {
    id: "uuid",
    name: "MyApplication",
    path: "/path/to/project",
    language: "csharp",
    frameworks: ["aspnetcore", "efcore"],
    analyzed_at: datetime()
})

// Module/Namespace node
CREATE (m:Module {
    id: "uuid",
    name: "MyApp.Core.Services",
    path: "src/Core/Services",
    type: "namespace"  // or "module", "package"
})

// Type node (class, interface, etc.)
CREATE (t:Type {
    id: "uuid",
    name: "CustomerRepository",
    fully_qualified_name: "MyApp.Infrastructure.CustomerRepository",
    kind: "class",  // class, interface, abstract, enum
    visibility: "public",
    is_abstract: false,
    is_generic: true,
    generic_parameters: ["T"],
    line_count: 150,
    member_count: 12,
    complexity: 8.5
})

// Member node (method, property, field)
CREATE (mem:Member {
    id: "uuid",
    name: "GetByIdAsync",
    kind: "method",
    visibility: "public",
    is_static: false,
    is_async: true,
    return_type: "Task<Customer?>",
    parameters: ["Guid id", "CancellationToken ct"],
    line_count: 5,
    complexity: 2
})

// Pattern node (pattern definition)
CREATE (pat:Pattern {
    id: "uuid",
    name: "Repository",
    category: "architectural",
    scope: "universal",
    description: "Data access abstraction"
})

// PatternInstance node (detected pattern)
CREATE (pi:PatternInstance {
    id: "uuid",
    confidence: 0.92,
    detected_at: datetime(),
    signals_matched: ["interface_impl", "crud_methods", "db_dependency"],
    signals_violated: []
})

// Aspect node (cross-cutting concern)
CREATE (a:Aspect {
    id: "uuid",
    name: "Logging",
    implementation: "ILogger injection",
    coverage: 0.85
})

// AntiPattern node
CREATE (ap:AntiPattern {
    id: "uuid",
    name: "GodClass",
    severity: "high",
    description: "Class has too many responsibilities"
})

// RELATIONSHIP TYPES

// Structural relationships
(p:Project)-[:CONTAINS]->(m:Module)
(m:Module)-[:CONTAINS]->(t:Type)
(t:Type)-[:HAS_MEMBER]->(mem:Member)

// Type relationships
(t:Type)-[:EXTENDS]->(t2:Type)
(t:Type)-[:IMPLEMENTS]->(i:Type {kind: "interface"})
(t:Type)-[:DEPENDS_ON {
    injection_method: "constructor",
    is_optional: false
}]->(t2:Type)

// Pattern relationships
(t:Type)-[:MATCHES {confidence: 0.92}]->(pi:PatternInstance)
(pi:PatternInstance)-[:INSTANCE_OF]->(pat:Pattern)
(pat:Pattern)-[:RELATED_TO]->(pat2:Pattern)

// Aspect relationships
(t:Type)-[:USES_ASPECT {
    implementation: "ILogger field",
    location: "constructor"
}]->(a:Aspect)

// Anti-pattern relationships
(t:Type)-[:EXHIBITS {
    severity: "high",
    metrics: {method_count: 45, line_count: 1200}
}]->(ap:AntiPattern)

// Analysis relationships
(p:Project)-[:ANALYZED_IN]->(ar:AnalysisRun {
    id: "uuid",
    timestamp: datetime(),
    version: "1.0.0"
})
```

### Example Graph Queries

```cypher
// Find all types that implement Repository pattern with high confidence
MATCH (t:Type)-[m:MATCHES]->(pi:PatternInstance)-[:INSTANCE_OF]->(p:Pattern {name: "Repository"})
WHERE m.confidence > 0.8
RETURN t.name, t.fully_qualified_name, m.confidence
ORDER BY m.confidence DESC

// Find circular dependencies
MATCH path = (t1:Type)-[:DEPENDS_ON*2..10]->(t1)
RETURN path

// Find all God Classes and their dependencies
MATCH (t:Type)-[:EXHIBITS]->(ap:AntiPattern {name: "GodClass"})
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Type)
RETURN t.name, t.line_count, t.member_count, collect(dep.name) as dependencies

// Find inconsistent pattern implementations
MATCH (t1:Type)-[:MATCHES]->(pi1:PatternInstance)-[:INSTANCE_OF]->(p:Pattern)
MATCH (t2:Type)-[:MATCHES]->(pi2:PatternInstance)-[:INSTANCE_OF]->(p)
WHERE t1 <> t2 
  AND pi1.signals_matched <> pi2.signals_matched
RETURN p.name, t1.name, pi1.signals_matched, t2.name, pi2.signals_matched

// Calculate pattern adoption across modules
MATCH (m:Module)-[:CONTAINS]->(t:Type)-[:MATCHES]->(pi:PatternInstance)-[:INSTANCE_OF]->(p:Pattern)
WITH m, p, count(t) as pattern_count
RETURN m.name, p.name, pattern_count
ORDER BY m.name, pattern_count DESC
```

## 4.4 Document Database Schema (MongoDB)

```javascript
// Collection: projects
{
    "_id": ObjectId("..."),
    "name": "MyApplication",
    "path": "/path/to/project",
    "analyzed_at": ISODate("2024-01-15T10:30:00Z"),
    
    "technology_stack": {
        "languages": [
            {"name": "csharp", "version": "12.0", "is_primary": true},
            {"name": "sql", "version": null, "is_primary": false}
        ],
        "frameworks": [
            {"name": "aspnetcore", "version": "8.0.0"},
            {"name": "efcore", "version": "8.0.0"}
        ],
        "tools": [
            {"name": "docker", "version": "24.0"},
            {"name": "github-actions", "version": null}
        ]
    },
    
    "structure": {
        "organization_pattern": "by_feature",
        "test_pattern": "parallel",
        "module_count": 12,
        "type_count": 345,
        "line_count": 45000
    },
    
    "quality_score": {
        "overall": 82,
        "components": {
            "pattern_consistency": 88,
            "anti_pattern_avoidance": 75,
            "structural_quality": 85,
            "best_practice_adherence": 80
        }
    }
}

// Collection: code_units
{
    "_id": ObjectId("..."),
    "project_id": ObjectId("..."),
    "analysis_run_id": ObjectId("..."),
    
    "identity": {
        "name": "CustomerRepository",
        "fully_qualified_name": "MyApp.Infrastructure.Data.CustomerRepository",
        "kind": "class",
        "language": "csharp"
    },
    
    "location": {
        "file_path": "src/Infrastructure/Data/CustomerRepository.cs",
        "start_line": 15,
        "end_line": 165,
        "module": "MyApp.Infrastructure"
    },
    
    "structure": {
        "visibility": "public",
        "is_abstract": false,
        "is_sealed": false,
        "is_partial": false,
        "generic_parameters": [
            {"name": "TEntity", "constraints": ["class", "IEntity"]}
        ]
    },
    
    "members": [
        {
            "name": "GetByIdAsync",
            "kind": "method",
            "visibility": "public",
            "is_async": true,
            "return_type": {
                "name": "Task",
                "generic_arguments": [{"name": "TEntity", "is_nullable": true}]
            },
            "parameters": [
                {"name": "id", "type": "Guid", "is_optional": false},
                {"name": "cancellationToken", "type": "CancellationToken", "is_optional": true}
            ],
            "metrics": {
                "line_count": 8,
                "cyclomatic_complexity": 2,
                "cognitive_complexity": 1
            }
        }
        // ... more members
    ],
    
    "relationships": {
        "base_types": [
            {"name": "RepositoryBase", "fully_qualified_name": "MyApp.Infrastructure.Data.RepositoryBase"}
        ],
        "implemented_interfaces": [
            {"name": "IRepository", "fully_qualified_name": "MyApp.Core.Interfaces.IRepository`1"}
        ],
        "dependencies": [
            {
                "target": "AppDbContext",
                "target_fqn": "MyApp.Infrastructure.Data.AppDbContext",
                "kind": "constructor",
                "is_optional": false
            }
        ]
    },
    
    "annotations": [
        {"name": "Injectable", "arguments": {"lifetime": "scoped"}}
    ],
    
    "metrics": {
        "line_count": 150,
        "member_count": 12,
        "public_member_count": 8,
        "cyclomatic_complexity": 15,
        "maintainability_index": 72,
        "coupling_afferent": 5,
        "coupling_efferent": 3,
        "instability": 0.375
    },
    
    "pattern_matches": [
        {
            "pattern_name": "Repository",
            "pattern_id": "uuid",
            "confidence": 0.92,
            "signals_matched": [
                {"name": "implements_repository_interface", "weight": 0.25, "evidence": "Implements IRepository<TEntity>"},
                {"name": "has_crud_methods", "weight": 0.20, "evidence": "GetByIdAsync, AddAsync, UpdateAsync, DeleteAsync"},
                {"name": "db_context_dependency", "weight": 0.25, "evidence": "Constructor depends on AppDbContext"}
            ],
            "signals_violated": [],
            "variations": ["generic_implementation", "async_methods"]
        }
    ],
    
    "anti_patterns": [],
    
    "aspects": [
        {
            "name": "Logging",
            "present": true,
            "implementation": "ILogger<CustomerRepository> injection"
        },
        {
            "name": "Transactions",
            "present": false,
            "note": "Transactions handled at service layer"
        }
    ]
}

// Collection: analysis_runs
{
    "_id": ObjectId("..."),
    "project_id": ObjectId("..."),
    "started_at": ISODate("2024-01-15T10:30:00Z"),
    "completed_at": ISODate("2024-01-15T10:35:00Z"),
    "version": "1.0.0",
    
    "configuration": {
        "pattern_catalog_version": "2024.1",
        "confidence_threshold": 0.65,
        "include_patterns": ["**/*.cs"],
        "exclude_patterns": ["**/obj/**", "**/bin/**"]
    },
    
    "summary": {
        "types_analyzed": 345,
        "patterns_detected": 156,
        "anti_patterns_detected": 12,
        "inconsistencies_found": 8,
        "quality_score": 82
    },
    
    "pattern_summary": [
        {"pattern": "Repository", "count": 15, "avg_confidence": 0.88},
        {"pattern": "Service", "count": 28, "avg_confidence": 0.91},
        {"pattern": "Factory", "count": 5, "avg_confidence": 0.76}
    ],
    
    "anti_pattern_summary": [
        {"anti_pattern": "GodClass", "count": 2, "severity": "high"},
        {"anti_pattern": "ServiceLocator", "count": 5, "severity": "medium"}
    ],
    
    "recommendations": [
        {
            "priority": "high",
            "category": "anti_pattern",
            "title": "Refactor UserService (God Class)",
            "description": "UserService has 45 methods and 1200 lines",
            "affected_types": ["MyApp.Core.Services.UserService"],
            "estimated_effort": "large"
        }
    ]
}

// Collection: pattern_catalog
{
    "_id": ObjectId("..."),
    "name": "Repository",
    "category": "architectural",
    "scope": "universal",
    "version": "1.0.0",
    
    "description": "Mediates between domain and data mapping layers",
    
    "signals": [
        {
            "name": "implements_repository_interface",
            "weight": 0.25,
            "detector": "interface_implementation",
            "config": {"patterns": ["IRepository*", "*Repository"]}
        },
        {
            "name": "has_crud_methods",
            "weight": 0.20,
            "detector": "method_signature_match",
            "config": {"patterns": ["Get*", "Find*", "Add*", "Update*", "Delete*"]}
        }
    ],
    
    "anti_signals": [
        {
            "name": "contains_business_logic",
            "weight": -0.30,
            "detector": "complexity_threshold",
            "config": {"max_cyclomatic": 8}
        }
    ],
    
    "language_variants": {
        "csharp": {
            "additional_signals": [
                {"name": "async_methods", "weight": 0.10}
            ]
        },
        "python": {
            "weight_adjustments": {
                "implements_repository_interface": 0.15
            }
        }
    },
    
    "examples": {
        "good": ["...code example..."],
        "bad": ["...code example..."]
    },
    
    "related_patterns": ["UnitOfWork", "Specification", "GenericRepository"]
}
```

## 4.5 Relational Database Schema (PostgreSQL)

```sql
-- Core tables for aggregated metrics and reporting

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    primary_language VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis runs
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    version VARCHAR(20),
    config JSONB,
    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Metrics snapshots (time series data)
CREATE TABLE metrics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    dimensions JSONB, -- {module: "...", pattern: "..."}
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

CREATE INDEX idx_metrics_name_time ON metrics_snapshots(metric_name, recorded_at);
CREATE INDEX idx_metrics_dimensions ON metrics_snapshots USING GIN(dimensions);

-- Pattern statistics
CREATE TABLE pattern_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    pattern_name VARCHAR(100) NOT NULL,
    occurrence_count INTEGER,
    avg_confidence DECIMAL(5,4),
    min_confidence DECIMAL(5,4),
    max_confidence DECIMAL(5,4),
    consistency_score DECIMAL(5,4),
    
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

-- Anti-pattern statistics
CREATE TABLE anti_pattern_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    anti_pattern_name VARCHAR(100) NOT NULL,
    occurrence_count INTEGER,
    severity VARCHAR(20),
    affected_types TEXT[], -- Array of FQNs
    
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

-- Quality score history
CREATE TABLE quality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    overall_score DECIMAL(5,2),
    pattern_consistency_score DECIMAL(5,2),
    anti_pattern_score DECIMAL(5,2),
    structural_quality_score DECIMAL(5,2),
    best_practice_score DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

CREATE INDEX idx_quality_project_time ON quality_scores(project_id, recorded_at);

-- Recommendations
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    priority VARCHAR(20),
    category VARCHAR(50),
    title VARCHAR(255),
    description TEXT,
    affected_types TEXT[],
    estimated_effort VARCHAR(20),
    status VARCHAR(20) DEFAULT 'open',
    resolved_at TIMESTAMP,
    
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

-- Module-level metrics
CREATE TABLE module_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id),
    module_name VARCHAR(255),
    type_count INTEGER,
    line_count INTEGER,
    avg_complexity DECIMAL(6,2),
    afferent_coupling INTEGER,
    efferent_coupling INTEGER,
    instability DECIMAL(5,4),
    abstractness DECIMAL(5,4),
    distance_from_main DECIMAL(5,4),
    
    CONSTRAINT fk_analysis_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)
);

-- Views for common queries

-- Quality trend view
CREATE VIEW quality_trend AS
SELECT 
    p.name as project_name,
    qs.recorded_at,
    qs.overall_score,
    qs.pattern_consistency_score,
    qs.anti_pattern_score,
    LAG(qs.overall_score) OVER (PARTITION BY p.id ORDER BY qs.recorded_at) as previous_score,
    qs.overall_score - LAG(qs.overall_score) OVER (PARTITION BY p.id ORDER BY qs.recorded_at) as score_change
FROM quality_scores qs
JOIN projects p ON qs.project_id = p.id
ORDER BY p.name, qs.recorded_at;

-- Pattern adoption view
CREATE VIEW pattern_adoption AS
SELECT 
    ar.id as analysis_run_id,
    p.name as project_name,
    ps.pattern_name,
    ps.occurrence_count,
    ps.avg_confidence,
    ps.consistency_score,
    RANK() OVER (PARTITION BY ar.id ORDER BY ps.occurrence_count DESC) as adoption_rank
FROM pattern_statistics ps
JOIN analysis_runs ar ON ps.analysis_run_id = ar.id
JOIN projects p ON ar.project_id = p.id;
```

## 4.6 Example Queries Across Databases

```python
class AnalysisQueryService:
    """
    Service that coordinates queries across all three databases.
    """
    
    def __init__(self, neo4j: Neo4jClient, mongo: MongoClient, postgres: PostgresClient):
        self.graph = neo4j
        self.documents = mongo
        self.sql = postgres
    
    async def get_pattern_details(self, project_id: str, pattern_name: str) -> PatternReport:
        """
        Get comprehensive pattern analysis combining all data sources.
        """
        # Get pattern instances and relationships from graph
        graph_query = """
        MATCH (p:Project {id: $project_id})
        MATCH (p)-[:CONTAINS*]->(t:Type)-[m:MATCHES]->(pi:PatternInstance)
              -[:INSTANCE_OF]->(pat:Pattern {name: $pattern_name})
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Type)
        RETURN t.name, t.fully_qualified_name, m.confidence, 
               collect(DISTINCT dep.name) as dependencies
        """
        graph_results = await self.graph.execute(graph_query, {
            'project_id': project_id,
            'pattern_name': pattern_name
        })
        
        # Get detailed code unit info from documents
        type_fqns = [r['fully_qualified_name'] for r in graph_results]
        doc_results = await self.documents.code_units.find({
            'project_id': project_id,
            'identity.fully_qualified_name': {'$in': type_fqns}
        }).to_list()
        
        # Get statistics from SQL
        sql_query = """
        SELECT 
            ps.occurrence_count,
            ps.avg_confidence,
            ps.consistency_score,
            qs.overall_score as project_quality
        FROM pattern_statistics ps
        JOIN analysis_runs ar ON ps.analysis_run_id = ar.id
        JOIN quality_scores qs ON ar.id = qs.analysis_run_id
        WHERE ar.project_id = %s 
          AND ps.pattern_name = %s
        ORDER BY ar.completed_at DESC
        LIMIT 1
        """
        sql_results = await self.sql.fetchone(sql_query, [project_id, pattern_name])
        
        # Combine results
        return PatternReport(
            pattern_name=pattern_name,
            instances=[
                PatternInstance(
                    type_name=gr['name'],
                    fqn=gr['fully_qualified_name'],
                    confidence=gr['confidence'],
                    dependencies=gr['dependencies'],
                    details=next(
                        (d for d in doc_results 
                         if d['identity']['fully_qualified_name'] == gr['fully_qualified_name']),
                        None
                    )
                )
                for gr in graph_results
            ],
            statistics=PatternStatistics(
                count=sql_results['occurrence_count'],
                avg_confidence=sql_results['avg_confidence'],
                consistency=sql_results['consistency_score']
            ),
            project_quality=sql_results['project_quality']
        )
    
    async def find_inconsistencies(self, project_id: str) -> List[Inconsistency]:
        """
        Find pattern inconsistencies using graph traversal.
        """
        query = """
        MATCH (p:Project {id: $project_id})
        MATCH (p)-[:CONTAINS*]->(t1:Type)-[:MATCHES]->(pi1:PatternInstance)
              -[:INSTANCE_OF]->(pat:Pattern)
        MATCH (p)-[:CONTAINS*]->(t2:Type)-[:MATCHES]->(pi2:PatternInstance)
              -[:INSTANCE_OF]->(pat)
        WHERE t1 <> t2 
          AND pi1.signals_matched <> pi2.signals_matched
        WITH pat.name as pattern, 
             collect(DISTINCT {type: t1.name, signals: pi1.signals_matched}) as variants
        WHERE size(variants) > 1
        RETURN pattern, variants
        """
        results = await self.graph.execute(query, {'project_id': project_id})
        
        inconsistencies = []
        for result in results:
            # Find majority approach
            signal_counts = Counter()
            for v in result['variants']:
                signal_counts[tuple(sorted(v['signals']))] += 1
            
            majority_signals = signal_counts.most_common(1)[0][0]
            
            deviations = [
                v for v in result['variants']
                if tuple(sorted(v['signals'])) != majority_signals
            ]
            
            inconsistencies.append(Inconsistency(
                pattern=result['pattern'],
                majority_approach=list(majority_signals),
                deviations=[
                    {'type': d['type'], 'signals': d['signals']}
                    for d in deviations
                ]
            ))
        
        return inconsistencies
    
    async def get_quality_trend(self, project_id: str, days: int = 30) -> QualityTrend:
        """
        Get quality score trend from SQL.
        """
        query = """
        SELECT 
            recorded_at,
            overall_score,
            pattern_consistency_score,
            anti_pattern_score,
            structural_quality_score
        FROM quality_scores
        WHERE project_id = %s
          AND recorded_at >= NOW() - INTERVAL '%s days'
        ORDER BY recorded_at
        """
        results = await self.sql.fetch(query, [project_id, days])
        
        return QualityTrend(
            project_id=project_id,
            data_points=[
                QualityDataPoint(
                    timestamp=r['recorded_at'],
                    overall=r['overall_score'],
                    consistency=r['pattern_consistency_score'],
                    anti_patterns=r['anti_pattern_score'],
                    structural=r['structural_quality_score']
                )
                for r in results
            ]
        )
```

---

# Part 5: Summary

## 5.1 Methodology Overview

```
EXPLORATION METHODOLOGY
═══════════════════════

1. RECONNAISSANCE
   └── Understand the technology landscape before diving into code
   
2. STRUCTURAL ANALYSIS  
   └── Map the architecture: modules, types, relationships
   
3. SEMANTIC ANALYSIS
   └── Understand behavior: method signatures, data flow, annotations
   
4. PATTERN RECOGNITION
   └── Match known patterns, discover unknown patterns, find anti-patterns
   
5. SYNTHESIS
   └── Generate insights, recommendations, and reports
```

## 5.2 Key Principles

```
PATTERN DISCOVERY PRINCIPLES
════════════════════════════

• Patterns emerge from observation, not prescription
• Cluster similar code to find recurring idioms
• Known patterns provide vocabulary; novel patterns capture innovation
• Anti-patterns are patterns that harm maintainability
• Aspects are cross-cutting concerns that span patterns
```

## 5.3 Data Architecture Summary

```
DATABASE SELECTION
══════════════════

GRAPH (Neo4j)
├── Best for: Relationships, dependencies, pattern matching
├── Store: Type nodes, relationship edges, pattern instances
└── Query: Cycles, paths, connected components

DOCUMENT (MongoDB)  
├── Best for: Flexible schema, nested data, full details
├── Store: Code units, analysis results, configurations
└── Query: Full-text search, complex filtering

RELATIONAL (PostgreSQL)
├── Best for: Aggregations, time series, reporting
├── Store: Metrics, statistics, quality scores
└── Query: Trends, dashboards, comparisons
```

## 5.4 Recommended Implementation Order

```
IMPLEMENTATION PHASES
═════════════════════

Phase 1: Core Pipeline
├── Project reconnaissance
├── Type inventory
├── Basic pattern matching
└── Simple reporting

Phase 2: Relationship Analysis
├── Dependency graph
├── Consistency checking
├── Anti-pattern detection
└── Graph database integration

Phase 3: Pattern Discovery
├── Cluster analysis
├── Novel pattern extraction
├── Aspect identification
└── Document database integration

Phase 4: Intelligence
├── Quality scoring
├── Trend analysis
├── Recommendations
└── Relational database integration
```
