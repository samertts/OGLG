# Development Rules

## Bounded Subsystem Execution

All development follows bounded stages. Each stage:

1. Targets **exactly one** subsystem
2. Implements **one logical change** per commit
3. Validates with **targeted** tests only
4. Never runs full-suite validation during iteration

## Anti-Freeze Rules

If any command produces no output for 15 seconds or exceeds 30 seconds:

1. Stop the command immediately
2. Summarize current progress
3. Continue from the last successful micro-step
4. Never restart completed work

## Low-Context Strategy

- Work on one file at a time within the active subsystem
- Never reread validated modules
- Never scan the repository recursively
- Never analyze unrelated services
- Keep execution context limited to the current numbering/workflow subsystem

## Localized Validation

- Run `pytest <target_file> -q --tb=short` — never full-suite
- Run `ruff check <target_file>` — never project-wide
- Reuse existing contracts, validators, and transaction helpers

## Micro-Commit Workflow

1. Implement the change
2. Run targeted tests
3. Run targeted lint
4. Stage only changed files (never unrelated modifications)
5. Commit with semantic message
6. Push immediately

## Performance Safety

- Maximum command runtime: 30 seconds
- No recursive file scans during development
- No automatic lint/test on every file save
- Manual invocation only

## Forbidden Patterns

- Placeholder logic (use NotImplementedError or ABC)
- Fake/mock repositories in production code
- Temporary architecture that bypasses clean layering
- Cross-subsystem changes in a single commit
- Internet-dependent code paths
- Magic numbers and hardcoded configuration
