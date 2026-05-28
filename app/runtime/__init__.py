"""Runtime management for the Correspondence System.

Provides the runtime state machine, lifecycle logging, crash recovery
bootstrap, temp/backup cleanup engines, and archive initialization.
"""

from app.runtime.archive import ArchiveDirectoryInitializer
from app.runtime.cleanup import BackupRotationEngine, TempCleanupEngine
from app.runtime.lifecycle import LifecycleEvent, LifecycleLogger
from app.runtime.recovery import CrashRecoveryBootstrap, RecoveryResult
from app.runtime.state import RuntimeState, RuntimeStateMachine, StateTransitionError

__all__ = [
    "RuntimeState",
    "RuntimeStateMachine",
    "StateTransitionError",
    "LifecycleLogger",
    "LifecycleEvent",
    "CrashRecoveryBootstrap",
    "RecoveryResult",
    "TempCleanupEngine",
    "BackupRotationEngine",
    "ArchiveDirectoryInitializer",
]
