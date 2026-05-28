# Deployment Documentation

This directory contains the deployment architecture for the
Correspondence System.

## Contents

| Document | Description |
|----------|-------------|
| `ARCHITECTURE.md` | Full deployment architecture, build system, directory layouts |
| This file | Entry point and index |

## Quick Start

### Development

```bash
# Run tests
python -m pytest

# Run linter
ruff check app tests

# Start application (headless)
python -m app.main
```

### Building

```bash
# Install build dependencies
pip install -r scripts/requirements-build.txt

# Build portable ZIP
python scripts/make.py build-portable --version 1.0.0

# Validate build
python scripts/make.py validate --path ./dist/OfflineCorrespondenceSystem_Portable_1.0.0.zip
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete documentation.
