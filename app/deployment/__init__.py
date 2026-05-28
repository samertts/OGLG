"""Windows deployment runtime support for the Correspondence System.

Handles PyInstaller-aware path resolution, platform detection,
startup validation, crash recovery, and RTL font management.
"""

from app.deployment.fonts import (
    FontManager,
    get_bundled_fonts,
    register_application_fonts,
)
from app.deployment.paths import (
    get_data_dir,
    get_deploy_mode,
    get_runtime_dir,
    resolve_bundled_path,
)
from app.deployment.platform import (
    PlatformInfo,
    detect_platform,
    is_windows_7_compatible,
    is_windows_8_compatible,
    is_windows_10_compatible,
    is_windows_11_compatible,
)
from app.deployment.validation import (
    DeploymentValidationResult,
    run_startup_validation,
    validate_directory_structure,
    validate_disk_space,
    validate_font_availability,
    validate_sqlite_integrity,
)

__all__ = [
    "get_deploy_mode",
    "get_runtime_dir",
    "get_data_dir",
    "resolve_bundled_path",
    "PlatformInfo",
    "detect_platform",
    "is_windows_7_compatible",
    "is_windows_8_compatible",
    "is_windows_10_compatible",
    "is_windows_11_compatible",
    "DeploymentValidationResult",
    "run_startup_validation",
    "validate_directory_structure",
    "validate_sqlite_integrity",
    "validate_font_availability",
    "validate_disk_space",
    "FontManager",
    "get_bundled_fonts",
    "register_application_fonts",
]
