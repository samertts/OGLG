# System Architecture Document

**Project**: Iraqi Government Offline Official Correspondence System
**Version**: 1.0 (Architecture Design)
**Last Updated**: 2026-05-28

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Modular Architecture](#2-modular-architecture)
3. [Layered Architecture](#3-layered-architecture)
4. [Core Modules](#4-core-modules)
5. [Internal Service Boundaries](#5-internal-service-boundaries)
6. [Data Flow Architecture](#6-data-flow-architecture)
7. [Database Architecture](#7-database-architecture)
8. [File Storage Architecture](#8-file-storage-architecture)
9. [PDF Generation Pipeline](#9-pdf-generation-pipeline)
10. [AI Local Assistant Architecture](#10-ai-local-assistant-architecture)
11. [Backup and Recovery Architecture](#11-backup-and-recovery-architecture)
12. [Logging Architecture](#12-logging-architecture)
13. [Error Handling Architecture](#13-error-handling-architecture)
14. [Future Integration Architecture](#14-future-integration-architecture)
15. [Plugin/Extension Architecture](#15-pluginextension-architecture)
16. [Offline-First Architecture](#16-offline-first-architecture)
17. [Windows Deployment Architecture](#17-windows-deployment-architecture)
18. [Security Architecture](#18-security-architecture)
19. [Audit Architecture](#19-audit-architecture)
20. [Scalability Strategy](#20-scalability-strategy)
21. [Performance Strategy](#21-performance-strategy)
22. [Dependency Isolation Strategy](#22-dependency-isolation-strategy)
23. [Update and Migration Strategy](#23-update-and-migration-strategy)
24. [Fail-Safe and Crash Recovery Strategy](#24-fail-safe-and-crash-recovery-strategy)

---

## 1. High-Level Architecture

### 1.1 Architectural Pattern

The system follows **Clean Architecture** with a **Service-Oriented Monolith** pattern:

- **Monolithic deployment** (single executable) — no microservices overhead
- **Logical separation** via service boundaries and dependency inversion
- **Framework-independent domain core** — business logic has zero knowledge of PySide6, SQLAlchemy, or ReportLab
- **Dependency Rule** — dependencies point inward; outer layers depend on inner layers, never the reverse

### 1.2 Architecture Overview Diagram

```
================================================================================
                          HIGH-LEVEL ARCHITECTURE
================================================================================

  +------------------------------------------------------------------+
  |                     PRESENTATION LAYER (GUI)                      |
  |  (PySide6 Windows, Dialogs, Widgets, View Models)                |
  +------------------------------------------------------------------+
            |                      |                      |
            v                      v                      v
  +------------------------------------------------------------------+
  |                    APPLICATION LAYER (Services)                    |
  |  (Use Cases, Service Orchestration, DTOs)                         |
  +------------------------------------------------------------------+
            |                      |                      |
            v                      v                      v
  +------------------------------------------------------------------+
  |                      DOMAIN LAYER (Core)                          |
  |  (Entities, Business Rules, Value Objects, Repository Interfaces) |
  +------------------------------------------------------------------+
            |                      |                      |
            v                      v                      v
  +------------------------------------------------------------------+
  |                   INFRASTRUCTURE LAYER                             |
  |  +----------+  +----------+  +----------+  +------------------+   |
  |  | Database |  |   PDF    |  |    AI    |  | File System      |   |
  |  | (SQLite) |  |(ReportLab)|  | (Local)  |  | (JSON/PDF Store) |   |
  |  +----------+  +----------+  +----------+  +------------------+   |
  |  +----------+  +----------+  +------------------+                 |
  |  | Logging  |  | Config  |  | Future Integ.    |                 |
  |  | (Loguru) |  | (JSON)  |  | (Plugin System)  |                 |
  |  +----------+  +----------+  +------------------+                 |
  +------------------------------------------------------------------+

================================================================================
                          DEPENDENCY DIRECTION
================================================================================

  GUI Layer  ──>  Services Layer  ──>  Domain Layer  <──  Infrastructure Layer

  All dependencies point INWARD toward the Domain Layer.
  Infrastructure implements interfaces defined by the Domain Layer.
  The Domain Layer has ZERO external dependencies.
```

### 1.3 Dependency Inversion Principle

```
  Domain Layer (pure Python)
       │
       │  defines interfaces (ports)
       │
       ▼
  Service / Infrastructure Layers
       │
       │  implement interfaces (adapters)
       │
       ▼
  SQLAlchemy, ReportLab, PySide6, etc.
```

---

## 2. Modular Architecture

### 2.1 Module Map

```
================================================================================
                            MODULE ARCHITECTURE
================================================================================

  app/
  ├── core/              # DOMAIN LAYER — Framework-independent business logic
  │   ├── entities/      #   Business entities (Letter, User, Department, etc.)
  │   ├── value_objects/ #   Value objects (Address, DocumentID, etc.)
  │   ├── repositories/  #   Repository interfaces (ports)
  │   ├── services/      #   Domain services (business rules)
  │   └── exceptions/    #   Domain-specific exceptions
  │
  ├── services/          # APPLICATION LAYER — Use case orchestration
  │   ├── letter_service.py
  │   ├── user_service.py
  │   ├── archive_service.py
  │   ├── backup_service.py
  │   ├── audit_service.py
  │   └── integration/   #   Integration service adapters (future)
  │
  ├── database/          # INFRASTRUCTURE — Persistence
  │   ├── connection.py  #   SQLAlchemy engine, session factory
  │   ├── models.py      #   ORM models (SQLAlchemy)
  │   ├── repositories/  #   Repository implementations
  │   └── migrations/    #   Alembic migrations
  │
  ├── pdf/               # INFRASTRUCTURE — PDF generation
  │   ├── generator.py   #   ReportLab engine wrapper
  │   ├── templates/     #   ReportLab templates (programmatic)
  │   └── renderer.py    #   RTL-safe document renderer
  │
  ├── ai/                # INFRASTRUCTURE — Local AI assistant
  │   ├── engine.py      #   AI inference engine
  │   ├── pipeline.py    #   Text processing pipeline
  │   ├── rules/         #   Rule-based checks
  │   └── models/        #   Local model files (non-code)
  │
  ├── gui/               # PRESENTATION — PySide6 interface
  │   ├── main_window.py
  │   ├── views/         #   Main views (letters, archive, settings)
  │   ├── dialogs/       #   Modal dialogs
  │   ├── widgets/       #   Reusable widgets (Arabic RTL aware)
  │   └── view_models/   #   Qt Model/View models
  │
  ├── config/            # INFRASTRUCTURE — Configuration
  │   ├── settings.py    #   Settings loader
  │   └── defaults.json  #   Default configuration
  │
  ├── utils/             # SHARED — Cross-cutting utilities
  │   ├── logger.py      #   Logging configuration
  │   ├── file_utils.py  #   Atomic file operations
  │   ├── validators.py  #   Validation helpers
  │   └── helpers.py     #   General utilities
  │
  ├── plugins/           # PLUGIN SYSTEM — Isolated extensions
  │   ├── registry.py    #   Plugin registry
  │   ├── interface.py   #   Plugin base class
  │   └── loader.py      #   Safe plugin loader
  │
  ├── assets/            # STATIC RESOURCES
  │   ├── fonts/         #   Arabic fonts
  │   ├── icons/         #   Application icons
  │   └── templates/     #   Template resources
  │
  ├── database/          # RUNTIME DATA DIRECTORIES
  ├── backups/           # (created at runtime)
  ├── logs/              #
  ├── generated_letters/ #
  └── temp/              #
```

### 2.2 Module Dependency Rules

```
  MODULE        DEPENDS ON                          DEPENDS ON IT
  ─────────────────────────────────────────────────────────────────
  core/         (nothing — pure Python)              services/, database/, pdf/, ai/, gui/
  services/     core/, config/                       gui/
  database/     core/, config/                       services/
  pdf/          core/, config/, assets/              services/
  ai/           core/, config/                       services/ (or called from GUI)
  gui/          services/, config/                   (nothing — outermost layer)
  config/       utils/                               (everyone)
  utils/        (nothing)                            (everyone)
  plugins/      core/, config/                       (loaded by core)
```

---

## 3. Layered Architecture

### 3.1 Layer Responsibilities

```
================================================================================
                          LAYERED ARCHITECTURE
================================================================================

  Layer             Responsibility                          Framework Tied?
  ──────────────────────────────────────────────────────────────────────────────
  Presentation      UI rendering, user input handling,      Yes (PySide6)
                    view models, event dispatching

  Application       Use case orchestration, DTO mapping,    No
                    transaction coordination, authorization

  Domain            Business entities, business rules,      No
                    repository interfaces, value objects    (PURE PYTHON)

  Infrastructure    Database access, PDF generation,        Yes (SQLAlchemy,
                    AI inference, file I/O, logging,        ReportLab, etc.)
                    configuration loading
```

### 3.2 Layer Communication

```
  User Action
       │
       ▼
  [Presentation Layer]  ──DTO──>  [Application Layer]
       ▲                                   │
       │                                   │
       │                              Use repository interface
       │                                   │
       │                                   ▼
       │                          [Domain Layer] (interfaces only)
       │                                   │
       │                                   │
       │                          [Infrastructure Layer] implements interfaces
       │                                   │
       │                                   ▼
       │                            SQLite / File System / PDF
       │
  Response (result/error) <── DTO <────────┘
```

---

## 4. Core Modules

### 4.1 Domain Module (`core/`)

The domain layer is the heart of the system — framework-independent, pure Python.

```
  core/
  ├── __init__.py
  ├── entities/
  │   ├── __init__.py
  │   ├── letter.py              # Letter entity
  │   ├── user.py                # User entity
  │   ├── department.py          # Department entity
  │   ├── archive.py             # Archive record entity
  │   └── audit_log.py           # Audit entry entity
  │
  ├── value_objects/
  │   ├── __init__.py
  │   ├── letter_number.py       # Official letter numbering
  │   ├── document_id.py         # Document identifier
  │   ├── date_range.py          # Date range value object
  │   └── address.py             # Address value object
  │
  ├── repositories/
  │   ├── __init__.py
  │   ├── letter_repository.py   # Interface
  │   ├── user_repository.py     # Interface
  │   ├── archive_repository.py  # Interface
  │   └── audit_repository.py    # Interface
  │
  ├── services/
  │   ├── __init__.py
  │   ├── letter_domain_service.py  # Business rules for letters
  │   └── archive_domain_service.py # Business rules for archiving
  │
  └── exceptions/
      ├── __init__.py
      ├── base.py                # Base domain exception
      ├── letter_exceptions.py   # Letter-related exceptions
      └── archive_exceptions.py  # Archive-related exceptions
```

### 4.2 Core Business Entities

```
  +------------------+       +------------------+
  |     Letter       |       |      User        |
  +------------------+       +------------------+
  | letter_id: UUID  |       | user_id: UUID    |
  | number: str      |       | full_name: str   |
  | subject: str     |       | role: UserRole   |
  | body: str        |       | department: str  |
  | sender: str      |       | is_active: bool  |
  | recipient: str   |       +------------------+
  | department: str  |               |
  | status: enum     |               |
  | created_at: dt   |               |
  | archived: bool   |               |
  +------------------+               |
          |                          |
          v                          v
  +------------------+       +------------------+
  |   ArchiveLog     |       |   AuditEntry     |
  +------------------+       +------------------+
  | archive_id: UUID |       | entry_id: UUID   |
  | letter_id: UUID  |       | user_id: UUID    |
  | archived_by: str |       | action: str      |
  | archived_at: dt  |       | timestamp: dt    |
  | hash_sha256: str |       | details: JSON    |
  +------------------+       +------------------+
```

### 4.3 Application Services (`services/`)

```
  services/
  ├── __init__.py
  ├── letter_service.py       # Letter CRUD use cases
  ├── user_service.py         # User management use cases
  ├── archive_service.py      # Archive/restore use cases
  ├── backup_service.py       # Backup/restore use cases
  ├── audit_service.py        # Audit logging use cases
  ├── search_service.py       # Full-text search use cases
  ├── report_service.py       # Reporting use cases
  └── integration/            # Future integration adapters
      ├── __init__.py
      ├── base_adapter.py     # Abstract integration adapter
      ├── gula_adapter.py     # Gula platform adapter (future)
      └── lab_adapter.py      # Laboratory system adapter (future)
```

---

## 5. Internal Service Boundaries

### 5.1 Service Communication Strategy

Services communicate through:

1. **Direct method calls** (same process, single-threaded orchestration)
2. **Repository interfaces** (domain layer contracts)
3. **DTOs (Data Transfer Objects)** — never pass ORM models to the GUI layer
4. **Events** — future event bus for loose coupling between services

```
  GUI Layer                    Services Layer                Infrastructure
  ──────────                   ──────────────                ──────────────
                          ┌──────────────────┐
  MainWindow ──action──>  │ LetterService    │ ──repo──>  SQLite via Repository
                          │                  │ <──model──
                          │  orchestrates:   │
                          │  1. validate     │ ──service──> AuditService
                          │  2. persist      │              (logs action)
                          │  3. generate PDF │ ──service──> PDFService
                          │  4. archive      │              (generates PDF)
                          │  5. log audit    │
                          └──────────────────┘
```

### 5.2 Service Contracts

Each application service exposes a stable public API:

```
  class LetterService:
      def create_letter(dto: CreateLetterDTO) -> LetterDTO
      def get_letter(letter_id: UUID) -> LetterDTO
      def update_letter(dto: UpdateLetterDTO) -> LetterDTO
      def delete_letter(letter_id: UUID) -> None
      def archive_letter(letter_id: UUID) -> ArchiveDTO
      def search_letters(query: SearchQuery) -> PageResult[LetterDTO]
      def generate_pdf(letter_id: UUID) -> FilePath
```

---

## 6. Data Flow Architecture

### 6.1 Letter Creation Flow

```
  +-----------+     +------------+     +----------+     +-----------+     +--------+
  |   GUI     |     |  Service   |     | Domain   |     | Database  |     |  PDF   |
  | (PySide6) |     |   Layer    |     |  Entity  |     |   (Repo)  |     | Engine |
  +-----------+     +------------+     +----------+     +-----------+     +--------+
       |                  |                  |                 |               |
       |  1. User fills  |                  |                 |               |
       |     form, clicks|                  |                 |               |
       |     "Send"      |                  |                 |               |
       |────────────────>|                  |                 |               |
       |                  |                  |                 |               |
       |                  | 2. Create       |                 |               |
       |                  |    LetterEntity |                 |               |
       |                  |───────────────>|                 |               |
       |                  |                 |                 |               |
       |                  |                 | 3. Validate     |               |
       |                  |                 |    business     |               |
       |                  |                 |    rules        |               |
       |                  |                 |<── (ok/error)   |               |
       |                  |                 |                 |               |
       |                  | 4. Persist      |                 |               |
       |                  |────────────────────────────────>|               |
       |                  |                 |                 |               |
       |                  |                 |                 | 5. Confirm    |
       |                  |<────────────────────────────────|               |
       |                  |                 |                 |               |
       |                  | 6. Generate PDF |                 |               |
       |                  |──────────────────────────────────────────────>|
       |                  |                 |                 |               |
       |                  |                 |                 |  7. Return   |
       |                  |<──────────────────────────────────────────────|
       |                  |                 |                 |               |
       |                  | 8. Log audit    |                 |               |
       |                  |────────> (AuditService)           |               |
       |                  |                 |                 |               |
       |  9. Return DTO  |                 |                 |               |
       |<────────────────|                 |                 |               |
       |                  |                 |                 |               |
```

### 6.2 Search Flow

```
  User enters search term
       │
       ▼
  [GUI] SearchView
       │
       │  call service.search_letters(query)
       ▼
  [LetterService]
       │
       │  build filter from query
       ▼
  [LetterRepository] (SQLAlchemy)
       │
       │  LIKE search on subject/body/number
       │  + full-text search (FTS5) for large bodies
       ▼
  [SQLite]
       │
       │  return matching entities
       ▼
  [LetterService]
       │
       │  map entities to DTOs
       ▼
  [GUI] display results in table
```

### 6.3 Archive Flow

```
  User triggers archive
       │
       ▼
  [ArchiveService]
       │
       ├── 1. Validate letter exists and not already archived
       ├── 2. Compute SHA-256 hash of current letter state
       ├── 3. Set letter.archived = True in database
       ├── 4. Write immutable JSON archive file to backups/
       ├── 5. Generate archival PDF with "ARCHIVED" watermark
       ├── 6. Log archive action via AuditService
       └── 7. Return ArchiveDTO to GUI
```

---

## 7. Database Architecture

### 7.1 Database Technology

- **Engine**: SQLite (embedded, zero-configuration)
- **ORM**: SQLAlchemy 2.0+ (declarative mapping)
- **Migrations**: Alembic
- **Full-Text Search**: SQLite FTS5 extension
- **Concurrency**: WAL mode for read concurrency; single writer

### 7.2 Schema Design

```
  +====================+     +====================+     +====================+
  |      letters       |     |       users        |     |    departments     |
  +====================+     +====================+     +====================+
  | id (PK, UUID)      |     | id (PK, UUID)      |     | id (PK, UUID)      |
  | number (UNIQUE)     |     | username (UNIQUE)  |     | name (UNIQUE)      |
  | subject             |     | full_name          |     | code                |
  | body                |     | password_hash      |     | parent_id (FK)      |
  | sender              |     | role               |     | is_active           |
  | recipient           |     | department_id (FK) |     +====================+
  | department_id (FK)  |     | is_active          |              │
  | status              |     | created_at         |              │
  | priority            |     +====================+              │
  | created_at          |              │                          │
  | updated_at          |              │                          │
  | archived            |              │                          │
  | hash_sha256         |              │                          │
  +====================+              │                          │
           │                          │                          │
           │                          │                          │
           v                          v                          v
  +====================+     +====================+     +====================+
  |   audit_logs       |     |   archive_index    |     |   letter_attachments|
  +====================+     +====================+     +====================+
  | id (PK, UUID)      |     | id (PK, UUID)      |     | id (PK, UUID)      |
  | user_id (FK)       |     | letter_id (FK)     |     | letter_id (FK)     |
  | action              |     | archive_path       |     | filename            |
  | entity_type         |     | hash_sha256        |     | file_path           |
  | entity_id           |     | archived_by (FK)   |     | mime_type           |
  | details (JSON)      |     | archived_at        |     | size_bytes          |
  | ip_address          |     | restored_at        |     +====================+
  | created_at          |     | restored_by        |
  +====================+     +====================+

  +====================+     +====================+
  |     backups        |     | system_config      |
  +====================+     +====================+
  | id (PK, UUID)      |     | key (PK, str)      |
  | backup_path        |     | value (JSON)       |
  | size_bytes         |     | description        |
  | hash_sha256        |     | updated_at         |
  | created_by (FK)    |     +====================+
  | created_at         |
  | restored_at        |
  +====================+

  +====================+
  | letter_fts (VIRTUAL|
  |  USING fts5)       |
  +====================+
  | content             |
  | subject             |
  | number              |
  +====================+
```

### 7.3 Repository Pattern

```
  ┌──────────────────────────────┐
  │   LetterRepository (interface)│  ← Defined in core/repositories
  │   + find_by_id(id)           │
  │   + find_by_number(num)      │
  │   + search(query, page)      │
  │   + save(letter)             │
  │   + delete(letter)           │
  │   + count(filters)           │
  └──────────────────────────────┘
              ▲
              │ implements
              │
  ┌──────────────────────────────┐
  │ SQLAlchemyLetterRepository    │  ← Implemented in database/repositories
  │  (wraps SQLAlchemy session)   │
  └──────────────────────────────┘
```

### 7.4 Migration Strategy

- All schema changes go through Alembic migrations
- Each migration is reversible (upgrade + downgrade)
- Migration version is stored in the database
- Application checks migration version on startup
- Automatic migration runs on version mismatch (with rollback on failure)

---

## 8. File Storage Architecture

### 8.1 Directory Layout

```
  user_data/
  ├── database/
  │   └── correspondence.db          # SQLite database
  │
  ├── archives/
  │   ├── index.json                 # Archive index
  │   ├── 2026/
  │   │   ├── 01/
  │   │   │   ├── L-2026-0001.json   # Archived letter JSON
  │   │   │   ├── L-2026-0001.pdf    # Archived letter PDF
  │   │   │   └── ...
  │   │   └── ...
  │   └── ...
  │
  ├── backups/
  │   ├── backup-2026-05-28-120000.zip
  │   ├── backup-2026-05-29-120000.zip
  │   └── ...
  │
  ├── generated_letters/
  │   ├── L-2026-0001.pdf
  │   ├── L-2026-0002.pdf
  │   └── ...
  │
  ├── logs/
  │   ├── correspondence.log
  │   ├── correspondence.log.1
  │   └── ...
  │
  └── temp/                          # Isolated temporary directory
      └── (cleared on startup)
```

### 8.2 Atomic File Writes

```
  def atomic_write(path: Path, content: bytes) -> None:
      """Write file atomically to prevent corruption."""
      temp_path = path.with_suffix(f"{path.suffix}.tmp")
      temp_path.write_bytes(content)
      temp_path.rename(path)  # Atomic on same filesystem
```

### 8.3 File Integrity

- SHA-256 hash stored alongside every archived file
- Hash verified on archive restore
- Corruption detection on read

---

## 9. PDF Generation Pipeline

### 9.1 Pipeline Flow

```
  +----------------+     +---------------+     +--------------+
  |  Input: DTO    |     |  Template     |     |  Renderer    |
  |  Letter Data   |──>  |  Selection    |──>  |  (ReportLab) |
  +----------------+     +---------------+     +--------------+
                                                      │
                                                      v
  +----------------+     +---------------+     +--------------+
  |  Output: PDF   |     |  Hash +       |     |  RTL Layout  |
  |  File          |<──  |  Verify       |<──  |  Processing  |
  +----------------+     +---------------+     +--------------+
```

### 9.2 PDF Generation Steps

```
  1. LetterService.create_letter() completes
       │
       ▼
  2. PDFService.generate_letter_pdf(letter_dto)
       │
       ├── 2a. Select template (official letter, memo, etc.)
       ├── 2b. Map DTO fields to template placeholders
       ├── 2c. Apply RTL layout (right-to-left text direction)
       ├── 2d. Embed Arabic fonts (ReportLab TTF embedding)
       ├── 2e. Add governmental header/footer (protected template)
       ├── 2f. Generate PDF bytes (deterministic, same input = same output)
       ├── 2g. Compute SHA-256 of PDF
       ├── 2h. Write to generated_letters/ directory
       └── 2i. Return FilePath + Hash
```

### 9.3 Deterministic Generation Guarantee

- Fixed random seed for ReportLab
- No date/time stamps in document content (except explicit date fields)
- Consistent font metrics across platforms (embedded fonts)
- Template version pinned to document format version

---

## 10. AI Local Assistant Architecture

### 10.1 Architecture Overview

```
  +------------------+       +------------------+
  |   GUI Widget     |       |  AI Pipeline     |
  | (Text Editor +   |<─────>|  (non-blocking)  |
  |  AI Panel)       |       |                  |
  +------------------+       +------------------+
                                      │
                                      v
  +------------------+       +------------------+       +------------------+
  |  Spell Checker   |       |  Grammar Checker |       |  Wording Engine  |
  |  (SymSpell/PySpel|       |  (Rule-based +   |       |  (Template-based)|
  |   ller local dict)|       |   Pattern Grammar)|      |                  |
  +------------------+       +------------------+       +------------------+
                                      │
                                      v
  +------------------+       +------------------+
  |  Colloquial      |       |  Formatter       |
  |  Detector        |       |  (Layout/         |
  |  (Arabic keyword |       |   Style Suggest)  |
  |   list + rules)  |       |                   |
  +------------------+       +------------------+
```

### 10.2 AI Constraints

- **No external APIs** — all models and rules are local
- **No internet access** — fully offline
- **Non-blocking** — runs in background thread; GUI remains responsive
- **User approval required** — all suggestions are advisory
- **Auditable** — all AI actions are logged

### 10.3 AI Pipeline Sequence

```
  User types text in editor
       │
       ▼
  [AI Panel] user clicks "Check"
       │
       │  submit to AI pipeline (background QThread)
       ▼
  [AI Pipeline]
       ├── 1. Spell check (local dictionary)
       ├── 2. Grammar check (rule-based patterns)
       ├── 3. Colloquial detection (keyword matching)
       ├── 4. Wording suggestions (template-based)
       └── 5. Formatting suggestions
       │
       ▼
  [Return suggestions to GUI]
       │
       ▼
  [User reviews and accepts/rejects each suggestion]
       │
       ▼
  [Accepted changes applied to document]
       │
       ▼
  [Audit log of AI-assisted changes]
```

---

## 11. Backup and Recovery Architecture

### 11.1 Backup Types

| Type | Trigger | Contents | Retention |
|---|---|---|---|
| Auto-backup | Daily on app close | Database + config + archives index | 30 days |
| Manual backup | User-initiated | Full snapshot (database + archives + config) | User-managed |
| Pre-migration | Before schema update | Database only | Until next migration |

### 11.2 Backup Flow

```
  [BackupService.start_backup()]
       │
       ├── 1. Acquire database lock (WAL checkpoint)
       ├── 2. Copy database file to temp directory
       ├── 3. Collect archive index + config
       ├── 4. Bundle into ZIP archive
       ├── 5. Compute SHA-256 of backup file
       ├── 6. Write backup to backup directory
       ├── 7. Record backup entry in database
       ├── 8. Remove old backups (retention policy)
       └── 9. Release database lock
```

### 11.3 Recovery Flow

```
  [BackupService.restore(backup_id)]
       │
       ├── 1. Verify backup file exists
       ├── 2. Verify SHA-256 integrity
       ├── 3. Verify backup version compatibility
       ├── 4. Acquire exclusive database lock
       ├── 5. Backup current state (pre-restore safety)
       ├── 6. Replace database file
       ├── 7. Restore configuration
       ├── 8. Verify restored database integrity
       ├── 9. Log restore operation
       └── 10. Release database lock
```

---

## 12. Logging Architecture

### 12.1 Logging Framework

- **Library**: `loguru` (zero-boilerplate, structured logging)
- **Output**: Rotating file + console (debug mode)
- **Format**: JSON-structured for machine parsing

### 12.2 Log Categories

```
  Logger            Purpose                                  Level
  ─────────────────────────────────────────────────────────────────
  app              General application events               INFO
  app.database     Database queries, migrations             INFO
  app.security     Authentication, authorization            WARNING
  app.audit        User actions (immutable log)             INFO
  app.pdf          PDF generation events                    INFO
  app.ai           AI assistant operations                  INFO
  app.backup       Backup and restore operations            INFO
  app.error        Unhandled exceptions, critical faults    ERROR
```

### 12.3 Log Rotation

```
  - 10 MB max per file
  - 10 rotated files retained
  - Compression after rotation
  - Logs stored in app/logs/
```

### 12.4 Audit Trail Immutability

```
  Audit logs are also written to the database (audit_logs table)
  Database audit records are never deleted (soft-delete / archive only)
  Audit records include: user, timestamp, action, entity type, entity ID, details (JSON)
```

---

## 13. Error Handling Architecture

### 13.1 Error Classification

```
  Error Type        Example                         Recovery
  ─────────────────────────────────────────────────────────────────
  Domain            Invalid letter number format     User input correction
  Validation        Missing required field           User input correction
  Infrastructure    Database connection failure      Retry / reconnect
  Application       Service unavailable              Graceful degradation
  System            Out of disk space                User notification
  Critical          Database corruption              Restore from backup
```

### 13.2 Error Handling Strategy

```
  ┌─────────────────────────────────────────────┐
  │              GUI Layer                       │
  │  Catches service exceptions, displays       │
  │  user-friendly Arabic error messages        │
  └─────────────────────┬───────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────┐
  │            Application Layer                 │
  │  Wraps domain/infra exceptions in            │
  │  ServiceException with user message + code   │
  └─────────────────────┬───────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────┐
  │            Domain Layer                      │
  │  Raises typed domain exceptions              │
  │  (no external dependency)                    │
  └─────────────────────┬───────────────────────┘
                        │
  ┌─────────────────────▼───────────────────────┐
  │         Infrastructure Layer                 │
  │  Catches technical exceptions, logs them,   │
  │  wraps in domain-appropriate exceptions      │
  └─────────────────────────────────────────────┘
```

### 13.3 Retry Strategy

```
  Recoverable operations (database connection, file I/O):
    - Retry 3 times with exponential backoff (1s, 2s, 4s)
    - After exhaustion: log critical, notify user, offer retry
```

### 13.4 Crash Recovery

```
  Application startup:
    1. Check for crash recovery flag (unclean shutdown marker)
    2. If set:
       a. Verify database integrity (PRAGMA integrity_check)
       b. Check for partial writes in temp/ and recover/clean
       c. Verify last backup integrity
       d. Log recovery check complete
    3. Clear crash recovery flag
    4. Start normally
```

---

## 14. Future Integration Architecture

### 14.1 Integration Adapter Pattern

```
  +------------------+       +------------------+
  |  Core System     |       |  Integration     |
  |  (Offline-first) |<─────>|  Service Layer   |
  +------------------+       +------------------+
                                      │
                          ┌───────────┼───────────┐
                          │           │           │
                          ▼           ▼           ▼
                  +----------+ +----------+ +----------+
                  |  Gula    | |  Lab     | |  Gov     |
                  | Adapter  | | Adapter  | | Archiver |
                  +----------+ +----------+ +----------+
```

### 14.2 Integration Principles

```
  - Each integration is an isolated adapter module
  - Integration modules live under services/integration/
  - Integrations communicate through the IntegrationService interface
  - Core system has NO knowledge of adapters
  - Adapter failures never crash the core system
  - All integration is opt-in
```

### 14.3 Integration Interface

```
  class BaseIntegrationAdapter(ABC):
      @abstractmethod
      def send_document(self, letter_dto: LetterDTO) -> Result
      @abstractmethod
      def receive_document(self, external_id: str) -> Result
      @abstractmethod
      def health_check(self) -> bool
      @property
      def name(self) -> str
```

### 14.4 Data Exchange Format

```
  JSON payload for integration:
  {
      "version": "1.0",
      "type": "letter",
      "id": "uuid",
      "number": "L-2026-0001",
      "subject": "...",
      "sender": "...",
      "recipient": "...",
      "created_at": "2026-05-28T10:00:00",
      "pdf_url": "file:///path/to/letter.pdf",
      "hash_sha256": "..."
  }
```

---

## 15. Plugin/Extension Architecture

### 15.1 Plugin System Design

```
  +------------------+
  |  PluginRegistry  |  ← Core component
  |  - load_all()    |
  |  - get(name)     |
  |  - register()    |
  +------------------+
          │
          │  loads from app/plugins/
          ▼
  +------------------+       +------------------+
  |  PluginInterface |<──────|  ConcretePlugin |
  |  + activate()    |       |  + activate()    |
  |  + deactivate()  |       |  + deactivate()  |
  |  + execute()     |       |  + execute()     |
  +------------------+       +------------------+
```

### 15.2 Plugin Isolation Rules

```
  - Plugins live in a dedicated app/plugins/ directory
  - Each plugin is a subdirectory with a manifest
  - Plugins are loaded in a restricted namespace (no access to core internals)
  - Plugin execution is wrapped in try/except — failure never crashes host
  - Plugins can define optional hooks (on_letter_create, on_archive, etc.)
  - Plugin manifest declares: name, version, author, hooks, dependencies
```

### 15.3 Plugin Loading Sequence

```
  Application startup:
    1. Scan plugins/ directory
    2. Validate each plugin manifest
    3. Load plugin Python module
    4. Instantiate plugin class
    5. Register hooks with PluginRegistry
    6. Call plugin.activate()
    7. On error: log warning, disable plugin, continue
```

---

## 16. Offline-First Architecture

### 16.1 Core Principle

Every feature works fully without internet connectivity. Network is never assumed.

### 16.2 Offline Design Patterns

```
  Pattern              Application
  ────────────────────────────────────────────────────────────
  Local-first data     All data stored in local SQLite
  Local AI             All AI models bundled with app
  No remote calls      No HTTP requests for core features
  Graceful absence     Features that could use network degrade gracefully
  Optional sync        Future integration is opt-in ADDITIVE
  Local fonts          Arabic fonts bundled, no system font dependency
  Self-contained       All resources (templates, config) are local files
```

### 16.3 What Runs Offline

```
  ✓ Letter creation, editing, deletion       FULLY OFFLINE
  ✓ PDF generation and printing              FULLY OFFLINE
  ✓ Search and archive retrieval             FULLY OFFLINE
  ✓ AI spell/grammar check                   FULLY OFFLINE
  ✓ Backup and restore                       FULLY OFFLINE
  ✓ User authentication                      FULLY OFFLINE
  ✓ Audit logging                            FULLY OFFLINE
  ✓ Configuration management                 FULLY OFFLINE

  ✗ Future Gula platform integration         OPTIONAL (adds on top)
  ✗ Future laboratory system sync            OPTIONAL (adds on top)
  ✗ Future ministry platform push            OPTIONAL (adds on top)
```

---

## 17. Windows Deployment Architecture

### 17.1 Deployment Model

```
  PyInstaller
       │
       │  Bundles:
       │    - Python interpreter
       │    - Application code
       │    - All dependencies (PySide6, SQLAlchemy, ReportLab, etc.)
       │    - Arabic fonts
       │    - AI models/rules
       │    - Default templates
       │    - Configuration defaults
       ▼
  Single executable (or single directory)
       │
       │  On first run:
       │    - Creates user data directory
       │    - Initializes SQLite database
       │    - Runs initial migration
       │    - Copies default config
       ▼
  Fully operational system
```

### 17.2 Directory Structure (Deployed)

```
  Installation Directory (Program Files / Portable):
  ├── oglg.exe                     # Main executable
  ├── oglg-cli.exe                 # CLI utilities (backup, restore, migrate)
  ├── _internal/                   # PyInstaller bundled runtime
  │   ├── Python/
  │   ├── Lib/
  │   └── ...
  │
  User Data Directory (%APPDATA%/oglg/ OR portable/data/):
  ├── database/
  │   └── correspondence.db
  ├── archives/
  ├── backups/
  ├── generated_letters/
  ├── logs/
  └── config.json
```

### 17.3 Windows Compatibility

```
  - Windows 7, 8, 10, 11: fully supported
  - No admin privileges required after installation
  - No Windows registry dependencies
  - Portable mode: run from USB drive (data stored alongside executable)
  - PyInstaller build: single-folder or single-file option
```

---

## 18. Security Architecture

### 18.1 Security Layers

```
  +----------------------------------------------------+
  |  Application Security                               |
  |  - Role-based access control (RBAC)                |
  |  - User authentication with password hashing        |
  |  - Session management (application-level)           |
  +----------------------------------------------------+
  |  Data Security                                      |
  |  - SQLite file permissions (OS-level)               |
  |  - Optional encrypted backups (AES-256)             |
  |  - SHA-256 integrity verification                   |
  +----------------------------------------------------+
  |  Operational Security                               |
  |  - Audit logging (all user actions)                 |
  |  - Immutable archives (read-only after archive)     |
  |  - Deletion confirmation required                   |
  +----------------------------------------------------+
```

### 18.2 Authentication

```
  - Local authentication only (no external identity provider)
  - Passwords hashed with bcrypt/argon2
  - User roles: Admin, Editor, Viewer, Auditor
  - Role determines available actions and views
```

### 18.3 Authorization Rules

```
  Action                  Admin   Editor   Viewer   Auditor
  ───────────────────────────────────────────────────────────
  Create letter             ✓       ✓        –        –
  Edit letter               ✓       ✓        –        –
  Delete letter             ✓       –        –        –
  Archive letter            ✓       ✓        –        –
  Restore archive           ✓       –        –        –
  View letters              ✓       ✓        ✓        ✓
  Manage users              ✓       –        –        –
  Manage settings           ✓       –        –        –
  View audit logs           ✓       –        –        ✓
  Create backups            ✓       ✓        –        –
  Restore backups           ✓       –        –        –
```

---

## 19. Audit Architecture

### 19.1 Audit Events

Every significant user action is recorded:

```
  Event                     Data Captured
  ──────────────────────────────────────────────────────────
  User login                user, timestamp, success/fail
  Letter created            user, letter number, timestamp
  Letter edited             user, letter number, field changes
  Letter deleted            user, letter number, timestamp
  Letter archived           user, letter number, hash, timestamp
  Letter restored           user, letter number, timestamp
  PDF generated             user, letter number, file path
  PDF printed               user, letter number, printer name
  Backup created            user, backup path, size, hash
  Backup restored           user, backup id, timestamp
  AI suggestion applied     user, letter, suggestion type, accepted/rejected
  Configuration changed     user, config key, old value, new value
  User management           admin, action, target user, timestamp
  Migration run             version from, version to, result
  Error / crash             error type, traceback, context
```

### 19.2 Audit Implementation

```
  [GUI Action]
       │
       ▼
  [Service Method]  ← calls →  [AuditService.log()]
                                    │
                                    │  writes to:
                                    ▼
                            [audit_logs database table]
                                    │
                                    │  (never deleted, never edited)
                                    ▼
                          [rotated text log file]
```

### 19.3 Audit Log Properties

```
  - Append-only: once written, audit records are never modified
  - Immutable: archived records cannot be altered
  - Timestamped: every entry has a reliable timestamp
  - User-attributed: every action is linked to a user
  - Exportable: audit logs can be exported for external review
```

---

## 20. Scalability Strategy

### 20.1 Vertical Scalability (Current)

```
  SQLite scales with hardware:
    - Faster storage (SSD) improves query performance
    - More RAM improves cache efficiency
    - WAL mode allows concurrent reads

  Practical limits for this system:
    - Letters: 100,000+ per year (tested target)
    - Users: 500+ per deployment
    - Archives: 1,000,000+ documents (10+ year target)
    - PDFs: 100,000+ stored files
```

### 20.2 Scaling Techniques

```
  Technique              Application
  ───────────────────────────────────────────────────────────
  Pagination             All list views use LIMIT/OFFSET
  Lazy loading           Archive indexes loaded on demand
  Indexed queries        Key columns indexed (number, date, user, status)
  FTS5 full-text search  Fast body/subject search on large datasets
  Archive partitioning   Year/month directory structure
  Database WAL mode      Concurrent read access without locking
  Periodic VACUUM        Prevent database file bloat
  Configurable archive   Archive older letters to file system, out of DB
```

### 20.3 Future Scaling (Optional)

```
  For deployments exceeding 500k+ active letters:
    - Optional read-replica SQLite (separate process)
    - Optional archive-only database separation
    - All optional: default deployment scales vertically
```

---

## 21. Performance Strategy

### 21.1 Performance Targets

```
  Metric                        Target
  ──────────────────────────────────────────────────────
  Cold startup time             < 3 seconds
  Warm startup time             < 1.5 seconds
  Letter creation               < 500ms
  PDF generation                < 2 seconds
  Search (10k letters)          < 200ms
  Archive lookup                < 100ms
  AI check (1 page text)        < 1 second
  Backup (10k letters)          < 10 seconds
  Restore (10k letters)         < 15 seconds
  RAM usage (idle)              < 200MB
  RAM usage (active)            < 400MB
  CPU usage (idle)              < 1%
```

### 21.2 Performance Patterns

```
  Pattern                    Implementation
  ──────────────────────────────────────────────────────────
  Lazy initialization        Services/objects created on demand
  Background threads         AI, PDF, Backup run in QThread
  Connection pooling         Single SQLAlchemy engine, reused
  Prepared statements        SQLAlchemy caching
  Batch operations           Bulk inserts for imports
  Caching                    Frequently accessed config cached in memory
  Resource cleanup           Periodic GC, explicit resource disposal
  No busy loops              All waits use signal/slot or event-driven
```

### 21.3 Anti-Patterns (Forbidden)

```
  ✗ Blocking the UI thread with database/PDF/AI operations
  ✗ Loading entire datasets into memory
  ✗ Polling loops
  ✗ Creating new database connections per operation
  ✗ Heavy computation on the main thread
  ✗ Unbounded cache growth
  ✗ Synchronous file I/O on main thread
```

---

## 22. Dependency Isolation Strategy

### 22.1 Isolation Layers

```
  Layer               Dependencies                    Isolation
  ──────────────────────────────────────────────────────────────────
  Domain (core/)      None (pure Python stdlib)       COMPLETE
  Services            core/, config/                  Framework-agnostic
  GUI (PySide6)       services/, config/              Tied to PySide6
  Database            core/, config/, SQLAlchemy      Replaceable
  PDF                 core/, config/, ReportLab       Replaceable
  AI                  core/, config/                  Replaceable
  Plugins             core/, config/                  Isolated by design
```

### 22.2 Dependency Rules

```
  1. The domain layer imports NOTHING except Python stdlib
  2. Service layer imports only domain entities and interfaces
  3. Infrastructure layer implements domain interfaces
  4. GUI depends on services (not directly on infrastructure)
  5. No circular imports (enforced by architecture, checked by linters)
  6. No shared mutable state
  7. All external dependencies are behind an interface in core/
```

### 22.3 Replaceability

```
  To replace ReportLab with another PDF engine:
    1. Implement PDFEngine interface (defined in core/)
    2. Wire new implementation in PDFService
    3. No changes to domain or services layer

  To replace SQLAlchemy with another ORM:
    1. Implement repository interfaces (defined in core/)
    2. Implement new repository classes
    3. Wire in dependency injection
    4. No changes to domain or services layer
```

---

## 23. Update and Migration Strategy

### 23.1 Application Updates

```
  Update Types:
    - Patch (1.0.0 → 1.0.1): Bug fixes, no schema changes
    - Minor (1.0.0 → 1.1.0): New features, backward-compatible schema
    - Major (1.0.0 → 2.0.0): Breaking changes, schema migrations

  Update Process:
    1. Replace executable (or files)
    2. On first run, check database version
    3. If version mismatch, run migrations
    4. If migration fails: rollback, log error, notify user
    5. On success: update version, log success
```

### 23.2 Database Migrations

```
  Migration workflow (Alembic):
    1. Developer creates migration script (autogenerate from models)
    2. Migration script includes upgrade() and downgrade()
    3. Script is tested against test database
    4. Migration is included in the release
    5. On application startup, migration runs automatically
    6. Failed migration triggers rollback
    7. Pre-migration backup is created automatically
```

### 23.3 Archive Format Migration

```
  Archive JSON format is versioned:
    - Version field in every JSON archive file
    - Migration path for reading older formats
    - Backward compatibility: newer app reads older archives
    - Forward notification: older app warns if newer format detected
```

---

## 24. Fail-Safe and Crash Recovery Strategy

### 24.1 Fail-Safe Principles

```
  1. Every write operation is atomic
  2. Every critical operation is wrapped in transaction
  3. Every external resource has timeout and retry
  4. Every user action is validated before execution
  5. Every failure is logged with context
  6. Every crash can be recovered without data loss
```

### 24.2 Recovery State Machine

```
  Application State:
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │   NORMAL OPERATION                                              │
  │       │                                                         │
  │       │ (unexpected error)                                      │
  │       ▼                                                         │
  │   ERROR DETECTED ──── (recoverable) ───> RETRY ──> NORMAL       │
  │       │                                                         │
  │       │ (unrecoverable)                                         │
  │       ▼                                                         │
  │   SAFE STATE     ──── (user action)  ───> RECOVERY ──> NORMAL   │
  │       │                                                         │
  │       │ (crash)                                                  │
  │       ▼                                                         │
  │   CRASH          ──── (restart)      ───> INTEGRITY CHECK       │
  │                                                 │               │
  │                                            (pass/fail)          │
  │                                                 │               │
  │                                            NORMAL / RESTORE     │
  └─────────────────────────────────────────────────────────────────┘
```

### 24.3 Crash Recovery Sequence

```
  Application crash:
       │
       ▼
  On next startup:
    1. Detect crash marker file (written on clean shutdown, absent on crash)
    2. Run SQLite integrity check (PRAGMA integrity_check)
    3. If integrity check fails:
       a. Log critical error
       b. Notify user of potential data corruption
       c. Offer to restore from latest backup
       d. Do not start normally until resolved
    4. If integrity check passes:
       a. Clean up temporary files
       b. Verify archive index consistency
       c. Log recovery success
       d. Start normally
    5. Write crash recovery report to logs/
```

### 24.4 Graceful Degradation

```
  Degradation scenario: AI model fails to load
    - AI features display "unavailable" state
    - All other features continue working
    - Error logged
    - Notification to user (non-blocking)

  Degradation scenario: PDF generation fails
    - Error logged with full context
    - User notified with error message
    - Letter data preserved (already saved to DB)
    - User can retry PDF generation later

  Degradation scenario: Database read error
    - Retry with exponential backoff (3 attempts)
    - If all fail: graceful shutdown, offer backup restore
```

### 24.5 Data Corruption Prevention

```
  - Atomic file writes (write to temp, then rename)
  - Database WAL mode (crash-safe transactions)
  - SHA-256 verification on every archive file
  - Pre-migration backup before schema changes
  - integrity_check on startup after unclean shutdown
  - Read-only archived files (OS file permissions)
  - Database backup before destructive operations
```

---

## Recommended Package Structure (Full)

```
  oglg/                              # Application root
  ├── main.py                        # Entry point
  │
  ├── app/
  │   ├── __init__.py
  │   │
  │   ├── core/                      # DOMAIN LAYER (pure Python)
  │   │   ├── __init__.py
  │   │   ├── entities/
  │   │   │   ├── __init__.py
  │   │   │   ├── letter.py
  │   │   │   ├── user.py
  │   │   │   ├── department.py
  │   │   │   ├── archive.py
  │   │   │   └── audit_log.py
  │   │   │
  │   │   ├── value_objects/
  │   │   │   ├── __init__.py
  │   │   │   ├── letter_number.py
  │   │   │   ├── document_id.py
  │   │   │   └── date_range.py
  │   │   │
  │   │   ├── repositories/
  │   │   │   ├── __init__.py
  │   │   │   ├── letter_repository.py      # Interface
  │   │   │   ├── user_repository.py         # Interface
  │   │   │   ├── archive_repository.py      # Interface
  │   │   │   └── audit_repository.py        # Interface
  │   │   │
  │   │   ├── services/
  │   │   │   ├── __init__.py
  │   │   │   └── letter_domain_service.py
  │   │   │
  │   │   └── exceptions/
  │   │       ├── __init__.py
  │   │       ├── base.py
  │   │       └── letter_exceptions.py
  │   │
  │   ├── services/                   # APPLICATION LAYER
  │   │   ├── __init__.py
  │   │   ├── letter_service.py
  │   │   ├── user_service.py
  │   │   ├── archive_service.py
  │   │   ├── backup_service.py
  │   │   ├── audit_service.py
  │   │   ├── search_service.py
  │   │   ├── report_service.py
  │   │   └── integration/
  │   │       ├── __init__.py
  │   │       ├── base_adapter.py
  │   │       ├── gula_adapter.py          # Future
  │   │       └── lab_adapter.py           # Future
  │   │
  │   ├── database/                   # INFRASTRUCTURE — Persistence
  │   │   ├── __init__.py
  │   │   ├── connection.py
  │   │   ├── models.py
  │   │   ├── repositories/
  │   │   │   ├── __init__.py
  │   │   │   ├── sqlalchemy_letter_repo.py
  │   │   │   ├── sqlalchemy_user_repo.py
  │   │   │   ├── sqlalchemy_archive_repo.py
  │   │   │   └── sqlalchemy_audit_repo.py
  │   │   └── migrations/
  │   │       ├── env.py
  │   │       ├── alembic.ini
  │   │       └── versions/
  │   │
  │   ├── pdf/                        # INFRASTRUCTURE — PDF Generation
  │   │   ├── __init__.py
  │   │   ├── generator.py
  │   │   ├── renderer.py
  │   │   └── templates/
  │   │       ├── __init__.py
  │   │       ├── official_letter.py
  │   │       └── memo.py
  │   │
  │   ├── ai/                         # INFRASTRUCTURE — Local AI
  │   │   ├── __init__.py
  │   │   ├── engine.py
  │   │   ├── pipeline.py
  │   │   ├── spell_checker.py
  │   │   ├── grammar_checker.py
  │   │   ├── wording_engine.py
  │   │   ├── colloquial_detector.py
  │   │   └── formatter.py
  │   │
  │   ├── gui/                        # PRESENTATION — PySide6
  │   │   ├── __init__.py
  │   │   ├── main_window.py
  │   │   ├── app.py                  # QApplication setup
  │   │   ├── views/
  │   │   │   ├── __init__.py
  │   │   │   ├── letter_list_view.py
  │   │   │   ├── letter_editor_view.py
  │   │   │   ├── archive_view.py
  │   │   │   ├── search_view.py
  │   │   │   ├── backup_view.py
  │   │   │   ├── settings_view.py
  │   │   │   └── audit_view.py
  │   │   ├── dialogs/
  │   │   │   ├── __init__.py
  │   │   │   ├── confirm_dialog.py
  │   │   │   ├── error_dialog.py
  │   │   │   └── about_dialog.py
  │   │   ├── widgets/
  │   │   │   ├── __init__.py
  │   │   │   ├── rtl_text_edit.py
  │   │   │   ├── letter_table.py
  │   │   │   └── status_bar.py
  │   │   └── view_models/
  │   │       ├── __init__.py
  │   │       ├── letter_table_model.py
  │   │       └── archive_table_model.py
  │   │
  │   ├── plugins/                    # PLUGIN SYSTEM
  │   │   ├── __init__.py
  │   │   ├── registry.py
  │   │   ├── interface.py
  │   │   └── loader.py
  │   │
  │   ├── config/                     # CONFIGURATION
  │   │   ├── __init__.py
  │   │   ├── settings.py
  │   │   └── defaults.json
  │   │
  │   ├── utils/                      # CROSS-CUTTING
  │   │   ├── __init__.py
  │   │   ├── logger.py
  │   │   ├── file_utils.py
  │   │   ├── validators.py
  │   │   └── helpers.py
  │   │
  │   └── assets/                     # STATIC RESOURCES
  │       ├── fonts/
  │       │   └── (bundled Arabic fonts)
  │       └── icons/
  │           └── (application icons)
  │
  ├── docs/                           # DOCUMENTATION
  │   ├── governance/
  │   ├── architecture/
  │   ├── api/
  │   ├── database/
  │   ├── deployment/
  │   └── modules/
  │
  ├── tests/                          # TEST SUITE
  │   ├── unit/
  │   │   ├── core/
  │   │   ├── services/
  │   │   └── ...
  │   ├── integration/
  │   │   ├── database/
  │   │   ├── pdf/
  │   │   └── ...
  │   └── fixtures/
  │
  ├── scripts/                        # BUILD & UTILITY SCRIPTS
  │   ├── build.bat                   # Windows PyInstaller build
  │   └── build.sh                    # Unix PyInstaller build
  │
  ├── requirements.txt
  ├── pyproject.toml
  ├── README.md
  └── .gitignore
```

---

## Runtime Lifecycle Flow

### Application Startup Sequence

```
  1. OS launches oglg.exe
       │
       ▼
  2. PyInstaller bootloader runs
       │
       ▼
  3. Python interpreter initializes
       │
       ▼
  4. main.py entry point
       │
       ├── 4a. Configure logging (loguru)
       ├── 4b. Load settings (config/settings.py)
       ├── 4c. Initialize database engine (SQLAlchemy + SQLite)
       ├── 4d. Run pending migrations (Alembic)
       ├── 4e. Check crash recovery (integrity check if unclean shutdown)
       ├── 4f. Initialize services (lazy — created on first use)
       ├── 4g. Load plugins (scan, validate, activate)
       ├── 4h. Create main window (PySide6)
       ├── 4i. Restore last session state (window size, position)
       ├── 4j. Check for auto-backup (daily on first launch)
       └── 4k. Enter Qt event loop
```

### Application Shutdown Sequence

```
  1. User closes main window (or OS shutdown signal)
       │
       ▼
  2. Main window closeEvent
       │
       ├── 2a. Prompt if unsaved work (with save confirmation)
       ├── 2b. Save window state (size, position, last view)
       │
       ▼
  3. Application shutdown
       │
       ├── 3a. Deactivate plugins (call plugin.deactivate())
       ├── 3b. Auto-backup (if due)
       ├── 3c. Close database connections
       ├── 3d. Write crash recovery marker (clean shutdown flag)
       ├── 3e. Flush and close log files
       └── 3f. Exit process
```

### Runtime Service Lifecycle

```
  Service             Created        Destroyed
  ──────────────────────────────────────────────────
  LetterService       On first use   Application shutdown
  UserService         On first use   Application shutdown
  ArchiveService      On first use   Application shutdown
  BackupService       On first use   Application shutdown
  AuditService        Application    Application shutdown
                      startup
  SearchService       On first use   Application shutdown
  PDFService          On first use   Application shutdown
  AIService           On first use   Application shutdown
  PluginRegistry      Application    Application shutdown
                      startup
  Database engine     Application    Application shutdown
                      startup
```

---

## Architecture Decision Records (ADRs)

The following key decisions are encoded in this architecture:

| Decision | Rationale |
|---|---|
| Monolithic (not microservices) | Single executable, offline-first, minimal complexity |
| SQLite (not PostgreSQL/MySQL) | Zero configuration, embedded, offline-native |
| Clean Architecture layers | Framework independence, testability, 10-year maintainability |
| Repository pattern | Database abstraction, testability, replaceable storage |
| Service layer | Use case orchestration, business logic outside GUI |
| ReportLab (not WeasyPrint/HTML) | Deterministic output, no browser dependency, RTL control |
| Plugin system (not dynamic loading) | Controlled extension, fault isolation, security |
| PyInstaller (not Nuitka/CX_Freeze) | Mature, stable, Windows-compatible |
| loguru (not stdlib logging) | Structured output, zero-boilerplate, rotation built-in |

---

*This architecture document is a living artifact. Update it as the system evolves. All significant architectural changes must be reflected here and approved through the governance process.*
