# Contributing to the Correspondence System

## Philosophy

This is an **offline-first, government-grade** correspondence management system.
Every contribution must preserve:

- **Offline capability** — no hard external dependencies at runtime
- **Data integrity** — atomic writes, crash recovery, audit trails
- **Windows 7–11 compatibility** — broad deployment target
- **Portable + installed modes** — dual deployment strategy
- **Clean architecture** — strict layering, no circular dependencies

## Getting Started

```bash
git clone https://github.com/anomalyco/oglg.git
cd oglg
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest tests/              # verify everything works
```

## Development Workflow

1. **Pick an issue** or create one describing your intent.
2. **Create a feature branch** following branch governance rules.
3. **Write tests first** where feasible (TDD encouraged).
4. **Implement** with full type hints and structured logging.
5. **Run the full test suite** — all tests must pass.
6. **Run lint and format** — `ruff check . && ruff format .`.
7. **Commit** using semantic commit messages.
8. **Push and open a pull request.**

## Code Standards

- Python 3.12+ syntax
- Strict type hints on all public APIs
- Dataclasses for value objects and DTOs
- Structured logging via `loguru`
- No wildcard imports (`from module import *`)
- No `print()` in production code (use logger)
- No bare `except:` clauses
- Atomic filesystem operations only

## Testing

- Unit tests in `tests/unit/` — pure logic, no IO
- Integration tests in `tests/integration/` — database, services
- Run all tests: `pytest tests/ -v`
- Aim for > 90 % coverage on new code

## Review Process

All submissions require review from at least one maintainer.
Reviewers check:

- Correctness and test coverage
- Adherence to architecture and offline-first philosophy
- Security implications
- Deployment impact (portable / installed modes)
- Documentation completeness

## Questions

Open a discussion or ask in the issue tracker.
