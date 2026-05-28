# Semantic Commit Conventions

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

| Type       | Usage                                              |
|------------|----------------------------------------------------|
| `feat`     | A new feature                                      |
| `fix`      | A bug fix                                          |
| `docs`     | Documentation only changes                         |
| `style`    | Formatting, missing semicolons, etc (no logic)     |
| `refactor` | Code change that neither fixes nor adds a feature  |
| `perf`     | Performance improvement                            |
| `test`     | Adding or correcting tests                         |
| `chore`    | Build, CI, dependencies, tooling                   |
| `ci`       | CI/CD configuration changes                        |
| `revert`   | Revert a previous commit                           |

## Scopes

| Scope             | Area                                      |
|-------------------|-------------------------------------------|
| `runtime`         | Application lifecycle and state machine   |
| `bootstrap`       | DI container and startup wiring           |
| `database`        | Models, migrations, connection            |
| `storage`         | File operations, atomic writes            |
| `deployment`      | Packaging, portable/installed modes       |
| `diagnostics`     | Environment checks, readiness validation  |
| `security`        | Signing, hashing, audit integrity         |
| `logging`         | Logging configuration and rotation        |
| `config`          | Settings, defaults, user config           |
| `gui`             | Desktop user interface                    |
| `pdf`             | PDF generation                            |
| `ai`              | AI assistant integration                  |
| `infrastructure`  | Repository, CI, project structure         |
| `docs`            | Documentation                             |
| `tests`           | Test suite                                |

## Examples

```
feat(runtime): add lifecycle event logging with timestamps
fix(database): handle connection timeout during startup
docs(deployment): document portable vs installed mode paths
chore(infrastructure): add ruff lint configuration
test(storage): add atomic write concurrency tests
```

## Rules

- **Imperative mood** — "add" not "added" or "adds"
- **No period** at end of subject line
- **Subject < 72 characters**
- **Body wraps at 72 characters**
- **Scope is optional** for trivial changes
- **Breaking changes** add `BREAKING CHANGE:` in footer
