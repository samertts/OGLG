# Architecture Overview

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## High-Level Layering

```
┌─────────────────────────────┐
│         UI (tkinter)        │
├─────────────────────────────┤
│    Application Services     │
│  (numbering, workflow, ..)  │
├─────────────────────────────┤
│       Domain / Core         │
│  (entities, value objects)  │
├─────────────────────────────┤
│   Infrastructure / Repos    │
│  (SQLAlchemy, SQLite, FTS5) │
├─────────────────────────────┤
│    SQLite (WAL mode)        │
└─────────────────────────────┘
```

## Dependency Direction

Strict one-way: UI → Application → Domain ← Infrastructure

- Domain has zero external dependencies
- Application depends on Domain only
- Infrastructure implements Domain interfaces
- UI depends on Application only

## Subsystems

| Subsystem | Responsibility |
|-----------|---------------|
| Numbering | Atomic sequence allocation, formatting, validation |
| Workflow | State machine, transitions, routing |
| Attachment | File storage, indexing, deduplication |
| Archive | Long-term storage, compression, retrieval |
| Search | FTS5 indexing, full-text queries |
| Audit | Immutable event log, reconciliation |

## WAL-Safe Execution

- All writes begin with appropriate transaction isolation
- Sequence allocation uses savepoint-based atomicity
- Crash recovery: WAL auto-checkpoint on startup
- Integrity check: `PRAGMA integrity_check` on initialization
