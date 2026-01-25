# Data Model Schema Reference

This document provides complete schema definitions for persisting codebase analysis findings.

---

## 1. Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ENTITY RELATIONSHIPS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              ┌──────────────┐                               │
│                              │   Project    │                               │
│                              └──────┬───────┘                               │
│                                     │                                       │
│                    ┌────────────────┼────────────────┐                      │
│                    │                │                │                      │
│                    ▼                ▼                ▼                      │
│            ┌──────────────┐  ┌─────────────┐  ┌─────────────┐              │
│            │AnalysisRun   │  │   Module    │  │  Framework  │              │
│            └──────┬───────┘  └──────┬──────┘  └─────────────┘              │
│                   │                 │                                       │
│         ┌─────────┴──────┐         │                                       │
│         │                │         │                                       │
│         ▼                ▼         ▼                                       │
│  ┌─────────────┐  ┌───────────┐ ┌─────────┐                                │
│  │  Findings   │  │  Metrics  │ │  Type   │◄────────────────┐              │
│  └─────────────┘  └───────────┘ └────┬────┘                 │              │
│                                      │                      │              │
│                    ┌─────────────────┼──────────────┐       │              │
│                    │                 │              │       │              │
│                    ▼                 ▼              ▼       │              │
│             ┌──────────┐      ┌──────────┐   ┌──────────┐   │              │
│             │  Member  │      │Annotation│   │Dependency├───┘              │
│             └──────────┘      └──────────┘   └──────────┘                  │
│                                                                             │
│  Type participates in:                                                      │
│  ┌──────────────────┐  ┌───────────────┐  ┌─────────────┐                  │
│  │  PatternMatch    │  │  AntiPattern  │  │   Aspect    │                  │
│  └──────────────────┘  └───────────────┘  └─────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete MongoDB Collections

### 2.1 Projects Collection

```javascript
// Collection: projects
{
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "external_id": "proj-001",  // For cross-db references
    
    "identity": {
        "name": "ECommerce.Platform",
        "display_name": "E-Commerce Platform",
        "description": "Main e-commerce application",
        "repository_url": "https://github.com/org/ecommerce",
        "default_branch": "main"
    },
    
    "paths": {
        "root": "/projects/ecommerce",
        "source": "/projects/ecommerce/src",
        "tests": "/projects/ecommerce/tests"
    },
    
    "technology_stack": {
        "languages": [
            {
                "name": "csharp",
                "version": "12.0",
                "is_primary": true,
                "file_count": 450,
                "line_count": 125000
            },
            {
                "name": "typescript",
                "version": "5.3",
                "is_primary": false,
                "file_count": 120,
                "line_count": 35000
            }
        ],
        "frameworks": [
            {
                "name": "aspnetcore",
                "version": "8.0.0",
                "detected_by": ["package_reference", "program_cs_analysis"],
                "confidence": 0.98
            },
            {
                "name": "efcore",
                "version": "8.0.0",
                "detected_by": ["package_reference", "dbcontext_presence"],
                "confidence": 0.95
            },
            {
                "name": "angular",
                "version": "17.0.0",
                "detected_by": ["angular_json", "package_json"],
                "confidence": 0.99
            }
        ],
        "libraries": {
            "state_management": ["ngrx"],
            "testing": ["xunit", "moq", "jest"],
            "resilience": ["polly"],
            "messaging": ["masstransit"]
        }
    },
    
    "structure": {
        "organization_pattern": "by_layer_and_feature",
        "layers": [
            {"name": "Presentation", "path": "src/Web"},
            {"name": "Application", "path": "src/Application"},
            {"name": "Domain", "path": "src/Domain"},
            {"name": "Infrastructure", "path": "src/Infrastructure"}
        ],
        "features": [
            {"name": "Catalog", "paths": ["src/*/Catalog"]},
            {"name": "Orders", "paths": ["src/*/Orders"]},
            {"name": "Customers", "paths": ["src/*/Customers"]}
        ],
        "test_organization": "parallel_structure"
    },
    
    "metadata": {
        "created_at": ISODate("2024-01-01T00:00:00Z"),
        "updated_at": ISODate("2024-01-15T10:30:00Z"),
        "last_analysis_at": ISODate("2024-01-15T10:30:00Z"),
        "analysis_count": 45,
        "team": "platform-team",
        "tags": ["ecommerce", "microservices", "production"]
    }
}
```

### 2.2 Code Units Collection (Types)

