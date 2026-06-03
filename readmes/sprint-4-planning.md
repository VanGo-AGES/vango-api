# Sprint 4 — Planejamento de Tarefas (Backend VanGo)

> Metodologia: TDD com requisitos executáveis. As TKs de feature seguem o slice
> vertical **DTO → Repository → Service → Controller**, cada uma com testes já
> escritos e `@pytest.mark.skip(reason="USxx-TKnn")` nas ainda não implementadas.
> O setup do TDD vive na branch `chore/tdd-setup-sprint-4` (a partir de `dev`).

## Objetivo do Sprint

1. **Finalizar Métricas & Relatórios** (US15) — o FE já tem as telas (rodando em
   mock); falta o endpoint de agregação com filtros.
2. **US00 — Refatoração & Configuração** — enums de status, padronização de erros,
   logging estruturado, observabilidade e segurança de infra.
3. **Épico 5 — Acesso e Segurança** (US16–US20) — cadastro seguro, login com JWT,
   recuperação de senha por e-mail, logout e exclusão de conta.

## Decisões de arquitetura (fechadas com a Tech Lead)

- **Autenticação:** JWT puro. O header mock `X-User-Id`/`X-User-Role` é substituído
  por `get_current_user` real (Bearer token) em todos os controllers protegidos.
- **Recuperação de senha:** e-mail real (SMTP/SES).
- **Exclusão de conta:** soft delete com anonimização dos dados pessoais (PII),
  preservando o `id` para integridade do histórico de viagens/métricas.
- **Formato de erro:** mantém o `detail` atual e **adiciona** os campos
  `{code, message, details, trace_id}` (não quebra o FE nem os testes existentes).
- **Logout com JWT:** exige denylist de `jti` (revogação server-side) — custo aceito.

## Já estava pronto (não re-mapear)

- **Gate de CI** (coverage 90%, Ruff lint+format, Bandit, pip-audit, gitleaks) — já
  presente em `.github/workflows/run_tests.yml` e `pyproject.toml`.
- **Stack Loki + Promtail + Grafana** — já existe em `infra/observability/`
  (branch `chore/US00-TK13-observability-stack-loki-grafana`).

## Modelo de dependência / block-state (para o board)

- **TK de DTO:** sem bloqueio. Bloqueia as TKs de service/controller do mesmo slice.
- **TK de Repository:** sem bloqueio (testada via SQLite em memória, sem mocks de service).
- **TK de Service:** mocka repositórios/serviços externos → bloqueia **apenas** na TK de DTO.
- **TK de Controller:** precisa da stack real → bloqueia em **service + repos + DTO**.
- **TK de refactor/entity/infra:** entra direto no código; validada pela suíte
  existente verde (+ Ruff), não por testes novos com skip.

---

# US15 — Métricas & Relatórios

O FE (`trip-reports-screen.tsx`) consome 4 agregados — `distance` (km), `duration`
(min), `passengers`, `trips` — por `period` (`day`/`week`/`month`) e um range de
datas, escopados ao motorista logado. Hoje a tela roda 100% em mock
(`buildTripReportMetrics`). Esta US entrega o slice de backend que substitui o mock.

Dados de origem já existem: `TripModel` (`total_km`, `trip_date`, `started_at`,
`finished_at`, `status`), `TripPassangerModel` (`status`) e `RouteModel.driver_id`.

## US15 - TK01 — MetricsReportDTOs

### Descrição
Acesse a branch `dev` e crie a sua branch a partir dela. Abra o arquivo
`src/domains/metrics/dtos.py`.

Definir os contratos Pydantic da feature de relatórios. É a base do slice — as TKs
de service e controller dependem destes DTOs.

### O que fazer
- `ReportPeriod` (`str`, `Enum`): `DAY` = `"day"`, `WEEK` = `"week"`, `MONTH` = `"month"`.
- `MetricsReportResponse`: `distance: float`, `duration: int` (minutos),
  `passengers: int`, `trips: int`, `period: ReportPeriod`, `start_date: date`,
  `end_date: date`. Todos com defaults coerentes (zeros) para período sem viagens.
- A validação dos parâmetros de entrada (`period`, `start_date`, `end_date`) é feita
  no controller via `Query`; o DTO de saída não precisa receber os filtros crus.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US15-TK01")/d' tests/test_metrics/test_metrics_dto.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_metrics/test_metrics_dto.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_metrics/test_metrics_dto.py -v`

Atenção: Não modifique o arquivo de testes!

## US15 - TK02 — TripMetricsRepository

### Descrição
Abra `src/infrastructure/repositories/trip_metrics_repository.py`. A interface
`ITripMetricsRepository` já está em `src/domains/metrics/repository.py`.

Implementar a query de agregação que alimenta os relatórios. Tudo em uma única
passada no banco, filtrando pelo motorista e pelo intervalo de datas.

### O que fazer
- `aggregate_driver_metrics(driver_id: UUID, start: datetime, end: datetime) -> MetricsAggregate`
  onde `MetricsAggregate` é um dataclass/named tuple com:
  - `total_km: float` — `SUM(trips.total_km)` das trips finalizadas no intervalo.
  - `total_duration_seconds: int` — `SUM(finished_at - started_at)` das trips finalizadas.
  - `passengers: int` — `COUNT` de `trip_passangers` com status embarcado/presente
    das trips do motorista no intervalo.
  - `trips: int` — `COUNT` de trips finalizadas do motorista no intervalo.
