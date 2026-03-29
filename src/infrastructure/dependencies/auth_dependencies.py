from fastapi import Header


def get_current_user(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role"),
) -> dict:
    """
    Dependência mock para extrair o usuário autenticado dos headers da requisição.
    Será substituída pela autenticação real (Firebase/JWT) em sprints futuros.
    """
    return {"id": x_user_id, "role": x_user_role}
