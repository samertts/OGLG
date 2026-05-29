# Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/deployment/](docs/deployment/) for full deployment documentation.

## Modes

### Portable

Single ZIP archive. Extract and run. No installation required. All data stored in the application directory.

### Installed

Windows installer (NSIS or similar). Creates Start Menu entry. Data stored in `%APPDATA%` by default.

## Requirements

- Windows 7–11 (64-bit recommended)
- 4GB RAM minimum
- 500MB disk space (plus data)
- No internet connection required
- No admin rights required for portable mode

## SQLite Deployment

- Database file created automatically on first run
- WAL journal mode applied at connection time
- Backup: copy database file while application is closed
- Migration: schema version tracked in `_migrations` table

## Printer Compatibility

- Windows GDI print API
- Supports all printers available to the OS
- RTL printing validated for Arabic correspondence