- Join `trips → routes` por `routes.id = trips.route_id` e filtro `routes.driver_id`.
- Considerar apenas trips com status finalizado e `trip_date` (ou `finished_at`)
  dentro de `[start, end]`.
- Retornar zeros (não `None`) quando não houver trips no intervalo.
- Nunca misturar trips de outro motorista no resultado.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US15-TK02")/d' tests/test_metrics/test_trip_metrics_repository.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_metrics/test_trip_metrics_repository.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_metrics/test_trip_metrics_repository.py -v`

Atenção: Não modifique o arquivo de testes!

## US15 - TK03 — MetricsService

### Descrição
Abra `src/domains/metrics/service.py`. Implementar `MetricsService.get_report`,
que traduz o período em um intervalo de datas, chama o repositório e mapeia o
resultado para o DTO.

### O que fazer
- `get_report(driver_id: UUID, period: ReportPeriod, start_date: date, end_date: date | None) -> MetricsReportResponse`.
- Derivar o intervalo `[start, end]`:
  - `DAY`: o dia inteiro de `start_date` (`00:00`–`23:59:59`).
  - `WEEK`: de `start_date` até `end_date` (ou +6 dias se `end_date` ausente).
  - `MONTH`: do primeiro ao último dia do mês de `start_date`.
- Converter `total_duration_seconds` para minutos (inteiro, arredondado) no campo `duration`.
- Repassar `total_km` para `distance`, contagens para `passengers`/`trips`.
- Retornar zeros quando o repositório não trouxer registros.
- Depende de `ITripMetricsRepository` injetado (mockado nos testes deste TK).

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US15-TK03")/d' tests/test_metrics/test_metrics_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_metrics/test_metrics_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_metrics/test_metrics_service.py -v`

Atenção: Não modifique o arquivo de testes!

## US15 - TK04 — MetricsController (GET /metrics/reports)

### Descrição
Abra `src/domains/metrics/controller.py`. Expor o endpoint de relatórios consumido
pela tela `trip-reports-screen`.

### O que fazer
- `GET /metrics/reports?period=&start_date=&end_date=` (todos via `Query`).
- `period` validado contra `ReportPeriod`; `start_date` obrigatório; `end_date`
  opcional (usado no `WEEK`).
- `driver_id` extraído do usuário autenticado (`get_current_user` — ver US17-TK02).
- Retorna `MetricsReportResponse` (200). `422` para `period`/datas inválidas.
- Registrar o router no `src/main.py`.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US15-TK04")/d' tests/test_metrics/test_metrics_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_metrics/test_metrics_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_metrics/test_metrics_controller.py -v`

Atenção: Não modifique o arquivo de testes!

> Decisão registrada: a tela *por viagem* (`trip-metrics-screen`) usa params do
> fluxo de finish; os dados já vêm no `TripResponse`. **Não** criamos endpoint
> dedicado para ela neste sprint.

---

# US00 — Refatoração & Configuração

> Numeração nova a partir de **TK14** (TK11 e TK13 já existem em branches).
> A maioria são refactors/infra: entram direto no código e são validados pela
> suíte existente verde + Ruff, não por testes novos com skip (exceções sinalizadas).

## US00 - TK14 — Enums de status (eliminar magic strings)

### Descrição
Centralizar os status hoje espalhados como strings cruas (~216 ocorrências) em
enums tipados, sem mudar os valores persistidos.

### O que fazer
- Criar `src/domains/<dominio>/enums.py` (ou um `src/shared/enums.py`) com:
  - `TripStatus(str, Enum)`: `INICIADA="iniciada"`, `FINALIZADA="finalizada"`, `CANCELADA="cancelada"`.
  - `TripPassangerStatus(str, Enum)`: `PENDENTE="pendente"`, `PRESENTE="presente"`, `AUSENTE="ausente"`.
  - `RoutePassangerStatus(str, Enum)`: `PENDING="pending"`, `ACCEPTED="accepted"`, `REJECTED="rejected"`.
- Herdar de `str` para manter compatibilidade com colunas `String` e respostas JSON.
- Substituir as strings cruas em services/repositories/controllers pelos enums.
- **Não** alterar os valores em si nem criar migration.

### Como testar (TDD)
1. Rode a suíte inteira e garanta que continua verde (nenhum teste deve mudar):
   - `pytest -q`
2. Rode o lint:
   - `ruff check src/ tests/`
3. (Opcional) há um teste de sanidade em `tests/test_shared/test_enums.py`
   conferindo os valores dos enums — remova o skip e rode:
   - `sed -i '/@pytest.mark.skip(reason="US00-TK14")/d' tests/test_shared/test_enums.py && pytest tests/test_shared/test_enums.py -v`

Atenção: refactor não pode alterar comportamento — se algum teste existente quebrar,
o valor do enum divergiu da string original.

## US00 - TK15 — DomainError base + exception handler global + ErrorResponse DTO (piloto)

### Descrição
Criar a base de tratamento de erros centralizado: uma hierarquia `DomainError` com
`code` e `status_code`, um exception handler global que a converte em resposta HTTP
padronizada, e o DTO de erro. Adotar em **um** domínio piloto (ex.: `users`).

### O que fazer
- `src/shared/errors.py`: `class DomainError(Exception)` com atributos `code: str`,
  `status_code: int`, `message: str`, `details: dict | None`.
- Fazer os erros existentes (ex.: `UserNotFoundError`, `DuplicateEmailError`) herdarem
  de `DomainError` com `code`/`status_code` apropriados.
