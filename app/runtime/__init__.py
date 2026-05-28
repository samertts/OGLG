"""Runtime management for the Correspondence System.

Provides the runtime state machine, lifecycle logging, crash recovery
bootstrap, temp/backup cleanup engines, archive initialization, and
runtime context management.
"""

from app.runtime.archive import ArchiveDirectoryInitializer
from app.runtime.archive_initializer import ArchiveInitializer, ArchiveInitResult
from app.runtime.cleanup import BackupRotationEngine, TempCleanupEngine
from app.runtime.crash_recovery import CrashRecoveryManager, RecoveryAction, RecoveryResult
from app.runtime.lifecycle import LifecycleEvent, LifecycleLogger
from app.runtime.path_resolver import PathResolver, create_path_resolver
from app.runtime.recovery import CrashRecoveryBootstrap
from app.runtime.runtime_context import (
    RuntimeContext,
    create_runtime_context,
    get_current_context,
    set_current_context,
)
from app.runtime.runtime_mode import RuntimeMode, detect_runtime_mode, is_frozen
from app.runtime.session_manager import SessionInfo, SessionManager, SessionState
from app.runtime.shutdown_manager import ShutdownManager, ShutdownResult
from app.runtime.startup_manager import StartupManager, StartupResult, StartupStep
from app.runtime.state import RuntimeState, RuntimeStateMachine, StateTransitionError
from app.runtime.state_machine import StateChangedEvent
from app.runtime.temp_cleanup import CleanupPolicy, CleanupResult, TempCleanupManager

__all__ = [
    "RuntimeMode",
    "detect_runtime_mode",
    "is_frozen",
    "RuntimeContext",
    "create_runtime_context",
    "get_current_context",
    "set_current_context",
    "RuntimeState",
    "RuntimeStateMachine",
    "StateTransitionError",
    "StateChangedEvent",
    "LifecycleLogger",
    "LifecycleEvent",
    "CrashRecoveryBootstrap",
    "CrashRecoveryManager",
    "RecoveryAction",
    "RecoveryResult",
    "TempCleanupEngine",
    "TempCleanupManager",
    "CleanupPolicy",
    "CleanupResult",
    "BackupRotationEngine",
    "ArchiveDirectoryInitializer",
    "ArchiveInitializer",
    "ArchiveInitResult",
    "PathResolver",
    "create_path_resolver",
    "StartupManager",
    "StartupResult",
    "StartupStep",
    "ShutdownManager",
    "ShutdownResult",
    "SessionManager",
    "SessionState",
    "SessionInfo",
]
