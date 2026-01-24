# Sample Pattern Definitions and Implementations

This file contains practical examples of pattern definitions and detection code.

---

## 1. Pattern Definition: Repository Pattern (YAML)

```yaml
# patterns/standard/architectural/repository.yaml
pattern:
  name: Repository
  category: Architectural
  description: |
    Mediates between the domain and data mapping layers, acting like an 
    in-memory domain object collection. Provides persistence ignorance to 
    the domain layer.
  
  confidence_threshold: 0.65
  
  # What indicates this pattern IS present
  signals:
    - name: ImplementsRepositoryInterface
      weight: 0.25
      detector: InterfaceImplementation
      config:
        patterns:
          - "*Repository*"
          - "IRepository`1"
          - "IGenericRepository*"
          - "IReadRepository*"
          - "IWriteRepository*"
    
    - name: HasDataAccessMethods
      weight: 0.20
      detector: MethodSignatureMatch
      config:
        patterns:
          - { name: "Get*", returns: "Task<*>|*", min_matches: 1 }
          - { name: "Find*", returns: "Task<*>|IEnumerable<*>|IQueryable<*>", min_matches: 0 }
          - { name: "Add*|Create*|Insert*", returns: "Task*|void", min_matches: 1 }
          - { name: "Update*|Save*", returns: "Task*|void", min_matches: 0 }
          - { name: "Remove*|Delete*", returns: "Task*|void|bool", min_matches: 1 }
        total_min_matches: 3
    
    - name: DataAccessDependency
      weight: 0.25
      detector: ConstructorDependency
      config:
        any_of:
          - "DbContext"
          - "*DbContext"
          - "IDbConnection"
          - "ISession"
          - "IDocumentSession"
          - "IMongoCollection*"
    
    - name: EntityFocused
      weight: 0.15
      detector: GenericTypeParameter
      config:
        has_generic_parameter: true
        parameter_constraints:
          - "class"
          - "*Entity*"
          - "*Aggregate*"
    
    - name: NamingConvention
      weight: 0.15
      detector: NamingPattern
      config:
        class_name_pattern: "*Repository"
  
  # What indicates this pattern is NOT present (or misused)
  anti_signals:
    - name: ContainsBusinessLogic
      weight: -0.30
      detector: MethodComplexity
      config:
        cyclomatic_complexity_threshold: 8
        description: "Repository should not contain complex business logic"
    
    - name: HasUIOrWebDependencies
      weight: -0.40
      detector: ConstructorDependency
      config:
        any_of:
          - "HttpContext*"
          - "IHttpContextAccessor"
          - "Controller"
          - "*ViewModel*"
    
    - name: ExposesQueryable
      weight: -0.15
      detector: MethodReturnType
      config:
        returns: "IQueryable<*>"
        severity: Warning
        description: "Leaky abstraction - exposes query implementation"
  
  # Expected variations within this codebase
  consistency_checks:
    - name: ReturnTypeConsistency
      check: MethodReturnTypes
      config:
        method_pattern: "Get*|Find*"
        expected_uniformity: true
        
    - name: AsyncConsistency
      check: AsyncPatterns
      config:
        all_data_methods_async: true
        cancellation_token_propagation: true
  
  # Related patterns to check
  related_patterns:
    - UnitOfWork
    - Specification
    - GenericRepository
  
  examples:
    good:
      - |
        public class CustomerRepository : IRepository<Customer>
        {
            private readonly AppDbContext _context;
            
            public CustomerRepository(AppDbContext context)
            {
                _context = context;
            }
            
            public async Task<Customer?> GetByIdAsync(Guid id, CancellationToken ct = default)
                => await _context.Customers.FindAsync(new object[] { id }, ct);
            
            public async Task AddAsync(Customer customer, CancellationToken ct = default)
            {
                await _context.Customers.AddAsync(customer, ct);
            }
            
            public async Task<IReadOnlyList<Customer>> GetAllAsync(CancellationToken ct = default)
                => await _context.Customers.ToListAsync(ct);
        }
    
    bad:
      - |
        // Anti-pattern: Business logic in repository
        public class OrderRepository : IRepository<Order>
        {
            public async Task<Order> CreateOrderAsync(CreateOrderRequest request)
            {
                // ❌ Validation belongs in domain/application layer
                if (request.Items.Count == 0)
                    throw new ValidationException("Order must have items");
                
                // ❌ Business calculations belong elsewhere
                var discount = CalculateDiscount(request.CustomerId);
                var total = request.Items.Sum(i => i.Price) * (1 - discount);
                
                var order = new Order { /* ... */ };
                await _context.Orders.AddAsync(order);
                return order;
            }
        }

  recommendations:
    when_to_use:
      - "You want to abstract data access from domain logic"
      - "You need testability via mock repositories"
      - "You want to encapsulate query logic"
    
    when_not_to_use:
      - "Simple applications where EF DbContext is sufficient"
      - "You're already using CQRS with separate read/write models"
      - "The abstraction adds no value (thin wrapper over DbContext)"
