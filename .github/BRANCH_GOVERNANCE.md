# Branch Governance

## Branch Structure

```
main                    Production-ready, protected
├── develop             Integration branch (future use)
├── feat/*              Feature branches
├── fix/*               Bug fix branches
├── chore/*             Maintenance branches
├── docs/*              Documentation branches
├── release/*           Release preparation branches
└── hotfix/*            Urgent production fixes
```

## Rules

### `main`
- **Protected** — no direct pushes
- Merged only via pull request with review
- Must pass all CI checks
- Must have linear history (squash or rebase merge)

### Feature Branches (`feat/*`)
- Branch from `main`
- Merge back to `main` via PR
- Name: `feat/short-description` (e.g. `feat/pdf-export`)
- Must include tests for new functionality

### Fix Branches (`fix/*`)
- Branch from `main`
- Name: `fix/short-description` (e.g. `fix/crash-on-empty-db`)

### Release Branches (`release/*`)
- Branch from `main` when cutting a release
- Only bug fixes and release-prep commits
- Merged back to `main` and tagged

### Hotfix Branches (`hotfix/*`)
- Branch from the release tag
- Merged to `main` and any active release branch
- Used for critical production defects only

## Branch Naming Conventions

- Use lowercase
- Use hyphens as separators
- Keep under 50 characters
- Include issue number when applicable: `feat/123-pdf-support`

## Pull Request Requirements

- Title must follow [semantic commit conventions](COMMIT_CONVENTIONS.md)
- Description must explain what and why
- At least one reviewer must approve
- All CI checks must pass
- No merge commits (rebase or squash)
