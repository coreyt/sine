# Language Provider Implementations

This document provides concrete implementation examples for each language provider.

---

## 1. Unified Code Model (UCM) Core Types

```typescript
// packages/core/src/domain/unified-code-model/types.ts

export enum Language {
  CSharp = 'csharp',
  TypeScript = 'typescript',
  Python = 'python',
  JavaScript = 'javascript',
}

export enum Framework {
  None = 'none',
  Angular = 'angular',
  React = 'react',
  Vue = 'vue',
  AspNetCore = 'aspnetcore',
  FastAPI = 'fastapi',
  Django = 'django',
  NestJS = 'nestjs',
}

export interface CodeUnit {
  id: string;
  name: string;
  fullyQualifiedName: string;
  kind: CodeUnitKind;
  language: Language;
  framework: Framework;
  location: SourceLocation;
  
  // Structure
  members: Member[];
  annotations: Annotation[];
  typeParameters: TypeParameter[];
  
  // Relationships
  baseTypes: TypeReference[];
  implementedInterfaces: TypeReference[];
  dependencies: Dependency[];
  
  // Metrics (computed)
  metrics?: CodeUnitMetrics;
}

export interface Member {
  name: string;
  kind: MemberKind;
  visibility: Visibility;
  isStatic: boolean;
  isAsync: boolean;
  isAbstract: boolean;
  
  // Method-specific
  parameters?: Parameter[];
  returnType?: TypeReference;
  body?: MethodBody;
  
  // Property/Field-specific
  type?: TypeReference;
  hasGetter?: boolean;
  hasSetter?: boolean;
  
  annotations: Annotation[];
  location: SourceLocation;
}

export interface MethodBody {
  lineCount: number;
  cyclomaticComplexity: number;
  
  // For detailed analysis
  invocations: MethodInvocation[];
  variableDeclarations: VariableDeclaration[];
  controlFlowStatements: ControlFlowStatement[];
}

export interface Dependency {
  target: TypeReference;
  kind: DependencyKind;
  injectionSite: InjectionSite;
  isOptional: boolean;
}

export interface Annotation {
  name: string;
  fullName: string;
  arguments: Map<string, AnnotationArgument>;
  location: SourceLocation;
}
```

---

## 2. C# Provider Implementation