```

---

## 2. Pattern Definition: Mediator/CQRS Pattern (YAML)

```yaml
# patterns/standard/architectural/mediator-cqrs.yaml
pattern:
  name: Mediator/CQRS
  aliases: [MediatR, CommandHandler, QueryHandler]
  category: Architectural
  description: |
    Separates read and write operations through commands and queries,
    dispatched through a mediator. Decouples sender from receiver.
  
  confidence_threshold: 0.70
  
  signals:
    - name: RequestHandlerInterface
      weight: 0.30
      detector: InterfaceImplementation
      config:
        patterns:
          - "IRequestHandler`2"
          - "ICommandHandler`*"
          - "IQueryHandler`*"
          - "INotificationHandler`1"
    
    - name: RequestTypePattern
      weight: 0.25
      detector: TypeInheritance
      config:
        patterns:
          - "IRequest`1"
          - "ICommand"
          - "IQuery`1"
          - "INotification"
    
    - name: SingleHandlerMethod
      weight: 0.20
      detector: MethodCount
      config:
        public_methods: 1
        method_name: "Handle"
    
    - name: MediatorDependency
      weight: 0.15
      detector: TypeUsage
      config:
        types:
          - "IMediator"
          - "ISender"
          - "IPublisher"
    
    - name: PipelineBehaviors
      weight: 0.10
      detector: InterfaceImplementation
      config:
        patterns:
          - "IPipelineBehavior`2"
  
  anti_signals:
    - name: DirectServiceCalls
      weight: -0.20
      detector: ConstructorDependency
      config:
        count_threshold: 5
        description: "Handlers should have minimal dependencies"
    
    - name: MultipleHandleMethods
      weight: -0.30
      detector: MethodCount
      config:
        method_pattern: "Handle*"
        max_count: 1
  
  consistency_checks:
    - name: CommandNamingConvention
      check: NamingPattern
      config:
        pattern: "*Command|*Query"
        applies_to: "classes implementing IRequest"
    
    - name: HandlerNamingConvention
      check: NamingPattern
      config:
        pattern: "*Handler|*CommandHandler|*QueryHandler"

  sub_patterns:
    - name: CommandPattern
      detection:
        type_name: "*Command"
        implements: "IRequest`1"
        not_returns: "IEnumerable|IList|IReadOnlyList"
    
    - name: QueryPattern
      detection:
        type_name: "*Query"
        implements: "IRequest`1"
        returns: "IEnumerable|IList|IReadOnlyList|*Dto|*Response"
```

---

## 3. C# Pattern Detector Implementation

```csharp
// CodebaseEvaluator.Roslyn/PatternDetectors/RepositoryPatternDetector.cs

using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using System.Collections.Immutable;

namespace CodebaseEvaluator.Roslyn.PatternDetectors;

public class RepositoryPatternDetector : IPatternDetector
{
    private static readonly ImmutableHashSet<string> CrudMethodPrefixes = 
        ImmutableHashSet.Create(StringComparer.OrdinalIgnoreCase,
            "Get", "Find", "Add", "Create", "Insert", "Update", "Save", "Remove", "Delete");
    
    private static readonly ImmutableHashSet<string> DataAccessTypes =
        ImmutableHashSet.Create(
            "DbContext", "IDbConnection", "ISession", "IDocumentSession", "IMongoCollection");

    public string PatternName => "Repository";
    
