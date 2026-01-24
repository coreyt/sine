# C# Codebase Quality Evaluation: Patterns, Detection, and Application Architecture

## Executive Summary

This document outlines the properties of a thoughtful, consistent C# codebase, mechanisms for detecting and cataloging patterns, and proposes an application architecture for automated codebase evaluation.

---

## Part 1: Properties of a Good C# Codebase

### 1.1 Beyond Surface-Level Consistency

A truly well-crafted codebase exhibits consistency at multiple layers:

| Layer | Surface Level | Deep Level |
|-------|---------------|------------|
| **Naming** | `PascalCase` for public members | Consistent domain vocabulary throughout |
| **Structure** | Files organized by feature/layer | Consistent dependency direction |
| **Error Handling** | Using exceptions | Consistent strategy (Result types vs exceptions vs either) |
| **Async** | Using `async/await` | Consistent cancellation token propagation |
| **Dependencies** | Using DI | Consistent lifetime management patterns |

### 1.2 Core Quality Dimensions

**Consistency**: Same problems solved the same way throughout
- Repository methods always return `Task<Result<T>>`
- All HTTP clients use the same resilience patterns
- Validation always occurs at the same architectural boundary

**Intentionality**: Patterns chosen deliberately
- Documentation or ADRs explaining pattern choices
- Patterns match problem complexity
- Clear reasoning for deviations

**Coherence**: Patterns work together harmoniously
- DI + Options + Repository forming a unified approach
- No conflicting paradigms (e.g., mixing service locator with pure DI)

**Proportionality**: Complexity matches problem complexity
- Simple CRUD doesn't need CQRS
- Not every class needs an interface
- Abstraction has clear purpose

---

## Part 2: Pattern Taxonomy for Modern C#

### 2.1 Structural Patterns

#### Classic (GoF)
```
Adapter     - Convert interface to another interface
Facade      - Simplified interface to complex subsystem
Decorator   - Add behavior without modifying class
Proxy       - Control access to an object
Composite   - Tree structures with uniform interface
```

#### Modern C# Extensions
```csharp
// Options Pattern - Type-safe configuration
public class EmailSettings
{
    public string SmtpHost { get; set; }
    public int Port { get; set; }
}

services.Configure<EmailSettings>(configuration.GetSection("Email"));

// Extension Methods as Lightweight Decorators
public static class StringExtensions
{
    public static string Truncate(this string value, int maxLength)
        => value?.Length <= maxLength ? value : value?[..maxLength] + "...";
}
```

### 2.2 Behavioral Patterns

#### Classic (GoF)
```
Strategy    - Interchangeable algorithms
Observer    - Pub/sub notification
Command     - Encapsulate request as object
State       - Behavior changes with state
Chain       - Pass request along handlers
```

#### Modern C# Extensions
```csharp
// Mediator Pattern (MediatR-style)
public record CreateOrderCommand(string CustomerId, List<OrderItem> Items) : IRequest<OrderResult>;

public class CreateOrderHandler : IRequestHandler<CreateOrderCommand, OrderResult>
{
    public async Task<OrderResult> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        // Handle the command
    }
}

// Pipeline/Middleware Pattern
public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        // Pre-processing
        var response = await next();
        // Post-processing
        return response;
    }
}

// Result Pattern (Railway-Oriented)
public class Result<T>
{
    public bool IsSuccess { get; }
    public T Value { get; }
    public Error Error { get; }
    
    public Result<TNext> Bind<TNext>(Func<T, Result<TNext>> func)
        => IsSuccess ? func(Value) : Result<TNext>.Failure(Error);
}
```

### 2.3 Creational Patterns

#### Classic (GoF)
```
Factory Method  - Create objects through method
Abstract Factory - Create families of objects
Builder         - Construct complex objects step-by-step
Singleton       - Single instance (⚠️ use with caution)
Prototype       - Clone existing objects
```