```typescript
// packages/provider-csharp/src/csharp-provider.ts

import { spawn } from 'child_process';
import { ILanguageProvider, CodeUnit, Language, ProjectModel } from '@codebase-eval/core';

export class CSharpProvider implements ILanguageProvider {
  readonly language = Language.CSharp;
  readonly fileExtensions = ['.cs'];
  
  private roslynBridge: RoslynBridge;
  
  constructor() {
    // Roslyn runs in .NET, so we need a bridge
    this.roslynBridge = new RoslynBridge();
  }
  
  async parseFile(filePath: string): Promise<CodeUnit[]> {
    const roslynResult = await this.roslynBridge.analyzeFile(filePath);
    return this.convertToUCM(roslynResult);
  }
  
  async parseProject(projectPath: string): Promise<ProjectModel> {
    // Find solution or csproj files
    const solutionFile = await this.findSolutionFile(projectPath);
    const roslynResult = await this.roslynBridge.analyzeSolution(solutionFile);
    
    return {
      path: projectPath,
      language: Language.CSharp,
      codeUnits: this.convertAllToUCM(roslynResult),
      dependencies: this.extractDependencies(roslynResult),
    };
  }
  
  private convertToUCM(roslynResult: RoslynAnalysisResult): CodeUnit[] {
    const units: CodeUnit[] = [];
    
    for (const classInfo of roslynResult.classes) {
      units.push({
        id: classInfo.fullName,
        name: classInfo.name,
        fullyQualifiedName: classInfo.fullName,
        kind: this.mapKind(classInfo.kind),
        language: Language.CSharp,
        framework: Framework.None, // Will be enriched later
        location: {
          filePath: classInfo.filePath,
          startLine: classInfo.startLine,
          endLine: classInfo.endLine,
        },
        members: classInfo.members.map(m => this.convertMember(m)),
        annotations: classInfo.attributes.map(a => this.convertAttribute(a)),
        typeParameters: classInfo.typeParameters,
        baseTypes: classInfo.baseTypes.map(t => this.convertTypeRef(t)),
        implementedInterfaces: classInfo.interfaces.map(t => this.convertTypeRef(t)),
        dependencies: this.extractDependencies(classInfo),
      });
    }
    
    return units;
  }
  
  private extractDependencies(classInfo: RoslynClassInfo): Dependency[] {
    const deps: Dependency[] = [];
    
    // Constructor injection
    for (const ctor of classInfo.constructors) {
      for (const param of ctor.parameters) {
        deps.push({
          target: this.convertTypeRef(param.type),
          kind: DependencyKind.Constructor,
          injectionSite: {
            kind: 'constructor',
            parameterName: param.name,
            parameterIndex: param.index,
          },
          isOptional: param.hasDefaultValue,
        });
      }
    }
    
    // Property injection (look for [Inject] or similar)
    for (const prop of classInfo.properties) {
      if (prop.attributes.some(a => a.name === 'Inject' || a.name === 'Dependency')) {
        deps.push({
          target: this.convertTypeRef(prop.type),
          kind: DependencyKind.Property,
          injectionSite: {
            kind: 'property',
            propertyName: prop.name,
          },
          isOptional: prop.type.isNullable,
        });
      }
    }
    
    return deps;
  }
  
  getPatternDetectors(): IPatternDetector[] {
    return [
      new CSharpRepositoryDetector(),
      new CSharpFactoryDetector(),
      new CSharpOptionsPatternDetector(),
      new CSharpMediatorDetector(),
      // ... more C#-specific detectors
    ];
  }
  
  detectFrameworks(project: ProjectModel): Framework[] {
    const frameworks: Framework[] = [];
    
    // Check for ASP.NET Core
    if (this.hasPackageReference(project, 'Microsoft.AspNetCore')) {
      frameworks.push(Framework.AspNetCore);
    }
    
    return frameworks;
  }
}

// Roslyn Bridge - calls out to .NET process
class RoslynBridge {
  private process: ChildProcess | null = null;
  
  async analyzeSolution(solutionPath: string): Promise<RoslynAnalysisResult> {
    // Start the .NET Roslyn analyzer process
    const result = await this.callRoslynAnalyzer('analyze-solution', { solutionPath });
    return JSON.parse(result);
  }
  
  private async callRoslynAnalyzer(command: string, args: object): Promise<string> {
    return new Promise((resolve, reject) => {
      const proc = spawn('dotnet', [
        'run',
        '--project', './tools/RoslynAnalyzer',
        '--',
        command,
        JSON.stringify(args)
      ]);
      
      let output = '';
      proc.stdout.on('data', (data) => output += data);
      proc.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Roslyn analyzer failed with code ${code}`));
      });
    });
  }
}
```

---

## 3. TypeScript Provider Implementation

```typescript
// packages/provider-typescript/src/typescript-provider.ts

import * as ts from 'typescript';
import * as path from 'path';
import { ILanguageProvider, CodeUnit, Language, Framework } from '@codebase-eval/core';

export class TypeScriptProvider implements ILanguageProvider {
  readonly language = Language.TypeScript;
  readonly fileExtensions = ['.ts', '.tsx'];
  
  private program: ts.Program | null = null;
  private typeChecker: ts.TypeChecker | null = null;
  
  async parseProject(projectPath: string): Promise<ProjectModel> {
    // Find tsconfig.json
    const configPath = ts.findConfigFile(projectPath, ts.sys.fileExists, 'tsconfig.json');
    if (!configPath) {
      throw new Error('tsconfig.json not found');
    }
    
    // Parse tsconfig
    const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
    const parsedConfig = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      path.dirname(configPath)
    );
    
    // Create program with full type checking
    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
    this.typeChecker = this.program.getTypeChecker();
    
    // Analyze all source files
    const codeUnits: CodeUnit[] = [];
    
