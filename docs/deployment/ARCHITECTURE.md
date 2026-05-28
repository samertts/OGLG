# Windows Packaging and Deployment Architecture
#
# This document describes the production-grade Windows executable
# packaging and deployment system for the Iraqi Government Offline
# Official Correspondence System.

---

## Overview

The deployment system supports two modes:

- **Portable mode** — USB/air-gapped deployment, data alongside executable
- **Installed mode** — Windows installed deployment, data in AppData

Both modes use the same PyInstaller-built executable, with a
`portable.txt` marker file distinguishing the modes at runtime.

---

## Directory Structure

### Installed Mode (`%LOCALAPPDATA%\OGLG\`)

```
OfflineCorrespondenceSystem/
├── OfflineCorrespondenceSystem.exe   # Main executable
├── runtime/                           # Python runtime DLLs
├── assets/
│   ├── fonts/                         # Bundled Arabic fonts
│   ├── icons/                         # Application icons
│   └── templates/                     # QWebEngine/Jinja2 templates
├── config/
│   └── defaults.json                  # Bundled default configuration
├── migrations/                        # Alembic migration scripts
├── plugins/                           # Plugin registry directory
├── data/
│   ├── database/correspondence.db     # SQLite database
│   ├── archives/                      # Archived letters
│   ├── backups/                       # Database backups
│   ├── logs/                          # Structured logs (rotation)
│   ├── temp/                          # Temporary files
│   ├── attachments/                   # Letter attachments
│   └── generated_letters/             # Generated PDF output
```

### Portable Mode (`<USB>/\{appname}_Portable/`)

```
OfflineCorrespondenceSystem_Portable/
├── OfflineCorrespondenceSystem.exe
├── portable.txt                       # Mode marker file
├── runtime/
├── assets/
├── config/
├── migrations/
├── plugins/
└── data/
    ├── database/
    ├── archives/
    ├── backups/
    ├── logs/
    ├── temp/
    ├── attachments/
    └── generated_letters/
```

---

## Build System

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| PyInstaller spec | Executable packaging | `build/oglg.spec` |
| Inno Setup script | Windows installer | `build/setup.iss` |
| Portable build script | ZIP distribution builder | `build/build_portable.py` |
| Installer build script | Inno Setup compiler wrapper | `build/build_installer.py` |
| Build validation | Artifact integrity checks | `build/validate_build.py` |
| Task runner | Developer convenience commands | `scripts/make.py` |
| Release script | GitHub release notes | `scripts/release.py` |
| CI/CD pipeline | Automated GitHub Actions builds | `.github/workflows/build.yml` |

### Build Requirements

```bash
pip install -r requirements.txt
pip install -r scripts/requirements-build.txt
```

### Building

```bash
# Portable ZIP distribution
python scripts/make.py build-portable --version 1.0.0

# Windows installer (requires Inno Setup)
python scripts/make.py build-installer --version 1.0.0

# Validate build artifacts
python scripts/make.py validate --path ./dist/OfflineCorrespondenceSystem_Portable_1.0.0.zip

# Run all tests
python scripts/make.py test --coverage

# Run linter
python scripts/make.py lint
```

---

## Deployment Validation

The startup validation (step 2 of the lifecycle) checks:

1. **Directory structure** — all required data directories exist
2. **Disk space** — at least 100 MB free
3. **Font availability** — Arabic RTL fonts are bundled
4. **Platform compatibility** — Windows 7+ detection
5. **SQLite integrity** — database integrity check on existing DB

Validation can be bypassed with `--skip-validation` for development.

---

## Arabic RTL Fonts

### Bundled Fonts

| Font | File | Style |
|------|------|-------|
| Amiri | `Amiri-Regular.ttf` | Regular |
| Amiri | `Amiri-Bold.ttf` | Bold |
| Amiri | `Amiri-Italic.ttf` | Italic |
| Noto Naskh Arabic | `NotoNaskhArabic-Regular.ttf` | Regular |
| Noto Naskh Arabic | `NotoNaskhArabic-Bold.ttf` | Bold |
| Traditional Arabic | `TraditionalArabic.ttf` | Regular |

### Font Registration

On Windows, fonts are registered via `AddFontResourceEx` with the
`FR_PRIVATE` flag, making them available only to the application
process without system-wide installation.

Arabic RTL rendering corruption is treated as a **critical deployment
failure**.

---

## Database Integrity

- SQLite WAL mode enabled at all times
- `PRAGMA integrity_check` runs at startup
- VACUUM attempted as first recovery step
- Atomic writes prevent partial overwrite corruption
- Database, backups, and archives are strictly separated

---

## Installer Features

The Inno Setup installer (built from `build/setup.iss`):

| Feature | Description |
|---------|-------------|
| Per-user installation | No admin rights required |
| Portable mode option | User selects at install time |
| Desktop shortcut | Optional, during install |
| Start menu shortcut | Always created |
| Safe uninstall | Data preserved by default, user prompted before deletion |
| Upgrade support | Data directories preserved during reinstall |
| Windows 7–11 | `MinVersion=6.1` |
| Arabic language | Inno Setup Arabic translation included |

---

## Release Process

