from __future__ import annotations

import pytest

from app.core.capabilities.contracts import CapabilityContract, DependencySpec
from app.core.capabilities.registry import CapabilityRegistry


def test_register_and_discover() -> None:
    registry = CapabilityRegistry()
    contract = CapabilityContract(
        name="search", version="1.0.0", description="Full-text search"
    )
    registry.register(contract)
    assert registry.has("search")
    assert registry.count == 1
    discovered = registry.discover()
    assert len(discovered) == 1


def test_register_duplicate() -> None:
    registry = CapabilityRegistry()
    contract = CapabilityContract(name="x", version="1.0.0")
    registry.register(contract)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(contract)


def test_get_version() -> None:
    registry = CapabilityRegistry()
    contract = CapabilityContract(name="auth", version="2.1.0")
    registry.register(contract)
    assert registry.version_of("auth") == "2.1.0"
    assert registry.version_of("missing") is None


def test_dependency_validation() -> None:
    registry = CapabilityRegistry()
    base = CapabilityContract(name="base", version="1.0.0")
    registry.register(base)

    dep = DependencySpec(name="base", min_version="1.0.0")
    dependent = CapabilityContract(
        name="extended",
        version="1.0.0",
        dependencies=[dep],
    )
    registry.register(dependent)
    assert registry.validate_dependencies("extended")


def test_dependency_missing() -> None:
    registry = CapabilityRegistry()
    dep = DependencySpec(name="missing_dep", min_version="1.0.0")
    contract = CapabilityContract(
        name="orphan",
        version="1.0.0",
        dependencies=[dep],
    )
    with pytest.raises(ValueError, match="Unsatisfied dependency"):
        registry.register(contract)


def test_discover_by_prefix() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityContract(name="ui.table", version="1.0.0"))
    registry.register(CapabilityContract(name="ui.form", version="1.0.0"))
    registry.register(CapabilityContract(name="data.export", version="1.0.0"))
    ui = registry.discover(prefix="ui")
    assert len(ui) == 2
    data = registry.discover(prefix="data")
    assert len(data) == 1


def test_state() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityContract(name="test", version="1.0.0"))
    state = registry.state()
    assert state["count"] == 1
    assert state["capabilities"][0]["name"] == "test"
