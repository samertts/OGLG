"""Runtime management for the Correspondence System.

Provides the runtime state machine, lifecycle logging, crash recovery
bootstrap, temp/backup cleanup engines, and archive initialization.
"""

from app.runtime.state import RuntimeState, RuntimeStateMachine, StateTransitionError
from app.runtime.lifecycle import LifecycleLogger, LifecycleEvent
from app.runtime.recovery import CrashRecoveryBootstrap, RecoveryResult
from app.runtime.cleanup import TempCleanupEngine, BackupRotationEngine
from app.runtime.archive import ArchiveDirectoryInitializer

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
