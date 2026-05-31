from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROFILE_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "profiles"
_REQUIRED_KEYS = {
    "organization_type",
    "branding",
    "federation_namespace",
    "audit_namespace",
    "offline_mode",
    "telemetry_mode",
    "replay_mode",
}
_VALID_OFFLINE_MODES = {"strict", "relaxed"}
_VALID_TELEMETRY_MODES = {"local_only", "off"}
_VALID_REPLAY_MODES = {"full", "standard", "archive", "minimal"}


class ProfileLoader:
    def __init__(self, profile_dir: str | Path | None = None) -> None:
        self._dir = Path(profile_dir) if profile_dir else _PROFILE_DIR

    def list_profiles(self) -> list[str]:
        if not self._dir.is_dir():
            return []
        return sorted(
            f.stem for f in self._dir.iterdir() if f.suffix == ".json"
        )

    def load(self, name: str) -> dict[str, Any]:
        path = self._dir / f"{name}.json"
        if not path.is_file():
            msg = f"Profile not found: {name}"
            raise FileNotFoundError(msg)
        with open(path, encoding="utf-8") as f:
            profile: dict[str, Any] = json.load(f)
        self._validate(name, profile)
        return profile

    def _validate(self, name: str, profile: dict[str, Any]) -> None:
        missing = _REQUIRED_KEYS - set(profile.keys())
        if missing:
            msg = f"Profile '{name}' missing keys: {missing}"
            raise ValueError(msg)
        if profile["offline_mode"] not in _VALID_OFFLINE_MODES:
            msg = f"Profile '{name}' invalid offline_mode: {profile['offline_mode']}"
            raise ValueError(msg)
        if profile["telemetry_mode"] not in _VALID_TELEMETRY_MODES:
            msg = f"Profile '{name}' invalid telemetry_mode: {profile['telemetry_mode']}"
            raise ValueError(msg)
        if profile["replay_mode"] not in _VALID_REPLAY_MODES:
            msg = f"Profile '{name}' invalid replay_mode: {profile['replay_mode']}"
            raise ValueError(msg)