#### Modern C# Extensions
```csharp
// Fluent Builder Pattern
var query = new QueryBuilder<Customer>()
    .Where(c => c.IsActive)
    .Include(c => c.Orders)
    .OrderBy(c => c.Name)
    .Take(10)
    .Build();

// Factory with DI Integration
public interface IProcessorFactory
{
    IProcessor Create(ProcessorType type);
}

public class ProcessorFactory : IProcessorFactory
{
    private readonly IServiceProvider _services;
    
    public IProcessor Create(ProcessorType type) => type switch
    {
        ProcessorType.Csv => _services.GetRequiredService<CsvProcessor>(),
        ProcessorType.Json => _services.GetRequiredService<JsonProcessor>(),
        _ => throw new ArgumentOutOfRangeException()
    };
}
```

### 2.4 Architectural Patterns

```
Repository          - Abstract data access
Unit of Work        - Coordinate multiple repositories
CQRS               - Separate read/write models
Event Sourcing     - Store events, derive state
Specification      - Encapsulate query logic
Domain Events      - Decouple domain operations
```

```csharp
// Repository + Unit of Work
public interface IUnitOfWork
{
    IRepository<Customer> Customers { get; }
    IRepository<Order> Orders { get; }
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}

// Specification Pattern
public class ActiveCustomersSpec : Specification<Customer>
{
    public override Expression<Func<Customer, bool>> ToExpression()
        => customer => customer.IsActive && customer.DeletedAt == null;
}

// Domain Events
public record OrderPlaced(Guid OrderId, Guid CustomerId, decimal Total) : IDomainEvent;
```

### 2.5 Integration/Resilience Patterns

```
Circuit Breaker    - Fail fast when downstream is unhealthy
Retry              - Automatic retry with backoff
Bulkhead           - Isolate failures
Outbox             - Reliable event publishing
Saga               - Distributed transaction coordination
```

```csharp
// Polly-based Resilience
services.AddHttpClient<IOrderService, OrderService>()
    .AddPolicyHandler(GetRetryPolicy())
    .AddPolicyHandler(GetCircuitBreakerPolicy());

private static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
    => HttpPolicyExtensions
        .HandleTransientHttpError()
        .WaitAndRetryAsync(3, retryAttempt => 
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
```

### 2.6 Anti-Patterns to Detect

| Anti-Pattern | Description | Detection Signal |
|--------------|-------------|------------------|
| **God Class** | Class doing too much | High method count, many dependencies |
| **Feature Envy** | Method uses other class more than own | Cross-class member access analysis |
| **Anemic Domain** | Logic outside entities | Entities with only getters/setters |
| **Service Locator** | Runtime DI resolution | `IServiceProvider.GetService` calls |
| **Primitive Obsession** | Primitives instead of value objects | `string email`, `decimal money` params |
| **Leaky Abstraction** | Implementation details exposed | Repository returning `IQueryable<T>` |
| **Over-Abstraction** | Interfaces with single implementation | `IFooService` : `FooService` only |
| **Shotgun Surgery** | Change requires many file edits | Feature change impact analysis |

---

## Part 3: Pattern Detection Mechanisms

### 3.1 Detection Approaches

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pattern Detection Stack                       │
├─────────────────────────────────────────────────────────────────┤
│  Semantic Analysis    │ Type relationships, inheritance trees   │
├───────────────────────┼─────────────────────────────────────────┤
│  Structural Analysis  │ AST patterns, method signatures         │
├───────────────────────┼─────────────────────────────────────────┤
│  Flow Analysis        │ Data flow, control flow, call graphs    │
├───────────────────────┼─────────────────────────────────────────┤
│  Metric Analysis      │ Cyclomatic complexity, coupling, etc.   │
├───────────────────────┼─────────────────────────────────────────┤
│  Convention Analysis  │ Naming patterns, file organization      │
└───────────────────────┴─────────────────────────────────────────┘
```

### 3.2 Roslyn-Based Detection

```csharp
// Example: Detecting Repository Pattern Implementation
public class RepositoryPatternDetector : ISyntaxNodeAnalyzer
{
    public PatternMatch Analyze(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var signals = new List<PatternSignal>();
        
        // Signal 1: Implements IRepository<T> or similar generic interface
        var interfaces = classDecl.BaseList?.Types
            .Select(t => model.GetTypeInfo(t.Type).Type)
            .Where(t => t?.Name.Contains("Repository") == true);
        
        if (interfaces?.Any() == true)
            signals.Add(new PatternSignal("ImplementsRepositoryInterface", 0.8));
        
        // Signal 2: Has data access methods (Get, Add, Update, Delete)
        var methods = classDecl.Members.OfType<MethodDeclarationSyntax>();
        var crudMethods = methods.Count(m => 
            CrudMethodNames.Contains(m.Identifier.Text));
        
        if (crudMethods >= 3)
            signals.Add(new PatternSignal("HasCrudMethods", 0.6));
        
        // Signal 3: Depends on DbContext or similar
        var hasDbContext = classDecl.Members
            .OfType<FieldDeclarationSyntax>()
            .Any(f => f.Declaration.Type.ToString().Contains("DbContext"));
        
        if (hasDbContext)
            signals.Add(new PatternSignal("DependsOnDbContext", 0.7));
        
        return new PatternMatch("Repository", CalculateConfidence(signals), signals);
    }
}
```

### 3.3 Pattern Signature Definitions

Patterns can be defined declaratively for the detection engine:

```yaml
# Pattern Definition: Repository Pattern
pattern:
  name: Repository
  category: Architectural
  confidence_threshold: 0.7
  
