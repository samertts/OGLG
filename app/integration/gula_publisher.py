"""Publish administrative correspondence events to GULA's integration inbox."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable

from app.core.events.base import DomainEvent


@dataclass(frozen=True)
class GulaEventPublisher:
    base_url: str
    access_token: str
    tenant_id: str
    opener: Callable[..., Any] = urllib.request.urlopen
    max_retries: int = 3
    backoff_seconds: float = 0.25

    def publish(self, event: DomainEvent) -> None:
        if not self.base_url.strip() or not self.access_token.strip() or not self.tenant_id.strip():
            raise ValueError("GULA base_url, access_token, and tenant_id are required")
        event_type = "correspondence.issued"
        idempotency_key = sha256(
            f"{event.event_id}:{event.version}:{event.aggregate_id}".encode("utf-8")
        ).hexdigest()
        payload = event.to_dict()
        envelope = {
            "event_id": event.event_id,
            "event_type": event_type,
            "schema_version": event.version,
            "source_service": "oglg",
            "tenant_id": self.tenant_id,
            "occurred_at": event.timestamp.astimezone().isoformat(),
            "actor_id": event.metadata.source or "oglg",
            "entity_id": event.aggregate_id,
            "correlation_id": event.correlation_id or event.event_id,
            "idempotency_key": idempotency_key,
            "payload": payload,
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/integrations/events",
            data=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(max(1, self.max_retries)):
            try:
                with self.opener(request, timeout=10) as response:
                    if 200 <= response.status < 300:
                        return
                    last_error = RuntimeError(f"GULA returned HTTP {response.status}")
            except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                last_error = exc
            if attempt + 1 < max(1, self.max_retries):
                time.sleep(self.backoff_seconds * (2**attempt))
        raise RuntimeError("failed to publish correspondence event to GULA") from last_error