    public async Task<IEnumerable<PatternMatch>> DetectAsync(
        AnalysisContext context, 
        CancellationToken ct = default)
    {
        var matches = new List<PatternMatch>();
        
        foreach (var document in context.Solution.Projects.SelectMany(p => p.Documents))
        {
            ct.ThrowIfCancellationRequested();
            
            var syntaxRoot = await document.GetSyntaxRootAsync(ct);
            var semanticModel = await document.GetSemanticModelAsync(ct);
            
            if (syntaxRoot == null || semanticModel == null) continue;
            
            var classDeclarations = syntaxRoot
                .DescendantNodes()
                .OfType<ClassDeclarationSyntax>();
            
            foreach (var classDecl in classDeclarations)
            {
                var match = AnalyzeClass(classDecl, semanticModel);
                if (match != null && match.Confidence >= 0.65)
                {
                    matches.Add(match);
                }
            }
        }
        
        return matches;
    }
    
    private PatternMatch? AnalyzeClass(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var signals = new List<PatternSignal>();
        var antiSignals = new List<PatternSignal>();
        
        var classSymbol = model.GetDeclaredSymbol(classDecl);
        if (classSymbol == null) return null;
        
        // Signal 1: Implements repository interface
        var repositoryInterfaceSignal = CheckRepositoryInterface(classSymbol);
        if (repositoryInterfaceSignal != null)
            signals.Add(repositoryInterfaceSignal);
        
        // Signal 2: Has CRUD methods
        var crudSignal = CheckCrudMethods(classDecl, model);
        if (crudSignal != null)
            signals.Add(crudSignal);
        
        // Signal 3: Data access dependency
        var dataAccessSignal = CheckDataAccessDependency(classDecl, model);
        if (dataAccessSignal != null)
            signals.Add(dataAccessSignal);
        
        // Signal 4: Entity-focused (generic type parameter)
        var genericSignal = CheckGenericEntityType(classSymbol);
        if (genericSignal != null)
            signals.Add(genericSignal);
        
        // Signal 5: Naming convention
        var namingSignal = CheckNamingConvention(classSymbol);
        if (namingSignal != null)
            signals.Add(namingSignal);
        
        // Anti-signal 1: Contains business logic
        var businessLogicAnti = CheckForBusinessLogic(classDecl, model);
        if (businessLogicAnti != null)
            antiSignals.Add(businessLogicAnti);
        
        // Anti-signal 2: Exposes IQueryable
        var queryableAnti = CheckQueryableExposure(classDecl, model);
        if (queryableAnti != null)
            antiSignals.Add(queryableAnti);
        
        var confidence = CalculateConfidence(signals, antiSignals);
        
        if (confidence < 0.3) return null; // Too low to even report
        
        return new PatternMatch(
            PatternName: PatternName,
            Location: new Location(
                classDecl.SyntaxTree.FilePath,
                classDecl.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                classDecl.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
                classSymbol.Name
            ),
            Confidence: confidence,
            MatchingSignals: signals.ToImmutableList(),
            ViolatedSignals: antiSignals.ToImmutableList()
        );
    }
    
    private PatternSignal? CheckRepositoryInterface(INamedTypeSymbol classSymbol)
    {
        var interfaces = classSymbol.AllInterfaces;
        var repositoryInterface = interfaces.FirstOrDefault(i => 
            i.Name.Contains("Repository", StringComparison.OrdinalIgnoreCase) ||
            (i.IsGenericType && i.Name.StartsWith("IRepository")));
        
        if (repositoryInterface != null)
        {
            return new PatternSignal(
                Name: "ImplementsRepositoryInterface",
                Weight: 0.25,
                Present: true,
                Evidence: $"Implements {repositoryInterface.ToDisplayString()}"
            );
        }
        
        return null;
    }
    
    private PatternSignal? CheckCrudMethods(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var methods = classDecl.Members
            .OfType<MethodDeclarationSyntax>()
            .Select(m => model.GetDeclaredSymbol(m))
            .Where(m => m != null && m.DeclaredAccessibility == Accessibility.Public)
            .ToList();
        
        var crudMethodCount = methods.Count(m => 
            CrudMethodPrefixes.Any(prefix => 
                m!.Name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)));
        
