def test_pytest_is_working():
    """Teste básico para verificar se o ambiente de testes está ativo."""
    assert True


def test_src_is_reachable():
    """Verifica se o PYTHONPATH está configurado corretamente no Dockerfile."""
    try:
        import src.main

        assert True
    except ImportError:
        assert False, "A pasta src não está no PYTHONPATH!"
