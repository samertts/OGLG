# Database Governance

## Data Authority

- **Single Source of Truth**: SQLite is the single source of truth.
- **No Shared Coupling**: Shared database coupling with external systems is forbidden.

---

## Schema Management

- **No Destructive Changes**: Direct destructive schema changes are forbidden.
- **Migration Required**: All schema modifications MUST use migrations.
- **Rollback Support**: Migration rollback support is mandatory.
- **Future Compatibility**: Future migration compatibility MUST be considered.

---

## Transaction Safety

- **Transaction Safety**: Transaction safety is mandatory.
- **Atomic Operations**: Atomic operations are mandatory.
- **Corruption Prevention**: Database corruption prevention has highest priority.

---

## Data Integrity

- **No Silent Deletion**: Silent data deletion is forbidden.
- **Immutable Archives**: Archived records MUST remain immutable.
- **Backup Compatibility**: Backup compatibility MUST be preserved across versions.

---

## Future Scalability Notes

- Migration framework MUST support forward and backward migration paths.
- Schema versioning SHOULD be embedded in the database itself for automatic compatibility checking.
- Future read-replica or archival database support MUST NOT alter the core migration system.
- Integration with Gula or laboratory platforms MUST use API/service layers — never direct database sharing.
