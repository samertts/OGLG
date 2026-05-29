# Performance Guidelines

## Startup Performance

- Target: under 3 seconds on standard governmental hardware
- Database open and integrity check must complete within 1 second
- UI must be responsive within 2 seconds of launch
- Lazy-load non-critical subsystems (search, archive)

## SQLite Optimization

- WAL journal mode for concurrent read/write performance
- `synchronous = NORMAL` balances safety and speed
- `cache_size = -8000` (8MB cache) for typical workloads
- `temp_store = MEMORY` for temporary table performance
- `mmap_size = 268435456` (256MB) for large database access

## Low-Resource Optimization

- Minimum target: 4GB RAM, 2 CPU cores
- Database connection pool limited to 1 writer + readers
- No background threads during idle periods
- Lazy initialization of expensive subsystems
- Memory-mapped I/O for database files

## UI Responsiveness

- All database writes must complete within 100ms
- Long-running operations (PDF generation, backups) must not block the UI
- Background tasks use a dedicated thread pool
- Progress reporting required for operations exceeding 2 seconds

## FTS5 Performance

- Full-text search indexes updated asynchronously
- Search queries timeout after 10 seconds
- Result sets limited to 1000 rows per query
- Index rebuild scheduled during low-activity periods

## Attachment Indexing

- File scanning uses background thread with configurable batch size
- Deduplication via content hash to avoid redundant indexing
- Thumbnail generation cached to disk

## Anti-Freeze Philosophy

- No operation should block the event loop for more than 200ms
- All I/O operations have configurable timeouts
- If an operation exceeds its timeout, it is cancelled gracefully
- The system must remain responsive even under high load
