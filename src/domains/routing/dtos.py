"""US10-TK06 — DTOs do domínio de roteamento."""

from pydantic import BaseModel, Field


# US10-TK06
class RouteInfoResult(BaseModel):
    """Resultado do cálculo de rota via Mapbox Directions API.

    Fields:
    - total_distance_km: distância total percorrida em quilômetros
    - estimated_duration_min: tempo estimado de percurso em minutos
    """

    total_distance_km: float = Field(..., description="Distância total em km")
    estimated_duration_min: int = Field(..., description="Duração estimada em minutos")
