from __future__ import annotations

from enum import Enum


class DeliveryMethod(Enum):
    COURIER = "COURIER"
    POSTAL = "POSTAL"
    FAX = "FAX"
    EMAIL = "EMAIL"
    INTERNAL = "INTERNAL"
    HAND_DELIVERY = "HAND_DELIVERY"


class DeliveryStatus(Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CONFIRMED = "CONFIRMED"
    RETURNED = "RETURNED"
    FAILED = "FAILED"
