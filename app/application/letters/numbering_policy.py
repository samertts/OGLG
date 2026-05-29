from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Protocol

_SEQUENCE_WIDTH = 6
_VALID_PREFIX_RE = re.compile(r"^[A-Z]{2,10}$")
_VALID_YEAR_RANGE = (1900, 2099)
_NUMBER_FORMAT_RE = re.compile(r"^[A-Z]{2,10}-\d{4}-\d{6}$")


def validate_prefix(prefix: str) -> str | None:
    if not prefix or not prefix.strip():
        return "prefix cannot be empty"
    if len(prefix) > 10:
        return f"prefix too long: {prefix}"
    if not _VALID_PREFIX_RE.match(prefix):
        return f"invalid prefix (uppercase letters only): {prefix}"
    return None


def validate_year(year: int) -> str | None:
    if year < _VALID_YEAR_RANGE[0] or year > _VALID_YEAR_RANGE[1]:
        return f"year out of range {_VALID_YEAR_RANGE}: {year}"
    return None


def normalize_sequence(sequence: int) -> str:
    if sequence < 0:
        raise ValueError(f"sequence cannot be negative: {sequence}")
    return f"{sequence:0{_SEQUENCE_WIDTH}d}"


def format_number(prefix: str, year: int, sequence: int) -> str:
    prefix_err = validate_prefix(prefix)
    if prefix_err:
        raise ValueError(prefix_err)
    year_err = validate_year(year)
    if year_err:
        raise ValueError(year_err)
    seq_str = normalize_sequence(sequence)
    return f"{prefix}-{year}-{seq_str}"


def validate_number_format(number: str) -> bool:
    return bool(_NUMBER_FORMAT_RE.match(number))


def parse_number(number: str) -> tuple[str, int, int]:
    if not validate_number_format(number):
        raise ValueError(f"invalid number format: {number}")
    prefix_str, year_str, seq_str = number.split("-")
    return prefix_str, int(year_str), int(seq_str)


class NumberingFormatterProtocol(Protocol):
    def format(self, prefix: str, year: int, sequence: int) -> str: ...
    def parse(self, number: str) -> tuple[str, int, int]: ...
    def validate(self, number: str) -> bool: ...


class NumberingExtensionHook(ABC):
    @abstractmethod
    def on_number_generated(self, number: str, prefix: str, year: int, sequence: int) -> None:
        ...

    @abstractmethod
    def on_number_validated(self, number: str, valid: bool) -> None:
        ...

    @abstractmethod
    def on_number_parsed(self, number: str, prefix: str, year: int, sequence: int) -> None:
        ...


class RegionalNumberingHook(ABC):
    @abstractmethod
    def resolve_region_prefix(self, region_code: str) -> str:
        ...

    @abstractmethod
    def validate_region_number(self, number: str, region_code: str) -> bool:
        ...


class MinistryFederationHook(ABC):
    @abstractmethod
    def resolve_ministry_code(self, ministry_id: str) -> str:
        ...

    @abstractmethod
    def validate_federated_number(self, number: str, ministry_id: str) -> bool:
        ...


class DistributedSyncHook(ABC):
    @abstractmethod
    def on_number_allocated(self, number: str, node_id: str) -> None:
        ...

    @abstractmethod
    def resolve_sequence_range(self, node_id: str, count: int) -> tuple[int, int]:
        ...


class DigitalSignatureHook(ABC):
    @abstractmethod
    def sign_number(self, number: str) -> str:
        ...

    @abstractmethod
    def verify_signature(self, number: str, signature: str) -> bool:
        ...


class QRMetadataHook(ABC):
    @abstractmethod
    def encode_metadata(self, number: str, metadata: dict[str, Any]) -> str:
        ...

    @abstractmethod
    def decode_metadata(self, payload: str) -> dict[str, Any]:
        ...


class AuditIntegrationHook(ABC):
    @abstractmethod
    def log_numbering_event(self, event_type: str, number: str, context: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def query_numbering_audit(self, number: str) -> list[dict[str, Any]]:
        ...


class ArchiveLinkageHook(ABC):
    @abstractmethod
    def link_to_archive(self, number: str, archive_id: str) -> None:
        ...

    @abstractmethod
    def resolve_archive_id(self, number: str) -> str | None:
        ...


class RecoveryValidationHook(ABC):
    @abstractmethod
    def validate_recovery(self, number: str, recovery_data: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def rebuild_sequence_state(self, numbers: list[str]) -> dict[str, Any]:
        ...


__all__ = [
    "validate_prefix",
    "validate_year",
    "normalize_sequence",
    "format_number",
    "validate_number_format",
    "parse_number",
    "NumberingFormatterProtocol",
    "NumberingExtensionHook",
    "RegionalNumberingHook",
    "MinistryFederationHook",
    "DistributedSyncHook",
    "DigitalSignatureHook",
    "QRMetadataHook",
    "AuditIntegrationHook",
    "ArchiveLinkageHook",
    "RecoveryValidationHook",
]
