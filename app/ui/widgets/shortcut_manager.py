from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from loguru import logger

try:
    from PySide6.QtCore import QKeyCombination, Qt
    from PySide6.QtGui import QAction, QKeySequence, QShortcut
    from PySide6.QtWidgets import QWidget
except ImportError:
    QWidget = object


@dataclass
class ShortcutBinding:
    id: str
    key_sequence: str
    description: str = ""
    category: str = "general"
    context: int | None = None


class ShortcutManager:
    def __init__(self, parent_widget: QWidget) -> None:
        self._parent = parent_widget
        self._shortcuts: dict[str, QShortcut] = {}
        self._actions: dict[str, QAction] = {}

    def register(
        self,
        binding: ShortcutBinding,
        callback: Callable[[], None],
    ) -> None:
        key_seq = QKeySequence(binding.key_sequence)
        shortcut = QShortcut(key_seq, self._parent)
        shortcut.activated.connect(callback)
        if binding.context is not None:
            shortcut.setContext(binding.context)
        self._shortcuts[binding.id] = shortcut
        logger.debug(f"Shortcut registered: {binding.id} → {binding.key_sequence}")

    def unregister(self, shortcut_id: str) -> None:
        shortcut = self._shortcuts.pop(shortcut_id, None)
        if shortcut:
            shortcut.setEnabled(False)
            shortcut.deleteLater()

    def register_action(
        self,
        action_id: str,
        key_sequence: str,
        callback: Callable[[], None],
        description: str = "",
    ) -> None:
        action = QAction(description, self._parent)
        action.setShortcut(QKeySequence(key_sequence))
        action.triggered.connect(callback)
        self._actions[action_id] = action
        self._parent.addAction(action)

    def set_enabled(self, shortcut_id: str, enabled: bool) -> None:
        shortcut = self._shortcuts.get(shortcut_id)
        if shortcut:
            shortcut.setEnabled(enabled)

    def set_all_enabled(self, enabled: bool) -> None:
        for shortcut in self._shortcuts.values():
            shortcut.setEnabled(enabled)

    @property
    def bindings(self) -> list[tuple[str, str]]:
        return [(sid, s.key().toString()) for sid, s in self._shortcuts.items()]

    def dispose(self) -> None:
        for sid in list(self._shortcuts.keys()):
            self.unregister(sid)
        for action in self._actions.values():
            self._parent.removeAction(action)
        self._actions.clear()