    for (const sourceFile of this.program.getSourceFiles()) {
      if (!sourceFile.isDeclarationFile) {
        const units = this.analyzeSourceFile(sourceFile);
        codeUnits.push(...units);
      }
    }
    
    return {
      path: projectPath,
      language: Language.TypeScript,
      codeUnits,
      dependencies: this.extractPackageDependencies(projectPath),
    };
  }
  
  private analyzeSourceFile(sourceFile: ts.SourceFile): CodeUnit[] {
    const units: CodeUnit[] = [];
    
    const visit = (node: ts.Node) => {
      if (ts.isClassDeclaration(node) && node.name) {
        units.push(this.analyzeClass(node, sourceFile));
      } else if (ts.isInterfaceDeclaration(node)) {
        units.push(this.analyzeInterface(node, sourceFile));
      } else if (ts.isFunctionDeclaration(node) && node.name) {
        units.push(this.analyzeFunction(node, sourceFile));
      }
      
      ts.forEachChild(node, visit);
    };
    
    visit(sourceFile);
    return units;
  }
  
  private analyzeClass(node: ts.ClassDeclaration, sourceFile: ts.SourceFile): CodeUnit {
    const symbol = this.typeChecker!.getSymbolAtLocation(node.name!);
    const type = this.typeChecker!.getTypeAtDeclaration(node);
    
    return {
      id: this.getFullyQualifiedName(symbol),
      name: node.name!.text,
      fullyQualifiedName: this.getFullyQualifiedName(symbol),
      kind: this.determineKind(node),
      language: Language.TypeScript,
      framework: Framework.None,
      location: this.getLocation(node, sourceFile),
      
      members: this.extractMembers(node),
      annotations: this.extractDecorators(node),
      typeParameters: this.extractTypeParameters(node),
      baseTypes: this.extractBaseTypes(node),
      implementedInterfaces: this.extractImplementedInterfaces(node),
      dependencies: this.extractDependencies(node),
    };
  }
  
  private extractDecorators(node: ts.ClassDeclaration): Annotation[] {
    const decorators: Annotation[] = [];
    
    // TypeScript 5.0+ uses getDecorators
    const nodeDecorators = ts.getDecorators(node) || [];
    
    for (const decorator of nodeDecorators) {
      if (ts.isCallExpression(decorator.expression)) {
        const name = decorator.expression.expression.getText();
        const args = this.extractDecoratorArguments(decorator.expression);
        
        decorators.push({
          name,
          fullName: name,
          arguments: args,
          location: this.getLocation(decorator, node.getSourceFile()),
        });
      }
    }
    
    return decorators;
  }
  
  private extractDependencies(node: ts.ClassDeclaration): Dependency[] {
    const deps: Dependency[] = [];
    
    // Find constructor
    const constructor = node.members.find(ts.isConstructorDeclaration);
    if (constructor) {
      for (let i = 0; i < constructor.parameters.length; i++) {
        const param = constructor.parameters[i];
        const type = this.typeChecker!.getTypeAtLocation(param);
        
        deps.push({
          target: this.convertType(type),
          kind: DependencyKind.Constructor,
          injectionSite: {
            kind: 'constructor',
            parameterName: param.name.getText(),
            parameterIndex: i,
          },
          isOptional: !!param.questionToken || !!param.initializer,
        });
      }
    }
    
    return deps;
  }
  
  getPatternDetectors(): IPatternDetector[] {
    return [
      new TypeScriptRepositoryDetector(),
      new TypeScriptFactoryDetector(),
      new TypeScriptModulePatternDetector(),
      new TypeScriptObserverDetector(),
    ];
  }
  
  detectFrameworks(project: ProjectModel): Framework[] {
    const frameworks: Framework[] = [];
    const packageJson = this.readPackageJson(project.path);
    
    if (packageJson) {
      const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
      
      if (deps['@angular/core']) {
        frameworks.push(Framework.Angular);
      }
      if (deps['react']) {
        frameworks.push(Framework.React);
      }
      if (deps['vue']) {
        frameworks.push(Framework.Vue);
      }
      if (deps['@nestjs/core']) {
        frameworks.push(Framework.NestJS);
      }
    }
    
    return frameworks;
  }
}
```

---

## 4. Python Provider Implementation

```typescript
// packages/provider-python/src/python-provider.ts