signals:
  - name: ImplementsRepositoryInterface
    weight: 0.3
    detector: InterfaceImplementation
    config:
      patterns: ["*Repository*", "IRepository`1"]
      
  - name: HasCrudMethods
    weight: 0.25
    detector: MethodSignature
    config:
      required_methods: [Get*, Find*, Add*, Create*, Update*, Remove*, Delete*]
      minimum_matches: 3
      
  - name: DataAccessDependency
    weight: 0.25
    detector: ConstructorDependency
    config:
      types: [DbContext, IDbConnection, ISession]
      
  - name: GenericEntityType
    weight: 0.2
    detector: GenericTypeParameter
    config:
      constraint_patterns: ["class", "IEntity"]

anti_signals:
  - name: BusinessLogicPresent
    weight: -0.3
    detector: MethodComplexity
    config:
      cyclomatic_threshold: 5
```

---

## Part 4: Pattern Catalog System

### 4.1 Catalog Hierarchy

```
PatternCatalog/
├── Standard/                    # Industry-wide patterns
│   ├── GoF/
│   │   ├── Creational/
│   │   ├── Structural/
│   │   └── Behavioral/
│   ├── Enterprise/
│   │   ├── Repository.yaml
│   │   ├── UnitOfWork.yaml
│   │   └── CQRS.yaml
│   └── Integration/
│       ├── CircuitBreaker.yaml
│       └── Outbox.yaml
│
├── BestPractices/              # Recommended approaches
│   ├── AsyncAwait/
│   │   ├── CancellationPropagation.yaml
│   │   ├── ConfigureAwaitUsage.yaml
│   │   └── AsyncVoidAvoidance.yaml
│   ├── DependencyInjection/
│   │   ├── ConstructorInjection.yaml
│   │   ├── LifetimeManagement.yaml
│   │   └── ServiceLocatorAvoidance.yaml
│   └── ErrorHandling/
│       ├── ResultPattern.yaml
│       └── ExceptionHierarchy.yaml
│
├── AntiPatterns/               # Patterns to avoid
│   ├── GodClass.yaml
│   ├── AnemicDomain.yaml
│   ├── ServiceLocator.yaml
│   └── PrimitiveObsession.yaml
│
└── Custom/                     # Codebase-specific patterns
    ├── .codebase-patterns.yaml # Auto-discovered
    └── team-conventions.yaml   # Manually defined
```

### 4.2 Pattern Categories

```csharp
public enum PatternCategory
{
    // Intent-based
    Creational,
    Structural,
    Behavioral,
    
    // Scope-based
    Architectural,
    Integration,
    Resilience,
    
    // Quality-based
    BestPractice,
    AntiPattern,
    
    // Source-based
    Standard,
    CodebaseSpecific
}