- `src/domains/shared/dtos.py` (ou similar): `ErrorResponse` com
  `detail: str`, `code: str`, `message: str`, `details: dict | None`, `trace_id: str | None`.
  > Mantém `detail` para compatibilidade com o FE/testes; adiciona os demais.
- `src/main.py`: registrar `@app.exception_handler(DomainError)` que monta o
  `ErrorResponse` (status vindo do erro, `trace_id` vindo do correlation id da request).
- Piloto: remover os `try/except` do controller de `users`, deixando o handler global
  resolver. Demais controllers ficam para a TK16.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US00-TK15")/d' tests/test_shared/test_error_handler.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_shared/test_error_handler.py tests/test_user/test_user_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_shared/test_error_handler.py tests/test_user/test_user_controller.py -v`

Atenção: os asserts de status code e do campo `detail` nos testes de integração
existentes devem continuar passando — o shape antigo é preservado.

## US00 - TK16 — Migrar controllers restantes para o handler global

### Descrição
Estender o padrão da TK15 aos demais controllers, removendo os ~100 blocos
`try/except` espalhados (absences, dependents, route_passangers, routes, trips, vehicles).

### O que fazer
- Garantir que todos os erros levantados pelos services herdam de `DomainError`
  com `code`/`status_code` corretos.
- Remover os `try/except`/`raise HTTPException` dos controllers, deixando o handler
  global responder.
- Manter exatamente os mesmos status codes que os controllers retornavam antes.

### Como testar (TDD)
1. Rode os testes de integração de todos os controllers e garanta que continuam verdes:
   - `pytest tests/test_absence tests/test_dependent tests/test_route_passanger tests/test_route tests/test_trip tests/test_vehicle -v`
2. Rode o lint:
   - `ruff check src/ tests/`

Atenção: refactor — nenhum teste de controller deve precisar mudar (status codes e
`detail` preservados).

## US00 - TK17 — Logging estruturado + correlation id

### Descrição
Configurar logging estruturado (JSON) e um middleware de correlation/request id, base
para o trace_id do handler de erros e para os dashboards do Grafana/Loki.

### O que fazer
- Adicionar `loguru` (ou `structlog`) e configurar saída JSON.
- `src/infrastructure/middleware/request_id.py`: middleware que gera/propaga
  `X-Request-Id`, guarda em contextvar e injeta no log de cada request (método, path,
  status, latência ms, request_id).
- Expor o `request_id` para o exception handler (US00-TK15) preencher `trace_id`.
- Registrar o middleware no `src/main.py`.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US00-TK17")/d' tests/test_shared/test_request_id_middleware.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_shared/test_request_id_middleware.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_shared/test_request_id_middleware.py -v`

Atenção: Não modifique o arquivo de testes!

## US00 - TK18 — Adotar logger e eliminar prints

### Descrição
Substituir os `print(...)` (lifespan do `main.py` e afins) e o
`traceback.print_exc` por chamadas de logger estruturado, e adicionar logs em pontos-chave
(start/finish de trip, envio de notificação, falhas de integração externa).

### O que fazer
- Trocar todos os `print(` por `logger.info/error` com contexto.
- Amarrar o log de erro ao `request_id`/`trace_id`.
- Garantir que nenhum `print(` permaneça em `src/` (a CI pode passar a barrar via Ruff `T201`).

### Como testar (TDD)
1. Garanta que não há mais prints no código de produção:
   - `! grep -rn "print(" src/`
2. Rode a suíte e o lint:
   - `pytest -q && ruff check src/ tests/`

Atenção: refactor — comportamento inalterado.

## US00 - TK19 — Health check estendido

### Descrição
Expandir `GET /health` para checar dependências externas e expor versão/commit.

### O que fazer
- Checar DB (já feito), Mapbox (ping leve/configuração) e Firebase (app inicializado).
- Retornar `status` agregado (`ok`/`degraded`), o status de cada dependência, e
  `version`/`commit` (de env var `GIT_COMMIT`/`APP_VERSION` ou arquivo).
- Status `200` quando tudo ok; `503` quando alguma dependência crítica estiver down.

### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US00-TK19")/d' tests/test_shared/test_health.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_shared/test_health.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_shared/test_health.py -v`

Atenção: Não modifique o arquivo de testes!

## US00 - TK20 — HTTPS (domínio + Route53 + ACM + ALB listener)

### Descrição
Infra (Terraform, sem TDD): habilitar HTTPS de ponta a ponta no ambiente de deploy.

### O que fazer
- Comprar/registrar o domínio e criar a zona no Route53.
- Provisionar o certificado no ACM (validação via DNS) na região do ALB.
- Adicionar o listener HTTPS (443) no ALB apontando para o target group da API.
- Redirecionar 80 → 443.
- Versionar em `infra/` (`.tf`), seguindo a convenção do diretório.

### Como testar
- `terraform plan`/`apply` no ambiente de staging.
- `curl -I https://<dominio>/health` retorna `200` com TLS válido; `http://` redireciona.

## US00 - TK21 — Secrets Manager dedicado

### Descrição
Infra (sem TDD): mover segredos (DATABASE_URL, MAPBOX_API_KEY, JWT_SECRET, credenciais
SMTP/SES, Firebase) para um secrets manager dedicado em vez de `.env`/variáveis soltas.

### O que fazer
- Criar os secrets no AWS Secrets Manager (ou equivalente) e a policy de leitura para a task/instância.
- Ajustar o boot da app para carregar do secrets manager (mantendo `.env` como fallback de dev).
- Garantir que nenhum segredo fica versionado (gitleaks já cobre na CI).

