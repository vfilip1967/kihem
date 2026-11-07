from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.dcs import DcsClient
from src.melodos import MelodosClient, ServiceDocument


@dataclass(frozen=True)
class ComposedService:
    selected_date: date
    documents: tuple[ServiceDocument, ...]
    tone: int | None


class ServiceComposer:
    """Compose services for a date while keeping their source boundaries."""

    def __init__(self, client: MelodosClient | None = None, dcs_client: DcsClient | None = None):
        self.client = client or MelodosClient()
        # Vespers has no Melodos page; it comes from the Digital Chant Stand.
        self.dcs = dcs_client or DcsClient()

    def compose(
        self,
        selected_date: date,
        services: tuple[str, ...] = ("orthros", "litourgia"),
        *,
        refresh: bool = False,
    ) -> ComposedService:
        documents = tuple(
            self.dcs.fetch_service(selected_date, service, refresh=refresh)
            if service == "esperinos"
            else self.client.fetch_service(selected_date, service, refresh=refresh)
            for service in services
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