```javascript
// Collection: code_units
{
    "_id": ObjectId("507f1f77bcf86cd799439012"),
    "project_id": ObjectId("507f1f77bcf86cd799439011"),
    "analysis_run_id": ObjectId("507f1f77bcf86cd799439099"),
    
    "identity": {
        "name": "OrderRepository",
        "fully_qualified_name": "ECommerce.Infrastructure.Data.OrderRepository",
        "kind": "class",
        "visibility": "public",
        "language": "csharp",
        "framework": "efcore"
    },
    
    "location": {
        "file_path": "src/Infrastructure/Data/Repositories/OrderRepository.cs",
        "start_line": 12,
        "end_line": 185,
        "module": "ECommerce.Infrastructure",
        "feature": "Orders"
    },
    
    "modifiers": {
        "is_abstract": false,
        "is_sealed": false,
        "is_partial": false,
        "is_static": false
    },
    
    "generics": {
        "is_generic": false,
        "type_parameters": [],
        "constraints": []
    },
    
    "inheritance": {
        "base_types": [
            {
                "name": "RepositoryBase",
                "fully_qualified_name": "ECommerce.Infrastructure.Data.RepositoryBase`1",
                "generic_arguments": ["Order"],
                "is_interface": false
            }
        ],
        "implemented_interfaces": [
            {
                "name": "IOrderRepository",
                "fully_qualified_name": "ECommerce.Domain.Interfaces.IOrderRepository",
                "generic_arguments": []
            },
            {
                "name": "IRepository",
                "fully_qualified_name": "ECommerce.Domain.Interfaces.IRepository`1",
                "generic_arguments": ["Order"]
            }
        ]
    },
    
    "members": [
        {
            "id": "mem-001",
            "name": "_context",
            "kind": "field",
            "visibility": "private",
            "is_readonly": true,
            "type": {
                "name": "OrderDbContext",
                "fully_qualified_name": "ECommerce.Infrastructure.Data.OrderDbContext",
                "is_nullable": false
            }
        },
        {
            "id": "mem-002",
            "name": "_logger",
            "kind": "field",
            "visibility": "private",
            "is_readonly": true,
            "type": {
                "name": "ILogger",
                "fully_qualified_name": "Microsoft.Extensions.Logging.ILogger`1",
                "generic_arguments": ["OrderRepository"],
                "is_nullable": false
            }
        },
        {
            "id": "mem-003",
            "name": "GetByIdAsync",
            "kind": "method",
            "visibility": "public",
            "is_async": true,
            "is_virtual": true,
            "return_type": {
                "name": "Task",
                "fully_qualified_name": "System.Threading.Tasks.Task`1",
                "generic_arguments": [
                    {
                        "name": "Order",
                        "is_nullable": true
                    }
                ]
            },
            "parameters": [
                {
                    "name": "id",
                    "type": {
                        "name": "Guid",
                        "fully_qualified_name": "System.Guid"
                    },
                    "is_optional": false,
                    "position": 0
                },
                {
                    "name": "cancellationToken",
                    "type": {
                        "name": "CancellationToken",
                        "fully_qualified_name": "System.Threading.CancellationToken"
                    },
                    "is_optional": true,
                    "default_value": "default",
                    "position": 1
                }
            ],
            "body_analysis": {
                "line_count": 12,
                "cyclomatic_complexity": 3,
                "cognitive_complexity": 2,
                "invocations": [
                    {
                        "target_type": "DbSet`1",
                        "method": "FindAsync",
                        "is_async": true
                    },
                    {
                        "target_type": "ILogger",
                        "method": "LogDebug",
                        "is_async": false
                    }
                ],
                "exception_handling": {
                    "has_try_catch": true,
                    "exception_types_caught": ["DbException"]
                }
            },
            "location": {
                "start_line": 35,
                "end_line": 47
            }
        },
        {
            "id": "mem-004",
            "name": "GetByCustomerAsync",
            "kind": "method",
            "visibility": "public",
            "is_async": true,
            "return_type": {
                "name": "Task",
                "generic_arguments": [
                    {
                        "name": "IReadOnlyList",
                        "generic_arguments": ["Order"]
                    }
                ]
            },
            "parameters": [
                {
                    "name": "customerId",
                    "type": {"name": "Guid"},
                    "is_optional": false
                },
                {
                    "name": "specification",
                    "type": {
                        "name": "ISpecification",
                        "generic_arguments": ["Order"]
                    },
                    "is_optional": true
                },
                {
                    "name": "cancellationToken",
                    "type": {"name": "CancellationToken"},
                    "is_optional": true
                }
            ],
            "body_analysis": {
                "line_count": 18,
                "cyclomatic_complexity": 4,
                "uses_specification_pattern": true
            },
            "location": {
                "start_line": 49,
                "end_line": 67
            }
        }
        // ... more members
    ],
    
    "dependencies": [
        {
            "id": "dep-001",
            "target": {
                "name": "OrderDbContext",
                "fully_qualified_name": "ECommerce.Infrastructure.Data.OrderDbContext"
            },
            "kind": "constructor_injection",
            "injection_site": {
                "method": "constructor",
                "parameter_name": "context",
                "parameter_position": 0
            },
            "is_optional": false,
            "usage_count": 8
        },
        {
            "id": "dep-002",
            "target": {
                "name": "ILogger",
                "fully_qualified_name": "Microsoft.Extensions.Logging.ILogger`1"
            },
            "kind": "constructor_injection",
            "injection_site": {
                "method": "constructor",
                "parameter_name": "logger",
                "parameter_position": 1
            },
            "is_optional": false,
            "usage_count": 5
        }
    ],
    
    "annotations": [
        {
            "name": "Repository",
            "fully_qualified_name": "ECommerce.Infrastructure.Attributes.RepositoryAttribute",
            "arguments": {
                "entity": "Order",
                "lifetime": "Scoped"
            },
            "location": {"line": 11}
        }
    ],
    
    "metrics": {
        "lines_of_code": 173,
        "logical_lines": 145,
        "member_count": 12,
        "public_member_count": 8,
        "private_member_count": 4,
        "method_count": 10,
        "property_count": 0,
        "field_count": 2,
        "cyclomatic_complexity_total": 28,
        "cyclomatic_complexity_average": 2.8,
        "max_method_complexity": 6,
        "maintainability_index": 68,
        "coupling": {
            "afferent": 12,      // Types depending on this
            "efferent": 5,       // Types this depends on
            "instability": 0.29  // Ce / (Ca + Ce)
        },
        "cohesion": {
            "lcom": 0.15,        // Lack of Cohesion of Methods (lower is better)
            "lcom4": 1           // Connected components (1 is ideal)
        }
    },
    
    "pattern_matches": [
        {
            "pattern_id": "pat-repository",
            "pattern_name": "Repository",
            "pattern_category": "architectural",
            "confidence": 0.94,
            "matched_at": ISODate("2024-01-15T10:30:00Z"),
            
            "signals": {
                "matched": [
                    {
                        "name": "implements_repository_interface",
                        "weight": 0.25,
                        "contribution": 0.25,
                        "evidence": "Implements IRepository<Order> and IOrderRepository"
                    },
                    {
                        "name": "has_crud_methods",
                        "weight": 0.20,
                        "contribution": 0.20,
                        "evidence": "Has GetByIdAsync, AddAsync, UpdateAsync, DeleteAsync"
                    },
                    {
                        "name": "db_context_dependency",
                        "weight": 0.25,
                        "contribution": 0.25,
                        "evidence": "Constructor depends on OrderDbContext"
                    },
                    {
                        "name": "async_methods",
                        "weight": 0.10,
                        "contribution": 0.10,
                        "evidence": "All data access methods are async"
                    },
                    {
                        "name": "naming_convention",
                        "weight": 0.10,
                        "contribution": 0.10,
                        "evidence": "Class name ends with 'Repository'"
                    },
                    {
                        "name": "cancellation_token_support",
                        "weight": 0.05,
                        "contribution": 0.05,
                        "evidence": "Methods accept CancellationToken"
                    }
                ],
                "violated": [],
                "missing": [
                    {
                        "name": "uses_specification_pattern",
                        "weight": 0.05,
                        "reason": "Some methods use specifications, not all"
                    }
                ]
            },
            
            "variations": [
                "generic_base_class",
                "specification_support",
                "logging_integrated"
            ]
        }
    ],
    
    "anti_patterns": [],
    
    "aspects": {
        "logging": {
            "present": true,
            "implementation": "ILogger<T> injection",
            "usage_locations": ["GetByIdAsync", "AddAsync", "error handlers"]
        },
        "error_handling": {
            "present": true,
            "implementation": "try-catch with specific exceptions",
            "patterns": ["catch DbException", "rethrow as domain exception"]
        },
        "transactions": {
            "present": false,
            "note": "Transactions managed at service layer"
        }
    },
    
    "documentation": {
        "has_xml_docs": true,
        "documented_members": 8,
        "undocumented_members": 4,
        "coverage": 0.67
    }
}
```

### 2.3 Analysis Runs Collection

```javascript
// Collection: analysis_runs
{
    "_id": ObjectId("507f1f77bcf86cd799439099"),
    "project_id": ObjectId("507f1f77bcf86cd799439011"),
    "external_id": "run-2024-01-15-001",
    
    "execution": {
        "started_at": ISODate("2024-01-15T10:25:00Z"),
        "completed_at": ISODate("2024-01-15T10:35:00Z"),
        "duration_seconds": 600,
        "status": "completed",
        "triggered_by": "schedule",
        "executor": "analysis-worker-03"
    },
    
    "configuration": {
        "analyzer_version": "2.1.0",
        "pattern_catalog_version": "2024.1.0",
        "confidence_thresholds": {
            "pattern_match": 0.65,
            "anti_pattern": 0.70
        },
        "include_patterns": ["**/*.cs", "**/*.ts"],
        "exclude_patterns": [
            "**/obj/**",
            "**/bin/**",
            "**/node_modules/**",
            "**/*.generated.cs"
        ],
        "enabled_analyzers": [
            "structural",
            "semantic",
            "pattern_matching",
            "anti_pattern_detection",
            "consistency_analysis"
        ]
    },
    
    "scope": {
        "files_analyzed": 570,
        "types_analyzed": 452,
        "members_analyzed": 3840,
        "lines_analyzed": 160000
    },
    
    "summary": {
        "quality_score": {
            "overall": 82,
            "grade": "B",
            "components": {
                "pattern_consistency": 88,
                "anti_pattern_avoidance": 75,
                "structural_quality": 85,
                "best_practice_adherence": 80
            },
            "trend": "stable",
            "change_from_previous": +2
        },
        
        "patterns": {
            "total_detected": 156,
            "by_category": {
                "creational": 12,
                "structural": 28,
                "behavioral": 45,
                "architectural": 71
            },
            "top_patterns": [
                {"name": "Service", "count": 35, "avg_confidence": 0.91},
                {"name": "Repository", "count": 18, "avg_confidence": 0.88},
                {"name": "Factory", "count": 8, "avg_confidence": 0.82},
                {"name": "Mediator Handler", "count": 42, "avg_confidence": 0.95}
            ]
        },
        
        "anti_patterns": {
            "total_detected": 8,
            "by_severity": {
                "critical": 0,
                "high": 2,
                "medium": 3,
                "low": 3
            },
            "details": [
                {
                    "name": "GodClass",
                    "count": 2,
                    "severity": "high",
                    "affected_types": [
                        "ECommerce.Application.Services.LegacyOrderService",
                        "ECommerce.Web.Controllers.AdminController"
                    ]
                },
                {
                    "name": "ServiceLocator",
                    "count": 3,
                    "severity": "medium",
                    "affected_types": [
                        "ECommerce.Infrastructure.Legacy.ReportGenerator",
                        "ECommerce.Infrastructure.Legacy.NotificationManager",
                        "ECommerce.Infrastructure.Legacy.DataMigrator"
                    ]
                }
            ]
        },
        
        "consistency": {
            "overall_score": 0.88,
            "inconsistencies_found": 5,
            "by_pattern": [
                {
                    "pattern": "Repository",
                    "consistency": 0.94,
                    "issues": [
                        "2 repositories don't use async suffix"
                    ]
                },
                {
                    "pattern": "Service",
                    "consistency": 0.85,
                    "issues": [
                        "5 services return raw entities instead of DTOs",
                        "3 services don't follow naming convention"
                    ]
                }
            ]
        },
        
        "aspects": {
            "logging": {
                "coverage": 0.85,
                "implementation_consistency": "high",
                "patterns": ["ILogger<T> injection"]
            },
            "error_handling": {
                "coverage": 0.78,
                "implementation_consistency": "medium",
                "patterns": ["domain exceptions", "result wrapper"]
            },
            "validation": {
                "coverage": 0.92,
                "implementation_consistency": "high",
                "patterns": ["FluentValidation", "data annotations"]
            }
        },
        
        "metrics": {
            "average_complexity": 4.2,
            "max_complexity": 28,
            "average_coupling": 3.8,
            "average_cohesion": 0.82,
            "test_coverage": 0.73
        }
    },
    
    "recommendations": [
        {
            "id": "rec-001",
            "priority": "high",
            "category": "anti_pattern",
            "title": "Refactor LegacyOrderService (God Class)",
            "description": "LegacyOrderService has 52 methods and 1,800 lines. Consider splitting into focused services.",
            "affected_types": ["ECommerce.Application.Services.LegacyOrderService"],
            "suggested_actions": [
                "Extract order creation logic to OrderCreationService",
                "Extract order fulfillment logic to FulfillmentService",
                "Extract reporting logic to OrderReportingService"
            ],
            "estimated_effort": "large",
            "impact": "high"
        },
        {
            "id": "rec-002",
            "priority": "medium",
            "category": "consistency",
            "title": "Standardize Repository Async Naming",
            "description": "2 repositories don't follow async naming convention",
            "affected_types": [
                "ECommerce.Infrastructure.Data.ProductRepository",
                "ECommerce.Infrastructure.Data.CategoryRepository"
            ],
            "suggested_actions": [
                "Add 'Async' suffix to async methods"
            ],
            "estimated_effort": "small",
            "impact": "low"
        }
    ],
    
    "errors": [],
    "warnings": [
        {
            "code": "WARN001",
            "message": "Unable to resolve type 'ExternalPaymentGateway' - external assembly",
            "location": "ECommerce.Infrastructure.Payments.PaymentProcessor"
        }
    ]
}
```

### 2.4 Pattern Catalog Collection

```javascript
// Collection: pattern_catalog
{
    "_id": ObjectId("507f1f77bcf86cd799439200"),
    
    "identity": {
        "name": "Repository",
        "display_name": "Repository Pattern",
        "version": "2.0.0",
        "category": "architectural",
        "scope": "universal"
    },
    
    "metadata": {
        "author": "system",
        "created_at": ISODate("2023-01-01T00:00:00Z"),
        "updated_at": ISODate("2024-01-01T00:00:00Z"),
        "source": "standard_catalog",
        "references": [
            "https://martinfowler.com/eaaCatalog/repository.html"
        ]
    },
    
    "description": {
        "summary": "Mediates between the domain and data mapping layers using a collection-like interface for accessing domain objects.",
        "problem": "Direct data access code scattered throughout the application couples business logic to specific data access technology.",
        "solution": "Create an interface that looks like an in-memory collection of domain objects, with the implementation handling all data access details.",
        "consequences": {
            "benefits": [
                "Decouples business logic from data access",
                "Enables unit testing with mock repositories",
                "Centralizes data access logic",
                "Provides a clear API for data operations"
            ],
            "drawbacks": [
                "Additional abstraction layer",
                "Can become a thin wrapper if not careful",
                "May hide query optimization opportunities"
            ]
        }
    },
    
    "detection": {
        "confidence_threshold": 0.65,
        
        "signals": [
            {
                "id": "sig-001",
                "name": "implements_repository_interface",
                "description": "Class implements an interface with 'Repository' in the name or IRepository<T>",
                "weight": 0.25,
                "detector": "interface_implementation",
                "config": {
                    "patterns": [
                        "IRepository*",
                        "*Repository",
                        "I*Repository"
                    ]
                }
            },
            {
                "id": "sig-002",
                "name": "has_crud_methods",
                "description": "Class has methods for Create, Read, Update, Delete operations",
                "weight": 0.20,
                "detector": "method_signature_match",
                "config": {
                    "method_patterns": [
                        {"prefix": ["Get", "Find", "Fetch", "Query"], "min_matches": 1},
                        {"prefix": ["Add", "Create", "Insert"], "min_matches": 1},
                        {"prefix": ["Update", "Modify", "Save"], "min_matches": 0},
                        {"prefix": ["Delete", "Remove"], "min_matches": 1}
                    ],
                    "total_min_matches": 3
                }
            },
            {
                "id": "sig-003",
                "name": "data_access_dependency",
                "description": "Constructor depends on data access infrastructure",
                "weight": 0.25,
                "detector": "constructor_dependency",
                "config": {
                    "type_patterns": [
                        "*DbContext",
                        "IDbConnection",
                        "ISession",
                        "IDocumentSession",
                        "IMongoCollection*"
                    ],
                    "match_any": true
                }
            },
            {
                "id": "sig-004",
                "name": "entity_focused",
                "description": "Repository is focused on a single entity type",
                "weight": 0.15,
                "detector": "generic_type_analysis",
                "config": {
                    "check_generic_parameter": true,
                    "check_method_return_types": true
                }
            },
            {
                "id": "sig-005",
                "name": "naming_convention",
                "description": "Class name ends with 'Repository'",
                "weight": 0.10,
                "detector": "naming_pattern",
                "config": {
                    "pattern": "*Repository"
                }
            },
            {
                "id": "sig-006",
                "name": "async_methods",
                "description": "Data access methods are asynchronous",
                "weight": 0.05,
                "detector": "async_pattern",
                "config": {
                    "check_return_type": "Task*",
                    "check_suffix": "Async"
                }
            }
        ],
        
        "anti_signals": [
            {
                "id": "anti-001",
                "name": "contains_business_logic",
                "description": "Repository contains complex business logic",
                "weight": -0.30,
                "detector": "complexity_analysis",
                "config": {
                    "max_cyclomatic_complexity": 8,
                    "check_for": ["business_calculations", "complex_conditionals"]
                }
            },
            {
                "id": "anti-002",
                "name": "exposes_queryable",
                "description": "Repository exposes IQueryable (leaky abstraction)",
                "weight": -0.15,
                "detector": "return_type_check",
                "config": {
                    "forbidden_return_types": ["IQueryable*"]
                }
            },
            {
                "id": "anti-003",
                "name": "ui_dependencies",
                "description": "Repository has UI or web framework dependencies",
                "weight": -0.40,
                "detector": "dependency_check",
                "config": {
                    "forbidden_dependencies": [
                        "*Controller",
                        "*ViewModel",
                        "HttpContext*"
                    ]
                }
            }
        ]
    },
    
    "language_variants": {
        "csharp": {
            "signal_adjustments": [
                {"signal": "async_methods", "weight": 0.10}
            ],
            "additional_signals": [
                {
                    "name": "cancellation_token_support",
                    "weight": 0.05,
                    "detector": "parameter_check",
                    "config": {"parameter_type": "CancellationToken"}
                }
            ],
            "examples": {
                "good": "public class OrderRepository : IRepository<Order> { ... }",
                "bad": "public class OrderRepository { public IQueryable<Order> GetAll() { ... } }"
            }
        },
        "typescript": {
            "signal_adjustments": [
                {"signal": "implements_repository_interface", "weight": 0.20}
            ],
            "additional_signals": [
                {
                    "name": "returns_promise",
                    "weight": 0.10,
                    "detector": "return_type_check",
                    "config": {"expected_type": "Promise<*>"}
                }
            ]
        },
        "python": {
            "signal_adjustments": [
                {"signal": "implements_repository_interface", "weight": 0.15},
                {"signal": "naming_convention", "weight": 0.20}
            ],
            "notes": "Python relies more on duck typing; naming conventions are more important"
        }
    },
    
    "framework_variants": {
        "efcore": {
            "additional_signals": [
                {
                    "name": "dbset_usage",
                    "weight": 0.10,
                    "detector": "member_usage",
                    "config": {"member_pattern": "DbSet<*>"}
                }
            ]
        },
        "angular": {
            "additional_signals": [
                {
                    "name": "injectable_decorator",
                    "weight": 0.10,
                    "detector": "decorator_presence",
                    "config": {"decorator": "Injectable"}
                },
                {
                    "name": "http_client_dependency",
                    "weight": 0.15,
                    "detector": "constructor_dependency",
                    "config": {"type": "HttpClient"}
                },
                {
                    "name": "returns_observable",
                    "weight": 0.10,
                    "detector": "return_type_check",
                    "config": {"expected_type": "Observable<*>"}
                }
            ]
        }
    },
    
    "consistency_rules": [
        {
            "name": "uniform_return_types",
            "description": "All repositories should use consistent return type wrapping",
            "check": "return_type_consistency",
            "config": {
                "expected_patterns": ["Task<T?>", "Task<Result<T>>", "Task<IReadOnlyList<T>>"]
            }
        },
        {
            "name": "async_naming",
            "description": "Async methods should have 'Async' suffix",
            "check": "naming_consistency",
            "config": {
                "async_methods_suffix": "Async"
            }
        }
    ],
    
    "related_patterns": [
        {
            "name": "UnitOfWork",
            "relationship": "often_used_together",
            "description": "Repository often used with Unit of Work for transaction management"
        },
        {
            "name": "Specification",
            "relationship": "can_enhance",
            "description": "Specification pattern can be used to encapsulate query logic"
        },
        {
            "name": "GenericRepository",
            "relationship": "variant",
            "description": "Generic base repository reduces boilerplate"
        }
    ]
}
```

---

## 3. Neo4j Graph Schema

### 3.1 Node Definitions

```cypher
// Create constraints and indexes

