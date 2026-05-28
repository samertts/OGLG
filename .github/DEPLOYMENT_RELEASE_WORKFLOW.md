# Deployment and Release Workflow

## Overview

The Correspondence System supports two deployment modes:

1. **Portable Mode** — self-contained directory, no installation
2. **Installed Mode** — Windows Installer (MSI/EXE), system-wide

Both modes produce the same application with different data directory
strategies.

## Build Pipeline

```
Source Code
    │
    ▼
PyInstaller ───────────► Portable ZIP
    │                        │
    ▼                        ▼
    │              build_portable.py
    │              - creates oglg.exe
    │              - bundles assets
    │              - generates checksums
    │
    ▼
Inno Setup ─────────────► Windows Installer
    │                        │
    ▼                        ▼
    │              build_installer.py
    │              - wraps portable ZIP
    │              - adds install/uninstall logic
    │              - signs installer (if configured)
```

## CI/CD Triggers

| Trigger              | Action                        | Artifacts           |
|----------------------|-------------------------------|---------------------|
| Push to `main`       | Validation only (tests, lint) | None                |
| Tag `v*.*.*`         | Full build + release          | ZIP + Installer     |
| `workflow_dispatch`  | Manual build with version     | ZIP + Installer     |

## Validation Steps

Every build runs:

1. Unit tests (`pytest tests/unit/`)
2. Integration tests (`pytest tests/integration/`)
3. Build artifact validation (`validate_build.py`)
4. Checksum verification

## Release Process

1. Version is determined from tag (`v1.2.3` → `1.2.3`)
2. CI builds portable ZIP and installer
3. Artifacts are uploaded as build artifacts
4. On tag pushes, a GitHub Release is created (draft)
5. Release notes are auto-generated
6. Manual review before publishing

## Manual Build

```bash
# Build portable ZIP
python build/build_portable.py --version 1.0.0

# Build installer (requires Inno Setup on Windows)
python build/build_installer.py --version 1.0.0

# Validate artifacts
python build/validate_build.py --zip dist/oglg_Portable_1.0.0.zip
python build/validate_build.py --installer dist/oglg_Installer_1.0.0.exe
```
