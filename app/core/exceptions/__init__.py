from app.core.exceptions.base import (
    DomainError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    ImmutableEntityError,
    PermissionDeniedError,
    AuthenticationError,
    BusinessRuleViolation,
)

__all__ = [
    "DomainError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    "ImmutableEntityError",
    "PermissionDeniedError",
    "AuthenticationError",
    "BusinessRuleViolation",
]