### Como testar
- App sobe lendo os secrets do manager em staging; `/health` ok.
- `firebase_service_account.json` e afins fora do repositório.

## US00 - TK22 — Sentry (backend)

### Descrição
Infra (sem TDD pesado): error tracking no backend FastAPI.

### O que fazer
- Adicionar `sentry-sdk[fastapi]`, inicializar com DSN via config/secrets.
- Integrar com o middleware de request id: enviar `request_id`/`trace_id` como tag.
- Filtrar PII e setar `environment`/`release` (commit).

### Como testar
- Disparar um erro proposital em staging e confirmar o evento no Sentry com a tag `request_id`.

## US00 - TK23 — Sentry (frontend)

### Descrição
Infra no `vango-frontend` (sem TDD — frontend não segue o fluxo TDD do backend).

### O que fazer
- Instalar e configurar `@sentry/react-native`.
- Configurar upload de sourcemaps no build (EAS/CI).
- Setar `environment`/`release` alinhados com o backend.

### Como testar
- Crash/erro de teste aparece no Sentry com stack desofuscada via sourcemap.

## US00 - TK24 — Prometheus (métricas da aplicação)

### Descrição
Infra (sem TDD): expor métricas da API para o Prometheus, base para os dashboards de
req/min, p95 de latência e taxa de erro do Grafana.

### O que fazer
- Adicionar `prometheus-fastapi-instrumentator` (ou `prometheus_client`) e expor `/metrics`.
- Instrumentar contadores/histogramas de request (por rota, método, status) e latência.
- Criar `infra/observability/prometheus/prometheus.yml` com o scrape job da API.
- Adicionar o service `prometheus` no `docker-compose.observability.yml` (imagem pinada,
  volume persistente) e o data source Prometheus no provisioning do Grafana.

### Como testar
- `curl localhost:<porta>/metrics` retorna métricas no formato Prometheus.
- Subindo a stack de observabilidade, o target da API aparece `UP` no Prometheus.

## US00 - TK25 — Dashboards Grafana (req/min, p95, error rate)

### Descrição
Infra (sem TDD): dashboards básicos de saúde da API a partir do Prometheus (TK24) e
dos logs do Loki (já existente).

### O que fazer
- Provisionar dashboards versionados em `infra/observability/grafana/provisioning/dashboards/`.
- Painéis: requisições/min, p95 de latência, taxa de erro (4xx/5xx), e um painel de logs
  filtrável por `request_id` (Loki).
- Auto-provisionar no boot do Grafana (sem criar manual na UI).

### Como testar
- Subir a stack; dashboards aparecem automaticamente e populam com tráfego de teste.

---

# Épico 5 — Acesso e Segurança (US16–US20)

## US16 — Cadastro de usuário e senha

> Registro, hash bcrypt e unicidade de e-mail **já existem** (`UserService.create_user`).
> Falta apenas reforçar as regras de senha.

### US16 - TK01 — Regras de senha no cadastro

#### Descrição
Abra `src/domains/users/dtos.py`. Reforçar a política de senha no `UserCreate`
(hoje só `min_length=6`).

#### O que fazer
- Validador de senha (field/model validator) exigindo as regras definidas:
  comprimento mínimo (ex.: 8), ao menos uma letra maiúscula, uma minúscula, um dígito
  e um caractere especial.
- Mensagem de erro clara e específica por regra violada (vira `422`).
- Aplicar a mesma regra onde a senha é trocada (`UserUpdate.password` e, depois,
  no reset de senha da US18) — extrair para um helper reutilizável
  `src/domains/users/password_rules.py`.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US16-TK01")/d' tests/test_user/test_password_rules.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_password_rules.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_password_rules.py -v`

Atenção: Não modifique o arquivo de testes!

## US17 — Login com JWT

### US17 - TK01 — Token service + settings (JWT)

#### Descrição
Abra `src/infrastructure/auth/jwt_token_service.py`. A interface `ITokenService`
fica em `src/domains/users/auth.py`. Encapsular emissão e verificação de JWT.

#### O que fazer
- Adicionar em `config.py`: `jwt_secret`, `jwt_algorithm` (default `HS256`),
  `jwt_access_token_expire_minutes`.
- `ITokenService.create_access_token(user_id: UUID, role: str, jti: str | None = None) -> str`.
- `ITokenService.decode_token(token: str) -> TokenPayload` (levanta erro de domínio
  quando inválido/expirado).
- `TokenPayload` (DTO): `sub` (user_id), `role`, `jti`, `exp`.
- Usar `PyJWT` (já no `requirements.txt`).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK01")/d' tests/test_auth/test_jwt_token_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_jwt_token_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_jwt_token_service.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK02 — get_current_user real (Bearer)

#### Descrição
Abra `src/infrastructure/dependencies/auth_dependencies.py`. Substituir o mock
(que lê `X-User-Id`/`X-User-Role`) pela dependência real baseada em JWT.

#### O que fazer
- `get_current_user` extrai o `Authorization: Bearer <token>`, decodifica via
  `ITokenService`, carrega o usuário e retorna a identidade autenticada.
- `401` quando o token está ausente, inválido ou expirado.
- (Gancho para US19) verificar a denylist de `jti` — a checagem real é ligada na US19-TK02.
- Deixar um helper opcional para extrair só o `user_id` (conveniência dos controllers).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK02")/d' tests/test_auth/test_get_current_user.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_get_current_user.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_get_current_user.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK03 — LoginResponse DTO + AuthService.login emitindo JWT