public record PatternDefinition(
    string Name,
    PatternCategory Category,
    string Description,
    IReadOnlyList<PatternSignal> Signals,
    IReadOnlyList<PatternSignal> AntiSignals,
    double ConfidenceThreshold,
    IReadOnlyList<string> Examples,
    IReadOnlyList<string> RelatedPatterns
);
```

### 4.3 Codebase-Specific Pattern Discovery

The system should learn patterns specific to a codebase:

```csharp
public class PatternDiscoveryEngine
{
    public async Task<IEnumerable<DiscoveredPattern>> DiscoverPatternsAsync(
        Solution solution,
        PatternDiscoveryOptions options)
    {
        // 1. Cluster similar code structures
        var clusters = await ClusterSimilarStructures(solution);
        
        // 2. Identify recurring patterns (>= threshold occurrences)
        var recurring = clusters.Where(c => c.Occurrences >= options.MinOccurrences);
        
        // 3. Extract pattern signature from cluster
        foreach (var cluster in recurring)
        {
            var signature = ExtractSignature(cluster);
            
            // 4. Match against known patterns
            var knownMatch = MatchKnownPattern(signature);
            
            if (knownMatch != null)
            {
                yield return new DiscoveredPattern
                {
                    Name = $"{knownMatch.Name} (Variant)",
                    BasePattern = knownMatch,
                    LocalVariations = IdentifyVariations(cluster, knownMatch),
                    Occurrences = cluster.Occurrences
                };
            }
            else
            {
                // Novel codebase-specific pattern
                yield return new DiscoveredPattern
                {
                    Name = GeneratePatternName(cluster),
                    IsCodebaseSpecific = true,
                    Signature = signature,
                    Occurrences = cluster.Occurrences,
                    Examples = cluster.Examples.Take(3).ToList()
                };
            }
        }
    }
}
```

---

## Part 5: Detecting Inappropriate Pattern Use

### 5.1 Over-Engineering Indicators

```yaml
# Detection: Over-Abstraction
indicator:
  name: SingleImplementationInterface
  description: Interface with exactly one implementation (not for testing boundaries)
  severity: Warning
  
  detection:
    query: |
      SELECT i.Name, i.Implementations
      FROM Interfaces i
      WHERE i.ImplementationCount = 1
        AND NOT i.Name IN (SELECT TestBoundaryInterfaces)
        AND NOT i.IsExternal
    
  exceptions:
    - "Interface is at architectural boundary"
    - "Interface is for dependency injection seam"
    - "Multiple implementations planned (documented)"
```

### 5.2 Wrong Pattern for Problem

```csharp
public class PatternAppropriateness
{
    public IEnumerable<PatternMismatch> Analyze(
        ProjectAnalysis project,
        IEnumerable<PatternMatch> detectedPatterns)
    {
        // CQRS in simple CRUD application
        if (detectedPatterns.Any(p => p.Name == "CQRS"))
        {
            var complexity = CalculateDomainComplexity(project);
            if (complexity < ComplexityThreshold.Medium)
            {
                yield return new PatternMismatch
                {
                    Pattern = "CQRS",
                    Issue = "Complexity overhead exceeds benefit",
                    Recommendation = "Consider simple repository pattern",
                    Severity = Severity.Warning
                };
            }
        }
        
        // Service Locator instead of Constructor Injection
        var serviceLocatorUsage = FindServiceLocatorUsage(project);
        if (serviceLocatorUsage.Any())
        {
            foreach (var usage in serviceLocatorUsage)
            {
                if (!IsLegitimateServiceLocatorUse(usage))
                {
                    yield return new PatternMismatch
                    {
                        Pattern = "ServiceLocator",
                        Issue = "Anti-pattern: hides dependencies",
                        Location = usage.Location,
                        Recommendation = "Use constructor injection",
                        Severity = Severity.Error
                    };
                }
            }
        }
    }
    
