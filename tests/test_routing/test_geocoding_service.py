"""US10-TK18 — Testes do IGeocodingService e MapboxGeocodingService.

Cobre:
- Interface IGeocodingService existe e é abstrata
- DTO GeocodeResult é válido
- MapboxGeocodingService implementa a interface
- DI get_geocoding_service devolve instância
- MapboxGeocodingService.geocode_address (skips US10-TK18):
  - chama Mapbox Geocoding API com query montada do endereço
  - retorna GeocodeResult quando a API encontra coordenadas
  - retorna None quando a API não encontra (relevance baixa, empty features)
  - retorna None quando a API falha (rede/credencial) — sem propagar exceção
"""

from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# US10-TK18 — IGeocodingService interface + DTO + DI
# ===========================================================================


def test_igeocoding_service_is_abstract():
    """IGeocodingService deve ser abstrata (não instanciável diretamente)."""
    from src.domains.routing.service import IGeocodingService

    with pytest.raises(TypeError):
        IGeocodingService()  # type: ignore[abstract]


def test_igeocoding_service_has_geocode_address():
    """IGeocodingService deve expor geocode_address."""
    from src.domains.routing.service import IGeocodingService

    assert hasattr(IGeocodingService, "geocode_address")


def test_geocode_result_valid():
    """GeocodeResult deve ser instanciável com latitude e longitude."""
    from src.domains.routing.dtos import GeocodeResult

    result = GeocodeResult(latitude=-30.0277, longitude=-51.2287)
    assert result.latitude == -30.0277
    assert result.longitude == -51.2287


def test_mapbox_geocoding_service_implements_interface():
    """MapboxGeocodingService deve implementar IGeocodingService."""
    from src.domains.routing.service import IGeocodingService
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")
    assert isinstance(service, IGeocodingService)


def test_get_geocoding_service_returns_instance():
    """get_geocoding_service deve retornar uma instância de IGeocodingService."""
    from src.domains.routing.service import IGeocodingService
    from src.infrastructure.dependencies.routing_dependencies import get_geocoding_service

    service = get_geocoding_service()
    assert isinstance(service, IGeocodingService)


# ===========================================================================
# US10-TK18 — MapboxGeocodingService.geocode_address (impl)
# ===========================================================================


def test_geocode_address_calls_mapbox_geocoding_api():
    """geocode_address deve chamar a Mapbox Geocoding API com query montada
    a partir dos campos do endereço (street, number, neighborhood, city,
    state, zip, country=BR)."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")

    # impl pode usar requests, httpx, ou o SDK do Mapbox — adaptar o patch
    with patch("src.infrastructure.routing.mapbox_routing_service.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "center": [-51.2287, -30.0277],
                    "relevance": 0.9,
                }
            ]
        }
        mock_get.return_value = mock_response

        service.geocode_address(
            street="Av. Ipiranga",
            number="6681",
            neighborhood="Partenon",
            zip_code="90619-900",
            city="Porto Alegre",
            state="RS",
        )

        mock_get.assert_called_once()
        called_url = mock_get.call_args.args[0]
        # query string deve conter componentes do endereço
        assert "Ipiranga" in called_url or "Ipiranga" in str(mock_get.call_args)


def test_geocode_address_returns_coordinates_when_found():
    """geocode_address deve devolver GeocodeResult com lat/lng quando a API
    retorna feature com relevance suficiente."""
    from src.domains.routing.dtos import GeocodeResult
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")

    with patch("src.infrastructure.routing.mapbox_routing_service.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "center": [-51.2287, -30.0277],
                    "relevance": 0.95,
                }
            ]
        }
        mock_get.return_value = mock_response

        result = service.geocode_address(
            street="Av. Ipiranga",
            number="6681",
            neighborhood="Partenon",
            zip_code="90619-900",
            city="Porto Alegre",
            state="RS",
        )

        assert isinstance(result, GeocodeResult)
        assert result.latitude == pytest.approx(-30.0277)
        assert result.longitude == pytest.approx(-51.2287)


def test_geocode_address_returns_none_when_no_features():
    """geocode_address deve devolver None quando a API retorna lista vazia."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")

    with patch("src.infrastructure.routing.mapbox_routing_service.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response

        result = service.geocode_address(
            street="Endereço Inexistente",
            number="0",
            neighborhood="X",
            zip_code="00000-000",
            city="Y",
            state="ZZ",
        )

        assert result is None


def test_geocode_address_returns_none_when_relevance_too_low():
    """geocode_address deve descartar features com relevance abaixo do limiar."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")

    with patch("src.infrastructure.routing.mapbox_routing_service.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "center": [-51.0, -30.0],
                    "relevance": 0.2,  # abaixo do limiar
                }
            ]
        }
        mock_get.return_value = mock_response

        result = service.geocode_address(
            street="Endereço Ambíguo",
            number="100",
            neighborhood="X",
            zip_code="00000-000",
            city="Y",
            state="ZZ",
        )

        assert result is None


def test_geocode_address_returns_none_on_api_error():
    """geocode_address deve absorver erros de rede/credencial e devolver None
    em vez de propagar a exceção — geocoding é best-effort."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService

    service = MapboxGeocodingService(api_key="test-key")

    with patch(
        "src.infrastructure.routing.mapbox_routing_service.requests.get",
        side_effect=RuntimeError("network down"),
    ):
        result = service.geocode_address(
            street="Qualquer",
            number="100",
            neighborhood="X",
            zip_code="00000-000",
            city="Y",
            state="ZZ",
        )

        assert result is None