1. Tag the release: `git tag v1.0.0 && git push origin v1.0.0`
2. CI/CD workflow automatically:
   - Runs validation and tests
   - Builds the PyInstaller executable
   - Creates portable ZIP distribution
   - Generates SHA-256 checksums
   - Creates a draft GitHub Release
3. Manually:
   - Build the Inno Setup installer
   - Verify artifacts
   - Publish the release

### Release Artifacts (GitHub Releases)

| Artifact | Description |
|----------|-------------|
| `OfflineCorrespondenceSystem_Portable_{ver}.zip` | Portable ZIP distribution |
| `OfflineCorrespondenceSystem_Portable_{ver}.sha256.txt` | SHA-256 checksum |
| `OfflineCorrespondenceSystem_Setup_{ver}.exe` | Windows installer |
| `OfflineCorrespondenceSystem_Setup_{ver}.exe.sha256.txt` | SHA-256 checksum |

---

## Code Signing Preparation

The architecture is compatible with future code signing without
redesign:

- The `app/deployment/signing.py` module provides hash computation
  and checksum manifest generation
- The PyInstaller spec includes `codesign_identity` parameter
- The build validation script supports integrity verification
- Signing can be integrated into the CI/CD pipeline

---

## Update Safety

| Operation | Data Preserved |
|-----------|---------------|
| Minor update | Yes — all data |
| Schema migration | Yes — automatic migration |
| Major upgrade | Yes — data directory separate |
| Uninstall | Prompted — default is preserve |
| Portable replacement | Yes — replace EXE, keep `data/` |

---

---

## Runtime Subsystem (`app/runtime/`)

The runtime subsystem manages application lifecycle, state transitions,
crash recovery, and resource cleanup.

### Components

| Component | Purpose |
|-----------|---------|
| `state.py` | `RuntimeState` enum (9 states), `RuntimeStateMachine` with validated transitions |
| `lifecycle.py` | `LifecycleLogger` — structured startup event logging with timing |
| `recovery.py` | `CrashRecoveryBootstrap` — crash marker detection, DB integrity check, lock management |
| `cleanup.py` | `TempCleanupEngine` — age-based temp file removal; `BackupRotationEngine` — retention-based backup rotation |
| `archive.py` | `ArchiveDirectoryInitializer` — yearly/monthly/corrupted subdirectory creation |

### State Machine Transitions

```
UNINITIALIZED → INITIALIZING → VALIDATING → STARTING → RUNNING
                                 ↕                         ↕
                              RECOVERING ←─────────────────┘
                                                   ↓
                                            SHUTTING_DOWN → STOPPED
                                                   ↓
                                                FAILED → UNINITIALIZED / RECOVERING
```

Invalid transitions raise `StateTransitionError`. The machine tracks
transition history for audit and diagnostics.

### Crash Recovery Sequence

1. Stale lock file detection (`app.lock` in temp dir, 30 min timeout)
2. SQLite `PRAGMA integrity_check` on existing database
3. VACUUM repair attempt on integrity failure
4. Stale temp file cleanup (>24 hours)
5. Stale archive `.tmp` file cleanup (>1 hour)
6. Lock file written for current session
7. Lock cleared on clean shutdown via signal handler

---

## Diagnostics Subsystem (`app/diagnostics/`)

The diagnostics subsystem validates the runtime environment and
deployment readiness at startup.

### Components

| Component | Purpose |
|-----------|---------|
| `environment.py` | `EnvironmentVerifier` — runs 6 checks (Python, SQLite, disk, RAM, encoding, display DPI) |
| `readiness.py` | `DeploymentReadinessValidator` — 3-tier validation (CRITICAL/WARNING/INFO), readiness score |
| `report.py` | `EnvironmentDiagnosticsReport` — structured diagnostic report with health score |
| `startup.py` | `StartupDiagnosticsEngine` — orchestrates phased diagnostics with lifecycle integration |

### Readiness Tiers

| Tier | Weight | Effect |
|------|--------|--------|
| **CRITICAL** | 3.0 | Blocking — application will not start |
| **WARNING** | 1.0 | Degraded — non-blocking, logged |
| **INFO** | 0.5 | Advisory — informational only |

Readiness score: 0.0 (unusable) to 1.0 (fully ready). A score < 1.0
with zero critical failures allows degraded startup.

### Startup Integration

The diagnostics engine integrates with the lifecycle logger to
track duration of each diagnostic phase:

```python
engine = StartupDiagnosticsEngine(
    env_verifier=env_verifier,
    readiness_validator=readiness_validator,
    lifecycle=lifecycle,
)
result = engine.run_diagnostics()
```

---

## Governance Compliance

This deployment architecture strictly follows all rules from the
project governance documents:

- ✅ Full offline operation — no internet dependency
- ✅ Windows 7–11 compatibility — `MinVersion=6.1`
- ✅ Portable + installed modes — single executable
- ✅ Arabic RTL — bundled fonts + private registration
- ✅ SQLite integrity — WAL + PRAGMA + atomic writes
- ✅ No Electron / Docker / WebView
- ✅ No Python preinstalled requirement
- ✅ User data never packaged inside builds
- ✅ Recovery-safe updates — data preserved
- ✅ GitHub-based release management