        if (crudMethodCount >= 3)
        {
            return new PatternSignal(
                Name: "HasDataAccessMethods",
                Weight: 0.20,
                Present: true,
                Evidence: $"Found {crudMethodCount} CRUD-style methods"
            );
        }
        
        return null;
    }
    
    private PatternSignal? CheckDataAccessDependency(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var constructors = classDecl.Members.OfType<ConstructorDeclarationSyntax>();
        
        foreach (var ctor in constructors)
        {
            foreach (var param in ctor.ParameterList.Parameters)
            {
                var typeInfo = model.GetTypeInfo(param.Type!);
                var typeName = typeInfo.Type?.Name ?? "";
                
                if (DataAccessTypes.Any(dat => 
                    typeName.Contains(dat, StringComparison.OrdinalIgnoreCase)))
                {
                    return new PatternSignal(
                        Name: "DataAccessDependency",
                        Weight: 0.25,
                        Present: true,
                        Evidence: $"Constructor depends on {typeName}"
                    );
                }
            }
        }
        
        return null;
    }
    
    private PatternSignal? CheckGenericEntityType(INamedTypeSymbol classSymbol)
    {
        if (classSymbol.IsGenericType || 
            classSymbol.BaseType?.IsGenericType == true ||
            classSymbol.AllInterfaces.Any(i => i.IsGenericType))
        {
            return new PatternSignal(
                Name: "EntityFocused",
                Weight: 0.15,
                Present: true,
                Evidence: "Uses generic type parameter for entity"
            );
        }
        
        return null;
    }
    
    private PatternSignal? CheckNamingConvention(INamedTypeSymbol classSymbol)
    {
        if (classSymbol.Name.EndsWith("Repository", StringComparison.OrdinalIgnoreCase))
        {
            return new PatternSignal(
                Name: "NamingConvention",
                Weight: 0.15,
                Present: true,
                Evidence: $"Class named '{classSymbol.Name}' follows *Repository convention"
            );
        }
        
        return null;
    }
    
    private PatternSignal? CheckForBusinessLogic(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var methods = classDecl.Members.OfType<MethodDeclarationSyntax>();
        
        foreach (var method in methods)
        {
            var complexity = CalculateCyclomaticComplexity(method);
            if (complexity > 8)
            {
                return new PatternSignal(
                    Name: "ContainsBusinessLogic",
                    Weight: -0.30,
                    Present: true,
                    Evidence: $"Method '{method.Identifier.Text}' has complexity {complexity} (>8)"
                );
            }
        }
        
        return null;
    }
    
    private PatternSignal? CheckQueryableExposure(ClassDeclarationSyntax classDecl, SemanticModel model)
    {
        var methods = classDecl.Members.OfType<MethodDeclarationSyntax>();
        
        foreach (var method in methods)
        {
            var returnType = method.ReturnType.ToString();
            if (returnType.Contains("IQueryable"))
            {
                return new PatternSignal(
                    Name: "ExposesQueryable",
                    Weight: -0.15,
                    Present: true,
                    Evidence: $"Method '{method.Identifier.Text}' returns IQueryable (leaky abstraction)"
                );
            }
        }
        
        return null;
    }
    
    private int CalculateCyclomaticComplexity(MethodDeclarationSyntax method)
    {
        int complexity = 1; // Base complexity
        
        complexity += method.DescendantNodes().OfType<IfStatementSyntax>().Count();
        complexity += method.DescendantNodes().OfType<WhileStatementSyntax>().Count();
        complexity += method.DescendantNodes().OfType<ForStatementSyntax>().Count();
        complexity += method.DescendantNodes().OfType<ForEachStatementSyntax>().Count();
        complexity += method.DescendantNodes().OfType<CaseSwitchLabelSyntax>().Count();
        complexity += method.DescendantNodes().OfType<CasePatternSwitchLabelSyntax>().Count();
        complexity += method.DescendantNodes().OfType<ConditionalExpressionSyntax>().Count();
        complexity += method.DescendantNodes().OfType<CatchClauseSyntax>().Count();
        complexity += method.DescendantNodes().OfType<BinaryExpressionSyntax>()
            .Count(b => b.IsKind(SyntaxKind.LogicalAndExpression) || 
                       b.IsKind(SyntaxKind.LogicalOrExpression));
        
        return complexity;
    }
    
    private double CalculateConfidence(List<PatternSignal> signals, List<PatternSignal> antiSignals)
    {
        var positiveScore = signals.Sum(s => s.Weight);
        var negativeScore = antiSignals.Sum(s => Math.Abs(s.Weight));
        
        return Math.Max(0, Math.Min(1, positiveScore - negativeScore));
    }
}
```

---

## 4. Consistency Analyzer Implementation

```csharp
// CodebaseEvaluator.Core/Analysis/ConsistencyAnalyzer.cs

