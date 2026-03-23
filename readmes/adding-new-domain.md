# Guia: como adicionar um domínio do zero

Este guia segue o padrão atual do projeto (FastAPI + SQLAlchemy + DI por função + contracts no domínio).

## Quando criar um novo domínio

Crie um domínio novo quando a feature tiver regras próprias e ciclo de vida separado (ex.: `schools`, `routes`, `drivers`).

## Estrutura mínima esperada

```text
src/
  domains/
    <domain>/
      controller.py
      dtos.py
      entity.py
      repository.py
      service.py
      errors.py
  infrastructure/
    dependencies/
      <domain>_dependencies.py
    repositories/
      <domain>_repository.py
```

## Passo a passo (do zero)

### 1) Criar o pacote de domínio

1. Criar pasta `src/domains/<domain>/`.
2. Criar os arquivos base: `controller.py`, `dtos.py`, `entity.py`, `repository.py`, `service.py`.
3. Criar `errors.py` para exceções de negócio (ex.: conflito, entidade não encontrada).

### 2) Definir contratos da API (DTOs)

No `dtos.py`:

- Defina o modelo de entrada (ex.: `CreateX`).
- Defina o modelo de saída (ex.: `XResponse`).
- Use validações de campo com `Field(...)`.
- Quando retornar ORM model, usar `from_attributes = True` no DTO de saída.

### 3) Definir entidade persistente

No `entity.py`:

- Criar model SQLAlchemy com `Base` de `src.infrastructure.database`.
- Definir `__tablename__`.
- Definir constraints necessárias (`unique`, `nullable`, `index`).
- Manter apenas atributos do agregado; evitar lógica de infraestrutura aqui.

### 4) Definir interfaces do domínio

No `repository.py`:

- Criar interface `I<Domain>Repository` com métodos necessários (`save`, `find_by_id`, etc.).
- Criar outras interfaces auxiliares só se necessário (ex.: hasher, gateway externo).

Regra importante: a camada de domínio deve depender de interface, não de implementação concreta.

### 5) Implementar repositório concreto na infraestrutura

No `src/infrastructure/repositories/<domain>_repository.py`:

- Implementar `I<Domain>Repository`.
- Receber `Session` no construtor.
- Encapsular operações de persistência (`add`, `commit`, `refresh`, queries).

### 6) Criar injeção de dependências

No `src/infrastructure/dependencies/<domain>_dependencies.py`:

- `get_<domain>_repository(db=Depends(get_db))`
- `get_<domain>_service(...)`
- Injetar interfaces e implementações no mesmo padrão já existente.

### 7) Implementar regras de negócio no service

No `service.py`:

- Orquestrar regras de negócio (ex.: unicidade, transições de estado).
- Lançar exceções de domínio definidas em `errors.py`.
- Não usar `HTTPException` no service.

### 8) Criar endpoints no controller

No `controller.py`:

- Definir `APIRouter` com `prefix` e `tags`.
- Injetar o service com `Depends(get_<domain>_service)`.
- Traduzir exceções de domínio para HTTP (`HTTPException`) no controller.

### 9) Registrar router na aplicação

Em `src/main.py`:

1. Importar `router` do novo domínio.
2. Adicionar `app.include_router(...)`.

### 10) Criar e aplicar migrations

Após criar/alterar `entity.py`:

```bash
alembic revision --autogenerate -m "add <domain> table"
alembic upgrade head
```

### 11) Testar fluxo mínimo

Checklist mínimo de testes:

- sucesso de criação (`201`);
- violação de regra de negócio (ex.: duplicidade -> `400`);
- validação de payload inválido (`422`);
- persistência no banco.

## Checklist de PR (copiar e colar)

```md
- [ ] Estrutura do domínio criada em `src/domains/<domain>/`
- [ ] DTOs de entrada/saída definidos e validados
- [ ] Entidade criada/ajustada com constraints corretas
- [ ] Interface(s) no domínio criada(s)
- [ ] Implementação concreta em `src/infrastructure/repositories/`
- [ ] Arquivo de DI criado em `src/infrastructure/dependencies/`
- [ ] Service sem dependência de FastAPI (`HTTPException`)
- [ ] Controller traduz exceções de domínio para HTTP
- [ ] Router registrado em `src/main.py`
- [ ] Migration criada e aplicada
- [ ] Testes adicionados/atualizados
- [ ] `make lint` e `make test` executados
```

## Anti-patterns para evitar

- Service importando `fastapi` diretamente para lançar erro HTTP.
- Controller acessando banco direto, pulando service/repository.
- Dependência concreta sendo tipada no domínio em vez de interface.
- Criar domínio novo sem migration e sem testes.