    private bool IsLegitimateServiceLocatorUse(ServiceLocatorUsage usage)
    {
        // Legitimate uses:
        // - Factory creating instances at runtime
        // - Framework integration points
        // - Plugin systems
        return usage.Context is FactoryContext or FrameworkIntegrationContext;
    }
}
```

### 5.3 Inconsistent Pattern Application

```csharp
public class ConsistencyAnalyzer
{
    public IEnumerable<InconsistencyReport> FindInconsistencies(
        IEnumerable<PatternMatch> patterns)
    {
        // Group by pattern type
        var repositoryImplementations = patterns
            .Where(p => p.Name == "Repository")
            .ToList();
        
        if (repositoryImplementations.Count > 1)
        {
            // Check for consistency
            var signatures = repositoryImplementations
                .Select(r => ExtractSignature(r))
                .ToList();
            
            var deviations = FindDeviations(signatures);
            
            foreach (var deviation in deviations)
            {
                yield return new InconsistencyReport
                {
                    Pattern = "Repository",
                    Issue = deviation.Description,
                    ExpectedBehavior = deviation.MajorityApproach,
                    ActualBehavior = deviation.DeviatingApproach,
                    Locations = deviation.Locations,
                    Recommendation = $"Align with codebase convention: {deviation.MajorityApproach}"
                };
            }
        }
    }
}
```

---

## Part 6: Application Architecture

### 6.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLI / Web Interface                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   Reporting  │  │   Analysis   │  │   Pattern Management     │ │
│  │   Engine     │  │  Orchestrator│  │   (CRUD for patterns)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│                           │                                        │
├───────────────────────────┼────────────────────────────────────────┤
│                           ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                     Analysis Pipeline                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │  │
│  │  │ Source  │→ │ Syntax  │→ │Semantic │→ │    Pattern      │ │  │
│  │  │ Loading │  │Analysis │  │Analysis │  │    Matching     │ │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                           │                                        │
├───────────────────────────┼────────────────────────────────────────┤
│                           ▼                                        │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │                    Pattern Catalog                            ││
│  │  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ ││
│  │  │ Standard │  │    Best    │  │   Anti-    │  │  Custom/  │ ││
│  │  │ Patterns │  │ Practices  │  │  Patterns  │  │ Discovered│ ││
│  │  └──────────┘  └────────────┘  └────────────┘  └───────────┘ ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 6.2 Core Domain Model

```csharp
// Core Entities
public record Codebase(
    string Path,
    IReadOnlyList<Project> Projects,
    CodebaseMetadata Metadata
);

public record AnalysisResult(
    Codebase Codebase,
    IReadOnlyList<PatternMatch> DetectedPatterns,
    IReadOnlyList<Inconsistency> Inconsistencies,
    IReadOnlyList<QualityMetric> Metrics,
    IReadOnlyList<Recommendation> Recommendations,
    OverallScore Score
);

public record PatternMatch(
    PatternDefinition Pattern,
    Location Location,
    double Confidence,
    IReadOnlyList<PatternSignal> MatchingSignals,
    IReadOnlyList<PatternSignal> ViolatedSignals
);

public record Inconsistency(
    string PatternName,
    string Description,
    IReadOnlyList<Location> Locations,
    string MajorityApproach,
    string DeviatingApproach,
    Severity Severity
);

// Value Objects
public record Location(string FilePath, int StartLine, int EndLine, string SymbolName);
public record OverallScore(double Value, string Grade, IReadOnlyDictionary<string, double> ComponentScores);
```

### 6.3 Project Structure

```
src/
├── CodebaseEvaluator.Core/
│   ├── Domain/
│   │   ├── Entities/
│   │   │   ├── Codebase.cs
│   │   │   ├── PatternMatch.cs
│   │   │   └── AnalysisResult.cs
│   │   ├── ValueObjects/
│   │   │   ├── Location.cs
│   │   │   ├── Confidence.cs
│   │   │   └── Score.cs
│   │   └── Services/
│   │       ├── IPatternDetector.cs
│   │       ├── IConsistencyAnalyzer.cs
│   │       └── IScoreCalculator.cs
│   │
│   ├── PatternCatalog/
│   │   ├── IPatternRepository.cs
│   │   ├── PatternDefinition.cs
│   │   ├── PatternSignal.cs
│   │   └── Loaders/
│   │       ├── YamlPatternLoader.cs
│   │       └── DiscoveredPatternLoader.cs
│   │
│   └── Analysis/
│       ├── Pipeline/
│       │   ├── IAnalysisPipeline.cs
│       │   ├── AnalysisContext.cs
│       │   └── AnalysisPipelineBuilder.cs
│       └── Rules/
│           ├── IRuleEngine.cs
│           └── RuleDefinition.cs

