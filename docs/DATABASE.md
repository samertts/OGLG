# Database Governance

- SQLite is the single source of truth.
- Direct destructive schema changes are forbidden.
- All schema modifications MUST use migrations.
- Migration rollback support is mandatory.
- Transaction safety is mandatory.
- Atomic operations are mandatory.
- Database corruption prevention has highest priority.
- Silent data deletion is forbidden.
- Archived records MUST remain immutable.
- Backup compatibility MUST be preserved across versions.
- Future migration compatibility MUST be considered.
- Shared database coupling with external systems is forbidden.
