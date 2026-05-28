# Deployment Governance

## Standalone Deployment

- **Executable Build**: The system MUST be deployable as standalone executable.
- **Simple Installation**: Installation MUST remain simple.
- **Stable Runtime**: Runtime environment MUST remain stable.
- **Portable Option**: Portable deployment SHOULD remain possible.
- **Data Integrity**: Updates MUST preserve data integrity.

---

## Distribution Requirements

- **Lightweight Installer**: The installer MUST remain lightweight and stable.
- **No Admin Required**: No administrator privileges should be required after installation.
- **Minimal Dependencies**: Runtime dependencies MUST remain minimal.

---

## Platform Support

- **Windows 7/8/10/11**: All listed Windows versions MUST be supported.
- **Portable Deployment**: Portable (USB-drive) deployment SHOULD remain possible.

---

## Update Management

- **Non-Destructive Updates**: Updates MUST NOT destroy or corrupt existing data.
- **Backward Compatibility**: Database and archive format compatibility MUST be preserved across updates where possible.
- **Rollback Support**: Deployment SHOULD support rollback to previous version in case of failure.

---

## Future Scalability Notes

- Deployment SHOULD support silent/unattended installation for institutional rollout.
- Version checking SHOULD compare data format versions, not just application versions.
- Network deployment (intranet push) SHOULD be considered for ministry-wide updates.
- Future auto-update mechanism MUST NOT require internet — SHOULD support local network update servers.
- Separate data directory from application directory to enable clean upgrades.
