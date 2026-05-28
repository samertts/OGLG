from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger

from app.ui.viewmodels.base_viewmodel import BaseViewModel


class BaseController(ABC):
    def __init__(self, view_model: BaseViewModel) -> None:
        self._view_model = view_model
        self._initialized = False

    @property
    def view_model(self) -> BaseViewModel:
        return self._view_model

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        if self._initialized:
            return
        self._on_initialize()
        self._initialized = True
        logger.debug(f"{type(self).__name__} initialized")

    @abstractmethod
    def _on_initialize(self) -> None: ...

    def dispose(self) -> None:
        if not self._initialized:
            return
        self._on_dispose()
        self._view_model.dispose()
        self._initialized = False

    def _on_dispose(self) -> None:
        pass

    def __repr__(self) -> str:
        vm_name = type(self._view_model).__name__ if self._view_model else "None"
        return f"{type(self).__name__}(vm={vm_name})"
