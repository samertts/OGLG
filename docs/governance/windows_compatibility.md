# Windows Compatibility Governance

## Supported Versions

- **Windows 7/8/10/11**: Compatibility with Windows 7, 8, 10, and 11 is mandatory.

---

## Runtime Requirements

- **Minimal Dependencies**: Runtime dependencies MUST remain minimal.
- **No Admin Required**: No administrator privileges should be required after installation.
- **Lightweight Installer**: The installer MUST remain lightweight and stable.

---

## Deployment Flexibility

- **Portable Deployment**: Portable deployment SHOULD remain possible.
- **Standalone Executable**: The system MUST be deployable as a standalone executable via PyInstaller or equivalent.
- **No Registry Dependency**: Core operation MUST not depend on Windows registry entries.

---

## Printer Compatibility

- **Windows Print Stack**: Printing consistency MUST remain stable across Windows versions.
- **Governmental Printer Support**: Compatibility with governmental printers MUST be maintained.

---

## Future Scalability Notes

- Testing MUST be performed on all supported Windows versions before release.
- Windows 7 specific workarounds SHOULD be documented and flagged for future deprecation.
- Cross-platform (Linux) support SHOULD be considered but MUST NOT compromise Windows stability.
- PyInstaller build process SHOULD be automated and reproducible.
