from app.core.exceptions.base import (
    AuthenticationError,
    BusinessRuleViolation,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    ImmutableEntityError,
    PermissionDeniedError,
    ValidationError,
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
