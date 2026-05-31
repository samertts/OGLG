from __future__ import annotations

from app.core.safety.cleanup import TempCleanupService


def test_cleanup_service_register_prefix() -> None:
    service = TempCleanupService()
    service.register_prefix("oglg_")
    assert "oglg_" in service.state()["prefixes"]
    service.unregister_prefix("oglg_")
    assert "oglg_" not in service.state()["prefixes"]


def test_cleanup_service_start_stop() -> None:
    service = TempCleanupService()
    assert not service.state()["running"]
    service.start()
    assert service.state()["running"]
    service.stop()
    assert not service.state()["running"]


def test_cleanup_service_state() -> None:
    service = TempCleanupService(max_age_seconds=60.0, cleanup_interval=120.0)
    state = service.state()
    assert state["max_age_seconds"] == 60.0
    assert state["cleanup_interval"] == 120.0
