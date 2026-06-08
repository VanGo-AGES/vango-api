"""US17-TK07 — get_current_driver (autorização por papel).

Remova o skip rodando:
  sed -i '/@pytest.mark.skip(reason="US17-TK07")/d' tests/test_auth/test_get_current_driver.py
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.infrastructure.auth.dependencies import get_current_driver


def _user(role: str):
    return type("U", (), {"id": uuid4(), "role": role})()


@pytest.mark.skip(reason="US17-TK07")
def test_driver_passes():
    user = _user("driver")
    assert get_current_driver(current_user=user) is user


@pytest.mark.skip(reason="US17-TK07")
def test_non_driver_forbidden_403():
    with pytest.raises(HTTPException) as exc:
        get_current_driver(current_user=_user("passenger"))
    assert exc.value.status_code == 403