// Project nodes
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Module nodes
CREATE CONSTRAINT module_fqn IF NOT EXISTS
FOR (m:Module) REQUIRE m.fully_qualified_name IS UNIQUE;

// Type nodes
CREATE CONSTRAINT type_fqn IF NOT EXISTS
FOR (t:Type) REQUIRE t.fully_qualified_name IS UNIQUE;

CREATE INDEX type_name IF NOT EXISTS
FOR (t:Type) ON (t.name);

CREATE INDEX type_kind IF NOT EXISTS
FOR (t:Type) ON (t.kind);

// Pattern nodes
CREATE CONSTRAINT pattern_name IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.name IS UNIQUE;

// Create full-text index for searching
CREATE FULLTEXT INDEX type_search IF NOT EXISTS
FOR (t:Type) ON EACH [t.name, t.fully_qualified_name];
```

### 3.2 Sample Data Creation

```cypher
// Create project
CREATE (proj:Project {
    id: 'proj-001',
    name: 'ECommerce.Platform',
    path: '/projects/ecommerce',
    primary_language: 'csharp',
    analyzed_at: datetime()
})

// Create modules
CREATE (mod1:Module {
    id: 'mod-001',
    name: 'Domain',
    fully_qualified_name: 'ECommerce.Domain',
    path: 'src/Domain',
    type_count: 45
})

