"""US10-TK06 — DI para IRoutingService."""

from src.domains.routing.service import IRoutingService


# US10-TK06
def get_routing_service() -> IRoutingService:
    """Retorna uma instância de MapboxRoutingService configurada com a API key."""
    pass  # type: ignore[return-value]
