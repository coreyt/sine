# Multi-Language Codebase Evaluation: Extensibility Architecture

## Executive Summary

This document outlines how to extend the codebase evaluation system to support multiple programming languages (C#, Python, TypeScript) and frameworks (Angular, React, ASP.NET Core, FastAPI). The architecture uses a plugin-based approach with clear abstraction boundaries.

---

## Part 1: Language Comparison Matrix

### 1.1 Parsing Infrastructure

| Language | Primary Parser | AST Access | Type Information |
|----------|---------------|------------|------------------|
| **C#** | Roslyn | Full AST + Semantic Model | Complete (static typing) |
| **TypeScript** | TS Compiler API | Full AST + Type Checker | Complete (static typing) |
| **Python** | ast module / Tree-sitter | AST only (basic) | Limited (dynamic typing) |
| **JavaScript** | Babel / Tree-sitter | AST only | None (requires inference) |

### 1.2 Pattern Expression Differences

| Pattern | C# | TypeScript | Python |
|---------|-----|------------|--------|
| **Dependency Injection** | Constructor injection, `IServiceCollection` | Constructor injection, decorators, modules | Constructor injection, decorators (`@inject`) |
| **Repository** | Interface + class | Interface/type + class | Protocol + class, or duck typing |
| **Factory** | Factory class/method | Factory function/class | Factory function, `__new__`, metaclass |
| **Observer** | Events, `IObservable<T>` | RxJS, EventEmitter | Callbacks, signals, `asyncio` |
| **Singleton** | Static instance, DI scope | Module scope, class instance | Module-level instance, `__new__` |
| **Decorator** | Wrapper class | Higher-order function, class decorator | `@decorator` syntax |

### 1.3 Type System Impact on Detection

```
Detection Confidence by Type System:

Static Typed (C#, TypeScript)
├── Interface implementation: HIGH confidence
├── Type relationships: HIGH confidence  
├── Method signatures: HIGH confidence
└── Generic constraints: HIGH confidence

Dynamic Typed (Python, JavaScript)
├── Interface implementation: MEDIUM (protocols/ABCs)
├── Type relationships: LOW (duck typing)
├── Method signatures: MEDIUM (type hints help)
└── Naming conventions: HIGH (more reliance on names)
```

---

## Part 2: Abstraction Architecture

### 2.1 Core Abstractions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Core Domain Layer                               │
│                      (Language-Agnostic)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │ PatternDefinition│  │  AnalysisResult │  │    QualityMetrics      │ │
│  │                 │  │                 │  │                         │ │
│  │ - Name          │  │ - Patterns      │  │ - Complexity            │ │
│  │ - Category      │  │ - Inconsistencies│  │ - Coupling             │ │
│  │ - Signals       │  │ - Metrics       │  │ - Cohesion             │ │
│  │ - AntiSignals   │  │ - Score         │  │ - TestCoverage         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Unified Code Model (UCM)                      │   │
│  │                                                                  │   │
│  │  Represents code structure in a language-neutral way            │   │
│  │  - Types, Methods, Properties, Parameters                        │   │
│  │  - Relationships (inheritance, composition, dependency)          │   │
│  │  - Annotations/Attributes/Decorators                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Adapters
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Language Provider Layer                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  C# Provider │  │  TS Provider │  │  Py Provider │  │  JS Provdr │ │
│  │              │  │              │  │              │  │            │ │
│  │  - Roslyn    │  │  - TS API    │  │  - ast/typed │  │  - Babel   │ │
│  │  - Semantic  │  │  - Type      │  │  - tree-sit  │  │  - tree-s  │ │
│  │    Model     │  │    Checker   │  │  - mypy      │  │  - Flow?   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Extensions
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Framework Extension Layer                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Angular    │  │    React     │  │  ASP.NET     │  │  FastAPI   │ │
│  │              │  │              │  │    Core      │  │            │ │
│  │  - Modules   │  │  - Hooks     │  │  - Middlewre │  │  - Routes  │ │
│  │  - Services  │  │  - Context   │  │  - Filters   │  │  - Depends │ │
│  │  - RxJS      │  │  - Redux     │  │  - DI        │  │  - Pydantc │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Unified Code Model (UCM)

The UCM is the key abstraction that allows language-agnostic pattern detection:

```typescript
// Core UCM Types (defined in TypeScript for clarity, implemented in each language)

interface CodeUnit {
  id: string;
  name: string;
  kind: CodeUnitKind;
  language: Language;
  framework?: Framework;
  location: SourceLocation;
  
  // Structural
  members: Member[];
  annotations: Annotation[];
  
  // Relationships
  inheritsFrom?: TypeReference[];
  implements?: TypeReference[];
  dependencies: Dependency[];
}

enum CodeUnitKind {
  Class = 'class',
  Interface = 'interface',
  Protocol = 'protocol',      // Python
  AbstractClass = 'abstract',
  Module = 'module',
  Function = 'function',
  Component = 'component',    // Framework-specific
  Service = 'service',        // Framework-specific
}

interface Member {
  name: string;
  kind: MemberKind;
  visibility: Visibility;
  isStatic: boolean;
  isAsync: boolean;
  
  // For methods
  parameters?: Parameter[];
  returnType?: TypeReference;
  
  // For properties/fields
  type?: TypeReference;
  
  // Metrics
  complexity?: number;
  lineCount?: number;
}

interface Dependency {
  target: TypeReference;
  kind: DependencyKind;
  injectionMethod: InjectionMethod;
}

enum DependencyKind {
  Constructor = 'constructor',
  Property = 'property',
  Method = 'method',
  Import = 'import',
  Inheritance = 'inheritance',
}

enum InjectionMethod {
  ConstructorInjection = 'constructor',
  PropertyInjection = 'property',
  ServiceLocator = 'serviceLocator',
  ModuleImport = 'import',
  Decorator = 'decorator',
}

interface TypeReference {
  name: string;
  fullName: string;
  isGeneric: boolean;
  typeArguments?: TypeReference[];
  isNullable: boolean;
  
  // For pattern matching
  matchesPattern(pattern: string): boolean;
}

interface Annotation {
  name: string;
  arguments: Record<string, unknown>;
  
  // Framework detection
  isFrameworkAnnotation: boolean;
  framework?: Framework;
}
```

### 2.3 Language Provider Interface

```typescript
interface ILanguageProvider {
  readonly language: Language;
  readonly fileExtensions: string[];
  
  // Parsing
  parseFile(filePath: string): Promise<CodeUnit[]>;
  parseProject(projectPath: string): Promise<ProjectModel>;
  
  // Type resolution (if available)
  resolveType(reference: TypeReference): Promise<TypeInfo | null>;
  getInheritanceChain(type: TypeReference): Promise<TypeReference[]>;
  
  // Language-specific pattern detection
  getPatternDetectors(): IPatternDetector[];
  
  // Framework detection
  detectFrameworks(project: ProjectModel): Framework[];
}

interface IFrameworkExtension {
  readonly framework: Framework;
  readonly baseLanguage: Language;
  
  // Additional patterns specific to this framework
  getPatternDetectors(): IPatternDetector[];
  
  // Framework-specific code unit transformations
  enrichCodeUnit(unit: CodeUnit): CodeUnit;
  
  // Framework-specific consistency rules
  getConsistencyRules(): IConsistencyRule[];
}
```

---

## Part 3: TypeScript vs Angular Analysis

### 3.1 Why They're Different

```
TypeScript (Base Language)
├── Language features only
│   ├── Classes, interfaces, types
│   ├── Generics, decorators (syntax only)
│   ├── Modules (ES modules)
│   └── Async/await
│
├── Generic patterns
│   ├── Factory functions
│   ├── Module pattern
│   ├── Revealing module
│   └── Basic DI (manual)
│
└── No prescribed architecture


Angular (Framework on TypeScript)
├── Everything from TypeScript, PLUS:
│
├── Decorator-driven architecture
│   ├── @Component, @Injectable, @NgModule
│   ├── @Input, @Output, @ViewChild
│   └── Decorators carry semantic meaning
│
├── Dependency Injection system
│   ├── Hierarchical injectors
│   ├── providedIn: 'root' | 'any' | module
│   ├── InjectionToken for non-class deps
│   └── Factory providers
│
├── Reactive patterns (RxJS)
│   ├── Observable everywhere
│   ├── Subject variants (BehaviorSubject, ReplaySubject)
│   ├── Operators (map, filter, switchMap)
│   └── Async pipe
│
├── Component architecture
│   ├── Smart vs Presentational components
│   ├── OnPush change detection
│   ├── Lifecycle hooks
│   └── Component communication patterns
│
├── State management patterns
│   ├── Services as state
│   ├── NgRx (Redux pattern)
│   ├── Signals (newer)
│   └── Component store
│
└── Module organization
    ├── Feature modules
    ├── Shared modules
    ├── Core module pattern
    └── Lazy loading
```

### 3.2 Pattern Detection Differences

| Pattern | Plain TypeScript Detection | Angular Detection |
|---------|---------------------------|-------------------|
| **Service/Injectable** | Class with methods, possibly singleton | `@Injectable()` decorator, `providedIn` |
| **Repository** | Class implementing interface | Service with HttpClient dependency |
| **Observer** | EventEmitter, callbacks | RxJS Observable, Subject usage |
| **Dependency Injection** | Constructor params | `@Injectable`, hierarchical injection |
| **Factory** | Factory function | `useFactory` in providers |
| **Singleton** | Module-level instance | `providedIn: 'root'` |
| **Mediator** | Manual implementation | NgRx Store, or service-based |
| **Component** | N/A | `@Component` decorator |
| **Smart/Dumb** | N/A | OnPush + Input/Output analysis |

### 3.3 Angular-Specific Pattern Catalog

```yaml
# patterns/frameworks/angular/injectable-service.yaml
pattern:
  name: AngularService
  framework: Angular
  base_language: TypeScript
  category: Architectural
  
  signals:
    - name: InjectableDecorator
      weight: 0.4
      detector: DecoratorPresence
      config:
        decorator: "Injectable"
        
    - name: ProvidedInRoot
      weight: 0.2
      detector: DecoratorArgument
      config:
        decorator: "Injectable"
        argument: "providedIn"
        value: "'root'"
        
    - name: ConstructorDependencies
      weight: 0.2
      detector: ConstructorInjection
      config:
        min_dependencies: 1
        
    - name: HttpClientUsage
      weight: 0.2
      detector: TypeUsage
      config:
        types: ["HttpClient"]
  
  sub_patterns:
    - name: DataService
      additional_signals:
        - HttpClient dependency
        - Returns Observable<T>
        
    - name: StateService
      additional_signals:
        - BehaviorSubject usage
        - Exposes Observable (not Subject)
        
    - name: FacadeService
      additional_signals:
        - Depends on multiple other services
        - Simplifies API for components

---
# patterns/frameworks/angular/smart-component.yaml
pattern:
  name: SmartComponent
  framework: Angular
  category: ComponentArchitecture
  
  signals:
    - name: ComponentDecorator
      weight: 0.2
      detector: DecoratorPresence
      config:
        decorator: "Component"
        
    - name: ServiceDependencies
      weight: 0.3
      detector: ConstructorDependency
      config:
        types: ["*Service", "*Facade", "*Store"]
        min_count: 1
        
    - name: StoreInteraction
      weight: 0.2
      detector: MethodInvocation
      config:
        patterns: ["store.dispatch", "store.select"]
        
    - name: SubscriptionManagement
      weight: 0.15
      detector: MethodPresence
      config:
        patterns: ["ngOnDestroy"]
        
    - name: ChildComponentUsage
      weight: 0.15
      detector: TemplateAnalysis
      config:
        has_child_components: true

---
# patterns/frameworks/angular/presentational-component.yaml
pattern:
  name: PresentationalComponent
  framework: Angular
  category: ComponentArchitecture
  
  signals:
    - name: OnPushStrategy
      weight: 0.3
      detector: DecoratorArgument
      config:
        decorator: "Component"
        argument: "changeDetection"
        value: "ChangeDetectionStrategy.OnPush"
        
    - name: InputsOutputsOnly
      weight: 0.3
      detector: MemberDecorators
      config:
        allowed: ["Input", "Output"]
        no_service_injection: true
        
    - name: NoServiceDependencies
      weight: 0.25
      detector: ConstructorDependency
      config:
        forbidden_types: ["*Service", "*Store", "HttpClient"]
        
    - name: PureTransformation
      weight: 0.15
      detector: MethodAnalysis
      config:
        no_side_effects: true

---
# patterns/frameworks/angular/rxjs-patterns.yaml
pattern:
  name: RxJSBestPractices
  framework: Angular
  category: BestPractice
  
  signals:
    - name: AsyncPipeUsage
      weight: 0.25
      detector: TemplateAnalysis
      config:
        pattern: "| async"
        
    - name: TakeUntilDestroy
      weight: 0.25
      detector: OperatorUsage
      config:
        operators: ["takeUntil", "takeUntilDestroyed"]
        
    - name: SubjectEncapsulation
      weight: 0.25
      detector: MemberVisibility
      config:
        pattern: "private.*Subject"
        exposed_as: "Observable"
        
    - name: AvoidNestedSubscribes
      weight: 0.25
      detector: CodePattern
      config:
        forbidden: "subscribe.*subscribe"
        
  anti_signals:
    - name: SubscribeInComponent
      weight: -0.2
      detector: MethodInvocation
      config:
        pattern: "\.subscribe\("
        context: "Component"
        description: "Prefer async pipe over manual subscribe"
        
    - name: UnmanagedSubscription
      weight: -0.3
      detector: SubscriptionAnalysis
      config:
        no_unsubscribe: true
        no_takeUntil: true
```

### 3.4 Framework Detection Logic

```typescript
// How to detect if a TypeScript project uses Angular

interface FrameworkDetector {
  detect(project: ProjectModel): FrameworkDetectionResult;
}

class AngularDetector implements FrameworkDetector {
  detect(project: ProjectModel): FrameworkDetectionResult {
    const signals: DetectionSignal[] = [];
    
    // Signal 1: Package dependencies
    const packageJson = project.getFile('package.json');
    if (packageJson) {
      const deps = JSON.parse(packageJson.content);
      if (deps.dependencies?.['@angular/core']) {
        signals.push({
          name: 'AngularCoreDependency',
          confidence: 0.9,
          evidence: `@angular/core version ${deps.dependencies['@angular/core']}`
        });
      }
    }
    
    // Signal 2: Angular CLI config
    if (project.hasFile('angular.json') || project.hasFile('.angular.json')) {
      signals.push({
        name: 'AngularCliConfig',
        confidence: 0.95,
        evidence: 'angular.json present'
      });
    }
    
    // Signal 3: Component decorators
    const componentCount = project.files
      .filter(f => f.extension === '.ts')
      .filter(f => f.content.includes('@Component'))
      .length;
    
    if (componentCount > 0) {
      signals.push({
        name: 'ComponentDecorators',
        confidence: 0.8,
        evidence: `${componentCount} @Component decorators found`
      });
    }
    
    // Signal 4: NgModule
    const hasNgModule = project.files.some(f => f.content.includes('@NgModule'));
    if (hasNgModule) {
      signals.push({
        name: 'NgModulePresent',
        confidence: 0.85,
        evidence: '@NgModule decorator found'
      });
    }
    
    const totalConfidence = signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length;
    
    return {
      framework: Framework.Angular,
      detected: totalConfidence > 0.7,
      confidence: totalConfidence,
      version: this.detectVersion(project),
      signals
    };
  }
}
```

---

## Part 4: Cross-Language Pattern Definitions

### 4.1 Universal Pattern with Language Variants

```yaml
# patterns/universal/repository.yaml
pattern:
  name: Repository
  category: Architectural
  is_universal: true
  
  description: |
    Mediates between domain and data mapping layers. Implementation
    varies by language but concept remains the same.
  
  # Language-agnostic signals (applied to UCM)
  universal_signals:
    - name: DataAccessMethods
      weight: 0.25
      detector: MethodSignature
      config:
        patterns:
          - { prefix: ["get", "find", "fetch"], min: 1 }
          - { prefix: ["add", "create", "insert", "save"], min: 1 }
          - { prefix: ["update", "modify"], min: 0 }
          - { prefix: ["delete", "remove"], min: 1 }
        total_min: 3
    
    - name: EntityFocused
      weight: 0.20
      detector: GenericOrTypedMethods
      config:
        description: "Methods work with a single entity type"
  
  # Language-specific signal extensions
  language_variants:
    
    csharp:
      additional_signals:
        - name: ImplementsIRepository
          weight: 0.25
          detector: InterfaceImplementation
          config:
            patterns: ["IRepository*", "*Repository"]
            
        - name: DbContextDependency
          weight: 0.20
          detector: ConstructorDependency
          config:
            types: ["DbContext", "*DbContext"]
            
        - name: AsyncMethods
          weight: 0.10
          detector: MethodSignature
          config:
            suffix: "Async"
            returns: "Task<*>"
    
    typescript:
      additional_signals:
        - name: ImplementsInterface
          weight: 0.20
          detector: InterfaceImplementation
          config:
            patterns: ["*Repository", "I*Repository"]
            
        - name: ReturnsPromise
          weight: 0.15
          detector: MethodReturnType
          config:
            types: ["Promise<*>"]
            
        - name: TypeORMUsage
          weight: 0.15
          detector: ImportAnalysis
          config:
            packages: ["typeorm", "@prisma/client", "mongoose"]
    
    typescript_angular:
      extends: typescript
      additional_signals:
        - name: InjectableDecorator
          weight: 0.15
          detector: DecoratorPresence
          config:
            decorator: "Injectable"
            
        - name: HttpClientDependency
          weight: 0.15
          detector: ConstructorDependency
          config:
            types: ["HttpClient"]
            
        - name: ReturnsObservable
          weight: 0.15
          detector: MethodReturnType
          config:
            types: ["Observable<*>"]
    
    python:
      additional_signals:
        - name: ProtocolOrABC
          weight: 0.20
          detector: InheritanceAnalysis
          config:
            bases: ["Protocol", "ABC", "*Repository"]
            
        - name: SQLAlchemyUsage
          weight: 0.15
          detector: ImportAnalysis
          config:
            modules: ["sqlalchemy", "databases", "tortoise"]
            
        - name: AsyncMethods
          weight: 0.15
          detector: MethodSignature
          config:
            has_async: true
            
        - name: TypeHints
          weight: 0.10
          detector: TypeAnnotationPresence
          config:
            min_coverage: 0.8
```

### 4.2 Framework-Specific Patterns (Non-Universal)

```yaml
# patterns/frameworks/angular/ngrx-store.yaml
pattern:
  name: NgRxStore
  framework: Angular
  is_universal: false
  
  description: |
    Redux-inspired state management for Angular using NgRx.
    Angular-specific pattern with no direct equivalent in other languages.
  
  signals:
    - name: StoreModuleImport
      weight: 0.3
      detector: ModuleAnalysis
      config:
        imports: ["StoreModule.forRoot", "StoreModule.forFeature"]
        
    - name: ReducerFunction
      weight: 0.25
      detector: FunctionSignature
      config:
        pattern: "createReducer|on("
        
    - name: ActionCreators
      weight: 0.2
      detector: FunctionCall
      config:
        pattern: "createAction"
        
    - name: Selectors
      weight: 0.15
      detector: FunctionCall
      config:
        pattern: "createSelector|createFeatureSelector"
        
    - name: Effects
      weight: 0.1
      detector: DecoratorPresence
      config:
        decorator: "Effect"
        or_class: "extends Effects"

  consistency_rules:
    - name: ActionNaming
      rule: NamingConvention
      config:
        pattern: "[Feature] Action Name"
        
    - name: SelectorPrefix
      rule: NamingConvention
      config:
        pattern: "select*"
```

---

## Part 5: Project Structure for Multi-Language Support

### 5.1 Revised Architecture

```
codebase-evaluator/
├── packages/
│   │
│   ├── core/                           # Language-agnostic core
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── unified-code-model/  # UCM types
│   │   │   │   ├── patterns/            # Pattern definitions
│   │   │   │   ├── scoring/             # Scoring logic
│   │   │   │   └── reporting/           # Report generation
│   │   │   │
│   │   │   ├── analysis/
│   │   │   │   ├── pattern-matcher.ts   # UCM-based matching
│   │   │   │   ├── consistency-analyzer.ts
│   │   │   │   └── quality-metrics.ts
│   │   │   │
│   │   │   └── interfaces/
│   │   │       ├── language-provider.ts
│   │   │       ├── framework-extension.ts
│   │   │       └── pattern-detector.ts
│   │   │
│   │   └── package.json
│   │
│   ├── provider-csharp/                # C# language provider
│   │   ├── src/
│   │   │   ├── roslyn-parser.ts        # Roslyn integration
│   │   │   ├── ucm-adapter.ts          # Convert to UCM
│   │   │   ├── type-resolver.ts
│   │   │   └── detectors/
│   │   │       ├── repository-detector.ts
│   │   │       └── ...
│   │   └── package.json
│   │
│   ├── provider-typescript/            # TypeScript language provider
│   │   ├── src/
│   │   │   ├── ts-parser.ts            # TS Compiler API
│   │   │   ├── ucm-adapter.ts
│   │   │   ├── type-resolver.ts
│   │   │   └── detectors/
│   │   └── package.json
│   │
│   ├── provider-python/                # Python language provider
│   │   ├── src/
│   │   │   ├── ast-parser.ts           # Python ast via subprocess
│   │   │   ├── tree-sitter-parser.ts   # Alternative parser
│   │   │   ├── ucm-adapter.ts
│   │   │   └── detectors/
│   │   └── package.json
│   │
│   ├── framework-angular/              # Angular extension
│   │   ├── src/
│   │   │   ├── angular-detector.ts     # Framework detection
│   │   │   ├── decorator-analyzer.ts
│   │   │   ├── rxjs-analyzer.ts
│   │   │   ├── template-analyzer.ts
│   │   │   └── detectors/
│   │   │       ├── component-detector.ts
│   │   │       ├── service-detector.ts
│   │   │       ├── ngrx-detector.ts
│   │   │       └── ...
│   │   └── package.json
│   │
│   ├── framework-react/                # React extension
│   │   ├── src/
│   │   │   ├── react-detector.ts
│   │   │   ├── hook-analyzer.ts
│   │   │   ├── jsx-analyzer.ts
│   │   │   └── detectors/
│   │   └── package.json
│   │
│   ├── framework-aspnetcore/           # ASP.NET Core extension
│   │   └── ...
│   │
│   ├── framework-fastapi/              # FastAPI extension
│   │   └── ...
│   │
│   └── cli/                            # Command-line interface
│       └── ...
│
├── patterns/                           # Pattern definitions (YAML)
│   ├── universal/                      # Cross-language patterns
│   │   ├── repository.yaml
│   │   ├── factory.yaml
│   │   ├── observer.yaml
│   │   └── ...
│   │
│   ├── languages/                      # Language-specific patterns
│   │   ├── csharp/
│   │   ├── typescript/
│   │   └── python/
│   │
│   └── frameworks/                     # Framework-specific patterns
│       ├── angular/
│       ├── react/
│       ├── aspnetcore/
│       └── fastapi/
│
└── tests/
    ├── fixtures/
    │   ├── csharp/
    │   ├── typescript/
    │   ├── typescript-angular/
    │   └── python/
    └── ...
```

### 5.2 Plugin Registration

```typescript
// packages/core/src/plugin-registry.ts

export class PluginRegistry {
  private languageProviders = new Map<Language, ILanguageProvider>();
  private frameworkExtensions = new Map<Framework, IFrameworkExtension>();
  
  registerLanguageProvider(provider: ILanguageProvider): void {
    this.languageProviders.set(provider.language, provider);
  }
  
  registerFrameworkExtension(extension: IFrameworkExtension): void {
    this.frameworkExtensions.set(extension.framework, extension);
  }
  
  async analyzeProject(projectPath: string): Promise<AnalysisResult> {
    // 1. Detect language(s)
    const languages = await this.detectLanguages(projectPath);
    
    // 2. Get appropriate providers
    const providers = languages.map(lang => this.languageProviders.get(lang));
    
    // 3. Parse project with each provider
    const codeUnits: CodeUnit[] = [];
    for (const provider of providers) {
      const units = await provider.parseProject(projectPath);
      codeUnits.push(...units);
    }
    
    // 4. Detect frameworks
    const frameworks = this.detectFrameworks(codeUnits, projectPath);
    
    // 5. Enrich code units with framework-specific info
    for (const framework of frameworks) {
      const extension = this.frameworkExtensions.get(framework);
      if (extension) {
        for (let i = 0; i < codeUnits.length; i++) {
          codeUnits[i] = extension.enrichCodeUnit(codeUnits[i]);
        }
      }
    }
    
    // 6. Run pattern detection (universal + language + framework specific)
    const patterns = await this.detectPatterns(codeUnits, languages, frameworks);
    
    // 7. Analyze consistency
    const inconsistencies = await this.analyzeConsistency(patterns, frameworks);
    
    // 8. Generate report
    return this.generateResult(patterns, inconsistencies, codeUnits);
  }
}

// Usage
const registry = new PluginRegistry();

// Register language providers
registry.registerLanguageProvider(new CSharpProvider());
registry.registerLanguageProvider(new TypeScriptProvider());
registry.registerLanguageProvider(new PythonProvider());

// Register framework extensions
registry.registerFrameworkExtension(new AngularExtension());
registry.registerFrameworkExtension(new ReactExtension());
registry.registerFrameworkExtension(new AspNetCoreExtension());
registry.registerFrameworkExtension(new FastApiExtension());

// Analyze
const result = await registry.analyzeProject('./my-angular-project');
```

---

## Part 6: Implementation Considerations

### 6.1 Type Information Challenges

```
┌─────────────────────────────────────────────────────────────────┐
│                  Type Information Quality                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  C# (Roslyn)                                                    │
│  ├── Full semantic model                                        │
│  ├── All types resolved                                         │
│  ├── Generic instantiation known                                │
│  └── Detection confidence: VERY HIGH                            │
│                                                                 │
│  TypeScript (TS Compiler API)                                   │
│  ├── Full type checker                                          │
│  ├── Types resolved (with inference)                            │
│  ├── May need tsconfig for full resolution                      │
│  └── Detection confidence: HIGH                                 │
│                                                                 │
│  Python (ast + type hints)                                      │
│  ├── Type hints optional                                        │
│  ├── Runtime typing (duck typing)                               │
│  ├── Can use mypy for better inference                          │
│  └── Detection confidence: MEDIUM                               │
│       → Compensate with stronger naming convention signals      │
│       → Use Protocol/ABC detection                              │
│       → Analyze actual method calls for duck typing             │
│                                                                 │
│  JavaScript (no types)                                          │
│  ├── No type information                                        │
│  ├── JSDoc comments may help                                    │
│  ├── Flow types if present                                      │
│  └── Detection confidence: LOW                                  │
│       → Heavy reliance on naming conventions                    │
│       → Structural analysis of method bodies                    │
│       → Import/export patterns                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Compensating for Weak Type Systems

```typescript
// For Python/JavaScript, we need alternative detection strategies

interface WeakTypeCompensation {
  // Naming conventions become more important
  namingPatternWeight: number;  // Increase from 0.15 to 0.30
  
  // Structural analysis
  methodBodyAnalysis: boolean;  // Analyze what methods actually do
  
  // Import analysis
  importPatterns: boolean;      // What modules are imported
  
  // Call site analysis
  usagePatterns: boolean;       // How is this class/function used
}

// Example: Repository detection in Python
const pythonRepositoryDetection = {
  signals: [
    // Type-based signals (lower weight due to optional hints)
    { name: 'InheritsProtocol', weight: 0.15, requiresTypeHints: true },
    
    // Naming-based signals (higher weight)
    { name: 'ClassNameEndsWithRepository', weight: 0.25 },
    { name: 'MethodNamesFollowCrudPattern', weight: 0.20 },
    
    // Import-based signals
    { name: 'ImportsSQLAlchemy', weight: 0.20 },
    { name: 'ImportsDatabases', weight: 0.20 },
    
    // Structural signals
    { name: 'HasSessionOrConnectionMember', weight: 0.15 },
    { name: 'MethodsAreAsync', weight: 0.10 },
  ]
};
```

### 6.3 Framework Detection Priority

```typescript
// When analyzing a project, detect frameworks in order of specificity

const frameworkDetectionOrder: FrameworkDetector[] = [
  // Most specific first
  new NgRxDetector(),      // NgRx is Angular + specific library
  new AngularDetector(),   // Angular is TypeScript + framework
  
  new ReduxDetector(),     // Redux could be React or vanilla
  new ReactDetector(),     // React is TypeScript/JavaScript + framework
  
  new FastApiDetector(),   // FastAPI is Python + framework
  new DjangoDetector(),    // Django is Python + framework
  
  new AspNetCoreDetector(), // ASP.NET Core is C# + framework
  
  // Language detection is implicit from file extensions
];

// A project can have multiple frameworks
// e.g., Angular frontend + ASP.NET Core backend in monorepo
```

---

## Part 7: Summary Comparison

### TypeScript vs Angular: Key Differences for Detection

| Aspect | Plain TypeScript | Angular |
|--------|------------------|---------|
| **DI Detection** | Manual constructor analysis | `@Injectable` decorator + `providedIn` |
| **Service Pattern** | Class with methods | Service with specific Angular lifecycle |
| **Observable Usage** | Optional | Core pattern (RxJS integration) |
| **Component Pattern** | N/A | `@Component` + template analysis |
| **Module Organization** | ES modules | `@NgModule` with specific structure |
| **State Management** | Various approaches | Services, NgRx, Signals |
| **Consistency Rules** | General TypeScript rules | Angular style guide + RxJS patterns |
| **Anti-patterns** | General OOP anti-patterns | Angular-specific (subscribe in component, etc.) |

### Recommendation: Treat as Separate Targets

```yaml
# Configuration example
analysis:
  targets:
    - language: typescript
      # Basic TypeScript analysis
      
    - language: typescript
      framework: angular
      # TypeScript + Angular patterns
      # More specific, more rules
      
    - language: typescript
      framework: react
      # TypeScript + React patterns
      # Different component model
```

The key insight is that **Angular is not just TypeScript with extra libraries** — it's a complete architectural paradigm with its own patterns, anti-patterns, and consistency rules that require dedicated detection logic.
