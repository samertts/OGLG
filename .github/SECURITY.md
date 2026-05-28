# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Correspondence System manages sensitive government correspondence.
Security is the highest priority.

**Do not file a public GitHub issue for security vulnerabilities.**

Instead, report via private channels:

1. **GitHub Security Advisories:** Use the "Report a Vulnerability" button
   under the repository's Security tab.
2. **Email:** Contact the repository maintainers directly at the address
   listed in the commit history.

You should receive an acknowledgment within 48 hours. A fix timeline will
be provided based on severity.

## Scope

This policy covers:

- The application runtime and its dependencies
- SQLite database storage and encryption
- File system operations and data isolation
- Portable and installed deployment modes
- Authentication and authorisation flows
- Audit log integrity

Out of scope:

- Operating system security (assume host is trusted)
- Physical access to the machine
- Third-party libraries (report upstream)

## Disclosure Policy

- Vulnerabilities are disclosed after a fix is released
- A CVE identifier will be requested when appropriate
- Credit is given to the reporter unless anonymity is requested
