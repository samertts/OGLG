from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Generator


class TransactionState(Enum):
    IDLE = auto()
    OPEN = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()


@dataclass
class DialogTransaction:
    transaction_id: str
    state: TransactionState = TransactionState.IDLE
    opened_at: datetime | None = None
    committed_at: datetime | None = None
    rolled_back_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    on_commit: Callable[[], None] | None = None
    on_rollback: Callable[[], None] | None = None

    def open(self) -> None:
        self.state = TransactionState.OPEN
        self.opened_at = datetime.now(timezone.utc)

    def commit(self) -> None:
        if self.state != TransactionState.OPEN:
            raise RuntimeError(f"Cannot commit transaction in state: {self.state}")
        self.state = TransactionState.COMMITTED
        self.committed_at = datetime.now(timezone.utc)
        if self.on_commit:
            self.on_commit()

    def rollback(self) -> None:
        if self.state != TransactionState.OPEN:
            return
        self.state = TransactionState.ROLLED_BACK
        self.rolled_back_at = datetime.now(timezone.utc)
        if self.on_rollback:
            self.on_rollback()

    @property
    def is_open(self) -> bool:
        return self.state == TransactionState.OPEN

    @property
    def is_terminal(self) -> bool:
        return self.state in (TransactionState.COMMITTED, TransactionState.ROLLED_BACK)


class TransactionSafeDialog:
    def __init__(self, dialog_id: str):
        self._dialog_id = dialog_id
        self._current_tx: DialogTransaction | None = None
        self._closed = False

    @property
    def dialog_id(self) -> str:
        return self._dialog_id

    @property
    def is_closed(self) -> bool:
        return self._closed

    def begin_transaction(self, transaction_id: str) -> DialogTransaction:
        tx = DialogTransaction(transaction_id=transaction_id)
        tx.open()
        self._current_tx = tx
        return tx

    @contextmanager
    def transaction(self, transaction_id: str) -> Generator[DialogTransaction, Any, None]:
        tx = self.begin_transaction(transaction_id)
        try:
            yield tx
            if tx.is_open:
                tx.commit()
        except Exception:
            if tx.is_open:
                tx.rollback()
            raise
        finally:
            if self._current_tx is tx:
                self._current_tx = None

    def close(self) -> None:
        if self._current_tx and self._current_tx.is_open:
            self._current_tx.rollback()
        self._closed = True