#### Descrição
Abra `src/domains/users/service.py` (ou um novo `AuthService`). Evoluir o login
intermediário para emitir o token.

#### O que fazer
- `LoginResponse` (DTO): `access_token: str`, `token_type: str = "bearer"`, `user: UserResponse`.
- `login(email, password) -> LoginResponse`: valida credenciais (já existe), gera o
  `jti`, emite o access token via `ITokenService` e devolve `LoginResponse`.
- Mantém `UserNotFoundError` (404) e `InvalidCredentialsError` (401).
- Bloquear login de usuário inativo/anonimizado (gancho que a US20-TK03 completa).
- Service mocka `ITokenService` e o repo nos testes deste TK.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK03")/d' tests/test_auth/test_auth_service_login.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_auth_service_login.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_auth_service_login.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK04 — Login controller retornando token

#### Descrição
Abra `src/domains/users/controller.py`. Atualizar `POST /users/login` (ou novo
`POST /auth/login`) para retornar `LoginResponse`.

#### O que fazer
- `response_model=LoginResponse`, `200` em sucesso.
- `400/422` para corpo inválido; `401` para credenciais incorretas; `404` para e-mail
  inexistente (mantendo o contrato atual).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK04")/d' tests/test_auth/test_auth_login_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_auth_login_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_auth_login_controller.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK05 — Migrar controllers de X-User-Id para get_current_user

#### Descrição
Refactor transversal: trocar a dependência mock (`X-User-Id`/`X-User-Role`) pela
dependência real de autenticação nos 6 controllers protegidos (absences,
route_passangers, routes, trips, users, metrics) e atualizar os testes de
integração para enviar `Authorization: Bearer`. A escolha entre `get_current_user`
e `get_current_driver` por endpoint segue a matriz da **US17-TK07**.

#### O que fazer
- Substituir `Header(alias="X-User-Id")` por `Depends(get_current_user)` (ou
  `Depends(get_current_driver)` nos endpoints driver-only — ver TK07) em cada endpoint protegido.
- Centralizar a geração de token de teste num helper em `tests/conftest.py`
  (fixture que cria usuário + token).
- Atualizar todos os testes de integração que hoje mandam `X-User-Id`.
- Endpoints públicos (registro, login, refresh, forgot/reset de senha) ficam **sem** auth.

#### Como testar (TDD)
1. Rode a suíte de integração inteira e garanta verde após a migração:
   - `pytest tests/test_absence tests/test_route_passanger tests/test_route tests/test_trip tests/test_user tests/test_metrics -v`
2. Garanta que nenhum `X-User-Id` permanece em `src/`:
   - `! grep -rn "X-User-Id" src/`

Atenção: este é o TK de maior risco do sprint — toca todos os controllers protegidos.
Os testes de integração **podem** e **devem** ser ajustados aqui (não é um TK de
feature com testes congelados, e sim a migração da autenticação).

### US17 - TK06 — GET /users/me (perfil do usuário logado)

**Bloqueado por:** US17-TK02 (`get_current_user`).

#### Descrição
Abra `src/domains/users/auth_controller.py`. Expor o endpoint que devolve o perfil
do usuário autenticado, consumido pelo app após o login para hidratar a sessão.

#### O que fazer
- `GET /users/me`, protegido por `Depends(get_current_user)`, `response_model=UserResponse`.
- Retornar o próprio `current_user` (o FastAPI serializa via `UserResponse` — não expõe `password_hash`).
- Sem token / token inválido → **401** (vem da cadeia `get_current_token_payload`).
- Não criar service novo: é leitura direta do usuário já resolvido pela dependência.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK06")/d' tests/test_user/test_me_endpoint.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_me_endpoint.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_me_endpoint.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK07 — get_current_driver (autorização por papel / RBAC)

**Bloqueado por:** US17-TK02 (`get_current_user`).

#### Descrição
Abra `src/infrastructure/auth/dependencies.py`. Criar a dependência de autorização
que restringe endpoints a motoristas, reaproveitando o `get_current_user`. O perfil
de cada endpoint foi confirmado no front (`vango-frontend`) pelo header usado em
cada chamada (`getDriverHeaders` vs `getPassangerHeaders`).

#### O que fazer
- `get_current_driver(current_user = Depends(get_current_user)) -> UserModel`.
- Se `current_user.role == "driver"`: retorna o usuário. Caso contrário:
  `raise HTTPException(status_code=403, detail=...)` (o teste fixa `HTTPException`, não erro de domínio).
- Aplicar a dependência correta em cada endpoint protegido (junto com a US17-TK05):

**Motorista — usar `Depends(get_current_driver)`:**
- `POST /routes/{route_id}/trips` (start_trip)
- `GET /trips/{trip_id}` (get_trip)
- `GET /trips/{trip_id}/next-stop` (get_next_stop)
- `POST /trips/{trip_id}/passangers/{trip_passanger_id}/board` (board_passanger)
- `POST /trips/{trip_id}/passangers/{trip_passanger_id}/absent` (mark_passanger_absent)
- `POST /trips/{trip_id}/passangers/{trip_passanger_id}/alight` (alight_passanger)
- `POST /trips/{trip_id}/stops/{stop_id}/skip` (skip_stop)
- `POST /trips/{trip_id}/finish` (finish_trip)
- `POST /routes/` (create_route)
- `GET /routes/` (list_routes)
- `GET /routes/{route_id}` (get_route)
- `PUT /routes/{route_id}` (update_route)
- `DELETE /routes/{route_id}` (delete_route)
- `POST /routes/{route_id}/invite-code/regenerate` (regenerate_invite_code)
- `GET /routes/{route_id}/passangers` (list_passangers)
- `POST /routes/{route_id}/passangers/{rp_id}/accept` (accept_request)
- `POST /routes/{route_id}/passangers/{rp_id}/reject` (reject_request)
- `DELETE /routes/{route_id}/passangers/{rp_id}` (remove_passanger)
- `GET /metrics/reports` (get_report)