import { spawn } from 'child_process';
import * as path from 'path';
import { ILanguageProvider, CodeUnit, Language, Framework } from '@codebase-eval/core';

export class PythonProvider implements ILanguageProvider {
  readonly language = Language.Python;
  readonly fileExtensions = ['.py'];
  
  async parseProject(projectPath: string): Promise<ProjectModel> {
    // Use Python ast module via subprocess
    const analysisResult = await this.runPythonAnalyzer(projectPath);
    
    return {
      path: projectPath,
      language: Language.Python,
      codeUnits: this.convertToUCM(analysisResult),
      dependencies: this.extractDependencies(projectPath),
    };
  }
  
  private async runPythonAnalyzer(projectPath: string): Promise<PythonAnalysisResult> {
    return new Promise((resolve, reject) => {
      const proc = spawn('python', [
        path.join(__dirname, 'python_analyzer.py'),
        projectPath
      ]);
      
      let output = '';
      let error = '';
      
      proc.stdout.on('data', (data) => output += data);
      proc.stderr.on('data', (data) => error += data);
      
      proc.on('close', (code) => {
        if (code === 0) {
          resolve(JSON.parse(output));
        } else {
          reject(new Error(`Python analyzer failed: ${error}`));
        }
      });
    });
  }
  
  private convertToUCM(result: PythonAnalysisResult): CodeUnit[] {
    const units: CodeUnit[] = [];
    
    for (const classInfo of result.classes) {
      units.push({
        id: `${classInfo.module}.${classInfo.name}`,
        name: classInfo.name,
        fullyQualifiedName: `${classInfo.module}.${classInfo.name}`,
        kind: this.determineKind(classInfo),
        language: Language.Python,
        framework: Framework.None,
        location: {
          filePath: classInfo.file,
          startLine: classInfo.lineno,
          endLine: classInfo.end_lineno,
        },
        
        members: this.convertMembers(classInfo),
        annotations: this.convertDecorators(classInfo),
        typeParameters: [], // Python doesn't have explicit type parameters
        baseTypes: classInfo.bases.map(b => this.convertTypeRef(b)),
        implementedInterfaces: [], // Handled via Protocol
        dependencies: this.extractClassDependencies(classInfo),
      });
    }
    
    return units;
  }
  
  private determineKind(classInfo: PythonClassInfo): CodeUnitKind {
    // Check if it's a Protocol (interface equivalent)
    if (classInfo.bases.some(b => b.name === 'Protocol')) {
      return CodeUnitKind.Protocol;
    }
    
    // Check if it's an ABC
    if (classInfo.bases.some(b => b.name === 'ABC')) {
      return CodeUnitKind.AbstractClass;
    }
    
    // Check decorators
    if (classInfo.decorators.some(d => d.name === 'dataclass')) {
      return CodeUnitKind.DataClass;
    }
    
    return CodeUnitKind.Class;
  }
  
  private extractClassDependencies(classInfo: PythonClassInfo): Dependency[] {
    const deps: Dependency[] = [];
    
    // Find __init__ method
    const initMethod = classInfo.methods.find(m => m.name === '__init__');
    if (initMethod) {
      // Skip 'self' parameter
      for (let i = 1; i < initMethod.parameters.length; i++) {
        const param = initMethod.parameters[i];
        
        // Python type hints
        if (param.annotation) {
          deps.push({
            target: this.convertTypeRef(param.annotation),
            kind: DependencyKind.Constructor,
            injectionSite: {
              kind: 'constructor',
              parameterName: param.name,
              parameterIndex: i - 1, // Exclude self
            },
            isOptional: param.has_default,
          });
        } else {
          // No type hint - try to infer from naming convention
          deps.push({
            target: this.inferTypeFromName(param.name),
            kind: DependencyKind.Constructor,
            injectionSite: {
              kind: 'constructor',
              parameterName: param.name,
              parameterIndex: i - 1,
            },
            isOptional: param.has_default,
          });
        }
      }
    }
    
    return deps;
  }
  
