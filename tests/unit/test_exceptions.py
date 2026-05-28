"""Tests for domain exception hierarchy."""

import pytest

from app.core.exceptions import (
    AuthenticationError,
    BusinessRuleViolation,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    ImmutableEntityError,
    PermissionDeniedError,
    ValidationError,
)


def test_domain_error_is_base() -> None:
    assert issubclass(EntityNotFoundError, DomainError)
    assert issubclass(DuplicateEntityError, DomainError)
    assert issubclass(ValidationError, DomainError)
    assert issubclass(ImmutableEntityError, DomainError)
    assert issubclass(PermissionDeniedError, DomainError)
    assert issubclass(AuthenticationError, DomainError)
    assert issubclass(BusinessRuleViolation, DomainError)


def test_domain_error_message() -> None:
    err = DomainError("test error")
    assert str(err) == "test error"
    assert err.message == "test error"


def test_entity_not_found() -> None:
    err = EntityNotFoundError("Letter", "123")
    assert "Letter" in str(err)
    assert "123" in str(err)


def test_duplicate_entity() -> None:
    err = DuplicateEntityError("User", "username", "admin")
    assert "User" in str(err)
    assert "username" in str(err)
    assert "admin" in str(err)


def test_validation_error() -> None:
    err = ValidationError("Letter", "subject", "is required")
    assert "Letter" in str(err)
    assert "subject" in str(err)


def test_immutable_entity_error() -> None:
    err = ImmutableEntityError("AuditEntry", "entry-1", "is append-only")
    assert "AuditEntry" in str(err)
    assert "entry-1" in str(err)


def test_permission_denied() -> None:
    err = PermissionDeniedError("user-1", "archive_letter")
    assert "user-1" in str(err)
    assert "archive_letter" in str(err)


def test_authentication_error() -> None:
    err = AuthenticationError("Invalid credentials")
    assert str(err) == "Invalid credentials"


def test_business_rule_violation() -> None:
    err = BusinessRuleViolation("Cannot archive a draft letter")
    assert "Cannot archive a draft letter" in str(err)


def test_error_inheritance_chain() -> None:
    assert issubclass(DomainError, Exception)


def test_domain_error_code() -> None:
    err = BusinessRuleViolation("test")
    assert err.code == "BUSINESS_RULE_VIOLATION"