CREATE (mod2:Module {
    id: 'mod-002', 
    name: 'Infrastructure',
    fully_qualified_name: 'ECommerce.Infrastructure',
    path: 'src/Infrastructure',
    type_count: 38
})

// Connect modules to project
CREATE (proj)-[:CONTAINS]->(mod1)
CREATE (proj)-[:CONTAINS]->(mod2)

// Create interface
CREATE (iface:Type:Interface {
    id: 'type-001',
    name: 'IOrderRepository',
    fully_qualified_name: 'ECommerce.Domain.Interfaces.IOrderRepository',
    kind: 'interface',
    visibility: 'public',
    member_count: 6
})

CREATE (mod1)-[:CONTAINS]->(iface)

// Create implementation
CREATE (impl:Type:Class {
    id: 'type-002',
    name: 'OrderRepository',
    fully_qualified_name: 'ECommerce.Infrastructure.Data.OrderRepository',
    kind: 'class',
    visibility: 'public',
    member_count: 12,
    line_count: 173,
    complexity: 28
})

CREATE (mod2)-[:CONTAINS]->(impl)

// Create relationships
CREATE (impl)-[:IMPLEMENTS]->(iface)

// Create DbContext dependency
CREATE (dbctx:Type:Class {
    id: 'type-003',
    name: 'OrderDbContext',
    fully_qualified_name: 'ECommerce.Infrastructure.Data.OrderDbContext',
    kind: 'class'
})

