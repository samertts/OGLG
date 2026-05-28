"""Tests for domain enums."""

from app.core.enums import (
    BackupType,
    IntegrationTarget,
    LanguageTag,
    LetterStatus,
    Priority,
    TemplateType,
    UserRole,
)


def test_priority_values() -> None:
    assert Priority.LOW.value == "LOW"
    assert Priority.NORMAL.value == "NORMAL"
    assert Priority.HIGH.value == "HIGH"
    assert Priority.URGENT.value == "URGENT"


def test_letter_status_values() -> None:
    assert LetterStatus.DRAFT.value == "DRAFT"
    assert LetterStatus.FINAL.value == "FINAL"
    assert LetterStatus.SENT.value == "SENT"
    assert LetterStatus.ARCHIVED.value == "ARCHIVED"
    assert LetterStatus.CANCELLED.value == "CANCELLED"


def test_user_role_values() -> None:
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.EDITOR.value == "EDITOR"
    assert UserRole.VIEWER.value == "VIEWER"
    assert UserRole.AUDITOR.value == "AUDITOR"


def test_backup_type_values() -> None:
    assert BackupType.AUTO.value == "AUTO"
    assert BackupType.MANUAL.value == "MANUAL"
    assert BackupType.PRE_MIGRATION.value == "PRE_MIGRATION"


def test_language_tag_values() -> None:
    assert LanguageTag.AR.value == "AR"
    assert LanguageTag.AR_EN.value == "AR_EN"


def test_integration_target_values() -> None:
    targets = [
        IntegrationTarget.GULA,
        IntegrationTarget.LAB_SYSTEM,
        IntegrationTarget.MINISTRY_ARCHIVE,
        IntegrationTarget.QR_VERIFICATION,
        IntegrationTarget.BARCODE,
        IntegrationTarget.INTERNAL_API,
    ]
    for t in targets:
        assert isinstance(t.value, str)


def test_template_type_values() -> None:
    assert TemplateType.OFFICIAL_LETTER.value == "OFFICIAL_LETTER"
    assert TemplateType.MEMO.value == "MEMO"
    assert TemplateType.INTERNAL.value == "INTERNAL"
    assert TemplateType.EXTERNAL.value == "EXTERNAL"


def test_priority_order() -> None:
    priorities = [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.URGENT]
    assert len(priorities) == 4
    assert all(isinstance(p, Priority) for p in priorities)


def test_all_enums_are_unique() -> None:
    for enum_cls in [Priority, LetterStatus, UserRole, BackupType, LanguageTag, TemplateType]:
        values = [e.value for e in enum_cls]
        assert len(values) == len(set(values)), f"{enum_cls.__name__} has duplicate values"