  // Python-specific: infer type from naming convention
  private inferTypeFromName(name: string): TypeReference {
    // Common Python naming patterns
    const patterns: [RegExp, string][] = [
      [/_repository$/i, 'Repository'],
      [/_service$/i, 'Service'],
      [/_factory$/i, 'Factory'],
      [/_client$/i, 'Client'],
      [/^db$|_db$/i, 'Database'],
      [/^session$|_session$/i, 'Session'],
    ];
    
    for (const [pattern, inferredType] of patterns) {
      if (pattern.test(name)) {
        return {
          name: inferredType,
          fullName: `Inferred:${inferredType}`,
          isGeneric: false,
          isNullable: false,
          isInferred: true,
          confidence: 0.6, // Lower confidence for inferred types
        };
      }
    }
    
    return {
      name: 'Unknown',
      fullName: 'Unknown',
      isGeneric: false,
      isNullable: false,
      isInferred: true,
      confidence: 0.3,
    };
  }
  
  getPatternDetectors(): IPatternDetector[] {
    return [
      new PythonRepositoryDetector(),
      new PythonFactoryDetector(),
      new PythonProtocolDetector(),
      new PythonDecoratorPatternDetector(),
      // Python-specific patterns
      new PythonContextManagerDetector(),
      new PythonMetaclassDetector(),
    ];
  }
  
  detectFrameworks(project: ProjectModel): Framework[] {
    const frameworks: Framework[] = [];
    
    // Check requirements.txt or pyproject.toml
    const requirements = this.readRequirements(project.path);
    
    if (requirements.includes('fastapi')) {
      frameworks.push(Framework.FastAPI);
    }
    if (requirements.includes('django')) {
      frameworks.push(Framework.Django);
    }
    if (requirements.includes('flask')) {
      frameworks.push(Framework.Flask);
    }
    
    return frameworks;
  }
}
```

### Python Analyzer Script (called by provider)

```python
# packages/provider-python/src/python_analyzer.py

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ParameterInfo:
    name: str
    annotation: Optional[Dict[str, Any]]
    has_default: bool

@dataclass 
class MethodInfo:
    name: str
    parameters: List[ParameterInfo]
    return_annotation: Optional[Dict[str, Any]]
    is_async: bool
    is_static: bool
    is_classmethod: bool
    decorators: List[Dict[str, Any]]
    lineno: int
    end_lineno: int
    body_complexity: int

@dataclass
class ClassInfo:
    name: str
    module: str
    file: str
    bases: List[Dict[str, Any]]
    decorators: List[Dict[str, Any]]
    methods: List[MethodInfo]
    attributes: List[Dict[str, Any]]
    lineno: int
    end_lineno: int

class PythonAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: str, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.classes: List[ClassInfo] = []
        self.functions: List[MethodInfo] = []
        
    def visit_ClassDef(self, node: ast.ClassDef):
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._analyze_method(item))
            elif isinstance(item, ast.AnnAssign):
                attributes.append(self._analyze_attribute(item))
        
        class_info = ClassInfo(
            name=node.name,
            module=self.module_name,
            file=self.file_path,
            bases=[self._analyze_expr(base) for base in node.bases],
            decorators=[self._analyze_decorator(d) for d in node.decorator_list],
            methods=methods,
            attributes=attributes,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno
        )
        
        self.classes.append(class_info)
        self.generic_visit(node)
        
    def _analyze_method(self, node) -> MethodInfo:
        params = []
        for arg in node.args.args:
            params.append(ParameterInfo(
                name=arg.arg,
                annotation=self._analyze_expr(arg.annotation) if arg.annotation else None,
                has_default=False  # Will be updated below
            ))
        
        # Mark defaults
        num_defaults = len(node.args.defaults)
        for i in range(num_defaults):
            params[-(num_defaults - i)].has_default = True
            
        return MethodInfo(
            name=node.name,
            parameters=params,
            return_annotation=self._analyze_expr(node.returns) if node.returns else None,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_static=any(self._is_staticmethod(d) for d in node.decorator_list),
            is_classmethod=any(self._is_classmethod(d) for d in node.decorator_list),
            decorators=[self._analyze_decorator(d) for d in node.decorator_list],
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            body_complexity=self._calculate_complexity(node)
        )
    
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1 + len(child.ifs)
        return complexity
    
    def _analyze_expr(self, node) -> Optional[Dict[str, Any]]:
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return {"kind": "name", "name": node.id}
        if isinstance(node, ast.Subscript):
            return {
                "kind": "generic",
                "name": self._analyze_expr(node.value),
                "args": self._analyze_expr(node.slice)
            }
        if isinstance(node, ast.Attribute):
            return {
                "kind": "attribute",
                "value": self._analyze_expr(node.value),
                "attr": node.attr
            }
        if isinstance(node, ast.Tuple):
            return {
                "kind": "tuple",
                "elements": [self._analyze_expr(e) for e in node.elts]
            }
        return {"kind": "unknown", "source": ast.unparse(node) if hasattr(ast, 'unparse') else str(node)}
    
    def _analyze_decorator(self, node) -> Dict[str, Any]:
        if isinstance(node, ast.Name):
            return {"name": node.id, "args": []}
        if isinstance(node, ast.Call):
            return {
                "name": self._analyze_expr(node.func),
                "args": [self._analyze_expr(a) for a in node.args],
                "kwargs": {kw.arg: self._analyze_expr(kw.value) for kw in node.keywords}
            }
        return {"name": "unknown"}

def analyze_project(project_path: str) -> Dict[str, Any]:
    result = {"classes": [], "functions": []}
    
    project = Path(project_path)
    for py_file in project.rglob("*.py"):
        # Skip common non-source directories
        if any(part.startswith('.') or part in ('venv', 'node_modules', '__pycache__', 'dist', 'build') 
               for part in py_file.parts):
            continue
            
        try:
            source = py_file.read_text()
            tree = ast.parse(source)
            
            module_name = str(py_file.relative_to(project)).replace('/', '.').replace('.py', '')
            analyzer = PythonAnalyzer(str(py_file), module_name)
            analyzer.visit(tree)
            
            result["classes"].extend([asdict(c) for c in analyzer.classes])
            result["functions"].extend([asdict(f) for f in analyzer.functions])
            
        except SyntaxError as e:
            print(f"Syntax error in {py_file}: {e}", file=sys.stderr)
    
    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python_analyzer.py <project_path>", file=sys.stderr)
        sys.exit(1)
    
    result = analyze_project(sys.argv[1])
    print(json.dumps(result, indent=2))
```

---

## 5. Angular Framework Extension

```typescript
// packages/framework-angular/src/angular-extension.ts

import { IFrameworkExtension, CodeUnit, Framework, Language } from '@codebase-eval/core';

export class AngularExtension implements IFrameworkExtension {
  readonly framework = Framework.Angular;
  readonly baseLanguage = Language.TypeScript;
  
  getPatternDetectors(): IPatternDetector[] {
    return [
      // Component patterns
      new AngularSmartComponentDetector(),
      new AngularPresentationalComponentDetector(),
      new AngularContainerComponentDetector(),
      
      // Service patterns
      new AngularServiceDetector(),
      new AngularFacadeServiceDetector(),
      new AngularStateServiceDetector(),
      
      // RxJS patterns
      new RxJSSubjectEncapsulationDetector(),
      new AsyncPipeUsageDetector(),
      new SubscriptionManagementDetector(),
      
      // NgRx patterns
      new NgRxStoreDetector(),
      new NgRxEffectsDetector(),
      new NgRxSelectorsDetector(),
      
      // Module patterns
      new FeatureModuleDetector(),
      new SharedModuleDetector(),
      new CoreModuleDetector(),
      
      // Anti-patterns
      new SubscribeInComponentDetector(),
      new NestedSubscribesDetector(),
      new SubjectLeakDetector(),
    ];
  }
  
