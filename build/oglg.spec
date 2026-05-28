# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Correspondence System.
#
# Build modes:
#   one-folder deployment with controlled asset bundling.
#
# Usage:
#   pyinstaller build/oglg.spec
#

import os
import sys
from pathlib import Path

BLOCK_CIPHER_KEY = None  # no encryption (government offline use)

# ---- Paths ----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
ASSETS_DIR = PROJECT_ROOT / "app" / "assets"
CONFIG_DIR = PROJECT_ROOT / "app" / "config"
MIGRATIONS_DIR = PROJECT_ROOT / "app" / "database" / "migrations"

# ---- Asset data files -----------------------------------------------------
# Fonts for Arabic RTL rendering
font_files = []
fonts_path = ASSETS_DIR / "fonts"
if fonts_path.is_dir():
    font_files = [
        (str(fonts_path), "assets/fonts")
        for f in fonts_path.rglob("*")
        if f.suffix.lower() in (".ttf", ".otf")
    ]

# Icon files
icon_files = []
icons_path = ASSETS_DIR / "icons"
if icons_path.is_dir():
    icon_files = [
        (str(icons_path), "assets/icons")
    ]

# Template files (QWebEngine / Jinja2 templates)
template_files = []
templates_path = ASSETS_DIR / "templates"
if templates_path.is_dir():
    template_files = [
        (str(templates_path), "assets/templates")
    ]

# Configuration defaults
config_files = [
    (str(CONFIG_DIR / "defaults.json"), "app/config"),
]

# Alembic migrations
migration_files = []
if MIGRATIONS_DIR.is_dir():
    migration_files = [
        (str(MIGRATIONS_DIR / "alembic.ini"), "app/database/migrations"),
    ]
    versions_dir = MIGRATIONS_DIR / "versions"
    if versions_dir.is_dir():
        migration_files.append((str(versions_dir), "app/database/migrations/versions"))
    env_py = MIGRATIONS_DIR / "env.py"
    if env_py.exists():
        migration_files.append((str(env_py), "app/database/migrations"))

# ---- Plugin registry stub -------------------------------------------------
plugin_files = []
plugins_installed = PROJECT_ROOT / "app" / "plugins" / "installed"
if plugins_installed.is_dir():
    plugin_files = [(str(plugins_installed), "app/plugins/installed")]

# ---- Collect all data files -----------------------------------------------
collected_datas = (
    font_files
    + icon_files
    + template_files
    + config_files
    + migration_files
    + plugin_files
)

# ---- Hidden imports -------------------------------------------------------
hidden_imports = [
    "alembic",
    "alembic.config",
    "alembic.command",
    "alembic.migration",
    "alembic.operations",
    "alembic.runtime.migration",
    "sqlalchemy",
    "sqlalchemy.ext.declarative",
    "sqlalchemy.orm",
    "sqlalchemy.sql",
    "loguru",
    "app",
    "app.config",
    "app.config.settings",
    "app.core",
    "app.core.enums",
    "app.core.exceptions",
    "app.core.entities",
    "app.core.repositories",
    "app.core.value_objects",
    "app.database",
    "app.database.connection",
    "app.database.models",
    "app.database.repositories",
    "app.deployment",
    "app.deployment.paths",
    "app.deployment.platform",
    "app.deployment.validation",
    "app.deployment.fonts",
    "app.deployment.signing",
    "app.services",
    "app.services.audit_service",
    "app.services.backup_service",
    "app.services.letter_service",
    "app.services.dto",
    "app.utils",
    "app.utils.logger",
    "app.utils.file_utils",
    "app.utils.paths",
    "app.utils.validators",
    "app.utils.helpers",
]

# ---- Exclusions -----------------------------------------------------------
excluded_modules = [
    "tkinter",
    "turtle",
    "test",
    "unittest",
    "distutils",
    "pip",
    "setuptools",
    "pdb",
    "pygments",
    "IPython",
    "matplotlib",
    "scipy",
    "numpy",
    "pandas",
    "bs4",
    "lxml",
    "PIL",
    "cv2",
    "zmq",
    "jedi",
    "parso",
    "black",
    "isort",
    "pytest",
    "nose",
]

# ---- Block cipher ---------------------------------------------------------
# No encryption for government offline deployment.
# Encryption adds complexity without benefit in air-gapped environments.

# ---- Analysis -------------------------------------------------------------
a = Analysis(
    [str(APP_DIR / "main.py")],
    pathex=[],
    binaries=[],
    datas=collected_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    noarchive=False,
    optimize=1,
)

# ---- PYZ (compressed Python archive) --------------------------------------
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=BLOCK_CIPHER_KEY,
)

# ---- Executable -----------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="OfflineCorrespondenceSystem",
    debug=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS_DIR / "icons" / "app.ico") if (ASSETS_DIR / "icons" / "app.ico").exists() else None,
)

# ---- One-directory COLLECT -------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name="OfflineCorrespondenceSystem",
)
