"""
US03 - TK02: Implementar Contratos de Criação (Schema de Dependentes)
Arquivo: src/domains/dependents/dtos.py

Testes de validação Pydantic para DependentCreate e DependentResponse.
"""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.domains.dependents.dtos import DependentCreate, DependentResponse


# ---------------------------------------------------------------------------
# DependentCreate — happy path
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_valid():
    """name preenchido corretamente deve criar o schema sem erros."""
    data = DependentCreate(name="Ana Silva")

    assert data.name == "Ana Silva"


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_accepts_full_name():
    """Nomes compostos devem ser aceitos."""
    data = DependentCreate(name="João Carlos da Silva")

    assert data.name == "João Carlos da Silva"


# ---------------------------------------------------------------------------
# DependentCreate — campo obrigatório ausente
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_missing_name():
    """name é obrigatório — omitir deve lançar ValidationError."""
    with pytest.raises(ValidationError):
        DependentCreate()


# ---------------------------------------------------------------------------
# DependentCreate — strings inválidas
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_empty_name():
    """name vazio não deve ser aceito."""
    with pytest.raises(ValidationError):
        DependentCreate(name="")


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_whitespace_only_name():
    """name com apenas espaços não deve ser aceito."""
    with pytest.raises(ValidationError):
        DependentCreate(name="   ")


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_create_single_space_name():
    """name com um único espaço não deve ser aceito."""
    with pytest.raises(ValidationError):
        DependentCreate(name=" ")


# ---------------------------------------------------------------------------
# DependentResponse
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_response_structure():
    """DependentResponse deve aceitar todos os campos e expô-los corretamente."""
    data = DependentResponse(
        id=uuid.uuid4(),
        guardian_id=uuid.uuid4(),
        name="Ana Silva",
        created_at=datetime.now(),
    )

    assert data.name == "Ana Silva"
    assert data.id is not None
    assert data.guardian_id is not None


@pytest.mark.skip(reason="US03-TK02")
def test_dependent_response_no_sensitive_fields():
    """DependentResponse não deve expor campos sensíveis do usuário."""
    fields = DependentResponse.model_fields.keys()

    assert "password" not in fields
    assert "password_hash" not in fields
    assert "email" not in fields


# ===========================================================================
# US04 - TK02: Implementar Contratos de Atualização (DependentUpdate)
# ===========================================================================


# ---------------------------------------------------------------------------
# DependentUpdate — happy path
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US04-TK02")
def test_dependent_update_no_fields_is_valid():
    """DependentUpdate sem nenhum campo deve ser válido (todos opcionais)."""
    from src.domains.dependents.dtos import DependentUpdate

    data = DependentUpdate()
    assert data.name is None


@pytest.mark.skip(reason="US04-TK02")
def test_dependent_update_with_name():
    """DependentUpdate com name preenchido deve ser válido."""
    from src.domains.dependents.dtos import DependentUpdate

    data = DependentUpdate(name="Carlos")
    assert data.name == "Carlos"


# ---------------------------------------------------------------------------
# DependentUpdate — validações quando nome é enviado
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US04-TK02")
def test_dependent_update_empty_name_invalid():
    """name enviado como string vazia não deve ser aceito."""
    from src.domains.dependents.dtos import DependentUpdate

    with pytest.raises(ValidationError):
        DependentUpdate(name="")


@pytest.mark.skip(reason="US04-TK02")
def test_dependent_update_whitespace_name_invalid():
    """name enviado com apenas espaços não deve ser aceito."""
    from src.domains.dependents.dtos import DependentUpdate

    with pytest.raises(ValidationError):
        DependentUpdate(name="   ")
