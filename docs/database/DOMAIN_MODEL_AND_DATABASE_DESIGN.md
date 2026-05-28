# Domain Model and Database Design

**Project**: Iraqi Government Offline Official Correspondence System
**Version**: 1.0 (Design Document)
**Last Updated**: 2026-05-28

---

## Table of Contents

1. [Core Domain Entities](#1-core-domain-entities)
2. [Value Objects](#2-value-objects)
3. [Aggregate Boundaries](#3-aggregate-boundaries)
4. [Repository Contracts](#4-repository-contracts)
5. [Service Contracts](#5-service-contracts)
6. [DTO Contracts](#6-dto-contracts)
7. [Database Schema Design](#7-database-schema-design)
8. [SQLite Table Definitions](#8-sqlite-table-definitions)
9. [FTS5 Search Architecture](#9-fts5-search-architecture)
10. [Audit Log Schema](#10-audit-log-schema)
11. [Backup Metadata Schema](#11-backup-metadata-schema)
12. [PDF Archive Schema](#12-pdf-archive-schema)
13. [File Integrity Schema](#13-file-integrity-schema)
14. [User and RBAC Schema](#14-user-and-rbac-schema)
15. [Template Schema](#15-template-schema)
16. [Plugin Registry Schema](#16-plugin-registry-schema)
17. [Integration Contract Schema](#17-integration-contract-schema)
18. [Migration Strategy](#18-migration-strategy)
19. [Versioning Strategy](#19-versioning-strategy)
20. [Soft Delete Strategy](#20-soft-delete-strategy)
21. [Immutable Archive Strategy](#21-immutable-archive-strategy)
22. [Transaction Safety Strategy](#22-transaction-safety-strategy)
23. [Atomic Write Strategy](#23-atomic-write-strategy)
24. [Data Retention Strategy](#24-data-retention-strategy)
25. [Search Indexing Strategy](#25-search-indexing-strategy)
26. [Performance Indexing Strategy](#26-performance-indexing-strategy)
27. [Foreign Key Policy](#27-foreign-key-policy)
28. [UUID Strategy](#28-uuid-strategy)
29. [File Storage Contracts](#29-file-storage-contracts)
30. [Future Integration Mapping Strategy](#30-future-integration-mapping-strategy)

---

## 1. Core Domain Entities

### 1.1 Entity Map

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                        DOMAIN ENTITIES                              │
  │                                                                     │
  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
  │  │    Letter    │    │     User     │    │    Department        │  │
  │  │  (Aggregate  │    │              │    │                      │  │
  │  │   Root)      │    │              │    │                      │  │
  │  └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
  │         │                  │                        │              │
  │         │  has many        │  belongs to            │              │
  │         ▼                  ▼                        │              │
  │  ┌──────────────┐    ┌──────────────┐               │              │
  │  │  Attachment  │    │  AuditEntry  │               │              │
  │  │              │    │  (append-    │               │              │
  │  │              │    │   only)      │               │              │
  │  └──────────────┘    └──────────────┘               │              │
  │                                                      │              │
  │  ┌──────────────┐    ┌──────────────┐               │              │
  │  │   ArchiveLog │    │   BackupLog  │               │              │
  │  │  (append-    │    │  (append-    │               │              │
  │  │   only)      │    │   only)      │               │              │
  │  └──────────────┘    └──────────────┘               │              │
  │                                                      │              │
  │  ┌──────────────┐    ┌──────────────┐    ┌──────────┴───────────┐  │
  │  │   Template   │    │    Plugin    │    │  IntegrationConfig  │  │
  │  │              │    │   Manifest   │    │  (future Gula/Lab)  │  │
  │  └──────────────┘    └──────────────┘    └────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Letter Entity

The `Letter` is the central aggregate root. It represents an official government correspondence document.

```
  ┌─────────────────────────────────────────────┐
  │                 Letter                       │
  │                                             │
  │  id              : LetterId     (UUID)      │
  │  number          : LetterNumber (value obj) │
  │  subject         : str                      │
  │  body            : str                      │
  │  sender_name     : str                      │
  │  sender_title    : str                      │
  │  recipient_name  : str                      │
  │  recipient_title : str                      │
  │  recipient_dept  : str                      │
  │  department_id   : DepartmentId  (UUID)     │
  │  priority        : Priority     (enum)      │
  │  status          : LetterStatus (enum)      │
  │  reference_number: str | None               │
  │  language        : LanguageTag  (ar/ar-en)  │
  │                                             │
  │  -- Metadata                                │
  │  created_by_id   : UserId       (UUID)      │
  │  created_at      : datetime                 │
  │  updated_by_id   : UserId | None (UUID)     │
  │  updated_at      : datetime | None          │
  │                                             │
  │  -- Archive state                           │
  │  is_archived     : bool                     │
  │  archived_at     : datetime | None          │
  │  archived_by_id  : UserId | None (UUID)     │
  │                                             │
  │  -- Integrity                               │
  │  content_hash   : SHA256Hash (str)          │
  │  version        : int                       │
  │                                             │
  │  -- Soft delete                             │
  │  is_deleted     : bool                      │
  │  deleted_at     : datetime | None           │
  │  deleted_by_id  : UserId | None (UUID)      │
  └─────────────────────────────────────────────┘
```

**Business Rules**:
- `number` is unique within a given year
- `content_hash` is SHA-256 of canonical JSON representation at time of creation
- Once `is_archived=true`, only `restore` operation may change `is_archived`
- `is_deleted=true` is a soft delete — record is hidden but never removed
- `version` increments on every update

### 1.3 User Entity

```
  ┌─────────────────────────────────────────────┐
  │                  User                        │
  │                                             │
  │  id              : UserId       (UUID)      │
  │  username        : str          (unique)    │
  │  full_name       : str                      │
  │  title           : str                      │
  │  email           : str | None               │
  │  password_hash   : str                      │
  │  role            : UserRole    (enum)       │
  │  department_id   : DepartmentId | None      │
  │  is_active       : bool                     │
  │  last_login_at   : datetime | None          │
  │  created_at      : datetime                 │
  │  updated_at      : datetime                 │
  └─────────────────────────────────────────────┘
```

**Business Rules**:
- `password_hash` uses bcrypt
- Only `Admin` role can create/modify users
- `is_active=false` prevents login but preserves audit trail

### 1.4 Department Entity

```
  ┌─────────────────────────────────────────────┐
  │               Department                     │
  │                                             │
  │  id              : DepartmentId (UUID)      │
  │  name            : str          (unique)    │
  │  code            : str          (unique)    │
  │  parent_id       : DepartmentId | None      │
  │  is_active       : bool                     │
  │  created_at      : datetime                 │
  │  updated_at      : datetime                 │
  └─────────────────────────────────────────────┘
```

**Business Rules**:
- `parent_id` enables hierarchical department tree
- `code` is a short alphanumeric code for official letter numbering

### 1.5 Attachment Entity

```
  ┌─────────────────────────────────────────────┐
  │              Attachment                      │
  │                                             │
  │  id              : AttachmentId (UUID)      │
  │  letter_id       : LetterId     (UUID)      │
  │  filename        : str                      │
  │  original_name   : str                      │
  │  file_path       : str                      │
  │  mime_type       : str                      │
  │  size_bytes      : int                      │
  │  hash_sha256     : str                      │
  │  created_at      : datetime                 │
  └─────────────────────────────────────────────┘
```

**Business Rules**:
- `original_name` is the user's filename; `filename` is the storage-safe name
- `hash_sha256` verified on every read
- Attachment files are immutable after creation

### 1.6 ArchiveLog Entity (Append-Only)

```
  ┌─────────────────────────────────────────────┐
  │               ArchiveLog                     │
  │                                             │
  │  id              : ArchiveLogId  (UUID)     │
  │  letter_id       : LetterId      (UUID)     │
  │  archived_by_id  : UserId        (UUID)     │
  │  archived_at     : datetime                 │
  │  archive_path    : str                      │
  │  content_hash    : str         (SHA-256)    │
  │  file_size_bytes : int                      │
  │  restored_at     : datetime | None          │
  │  restored_by_id  : UserId | None            │
  └─────────────────────────────────────────────┘
```

**Business Rules**:
- Append-only: records are never modified or deleted
- `content_hash` is the SHA-256 of the archived letter state
- A letter may have multiple archive entries (re-archive after restore)

### 1.7 BackupLog Entity (Append-Only)

```
  ┌─────────────────────────────────────────────┐
  │                BackupLog                     │
  │                                             │
  │  id              : BackupLogId   (UUID)     │
  │  backup_path     : str                      │
  │  size_bytes      : int                      │
  │  hash_sha256     : str                      │
  │  type            : BackupType   (enum)      │
  │  created_by_id   : UserId       (UUID)      │
  │  created_at      : datetime                 │
  │  restored_at     : datetime | None          │
  │  restored_by_id  : UserId | None            │
  │  notes           : str | None               │
  └─────────────────────────────────────────────┘
```

### 1.8 AuditEntry Entity (Append-Only)

```
  ┌─────────────────────────────────────────────┐
  │               AuditEntry                     │
  │                                             │
  │  id              : AuditEntryId  (UUID)     │
  │  timestamp       : datetime                 │
  │  user_id         : UserId        (UUID)     │
  │  action          : str                      │
  │  entity_type     : str                      │
  │  entity_id       : str          (UUID str)  │
  │  details_json    : str          (JSON)      │
  │  ip_address      : str | None               │
  │  result          : str          (success/   │
  │                                  failure)   │
  └─────────────────────────────────────────────┘
```

---

## 2. Value Objects

Value objects are immutable, defined by their attributes, and have no identity.

```
  ┌─────────────────────────────────────────────┐
  │              VALUE OBJECTS                   │
  │                                             │
  │  LetterNumber                               │
  │  ├── prefix     : str    (e.g. "MOH")      │
  │  ├── year       : int    (e.g. 2026)       │
  │  └── sequence   : int    (e.g. 42)          │
  │  └── format()   -> "MOH-2026-0042"          │
  │                                             │
  │  DocumentId                                 │
  │  └── value      : UUID                      │
  │                                             │
  │  SHA256Hash                                 │
  │  └── value      : str    (64 hex chars)     │
  │                                             │
  │  DateRange                                   │
  │  ├── start_date : date                      │
  │  └── end_date   : date                      │
  │                                             │
  │  PersonName                                 │
  │  ├── first_name : str                       │
  │  ├── father_name: str                       │
  │  ├── last_name  : str                       │
  │  └── full()     -> formatted Arabic name    │
  │                                             │
  │  Address                                    │
  │  ├── city      : str                        │
  │  ├── district  : str | None                 │
  │  └── detail    : str | None                 │
  │                                             │
  │  Email                                      │
  │  └── value     : str  (validated)           │
  │                                             │
  │  PhoneNumber                                │
  │  └── value     : str  (validated)           │
  │                                             │
  │  TemplateVersion                             │
  │  ├── major     : int                        │
  │  └── minor     : int                        │
  └─────────────────────────────────────────────┘
```

### 2.1 LetterNumber Format

```
  Pattern:  {PREFIX}-{YEAR}-{SEQUENCE:04d}
  Example:  MOH-2026-0042

  Prefix:   3-5 character department/organization code
  Year:     4-digit Gregorian year
  Sequence: Zero-padded to 4 digits (supports 9999 letters/year)

  Parsing:  static LetterNumber.parse(str) -> LetterNumber
  Equality: based on prefix + year + sequence
```

### 2.2 Enum Definitions

```
  Priority:          LOW, NORMAL, HIGH, URGENT
  LetterStatus:      DRAFT, FINAL, SENT, ARCHIVED, CANCELLED
  UserRole:          ADMIN, EDITOR, VIEWER, AUDITOR
  BackupType:        AUTO, MANUAL, PRE_MIGRATION
  LanguageTag:       AR, AR_EN  (Arabic only, Arabic + English)
```

---

## 3. Aggregate Boundaries

### 3.1 Aggregate Diagram

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    AGGREGATE BOUNDARIES                      │
  │                                                             │
  │  ┌───────────────────────────────────────┐                  │
  │  │          LETTER AGGREGATE             │                  │
  │  │                                       │                  │
  │  │  Root:  Letter                        │                  │
  │  │  Owns:  Attachment[]                  │                  │
  │  │  Ref:   Department   (by ID)          │                  │
  │  │  Ref:   User         (by ID)          │                  │
  │  │  Ref:   ArchiveLog[] (by LetterId)    │                  │
  │  │                                       │                  │
  │  │  Invariants:                          │                  │
  │  │   - number unique within year         │                  │
  │  │   - content_hash immutable after      │                  │
  │  │     creation                          │                  │
  │  │   - archived letters are read-only    │                  │
  │  │   - soft-deleted letters hidden       │                  │
  │  └───────────────────────────────────────┘                  │
  │                                                             │
  │  ┌───────────────────────────────────────┐                  │
  │  │          USER AGGREGATE               │                  │
  │  │                                       │                  │
  │  │  Root:  User                          │                  │
  │  │  Ref:   Department   (by ID)          │                  │
  │  │                                       │                  │
  │  │  Invariants:                          │                  │
  │  │   - username unique                   │                  │
  │  │   - password_hash never returned      │                  │
  │  │   - deactivation preserves audit      │                  │
  │  └───────────────────────────────────────┘                  │
  │                                                             │
  │  ┌───────────────────────────────────────┐                  │
  │  │       DEPARTMENT AGGREGATE            │                  │
  │  │                                       │                  │
  │  │  Root:  Department                    │                  │
  │  │  Ref:   Department.parent_id (self)   │                  │
  │  │                                       │                  │
  │  │  Invariants:                          │                  │
  │  │   - name unique                       │                  │
  │  │   - code unique                       │                  │
  │  │   - no circular parent references     │                  │
  │  └───────────────────────────────────────┘                  │
  │                                                             │
  │  ┌───────────────────────────────────────┐                  │
  │  │     AUDIT / ARCHIVE / BACKUP          │                  │
  │  │     (Standalone Append-Only Logs)     │                  │
  │  │                                       │                  │
  │  │  These are NOT aggregates.             │                  │
  │  │  They are append-only event records    │                  │
  │  │  referenced by Letter/User aggregates. │                  │
  │  └───────────────────────────────────────┘                  │
  └─────────────────────────────────────────────────────────────┘
```

### 3.2 Aggregate Access Rules

```
  Aggregate      Accessed via              Modified via
  ──────────────────────────────────────────────────────────
  Letter         LetterRepository          LetterService only
  User           UserRepository            UserService only
  Department     DepartmentRepository      AdminService only

  AuditEntry     AuditRepository           INSERT only (append)
  ArchiveLog     ArchiveRepository         INSERT only (append)
  BackupLog      BackupRepository          INSERT only (append)
```

---

## 4. Repository Contracts

Repository interfaces live in the domain layer (`core/repositories/`). They define the contract that infrastructure implements.

### 4.1 LetterRepository (Interface)

```
  ┌─────────────────────────────────────────────────────────────┐
  │              LetterRepository (Interface)                    │
  │                                                             │
  │  -- Query methods                                           │
  │  find_by_id(id: LetterId) -> Letter | None                  │
  │  find_by_number(number: LetterNumber) -> Letter | None      │
  │                                                             │
  │  search(query: str, filters: LetterFilters,                 │
  │         page: int, size: int) -> PageResult[Letter]         │
  │                                                             │
  │  find_by_department(dept_id: DepartmentId,                  │
  │                     page: int, size: int) -> PageResult     │
  │                                                             │
  │  find_by_date_range(range: DateRange,                       │
  │                     page: int, size: int) -> PageResult     │
  │                                                             │
  │  find_by_status(status: LetterStatus,                       │
  │                 page: int, size: int) -> PageResult         │
  │                                                             │
  │  find_archived(page: int, size: int) -> PageResult          │
  │  find_deleted(page: int, size: int) -> PageResult           │
  │                                                             │
  │  count(filters: LetterFilters) -> int                       │
  │  exists(number: LetterNumber) -> bool                       │
  │                                                             │
  │  -- Command methods                                         │
  │  save(letter: Letter) -> Letter          (insert or update) │
  │  delete(letter: Letter) -> None          (soft delete)      │
  │  hard_delete(letter: Letter) -> None     (admin purge)      │
  │                                                             │
  │  -- Next sequence                                           │
  │  next_sequence_for_year(year: int) -> int                   │
  └─────────────────────────────────────────────────────────────┘
```

### 4.2 UserRepository (Interface)

```
  ┌─────────────────────────────────────────────────────────────┐
  │              UserRepository (Interface)                      │
  │                                                             │
  │  find_by_id(id: UserId) -> User | None                      │
  │  find_by_username(username: str) -> User | None             │
  │  find_all(page: int, size: int) -> PageResult[User]         │
  │  find_by_department(dept_id: DepartmentId) -> list[User]    │
  │  find_by_role(role: UserRole) -> list[User]                 │
  │  count() -> int                                             │
  │  save(user: User) -> User                                   │
  │  update_last_login(user_id: UserId) -> None                 │
  └─────────────────────────────────────────────────────────────┘
```

### 4.3 DepartmentRepository (Interface)

```
  ┌─────────────────────────────────────────────────────────────┐
  │           DepartmentRepository (Interface)                   │
  │                                                             │
  │  find_by_id(id: DepartmentId) -> Department | None          │
  │  find_by_code(code: str) -> Department | None              │
  │  find_all() -> list[Department]                             │
  │  find_root_departments() -> list[Department]                │
  │  find_children(parent_id: DepartmentId) -> list[Department] │
  │  save(department: Department) -> Department                 │
  │  delete(id: DepartmentId) -> None                           │
  └─────────────────────────────────────────────────────────────┘
```

### 4.4 AuditRepository (Interface — Append-Only)

```
  ┌─────────────────────────────────────────────────────────────┐
  │            AuditRepository (Interface)                       │
  │                                                             │
  │  -- Append-only: no update, no delete                        │
  │  append(entry: AuditEntry) -> AuditEntry                    │
  │                                                             │
  │  -- Query (read-only)                                        │
  │  find_by_id(id: AuditEntryId) -> AuditEntry | None          │
  │  find_by_user(user_id: UserId,                              │
  │               page: int, size: int) -> PageResult           │
  │                                                             │
  │  find_by_entity(entity_type: str, entity_id: str,           │
  │                page: int, size: int) -> PageResult          │
  │                                                             │
  │  find_by_action(action: str,                                │
  │                 page: int, size: int) -> PageResult         │
  │                                                             │
  │  find_by_date_range(range: DateRange,                       │
  │                     page: int, size: int) -> PageResult     │
  │                                                             │
  │  count(filters: AuditFilters) -> int                        │
  └─────────────────────────────────────────────────────────────┘
```

### 4.5 ArchiveRepository (Interface — Append-Only)

```
  ┌─────────────────────────────────────────────────────────────┐
  │           ArchiveRepository (Interface)                      │
  │                                                             │
  │  -- Append-only for archive creation                         │
  │  append(entry: ArchiveLog) -> ArchiveLog                    │
  │                                                             │
  │  -- Query                                                    │
  │  find_by_id(id: ArchiveLogId) -> ArchiveLog | None          │
  │  find_by_letter(letter_id: LetterId) -> list[ArchiveLog]    │
  │  find_latest_by_letter(letter_id: LetterId) -> ArchiveLog   │
  │  find_by_date_range(range: DateRange,                       │
  │                     page: int, size: int) -> PageResult     │
  │                                                             │
  │  -- Update restore metadata (only field that changes)        │
  │  mark_restored(id: ArchiveLogId, user_id: UserId) -> None   │
  └─────────────────────────────────────────────────────────────┘
```

### 4.6 BackupRepository (Interface — Append-Only)

```
  ┌─────────────────────────────────────────────────────────────┐
  │           BackupRepository (Interface)                       │
  │                                                             │
  │  append(entry: BackupLog) -> BackupLog                      │
  │                                                             │
  │  find_by_id(id: BackupLogId) -> BackupLog | None            │
  │  find_all(page: int, size: int) -> PageResult               │
  │  find_by_type(type: BackupType) -> list[BackupLog]          │
  │  find_latest() -> BackupLog | None                          │
  │  mark_restored(id: BackupLogId, user_id: UserId) -> None    │
  └─────────────────────────────────────────────────────────────┘
```

### 4.7 AttachmentRepository (Interface)

```
  ┌─────────────────────────────────────────────────────────────┐
  │          AttachmentRepository (Interface)                    │
  │                                                             │
  │  find_by_id(id: AttachmentId) -> Attachment | None          │
  │  find_by_letter(letter_id: LetterId) -> list[Attachment]    │
  │  save(attachment: Attachment) -> Attachment                 │
  │  delete(id: AttachmentId) -> None                            │
  │  delete_by_letter(letter_id: LetterId) -> int               │
  └─────────────────────────────────────────────────────────────┘
```

---

## 5. Service Contracts

### 5.1 LetterService

```
  ┌─────────────────────────────────────────────────────────────┐
  │                 LetterService                                │
  │                                                             │
  │  create_letter(dto: CreateLetterDTO) -> LetterDTO            │
  │    - Validates all fields                                    │
  │    - Assigns next letter number                             │
  │    - Computes content_hash                                   │
  │    - Persists letter                                         │
  │    - Generates initial PDF                                   │
  │    - Logs audit: "letter.created"                            │
  │    - Returns LetterDTO                                      │
  │                                                             │
  │  update_letter(dto: UpdateLetterDTO) -> LetterDTO            │
  │    - Validates letter is not archived                        │
  │    - Validates letter is not deleted                         │
  │    - Updates fields, increments version                     │
  │    - Re-computes content_hash                                │
  │    - Logs audit: "letter.updated" with changed fields        │
  │    - Returns LetterDTO                                      │
  │                                                             │
  │  get_letter(id: LetterId) -> LetterDTO                       │
  │    - Returns letter (including deleted if requested)         │
  │                                                             │
  │  delete_letter(id: LetterId, user_id: UserId) -> None        │
  │    - Soft delete (sets is_deleted, deleted_at, deleted_by)   │
  │    - Logs audit: "letter.deleted"                            │
  │                                                             │
  │  restore_letter(id: LetterId, user_id: UserId) -> None       │
  │    - Restores from soft delete                               │
  │    - Logs audit: "letter.restored"                           │
  │                                                             │
  │  hard_delete_letter(id: LetterId) -> None                    │
  │    - Admin only: permanently removes letter + attachments    │
  │    - Logs audit: "letter.hard_deleted"                       │
  │                                                             │
  │  search_letters(query: SearchQuery) -> PageResult[LetterDTO] │
  │    - Full-text search across subject, body, number          │
  │                                                             │
  │  get_letters_by_department(dept_id, page, size) -> PageResult│
  │  get_letters_by_date_range(range, page, size) -> PageResult  │
  │  get_letters_by_status(status, page, size) -> PageResult    │
  │  get_archived_letters(page, size) -> PageResult              │
  │  get_deleted_letters(page, size) -> PageResult               │
  └─────────────────────────────────────────────────────────────┘
```

### 5.2 ArchiveService

```
  ┌─────────────────────────────────────────────────────────────┐
  │                ArchiveService                                │
  │                                                             │
  │  archive_letter(letter_id: LetterId,                         │
  │                 user_id: UserId) -> ArchiveDTO               │
  │    - Validates letter exists and not already archived        │
  │    - Computes SHA-256 of current letter state                │
  │    - Writes immutable JSON + PDF to archive storage          │
  │    - Sets letter.is_archived = True                          │
  │    - Creates ArchiveLog entry (append-only)                  │
  │    - Logs audit: "letter.archived"                           │
  │    - Returns ArchiveDTO                                     │
  │                                                             │
  │  restore_archive(archive_id: ArchiveLogId,                   │
  │                  user_id: UserId) -> LetterDTO               │
  │    - Validates archive record exists                         │
  │    - Verifies content_hash integrity                         │
  │    - Restores letter from archived state                     │
  │    - Sets letter.is_archived = False                         │
  │    - Marks ArchiveLog with restored_at/restored_by           │
  │    - Creates new version of letter                           │
  │    - Logs audit: "letter.restored_from_archive"              │
  │    - Returns restored LetterDTO                              │
  │                                                             │
  │  get_archive_history(letter_id: LetterId) -> list[ArchiveDTO]│
  │  verify_archive_integrity(archive_id: ArchiveLogId) -> bool  │
  └─────────────────────────────────────────────────────────────┘
```

### 5.3 BackupService

```
  ┌─────────────────────────────────────────────────────────────┐
  │                BackupService                                 │
  │                                                             │
  │  create_backup(type: BackupType,                             │
  │               user_id: UserId) -> BackupDTO                  │
  │    - Validates no other backup is running                    │
  │    - Acquires database lock (WAL checkpoint)                 │
  │    - Copies database to temp                                │
  │    - Collects config + archive index                        │
  │    - Creates ZIP archive                                    │
  │    - Computes SHA-256 of backup file                         │
  │    - Writes backup to backup storage                        │
  │    - Appends BackupLog entry                                 │
  │    - Enforces retention policy (oldest removed)              │
  │    - Logs audit: "backup.created"                            │
  │    - Returns BackupDTO                                      │
  │                                                             │
  │  restore_backup(backup_id: BackupLogId,                      │
  │                 user_id: UserId) -> None                     │
  │    - Verifies backup file integrity (SHA-256)                │
  │    - Creates pre-restore safety backup                       │
  │    - Replaces database                                      │
  │    - Restores config                                         │
  │    - Marks BackupLog as restored                             │
  │    - Logs audit: "backup.restored"                           │
  │                                                             │
  │  list_backups(page, size) -> PageResult[BackupDTO]           │
  │  delete_backup(backup_id: BackupLogId) -> None               │
  │  verify_backup(backup_id: BackupLogId) -> bool               │
  └─────────────────────────────────────────────────────────────┘
```

### 5.4 AuditService

```
  ┌─────────────────────────────────────────────────────────────┐
  │                AuditService                                  │
  │                                                             │
  │  log(action: str, entity_type: str, entity_id: str,         │
  │       user_id: UserId, details: dict | None,                │
  │       result: str = "success") -> AuditEntry                 │
  │    - Creates AuditEntry with timestamp                      │
  │    - Appends via AuditRepository                            │
  │    - Also writes to rotating log file                       │
  │    - Returns AuditEntry                                     │
  │                                                             │
  │  query(filters: AuditFilters, page, size) -> PageResult      │
  │  export(filters: AuditFilters, format: str) -> FilePath      │
  │  get_entity_history(entity_type, entity_id) -> list[AuditDTO]│
  │  get_user_activity(user_id: UserId, range: DateRange)        │
  │                    -> list[AuditDTO]                         │
  └─────────────────────────────────────────────────────────────┘
```

### 5.5 UserService

```
  ┌─────────────────────────────────────────────────────────────┐
  │                UserService                                   │
  │                                                             │
  │  create_user(dto: CreateUserDTO) -> UserDTO                  │
  │  update_user(dto: UpdateUserDTO) -> UserDTO                  │
  │  deactivate_user(id: UserId) -> None                         │
  │  activate_user(id: UserId) -> None                           │
  │  authenticate(username: str, password: str) -> UserDTO       │
  │  change_password(id: UserId, old: str, new: str) -> None     │
  │  get_user(id: UserId) -> UserDTO                             │
  │  list_users(page, size) -> PageResult[UserDTO]               │
  └─────────────────────────────────────────────────────────────┘
```

---

## 6. DTO Contracts

DTOs are immutable data transfer objects used for service boundary communication. They carry NO business logic.

### 6.1 Letter DTOs

```
  ┌─────────────────────────────────────────────────────────────┐
  │  CreateLetterDTO                                            │
  │  ├── subject: str                                           │
  │  ├── body: str                                              │
  │  ├── sender_name: str                                       │
  │  ├── sender_title: str                                      │
  │  ├── recipient_name: str                                    │
  │  ├── recipient_title: str                                   │
  │  ├── recipient_dept: str                                    │
  │  ├── department_id: str          (UUID)                     │
  │  ├── priority: str               (enum)                     │
  │  ├── reference_number: str | None                           │
  │  ├── language: str               (enum)                     │
  │  └── created_by_id: str          (UUID)                     │
  │                                                             │
  │  UpdateLetterDTO                                            │
  │  ├── id: str                      (UUID)                    │
  │  ├── subject: str | None                                    │
  │  ├── body: str | None                                       │
  │  ├── sender_name: str | None                                │
  │  ├── sender_title: str | None                               │
  │  ├── recipient_name: str | None                             │
  │  ├── recipient_title: str | None                            │
  │  ├── recipient_dept: str | None                             │
  │  ├── priority: str | None                                   │
  │  ├── reference_number: str | None                           │
  │  ├── status: str | None                                     │
  │  └── updated_by_id: str          (UUID)                     │
  │                                                             │
  │  LetterDTO  (response)                                       │
  │  ├── id: str                      (UUID)                    │
  │  ├── number: str                  (formatted)               │
  │  ├── subject: str                                           │
  │  ├── body: str                                              │
  │  ├── sender_name: str                                       │
  │  ├── sender_title: str                                      │
  │  ├── recipient_name: str                                    │
  │  ├── recipient_title: str                                   │
  │  ├── recipient_dept: str                                    │
  │  ├── department_id: str          (UUID)                     │
  │  ├── department_name: str                                   │
  │  ├── priority: str                                          │
  │  ├── status: str                                            │
  │  ├── reference_number: str | None                           │
  │  ├── language: str                                          │
  │  ├── content_hash: str                                      │
  │  ├── version: int                                           │
  │  ├── created_by_id: str          (UUID)                     │
  │  ├── created_by_name: str                                   │
  │  ├── created_at: str              (ISO 8601)                │
  │  ├── updated_by_id: str | None                              │
  │  ├── updated_at: str | None                                 │
  │  ├── is_archived: bool                                      │
  │  ├── archived_at: str | None                                │
  │  ├── is_deleted: bool                                       │
  │  ├── attachments: list[AttachmentDTO]                       │
  │  └── pdf_path: str | None                                   │
  └─────────────────────────────────────────────────────────────┘
```

### 6.2 Search DTOs

```
  ┌─────────────────────────────────────────────────────────────┐
  │  SearchQuery                                                │
  │  ├── query: str                                             │
  │  ├── filters: LetterFilters | None                          │
  │  ├── sort_by: str            (default: "created_at")        │
  │  ├── sort_order: str         (asc/desc)                     │
  │  ├── page: int               (default: 1)                   │
  │  └── size: int               (default: 50, max: 200)        │
  │                                                             │
  │  LetterFilters                                              │
  │  ├── status: str | None                                     │
  │  ├── priority: str | None                                   │
  │  ├── department_id: str | None                              │
  │  ├── created_by_id: str | None                              │
  │  ├── date_from: str | None                                  │
  │  ├── date_to: str | None                                    │
  │  ├── is_archived: bool | None                               │
  │  └── is_deleted: bool | None                                │
  │                                                             │
  │  PageResult[T]                                              │
  │  ├── items: list[T]                                         │
  │  ├── total: int                                             │
  │  ├── page: int                                              │
  │  ├── size: int                                              │
  │  ├── total_pages: int                                       │
  │  └── has_next: bool                                         │
  └─────────────────────────────────────────────────────────────┘
```

### 6.3 Archive DTOs

```
  ┌─────────────────────────────────────────────────────────────┐
  │  ArchiveDTO                                                 │
  │  ├── id: str                    (UUID)                      │
  │  ├── letter_id: str             (UUID)                      │
  │  ├── archived_by_id: str        (UUID)                      │
  │  ├── archived_by_name: str                                  │
  │  ├── archived_at: str            (ISO 8601)                 │
  │  ├── archive_path: str                                      │
  │  ├── content_hash: str                                      │
  │  ├── file_size_bytes: int                                   │
  │  ├── restored_at: str | None                                │
  │  └── restored_by_name: str | None                           │
  └─────────────────────────────────────────────────────────────┘
```

### 6.4 Backup DTOs

```
  ┌─────────────────────────────────────────────────────────────┐
  │  BackupDTO                                                  │
  │  ├── id: str                    (UUID)                      │
  │  ├── backup_path: str                                       │
  │  ├── size_bytes: int                                        │
  │  ├── hash_sha256: str                                       │
  │  ├── type: str                 (auto/manual/pre_migration)  │
  │  ├── created_by_id: str         (UUID)                      │
  │  ├── created_by_name: str                                   │
  │  ├── created_at: str             (ISO 8601)                 │
  │  ├── restored_at: str | None                                │
  │  └── notes: str | None                                      │
  └─────────────────────────────────────────────────────────────┘
```

### 6.5 User DTOs

```
  ┌─────────────────────────────────────────────────────────────┐
  │  CreateUserDTO                                              │
  │  ├── username: str                                          │
  │  ├── full_name: str                                         │
  │  ├── title: str                                             │
  │  ├── email: str | None                                      │
  │  ├── password: str                                          │
  │  ├── role: str                                               │
  │  └── department_id: str | None                              │
  │                                                             │
  │  UserDTO  (response — NEVER includes password_hash)          │
  │  ├── id: str                    (UUID)                      │
  │  ├── username: str                                           │
  │  ├── full_name: str                                          │
  │  ├── title: str                                              │
  │  ├── email: str | None                                       │
  │  ├── role: str                                               │
  │  ├── department_id: str | None                               │
  │  ├── department_name: str | None                             │
  │  ├── is_active: bool                                         │
  │  ├── last_login_at: str | None                               │
  │  ├── created_at: str                                         │
  │  └── updated_at: str                                         │
  └─────────────────────────────────────────────────────────────┘
```

### 6.6 Attachment DTO

```
  ┌─────────────────────────────────────────────────────────────┐
  │  AttachmentDTO                                              │
  │  ├── id: str                    (UUID)                      │
  │  ├── letter_id: str             (UUID)                      │
  │  ├── original_name: str                                     │
  │  ├── mime_type: str                                         │
  │  ├── size_bytes: int                                        │
  │  ├── hash_sha256: str                                       │
  │  └── created_at: str            (ISO 8601)                  │
  └─────────────────────────────────────────────────────────────┘
```

---

## 7. Database Schema Design

### 7.1 Entity-Relationship Diagram (ASCII)

```
  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
  │   letters    │       │    users     │       │ departments  │
  ├──────────────┤       ├──────────────┤       ├──────────────┤
  │ id (PK)      │       │ id (PK)      │       │ id (PK)      │
  │ number       │──┐    │ username     │       │ name         │
  │ subject      │  │    │ full_name    │       │ code         │
  │ body         │  │    │ title        │       │ parent_id──┐ │
  │ sender_name  │  │    │ email        │       │ is_active  │ │
  │ sender_title │  │    │ password_hash│       │ created_at │ │
  │ recipient_nm │  │    │ role         │──┐    │ updated_at │ │
  │ recipient_tl │  │    │ department_id│─┐│    └────────────┘ │
  │ recipient_dp │  │    │ is_active    │ ││                    │
  │ department_id│──┤    │ last_login   │ ││    ┌──────────────┐ │
  │ priority     │  │    │ created_at   │ ││    │ self-ref     │─┘
  │ status       │  │    │ updated_at   │ ││    └──────────────┘
  │ reference_nbr│  │    └──────┬───────┘ ││
  │ language     │  │           │         ││
  │ created_by_id│──┤    ┌──────┴───────┐ ││
  │ created_at   │  │    │audit_logs    │ ││
  │ updated_by_id│──┤    ├──────────────┤ ││
  │ updated_at   │  │    │ id (PK)      │ ││
  │ is_archived  │  │    │ timestamp    │ ││
  │ archived_at  │  │    │ user_id (FK)─┼─┘│
  │ archived_by  │──┤    │ action       │  │
  │ content_hash │  │    │ entity_type  │  │
  │ version      │  │    │ entity_id    │  │
  │ is_deleted   │  │    │ details_json │  │
  │ deleted_at   │  │    │ ip_address   │  │
  │ deleted_by   │──┤    │ result       │  │
  └──────┬───────┘  │    └─────────────┘   │
         │          │                      │
         │          │    ┌────────────────┐│
         │          │    │ archive_logs   ││
         │          │    ├────────────────┤│
         │          └────│ letter_id (FK)─┘│
         │               │ archived_by(FK)─┘
         │               │ archived_at    │
         │               │ archive_path   │
         │               │ content_hash   │
         │               │ file_size_bytes│
         │               │ restored_at    │
         │               │ restored_by(FK)│
         │               └────────┬───────┘
         │                        │
         │   ┌────────────────┐   │
         │   │ attachments    │   │
         │   ├────────────────┤   │
         └───│ letter_id (FK)─┘   │
             │ filename        │   │
             │ original_name   │   │
             │ file_path       │   │
             │ mime_type       │   │
             │ size_bytes      │   │
             │ hash_sha256     │   │
             │ created_at      │   │
             └────────────────┘   │
                                   │
  ┌──────────────┐   ┌────────────┴────────┐
  │ backup_logs  │   │letter_fts (VIRTUAL)  │
  ├──────────────┤   ├─────────────────────┤
  │ id (PK)      │   │ content              │
  │ backup_path  │   │ subject              │
  │ size_bytes   │   │ number               │
  │ hash_sha256  │   └─────────────────────┘
  │ type         │
  │ created_by   │──┐
  │ created_at   │  │   ┌────────────────┐
  │ restored_at  │  │   │ templates      │
  │ restored_by  │──┤   ├────────────────┤
  │ notes        │  │   │ id (PK)        │
  └──────────────┘  │   │ name           │
                     │   │ type           │
  ┌────────────────┐ │   │ content_json   │
  │ system_config  │ │   │ version_major  │
  ├────────────────┤ │   │ version_minor  │
  │ key (PK)       │ │   │ is_active      │
  │ value_json     │ │   │ created_at     │
  │ description    │ │   │ updated_at     │
  │ updated_at     │ │   └────────────────┘
  └────────────────┘ │
                      │   ┌────────────────┐
                      │   │ plugins        │
                      │   ├────────────────┤
                      └───│ id (PK)        │
                          │ name           │
                          │ version        │
                          │ module_path    │
                          │ is_active      │
                          │ config_json    │
                          │ installed_at   │
                          └────────────────┘

  ┌────────────────┐
  │ integration_cfg│    (Future: Gula, Lab, Ministry)
  ├────────────────┤
  │ id (PK)        │
  │ target_name    │
  │ adapter_module │
  │ endpoint_url   │
  │ auth_config_jsn│
  │ is_active      │
  │ last_sync_at   │
  │ created_at     │
  └────────────────┘
```

---

## 8. SQLite Table Definitions

### 8.1 `departments`

```sql
CREATE TABLE departments (
    id          TEXT PRIMARY KEY NOT NULL,       -- UUID
    name        TEXT NOT NULL UNIQUE,
    code        TEXT NOT NULL UNIQUE,
    parent_id   TEXT REFERENCES departments(id)  -- Self-referencing FK
                ON DELETE SET NULL
                ON UPDATE CASCADE,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,                   -- ISO 8601
    updated_at  TEXT NOT NULL                    -- ISO 8601
);
```

### 8.2 `users`

```sql
CREATE TABLE users (
    id              TEXT PRIMARY KEY NOT NULL,       -- UUID
    username        TEXT NOT NULL UNIQUE,
    full_name       TEXT NOT NULL,
    title           TEXT NOT NULL DEFAULT '',
    email           TEXT,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL                    -- ADMIN, EDITOR, VIEWER, AUDITOR
                    CHECK(role IN ('ADMIN','EDITOR','VIEWER','AUDITOR')),
    department_id   TEXT REFERENCES departments(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,
    is_active       INTEGER NOT NULL DEFAULT 1,
    last_login_at   TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

### 8.3 `letters`

```sql
CREATE TABLE letters (
    id              TEXT PRIMARY KEY NOT NULL,       -- UUID
    number          TEXT NOT NULL,                   -- Formatted: "MOH-2026-0042"
    subject         TEXT NOT NULL,
    body            TEXT NOT NULL,
    sender_name     TEXT NOT NULL,
    sender_title    TEXT NOT NULL DEFAULT '',
    recipient_name  TEXT NOT NULL,
    recipient_title TEXT NOT NULL DEFAULT '',
    recipient_dept  TEXT NOT NULL DEFAULT '',
    department_id   TEXT NOT NULL REFERENCES departments(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    priority        TEXT NOT NULL DEFAULT 'NORMAL'
                    CHECK(priority IN ('LOW','NORMAL','HIGH','URGENT')),
    status          TEXT NOT NULL DEFAULT 'DRAFT'
                    CHECK(status IN ('DRAFT','FINAL','SENT','ARCHIVED','CANCELLED')),
    reference_number TEXT,
    language        TEXT NOT NULL DEFAULT 'AR'
                    CHECK(language IN ('AR','AR_EN')),

    -- Metadata
    created_by_id   TEXT NOT NULL REFERENCES users(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    created_at      TEXT NOT NULL,
    updated_by_id   TEXT REFERENCES users(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,
    updated_at      TEXT,

    -- Archive state
    is_archived     INTEGER NOT NULL DEFAULT 0,
    archived_at     TEXT,
    archived_by_id  TEXT REFERENCES users(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,

    -- Integrity
    content_hash    TEXT NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,

    -- Soft delete
    is_deleted      INTEGER NOT NULL DEFAULT 0,
    deleted_at      TEXT,
    deleted_by_id   TEXT REFERENCES users(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,

    -- Unique constraint: number must be unique globally
    UNIQUE(number)
);

-- Performance indexes
CREATE INDEX idx_letters_department ON letters(department_id);
CREATE INDEX idx_letters_status ON letters(status);
CREATE INDEX idx_letters_priority ON letters(priority);
CREATE INDEX idx_letters_created_at ON letters(created_at);
CREATE INDEX idx_letters_created_by ON letters(created_by_id);
CREATE INDEX idx_letters_is_archived ON letters(is_archived);
CREATE INDEX idx_letters_is_deleted ON letters(is_deleted);
CREATE INDEX idx_letters_number ON letters(number);
CREATE INDEX idx_letters_archived_at ON letters(archived_at);
```

### 8.4 `attachments`

```sql
CREATE TABLE attachments (
    id              TEXT PRIMARY KEY NOT NULL,
    letter_id       TEXT NOT NULL REFERENCES letters(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
    filename        TEXT NOT NULL,                   -- Storage-safe name
    original_name   TEXT NOT NULL,                   -- User's original name
    file_path       TEXT NOT NULL,
    mime_type       TEXT NOT NULL,
    size_bytes      INTEGER NOT NULL,
    hash_sha256     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_attachments_letter ON attachments(letter_id);
```

### 8.5 `audit_logs`

```sql
CREATE TABLE audit_logs (
    id              TEXT PRIMARY KEY NOT NULL,
    timestamp       TEXT NOT NULL,
    user_id         TEXT NOT NULL REFERENCES users(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    details_json    TEXT NOT NULL DEFAULT '{}',
    ip_address      TEXT,
    result          TEXT NOT NULL DEFAULT 'success'
                    CHECK(result IN ('success','failure'))
);

-- Indexes for audit queries
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
```

### 8.6 `archive_logs`

```sql
CREATE TABLE archive_logs (
    id              TEXT PRIMARY KEY NOT NULL,
    letter_id       TEXT NOT NULL REFERENCES letters(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    archived_by_id  TEXT NOT NULL REFERENCES users(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    archived_at     TEXT NOT NULL,
    archive_path    TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    restored_at     TEXT,
    restored_by_id  TEXT REFERENCES users(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
);

CREATE INDEX idx_archive_letter ON archive_logs(letter_id);
CREATE INDEX idx_archive_date ON archive_logs(archived_at);
```

### 8.7 `backup_logs`

```sql
CREATE TABLE backup_logs (
    id              TEXT PRIMARY KEY NOT NULL,
    backup_path     TEXT NOT NULL,
    size_bytes      INTEGER NOT NULL,
    hash_sha256     TEXT NOT NULL,
    type            TEXT NOT NULL
                    CHECK(type IN ('AUTO','MANUAL','PRE_MIGRATION')),
    created_by_id   TEXT NOT NULL REFERENCES users(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    created_at      TEXT NOT NULL,
    restored_at     TEXT,
    restored_by_id  TEXT REFERENCES users(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,
    notes           TEXT
);

CREATE INDEX idx_backup_date ON backup_logs(created_at);
CREATE INDEX idx_backup_type ON backup_logs(type);
```

### 8.8 `system_config`

```sql
CREATE TABLE system_config (
    key             TEXT PRIMARY KEY NOT NULL,
    value_json      TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    updated_at      TEXT NOT NULL
);
```

### 8.9 `templates`

```sql
CREATE TABLE templates (
    id              TEXT PRIMARY KEY NOT NULL,
    name            TEXT NOT NULL UNIQUE,
    type            TEXT NOT NULL
                    CHECK(type IN ('OFFICIAL_LETTER','MEMO','INTERNAL','EXTERNAL')),
    content_json    TEXT NOT NULL,                   -- Template definition JSON
    version_major   INTEGER NOT NULL DEFAULT 1,
    version_minor   INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

### 8.10 `plugins`

```sql
CREATE TABLE plugins (
    id              TEXT PRIMARY KEY NOT NULL,
    name            TEXT NOT NULL UNIQUE,
    version         TEXT NOT NULL,
    module_path     TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 0,
    config_json     TEXT NOT NULL DEFAULT '{}',
    installed_at    TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

### 8.11 `integration_config`

```sql
CREATE TABLE integration_config (
    id              TEXT PRIMARY KEY NOT NULL,
    target_name     TEXT NOT NULL UNIQUE
                    CHECK(target_name IN ('GULA','LAB_SYSTEM','MINISTRY_ARCHIVE',
                                          'QR_VERIFICATION','BARCODE','INTERNAL_API')),
    adapter_module  TEXT NOT NULL,                   -- Python module path
    is_active       INTEGER NOT NULL DEFAULT 0,
    endpoint_config_json TEXT NOT NULL DEFAULT '{}',
    auth_config_json     TEXT NOT NULL DEFAULT '{}',
    last_sync_at    TEXT,
    last_error      TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
```

---

## 9. FTS5 Search Architecture

### 9.1 FTS5 Virtual Table

```sql
-- FTS5 virtual table for full-text search on letters
CREATE VIRTUAL TABLE letter_fts USING fts5(
    content,
    subject,
    letter_number,           -- The formatted number "MOH-2026-0042"
    tokenize='unicode61',
    content=letters,         -- Content sync with letters table
    content_rowid='rowid'    -- Uses letters.rowid
);

-- Triggers to keep FTS index in sync with letters table
CREATE TRIGGER letter_fts_insert AFTER INSERT ON letters BEGIN
    INSERT INTO letter_fts(rowid, content, subject, letter_number)
    VALUES (new.rowid, new.body, new.subject, new.number);
END;

CREATE TRIGGER letter_fts_delete AFTER DELETE ON letters BEGIN
    INSERT INTO letter_fts(letter_fts, rowid, content, subject, letter_number)
    VALUES ('delete', old.rowid, old.body, old.subject, old.number);
END;

CREATE TRIGGER letter_fts_update AFTER UPDATE ON letters BEGIN
    INSERT INTO letter_fts(letter_fts, rowid, content, subject, letter_number)
    VALUES ('delete', old.rowid, old.body, old.subject, old.number);
    INSERT INTO letter_fts(rowid, content, subject, letter_number)
    VALUES (new.rowid, new.body, new.subject, new.number);
END;

-- Rebuild FTS index function (called after migration or bulk import)
-- SELECT letter_fts_rebuild();
```

### 9.2 Search Query Pattern

```sql
-- Full-text search across subject, body, and letter number
SELECT l.*
FROM letters l
JOIN letter_fts fts ON l.rowid = fts.rowid
WHERE letter_fts MATCH ?
  AND l.is_deleted = 0
  AND l.is_archived = ?
ORDER BY rank
LIMIT ? OFFSET ?;
```

### 9.3 FTS5 Ranking

```sql
-- BM25 ranking (default) for relevance scoring
-- Weights: subject=5, number=3, body=1
SELECT l.*, rank
FROM letters l
JOIN (
    SELECT rowid, rank
    FROM letter_fts
    WHERE letter_fts MATCH ?
    ORDER BY rank
    LIMIT ? OFFSET ?
) fts ON l.rowid = fts.rowid
WHERE l.is_deleted = 0
ORDER BY fts.rank;
```

**Ranking Weights**: Subject matches score highest (5x), number exact matches next (3x), body content matches baseline (1x). This matches the domain expectation that official letter number and subject are the primary search dimensions.

### 9.4 FTS5 Rebuild Strategy

```
  Trigger                          When
  ─────────────────────────────────────────────────────
  Initial build                    First application startup after migration
  After migration                  Migration script includes FTS rebuild
  After bulk import                Import completes
  On application request           Admin-initiated "Rebuild Search Index"
```

---

## 10. Audit Log Schema

(Defined in Section 8.5 — `audit_logs` table)

### 10.1 Action Naming Convention

```
  {entity_type}.{action}

  Examples:
    letter.created
    letter.updated
    letter.deleted
    letter.archived
    letter.restored
    letter.pdf_generated
    letter.printed
    user.login
    user.login_failed
    user.created
    user.deactivated
    backup.created
    backup.restored
    archive.verified
    integration.synced
    config.updated
    migration.run
    migration.rolled_back
    system.error
```

### 10.2 Audit Record Examples

```
  Record 1:
    id:          "a1b2c3d4-..."
    timestamp:   "2026-05-28T10:30:00"
    user_id:     "u001-..."
    action:      "letter.created"
    entity_type: "letter"
    entity_id:   "l001-..."
    details_json: '{"number":"MOH-2026-0042","priority":"HIGH"}'
    result:      "success"

  Record 2:
    id:          "e5f6g7h8-..."
    timestamp:   "2026-05-28T11:00:00"
    user_id:     "u001-..."
    action:      "letter.updated"
    entity_type: "letter"
    entity_id:   "l001-..."
    details_json: '{"changed_fields":["subject","body"],"version":2}'
    result:      "success"

  Record 3:
    id:          "i9j0k1l2-..."
    timestamp:   "2026-05-28T11:05:00"
    user_id:     "u002-..."
    action:      "user.login_failed"
    entity_type: "user"
    entity_id:   "u002-..."
    details_json: '{"attempt_username":"admin","reason":"invalid_password"}'
    result:      "failure"
```

---

## 11. Backup Metadata Schema

(Defined in Section 8.7 — `backup_logs` table)

### 11.1 Backup File Naming Convention

```
  backup-{YYYY}-{MM}-{DD}-{HH24}{MI}{SS}-{TYPE}.zip

  Examples:
    backup-2026-05-28-120000-AUTO.zip
    backup-2026-05-28-150000-MANUAL.zip
    backup-2026-06-01-080000-PRE_MIGRATION.zip
```

### 11.2 Backup ZIP Contents

```
  backup-2026-05-28-120000-AUTO.zip
  ├── correspondence.db              # SQLite database
  ├── config.json                    # Application configuration
  ├── archive_index.json             # Archive index reference
  ├── manifest.json                  # Backup metadata (version, schema version, etc.)
  └── integrity.sha256               # SHA-256 hashes of all files in archive
```

### 11.3 Backup Manifest Format

```json
{
  "backup_version": "1.0",
  "created_at": "2026-05-28T12:00:00",
  "application_version": "1.0.0",
  "schema_version": 3,
  "database_size_bytes": 52428800,
  "file_count": 4,
  "files": {
    "correspondence.db": "sha256:abc...",
    "config.json": "sha256:def...",
    "archive_index.json": "sha256:ghi..."
  }
}
```

---

## 12. PDF Archive Schema

### 12.1 Archive File Structure

```
  archives/
  ├── index.json
  ├── 2026/
  │   ├── 01/
  │   │   ├── MOH-2026-0001.json
  │   │   ├── MOH-2026-0001.pdf
  │   │   ├── MOH-2026-0002.json
  │   │   └── MOH-2026-0002.pdf
  │   ├── 02/
  │   └── ...
  ├── 2027/
  └── ...
```

### 12.2 Archive JSON Format

```json
{
  "format_version": "1.0",
  "letter": {
    "id": "uuid",
    "number": "MOH-2026-0042",
    "subject": "Official Correspondence Subject",
    "body": "Full letter body text...",
    "sender_name": "Dr. Ali Ahmed",
    "sender_title": "Director General",
    "recipient_name": "Ministry of Health",
    "recipient_title": "Minister",
    "recipient_dept": "Department of Planning",
    "department": "MOH",
    "priority": "HIGH",
    "status": "SENT",
    "reference_number": "REF-2025-001",
    "language": "AR_EN",
    "attachments": [
      {
        "original_name": "report.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1024000,
        "hash_sha256": "abc..."
      }
    ]
  },
  "metadata": {
    "archived_at": "2026-05-28T12:00:00",
    "archived_by": "user-uuid",
    "archived_by_name": "Dr. Ali Ahmed",
    "content_hash": "sha256-of-canonical-letter-state",
    "pdf_hash": "sha256-of-archived-pdf",
    "previous_archives": []
  }
}
```

### 12.3 Archive Index

```json
{
  "version": "1",
  "letters": {
    "MOH-2026-0001": {
      "id": "uuid",
      "subject": "...",
      "archived_at": "2026-05-28T12:00:00",
      "json_path": "2026/01/MOH-2026-0001.json",
      "pdf_path": "2026/01/MOH-2026-0001.pdf",
      "content_hash": "sha256...",
      "size_bytes": 204800
    }
  },
  "last_updated": "2026-05-28T12:00:00"
}
```

---

## 13. File Integrity Schema

### 13.1 Integrity Chain

```
  ┌─────────────────────────────────────────────────────────┐
  │                  INTEGRITY CHAIN                         │
  │                                                         │
  │  Letter Creation:                                       │
  │    letter.content_hash = SHA256( canonical_json(letter) )│
  │                                                         │
  │  Archive:                                                │
  │    archive.content_hash = letter.content_hash            │
  │    archive.file_hash    = SHA256( archive_file_contents ) │
  │                                                         │
  │  Backup:                                                 │
  │    backup.hash_sha256   = SHA256( backup_zip_contents )  │
  │    Each file inside ZIP has its own SHA256 in manifest   │
  │                                                         │
  │  Verification flow:                                      │
  │    Read file        Compute SHA256     Compare to stored │
  │    ─────────        ─────────────      ────────────────  │
  │    letter from DB   recompute hash     match? OK/FAIL    │
  │    JSON archive     file content hash  match? OK/FAIL    │
  │    PDF archive      file content hash  match? OK/FAIL    │
  │    Backup ZIP       ZIP content hash   match? OK/FAIL    │
  └─────────────────────────────────────────────────────────┘
```

### 13.2 Canonical JSON for Content Hash

```python
  def compute_content_hash(letter: Letter) -> str:
      """Deterministic JSON representation for hashing."""
      canonical = {
          "id": str(letter.id),
          "number": letter.number,
          "subject": letter.subject,
          "body": letter.body,
          "sender_name": letter.sender_name,
          "sender_title": letter.sender_title,
          "recipient_name": letter.recipient_name,
          "recipient_title": letter.recipient_title,
          "recipient_dept": letter.recipient_dept,
          "department_id": str(letter.department_id),
          "priority": letter.priority,
          "status": letter.status,
          "reference_number": letter.reference_number,
          "language": letter.language,
      }
      # Sort keys for deterministic output
      json_str = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
      return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
```

---

## 14. User and RBAC Schema

### 14.1 Roles and Permissions Matrix

```
  Permission                 ADMIN   EDITOR   VIEWER   AUDITOR
  ──────────────────────────────────────────────────────────────
  letter.create                ✓       ✓        –        –
  letter.read                  ✓       ✓        ✓        ✓
  letter.update                ✓       ✓        –        –
  letter.delete (soft)         ✓       –        –        –
  letter.hard_delete           ✓       –        –        –
  letter.archive               ✓       ✓        –        –
  letter.restore               ✓       –        –        –
  letter.generate_pdf          ✓       ✓        ✓        –
  letter.print                 ✓       ✓        ✓        ✓
  letter.export                ✓       ✓        ✓        ✓

  user.create                  ✓       –        –        –
  user.read                    ✓       –        –        ✓
  user.update                  ✓       –        –        –
  user.deactivate              ✓       –        –        –

  department.manage            ✓       –        –        –
  backup.create                ✓       ✓        –        –
  backup.restore               ✓       –        –        –
  backup.delete                ✓       –        –        –

  audit.read                   ✓       –        –        ✓
  audit.export                 ✓       –        –        ✓

  config.read                  ✓       ✓        –        –
  config.update                ✓       –        –        –

  plugin.manage                ✓       –        –        –
  integration.manage           ✓       –        –        –
```

### 14.2 Authorization Check Pattern

```python
  # Domain-level: no framework dependency
  def require_permission(user_role: UserRole, permission: str) -> bool:
      """Check if role has permission. Returns True/False."""
      return permission in PERMISSION_MATRIX.get(user_role, set())
```

---

## 15. Template Schema

(Defined in Section 8.9 — `templates` table)

### 15.1 Template Content Format

```json
{
  "template_version": "1.0",
  "page_size": "A4",
  "margins_mm": {
    "top": 25,
    "bottom": 20,
    "left": 25,
    "right": 20
  },
  "header": {
    "logo_path": "assets/logo.png",
    "ministry_name": "وزارة الصحة",
    "department_name": "{department_name}",
    "font_size": 14,
    "alignment": "CENTER"
  },
  "fields": [
    {"name": "letter_number", "x": 50, "y": 200, "font": "Arabic", "size": 12},
    {"name": "subject",       "x": 50, "y": 230, "font": "Arabic", "size": 14, "bold": true},
    {"name": "date",          "x": 450, "y": 200, "font": "Arabic", "size": 12},
    {"name": "recipient",     "x": 50, "y": 270, "font": "Arabic", "size": 12},
    {"name": "body",          "x": 50, "y": 320, "font": "Arabic", "size": 12, "width": 500, "height": 400}
  ],
  "footer": {
    "text": "هذا المستند صادر عن وزارة الصحة",
    "font_size": 8,
    "alignment": "CENTER"
  }
}
```

---

## 16. Plugin Registry Schema

(Defined in Section 8.10 — `plugins` table)

### 16.1 Plugin Manifest Format

```json
{
  "name": "statistics-export",
  "version": "1.0.0",
  "author": "Ministry of Health IT",
  "description": "Export letter statistics in CSV/Excel format",
  "hooks": ["on_letter_created", "on_letter_archived"],
  "dependencies": {},
  "min_app_version": "1.0.0",
  "python_version": ">=3.12"
}
```

---

## 17. Integration Contract Schema

(Defined in Section 8.11 — `integration_config` table)

### 17.1 Integration Endpoint Configuration

```json
{
  "gula": {
    "base_url": "",
    "timeout_seconds": 30,
    "retry_count": 3,
    "sync_interval_minutes": 60,
    "data_format": "HL7_FHIR",
    "auth_method": "API_KEY"
  },
  "lab_system": {
    "base_url": "",
    "timeout_seconds": 30,
    "retry_count": 3,
    "sync_interval_minutes": 15,
    "data_format": "JSON",
    "auth_method": "CERTIFICATE"
  }
}
```

### 17.2 Integration Data Mapping

```
  Correspondence Field           Gula Mapping           Lab System Mapping
  ──────────────────────────────────────────────────────────────────────
  letter.number                  DocumentReference.id   requisition.number
  letter.subject                 Description            test.name
  letter.body                    text.content            notes
  letter.sender_name             author.display         requesting_physician
  letter.recipient_name          custodian.display      performing_lab
  letter.department_id           facility               department
  letter.created_at              date                   date_ordered
  attachment[]                   Attachments[]          supporting_documents[]

  Mapping is configurable per integration target via integration_config
```

---

## 18. Migration Strategy

### 18.1 Migration Framework

- **Tool**: Alembic
- **Location**: `app/database/migrations/`
- **Naming**: `{revision_id}_{description}.py`
- **Version Storage**: `alembic_version` table in SQLite

### 18.2 Migration Rules

```
  1. Every migration MUST have both upgrade() and downgrade()
  2. Every migration MUST be reversible (no destructive downgrade)
  3. Every migration MUST be tested on a copy of production data
  4. Every migration MUST create a pre-migration backup automatically
  5. Migration version is checked on application startup
  6. Stale or missing migrations trigger application exit with error message
```

### 18.3 Migration Lifecycle

```
  Developer:
    1. alembic revision --autogenerate -m "description"
    2. Review generated migration script
    3. Test upgrade + downgrade
    4. Commit migration script

  Application Startup:
    1. alembic upgrade head
    2. On failure: log error, rollback, notify user
    3. On success: log migration, update schema version
```

### 18.4 Migration Sequence Example

```
  Revision ID: 001
  Description: create_initial_tables
  Changes:
    - CREATE TABLE departments
    - CREATE TABLE users
    - CREATE TABLE letters
    - CREATE TABLE attachments
    - CREATE TABLE audit_logs
    - CREATE TABLE archive_logs
    - CREATE TABLE backup_logs
    - CREATE TABLE system_config
    - CREATE TABLE templates
    - CREATE TABLE plugins
    - CREATE TABLE integration_config
    - CREATE VIRTUAL TABLE letter_fts

  Revision ID: 002
  Description: add_letter_language_field
  Changes:
    - ALTER TABLE letters ADD COLUMN language TEXT
    - UPDATE letters SET language = 'AR' WHERE language IS NULL
    - Rebuild FTS index

  Revision ID: 003
  Description: add_attachment_hash
  Changes:
    - ALTER TABLE attachments ADD COLUMN hash_sha256 TEXT
    - Backfill existing attachments with computed hashes
```

---

## 19. Versioning Strategy

### 19.1 Application Version

```
  Format:  MAJOR.MINOR.PATCH  (SemVer)
  Example: 1.3.2

  MAJOR: Breaking schema changes, incompatible archive formats
  MINOR: New features, backward-compatible schema additions
  PATCH: Bug fixes, no schema changes
```

### 19.2 Schema Version

```
  Stored in: system_config WHERE key = 'schema_version'
  Format:    Integer (monotonically increasing)

  Schema version increments ONLY with migrations.
  Application checks: app_schema >= db_schema.
```

### 19.3 Archive Format Version

```
  Stored in: archive JSON file as format_version field
  Format:    "MAJOR.MINOR" string
  Example:   "1.0"

  Backward compatibility: app reads all archives with same MAJOR version.
  Cross-MAJOR migration requires explicit archive migration tool.
```

### 19.4 Backup Format Version

```
  Stored in: manifest.json inside backup ZIP as backup_version field
  Format:    "MAJOR.MINOR" string
```

---

## 20. Soft Delete Strategy

### 20.1 Soft Delete Implementation

```sql
  -- Soft delete columns on letters table:
  is_deleted      INTEGER NOT NULL DEFAULT 0,
  deleted_at      TEXT,
  deleted_by_id   TEXT REFERENCES users(id)
```

### 20.2 Soft Delete Rules

```
  1. Soft delete sets is_deleted=1, deleted_at=NOW, deleted_by_id=user
  2. Soft-deleted records are hidden from default search/queries
     - All repository queries include: WHERE is_deleted = 0 (by default)
     - Explicit find_deleted() queries return only deleted records
  3. Soft-deleted records can be restored (is_deleted=0)
  4. Hard delete (admin only, logged, permanent) calls hard_delete()
  5. Hard delete physically removes from database (admin confirmation required)
  6. Audit log preserves the record of deletion regardless of type
```

### 20.3 Soft Delete vs Hard Delete Decision

```
  Operation         Soft Delete    Hard Delete
  ──────────────────────────────────────────────────
  User deletes      ✓              ✗ (only admin)
  Admin deletes     ✓              ✓ (with confirmation)
  Recoverable?      ✓ (restore)    ✗
  Appears in audit  ✓              ✓
  Triggers FTS      removes from   removes from
  removal?          index          index
  Attachments       preserved      removed from disk
```

---

## 21. Immutable Archive Strategy

### 21.1 Archive Immutability Rules

```
  1. Once a letter is archived:
     - letter.is_archived = True
     - letter.status = 'ARCHIVED'
     - No UPDATE operations allowed (service layer enforces)
     - Attachment modifications blocked
     - PDF regeneration blocked

  2. Archive file (JSON + PDF):
     - Written to year/month directory
     - SHA-256 hash stored in archive_logs
     - File permissions set to read-only on OS level
     - Never overwritten (append-only)

  3. Archive reversal:
     - Not "unarchive" — it's "restore from archive"
     - Creates a NEW version of the letter
     - Original archive record remains untouched (append-only)
     - New letter version has new content_hash

  4. Archive verification:
     - On-demand: verify any archive file against its stored hash
     - Bulk: verify archive index integrity
     - Automatic: periodic integrity check (configurable)
```

### 21.2 Archive State Machine

```
  ┌──────────┐    archive    ┌──────────┐   restore    ┌──────────┐
  │  ACTIVE  │ ────────────> │ ARCHIVED │ ───────────> │  ACTIVE  │
  │  letter  │               │  letter  │  (new        │  letter  │
  │          │               │ (read-   │   version)   │ (v+1)    │
  │          │               │  only)   │              │          │
  └──────────┘               └──────────┘              └──────────┘
       │                           │                        │
       │ soft delete               │ soft delete            │
       ▼                           ▼                        ▼
  ┌──────────┐               ┌──────────┐            ┌──────────┐
  │ DELETED  │               │ DELETED  │            │ DELETED  │
  │ (hidden) │               │ (hidden) │            │ (hidden) │
  └──────────┘               └──────────┘            └──────────┘
```

---

## 22. Transaction Safety Strategy

### 22.1 SQLite Transaction Configuration

```sql
  -- Enforced on every database connection
  PRAGMA journal_mode = WAL;           -- Write-Ahead Logging for crash safety
  PRAGMA synchronous = NORMAL;         -- Balance safety and performance
  PRAGMA foreign_keys = ON;            -- Enforce FK constraints
  PRAGMA busy_timeout = 5000;          -- 5-second busy wait before error
  PRAGMA cache_size = -8000;           -- 8MB page cache
  PRAGMA temp_store = MEMORY;          -- Temp tables in memory
```

### 22.2 Transaction Patterns

```
  Read Operation (auto-transaction):
    BEGIN DEFERRED
      SELECT ...
    COMMIT
    (No explicit transaction needed — SQLAlchemy auto-transactions)

  Write Operation (single entity):
    BEGIN IMMEDIATE
      UPDATE / INSERT
    COMMIT

  Write Operation (multi-step, e.g. archive):
    BEGIN IMMEDIATE          -- Prevents writer deadlock
      UPDATE letters SET is_archived = 1 WHERE id = ?
      INSERT INTO archive_logs (...)
      INSERT INTO audit_logs (...)
    COMMIT

  Backup (read lock):
    BEGIN IMMEDIATE
      PRAGMA wal_checkpoint(TRUNCATE)
      -- File copy outside transaction
    COMMIT
```

### 22.3 Transaction Flow: Archive Letter

```
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │ ArchiveServ  │     │  SQLite DB   │     │  File System │
  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
         │                    │                    │
         │ BEGIN IMMEDIATE    │                    │
         │───────────────────>│                    │
         │                    │                    │
         │ UPDATE letters     │                    │
         │ SET is_archived=1  │                    │
         │───────────────────>│                    │
         │                    │  OK                │
         │<───────────────────│                    │
         │                    │                    │
         │ INSERT archive_logs│                    │
         │───────────────────>│                    │
         │                    │  OK                │
         │<───────────────────│                    │
         │                    │                    │
         │ INSERT audit_logs  │                    │
         │───────────────────>│                    │
         │                    │  OK                │
         │<───────────────────│                    │
         │                    │                    │
         │ COMMIT             │                    │
         │───────────────────>│                    │
         │                    │                    │
         │ Write JSON archive │                    │
         │────────────────────────────────────────>│
         │                    │                    │  OK
         │<────────────────────────────────────────│
         │                    │                    │
         │ Write PDF archive  │                    │
         │────────────────────────────────────────>│
         │                    │                    │  OK
         │<────────────────────────────────────────│
         │                    │                    │
```

### 22.4 Deadlock Prevention

```
  1. All write transactions start with BEGIN IMMEDIATE
  2. Table access order is consistent across the codebase:
     letters -> attachments -> archive_logs -> audit_logs
  3. No nested transactions
  4. Busy timeout of 5 seconds before SQLITE_BUSY
  5. Retry logic for SQLITE_BUSY (3 retries with exponential backoff)
```

---

## 23. Atomic Write Strategy

### 23.1 File System Atomic Writes

```python
  def atomic_write(target_path: Path, content: bytes) -> None:
      """Write file atomically to prevent partial writes on crash."""
      temp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
      temp_path.write_bytes(content)
      temp_path.rename(target_path)  # Atomic on same filesystem
      # On Windows: os.replace() is the atomic rename
```

### 23.2 Atomic Operations Summary

```
  Operation               Atomicity Mechanism
  ──────────────────────────────────────────────────────────
  Database write          SQLite transactions (WAL mode)
  File write (JSON)       Write to .tmp, then rename
  File write (PDF)        Write to .tmp, then rename
  Backup creation         Write to .tmp.zip, then rename
  Config update           Read + write in transaction
  Archive file write      Write to .tmp, verify hash, rename
```

### 23.3 Partial Write Recovery

```
  On startup:
    1. Scan temp/ directory for .tmp files
    2. If .tmp file exists without matching target:
       a. Verify .tmp file integrity
       b. If valid, rename to target
       c. If invalid, delete .tmp
    3. Log recovery actions
```

---

## 24. Data Retention Strategy

### 24.1 Retention Policy

```
  Data Type               Active      Archived    Retention
  ─────────────────────────────────────────────────────────────────
  Active letters           Forever     N/A         Until archived or deleted
  Archived letters         N/A         Forever     Permanent (immutable)
  Soft-deleted letters     N/A         N/A         90 days then auto hard-delete
  Audit logs               N/A         N/A         Forever (append-only)
  Archive logs             N/A         N/A         Forever (append-only)
  Backup files             N/A         N/A         30 days (AUTO), manual (forever)
  Backup logs              N/A         N/A         Forever (append-only)
  System config            Forever     N/A         Forever
  Templates                Forever     N/A         Forever
  Plugin registry          Forever     N/A         Forever
  Integration config       Forever     N/A         Forever
  Temp files               N/A         N/A         Cleared on startup
  Log files (text)         N/A         N/A         10 rotations of 10MB
```

### 24.2 Hard-Delete Purge Job

```sql
  -- Runs daily: permanently removes records soft-deleted >90 days
  DELETE FROM letters WHERE is_deleted = 1
      AND deleted_at < datetime('now', '-90 days');
```

### 24.3 Auto-Backup Retention

```sql
  -- Removes AUTO backups older than 30 days (except PRE_MIGRATION)
  DELETE FROM backup_logs WHERE type = 'AUTO'
      AND created_at < datetime('now', '-30 days');
  -- Remove corresponding backup files from disk
```

---

## 25. Search Indexing Strategy

### 25.1 Search Coverage

```
  Field        Indexed      FTS5        LIKE
  ──────────────────────────────────────────────
  number       ✓ (btree)    ✓           ✓
  subject      ✗            ✓           ✓
  body         ✗            ✓           ✓
  sender_name  ✗            ✗           ✓
  recipient_nm ✗            ✗           ✓
```

### 25.2 Search Execution Order

```
  1. Parse query into tokens
  2. If query looks like a letter number pattern (e.g. "MOH-2026-*"):
     - First: exact prefix match on idx_letters_number
     - Then: FTS5 fallback
  3. If query is general text:
     - FTS5 MATCH on letter_fts (ranked by BM25)
     - Fallback: LIKE '%query%' if FTS returns no results
  4. Apply filters (status, department, date range, archived)
  5. Paginate results
  6. Return PageResult[LetterDTO]
```

### 25.3 Search Performance Targets

```
  Letters      Query Time (FTS5)    Query Time (LIKE)
  ──────────────────────────────────────────────────────
  1,000        < 10ms               < 20ms
  10,000       < 30ms               < 100ms
  100,000      < 100ms              < 500ms
  1,000,000    < 300ms              ~ 2-3s
```

---

## 26. Performance Indexing Strategy

### 26.1 Index Summary

```
  Table            Index                          Type       Purpose
  ─────────────────────────────────────────────────────────────────────
  letters          idx_letters_department         btree      Filter by dept
  letters          idx_letters_status             btree      Filter by status
  letters          idx_letters_priority           btree      Filter/sort by prio
  letters          idx_letters_created_at         btree      Sort by date
  letters          idx_letters_created_by         btree      Filter by creator
  letters          idx_letters_is_archived        btree      Filter archived
  letters          idx_letters_is_deleted         btree      Filter deleted
  letters          idx_letters_number             btree      Exact match
  letters          idx_letters_archived_at        btree      Sort archive date
  attachments      idx_attachments_letter         btree      Find by letter
  audit_logs       idx_audit_timestamp            btree      Date range queries
  audit_logs       idx_audit_user                 btree      User activity
  audit_logs       idx_audit_action               btree      Action filter
  audit_logs       idx_audit_entity               btree      Entity history
  archive_logs     idx_archive_letter             btree      Find by letter
  archive_logs     idx_archive_date               btree      Date range queries
  backup_logs      idx_backup_date                btree      Sort by date
  backup_logs      idx_backup_type                btree      Filter by type
```

### 26.2 Composite Index Candidates

```sql
  -- Common query pattern: filter by department + status + date
  CREATE INDEX idx_letters_dept_status_date
      ON letters(department_id, status, created_at);

  -- Common query pattern: filter by creator + status + date
  CREATE INDEX idx_letters_creator_status_date
      ON letters(created_by_id, status, created_at);
```

### 26.3 Index Maintenance

```
  - SQLite automatically maintains indexes on write operations
  - REINDEX command available for index rebuild after bulk operations
  - ANALYZE command updates query planner statistics
  - Both executed periodically during maintenance windows
```

---

## 27. Foreign Key Policy

### 27.1 FK Enforcement

```sql
  PRAGMA foreign_keys = ON;  -- Enforced on every connection
```

### 27.2 FK Rules by Table

```
  Table           FK Column        References       On Delete     On Update
  ────────────────────────────────────────────────────────────────────────────
  users           department_id    departments(id)  SET NULL      CASCADE
  letters         department_id    departments(id)  RESTRICT      CASCADE
  letters         created_by_id    users(id)        RESTRICT      CASCADE
  letters         updated_by_id    users(id)        SET NULL      CASCADE
  letters         archived_by_id   users(id)        SET NULL      CASCADE
  letters         deleted_by_id    users(id)        SET NULL      CASCADE
  attachments     letter_id        letters(id)      CASCADE       CASCADE
  audit_logs      user_id          users(id)        RESTRICT      CASCADE
  archive_logs    letter_id        letters(id)      RESTRICT      CASCADE
  archive_logs    archived_by_id   users(id)        RESTRICT      CASCADE
  archive_logs    restored_by_id   users(id)        SET NULL      CASCADE
  backup_logs     created_by_id    users(id)        RESTRICT      CASCADE
  backup_logs     restored_by_id   users(id)        SET NULL      CASCADE
  departments     parent_id       departments(id)   SET NULL      CASCADE
```

### 27.3 FK Design Decisions

```
  RESTRICT:  Prevents deletion of referenced record if references exist
             Used for critical audit/integrity relationships
  SET NULL:  Allows referenced record deletion, sets FK to NULL
             Used for optional relationships
  CASCADE:   Propagates key changes to child records
             Used for UUID updates (rare) and attachment cleanup
```

---

## 28. UUID Strategy

### 28.1 UUID Generation

```
  Format:     UUIDv4 (random)
  Storage:    TEXT (36 characters: "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")
  Generation: Python uuid.uuid4()
  Indexing:   B-tree on TEXT column (SQLite has no native UUID type)
```

### 28.2 UUID Rationale

```
  Decision: TEXT storage, not BLOB or INTEGER

  Reasons:
    1. Readability: UUIDs in logs and exports are human-readable
    2. Debugging: TEXT UUIDs are directly visible in SQLite CLI
    3. Portability: No endianness issues across platforms
    4. Migration: No type conversion needed for archive JSON files
    5. SQLite: No native UUID type — TEXT is the standard convention

  Performance: B-tree index on TEXT UUID (16 bytes hex) is efficient
               for expected data volumes (< 10M rows)
```

### 28.3 UUID Domain Type Mapping

```python
  # Domain layer: NewType for type safety
  LetterId = NewType("LetterId", uuid.UUID)
  UserId = NewType("UserId", uuid.UUID)
  DepartmentId = NewType("DepartmentId", uuid.UUID)
  AttachmentId = NewType("AttachmentId", uuid.UUID)
  AuditEntryId = NewType("AuditEntryId", uuid.UUID)
  ArchiveLogId = NewType("ArchiveLogId", uuid.UUID)
  BackupLogId = NewType("BackupLogId", uuid.UUID)
```

---

## 29. File Storage Contracts

### 29.1 File Storage Interface

```python
  class FileStorage(ABC):
      """Abstract file storage for letters, archives, backups."""

      @abstractmethod
      def store(self, relative_path: str, content: bytes) -> str:
          """Store file, return full path."""

      @abstractmethod
      def retrieve(self, relative_path: str) -> bytes:
          """Retrieve file contents."""

      @abstractmethod
      def delete(self, relative_path: str) -> None:
          """Delete file."""

      @abstractmethod
      def exists(self, relative_path: str) -> bool:
          """Check if file exists."""

      @abstractmethod
      def compute_hash(self, relative_path: str) -> str:
          """Compute SHA-256 of stored file."""

      @abstractmethod
      def size(self, relative_path: str) -> int:
          """Get file size in bytes."""
```

### 29.2 Storage Directory Mapping

```
  Logical Path                     Physical Directory      Content
  ──────────────────────────────────────────────────────────────────
  letters/{letter_id}.pdf          generated_letters/      Generated PDF
  letters/{letter_id}/{filename}   generated_letters/      Attachments
  archives/{year}/{month}/{num}.json  archives/            Archived JSON
  archives/{year}/{month}/{num}.pdf   archives/            Archived PDF
  backups/{filename}.zip           backups/                Backup files
  temp/{uuid}.tmp                  temp/                   Temporary files
  logs/{filename}.log              logs/                   Log files
```

### 29.3 File Naming Rules

```
  - Generated PDF:    {letter_number}.pdf          (e.g. MOH-2026-0042.pdf)
  - Archived JSON:    {letter_number}.json
  - Archived PDF:     {letter_number}.pdf
  - Attachment:       {attachment_id}-{sanitized_original_name}
  - Backup:           backup-{YYYYMMDD-HHMMSS}-{TYPE}.zip
  - Temp:             {uuid}.tmp
  - Log:              correspondence.{date}.log
```

### 29.4 Sanitized Filename Function

```python
  def sanitize_filename(name: str) -> str:
      """Remove unsafe characters from filename."""
      # Remove path separators, null bytes, and control characters
      safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', name)
      # Limit length (max 200 chars)
      if len(safe) > 200:
          name_part, ext = os.path.splitext(safe)
          safe = name_part[:195] + ext
      return safe
```

---

## 30. Future Integration Mapping Strategy

### 30.1 Integration Principles

```
  1. All integration is OPTIONAL and ADDITIVE
  2. Core offline functionality NEVER depends on integration
  3. Each integration target has its own adapter module
  4. Adapters communicate via the IntegrationService (service layer)
  5. Integration data NEVER shares the core database directly
  6. All integration data exchange uses message-based or API patterns
  7. Integration failures are isolated — never crash core
```

### 30.2 Gula Platform Mapping

```
  Correspondence Domain          Gula Equivalent
  ──────────────────────────────────────────────────────────
  Letter                         DocumentReference
  Letter.subject                 Description
  Letter.body                    text.content
  Letter.sender_name             author.display
  Letter.sender_title            author.practitioner.role
  Letter.recipient_name          custodian.display
  Letter.recipient_dept          facility.organization
  Letter.department_id           facility.department
  Letter.number                  identifier.value
  Letter.created_at              date
  Letter.priority                urgency
  Letter.reference_number        replaces.identifier
  Attachment                     DocumentReference.attachment
  Attachment.hash_sha256         attachment.hash
  User                           Practitioner
  User.full_name                 practitioner.name
  User.title                     practitioner.role
  Department                     Organization
  Department.code                organization.identifier
  ArchiveLog                     DocumentReference.status=superseded

  Sync Mode:     Push (outgoing) + Pull (incoming)
  Trigger:       On letter create/archive + periodic sync
  Auth:          API Key or Certificate (configured per deployment)
  Failure:       Queue failed, retry, never block core
```

### 30.3 Laboratory Receipt and Delivery System Mapping

```
  Correspondence Domain          Lab System Equivalent
  ──────────────────────────────────────────────────────────
  Letter (lab request)           LabOrder / ServiceRequest
  Letter.number                  order.identifier
  Letter.subject                 order.description
  Letter.body                    order.notes / instructions
  Letter.sender_name             order.requester
  Letter.recipient_name          order.performer (lab name)
  Letter.created_at              order.date
  Letter.priority                order.priority
  Attachment (lab results)       DiagnosticReport
  Attachment.hash_sha256         report.hash
  Letter.status                  order.status

  Sync Mode:     Bidirectional (request → lab, results → correspondence)
  Trigger:       On letter create (push), periodic (poll for results)
  Auth:          Certificate-based
  Failure:       Queue failed, retry, never block core
  Data Format:   JSON / HL7 FHIR (configurable)
```

### 30.4 Integration Adapter Contract

```python
  class IntegrationAdapter(ABC):
      """Base class for all integration adapters."""

      @abstractmethod
      def initialize(self, config: dict) -> bool:
          """Initialize adapter with configuration."""

      @abstractmethod
      def send_letter(self, letter_dto: LetterDTO) -> IntegrationResult:
          """Send letter to external system."""

      @abstractmethod
      def receive_documents(self, since: datetime) -> list[dict]:
          """Pull documents from external system."""

      @abstractmethod
      def health_check(self) -> bool:
          """Check if external system is reachable."""

      @abstractmethod
      def shutdown(self) -> None:
          """Clean up connection resources."""

  @dataclass
  class IntegrationResult:
      success: bool
      external_id: str | None
      error_message: str | None
      synced_at: datetime
```

### 30.5 Integration Data Isolation

```
  ┌──────────────────────────────────────────────────────┐
  │                  CORE DATABASE                        │
  │  (SQLite — local, offline, single source of truth)    │
  │  - letters, users, departments, audit_logs, etc.     │
  └──────────────────────┬───────────────────────────────┘
                         │
                         │  No direct database access
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │               INTEGRATION SERVICE LAYER                │
  │  - Reads LetterDTO from core via service calls        │
  │  - Maps to external format (FHIR, JSON, etc.)         │
  │  - Calls adapter.send_letter()                        │
  │  - Logs integration results in audit_logs             │
  │  - Handles retry, error logging, failure isolation    │
  └──────┬──────────────────────┬─────────────────────────┘
         │                      │
         ▼                      ▼
  ┌──────────────┐    ┌──────────────────┐
  │ Gula Adapter │    │ Lab System       │
  │ (external)   │    │ Adapter (ext.)   │
  └──────────────┘    └──────────────────┘

  Key constraint: Integration layer calls core services (not database).
  Core has zero knowledge of integration targets.
```

### 30.6 Integration Lifecycle

```
  1. System starts with integration modules inactive
  2. Admin configures integration target via integration_config
  3. IntegrationAdapter.initialize(config) is called
  4. Integration becomes active if initialization succeeds
  5. On letter create/archive:
     - Core service completes (always succeeds regardless of integration)
     - IntegrationService.send_letter() called asynchronously
     - Success: log audit "integration.synced", update last_sync_at
     - Failure: log audit "integration.failed", queue retry
  6. On periodic sync:
     - IntegrationService.receive_documents() called
     - New documents mapped to internal format
     - Core services notified of new documents
  7. Integration can be deactivated at any time (no data loss)
```

---

## Appendix A: Complete Table Index

```
  Table                Row Estimate    Primary Key    FTS    Append-Only
  ──────────────────────────────────────────────────────────────────────
  letters              500,000         UUID           ✓      ✗
  users                500             UUID           ✗      ✗
  departments          100             UUID           ✗      ✗
  attachments          1,000,000       UUID           ✗      ✗
  audit_logs           5,000,000       UUID           ✗      ✓
  archive_logs         500,000         UUID           ✗      ✓
  backup_logs          10,000          UUID           ✗      ✓
  system_config        100             KEY (str)      ✗      ✗
  templates            20              UUID           ✗      ✗
  plugins              50              UUID           ✗      ✗
  integration_config   10              UUID           ✗      ✗
  letter_fts           N/A             rowid          ✓      N/A
```

## Appendix B: Schema Version History

```
  Version   Migration ID     Description
  ────────────────────────────────────────────────────────────
  1         001              Create initial tables
  2         002              Add language field to letters
  3         003              Add hash_sha256 to attachments
  ...
```

## Appendix C: Canonical Letter JSON (for hashing)

```json
{
  "id": "3a1b2c3d-4e5f-6789-0abc-def012345678",
  "number": "MOH-2026-0042",
  "subject": "طلب تخصيص ميزانية إضافية",
  "body": "نحيطكم علماً بأن...",
  "sender_name": "د. علي أحمد",
  "sender_title": "مدير عام",
  "recipient_name": "وزارة المالية",
  "recipient_title": "السيد الوزير",
  "recipient_dept": "دائرة الموازنة",
  "department_id": "b2c3d4e5-6f78-90ab-cdef-0123456789ab",
  "priority": "HIGH",
  "status": "SENT",
  "reference_number": "REF-2025-001",
  "language": "AR"
}
```

---

*This domain model and database design document is a living artifact. All schema changes must be reflected here and approved through the governance process. Every migration must update this document.*
