"""US00-TK14 — Sanidade dos enums de status.

Guarda os valores dos enums para garantir que o refactor não alterou as
strings persistidas. Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US00-TK14")/d' tests/test_shared/test_enums.py
"""

import pytest

from src.shared.enums import RoutePassangerStatus, TripPassangerStatus, TripStatus


@pytest.mark.skip(reason="US00-TK14")
def test_trip_status_values():
    assert TripStatus.INICIADA.value == "iniciada"
    assert TripStatus.FINALIZADA.value == "finalizada"
    assert TripStatus.CANCELADA.value == "cancelada"


@pytest.mark.skip(reason="US00-TK14")
def test_trip_passanger_status_values():
    assert TripPassangerStatus.PENDENTE.value == "pendente"
    assert TripPassangerStatus.PRESENTE.value == "presente"
    assert TripPassangerStatus.AUSENTE.value == "ausente"


@pytest.mark.skip(reason="US00-TK14")
def test_route_passanger_status_values():
    assert RoutePassangerStatus.PENDING.value == "pending"
    assert RoutePassangerStatus.ACCEPTED.value == "accepted"
    assert RoutePassangerStatus.REJECTED.value == "rejected"


@pytest.mark.skip(reason="US00-TK14")
def test_enum_is_str_compatible():
    # herdar de str mantém compatibilidade com colunas String e JSON
    assert TripStatus.FINALIZADA == "finalizada"
