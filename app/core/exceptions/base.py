class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """Raised when a domain entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message=f"{entity_type} not found: {entity_id}",
            code="ENTITY_NOT_FOUND",
        )


class DuplicateEntityError(DomainError):
    """Raised when a duplicate entity would be created."""

    def __init__(self, entity_type: str, field: str, value: str) -> None:
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(
            message=f"{entity_type} with {field} '{value}' already exists",
            code="DUPLICATE_ENTITY",
        )


class ValidationError(DomainError):
    """Raised when entity validation fails."""

    def __init__(self, entity_type: str, field: str, reason: str) -> None:
        self.entity_type = entity_type
        self.field = field
        self.reason = reason
        super().__init__(
            message=f"Validation failed for {entity_type}.{field}: {reason}",
            code="VALIDATION_ERROR",
        )


class ImmutableEntityError(DomainError):
    """Raised when attempting to modify an immutable entity."""

    def __init__(self, entity_type: str, entity_id: str, reason: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.reason = reason
        super().__init__(
            message=f"Cannot modify {entity_type} {entity_id}: {reason}",
            code="IMMUTABLE_ENTITY",
        )


class PermissionDeniedError(DomainError):
    """Raised when user lacks permission for an action."""

    def __init__(self, user_id: str, action: str) -> None:
        self.user_id = user_id
        self.action = action
        super().__init__(
            message=f"User {user_id} lacks permission: {action}",
            code="PERMISSION_DENIED",
        )


class AuthenticationError(DomainError):
    """Raised when authentication fails."""

    def __init__(self, reason: str = "Authentication failed") -> None:
        super().__init__(message=reason, code="AUTHENTICATION_FAILED")


class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, rule: str, detail: str = "") -> None:
        message = f"Business rule violation: {rule}"
        if detail:
            message += f" ({detail})"
        super().__init__(message=message, code="BUSINESS_RULE_VIOLATION")
