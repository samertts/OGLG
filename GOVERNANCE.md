# Governance Model

## Principles

- **Stability first** — main branch is always deployable
- **Offline-first** — no dependency on external services or cloud
- **Clean architecture** — strict layer isolation, no circular dependencies
- **Transactional safety** — every write is atomic, recoverable, and auditable
- **Ministry-scale** — subsystems are designed for cross-ministry federation

## Authority

The maintainer has architectural authority over:

- Module boundaries and dependency direction
- Database schema and migration strategy
- Public API contracts between subsystems
- Deployment and release governance

## Review Workflow

1. Contributor opens a pull request against a feature branch
2. Automated checks: lint, targeted tests, security scan
3. Maintainer reviews architecture compliance, test coverage, documentation
4. Merge requires: passing checks, maintainer approval, no unresolved discussions

## Release Governance

- Releases follow semantic versioning
- Breaking changes require a major version bump and migration path
- Database migrations must be backward-compatible within a major version
- Release notes must document all API changes, schema migrations, and deprecations

## Compatibility Guarantees

- Windows 7–11 support is guaranteed for all releases
- SQLite database format is stable — no silent format changes
- Public service interfaces maintain backward compatibility within major versions
- Config file format is versioned and validated on startup
