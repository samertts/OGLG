# Contributing

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for the full contribution guidelines.

## Quick Reference

### Bounded Subsystem Execution

Work is organized into bounded stages. Each stage:

1. Targets exactly one subsystem (e.g., numbering, workflow, attachment)
2. Implements one logical change (atomic allocation, concurrency, recovery)
3. Validates with targeted tests only — no full-suite runs during iteration
4. Commits independently with a semantic message

### Commit Strategy

```
feat(numbering): add atomic sqlite number allocation
fix(workflow): correct state transition on reject
docs(governance): add recovery documentation
```

### Validation

- **Lint**: `ruff check <file>` — targeted, not project-wide
- **Tests**: `pytest <target_test_file> -q --tb=short`
- **Never** run full pytest or full lint during active development

### Forbidden

- No placeholder logic
- No recursive refactoring
- No full-suite runs during bounded execution
- No cross-subsystem changes in a single commit
- No internet-dependent code paths
