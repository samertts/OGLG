# Security Policy

This document outlines the security posture for the Government Correspondence System. For the full vulnerability reporting process, see [.github/SECURITY.md](.github/SECURITY.md).

## Principles

- **Offline-first** — no cloud dependencies, no remote attack surface
- **Local data isolation** — all data stored locally in SQLite with WAL journaling
- **Deterministic operations** — no external API calls during normal operation
- **Audit trail** — all numbering and state transitions are logged immutably

## Data Protection

- Correspondence data never leaves the local machine
- SQLite database files are self-contained; no network services required
- Attachment storage uses application-managed directory isolation
- Future: SQLite encryption via `sqlcipher` or similar

## Transaction Safety

- All write operations use atomic transactions
- WAL mode provides crash recovery without data loss
- Sequence allocation uses BEGIN IMMEDIATE to prevent deadlocks
- Rollback on any failure preserves database consistency

## Reporting

See [.github/SECURITY.md](.github/SECURITY.md) for the full disclosure policy.
