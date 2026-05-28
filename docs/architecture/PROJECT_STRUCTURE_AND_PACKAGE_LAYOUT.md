# Project Structure and Package Layout

**Project**: Iraqi Government Offline Official Correspondence System
**Version**: 1.0 (Design Document)
**Last Updated**: 2026-05-28

---

## Table of Contents

1. [Final Package Structure](#1-final-package-structure)
2. [Layer Boundaries](#2-layer-boundaries)
3. [Domain Layer Structure](#3-domain-layer-structure)
4. [Application Layer Structure](#4-application-layer-structure)
5. [Infrastructure Layer Structure](#5-infrastructure-layer-structure)
6. [GUI Layer Structure](#6-gui-layer-structure)
7. [PDF Engine Package Structure](#7-pdf-engine-package-structure)
8. [AI Module Structure](#8-ai-module-structure)
9. [Plugin System Structure](#9-plugin-system-structure)
10. [Integration Adapters Structure](#10-integration-adapters-structure)
11. [Backup Engine Structure](#11-backup-engine-structure)
12. [Audit System Structure](#12-audit-system-structure)
13. [Logging Structure](#13-logging-structure)
14. [Migration Structure](#14-migration-structure)
15. [Template System Structure](#15-template-system-structure)
16. [Config System Structure](#16-config-system-structure)
17. [Dependency Direction Rules](#17-dependency-direction-rules)
18. [Import Rules](#18-import-rules)
19. [Runtime Initialization Flow](#19-runtime-initialization-flow)
20. [Boot Sequence](#20-boot-sequence)
21. [Service Registration Flow](#21-service-registration-flow)
22. [Plugin Loading Flow](#22-plugin-loading-flow)
23. [File Storage Directory Structure](#23-file-storage-directory-structure)
24. [Archive Storage Structure](#24-archive-storage-structure)
25. [Backup Storage Structure](#25-backup-storage-structure)
26. [Temp Directory Rules](#26-temp-directory-rules)
27. [Portable Mode Structure](#27-portable-mode-structure)
28. [Windows Executable Structure](#28-windows-executable-structure)
29. [Testing Structure](#29-testing-structure)
30. [Future Expansion Strategy](#30-future-expansion-strategy)

---

## 1. Final Package Structure

### 1.1 Repository Root

```
  oglg/                                    # Git repository root
  ├── main.py                              # Application entry point
  ├── pyproject.toml                       # Project metadata, dependencies, tool config
  ├── requirements.txt                     # Pinned dependencies for reproducible builds
  ├── README.md                            # Project overview
  ├── .gitignore                           # Git ignore rules (see 1.2)
  │
  ├── app/                                 # Application package (Python package)
  │   ├── __init__.py
  │   ├── core/                            # DOMAIN LAYER
  │   ├── services/                        # APPLICATION LAYER
  │   ├── database/                        # INFRASTRUCTURE — persistence
  │   ├── pdf/                             # INFRASTRUCTURE — PDF generation
  │   ├── ai/                              # INFRASTRUCTURE — local AI
  │   ├── gui/                             # PRESENTATION — PySide6
  │   ├── plugins/                         # PLUGIN SYSTEM
  │   ├── config/                          # CONFIGURATION
  │   ├── utils/                           # CROSS-CUTTING UTILITIES
  │   └── assets/                          # STATIC RESOURCES
  │
  ├── tests/                               # Test suite
  │   ├── unit/                            # Pure unit tests (no infra)
  │   ├── integration/                     # Integration tests (DB, PDF, AI)
  │   ├── e2e/                             # End-to-end GUI tests
  │   └── fixtures/                        # Test data and helpers
  │
  ├── docs/                                # Documentation
  ├── scripts/                             # Build and utility scripts
  └── venv/                                # Virtual environment (git-ignored)
```

### 1.2 `.gitignore`

```
  # Python
  __pycache__/
  *.py[cod]
  *.egg-info/
  dist/
  build/

  # Virtual environment
  venv/
  .venv/

  # IDE
  .vscode/
  .idea/
  *.swp
  *.swo

  # Runtime data (user-specific, not committed)
  app/database/*.db
  app/backups/
  app/logs/
  app/generated_letters/
  app/temp/
  app/archives/

  # OS files
  Thumbs.db
  .DS_Store

  # PyInstaller output
  *.spec
  dist/

  # Logs
  *.log
```

---

## 2. Layer Boundaries

### 2.1 Layer Map

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    PACKAGE LAYER BOUNDARIES                          │
  │                                                                     │
  │  ┌──────────────────────────────────────────────────────────────┐   │
  │  │  app/gui/       PRESENTATION LAYER                            │   │
  │  │  (PySide6 windows, widgets, dialogs, view models)            │   │
  │  │  Depends on: services/ (application layer only)               │   │
  │  │  NEVER depends on: database/, pdf/, ai/ (directly)           │   │
  │  └──────────────────────────┬───────────────────────────────────┘   │
  │                             │                                       │
  │                             ▼                                       │
  │  ┌──────────────────────────────────────────────────────────────┐   │
  │  │  app/services/   APPLICATION LAYER                            │   │
  │  │  (use case orchestration, DTO mapping, transaction coord.)   │   │
  │  │  Depends on: core/ (entities, repository interfaces)          │   │
  │  │  Depends on: config/ (settings)                               │   │
  │  │  NEVER depends on: gui/, database/ (directly), pdf/, ai/     │   │
  │  └──────────────────────────┬───────────────────────────────────┘   │
  │                             │                                       │
  │                             ▼                                       │
  │  ┌──────────────────────────────────────────────────────────────┐   │
  │  │  app/core/        DOMAIN LAYER                                │   │
  │  │  (entities, value objects, repository interfaces,            │   │
  │  │   domain services, domain exceptions)                        │   │
  │  │  Depends on: NOTHING (pure Python stdlib only)               │   │
  │  └──────────────────────────────────────────────────────────────┘   │
  │                             ▲                                       │
  │                             │                                       │
  │  ┌──────────────────────────────────────────────────────────────┐   │
  │  │  INFRASTRUCTURE LAYER (implements domain interfaces)          │   │
  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │   │
  │  │  │database/ │  │   pdf/   │  │   ai/    │  │    utils/    │ │   │
  │  │  │(SQLite)  │  │(ReportLab│  │ (local)  │  │ (file I/O,   │ │   │
  │  │  │          │  │          │  │          │  │  logging)    │ │   │
  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │   │
  │  │  Depends on: core/ (repository interfaces, entities)          │   │
  │  └──────────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Boundary Rules

```
  RULE 1: Presentation depends on Application, never on Infrastructure
  RULE 2: Application depends on Domain, never on Infrastructure
  RULE 3: Domain depends on NOTHING (pure Python)
  RULE 4: Infrastructure depends on Domain (implements interfaces)
  RULE 5: Infrastructure NEVER depends on Presentation
  RULE 6: Infrastructure NEVER depends on Application
  RULE 7: Cross-layer communication uses DTOs, never ORM models
  RULE 8: Config is available to all layers EXCEPT Domain
```

---

## 3. Domain Layer Structure

### 3.1 Package Tree

```
  app/core/                              # DOMAIN LAYER — pure Python
  ├── __init__.py                        # Public API exports
  │
  ├── entities/                          # Business entities
  │   ├── __init__.py
  │   ├── letter.py                      # Letter aggregate root
  │   ├── user.py                        # User entity
  │   ├── department.py                  # Department entity
  │   ├── attachment.py                  # Attachment entity
  │   ├── archive_log.py                 # Archive log entry (append-only)
  │   ├── backup_log.py                  # Backup log entry (append-only)
  │   └── audit_entry.py                 # Audit entry (append-only)
  │
  ├── value_objects/                     # Immutable value objects
  │   ├── __init__.py
  │   ├── letter_number.py               # LetterNumber (prefix-year-seq)
  │   ├── document_id.py                 # DocumentId (UUID wrapper)
  │   ├── sha256_hash.py                 # SHA256Hash (hex string wrapper)
  │   ├── date_range.py                  # DateRange (start, end)
  │   ├── person_name.py                 # PersonName (first, father, last)
  │   ├── address.py                     # Address (city, district, detail)
  │   ├── email.py                       # Email (validated)
  │   ├── phone_number.py                # PhoneNumber (validated)
  │   └── template_version.py            # TemplateVersion (major, minor)
  │
  ├── repositories/                      # Repository interfaces (ports)
  │   ├── __init__.py
  │   ├── letter_repository.py           # LetterRepository interface
  │   ├── user_repository.py             # UserRepository interface
  │   ├── department_repository.py       # DepartmentRepository interface
  │   ├── attachment_repository.py       # AttachmentRepository interface
  │   ├── audit_repository.py            # AuditRepository interface
  │   ├── archive_repository.py          # ArchiveRepository interface
  │   └── backup_repository.py           # BackupRepository interface
  │
  ├── services/                          # Domain services (business rules)
  │   ├── __init__.py
  │   ├── letter_domain_service.py       # Letter validation, numbering rules
  │   ├── user_domain_service.py         # User validation, password policy
  │   └── archive_domain_service.py      # Archive immutability rules
  │
  ├── enums.py                           # All domain enums (Priority, Status, Role, etc.)
  │
  └── exceptions/                        # Domain-specific exceptions
      ├── __init__.py
      ├── base.py                        # Base domain exception
      ├── letter_exceptions.py           # LetterNotFound, InvalidLetterNumber, etc.
      ├── user_exceptions.py             # UserNotFound, AuthenticationFailed, etc.
      ├── archive_exceptions.py          # AlreadyArchived, ArchiveNotFound, etc.
      └── permission_exceptions.py       # InsufficientPermissions, etc.
```

### 3.2 Domain Layer Contract

```
  Import policy for app/core/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED (dataclasses, uuid, datetime, enum, abc, hashlib)
    third-party:          FORBIDDEN
    other app packages:   FORBIDDEN

  This is the only layer with zero external dependencies.
```

---

## 4. Application Layer Structure

### 4.1 Package Tree

```
  app/services/                          # APPLICATION LAYER — use case orchestration
  ├── __init__.py                        # Public API exports
  │
  ├── letter_service.py                  # Create, read, update, delete, search letters
  ├── user_service.py                    # Create, read, update, authenticate users
  ├── archive_service.py                 # Archive, restore, verify letters
  ├── backup_service.py                  # Create, restore, verify backups
  ├── audit_service.py                   # Log and query audit entries
  ├── search_service.py                  # Full-text search orchestration
  ├── report_service.py                  # Reporting and statistics
  │
  ├── dto/                               # Data Transfer Objects
  │   ├── __init__.py
  │   ├── letter_dto.py                  # CreateLetterDTO, UpdateLetterDTO, LetterDTO
  │   ├── user_dto.py                    # CreateUserDTO, UserDTO
  │   ├── archive_dto.py                 # ArchiveDTO
  │   ├── backup_dto.py                  # BackupDTO
  │   ├── audit_dto.py                   # AuditDTO
  │   ├── search_dto.py                  # SearchQuery, LetterFilters, PageResult
  │   └── attachment_dto.py             # AttachmentDTO
  │
  └── integration/                       # FUTURE INTEGRATION ADAPTERS (optional)
      ├── __init__.py
      ├── base_adapter.py                # Abstract integration adapter
      ├── gula_adapter.py                # Gula platform adapter (future)
      └── lab_adapter.py                 # Laboratory system adapter (future)
```

### 4.2 Application Layer Contract

```
  Import policy for app/services/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED
    app/core/:            ALLOWED (entities, repository interfaces, value objects)
    app/config/:          ALLOWED (settings)
    third-party:          FORBIDDEN (framework independence)

  Services receive repository implementations via dependency injection.
  Services NEVER import from app/database/, app/pdf/, app/ai/, app/gui/.
```

---

## 5. Infrastructure Layer Structure

### 5.1 Package Tree

```
  app/database/                          # INFRASTRUCTURE — Persistence
  ├── __init__.py
  ├── connection.py                      # SQLAlchemy engine, session factory, WAL config
  ├── models.py                          # SQLAlchemy ORM model definitions
  ├── repositories/                      # Repository implementations
  │   ├── __init__.py
  │   ├── sqlalchemy_letter_repo.py      # SQLAlchemyLetterRepository
  │   ├── sqlalchemy_user_repo.py        # SQLAlchemyUserRepository
  │   ├── sqlalchemy_department_repo.py  # SQLAlchemyDepartmentRepository
  │   ├── sqlalchemy_attachment_repo.py  # SQLAlchemyAttachmentRepository
  │   ├── sqlalchemy_audit_repo.py       # SQLAlchemyAuditRepository
  │   ├── sqlalchemy_archive_repo.py     # SQLAlchemyArchiveRepository
  │   └── sqlalchemy_backup_repo.py      # SQLAlchemyBackupRepository
  │
  └── migrations/                        # Alembic migration scripts
      ├── env.py                         # Alembic environment config
      ├── script.py.mako                 # Migration template
      └── versions/                      # Migration version scripts
          ├── 001_create_initial_tables.py
          ├── 002_add_letter_language.py
          └── ...
```

### 5.2 Infrastructure Layer Contract

```
  Import policy for app/database/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED
    app/core/:            ALLOWED (entities, repository interfaces)
    app/config/:          ALLOWED (settings)
    third-party:          ALLOWED (SQLAlchemy, Alembic)
    other infra:          ALLOWED (app/utils/ for logging)

  Repository classes implement interfaces defined in app/core/repositories/.
  ORM models are NEVER exposed outside app/database/.
```

---

## 6. GUI Layer Structure

### 6.1 Package Tree

```
  app/gui/                               # PRESENTATION — PySide6 interface
  ├── __init__.py
  ├── app.py                             # QApplication setup, style, locale
  ├── main_window.py                     # Main application window
  │
  ├── views/                             # Main application views
  │   ├── __init__.py
  │   ├── letter_list_view.py            # Letter list/table view
  │   ├── letter_editor_view.py          # Letter compose/edit view
  │   ├── archive_view.py                # Archive browser view
  │   ├── search_view.py                 # Search panel view
  │   ├── backup_view.py                 # Backup management view
  │   ├── settings_view.py               # Settings/preferences view
  │   ├── audit_view.py                  # Audit log viewer
  │   └── dashboard_view.py              # Main dashboard / summary
  │
  ├── dialogs/                           # Modal dialogs
  │   ├── __init__.py
  │   ├── confirm_dialog.py              # Generic confirmation dialog (Arabic)
  │   ├── error_dialog.py                # Error display dialog
  │   ├── about_dialog.py                # About system dialog
  │   ├── login_dialog.py                # User authentication dialog
  │   ├── archive_dialog.py              # Archive confirmation dialog
  │   └── backup_dialog.py               # Backup/restore dialog
  │
  ├── widgets/                           # Reusable custom widgets
  │   ├── __init__.py
  │   ├── rtl_text_edit.py               # RTL-aware text editor (Arabic)
  │   ├── letter_table.py                # Letter list table widget
  │   ├── status_bar.py                  # Status bar with connection state
  │   ├── search_bar.py                  # Search input widget
  │   ├── date_picker.py                 # Date selection widget (RTL)
  │   └── priority_indicator.py          # Priority color indicator
  │
  ├── view_models/                       # Qt Model/View architecture
  │   ├── __init__.py
  │   ├── letter_table_model.py          # QAbstractTableModel for letters
  │   ├── archive_table_model.py         # QAbstractTableModel for archives
  │   ├── audit_table_model.py           # QAbstractTableModel for audit logs
  │   └── backup_table_model.py          # QAbstractTableModel for backups
  │
  └── resources/                         # Qt resources (icons, styles)
      ├── resources.qrc                  # Qt resource file
      ├── styles/
      │   └── default.qss                # Application stylesheet
      └── icons/                         # Icon files (or symlink to app/assets/icons)
```

### 6.2 GUI Layer Contract

```
  Import policy for app/gui/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED
    app/services/:        ALLOWED (service DTOs, service calls)
    app/config/:          ALLOWED (UI-related settings)
    app/core/entities/:   ALLOWED (read-only entity access for display)
    third-party:          ALLOWED (PySide6 only)

  GUI NEVER imports from app/database/, app/pdf/, app/ai/ directly.
  GUI calls services, services orchestrate infrastructure.
```

---

## 7. PDF Engine Package Structure

### 7.1 Package Tree

```
  app/pdf/                               # INFRASTRUCTURE — PDF Generation
  ├── __init__.py
  ├── generator.py                       # PDFService entry point
  │                                      #   generate_letter_pdf(letter_dto) -> FilePath
  │                                      #   generate_archive_pdf(archive_dto) -> FilePath
  │
  ├── renderer.py                        # ReportLab rendering engine
  │                                      #   render_document(template, data) -> bytes
  │
  ├── fonts.py                           # Arabic font management and embedding
  │                                      #   register_arabic_fonts()
  │                                      #   get_font_path(name)
  │
  ├── templates/                         # Programmatic PDF templates
  │   ├── __init__.py
  │   ├── base_template.py               # Base template class (header, footer, margins)
  │   ├── official_letter.py             # Official government letter template
  │   ├── memo.py                        # Internal memo template
  │   ├── external_letter.py             # External ministry letter template
  │   └── archive_copy.py                # Archived document template with watermark
  │
  └── utils.py                           # PDF utility functions
                                          #   draw_rtl_text(canvas, text, x, y)
                                          #   draw_table(canvas, headers, rows)
                                          #   add_watermark(canvas, text)
```

### 7.2 PDF Package Contract

```
  Import policy for app/pdf/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED
    app/core/:            ALLOWED (entities, value objects)
    app/config/:          ALLOWED (PDF settings, defaults)
    app/utils/:           ALLOWED (file_utils, logger)
    third-party:          ALLOWED (ReportLab only)
    app/assets/:          ALLOWED (fonts, logo images)

  PDF package is called by services layer.
  PDF package NEVER depends on app/gui/ or app/database/.
```

---

## 8. AI Module Structure

### 8.1 Package Tree

```
  app/ai/                                # INFRASTRUCTURE — Local AI Assistant
  ├── __init__.py
  ├── engine.py                          # AI service entry point
  │                                      #   check_text(text, language) -> AISuggestions
  │
  ├── pipeline.py                        # Text processing pipeline orchestrator
  │                                      #   run_pipeline(text) -> PipelineResult
  │                                      #   (spell -> grammar -> colloquial -> wording
  │                                      #    -> formatting)
  │
  ├── spell_checker.py                   # Arabic spell checker
  │                                      #   check(text) -> list[SpellError]
  │
  ├── grammar_checker.py                 # Arabic grammar rule engine
  │                                      #   check(text) -> list[GrammarError]
  │
  ├── colloquial_detector.py             # Colloquial Arabic detection
  │                                      #   detect(text) -> list[ColloquialMatch]
  │
  ├── wording_engine.py                  # Formal wording suggestions
  │                                      #   suggest(text) -> list[WordingSuggestion]
  │
  ├── formatter.py                       # Formatting improvement suggestions
  │                                      #   suggest(text) -> list[FormatSuggestion]
  │
  ├── models/                            # Local model data (not Python code)
  │   ├── arabic_dict.dat                # Arabic word dictionary
  │   ├── grammar_rules.json             # Grammar rule definitions
  │   └── colloquial_keywords.json       # Colloquial word list
  │
  └── types.py                           # AI-specific types and DTOs
                                          #   SpellError, GrammarError, AISuggestion, etc.
```

### 8.2 AI Package Contract

```
  Import policy for app/ai/:
    ─────────────────────────────────────────────
    stdlib:               ALLOWED
    app/core/:            ALLOWED (value objects)
    app/config/:          ALLOWED (AI settings)
    app/utils/:           ALLOWED (logger)
    third-party:          FORBIDDEN (no external AI APIs)

  All AI models and data are local files within app/ai/models/.
  AI runs in a background QThread, never blocking the GUI.
```

---

## 9. Plugin System Structure

### 9.1 Package Tree

```
  app/plugins/                           # PLUGIN SYSTEM
  ├── __init__.py
  ├── registry.py                        # Plugin registry
  │                                      #   register(plugin)
  │                                      #   get(name) -> PluginInterface
  │                                      #   get_all() -> list[PluginInterface]
  │                                      #   get_hooks(event) -> list[PluginInterface]
  │
  ├── interface.py                       # Plugin base class
  │                                      #   class PluginInterface(ABC):
  │                                      #       name, version, author
  │                                      #       activate(), deactivate(), execute()
  │
  ├── loader.py                          # Safe plugin loader
  │                                      #   load_plugins(directory) -> list[PluginInterface]
  │                                      #   validate_manifest(path) -> bool
  │                                      #   load_single(path) -> PluginInterface
  │
  ├── hooks.py                           # Hook definitions
  │                                      #   on_letter_created, on_letter_archived
  │                                      #   on_backup_created, on_startup, on_shutdown
  │
  ├── manifest.py                        # Plugin manifest model
  │                                      #   name, version, author, hooks, deps
  │
  └── installed/                         # Installed plugin directories
      ├── __init__.py                    # (runtime-created per plugin)
      └── example_plugin/                # Example plugin structure
          ├── manifest.json
          ├── __init__.py
          └── main.py
```

### 9.2 Plugin Isolation

```
  Plugin loading isolation:
    - Each plugin runs in its own namespace
    - Plugin code is loaded from app/plugins/installed/{name}/
    - Manifest declares hooks, dependencies, min app version
    - Plugin execution wrapped in try/except — failure NEVER crashes app
    - Plugins access core entities and services through public API only
    - Plugin registry tracks active/inactive state in database
```

---

## 10. Integration Adapters Structure

### 10.1 Package Tree

```
  app/services/integration/              # INTEGRATION ADAPTERS (optional, future)
  ├── __init__.py
  ├── base_adapter.py                    # Abstract base adapter
  │                                      #   send_letter(dto) -> IntegrationResult
  │                                      #   receive_documents(since) -> list[dict]
  │                                      #   health_check() -> bool
  │                                      #   initialize(config) -> bool
  │                                      #   shutdown()
  │
  ├── gula_adapter.py                    # Gula platform integration (future)
  │                                      #   Maps LetterDTO to Gula FHIR format
  │                                      #   REST or local network transport
  │
  ├── lab_adapter.py                     # Laboratory system integration (future)
  │                                      #   Maps LetterDTO to lab order format
  │                                      #   Bidirectional sync for test results
  │
  ├── ministry_adapter.py                # Government archiving integration (future)
  │
  ├── registry.py                        # Integration adapter registry
  │                                      #   register(target_name, adapter_class)
  │                                      #   get(target_name) -> IntegrationAdapter
  │                                      #   get_active() -> list[IntegrationAdapter]
  │
  └── types.py                           # Integration-specific types
                                          #   IntegrationResult, SyncStatus, TargetConfig
```

### 10.2 Integration Contract

```
  Integration design rules:
    1. Core system has ZERO knowledge of integration adapters
    2. Adapters communicate through IntegrationService (app/services/)
    3. Integration failures NEVER affect core operations
    4. Each adapter is independently configurable via integration_config table
    5. Integration is always OPTIONAL and OFF by default
    6. Adapters run in background threads, never blocking UI
```

---

## 11. Backup Engine Structure

### 11.1 Package Tree

```
  app/services/backup_service.py         # BACKUP SERVICE (application layer)
                                          #   create_backup(type, user_id) -> BackupDTO
                                          #   restore_backup(id, user_id)
                                          #   list_backups() -> PageResult
                                          #   verify_backup(id) -> bool
                                          #   delete_backup(id)
                                          #
                                          # Internal helpers:
                                          #   _acquire_db_lock()
                                          #   _copy_database(dest)
                                          #   _create_zip(sources, dest)
                                          #   _compute_hash(path)
                                          #   _enforce_retention()
                                          #   _safety_backup()

  app/backups/                           # Backup output directory (runtime)
                                          #   backup-2026-05-28-120000-AUTO.zip
                                          #   backup-2026-05-28-150000-MANUAL.zip
```

### 11.2 Backup Design

```
  BackupService is in the application layer because:
    - It orchestrates multiple infrastructure concerns (database, filesystem, config)
    - It coordinates transaction safety (WAL checkpoint)
    - It enforces business rules (retention policy, pre-restore safety backup)
    - It calls AuditService for logging

  Backup file storage is on the filesystem (app/backups/) but abstracted
  behind a FileStorage interface for future replaceability.
```

---

## 12. Audit System Structure

### 12.1 Package Tree

```
  app/services/audit_service.py          # AUDIT SERVICE (application layer)
                                          #   log(action, entity_type, entity_id,
                                          #       user_id, details, result) -> AuditEntry
                                          #   query(filters, page, size) -> PageResult
                                          #   export(filters, format) -> FilePath
                                          #   get_entity_history(type, id) -> list
                                          #   get_user_activity(user_id, range) -> list
                                          #
                                          # Internal:
                                          #   _validate_entry(entry)
                                          #   _serialize_details(dict) -> str
                                          #   _write_log_file(entry)

  app/core/entities/audit_entry.py       # AuditEntry domain entity
  app/core/repositories/audit_repository.py  # AuditRepository interface
  app/database/repositories/sqlalchemy_audit_repo.py  # SQLAlchemy implementation
```

### 12.2 Audit Design

```
  Audit is a cross-cutting concern:
    - Audit entry creation goes through AuditService (application layer)
    - Audit persistence goes through AuditRepository (infrastructure)
    - Audit log files are written by app/utils/logger.py (loguru)

  This separates concerns:
    Service layer: decides WHAT to audit
    Domain layer: defines WHAT an audit entry IS
    Infrastructure: decides WHERE/HOW to store audit data
```

---

## 13. Logging Structure

### 13.1 Package Tree

```
  app/utils/logger.py                    # Logging configuration
                                          #   configure_logging(log_dir, level)
                                          #   get_logger(name) -> Logger
                                          #   set_context(user_id, session_id)
                                          #
                                          # Provides pre-configured loggers:
                                          #   app_logger        — general app events
                                          #   db_logger         — database queries
                                          #   security_logger   — auth/security events
                                          #   audit_logger      — audit trail
                                          #   pdf_logger        — PDF generation
                                          #   ai_logger         — AI operations
                                          #   backup_logger     — backup/restore
                                          #   error_logger      — errors/exceptions

  app/logs/                              # Log output directory (runtime)
                                          #   correspondence.log
                                          #   correspondence.log.1
                                          #   correspondence.log.2.gz
                                          #   ...
```

### 13.2 Logging Architecture

```
  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
  │  Application  │ ──> │   app/utils/     │ ──> │  Rotating File   │
  │  Code         │     │   logger.py      │     │  (app/logs/)     │
  │              │     │  (loguru)        │     │                  │
  │  Services    │     │                  │     │  + Console       │
  │  GUI         │     │  JSON format     │     │  (debug mode)    │
  │  Infra       │     │  Structured      │     │                  │
  └──────────────┘     └──────────────────┘     └──────────────────┘
                                │
                                │ (also)
                                ▼
                       ┌──────────────────┐
                       │  AuditService    │
                       │  (database       │
                       │   audit_logs)    │
                       └──────────────────┘
```

---

## 14. Migration Structure

### 14.1 Package Tree

```
  app/database/migrations/               # Alembic migration scripts
  ├── env.py                             # Alembic environment configuration
  │                                      #   target_metadata = SQLAlchemy models
  │                                      #   run_migrations_online()
  │                                      #   run_migrations_offline()
  │
  ├── script.py.mako                     # Migration script template
  │                                      #   revision, down_revision
  │                                      #   upgrade(), downgrade()
  │
  ├── alembic.ini                        # Alembic configuration
  │                                      #   sqlalchemy.url = sqlite:///...
  │                                      #   script_location = app/database/migrations
  │
  └── versions/                          # Migration version scripts
      ├── 001_create_initial_tables.py
      ├── 002_add_letter_language.py
      ├── 003_add_attachment_hash.py
      └── ...
```

### 14.2 Migration Lifecycle

```
  ┌──────────────────────┐
  │  Developer creates   │
  │  or auto-generates   │
  │  migration script    │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  Migration script    │
  │  tested (+downgrade) │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  Script committed    │
  │  to version control  │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────────────────────┐
  │  Application startup:                │
  │  1. Check alembic_version table      │
  │  2. Compare with latest migration    │
  │  3. If mismatch:                     │
  │     a. Pre-migration backup          │
  │     b. Run alembic upgrade head      │
  │     c. Verify database integrity     │
  │     d. Log migration result          │
  │  4. If failure: rollback, log, alert │
  └──────────────────────────────────────┘
```

---

## 15. Template System Structure

### 15.1 Package Tree

```
  app/pdf/templates/                     # PDF programmatic templates
  ├── __init__.py
  ├── base_template.py                   # Abstract base template
  │                                      #   draw_header(), draw_footer()
  │                                      #   set_margins(), set_fonts()
  │                                      #   render(data) -> bytes
  │
  ├── official_letter.py                 # Ministry official letter template
  ├── memo.py                            # Internal memo template
  ├── external_letter.py                 # External correspondence template
  └── archive_copy.py                    # Archived letter with watermark

  app/assets/templates/                  # Static template resources
  └── (empty — currently templates are programmatic)

  app/database/models.py                 # Templates table stores JSON template definitions
                                          # (not the Python programmatic templates above)

  Note: Two types of "templates" exist:
    1. Programmatic Python templates (app/pdf/templates/) — control PDF layout
    2. JSON template definitions (database templates table) — configurable field layout
    They complement each other: Python templates use JSON definitions for layout parameters.
```

---

## 16. Config System Structure

### 16.1 Package Tree

```
  app/config/                            # CONFIGURATION SYSTEM
  ├── __init__.py
  ├── settings.py                        # Settings manager
  │                                      #   load() -> Settings
  │                                      #   save(settings)
  │                                      #   get(key) -> value
  │                                      #   set(key, value)
  │                                      #   reset_to_defaults()
  │                                      #
  │                                      # Settings dataclass:
  │                                      #   database_path: Path
  │                                      #   archive_path: Path
  │                                      #   backup_path: Path
  │                                      #   log_level: str
  │                                      #   language: str
  │                                      #   theme: str
  │                                      #   auto_backup_enabled: bool
  │                                      #   auto_backup_interval_days: int
  │                                      #   backup_retention_days: int
  │                                      #   pdf_dpi: int
  │                                      #   font_paths: dict[str, str]
  │                                      #   ...
  │
  ├── defaults.json                      # Factory default configuration
  │                                      #   (bundled in executable)
  │
  └── user_config.json                   # User override configuration
                                          #   (in user data directory, runtime)
```

### 16.2 Config Loading Order

```
  1. defaults.json (bundled)      — base defaults
  2. user_config.json (user data) — user overrides (overrides defaults)
  3. Database system_config table — runtime overrides (overrides both)
  4. CLI arguments                — session overrides (overrides all)

  Precedence: CLI > database > user_config.json > defaults.json
```

---

## 17. Dependency Direction Rules

### 17.1 Complete Dependency Matrix

```
  PACKAGE         IMPORTS FROM                                   IMPORTED BY
  ─────────────────────────────────────────────────────────────────────────────────
  core/           stdlib only                                    services/, database/, pdf/,
                                                                 ai/, gui/, plugins/, config/,
                                                                 utils/
  services/       core/, config/                                 gui/, plugins/
  database/       core/, config/, utils/                         (called by services via DI)
  pdf/            core/, config/, utils/, assets/                (called by services via DI)
  ai/             core/, config/, utils/                         (called by services via DI)
  gui/            services/, config/, core/ (entities, read)     (nothing — outermost)
  plugins/        core/, config/, services/                      (loaded by app startup)
  config/         utils/                                         (everyone except core/)
  utils/          stdlib only                                    (everyone)
  assets/         (static data — no imports)                     pdf/, gui/
```

### 17.2 Strict Forbidden Imports

```
  ✗ gui/          importing database/, pdf/, ai/ directly
  ✗ services/     importing database/, pdf/, ai/ directly
  ✗ services/     importing gui/
  ✗ database/     importing gui/, services/
  ✗ pdf/          importing gui/, services/, database/
  ✗ ai/           importing gui/, services/, database/
  ✗ core/         importing ANYTHING outside stdlib
  ✗ plugins/      importing gui/, database/, pdf/, ai/
```

### 17.3 Dependency Inversion Diagram

```
  ┌────────────┐
  │   core/    │  <──  defines interfaces (ports)
  └─────┬──────┘
        │
        │ implements
        ▼
  ┌────────────┐  <──  injected into services
  │ database/  │
  │ pdf/       │
  │ ai/        │
  └────────────┘
        │
        │ injected by
        ▼
  ┌────────────┐
  │ services/  │  <──  uses interfaces, not implementations
  └─────┬──────┘
        │
        │ called by
        ▼
  ┌────────────┐
  │   gui/     │
  └────────────┘
```

### 17.4 Dependency Injection Wiring

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    DEPENDENCY INJECTION                          │
  │                                                                 │
  │  Application startup (main.py):                                 │
  │                                                                 │
  │  1. Create infrastructure instances:                            │
  │     engine = create_db_engine(config.database_path)             │
  │     letter_repo = SQLAlchemyLetterRepository(engine)            │
  │     user_repo = SQLAlchemyUserRepository(engine)                │
  │     audit_repo = SQLAlchemyAuditRepository(engine)              │
  │     pdf_engine = ReportLabPDFEngine(config)                     │
  │     ai_engine = LocalAIEngine(config)                           │
  │                                                                 │
  │  2. Create services with injected dependencies:                 │
  │     letter_service = LetterService(                              │
  │         letter_repo=letter_repo,                                │
  │         audit_repo=audit_repo,                                  │
  │         pdf_engine=pdf_engine,                                  │
  │     )                                                            │
  │     audit_service = AuditService(audit_repo=audit_repo)         │
  │     archive_service = ArchiveService(                            │
  │         letter_repo=letter_repo,                                 │
  │         archive_repo=archive_repo,                               │
  │         audit_service=audit_service,                             │
  │     )                                                            │
  │                                                                 │
  │  3. Create GUI with injected services:                          │
  │     window = MainWindow(                                         │
  │         letter_service=letter_service,                          │
  │         audit_service=audit_service,                            │
  │         archive_service=archive_service,                        │
  │     )                                                            │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 18. Import Rules

### 18.1 Absolute Import Convention

```python
  # ALWAYS use absolute imports within the app package
  from app.core.entities.letter import Letter
  from app.core.repositories.letter_repository import LetterRepository
  from app.services.dto.letter_dto import LetterDTO
  from app.services.letter_service import LetterService

  # NEVER use relative imports
  # from ..core.entities.letter import Letter  ✗
  # from .letter_repository import ...        ✗
```

### 18.2 `__init__.py` Export Policy

```python
  # Each __init__.py exports ONLY what is part of the public API:

  # app/core/__init__.py
  from app.core.entities.letter import Letter
  from app.core.entities.user import User
  from app.core.value_objects.letter_number import LetterNumber
  from app.core.enums import Priority, LetterStatus, UserRole

  __all__ = [
      "Letter", "User",
      "LetterNumber",
      "Priority", "LetterStatus", "UserRole",
  ]
```

### 18.3 Circular Import Prevention

```
  Rules to prevent circular imports:
    1. Domain layer (app/core/) imports NOTHING from other app packages
    2. Repository interfaces are in app/core/repositories/
    3. Repository implementations are in app/database/repositories/
    4. ORM models are in app/database/models.py (separate from domain entities)
    5. Service classes are in app/services/, NOT app/core/services/
    6. DTOs are in app/services/dto/, NOT in app/core/
    7. Domain services (app/core/services/) contain business rules only
    8. Use TYPE_CHECKING for type annotations that would cause circular imports
```

### 18.4 Third-Party Import Isolation

```python
  # Third-party imports are confined to infrastructure packages.
  # They are NEVER exposed to domain or application layers.

  # ALLOWED in app/database/repositories/sqlalchemy_letter_repo.py:
  from sqlalchemy import select, update
  from sqlalchemy.orm import Session

  # FORBIDDEN in app/services/letter_service.py:
  # from sqlalchemy import select   ✗
```

---

## 19. Runtime Initialization Flow

### 19.1 Initialization Sequence

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    INITIALIZATION SEQUENCE                       │
  │                                                                 │
  │  main()                                                         │
  │    │                                                            │
  │    ├── 1. Parse CLI arguments                                    │
  │    │                                                             │
  │    ├── 2. Configure logging (app/utils/logger.py)                │
  │    │      - Initialize loguru                                    │
  │    │      - Set log level from config/CLI                       │
  │    │      - Start rotating file handler                         │
  │    │                                                             │
  │    ├── 3. Load configuration (app/config/settings.py)            │
  │    │      - Load defaults.json                                   │
  │    │      - Load user_config.json (if exists)                   │
  │    │      - Load database overrides (system_config table)       │
  │    │      - Apply CLI overrides                                  │
  │    │                                                             │
  │    ├── 4. Determine data directory                               │
  │    │      - Check for portable mode (data/ next to exe)         │
  │    │      - Fall back to %APPDATA%/oglg/                        │
  │    │      - Create directory structure if missing                │
  │    │                                                             │
  │    ├── 5. Initialize database (app/database/connection.py)       │
  │    │      - Create SQLAlchemy engine                             │
  │    │      - Apply WAL pragmas                                    │
  │    │      - Configure session factory                            │
  │    │                                                             │
  │    ├── 6. Run pending migrations (Alembic)                       │
  │    │      - Compare schema version                               │
  │    │      - Create pre-migration backup                         │
  │    │      - Execute upgrade                                      │
  │    │      - On failure: rollback, log, exit                     │
  │    │                                                             │
  │    ├── 7. Check crash recovery                                   │
  │    │      - Check for unclean shutdown marker                    │
  │    │      - If found: run integrity_check                       │
  │    │      - If corrupt: alert user, offer backup restore        │
  │    │                                                             │
  │    ├── 8. Create infrastructure instances                        │
  │    │      - Repository implementations                           │
  │    │      - PDF engine                                           │
  │    │      - AI engine                                            │
  │    │                                                             │
  │    ├── 9. Create service instances (with DI)                     │
  │    │      - LetterService, UserService, AuditService, etc.       │
  │    │                                                             │
  │    ├── 10. Load plugins (app/plugins/loader.py)                  │
  │    │      - Scan installed/ directory                            │
  │    │      - Validate manifests                                   │
  │    │      - Activate plugins                                     │
  │    │                                                             │
  │    ├── 11. Create main window (app/gui/app.py)                   │
  │    │      - QApplication setup                                   │
  │    │      - Load stylesheet                                      │
  │    │      - Create MainWindow with injected services            │
  │    │      - Restore window state                                 │
  │    │                                                             │
  │    ├── 12. Check daily auto-backup                               │
  │    │      - Check if backup is due                               │
  │    │      - If yes: run in background thread                     │
  │    │                                                             │
  │    └── 13. Enter Qt event loop                                   │
  │           - app.exec()                                           │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 20. Boot Sequence

### 20.1 `main.py` Entry Point

```python
  """
  main.py — Application entry point.

  Boot sequence:
    1. CLI arg parsing
    2. Logging setup
    3. Config loading
    4. Data directory detection
    5. Database init + migrations
    6. Crash recovery check
    7. Infrastructure init
    8. Service init (DI)
    9. Plugin loading
    10. GUI init
    11. Qt event loop
  """

  def main() -> None:
      # Phase 1: Bootstrap (no dependencies)
      cli_args = parse_cli_args()
      configure_logging(cli_args.log_level)
      config = load_config(cli_args.config_path)

      # Phase 2: Infrastructure
      data_dir = resolve_data_directory(cli_args.portable)
      ensure_directory_structure(data_dir)

      engine = create_database_engine(data_dir / "database" / "correspondence.db")
      run_migrations(engine)
      check_crash_recovery(engine)

      # Phase 3: Dependency injection
      repos = create_repositories(engine)
      pdf_engine = create_pdf_engine(config)
      ai_engine = create_ai_engine(config)

      services = create_services(repos, pdf_engine, ai_engine, config)

      # Phase 4: Plugins
      plugin_registry = load_plugins(services)

      # Phase 5: GUI
      app = create_qt_app(config)
      window = MainWindow(services, plugin_registry)

      # Phase 6: Run
      check_auto_backup(services.backup_service)
      sys.exit(app.exec())

  if __name__ == "__main__":
      main()
```

### 20.2 CLI Arguments

```
  oglg.exe [OPTIONS]

  --portable         Run in portable mode (data dir next to executable)
  --config PATH      Path to custom config file
  --log-level LVL    Log level (DEBUG, INFO, WARNING, ERROR)
  --data-dir PATH    Explicit data directory path
  --reset-config     Reset configuration to defaults
  --version          Show version and exit
  --help             Show help and exit

  CLI-only commands (non-interactive):
  oglg.exe --migrate         Run database migrations only
  oglg.exe --backup          Create backup from CLI
  oglg.exe --restore PATH    Restore backup from CLI
  oglg.exe --verify-db       Verify database integrity
  oglg.exe --export-audit    Export audit log to CSV
```

---

## 21. Service Registration Flow

### 21.1 Service Factory Pattern

```python
  # app/__init__.py or app/bootstrap.py

  @dataclass
  class Services:
      letter_service: LetterService
      user_service: UserService
      archive_service: ArchiveService
      backup_service: BackupService
      audit_service: AuditService
      search_service: SearchService
      report_service: ReportService

  def create_services(
      repos: Repositories,
      pdf_engine: PDFEngine,
      ai_engine: AIEngine,
      config: Settings,
  ) -> Services:
      # Audit service first (other services depend on it)
      audit_service = AuditService(repos.audit_repo)

      # Domain services
      letter_domain = LetterDomainService()

      # Application services
      letter_service = LetterService(
          letter_repo=repos.letter_repo,
          attachment_repo=repos.attachment_repo,
          audit_service=audit_service,
          pdf_engine=pdf_engine,
          letter_domain=letter_domain,
      )

      user_service = UserService(
          user_repo=repos.user_repo,
          audit_service=audit_service,
      )

      archive_service = ArchiveService(
          letter_repo=repos.letter_repo,
          archive_repo=repos.archive_repo,
          audit_service=audit_service,
          pdf_engine=pdf_engine,
      )

      backup_service = BackupService(
          backup_repo=repos.backup_repo,
          audit_service=audit_service,
          config=config,
      )

      search_service = SearchService(
          letter_repo=repos.letter_repo,
      )

      report_service = ReportService(
          letter_repo=repos.letter_repo,
      )

      return Services(
          letter_service=letter_service,
          user_service=user_service,
          archive_service=archive_service,
          backup_service=backup_service,
          audit_service=audit_service,
          search_service=search_service,
          report_service=report_service,
      )
```

### 21.2 Service Registration Diagram

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    SERVICE REGISTRATION                          │
  │                                                                 │
  │  create_repositories(engine)                                     │
  │    ├── SQLAlchemyLetterRepository(engine)                        │
  │    ├── SQLAlchemyUserRepository(engine)                          │
  │    ├── SQLAlchemyDepartmentRepository(engine)                    │
  │    ├── SQLAlchemyAttachmentRepository(engine)                    │
  │    ├── SQLAlchemyAuditRepository(engine)                         │
  │    ├── SQLAlchemyArchiveRepository(engine)                       │
  │    └── SQLAlchemyBackupRepository(engine)                        │
  │         │                                                        │
  │         ▼                                                        │
  │  create_services(repos, pdf_engine, ai_engine, config)           │
  │    │    (order matters — audit first)                            │
  │    ├── AuditService(audit_repo)                                  │
  │    ├── LetterService(letter_repo, attachment_repo,               │
  │    │                 audit_service, pdf_engine, letter_domain)   │
  │    ├── UserService(user_repo, audit_service)                     │
  │    ├── ArchiveService(letter_repo, archive_repo,                 │
  │    │                 audit_service, pdf_engine)                  │
  │    ├── BackupService(backup_repo, audit_service, config)         │
  │    ├── SearchService(letter_repo)                                │
  │    └── ReportService(letter_repo)                                │
  │         │                                                        │
  │         ▼                                                        │
  │  MainWindow(services, plugin_registry)                           │
  │    │    (GUI receives all services via a single Services object) │
  │    └── Each view uses only the services it needs                 │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 22. Plugin Loading Flow

### 22.1 Plugin Loading Sequence

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    PLUGIN LOADING SEQUENCE                       │
  │                                                                 │
  │  load_plugins(services)                                         │
  │    │                                                            │
  │    ├── 1. Scan app/plugins/installed/ directory                 │
  │    │      - List subdirectories                                  │
  │    │      - Skip hidden dirs (starting with _ or .)              │
  │    │                                                             │
  │    ├── 2. For each plugin directory:                            │
  │    │                                                            │
  │    │    ├── 2a. Read manifest.json                               │
  │    │    │      - Validate required fields (name, version, hooks) │
  │    │    │      - Validate min_app_version                       │
  │    │    │      - If invalid: log warning, skip plugin           │
  │    │    │                                                       │
  │    │    ├── 2b. Check plugin is enabled in database              │
  │    │    │      - Query plugins table for name                   │
  │    │    │      - If not enabled and not registered: skip         │
  │    │    │                                                       │
  │    │    ├── 2c. Import plugin module                             │
  │    │    │      - Use importlib.import_module()                   │
  │    │    │      - Wrap in try/except                             │
  │    │    │      - On import error: log, disable, continue         │
  │    │    │                                                       │
  │    │    ├── 2d. Instantiate plugin class                         │
  │    │    │      - Verify it implements PluginInterface            │
  │    │    │      - Wrap in try/except                             │
  │    │    │                                                       │
  │    │    ├── 2e. Register with PluginRegistry                     │
  │    │    │      - Register hooks (on_letter_created, etc.)        │
  │    │    │                                                       │
  │    │    └── 2f. Call plugin.activate()                          │
  │    │           - Wrap in try/except                             │
  │    │           - On failure: log, disable, continue              │
  │    │                                                             │
  │    └── 3. Return PluginRegistry with all loaded plugins          │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘
```

### 22.2 Plugin Hook Execution

```
  When a service method triggers a hook:

  letter_service.create_letter(dto)
      │
      ├── 1. Execute business logic (save to DB, etc.)
      │
      ├── 2. After successful save:
      │      registry.execute_hooks("on_letter_created", letter_dto)
      │      │
      │      │   for plugin in registry.get_hooks("on_letter_created"):
      │      │       try:
      │      │           plugin.on_letter_created(letter_dto)
      │      │       except Exception as e:
      │      │           logger.error(f"Plugin {plugin.name} failed: {e}")
      │      │           # Plugin failure NEVER blocks the main flow
      │      │
      ├── 3. Log audit
      └── 4. Return DTO
```

---

## 23. File Storage Directory Structure

### 23.1 Runtime Data Directory

```
  Data Directory (resolved at startup):
  ┌────────────────────────────────────────────────────────────┐
  │  Portable mode:  <exe_dir>/data/                           │
  │  Installed mode: %APPDATA%/oglg/  (Windows)                │
  │                   ~/.local/share/oglg/  (Linux)            │
  └────────────────────────────────────────────────────────────┘

  Data Directory Contents:
  ├── database/
  │   └── correspondence.db              # SQLite database file
  │
  ├── archives/                          # Archived letters (immutable)
  │   ├── index.json                     # Archive index (fast lookup)
  │   └── {year}/
  │       └── {month}/
  │           ├── {number}.json          # Letter metadata JSON
  │           └── {number}.pdf           # Letter PDF
  │
  ├── backups/                           # Backup ZIP files
  │   ├── backup-2026-05-28-120000-AUTO.zip
  │   ├── backup-2026-05-28-150000-MANUAL.zip
  │   └── ...
  │
  ├── generated_letters/                 # Generated PDF output
  │   ├── {number}.pdf                    # Generated letter PDFs
  │   └── ...
  │
  ├── attachments/                       # Letter attachment files
  │   └── {letter_id}/
  │       ├── {attachment_id}-{filename}
  │       └── ...
  │
  ├── logs/                              # Rotating log files
  │   ├── correspondence.log
  │   ├── correspondence.log.1
  │   └── ...
  │
  ├── temp/                              # Temporary files (cleared on startup)
  │   └── ...
  │
  └── user_config.json                   # User configuration overrides
```

### 23.2 Directory Creation on Startup

```python
  def ensure_directory_structure(data_dir: Path) -> None:
      """Create required runtime directories if they don't exist."""
      directories = [
          data_dir / "database",
          data_dir / "archives",
          data_dir / "backups",
          data_dir / "generated_letters",
          data_dir / "attachments",
          data_dir / "logs",
          data_dir / "temp",
      ]
      for directory in directories:
          directory.mkdir(parents=True, exist_ok=True)
```

---

## 24. Archive Storage Structure

### 24.1 Archive Directory Layout

```
  archives/
  ├── index.json                         # Master archive index
  │                                      #   Maps letter numbers to file paths
  │                                      #   Contains: number, id, path, hash, date
  │                                      #
  ├── 2026/                              # Year directory
  │   ├── 01/                            # Month directory (zero-padded)
  │   │   ├── MOH-2026-0001.json         # Archived letter metadata
  │   │   ├── MOH-2026-0001.pdf          # Archived letter PDF
  │   │   ├── MOH-2026-0002.json
  │   │   ├── MOH-2026-0002.pdf
  │   │   └── ...
  │   ├── 02/
  │   ├── 03/
  │   ├── 04/
  │   ├── 05/
  │   ├── 06/
  │   ├── 07/
  │   ├── 08/
  │   ├── 09/
  │   ├── 10/
  │   ├── 11/
  │   └── 12/
  │
  ├── 2027/
  │   └── ...
  │
  └── (year/month partitioning continues)
```

### 24.2 Archive Index Format

```json
{
  "version": 1,
  "last_updated": "2026-05-28T12:00:00",
  "letters": {
    "MOH-2026-0001": {
      "id": "3a1b2c3d-4e5f-6789-0abc-def012345678",
      "subject": "طلب تخصيص ميزانية إضافية",
      "archived_at": "2026-05-28T12:00:00",
      "json_path": "2026/05/MOH-2026-0001.json",
      "pdf_path": "2026/05/MOH-2026-0001.pdf",
      "content_hash": "abc123...",
      "pdf_hash": "def456...",
      "size_bytes": 204800
    }
  }
}
```

### 24.3 Archive Index Strategy

```
  - index.json is rebuilt on every archive operation
  - Written atomically (tmp + rename)
  - Used for fast lookup without scanning filesystem
  - Rebuildable by scanning archive directory (recovery)
  - Backward compatible: older app versions skip unknown fields
```

---

## 25. Backup Storage Structure

### 25.1 Backup Directory Layout

```
  backups/
  ├── backup-2026-05-28-120000-AUTO.zip
  ├── backup-2026-05-28-150000-MANUAL.zip
  ├── backup-2026-05-29-000000-MANUAL.zip
  ├── backup-2026-06-01-080000-PRE_MIGRATION.zip
  ├── backup-2026-06-01-080100-AUTO.zip
  └── ...
```

### 25.2 Backup ZIP Contents

```
  backup-2026-05-28-120000-AUTO.zip
  ├── correspondence.db                  # SQLite database (compressed)
  ├── config.json                        # Application configuration
  ├── archive_index.json                 # Archive index reference
  ├── manifest.json                      # Backup metadata
  └── integrity.sha256                   # Verification hashes
```

### 25.3 Backup Retention

```
  Retention policy enforced on every backup creation:

  Type            Retention        Logic
  ──────────────────────────────────────────────────────────
  AUTO            30 days          Created >= 30 days ago
  MANUAL          Forever          Kept until user deletes
  PRE_MIGRATION   Forever          Kept until user deletes
```

---

## 26. Temp Directory Rules

### 26.1 Temp Directory Location

```
  Path: <data_dir>/temp/

  Purpose:
    - Intermediate file writes before atomic rename
    - Temporary export files
    - Background processing artifacts
```

### 26.2 Temp File Lifecycle

```
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Create .tmp  │ ──> │  Write full  │ ──> │  Atomic      │
  │  file         │     │  content     │     │  rename to   │
  │               │     │              │     │  target      │
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                                     ┌─────────────┴─────────────┐
                                     │                           │
                                     ▼                           ▼
                               ┌──────────────┐          ┌──────────────┐
                               │  Success:    │          │  Crash:      │
                               │  .tmp deleted│          │  .tmp orphan │
                               └──────────────┘          └──────┬───────┘
                                                                 │
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │  Startup scans   │
                                                        │  temp/ for .tmp  │
                                                        │  files, recovers │
                                                        │  or deletes      │
                                                        └──────────────────┘
```

### 26.3 Temp Directory Cleanup

```
  Cleanup rules:
    1. All .tmp files older than 24 hours: DELETE
    2. .tmp files with matching target and matching content: RENAME
    3. .tmp files with matching target and mismatched content: LOG WARNING, DELETE
    4. Orphan .tmp files (no matching target): DELETE
    5. Empty subdirectories: REMOVE
    6. All operations logged
```

---

## 27. Portable Mode Structure

### 27.1 Portable Mode Detection

```
  Portable mode activates when:
    - User passes --portable flag
    - OR oglg.exe is run from a removable drive
    - OR oglg.exe is in a directory containing a portable.txt marker file

  Data directory: <exe_dir>/data/ (relative to executable)
```

### 27.2 Portable Mode Layout

```
  <USB drive or portable folder>/
  ├── oglg.exe                         # Application executable
  ├── _internal/                       # PyInstaller runtime files
  │   ├── Python/
  │   ├── Lib/
  │   └── ...
  │
  ├── data/                            # All user data (portable)
  │   ├── database/
  │   │   └── correspondence.db
  │   ├── archives/
  │   ├── backups/
  │   ├── generated_letters/
  │   ├── attachments/
  │   ├── logs/
  │   ├── temp/
  │   └── user_config.json
  │
  └── portable.txt                     # Marker file (optional)
```

### 27.3 Portable Mode vs Installed Mode

```
  Aspect               Portable                    Installed
  ─────────────────────────────────────────────────────────────────
  Data location         <exe_dir>/data/             %APPDATA%/oglg/
  Multiple users        One data per exe copy       Per-user data
  USB drive             Yes                         No
  Admin required        No                          For install only
  Registry              None                        None (both modes)
  Config file           data/user_config.json       %APPDATA%/config.json
  Performance           Same                        Same
```

---

## 28. Windows Executable Structure

### 28.1 PyInstaller Build Output

```
  dist/oglg/                             # Single-folder build (recommended)
  ├── oglg.exe                          # Application entry point
  ├── oglg-cli.exe                      # CLI utilities (migrate, backup, restore)
  │
  ├── _internal/                        # PyInstaller bootloader + bundled runtime
  │   ├── app/                          # Application Python code
  │   │   ├── core/
  │   │   ├── services/
  │   │   ├── database/
  │   │   ├── pdf/
  │   │   ├── ai/
  │   │   ├── gui/
  │   │   ├── plugins/
  │   │   ├── config/
  │   │   └── utils/
  │   │
  │   ├── assets/                       # Bundled static resources
  │   │   ├── fonts/
  │   │   ├── icons/
  │   │   └── templates/
  │   │
  │   ├── config/
  │   │   └── defaults.json
  │   │
  │   └── (Python DLLs, standard library, third-party packages)
  │
  ├── Qt/                               # PySide6 Qt libraries
  ├── platform/                         # Qt platform plugins
  ├── iconengines/                      # Qt image format plugins
  │
  ├── portable.txt                      # Optional marker for portable mode
  └── (DLLs: sqlite3, openssl, etc.)
```

### 28.2 Build Configuration (PyInstaller `.spec`)

```python
  # oglg.spec
  a = Analysis(
      ['main.py'],
      pathex=[],
      binaries=[],
      datas=[
          ('app/assets', 'assets'),
          ('app/config/defaults.json', 'config'),
          ('app/ai/models', 'ai/models'),
          ('app/plugins/installed', 'plugins/installed'),
      ],
      hiddenimports=[
          'app.core',
          'app.services',
          'app.database',
          'app.pdf',
          'app.ai',
          'app.gui',
          'app.plugins',
          'app.config',
          'app.utils',
          # SQLAlchemy dialects (sqlite)
          'sqlalchemy.dialects.sqlite',
          # Alembic
          'alembic',
      ],
      hookspath=[],
      runtime_hooks=[],
      excludes=[
          'tkinter', 'matplotlib', 'PIL', 'numpy', 'pandas',
          'cryptography', 'OpenSSL',
      ],
      win_no_prefer_redirects=False,
      win_private_assemblies=False,
      cipher=None,
      noarchive=False,
  )

  pyz = PYZ(a.pure, a.zipped_data, cipher=None)

  exe = EXE(
      pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
      [],
      name='oglg',
      debug=False,
      bootloader_ignore_signals=False,
      strip=False,
      upx=True,
      upx_exclude=[],
      runtime_tmpdir=None,
      console=False,                   # No console window
      disable_windowed_traceback=False,
      argv_emulation=False,
      target_arch=None,
      codesign_identity=None,
      entitlements_file=None,
      icon='app/assets/icons/app.ico',
  )

  # CLI tool (console mode)
  exe_cli = EXE(
      pyz, ['cli_main.py'], a.binaries, a.zipfiles, a.datas,
      [],
      name='oglg-cli',
      debug=False,
      bootloader_ignore_signals=False,
      strip=False,
      upx=True,
      console=True,                    # Console window for CLI
      icon='app/assets/icons/cli.ico',
  )
```

---

## 29. Testing Structure

### 29.1 Test Suite Layout

```
  tests/
  ├── __init__.py
  │
  ├── unit/                             # Pure unit tests (fast, no infra)
  │   ├── __init__.py
  │   │
  │   ├── core/                         # Domain layer tests
  │   │   ├── __init__.py
  │   │   ├── test_letter_entity.py
  │   │   ├── test_letter_number.py
  │   │   ├── test_user_entity.py
  │   │   ├── test_department_entity.py
  │   │   ├── test_value_objects.py
  │   │   ├── test_enums.py
  │   │   └── test_domain_services.py
  │   │
  │   ├── services/                     # Application layer tests (mocked repos)
  │   │   ├── __init__.py
  │   │   ├── test_letter_service.py
  │   │   ├── test_user_service.py
  │   │   ├── test_archive_service.py
  │   │   ├── test_backup_service.py
  │   │   ├── test_audit_service.py
  │   │   └── test_search_service.py
  │   │
  │   └── dto/                          # DTO tests
  │       ├── __init__.py
  │       └── test_dto_serialization.py
  │
  ├── integration/                      # Integration tests (real infra)
  │   ├── __init__.py
  │   │
  │   ├── database/                     # Database integration tests
  │   │   ├── __init__.py
  │   │   ├── conftest.py               # SQLite in-memory engine fixture
  │   │   ├── test_sqlalchemy_letter_repo.py
  │   │   ├── test_sqlalchemy_user_repo.py
  │   │   ├── test_sqlalchemy_audit_repo.py
  │   │   ├── test_migrations.py
  │   │   └── test_fts5_search.py
  │   │
  │   ├── pdf/                          # PDF generation tests
  │   │   ├── __init__.py
  │   │   ├── conftest.py               # ReportLab fixtures
  │   │   ├── test_pdf_generator.py
  │   │   ├── test_rtl_rendering.py
  │   │   └── test_template_rendering.py
  │   │
  │   ├── ai/                           # AI module tests
  │   │   ├── __init__.py
  │   │   ├── conftest.py
  │   │   ├── test_spell_checker.py
  │   │   ├── test_grammar_checker.py
  │   │   └── test_pipeline.py
  │   │
  │   ├── filesystem/                   # File I/O integration tests
  │   │   ├── __init__.py
  │   │   ├── test_atomic_writes.py
  │   │   └── test_archive_storage.py
  │   │
  │   └── backup/                       # Backup/restore tests
  │       ├── __init__.py
  │       ├── test_backup_create.py
  │       └── test_backup_restore.py
  │
  ├── e2e/                              # End-to-end tests (full stack)
  │   ├── __init__.py
  │   ├── conftest.py                   # Full application bootstrap
  │   ├── test_create_letter_flow.py
  │   ├── test_archive_flow.py
  │   ├── test_search_flow.py
  │   └── test_backup_restore_flow.py
  │
  └── fixtures/                         # Shared test data and helpers
      ├── __init__.py
      ├── factories.py                  # Entity factories (LetterFactory, UserFactory)
      ├── mock_repositories.py          # In-memory mock implementations
      ├── sample_data.py               # Sample letter data for tests
      └── conftest.py                   # Global pytest fixtures
```

### 29.2 Test Configuration

```ini
  # pytest.ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = -v --tb=short --strict-markers

  markers =
      unit: Unit tests (no infrastructure)
      integration: Integration tests (real infrastructure)
      e2e: End-to-end tests
      slow: Slow tests (mark to skip by default)
      db: Database tests
      pdf: PDF generation tests
      ai: AI module tests
```

### 29.3 Test Naming Convention

```
  Test files:    test_{module_name}.py
  Test classes:  Test{Feature}
  Test methods:  test_{scenario}_{expected_behavior}

  Examples:
    test_letter_service.py:
      class TestCreateLetter:
          def test_valid_data_creates_letter_successfully(self): ...
          def test_duplicate_number_raises_error(self): ...
          def test_archived_letter_cannot_be_edited(self): ...

    test_sqlalchemy_letter_repo.py:
      class TestFindById:
          def test_existing_id_returns_letter(self): ...
          def test_nonexistent_id_returns_none(self): ...
```

### 29.4 Mock Repository Pattern

```python
  # tests/fixtures/mock_repositories.py

  class MockLetterRepository(LetterRepository):
      """In-memory mock for unit tests."""

      def __init__(self):
          self._letters: dict[UUID, Letter] = {}

      def find_by_id(self, id: LetterId) -> Letter | None:
          return self._letters.get(id)

      def save(self, letter: Letter) -> Letter:
          self._letters[letter.id] = letter
          return letter
      # ... remaining methods
```

### 29.5 Factory Pattern for Tests

```python
  # tests/fixtures/factories.py

  class LetterFactory:
      """Creates test Letter instances with sensible defaults."""

      @staticmethod
      def create(**overrides) -> Letter:
          defaults = {
              "id": uuid.uuid4(),
              "number": "MOH-2026-0001",
              "subject": "Test Subject",
              "body": "Test body content",
              "sender_name": "د. علي أحمد",
              "recipient_name": "وزارة الصحة",
              "department_id": uuid.uuid4(),
              "priority": Priority.NORMAL,
              "status": LetterStatus.DRAFT,
              "created_by_id": uuid.uuid4(),
              "created_at": datetime.now(),
              "content_hash": "abc123",
          }
          defaults.update(overrides)
          return Letter(**defaults)
```

---

## 30. Future Expansion Strategy

### 30.1 Expansion Directions

```
  Priority  Direction                    Package Impact         Isolation
  ──────────────────────────────────────────────────────────────────────────
  HIGH      Gula platform integration    app/services/integration/  FULL
  HIGH      Laboratory system            app/services/integration/  FULL
  MEDIUM    QR/Barcode generation        app/pdf/templates/        MODULE
  MEDIUM    Advanced reporting           app/services/report_service.py  MODULE
  MEDIUM    LAN deployment               app/services/network/     FULL
  LOW       Multi-language support       app/core/value_objects/  MODULE
  LOW       Digital signatures           app/pdf/                  MODULE
  LOW       Document templates UI        app/gui/views/            MODULE
```

### 30.2 Expansion Rules

```
  1. New features MUST be added as isolated modules
  2. Core business logic (app/core/) MUST NOT change for new features
  3. Existing service interfaces MUST remain backward compatible
  4. New packages MUST follow the same layer rules (Section 17)
  5. New features MUST be optional — core operation unaffected
  6. Integration adapters MUST use the base_adapter interface
  7. Plugin system is the preferred extension mechanism for third-party features
```

### 30.3 Package Growth Tolerance

```
  The package structure is designed to scale to:

    - 50+ entity types (currently 7)
    - 30+ repository interfaces (currently 7)
    - 20+ application services (currently 7)
    - 20+ GUI views (currently 8)
    - 10+ integration adapters (currently 2 planned)
    - 100+ plugin packages

  This is achieved by:
    - Each package is a flat directory — no deep nesting
    - Each file has a single, clear responsibility
    - Naming conventions remain consistent at any scale
    - No circular dependencies possible if import rules are followed
    - Test structure mirrors source structure exactly
```

### 30.4 Deprecation Strategy

```
  1. Deprecated features are marked with a deprecation warning (logged)
  2. Deprecated features remain functional for 2 major versions
  3. Removal is documented in migration guides
  4. Old packages are moved to app/_deprecated/ before removal
  5. Major version bump signals breaking changes only
```

---

## Appendix A: Complete File Count Estimate

```
  Package         Files (approx)   Purpose
  ────────────────────────────────────────────────────────
  app/core/       25               Entities, VOs, repos, services, exceptions
  app/services/   15               Services, DTOs, integration
  app/database/   15               Connection, models, repos, migrations
  app/pdf/        10               Generator, renderer, fonts, templates
  app/ai/         12               Engine, pipeline, checkers, models
  app/gui/        30               Views, dialogs, widgets, view models
  app/plugins/    6                Registry, interface, loader, hooks
  app/config/     3                Settings, defaults
  app/utils/      5                Logger, file_utils, validators, helpers
  tests/          60+              Unit, integration, e2e, fixtures
  docs/           20+              Governance, architecture, database, api, modules
  scripts/        2                Build scripts (bat, sh)

  Total:          ~200 files       Production codebase
```

## Appendix B: Key File Patterns

```
  Pattern                      Convention
  ──────────────────────────────────────────────────────
  Entity file                  app/core/entities/{snake_name}.py
  Value object                 app/core/value_objects/{snake_name}.py
  Repository interface         app/core/repositories/{snake_name}_repository.py
  Repository impl              app/database/repositories/sqlalchemy_{snake_name}_repo.py
  Service                      app/services/{snake_name}_service.py
  DTO                          app/services/dto/{snake_name}_dto.py
  GUI view                     app/gui/views/{snake_name}_view.py
  GUI dialog                   app/gui/dialogs/{snake_name}_dialog.py
  GUI widget                   app/gui/widgets/{snake_name}.py
  GUI view model               app/gui/view_models/{snake_name}_model.py
  PDF template                 app/pdf/templates/{snake_name}.py
  AI checker                   app/ai/{snake_name}_checker.py
  Integration adapter          app/services/integration/{name}_adapter.py
  Migration script             app/database/migrations/versions/{rev}_{desc}.py
  Test (unit)                  tests/unit/{layer}/test_{module}.py
  Test (integration)           tests/integration/{layer}/test_{module}.py
  Test fixtures                tests/fixtures/{name}.py
```

## Appendix C: Reserved Package Names

```
  The following names are reserved for future system expansion
  and MUST NOT be used by plugins or third-party modules:

  app/core/          — Domain layer (reserved, exclusive)
  app/services/      — Application layer (reserved, exclusive)
  app/database/      — Persistence infrastructure (reserved)
  app/pdf/           — PDF infrastructure (reserved)
  app/ai/            — AI infrastructure (reserved)
  app/gui/           — Presentation layer (reserved, exclusive)
  app/plugins/       — Plugin system (reserved for core plugin manager)
  app/config/        — Configuration (reserved)
  app/utils/         — Cross-cutting utilities (reserved)
```

---

*This project structure document is a living artifact. All significant structural changes must be reflected here and approved through the governance process. Every new module or package must be consistent with the layer boundaries and import rules defined herein.*
