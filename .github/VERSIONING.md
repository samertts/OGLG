# Release Versioning Strategy

## Scheme

This project follows **Semantic Versioning 2.0.0**:

```
MAJOR.MINOR.PATCH
```

- **MAJOR** — incompatible API or data format changes
- **MINOR** — backward-compatible new functionality
- **PATCH** — backward-compatible bug fixes

## Pre-Release Suffixes

```
X.Y.Z-alpha.N   Internal / experimental
X.Y.Z-beta.N    Feature-complete, testing
X.Y.Z-rc.N      Release candidate
```

## Version Location

- Primary: `pyproject.toml` `[project] version`
- Canonical: `app/__init__.py` `__version__`
- Display: `oglg --version`

## Version Bump Process

1. Determine bump type from unreleased changes
2. Update `pyproject.toml` and `app/__init__.py`
3. Update `CHANGELOG.md` with release date
4. Commit: `chore(release): bump version to X.Y.Z`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push && git push --tags`

## Breaking Changes

A change is **breaking** if it requires user action:

- Database schema migration (non-additive)
- Data directory layout change
- Configuration file format change
- Removed CLI flags or arguments
- Changed default behaviour affecting existing data

Breaking changes increment MAJOR version and must be documented in
migration instructions.
