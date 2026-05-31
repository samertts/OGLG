Windows Native Build
====================

This document describes how to produce a **native Windows PE executable**
on a Windows 10 or Windows 11 host.

Prerequisites
-------------

1. **Windows 10/11** (x86-64) — the build must run on Windows;
   cross-compilation from Linux produces a Linux ELF binary, not a
   Windows PE executable.

2. **Python 3.10+** installed from python.org (ensure "Add Python to
   PATH" is checked).

3. **Git** for cloning the repository.

4. **PowerShell 5.1+** (comes with Windows 10/11).

Build Steps
-----------

Run the following in **PowerShell** as a normal (non-admin) user:

```powershell
# 1. Clone the repository
git clone <repository-url> OGLG
cd OGLG

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 4. Prepare assets
mkdir assets 2>$null
# Copy or generate assets/icon.ico (a valid ICO file is required)
# The icon.ico from this repository works directly.

# 5. Build the executable
pyinstaller --windowed --onefile --name "GovernmentPlatform" `
    --icon assets\icon.ico `
    --add-data "config;config" `
    --add-data "assets;assets" `
    --add-data "alembic;alembic" `
    main.py

# 6. Verify the output
dir dist\GovernmentPlatform.exe

# 7. (Optional) Run a quick smoke test
dist\GovernmentPlatform.exe --help
```

Output
------

The single-file executable is placed at:

```
dist\GovernmentPlatform.exe
```

It can be deployed to any Windows machine without Python installed.

Notes
-----

- `--onefile` produces a single `.exe`; `--onedir` (default) produces a
  `dist\GovernmentPlatform\` directory with faster startup.
- Windows Defender may flag the first run; this is normal for PyInstaller
  builds. Submit the file to Microsoft if needed.
- Arabic RTL fonts must be bundled via `--add-data` if they are not
  installed system-wide.
- For a portable (directory) build that supports profile-based
  configuration, use `--onedir` instead of `--onefile`.