├── CodebaseEvaluator.Roslyn/
│   ├── SourceLoading/
│   │   ├── SolutionLoader.cs
│   │   └── ProjectLoader.cs
│   │
│   ├── Analyzers/
│   │   ├── Syntax/
│   │   │   ├── ClassStructureAnalyzer.cs
│   │   │   ├── MethodSignatureAnalyzer.cs
│   │   │   └── NamingConventionAnalyzer.cs
│   │   ├── Semantic/
│   │   │   ├── TypeRelationshipAnalyzer.cs
│   │   │   ├── DependencyAnalyzer.cs
│   │   │   └── InheritanceAnalyzer.cs
│   │   └── Flow/
│   │       ├── DataFlowAnalyzer.cs
│   │       └── CallGraphAnalyzer.cs
│   │
│   └── PatternDetectors/
│       ├── RepositoryPatternDetector.cs
│       ├── FactoryPatternDetector.cs
│       ├── MediatorPatternDetector.cs
│       └── ...

├── CodebaseEvaluator.Reporting/
│   ├── Formatters/
│   │   ├── MarkdownFormatter.cs
│   │   ├── HtmlFormatter.cs
│   │   └── JsonFormatter.cs
│   └── Templates/
│       └── ...

├── CodebaseEvaluator.CLI/
│   ├── Commands/
│   │   ├── AnalyzeCommand.cs
│   │   ├── DiscoverPatternsCommand.cs
│   │   └── CompareCommand.cs
│   └── Program.cs

└── CodebaseEvaluator.Web/
    └── ... (optional web interface)

patterns/
├── standard/
│   ├── gof/
│   │   ├── factory.yaml
│   │   ├── strategy.yaml
│   │   └── ...
│   ├── architectural/
│   │   ├── repository.yaml
│   │   ├── cqrs.yaml
│   │   └── ...
│   └── integration/
│       ├── circuit-breaker.yaml
│       └── ...
│
├── best-practices/
│   ├── async/
│   │   ├── cancellation-propagation.yaml
│   │   └── ...
│   └── di/
│       ├── constructor-injection.yaml
│       └── ...
│
└── anti-patterns/
    ├── god-class.yaml
    ├── service-locator.yaml
    └── ...

tests/
├── CodebaseEvaluator.Core.Tests/
├── CodebaseEvaluator.Roslyn.Tests/
└── TestCodebases/
    ├── WellStructured/
    ├── Inconsistent/
    └── AntiPatterns/
```

### 6.4 Key Interfaces

```csharp
// Analysis Pipeline
public interface IAnalysisPipeline
{
    Task<AnalysisResult> AnalyzeAsync(
        string solutionPath, 
        AnalysisOptions options,
        CancellationToken ct = default);
}

// Pattern Detection
public interface IPatternDetector
{
    string PatternName { get; }
    Task<IEnumerable<PatternMatch>> DetectAsync(
        AnalysisContext context,
        CancellationToken ct = default);
}

// Pattern Catalog
public interface IPatternCatalog
{
    IEnumerable<PatternDefinition> GetAllPatterns();
    IEnumerable<PatternDefinition> GetByCategory(PatternCategory category);
    PatternDefinition? GetByName(string name);
    void AddCustomPattern(PatternDefinition pattern);
    Task<IEnumerable<PatternDefinition>> DiscoverPatternsAsync(AnalysisContext context);
}

// Consistency Analysis
public interface IConsistencyAnalyzer
{
    Task<IEnumerable<Inconsistency>> AnalyzeAsync(
        IEnumerable<PatternMatch> patterns,
        CancellationToken ct = default);
}

// Scoring
public interface IScoreCalculator
{
    OverallScore Calculate(
        IEnumerable<PatternMatch> patterns,
        IEnumerable<Inconsistency> inconsistencies,
        IEnumerable<QualityMetric> metrics);
}
```

### 6.5 Configuration

```json
{
  "analysis": {
    "includePatterns": ["**/*.cs"],
    "excludePatterns": ["**/obj/**", "**/bin/**", "**/*.Generated.cs"],
    "parallelism": 4
  },
  "patterns": {
    "catalogPaths": [
      "./patterns/standard",
      "./patterns/best-practices"
    ],
    "enableAntiPatternDetection": true,
    "customPatternsPath": "./patterns/custom"
  },
  "scoring": {
    "weights": {
      "patternConsistency": 0.3,
      "bestPracticeAdherence": 0.25,
      "antiPatternAvoidance": 0.25,
      "codeMetrics": 0.2
    },
    "thresholds": {
      "A": 90,
      "B": 80,
      "C": 70,
      "D": 60
    }
  },
  "reporting": {
    "format": "markdown",
    "includeRecommendations": true,
    "includeCodeExamples": true
  }
}
```

---

## Part 7: Usage Examples

### 7.1 CLI Usage

```bash
# Basic analysis
codebase-eval analyze ./MyProject.sln