**Passageiro/responsável (dono) — `Depends(get_current_user)` + checagem de posse no service:**
- `GET /routes/me` (list_my_routes)
- `GET /routes/{route_id}/me` (get_my_route_detail)
- `POST /routes/{route_id}/passangers` (join_route)
- `DELETE /routes/{route_id}/passangers/me` (leave_route)
- `PATCH /routes/{route_id}/passangers/me` (update_schedules)
- `GET /routes/invite/{invite_code}` (get_route_by_invite_code)
- `POST /absences` (report_absence)

**Dual (motorista E passageiro) — `Depends(get_current_user)` + lógica por papel no service:**
- `GET /routes/{route_id}/trips/current` — motorista (recuperação do 409) e passageiro consomem.
- `GET /routes/{route_id}/absences` — motorista e passageiro consomem.

**Qualquer autenticado — `Depends(get_current_user)`:** `GET /users/me`, `DELETE /users/me`, `POST /auth/logout`.
**Público (sem auth):** `POST /auth/login`, `POST /auth/refresh`, `POST /auth/password/forgot`, `POST /auth/password/reset`, `POST /users/` (cadastro).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK07")/d' tests/test_auth/test_get_current_driver.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_get_current_driver.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_get_current_driver.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK08 — refresh_tokens (entity + repository + migration)

**Sem bloqueio** (testado via SQLite em memória).

#### Descrição
Abra `src/domains/users/refresh_token_entity.py` e
`src/infrastructure/repositories/refresh_token_repository.py`. A interface
`IRefreshTokenRepository` fica em `src/domains/users/refresh_token_repository.py`.

#### O que fazer
- Entity `RefreshTokenModel`: `id`, `user_id` (FK CASCADE), `token_hash` (único),
  `expires_at`, `revoked_at: datetime | None`, `created_at`. (Guardar **hash** do token, nunca o valor cru.)
- Repo: `create(user_id, token_hash, expires_at) -> model`,
  `find_valid(token_hash) -> model | None` (não expirado e não revogado),
  `revoke(token_id)`, `revoke_all_for_user(user_id) -> int`.
- Migration `d5e6f7a8b9c0` já criada e aplicada; entity já registrada em `main.py`/`conftest.py`/`env.py`.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK08")/d' tests/test_auth/test_refresh_token_repository.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_refresh_token_repository.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_refresh_token_repository.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK09 — AuthService: login emite refresh + refresh() com rotação

**Bloqueado por:** US17-TK08 (repo de refresh) e US17-TK01 (token service).

#### Descrição
Abra `src/domains/users/auth_service.py`. Fazer o `login` emitir também um refresh
token e implementar `refresh()` com rotação.

#### O que fazer
- `LoginResponse` ganha `refresh_token: str | None`. No `login`, gerar o refresh
  (valor opaco via `secrets`), persistir o **hash** (`refresh_token_repository.create`)
  e devolver o valor cru no response.
- `refresh(refresh_token) -> LoginResponse`: valida via `find_valid`; se válido,
  **rotaciona** (emite novo access+refresh, revoga o usado via `revoke`); se inválido/
  expirado/revogado, `raise InvalidRefreshTokenError`.
- Service mocka os repositórios nos testes deste TK.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK09")/d' tests/test_auth/test_refresh_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_refresh_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_refresh_service.py -v`

Atenção: Não modifique o arquivo de testes!

### US17 - TK10 — POST /auth/refresh (controller)

**Bloqueado por:** US17-TK09.

#### Descrição
Abra `src/domains/users/auth_controller.py`. Expor o endpoint público que troca um
refresh token válido por um novo par de tokens.

#### O que fazer
- `POST /auth/refresh`, body `RefreshRequest { refresh_token }`, `response_model=LoginResponse`, `200`.
- Refresh inválido/expirado/revogado → **401**.
- Público (não exige Bearer): é justamente o mecanismo para renovar o access expirado.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US17-TK10")/d' tests/test_auth/test_refresh_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_refresh_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_refresh_controller.py -v`

Atenção: Não modifique o arquivo de testes!

## US18 — Recuperação de senha (e-mail real)

### US18 - TK01 — Email infra (IEmailService + SMTP/SES)

#### Descrição
Abra `src/infrastructure/email/`. Criar a abstração de envio de e-mail e a impl
SMTP/SES, com config dedicada.

#### O que fazer
- `IEmailService.send(to: str, subject: str, body_html: str, body_text: str | None) -> None`
  em `src/domains/users/email.py`.
- Impl `SmtpEmailService` (ou `SesEmailService`) em `src/infrastructure/email/`.
- Config: host/port/user/password/from (ou credenciais SES) via `config.py`/secrets.
- Helper para montar o e-mail de reset (link/token).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US18-TK01")/d' tests/test_auth/test_email_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_email_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_email_service.py -v`

Atenção: os testes mockam o transporte SMTP/SES — não enviam e-mail de verdade.

