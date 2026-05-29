# OGLG — Government Correspondence System

Offline-first, production-grade correspondence management for Iraqi governmental institutions. Built for long-term institutional deployment with SQLite/WAL durability, clean architecture, and zero online dependencies.

## Mission

Deliver a stable, recoverable, offline-capable correspondence system that operates on standard governmental hardware (Windows 7–11, 4GB RAM) without internet connectivity. The system prioritizes data integrity, transactional safety, and long-term maintainability over rapid feature expansion.

## Philosophy

- **Offline-first** — all core functionality works without internet
- **Clean architecture** — strict layering, no circular dependencies
- **Transactional safety** — atomic writes, WAL journaling, crash recovery
- **Government-grade** — stability, auditability, recoverability
- **Ministry-scale** — designed for cross-ministry federation

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Database | SQLite 3 (WAL mode) |
| ORM | SQLAlchemy 2.0 |
| GUI | tkinter (ttk themed) |
| Search | FTS5 |
| PDF | python-doctr |
| Logging | loguru |
| Linting | ruff |
| Testing | pytest |

## Repository Structure

```
app/
  core/            Domain entities, value objects, enums
  application/     Services, orchestrators, numbering engine
  infrastructure/  SQLAlchemy repos, FTS5, PDF engine
  ui/              tkinter views and controllers
  database/        Connection management, migrations
tests/
  unit/            Pure logic, no IO
  integration/     Database and service integration
docs/              Architecture, deployment, governance
```

## Installation

```bash
git clone https://github.com/samertts/OGLG.git
cd OGLG
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest tests/               # Verify installation
```

## Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run linter
ruff check app tests

# Run type checker
mypy app
```

## SQLite / WAL Notes

- WAL journal mode is mandatory — set via `PRAGMA journal_mode=WAL`
- `busy_timeout` set to 5000ms for concurrent access
- Foreign keys enforced via `PRAGMA foreign_keys=ON`
- All allocation is atomic via BEGIN IMMEDIATE semantics
- Recovery: integrity_check on startup, WAL auto-checkpoint

## Arabic RTL Support

The UI supports Arabic right-to-left rendering. All ttk widgets are configured for RTL layout when the system locale is Arabic.

## Deployment Modes

- **Portable** — single ZIP, runs without installation
- **Installed** — Windows installer, Start Menu integration
- Both support offline-only operation

## Roadmap

- [x] Core numbering engine (deterministic, atomic)
- [x] Workflow engine with state machine
- [ ] Concurrent-safe allocation
- [ ] Recovery and integrity validation
- [x] FTS5 full-text search
- [x] PDF generation and printing
- [ ] Ministry federation numbering
- [ ] Audit reconciliation
- [ ] Archive linkage

## License

Proprietary — Iraqi Government Institutional Use.