CREATE (impl)-[:DEPENDS_ON {
    kind: 'constructor_injection',
    parameter_name: 'context',
    is_optional: false
}]->(dbctx)

// Create pattern
CREATE (pat:Pattern {
    id: 'pat-repository',
    name: 'Repository',
    category: 'architectural',
    scope: 'universal'
})

// Create pattern instance
CREATE (pi:PatternInstance {
    id: 'pi-001',
    confidence: 0.94,
    detected_at: datetime(),
    signals_matched: ['implements_interface', 'crud_methods', 'db_dependency'],
    variations: ['generic_base', 'async_methods']
})

// Connect pattern instance
CREATE (impl)-[:MATCHES {confidence: 0.94}]->(pi)
CREATE (pi)-[:INSTANCE_OF]->(pat)
```

### 3.3 Useful Graph Queries

```cypher
// 1. Find all types that implement a specific pattern with relationships
MATCH (t:Type)-[m:MATCHES]->(pi:PatternInstance)-[:INSTANCE_OF]->(p:Pattern {name: 'Repository'})
OPTIONAL MATCH (t)-[:IMPLEMENTS]->(i:Interface)
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(d:Type)
RETURN t.name, 
       m.confidence, 
       collect(DISTINCT i.name) as interfaces,
       collect(DISTINCT d.name) as dependencies
