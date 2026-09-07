from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.melodos import MelodosClient, ServiceDocument


@dataclass(frozen=True)
class ComposedService:
    selected_date: date
    documents: tuple[ServiceDocument, ...]
    tone: int | None


class ServiceComposer:
    """Compose services for a date while keeping their source boundaries."""

    def __init__(self, client: MelodosClient | None = None):
        self.client = client or MelodosClient()

    def compose(
        self,
        selected_date: date,
        services: tuple[str, ...] = ("orthros", "litourgia"),
        *,
        refresh: bool = False,
    ) -> ComposedService:
        documents = tuple(
            self.client.fetch_service(selected_date, service, refresh=refresh) for service in services
        )
        tone = next((document.tone for document in documents if document.tone is not None), None)
        return ComposedService(selected_date=selected_date, documents=documents, tone=tone)

    def compose_sunday(
        self,
        selected_date: date,
        services: tuple[str, ...] = ("orthros", "litourgia"),
        *,
        refresh: bool = False,
    ) -> ComposedService:
        """Compatibility alias; composition is no longer limited to Sundays."""
        return self.compose(selected_date, services=services, refresh=refresh)


# Backwards-compatible name used by the initial prototype.
Composer = ServiceComposer
