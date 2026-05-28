from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Generic, TypeVar

from loguru import logger


class ViewModelState(Enum):
    IDLE = auto()
    LOADING = auto()
    READY = auto()
    ERROR = auto()
    BUSY = auto()


T = TypeVar("T")


@dataclass
class ViewModelProperty(Generic[T]):
    value: T
    _listeners: list[Callable[[T, T], None]] = field(default_factory=list, repr=False)

    def set(self, new_value: T) -> None:
        old = self.value
        if old == new_value:
            return
        self.value = new_value
        for listener in self._listeners:
            try:
                listener(old, new_value)
            except Exception as exc:
                logger.error("ViewModel listener error", extra={"error": str(exc)})

    def get(self) -> T:
        return self.value

    def listen(self, callback: Callable[[T, T], None]) -> Callable[[], None]:
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback)

    def __get__(self, obj, objtype=None) -> T:
        return self.value

    def __set__(self, obj, value: T) -> None:
        self.set(value)


class BaseViewModel(ABC):
    def __init__(self) -> None:
        self._state: ViewModelProperty[ViewModelState] = ViewModelProperty(ViewModelState.IDLE)
        self._error_message: ViewModelProperty[str | None] = ViewModelProperty(None)
        self._disposed = False

    @property
    def state(self) -> ViewModelState:
        return self._state.value

    @state.setter
    def state(self, new_state: ViewModelState) -> None:
        self._state.set(new_state)

    @property
    def error_message(self) -> str | None:
        return self._error_message.value

    @error_message.setter
    def error_message(self, msg: str | None) -> None:
        self._error_message.set(msg)

    @property
    def is_loading(self) -> bool:
        return self.state == ViewModelState.LOADING

    @property
    def is_ready(self) -> bool:
        return self.state == ViewModelState.READY

    @property
    def has_error(self) -> bool:
        return self.state == ViewModelState.ERROR

    @property
    def disposed(self) -> bool:
        return self._disposed

    @abstractmethod
    def initialize(self) -> None: ...

    def on_state_changed(
        self, callback: Callable[[ViewModelState, ViewModelState], None]
    ) -> Callable[[], None]:
        return self._state.listen(callback)

    def on_error_changed(
        self, callback: Callable[[str | None, str | None], None]
    ) -> Callable[[], None]:
        return self._error_message.listen(callback)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._on_dispose()
        self._disposed = True

    def _on_dispose(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}(state={self.state.name})"


class ScreenViewModel(BaseViewModel):
    def __init__(self, screen_id: str, title: str) -> None:
        super().__init__()
        self._screen_id = screen_id
        self._title = title

    @property
    def screen_id(self) -> str:
        return self._screen_id

    @property
    def title(self) -> str:
        return self._title