# Analysis with custom patterns
codebase-eval analyze ./MyProject.sln --patterns ./team-patterns

# Discover patterns in codebase
codebase-eval discover ./MyProject.sln --min-occurrences 3

# Compare two codebases
codebase-eval compare ./Project1.sln ./Project2.sln

# Generate detailed report
codebase-eval analyze ./MyProject.sln --output report.md --format markdown
```

### 7.2 Sample Output

```markdown
# Codebase Analysis Report: MyProject

## Overall Score: B (82/100)

### Pattern Summary
| Pattern | Occurrences | Consistency | Notes |
|---------|-------------|-------------|-------|
| Repository | 12 | 91% | 1 deviation in OrderRepository |
| MediatR/Mediator | 45 | 100% | Excellent consistency |
| Options Pattern | 8 | 100% | |
| Factory | 3 | 67% | Inconsistent naming |

### Detected Anti-Patterns
| Anti-Pattern | Severity | Location | Recommendation |
|--------------|----------|----------|----------------|
| God Class | High | `UserService.cs` | Split into focused services |
| Service Locator | Medium | `ReportGenerator.cs:45` | Use constructor injection |

### Inconsistencies
1. **Repository Return Types** (2 deviations)
   - Expected: `Task<Result<T>>`
   - Found: `Task<T?>` in `OrderRepository`, `ProductRepository`
   
2. **Async Naming** (5 deviations)
   - Expected: `*Async` suffix
   - Found: Methods without suffix in `DataAccess/`

### Recommendations
1. **High Priority**: Refactor `UserService` (God Class)
2. **Medium Priority**: Standardize repository return types
3. **Low Priority**: Add `Async` suffix to remaining async methods
```

---

## Part 8: Implementation Roadmap

### Phase 1: Foundation (MVP)
- [ ] Roslyn-based solution loading
- [ ] Basic syntax and semantic analysis
- [ ] 5-10 core pattern detectors (Repository, Factory, Strategy, etc.)
- [ ] Simple consistency checking
- [ ] CLI with basic reporting

### Phase 2: Expansion
- [ ] Extended pattern catalog (20+ patterns)
- [ ] YAML-based pattern definitions
- [ ] Anti-pattern detection
- [ ] Code metrics integration
- [ ] HTML/Web reporting

### Phase 3: Intelligence
- [ ] Pattern discovery (clustering similar code)
- [ ] Codebase-specific pattern learning
- [ ] Historical analysis (trend over time)
- [ ] IDE integration (VS Code extension)

### Phase 4: Enterprise
- [ ] Multi-repository analysis
- [ ] Team convention enforcement
- [ ] CI/CD integration
- [ ] Custom rule authoring UI

---

## Appendix A: Pattern Detection Heuristics

### Repository Pattern Detection
```
Confidence = Σ(signal_weight × signal_present)

Signals:
- Implements generic repository interface (0.3)
- Has CRUD method signatures (0.25)
- Depends on data access infrastructure (0.25)
- Entity-centric (single entity focus) (0.2)

Anti-signals:
- Contains business logic (complex conditionals) (-0.3)
- Has UI dependencies (-0.5)
```

### Mediator Pattern Detection
```
Signals:
- Request/Response generic interfaces (0.3)
- Handler pattern (IRequestHandler<T,R>) (0.35)
- Single public method (Handle) (0.2)
- No direct service dependencies (0.15)
```

---

## Appendix B: Quality Metrics

| Metric | Description | Healthy Range |
|--------|-------------|---------------|
| Cyclomatic Complexity | Paths through code | < 10 per method |
| Coupling (Ce) | Outgoing dependencies | < 20 per class |
| Coupling (Ca) | Incoming dependencies | Context-dependent |
| Depth of Inheritance | Class hierarchy depth | ≤ 3 |
| LCOM | Lack of Cohesion | < 0.8 |
| Test Coverage | Code covered by tests | > 70% |
| Pattern Consistency | Same pattern, same implementation | > 85% |