### US18 - TK02 — password_reset_tokens (entity + repository + migration)

#### Descrição
Abra `src/domains/users/reset_token_entity.py` e
`src/infrastructure/repositories/password_reset_token_repository.py`. A interface
`IPasswordResetTokenRepository` fica em `src/domains/users/repository.py`.

#### O que fazer
- Entity `PasswordResetTokenModel`: `id`, `user_id` (FK), `token_hash`, `expires_at`,
  `used_at: datetime | None`, `created_at`.
- Repo: `create(user_id, token_hash, expires_at)`, `find_valid(token_hash) -> model | None`
  (não expirado e não usado), `mark_used(id)`.
- Migration Alembic criando a tabela. Registrar a entity no `main.py`/`conftest.py`.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US18-TK02")/d' tests/test_auth/test_password_reset_token_repository.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_password_reset_token_repository.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_password_reset_token_repository.py -v`

Atenção: Não modifique o arquivo de testes!

### US18 - TK03 — DTOs de recuperação de senha

#### Descrição
Abra `src/domains/users/dtos.py`. DTOs do fluxo de reset.

#### O que fazer
- `ForgotPasswordRequest`: `email: EmailStr`.
- `ResetPasswordConfirm`: `token: str`, `new_password: str` (reaproveita o helper de
  regras de senha da US16-TK01).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US18-TK03")/d' tests/test_auth/test_reset_password_dto.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_reset_password_dto.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_reset_password_dto.py -v`

Atenção: Não modifique o arquivo de testes!

### US18 - TK04 — AuthService.request_reset + reset_password

#### Descrição
Abra `src/domains/users/service.py`. Orquestrar o fluxo de recuperação.

#### O que fazer
- `request_password_reset(email)`: se o e-mail existir, gera token, persiste o hash
  (via repo) e dispara o e-mail (via `IEmailService`). **Não vaza** se o e-mail existe
  (resposta neutra de sucesso, para não permitir enumeração de usuários).
- `reset_password(token, new_password)`: valida o token (`find_valid`), aplica as
  regras de senha, atualiza o hash, marca o token como usado e revoga sessões/tokens
  ativos (gancho US19).
- Erros de domínio para token inválido/expirado/usado.
- Service mocka repo + email nos testes.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US18-TK04")/d' tests/test_auth/test_password_reset_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_password_reset_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_password_reset_service.py -v`

Atenção: Não modifique o arquivo de testes!

### US18 - TK05 — Controllers de recuperação de senha

#### Descrição
Abra `src/domains/users/controller.py` (ou `auth_controller.py`). Endpoints públicos
do fluxo de reset.

#### O que fazer
- `POST /auth/password/forgot` (body `ForgotPasswordRequest`) → `200` neutro sempre.
- `POST /auth/password/reset` (body `ResetPasswordConfirm`) → `200` em sucesso;
  `400/422` para token inválido/expirado/usado ou senha fora das regras.
- Ambos **sem** autenticação.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US18-TK05")/d' tests/test_auth/test_password_reset_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_password_reset_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_password_reset_controller.py -v`

Atenção: Não modifique o arquivo de testes!

## US19 — Logout (denylist de token)

### US19 - TK01 — Token denylist (entity + repository + migration)

#### Descrição
Abra `src/domains/users/revoked_token_entity.py` e
`src/infrastructure/repositories/revoked_token_repository.py`. Interface
`IRevokedTokenRepository` em `src/domains/users/repository.py`. Suporta revogação real
de JWT no logout.

#### O que fazer
- Entity `RevokedTokenModel`: `jti` (PK ou unique), `user_id`, `expires_at`, `revoked_at`.
- Repo: `revoke(jti, user_id, expires_at)`, `is_revoked(jti) -> bool`.
- Migration Alembic. Registrar a entity. (Opcional: housekeeping de jti expirados.)

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US19-TK01")/d' tests/test_auth/test_revoked_token_repository.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_revoked_token_repository.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_revoked_token_repository.py -v`

Atenção: Não modifique o arquivo de testes!

### US19 - TK02 — AuthService.logout + checagem na get_current_user

#### Descrição
Abra `src/domains/users/service.py` e
`src/infrastructure/dependencies/auth_dependencies.py`. Ligar a revogação ao fluxo de auth.

#### O que fazer
- `logout(token_payload)`: revoga o `jti` atual via `IRevokedTokenRepository` até o `exp`.
- `get_current_user` (US17-TK02) passa a checar `is_revoked(jti)` → `401` se revogado.
- Service mocka o repo nos testes.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US19-TK02")/d' tests/test_auth/test_logout_service.py tests/test_auth/test_get_current_user_revocation.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_logout_service.py tests/test_auth/test_get_current_user_revocation.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_logout_service.py tests/test_auth/test_get_current_user_revocation.py -v`

Atenção: Não modifique o arquivo de testes!

### US19 - TK03 — Controller POST /auth/logout

#### Descrição
Abra `src/domains/users/controller.py`. Endpoint de logout (autenticado).

#### O que fazer
- `POST /auth/logout` protegido por `get_current_user`; revoga o token atual.
- `204` em sucesso. Token revogado não acessa mais áreas protegidas.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US19-TK03")/d' tests/test_auth/test_logout_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_auth/test_logout_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_auth/test_logout_controller.py -v`

Atenção: Não modifique o arquivo de testes!

## US20 — Exclusão de conta (soft delete + anonimização)

### US20 - TK01 — Entity + migration (deleted_at, is_active)

