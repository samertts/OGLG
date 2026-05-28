"""Windows deployment runtime support for the Correspondence System.

Handles PyInstaller-aware path resolution, platform detection,
startup validation, crash recovery, RTL font management, and
deployment mode detection (portable / installed / development).
"""

from app.deployment.asset_validator import AssetValidationResult, AssetValidator
from app.deployment.fonts import (
    FontManager,
    get_bundled_fonts,
    register_application_fonts,
)
from app.deployment.install_detector import InstallDetectionResult, InstallDetector
from app.deployment.path_strategy import (
    DevelopmentPathStrategy,
    InstalledPathStrategy,
    PathStrategy,
    PortablePathStrategy,
    get_path_strategy,
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
from app.deployment.portable_detector import PortableDetectionResult, PortableDetector
from app.deployment.runtime_layout import (
    RuntimeLayout,
    create_runtime_layout,
    get_standard_layout,
    is_layout_complete,
)
from app.deployment.user_data_initializer import InitResult, UserDataInitializer
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
    "PortableDetector",
    "PortableDetectionResult",
    "InstallDetector",
    "InstallDetectionResult",
    "RuntimeLayout",
    "create_runtime_layout",
    "get_standard_layout",
    "is_layout_complete",
    "PathStrategy",
    "DevelopmentPathStrategy",
    "PortablePathStrategy",
    "InstalledPathStrategy",
    "get_path_strategy",
    "AssetValidator",
    "AssetValidationResult",
    "UserDataInitializer",
    "InitResult",
]
