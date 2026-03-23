import importlib.util


def test_pytest_is_working():
    """Teste básico para verificar se o ambiente de testes está ativo."""
    assert True


def test_src_is_reachable():
    """Verifica se o PYTHONPATH está configurado corretamente no Dockerfile."""
    assert importlib.util.find_spec("src") is not None, "A pasta src não está no PYTHONPATH!"