#### Descrição
Refactor de entidade (entra direto no código): adicionar campos de soft delete ao
`UserModel`.

#### O que fazer
- Em `src/domains/users/entity.py`: `is_active: bool` (default `True`),
  `deleted_at: datetime | None`.
- Migration Alembic adicionando as colunas (com default que preserva os usuários atuais ativos).
- Registrar no `conftest.py` se necessário.

#### Como testar (TDD)
1. Rode a suíte e garanta que continua verde (entidade nova não quebra nada):
   - `pytest -q`
2. Gere/aplique a migration localmente:
   - `alembic upgrade head`

Atenção: entity/migration — sem testes novos com skip.

### US20 - TK02 — Repository: soft-delete + anonimização

#### Descrição
Abra `src/infrastructure/repositories/user_repository.py`. Implementar a remoção
lógica com scrub de PII.

#### O que fazer
- `soft_delete_and_anonymize(user_id) -> bool`: seta `is_active=False`, `deleted_at=now()`
  e anonimiza PII — `name` → `"Usuário removido"`, `email` → valor único anonimizado
  (ex.: `deleted+<id>@vango.invalid` para respeitar a constraint unique), `phone`/`cpf`/
  `photo_url`/`push_token` → `None`/placeholder.
- Mantém o `id` e o histórico de viagens/métricas intactos (não cascateia delete).
- Retorna `False` se o usuário não existir.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US20-TK02")/d' tests/test_user/test_user_soft_delete_repository.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_user_soft_delete_repository.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_user_soft_delete_repository.py -v`

Atenção: Não modifique o arquivo de testes!

### US20 - TK03 — Finders excluem usuários inativos

#### Descrição
Abra `src/infrastructure/repositories/user_repository.py`. Garantir que usuários
soft-deletados não voltem em buscas nem consigam logar.

#### O que fazer
- `find_by_email` (usado no login) e `find_by_id` filtram `is_active = True`
  (ou um parâmetro `include_inactive=False` por padrão).
- `find_all` não retorna inativos.
- Login de conta inativa → `InvalidCredentialsError`/`UserNotFoundError` (não vaza estado).

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US20-TK03")/d' tests/test_user/test_user_finders_active.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_user_finders_active.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_user_finders_active.py -v`

Atenção: Não modifique o arquivo de testes! Rode também a suíte de usuário inteira
para garantir que os finders ajustados não quebraram os fluxos existentes.

### US20 - TK04 — Service.delete_account

#### Descrição
Abra `src/domains/users/service.py`. Orquestrar a exclusão com confirmação e
revogação de sessão.

#### O que fazer
- `delete_account(user_id, confirm: bool)`: exige confirmação; chama
  `soft_delete_and_anonymize`; revoga o(s) token(s) ativo(s) (via US19 repo).
- `UserNotFoundError` se não existir; erro de domínio se `confirm` não for verdadeiro.
- Service mocka os repos nos testes.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US20-TK04")/d' tests/test_user/test_delete_account_service.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_delete_account_service.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_delete_account_service.py -v`

Atenção: Não modifique o arquivo de testes!

### US20 - TK05 — Controller DELETE /users/me

#### Descrição
Abra `src/domains/users/controller.py`. Endpoint autenticado de exclusão da própria conta.

#### O que fazer
- `DELETE /users/me` protegido por `get_current_user`, com confirmação (body/flag).
- `204` em sucesso; sessão encerrada; conta inacessível depois.
- Depreciar o `DELETE /users/{id}` (hard delete) ou restringir o uso.

#### Como testar (TDD)
1. Remova o skip dos testes da task rodando:
   - `sed -i '/@pytest.mark.skip(reason="US20-TK05")/d' tests/test_user/test_delete_account_controller.py`
2. Rode os testes para ver eles falhar (vermelho):
   - `pytest tests/test_user/test_delete_account_controller.py -v`
3. Implemente o código.
4. Rode os testes novamente para ver eles passar (verde):
   - `pytest tests/test_user/test_delete_account_controller.py -v`

Atenção: Não modifique o arquivo de testes!

---

## Resumo (35 TKs)

| US | TKs | Tipo |
|----|-----|------|
| US15 — Métricas & Relatórios | TK01 DTO, TK02 Repo, TK03 Service, TK04 Controller | TDD (slice) |
| US00 — Refatoração & Config | TK14 Enums, TK15 ErrorHandler, TK16 Migrar controllers, TK17 Logging, TK18 Prints→logger, TK19 Health, TK20 HTTPS, TK21 Secrets, TK22 Sentry BE, TK23 Sentry FE, TK24 Prometheus, TK25 Dashboards | Refactor + Infra (TDD em TK15/17/19) |
| US16 — Cadastro seguro | TK01 Regras de senha | TDD |
| US17 — Login JWT | TK01 Token service, TK02 get_current_user, TK03 Service login, TK04 Controller, TK05 Migração X-User-Id | TDD + refactor (TK05) |
| US18 — Recuperar senha | TK01 Email infra, TK02 Reset token repo, TK03 DTOs, TK04 Service, TK05 Controllers | TDD (slice) |
| US19 — Logout | TK01 Denylist repo, TK02 Service+guard, TK03 Controller | TDD (slice) |
| US20 — Excluir conta | TK01 Entity/migration, TK02 Repo soft-delete, TK03 Finders, TK04 Service, TK05 Controller | TDD + entity (TK01) |

**Já prontos (não contam):** gate de CI; stack Loki/Promtail/Grafana.
