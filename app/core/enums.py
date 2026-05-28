import enum


class Priority(enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class LetterStatus(enum.Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"
    SENT = "SENT"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"
    AUDITOR = "AUDITOR"


class BackupType(enum.Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    PRE_MIGRATION = "PRE_MIGRATION"


class LanguageTag(enum.Enum):
    AR = "AR"
    AR_EN = "AR_EN"


class IntegrationTarget(enum.Enum):
    GULA = "GULA"
    LAB_SYSTEM = "LAB_SYSTEM"
    MINISTRY_ARCHIVE = "MINISTRY_ARCHIVE"
    QR_VERIFICATION = "QR_VERIFICATION"
    BARCODE = "BARCODE"
    INTERNAL_API = "INTERNAL_API"


class TemplateType(enum.Enum):
    OFFICIAL_LETTER = "OFFICIAL_LETTER"
    MEMO = "MEMO"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