ORDER BY m.confidence DESC

// 2. Find circular dependencies
MATCH path = (t1:Type)-[:DEPENDS_ON*2..5]->(t1)
RETURN [n in nodes(path) | n.name] as cycle, length(path) as cycle_length

// 3. Find types with highest coupling (most dependencies)
MATCH (t:Type)-[d:DEPENDS_ON]->(:Type)
WITH t, count(d) as dependency_count
ORDER BY dependency_count DESC
LIMIT 10
RETURN t.name, t.fully_qualified_name, dependency_count

// 4. Find modules with highest coupling between them
MATCH (m1:Module)-[:CONTAINS]->(t1:Type)-[:DEPENDS_ON]->(t2:Type)<-[:CONTAINS]-(m2:Module)
WHERE m1 <> m2
WITH m1, m2, count(*) as connection_count
ORDER BY connection_count DESC
RETURN m1.name, m2.name, connection_count

// 5. Pattern consistency analysis
MATCH (t:Type)-[:MATCHES]->(pi:PatternInstance)-[:INSTANCE_OF]->(p:Pattern)
WITH p.name as pattern, 
     collect({type: t.name, signals: pi.signals_matched}) as implementations
UNWIND implementations as impl
WITH pattern, impl.signals as signals, count(*) as signal_count
ORDER BY pattern, signal_count DESC
RETURN pattern, signals, signal_count

