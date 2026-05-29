# Backup and Recovery

## Philosophy

The system prioritizes data integrity over performance. Every write is transactional, every transaction is atomic, and every atomic operation is recoverable.

## WAL Recovery

- WAL (Write-Ahead Log) journal mode is mandatory
- On crash, SQLite automatically replays the WAL on next connection
- No manual recovery steps required for standard crashes
- WAL checkpoint runs automatically at configurable intervals

## Backup Workflow

1. Close the application (or ensure no writes are in progress)
2. Copy the SQLite database file (`correspondence.db`)
3. Copy the WAL file (`correspondence.db-wal`) if present
4. Copy the `attachments/` directory for full backup
5. Store backup in a secure location

## Restore Workflow

1. Close the application
2. Replace the database file with the backup
3. Delete any existing WAL and SHM files (they will be recreated)
4. Start the application — integrity check runs automatically

## Crash Recovery

- On startup, `PRAGMA integrity_check` validates database health
- If corruption is detected: log the error, attempt recovery from WAL, notify administrator
- WAL replay is automatic — no data loss from crashes
- RecoveryValidationHook interface available for custom recovery logic

## Orphan Cleanup

- Orphaned sequence entries are detected during startup validation
- Attachments without corresponding letter records are flagged
- Recovery service provides tools for orphan resolution

## Deterministic Recovery Ordering

1. Open database (auto WAL replay)
2. Run integrity check
3. Validate schema version
4. Detect and flag orphans
5. Apply any pending migrations
6. Initialize subsystems
7. Start application