  enrichCodeUnit(unit: CodeUnit): CodeUnit {
    // Add Angular-specific metadata based on decorators
    const componentDecorator = unit.annotations.find(a => a.name === 'Component');
    const injectableDecorator = unit.annotations.find(a => a.name === 'Injectable');
    const ngModuleDecorator = unit.annotations.find(a => a.name === 'NgModule');
    
    if (componentDecorator) {
      return {
        ...unit,
        kind: CodeUnitKind.Component,
        framework: Framework.Angular,
        frameworkMetadata: {
          angularType: 'component',
          selector: componentDecorator.arguments.get('selector'),
          changeDetection: componentDecorator.arguments.get('changeDetection'),
          templateUrl: componentDecorator.arguments.get('templateUrl'),
          styleUrls: componentDecorator.arguments.get('styleUrls'),
        },
      };
    }
    
    if (injectableDecorator) {
      return {
        ...unit,
        kind: CodeUnitKind.Service,
        framework: Framework.Angular,
        frameworkMetadata: {
          angularType: 'service',
          providedIn: injectableDecorator.arguments.get('providedIn') || 'module',
        },
      };
    }
    
    if (ngModuleDecorator) {
      return {
        ...unit,
        kind: CodeUnitKind.Module,
        framework: Framework.Angular,
        frameworkMetadata: {
          angularType: 'module',
          imports: ngModuleDecorator.arguments.get('imports'),
          exports: ngModuleDecorator.arguments.get('exports'),
          declarations: ngModuleDecorator.arguments.get('declarations'),
          providers: ngModuleDecorator.arguments.get('providers'),
        },
      };
    }
    
    return { ...unit, framework: Framework.Angular };
  }
  
  getConsistencyRules(): IConsistencyRule[] {
    return [
      // Component rules
      {
        name: 'SmartComponentsUseOnPush',
        description: 'Smart components should use OnPush change detection when possible',
        severity: 'warning',
        appliesTo: (unit) => unit.frameworkMetadata?.angularType === 'component',
      },
      
      // Service rules
      {
        name: 'ServicesProvidedInRoot',
        description: 'Services should use providedIn: root for tree-shaking',
        severity: 'info',
        appliesTo: (unit) => unit.frameworkMetadata?.angularType === 'service',
      },
      
      // RxJS rules
      {
        name: 'SubjectsArePrivate',
        description: 'Subjects should be private, expose as Observable',
        severity: 'warning',
        appliesTo: (unit) => this.hasSubjectMember(unit),
      },
      
      // Module rules
      {
        name: 'FeatureModulesAreLazy',
        description: 'Feature modules should be lazy loaded',
        severity: 'info',
        appliesTo: (unit) => this.isFeatureModule(unit),
      },
    ];
  }
}

// Example Angular-specific detector
class AngularSmartComponentDetector implements IPatternDetector {
  readonly patternName = 'AngularSmartComponent';
  