// 6. Find all anti-patterns and their affected types
MATCH (t:Type)-[e:EXHIBITS]->(ap:AntiPattern)
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Type)
RETURN ap.name as anti_pattern,
       ap.severity,
       t.name as affected_type,
       t.line_count,
       t.complexity,
       count(dep) as dependency_count

// 7. Impact analysis - what would be affected if we change a type?
MATCH (target:Type {name: 'OrderRepository'})
MATCH (dependent:Type)-[:DEPENDS_ON|IMPLEMENTS*1..3]->(target)
RETURN target.name as changed_type,
       collect(DISTINCT dependent.name) as affected_types,
       count(DISTINCT dependent) as impact_count

// 8. Find orphan types (no incoming or outgoing relationships)
MATCH (t:Type)
WHERE NOT (t)-[:DEPENDS_ON|IMPLEMENTS]->() 
  AND NOT ()-[:DEPENDS_ON|IMPLEMENTS]->(t)
RETURN t.name, t.fully_qualified_name
```

---

## 4. Query Examples Across Databases

### 4.1 Combined Query Service

```typescript
// Example service that queries across all three databases

interface PatternAnalysisRequest {
    projectId: string;
    patternName: string;
    includeRelationships: boolean;
    includeTrends: boolean;
}

interface PatternAnalysisResult {
    pattern: PatternInfo;
    instances: PatternInstanceDetail[];
    relationships: TypeRelationship[];
    statistics: PatternStatistics;
    trends: TrendData[];
    consistency: ConsistencyReport;
}