namespace CodebaseEvaluator.Core.Analysis;

public class ConsistencyAnalyzer : IConsistencyAnalyzer
{
    public async Task<IEnumerable<Inconsistency>> AnalyzeAsync(
        IEnumerable<PatternMatch> patterns,
        CancellationToken ct = default)
    {
        var inconsistencies = new List<Inconsistency>();
        
        // Group patterns by type
        var patternGroups = patterns.GroupBy(p => p.PatternName);
        
        foreach (var group in patternGroups)
        {
            var matches = group.ToList();
            if (matches.Count < 2) continue; // Need at least 2 to compare
            
            // Analyze consistency within this pattern type
            var patternInconsistencies = await AnalyzePatternConsistency(matches, ct);
            inconsistencies.AddRange(patternInconsistencies);
        }
        
        return inconsistencies;
    }
    
    private async Task<IEnumerable<Inconsistency>> AnalyzePatternConsistency(
        List<PatternMatch> matches,
        CancellationToken ct)
    {
        var inconsistencies = new List<Inconsistency>();
        
        // Check signal consistency
        var signalFrequencies = new Dictionary<string, int>();
        
        foreach (var match in matches)
        {
            foreach (var signal in match.MatchingSignals)
            {
                if (!signalFrequencies.ContainsKey(signal.Name))
                    signalFrequencies[signal.Name] = 0;
                signalFrequencies[signal.Name]++;
            }
        }
        
        // Find signals that appear in majority but not all
        var total = matches.Count;
        foreach (var (signalName, count) in signalFrequencies)
        {
            var percentage = (double)count / total;
            
            if (percentage >= 0.7 && percentage < 1.0)
            {
                // This is a majority pattern that some implementations don't follow
                var conforming = matches.Where(m => 
                    m.MatchingSignals.Any(s => s.Name == signalName)).ToList();
                var deviating = matches.Except(conforming).ToList();
                
                var majorityEvidence = conforming.First()
                    .MatchingSignals.First(s => s.Name == signalName).Evidence;
                
                inconsistencies.Add(new Inconsistency(
                    PatternName: matches.First().PatternName,
                    Description: $"Inconsistent '{signalName}' across {matches.First().PatternName} implementations",
                    Locations: deviating.Select(m => m.Location).ToList(),
                    MajorityApproach: majorityEvidence ?? signalName,
                    DeviatingApproach: $"{deviating.Count} implementation(s) don't follow this pattern",
                    Severity: Severity.Warning
                ));
            }
        }
        
        // Check for anti-signal presence in some but not others
        var antiSignalPresence = matches
            .SelectMany(m => m.ViolatedSignals.Select(s => (Match: m, Signal: s)))
            .GroupBy(x => x.Signal.Name);
        
        foreach (var antiGroup in antiSignalPresence)
        {
            var affectedMatches = antiGroup.Select(x => x.Match).Distinct().ToList();
            
            if (affectedMatches.Count < matches.Count)
            {
                inconsistencies.Add(new Inconsistency(
                    PatternName: matches.First().PatternName,
                    Description: $"Some {matches.First().PatternName} implementations violate: {antiGroup.Key}",
                    Locations: affectedMatches.Select(m => m.Location).ToList(),
                    MajorityApproach: "No violations",
                    DeviatingApproach: antiGroup.First().Signal.Evidence ?? antiGroup.Key,
                    Severity: Severity.Warning
                ));
            }
        }
        
        return inconsistencies;
    }
}
```

---

## 5. Anti-Pattern Definitions

```yaml
# patterns/anti-patterns/god-class.yaml
anti_pattern:
  name: GodClass
  category: AntiPattern
  description: |
    A class that knows too much or does too much. Violates Single Responsibility 
    Principle by handling multiple unrelated concerns.
  
  severity: High
  
  detection:
    - name: TooManyMethods
      detector: MethodCount
      config:
        threshold: 20
        weight: 0.3
    
    - name: TooManyDependencies
      detector: ConstructorParameterCount
      config:
        threshold: 7
        weight: 0.3
    
    - name: TooManyLines
      detector: LinesOfCode
      config:
        threshold: 500
        weight: 0.2
    
    - name: LowCohesion
      detector: LCOM
      config:
        threshold: 0.8
        weight: 0.2
  
  recommendations:
    - "Extract related methods into focused classes"
    - "Apply Single Responsibility Principle"
    - "Consider domain-driven design bounded contexts"
  
  refactoring_strategies:
    - name: ExtractClass
      description: "Group related methods and extract to new class"
    - name: FacadePattern
      description: "If class coordinates many operations, consider Facade"
