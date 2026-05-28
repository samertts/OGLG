# Release Checklist

## Pre-Release

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No lint errors: `ruff check .`
- [ ] Formatting clean: `ruff format --check .`
- [ ] Type checks pass: `mypy app/`
- [ ] CHANGELOG updated with all user-facing changes
- [ ] Version bumped in `pyproject.toml` and `app/__init__.py`
- [ ] Migration revisions checked (no uncommitted migrations)
- [ ] All governance documents up to date

## Build

- [ ] Build portable ZIP: `python build/build_portable.py --version X.Y.Z`
- [ ] Build installer (Windows): `python build/build_installer.py --version X.Y.Z`
- [ ] Validate portable ZIP: `python build/validate_build.py --zip dist/*.zip`
- [ ] Validate installer: `python build/validate_build.py --installer dist/*.exe`
- [ ] Generate checksums
- [ ] Verify checksums match

## Testing

- [ ] Test portable mode on Windows 10 / 11
- [ ] Test portable mode on Windows 7 / 8 (if available)
- [ ] Test installed mode on Windows
- [ ] Test database migration from previous version
- [ ] Test crash recovery (kill process, restart)
- [ ] Verify audit log integrity after recovery
- [ ] Test backup / restore cycle
- [ ] Test with Arabic locale and fonts

## Release

- [ ] Tag commit: `git tag vX.Y.Z && git push origin vX.Y.Z`
- [ ] GitHub Release created automatically (or manually)
- [ ] Release notes written and reviewed
- [ ] Draft release published
- [ ] Release announcement sent

## Post-Release

- [ ] Verify release artifacts downloadable
- [ ] Verify release checksums match
- [ ] Update documentation branch if needed
- [ ] Close related milestone in issue tracker