async function analyzePattern(request: PatternAnalysisRequest): Promise<PatternAnalysisResult> {
    
    // 1. Get pattern definition from MongoDB
    const patternDef = await mongo.collection('pattern_catalog').findOne({
        'identity.name': request.patternName
    });
    
    // 2. Get all instances with relationships from Neo4j
    const graphQuery = `
        MATCH (p:Project {id: $projectId})
        MATCH (p)-[:CONTAINS*]->(t:Type)-[m:MATCHES]->(pi:PatternInstance)
              -[:INSTANCE_OF]->(pat:Pattern {name: $patternName})
        OPTIONAL MATCH (t)-[:IMPLEMENTS]->(iface:Interface)
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Type)
        OPTIONAL MATCH (t)-[:EXTENDS]->(base:Type)
        RETURN t, m, pi, 
               collect(DISTINCT iface) as interfaces,
               collect(DISTINCT dep) as dependencies,
               collect(DISTINCT base) as baseTypes
    `;
    const graphResults = await neo4j.run(graphQuery, {
        projectId: request.projectId,
        patternName: request.patternName
    });
    
    // 3. Get detailed code unit info from MongoDB
    const typeIds = graphResults.map(r => r.t.id);
    const codeUnits = await mongo.collection('code_units').find({
        '_id': { $in: typeIds.map(id => new ObjectId(id)) }
    }).toArray();
    
    // 4. Get statistics and trends from PostgreSQL
    const statsQuery = `
        SELECT 
            ps.occurrence_count,
            ps.avg_confidence,
            ps.consistency_score,
            ar.completed_at
        FROM pattern_statistics ps
        JOIN analysis_runs ar ON ps.analysis_run_id = ar.id
        WHERE ar.project_id = $1 
          AND ps.pattern_name = $2
        ORDER BY ar.completed_at DESC
        LIMIT 30
    `;
    const statsResults = await postgres.query(statsQuery, [
        request.projectId, 
        request.patternName
    ]);
    
    // 5. Calculate consistency
    const consistency = analyzeConsistency(graphResults);
    
    // 6. Combine and return
    return {
        pattern: {
            name: patternDef.identity.name,
            category: patternDef.identity.category,
            description: patternDef.description.summary
        },
        instances: graphResults.map((r, idx) => ({
            type: r.t,
            confidence: r.m.confidence,
            signals: r.pi.signals_matched,
            details: codeUnits[idx],
            interfaces: r.interfaces,
            dependencies: r.dependencies
        })),
        relationships: request.includeRelationships 
            ? buildRelationshipMap(graphResults) 
            : [],
        statistics: {
            count: statsResults[0]?.occurrence_count ?? 0,
            avgConfidence: statsResults[0]?.avg_confidence ?? 0,
            consistency: statsResults[0]?.consistency_score ?? 0
        },
        trends: request.includeTrends 
            ? statsResults.map(r => ({
                date: r.completed_at,
                count: r.occurrence_count,
                confidence: r.avg_confidence
            }))
            : [],
        consistency
    };
}
```

---

## 5. Summary: When to Use Each Database

| Use Case | Database | Reason |
|----------|----------|--------|
| Store full code unit details | MongoDB | Flexible schema, nested data |
| Store pattern definitions | MongoDB | Complex nested structure |
| Query type relationships | Neo4j | Graph traversal |
| Find circular dependencies | Neo4j | Path queries |
| Impact analysis | Neo4j | Relationship traversal |
| Pattern adoption trends | PostgreSQL | Time series aggregation |
| Quality score history | PostgreSQL | Trend analysis |
| Generate reports | PostgreSQL | Complex aggregations |
| Search code units | MongoDB | Full-text search |
| Find inconsistencies | Neo4j | Compare related nodes |

The hybrid approach allows each database to do what it does best while providing a unified API for the application layer.