```

```yaml
# patterns/anti-patterns/service-locator.yaml
anti_pattern:
  name: ServiceLocator
  category: AntiPattern
  severity: Medium
  description: |
    Using a service locator (IServiceProvider.GetService) instead of 
    constructor injection. Hides dependencies and makes testing difficult.
  
  detection:
    - name: DirectServiceProviderUsage
      detector: MethodInvocation
      config:
        patterns:
          - "IServiceProvider.GetService"
          - "IServiceProvider.GetRequiredService"
          - "ServiceProviderServiceExtensions.GetService"
          - "ServiceProviderServiceExtensions.GetRequiredService"
        weight: 1.0
  
  exceptions:
    - "Factory classes creating instances at runtime"
    - "Plugin or extension loading"
    - "Framework integration points"
    - "Composition roots"
  
  recommendations:
    - "Use constructor injection to declare dependencies explicitly"
    - "If runtime resolution needed, use factory pattern"
    - "For optional dependencies, use IOptions<T> pattern"
```

---

## 6. Sample Analysis Report Structure

```csharp
// CodebaseEvaluator.Reporting/ReportGenerator.cs

public class AnalysisReport
{
    public required string ProjectName { get; init; }
    public required DateTime AnalyzedAt { get; init; }
    public required OverallScore Score { get; init; }
    
    public required PatternSummary PatternSummary { get; init; }
    public required IReadOnlyList<DetectedAntiPattern> AntiPatterns { get; init; }
    public required IReadOnlyList<Inconsistency> Inconsistencies { get; init; }
    public required IReadOnlyList<Recommendation> Recommendations { get; init; }
    public required CodebaseMetrics Metrics { get; init; }
}

public class PatternSummary
{
    public required int TotalPatternsDetected { get; init; }
    public required IReadOnlyDictionary<string, PatternStats> ByPattern { get; init; }
}

public class PatternStats
{
    public required int Occurrences { get; init; }
    public required double AverageConfidence { get; init; }
    public required double ConsistencyScore { get; init; }
    public required IReadOnlyList<string> CommonVariations { get; init; }
}

public class CodebaseMetrics
{
    public required int TotalClasses { get; init; }
    public required int TotalMethods { get; init; }
    public required int TotalLinesOfCode { get; init; }
    public required double AverageCyclomaticComplexity { get; init; }
    public required double AverageMaintainabilityIndex { get; init; }
    public required Dictionary<string, int> DependencyMetrics { get; init; }
}
```

---

## Summary

This implementation provides:

1. **Declarative Pattern Definitions** - YAML-based definitions that separate pattern knowledge from detection code
2. **Signal-Based Detection** - Weighted signals and anti-signals for nuanced pattern matching
3. **Consistency Analysis** - Identifies when patterns are applied inconsistently
4. **Anti-Pattern Detection** - Catches common mistakes and code smells
5. **Extensibility** - Easy to add new patterns without changing core code

The architecture follows clean architecture principles, making it easy to:
- Add new pattern detectors
- Customize scoring weights
- Integrate with CI/CD pipelines
- Generate different report formats