  async detect(context: AnalysisContext): Promise<PatternMatch[]> {
    const matches: PatternMatch[] = [];
    
    for (const unit of context.codeUnits) {
      if (unit.framework !== Framework.Angular) continue;
      if (unit.frameworkMetadata?.angularType !== 'component') continue;
      
      const signals: PatternSignal[] = [];
      
      // Signal 1: Has service dependencies
      const serviceDeps = unit.dependencies.filter(d => 
        d.target.name.endsWith('Service') ||
        d.target.name.endsWith('Facade') ||
        d.target.name.endsWith('Store')
      );
      
      if (serviceDeps.length > 0) {
        signals.push({
          name: 'ServiceDependencies',
          weight: 0.3,
          present: true,
          evidence: `Depends on ${serviceDeps.length} services`,
        });
      }
      
      // Signal 2: Uses store (NgRx)
      const usesStore = unit.members.some(m => 
        m.body?.invocations.some(i => 
          i.methodName.includes('dispatch') || 
          i.methodName.includes('select')
        )
      );
      
      if (usesStore) {
        signals.push({
          name: 'StoreInteraction',
          weight: 0.25,
          present: true,
          evidence: 'Uses NgRx store',
        });
      }
      
      // Signal 3: Has ngOnDestroy (manages subscriptions)
      const hasOnDestroy = unit.members.some(m => m.name === 'ngOnDestroy');
      if (hasOnDestroy) {
        signals.push({
          name: 'SubscriptionManagement',
          weight: 0.15,
          present: true,
          evidence: 'Implements ngOnDestroy',
        });
      }
      
      // Signal 4: Has child components in template
      // (Would require template analysis - simplified here)
      
      // Calculate confidence
      const confidence = signals.reduce((sum, s) => sum + s.weight, 0);
      
      if (confidence >= 0.4) {
        matches.push({
          patternName: this.patternName,
          location: unit.location,
          confidence,
          matchingSignals: signals,
          violatedSignals: [],
        });
      }
    }
    
    return matches;
  }
}
```

---

## 6. Detection Confidence Adjustments by Language

```typescript
// packages/core/src/analysis/confidence-adjuster.ts

export class ConfidenceAdjuster {
  
  adjustForLanguage(
    baseConfidence: number,
    language: Language,
    signalType: SignalType
  ): number {
    const adjustments = this.getAdjustments(language);
    const factor = adjustments[signalType] || 1.0;
    
    return Math.min(1.0, baseConfidence * factor);
  }
  
  private getAdjustments(language: Language): Record<SignalType, number> {
    switch (language) {
      case Language.CSharp:
        // Full type information - high confidence
        return {
          [SignalType.InterfaceImplementation]: 1.0,
          [SignalType.TypeRelationship]: 1.0,
          [SignalType.MethodSignature]: 1.0,
          [SignalType.NamingConvention]: 0.8, // Less reliance on names
          [SignalType.StructuralAnalysis]: 1.0,
        };
        
      case Language.TypeScript:
        // Good type information, but some inference
        return {
          [SignalType.InterfaceImplementation]: 0.95,
          [SignalType.TypeRelationship]: 0.9,
          [SignalType.MethodSignature]: 0.95,
          [SignalType.NamingConvention]: 0.85,
          [SignalType.StructuralAnalysis]: 1.0,
        };
        
      case Language.Python:
        // Limited type information - boost naming conventions
        return {
          [SignalType.InterfaceImplementation]: 0.7, // Protocols are optional
          [SignalType.TypeRelationship]: 0.6,
          [SignalType.MethodSignature]: 0.8, // If type hints present
          [SignalType.NamingConvention]: 1.2, // Increased reliance
          [SignalType.StructuralAnalysis]: 1.1, // Analyze what code does
          [SignalType.ImportAnalysis]: 1.2, // What's imported matters more
        };
        
      case Language.JavaScript:
        // No type information - heavy reliance on structure and naming
        return {
          [SignalType.InterfaceImplementation]: 0.4, // No interfaces
          [SignalType.TypeRelationship]: 0.5,
          [SignalType.MethodSignature]: 0.6,
          [SignalType.NamingConvention]: 1.3, // Critical importance
          [SignalType.StructuralAnalysis]: 1.2,
          [SignalType.ImportAnalysis]: 1.2,
          [SignalType.UsageAnalysis]: 1.3, // How it's used matters most
        };
        
      default:
        return {};
    }
  }
}
```

---

## Summary: Multi-Language Support Strategy

| Aspect | Approach |
|--------|----------|
| **Abstraction** | Unified Code Model (UCM) as common representation |
| **Parsing** | Language-specific providers (Roslyn, TS API, Python ast) |
| **Type Info** | Adapt confidence based on type system strength |
| **Patterns** | Universal patterns + language variants + framework-specific |
| **Frameworks** | Extensions that enrich UCM with framework metadata |
| **Detection** | Signal-based with language-appropriate weights |

**Key Insight**: TypeScript and Angular are different analysis targets because Angular adds semantic meaning through decorators, RxJS patterns, and architectural conventions that plain TypeScript doesn't have.
